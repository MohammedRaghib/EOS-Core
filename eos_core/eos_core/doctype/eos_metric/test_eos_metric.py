import frappe
from frappe.tests import IntegrationTestCase


class TestEOSMetric(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Player")
		frappe.db.delete("Team")

	def test_auto_status_on_save(self):
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Auto Status",
				"owner": "Administrator",
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		)
		metric.append("entries", {"week_start_date": "2026-09-07", "actual_value": 80})
		metric.append("entries", {"week_start_date": "2026-09-14", "actual_value": 120})
		metric.insert()
		self.assertEqual(metric.entries[0].status, "Off Track")
		self.assertEqual(metric.entries[1].status, "On Track")
		self.assertEqual(metric.entries[0].metric, metric.name)

	def test_team_scoped_owner_rule(self):
		team = frappe.get_doc({"doctype": "Team", "team_name": "GM Leadership"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "GM Admin",
				"user": "Administrator",
				"team": team.name,
			}
		).insert()
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Team Metric",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		self.assertEqual(metric.team, team.name)
		other = frappe.get_doc({"doctype": "Team", "team_name": "GM Other"}).insert()
		with self.assertRaises(frappe.ValidationError):
			bad = frappe.get_doc(
				{
					"doctype": "EOS Metric",
					"metric_name": "GM Bad Metric",
					"owner": "Administrator",
					"team": other.name,
					"target_value": 100,
					"operator": ">=",
					"frequency": "Weekly",
				}
			)
			bad.insert()

	def test_team_metric_autocreates_scorecard(self):
		team = frappe.get_doc({"doctype": "Team", "team_name": "GM Scorecard Team"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "GM Scorecard Admin",
				"user": "Administrator",
				"team": team.name,
			}
		).insert()
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Scorecard Metric",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		scorecard = frappe.db.get_value(
			"Scorecard", {"team": team.name, "timeframe": "Weekly"}, "name"
		)
		self.assertTrue(scorecard)
		self.assertEqual(metric.scorecard, scorecard)

	def test_range_metric_validation(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "EOS Metric",
					"metric_name": "GM Range No Bound",
					"owner": "Administrator",
					"operator": "Inside min/max",
					"frequency": "Weekly",
				}
			).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "EOS Metric",
					"metric_name": "GM Range Min Above Max",
					"owner": "Administrator",
					"min_value": 100,
					"max_value": 50,
					"operator": "Inside min/max",
					"frequency": "Weekly",
				}
			).insert()

	def test_range_metric_status(self):
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Range Status",
				"owner": "Administrator",
				"min_value": 80,
				"max_value": 120,
				"operator": "Inside min/max",
				"frequency": "Weekly",
			}
		).insert()
		metric.append("entries", {"week_start_date": "2026-09-07", "actual_value": 90})
		metric.append("entries", {"week_start_date": "2026-09-14", "actual_value": 130})
		metric.save()
		self.assertEqual(metric.entries[0].status, "On Track")
		self.assertEqual(metric.entries[1].status, "Off Track")

	def test_formula_builder_computes_entries(self):
		base = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Formula Base",
				"owner": "Administrator",
				"target_value": 50,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		base.append("entries", {"week_start_date": "2026-09-07", "actual_value": 50})
		base.append("entries", {"week_start_date": "2026-09-14", "actual_value": 60})
		base.save()
		smart = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Formula Smart",
				"owner": "Administrator",
				"is_smart": 1,
				"formula": "{GM Formula Base} * 2",
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		)
		smart.append("entries", {"week_start_date": "2026-09-07", "actual_value": 999})
		smart.append(
			"entries",
			{"week_start_date": "2026-09-14", "actual_value": 999, "is_manual": 1},
		)
		smart.insert()
		self.assertEqual(smart.entries[0].actual_value, 100.0)
		self.assertEqual(smart.entries[0].status, "On Track")
		self.assertEqual(smart.entries[1].actual_value, 999)

	def test_non_range_metric_resaves_after_reload(self):
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Resave",
				"owner": "Administrator",
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		metric.append("entries", {"week_start_date": "2026-09-07", "actual_value": 90})
		metric.save()
		metric.reload()
		metric.description = "resaved"
		metric.save()
		self.assertEqual(metric.entries[0].status, "Off Track")
		self.assertEqual(metric.min_value, None)

	def test_formula_with_division_is_accepted(self):
		base = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Div Base",
				"owner": "Administrator",
				"target_value": 50,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		base.append("entries", {"week_start_date": "2026-09-07", "actual_value": 10})
		base.save()
		smart = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Div Smart",
				"owner": "Administrator",
				"is_smart": 1,
				"formula": "{GM Div Base} / (1 - 0.5)",
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		)
		smart.append("entries", {"week_start_date": "2026-09-07"})
		smart.insert()
		self.assertEqual(smart.entries[0].actual_value, 20.0)

	def test_formula_keeps_value_when_source_missing(self):
		base = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Partial Base",
				"owner": "Administrator",
				"target_value": 50,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		base.append("entries", {"week_start_date": "2026-09-07", "actual_value": 20})
		base.save()
		smart = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Partial Smart",
				"owner": "Administrator",
				"is_smart": 1,
				"formula": "{GM Partial Base} * 2",
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		)
		smart.append("entries", {"week_start_date": "2026-09-07"})
		smart.append("entries", {"week_start_date": "2026-09-14"})
		smart.insert()
		self.assertEqual(smart.entries[0].actual_value, 40.0)
		smart.reload()
		smart.entries[1].actual_value = 7
		smart.save()
		self.assertEqual(smart.entries[1].actual_value, 7)
		self.assertEqual(smart.entries[0].actual_value, 40.0)

	def test_formula_self_reference_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "EOS Metric",
					"metric_name": "GM Self Reference",
					"owner": "Administrator",
					"is_smart": 1,
					"formula": "{GM Self Reference} + 1",
					"frequency": "Weekly",
				}
			).insert()

	def test_dangling_group_raises_validation_error(self):
		metric, group = self._metric_with_group()

		frappe.delete_doc("Measurable Group", group.name, force=True)

		metric.flags.ignore_links = True
		with self.assertRaises(frappe.ValidationError) as context:
			metric.description = "Touch"
			metric.save()
		message = str(context.exception)
		self.assertIn(group.name, message)
		self.assertIn("Group", message)
		self.assertNotIsInstance(context.exception, frappe.DoesNotExistError)

	def test_dangling_group_caught_by_link_validation_on_normal_save(self):
		metric, group = self._metric_with_group()

		frappe.delete_doc("Measurable Group", group.name, force=True)

		with self.assertRaises(frappe.LinkValidationError):
			metric.description = "Touch"
			metric.save()

	def _metric_with_group(self):
		team = frappe.get_doc({"doctype": "Team", "team_name": "GM Group Team"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "GM Group Admin",
				"user": "Administrator",
				"team": team.name,
			}
		).insert()
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Group Metric",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		group = frappe.get_doc(
			{
				"doctype": "Measurable Group",
				"group_name": "GM Revenue Group",
				"scorecard": metric.scorecard,
			}
		).insert()
		metric.group = group.name
		metric.save()
		return metric, group

	def tearDown(self):
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Player")
		frappe.db.delete("Team")