import frappe
from frappe.tests import IntegrationTestCase


class TestScorecard(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Player")
		frappe.db.delete("Team")

	def test_unique_team_timeframe(self):
		frappe.get_doc({"doctype": "Team", "team_name": "SC Team"}).insert()
		first = frappe.get_doc({"doctype": "Scorecard", "team": "SC Team", "timeframe": "Weekly"}).insert()
		self.assertEqual(first.name, "SC Team-Weekly")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "Scorecard", "team": "SC Team", "timeframe": "Weekly"}).insert()

	def test_group_limit_and_unique_name(self):
		frappe.get_doc({"doctype": "Team", "team_name": "SC Group Team"}).insert()
		scorecard = frappe.get_doc({"doctype": "Scorecard", "team": "SC Group Team", "timeframe": "Weekly"}).insert()
		for number in range(1, 21):
			frappe.get_doc(
				{
					"doctype": "Measurable Group",
					"group_name": f"SC Group {number}",
					"scorecard": scorecard.name,
				}
			).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Measurable Group",
					"group_name": "SC Group 21",
					"scorecard": scorecard.name,
				}
			).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Measurable Group",
					"group_name": "SC Group 1",
					"scorecard": scorecard.name,
				}
			).insert()

	def test_rollup_view_splits_month_by_calendar_day(self):
		scorecard = self._seed_weekly_scorecard()
		metric = self._seed_metric(scorecard, "SC Straddle")
		metric.append("entries", {"week_start_date": "2026-10-27", "actual_value": 70})
		metric.save()
		view = scorecard.get_rollup_view("Month", "2026-10-01", "2026-11-30")
		self.assertEqual([period["label"] for period in view["periods"]], ["October 2026", "November 2026"])
		values = view["metrics"][0]["values"]
		self.assertAlmostEqual(values[0]["value"], 50.0)
		self.assertAlmostEqual(values[1]["value"], 20.0)

	def test_rollup_view_totals_whole_and_partial_weeks(self):
		scorecard = self._seed_weekly_scorecard()
		metric = self._seed_metric(scorecard, "SC Total")
		metric.append("entries", {"week_start_date": "2026-10-19", "actual_value": 70})
		metric.append("entries", {"week_start_date": "2026-10-26", "actual_value": 70})
		metric.save()
		view = scorecard.get_rollup_view("Month", "2026-10-01", "2026-10-31")
		self.assertAlmostEqual(view["metrics"][0]["values"][0]["value"], 130.0)

	def test_rollup_view_honours_average_rollup(self):
		scorecard = self._seed_weekly_scorecard()
		metric = self._seed_metric(scorecard, "SC Average", rollup="Average")
		metric.append("entries", {"week_start_date": "2026-10-19", "actual_value": 70})
		metric.append("entries", {"week_start_date": "2026-10-26", "actual_value": 70})
		metric.save()
		view = scorecard.get_rollup_view("Month", "2026-10-01", "2026-10-31")
		self.assertAlmostEqual(view["metrics"][0]["values"][0]["value"], 65.0)

	def test_rollup_view_returns_none_for_period_without_data(self):
		scorecard = self._seed_weekly_scorecard()
		metric = self._seed_metric(scorecard, "SC Sparse")
		metric.append("entries", {"week_start_date": "2026-10-19", "actual_value": 70})
		metric.save()
		view = scorecard.get_rollup_view("Month", "2026-10-01", "2026-11-30")
		values = view["metrics"][0]["values"]
		self.assertAlmostEqual(values[0]["value"], 70.0)
		self.assertIsNone(values[1]["value"])

	def test_rollup_view_keeps_weekly_goal_and_omits_status(self):
		scorecard = self._seed_weekly_scorecard()
		metric = self._seed_metric(scorecard, "SC Goal")
		metric.append("entries", {"week_start_date": "2026-10-19", "actual_value": 70})
		metric.save()
		view = scorecard.get_rollup_view("Month", "2026-10-01", "2026-10-31")
		row = view["metrics"][0]
		self.assertEqual(row["goal"], 100.0)
		self.assertNotIn("status", row)
		self.assertNotIn("status_indicator", row)
		self.assertNotIn("trend", row)
		self.assertTrue(view["read_only"])

	def test_rollup_view_labels_quarter_columns(self):
		scorecard = self._seed_weekly_scorecard()
		view = scorecard.get_rollup_view("Quarter", "2026-10-01", "2027-02-28")
		self.assertEqual(
			[period["label"] for period in view["periods"]],
			["Q4 2026", "Q1 2027"],
		)

	def test_rollup_view_accepts_scorecard_timeframe_alias(self):
		scorecard = self._seed_weekly_scorecard()
		view = scorecard.get_rollup_view("Monthly", "2026-10-01", "2026-10-31")
		self.assertEqual(view["view_by"], "Month")

	def test_rollup_view_rejects_week_view_by(self):
		scorecard = self._seed_weekly_scorecard()
		with self.assertRaises(frappe.ValidationError):
			scorecard.get_rollup_view("Week", "2026-10-01", "2026-10-31")

	def test_rollup_view_rejects_unknown_view_by(self):
		scorecard = self._seed_weekly_scorecard()
		with self.assertRaises(frappe.ValidationError):
			scorecard.get_rollup_view("Fortnight", "2026-10-01", "2026-10-31")

	def test_rollup_view_rejects_non_weekly_scorecard(self):
		self._seed_weekly_scorecard()
		quarterly = frappe.get_doc(
			{"doctype": "Scorecard", "team": "SC Rollup Team", "timeframe": "Quarterly"}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			quarterly.get_rollup_view("Month", "2026-10-01", "2026-10-31")

	def test_rollup_view_rejects_inverted_range(self):
		scorecard = self._seed_weekly_scorecard()
		with self.assertRaises(frappe.ValidationError):
			scorecard.get_rollup_view("Month", "2026-11-30", "2026-10-01")

	def _seed_weekly_scorecard(self):
		frappe.get_doc({"doctype": "Team", "team_name": "SC Rollup Team"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "SC Rollup Leader",
				"user": "Administrator",
				"team": "SC Rollup Team",
			}
		).insert()
		return frappe.get_doc(
			{"doctype": "Scorecard", "team": "SC Rollup Team", "timeframe": "Weekly"}
		).insert()

	def _seed_metric(self, scorecard, metric_name, rollup="Total"):
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": metric_name,
				"owner": "Administrator",
				"team": "SC Rollup Team",
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
				"rollup": rollup,
			}
		).insert()
		self.assertEqual(metric.scorecard, scorecard.name)
		return metric

	def tearDown(self):
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Player")
		frappe.db.delete("Team")
