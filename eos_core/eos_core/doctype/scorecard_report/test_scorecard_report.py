import frappe
from frappe.tests import IntegrationTestCase
from unittest import mock

from eos_core.scorecard_engine import STATUS_INDICATORS

EMAIL_TEMPLATE_NAME = "weekly_scorecard_report.html"


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
		good.append("entries", {"week_start_date": "2026-08-17", "actual_value": 105})
		good.append("entries", {"week_start_date": "2026-08-24", "actual_value": 115})
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

	def test_snapshot_follows_measurable_group_order(self):
		team = self._seed_metrics()
		scorecard = frappe.db.get_value(
			"Scorecard", {"team": team.name, "timeframe": "Weekly"}, "name"
		)
		second = frappe.get_doc(
			{
				"doctype": "Measurable Group",
				"group_name": "SR Second",
				"scorecard": scorecard,
				"order": 1,
			}
		).insert()
		first = frappe.get_doc(
			{
				"doctype": "Measurable Group",
				"group_name": "SR First",
				"scorecard": scorecard,
				"order": 0,
			}
		).insert()
		frappe.db.set_value("EOS Metric", "SR Good", "group", first.name)
		frappe.db.set_value("EOS Metric", "SR Bad", "group", second.name)
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		rows = [(row.group, row.metric) for row in report.report_metrics]
		self.assertEqual(
			rows, [("SR First", "SR Good"), ("SR Second", "SR Bad")]
		)

	def test_snapshot_places_ungrouped_metrics_last(self):
		team = self._seed_metrics()
		scorecard = frappe.db.get_value(
			"Scorecard", {"team": team.name, "timeframe": "Weekly"}, "name"
		)
		group = frappe.get_doc(
			{
				"doctype": "Measurable Group",
				"group_name": "SR Only Group",
				"scorecard": scorecard,
				"order": 0,
			}
		).insert()
		frappe.db.set_value("EOS Metric", "SR Good", "group", group.name)
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		rows = [(row.group, row.metric) for row in report.report_metrics]
		self.assertEqual(rows[-1], ("", "SR Bad"))
		self.assertEqual(rows[0], ("SR Only Group", "SR Good"))

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

	def test_send_report_reads_template_as_utf8(self):
		team = self._seed_metrics()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		real_open = open
		calls = []

		def recording_open(path, *args, **kwargs):
			calls.append((str(path), kwargs))
			return real_open(path, *args, **kwargs)

		with mock.patch.object(frappe, "sendmail") as sendmail:
			with mock.patch("builtins.open", recording_open):
				report.send_report()

		template_calls = [
			kwargs for path, kwargs in calls if path.endswith(EMAIL_TEMPLATE_NAME)
		]
		self.assertEqual(len(template_calls), 1)
		self.assertEqual(template_calls[0].get("encoding"), "utf-8")
		self.assertIn("—", sendmail.call_args.kwargs["message"])

	def test_send_report_is_refused_without_the_email_permission(self):
		team = self._seed_metrics()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-07",
			}
		).insert()
		observer = "sro.observer@example.com"
		frappe.get_doc(
			{
				"doctype": "User",
				"name": observer,
				"email": observer,
				"first_name": "Observer",
				"roles": [{"role": "Observer"}],
			}
		).insert(ignore_permissions=True)
		frappe.cache.hdel("roles", observer)
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "SR Observer",
				"user": observer,
				"team": team.name,
			}
		).insert()
		with self.set_user(observer), mock.patch.object(frappe, "sendmail") as sendmail:
			report = frappe.get_doc("Scorecard Report", report.name)
			report.check_permission("read")
			with self.assertRaises(frappe.PermissionError):
				report.send_report()
			sendmail.assert_not_called()
		self.assertEqual(
			frappe.db.get_value("Scorecard Report", report.name, "status"), "Draft"
		)

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
		off_track = frappe.get_doc("EOS Metric", "SR Good")
		off_track.append("entries", {"week_start_date": "2026-09-14", "actual_value": 20})
		off_track.save()
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

	def test_status_indicator_counts_empty_intervals_against(self):
		team = self._seed_metrics()
		sparse = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "SR Sparse",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		sparse.append("entries", {"week_start_date": "2026-09-07", "actual_value": 120})
		sparse.save()
		report = frappe.get_doc(
			{
				"doctype": "Scorecard Report",
				"team": team.name,
				"week_start_date": "2026-09-14",
			}
		).insert()
		row = next(row for row in report.report_metrics if row.metric == "SR Sparse")
		self.assertEqual(row.status_indicator, "Yellow")

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
