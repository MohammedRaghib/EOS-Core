import frappe
from frappe.tests import IntegrationTestCase
from unittest import mock

from eos_core.scorecard_engine import STATUS_INDICATORS


class TestScorecardReport(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Scorecard Report Metric")
		frappe.db.delete("Scorecard Report")
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Player")
		frappe.db.delete("Team")

	def _seed_metrics(self):
		team = frappe.get_doc({"doctype": "Team", "team_name": "SR Team"}).insert()
		leader = frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "SR Leader",
				"user": "Administrator",
				"team": team.name,
			}
		).insert()
		frappe.db.set_value("Team", team.name, "leader", leader.name)

		good = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "SR Good",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		good.append("entries", {"week_start_date": "2026-08-31", "actual_value": 110})
		good.append("entries", {"week_start_date": "2026-09-07", "actual_value": 120})
		good.save()

		bad = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "SR Bad",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		for value in (80, 70, 60):
			bad.append("entries", {"week_start_date": "2026-08-30", "actual_value": value})
		bad.entries[0].week_start_date = "2026-08-17"
		bad.entries[1].week_start_date = "2026-08-24"
		bad.save()
		return team

	def test_snapshot_generation(self):
		team = self._seed_metrics()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		self.assertEqual(report.total_metrics, 2)
		self.assertEqual(report.on_track, 1)
		self.assertEqual(report.off_track, 1)
		rows = {row.metric: row for row in report.report_metrics}
		self.assertEqual(rows["SR Bad"].status, "Off Track")
		self.assertEqual(rows["SR Bad"].trend, 3)

	def test_snapshot_ignores_later_entries(self):
		team = self._seed_metrics()
		bad = frappe.get_doc("EOS Metric", "SR Bad")
		bad.append("entries", {"week_start_date": "2026-09-14", "actual_value": 95})
		bad.save()
		reloaded = frappe.get_doc("EOS Metric", "SR Bad")
		late = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		early = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-08-17",
			}
		).insert()
		late_row = {row.metric: row for row in late.report_metrics}["SR Bad"]
		early_row = {row.metric: row for row in early.report_metrics}["SR Bad"]
		self.assertEqual(reloaded.entries[-1].actual_value, 95)
		self.assertEqual(late_row.actual_value, 60)
		self.assertEqual(late_row.trend, 3)
		self.assertEqual(early_row.actual_value, 80)
		self.assertEqual(early_row.trend, 1)

	def test_unique_team_week(self):
		team = self._seed_metrics()
		frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Scorecard Report",
					"team": team.name,
					"week_start_date": "2026-09-07",
				}
			).insert()

	def test_send_report(self):
		team = self._seed_metrics()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		with mock.patch.object(frappe, "sendmail") as sendmail:
			report.send_report()
		self.assertEqual(report.status, "Sent")
		sendmail.assert_called_once()
		kwargs = sendmail.call_args.kwargs
		self.assertEqual(kwargs["recipients"], ["Administrator"])
		self.assertIn("SR Bad", kwargs["message"])
		self.assertIn("off track", kwargs["message"].lower())

	def test_status_indicator_uses_completed_periods_only(self):
		team = self._seed_metrics()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		indicators = {row.metric: row.status_indicator for row in report.report_metrics}
		self.assertEqual(indicators["SR Good"], "Green")
		self.assertEqual(indicators["SR Bad"], "Red")

	def test_status_indicator_ignores_in_progress_report_week(self):
		team = self._seed_metrics()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-14",
			}
		).insert()
		self.assertEqual(report.status, "Draft")
		good = next(row for row in report.report_metrics if row.metric == "SR Good")
		bad = next(row for row in report.report_metrics if row.metric == "SR Bad")
		self.assertEqual(bad.status_indicator, "Red")
		self.assertEqual(good.status_indicator, "Green")

	def test_status_indicator_no_recent_data(self):
		team = frappe.get_doc({"doctype": "Team", "team_name": "SR Empty"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "SR Empty Leader",
				"user": "Administrator",
				"team": team.name,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "SR Unscored",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		row = next(row for row in report.report_metrics if row.metric == "SR Unscored")
		self.assertEqual(row.status_indicator, "No Recent Data")

	def test_send_report_includes_indicator(self):
		team = self._seed_metrics()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		with mock.patch.object(frappe, "sendmail") as sendmail:
			report.send_report()
		message = sendmail.call_args.kwargs["message"]
		self.assertIn("Red", message)

	def test_status_indicator_field_options_match_engine(self):
		field = frappe.get_meta("Scorecard Report Metric").get_field("status_indicator")
		self.assertEqual(tuple(field.options.split("\n")), STATUS_INDICATORS)

	def tearDown(self):
		frappe.db.delete("Scorecard Report Metric")
		frappe.db.delete("Scorecard Report")
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Player")
		frappe.db.delete("Team")