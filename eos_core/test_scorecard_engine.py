import datetime
import unittest

from eos_core.scorecard_engine import (
	aggregate_values,
	build_quarterly_review,
	build_scorecard_report,
	compute_achievement,
	compute_health,
	compute_status,
	count_consecutive_off_track,
	default_agenda_sections,
	evaluate_formula,
	extract_variables,
	prorate_for_period,
	quarter_bounds,
	rollup_rock_summary,
	rollup_todo_summary,
	scorecard_summary,
)


class TestScorecardEngine(unittest.TestCase):
	def test_compute_status_greater_than(self):
		self.assertEqual(compute_status(100, 80, ">="), "Off Track")
		self.assertEqual(compute_status(100, 120, ">="), "On Track")
		self.assertEqual(compute_status(100, 100, ">="), "On Track")
		self.assertIsNone(compute_status(100, None, ">="))

	def test_compute_status_less_than(self):
		self.assertEqual(compute_status(100, 120, "<="), "Off Track")
		self.assertEqual(compute_status(100, 80, "<="), "On Track")

	def test_compute_status_equal(self):
		self.assertEqual(compute_status(100, 100, "=="), "On Track")
		self.assertEqual(compute_status(100, 110, "=="), "Off Track")

	def test_compute_achievement_clamps(self):
		self.assertEqual(compute_achievement(100, 40, ">="), 40.0)
		self.assertEqual(compute_achievement(100, 140, ">="), 100.0)
		self.assertEqual(compute_achievement(100, 50, "<="), 100.0)
		self.assertIsNone(compute_achievement(0, 50, ">="))

	def test_compute_health_bands(self):
		self.assertEqual(compute_health(100, 110, ">="), "Green")
		self.assertEqual(compute_health(100, 96, ">="), "Yellow")
		self.assertEqual(compute_health(100, 40, ">="), "Red")
		self.assertEqual(compute_health(100, 90, "<="), "Green")
		self.assertEqual(compute_health(100, 102, "<="), "Yellow")
		self.assertEqual(compute_health(100, 150, "<="), "Red")

	def test_aggregate_values(self):
		self.assertEqual(aggregate_values([1, 2, None, 3], "Total"), 6.0)
		self.assertEqual(aggregate_values([2, 4], "Average"), 3.0)
		self.assertIsNone(aggregate_values([None], "Total"))

	def test_range_status_inside(self):
		self.assertEqual(compute_status(None, 100, "Inside min/max", 80, 120), "On Track")
		self.assertEqual(compute_status(None, 130, "Inside min/max", 80, 120), "Off Track")
		self.assertEqual(compute_status(None, 79, "Inside min/max", 80, 120), "Off Track")
		self.assertEqual(compute_status(None, 90, "Inside min/max", 80, None), "On Track")
		self.assertIsNone(compute_status(None, None, "Inside min/max", 80, 120))

	def test_range_status_outside(self):
		self.assertEqual(compute_status(None, 100, "Outside min/max", 80, 120), "Off Track")
		self.assertEqual(compute_status(None, 130, "Outside min/max", 80, 120), "On Track")
		self.assertEqual(compute_status(None, 70, "Outside min/max", 80, 120), "On Track")
		self.assertEqual(compute_status(None, 130, "Outside min/max", 80, None), "Off Track")
		self.assertEqual(compute_status(None, 70, "Outside min/max", 80, None), "On Track")

	def test_range_achievement(self):
		self.assertEqual(compute_achievement(None, 100, "Inside min/max", 80, 120), 100.0)
		self.assertEqual(compute_achievement(None, 40, "Inside min/max", 80, 120), 50.0)
		self.assertEqual(compute_achievement(None, 60, "Inside min/max", 80, None), 75.0)
		self.assertEqual(
			round(compute_achievement(None, 130, "Inside min/max", None, 100), 2), 76.92
		)
		self.assertEqual(compute_achievement(None, 70, "Outside min/max", 80, 120), 100.0)
		self.assertEqual(compute_achievement(None, 100, "Outside min/max", 80, 120), 0.0)

	def test_range_health(self):
		self.assertEqual(compute_health(None, 90, "Inside min/max", min_value=80, max_value=120), "Green")
		self.assertEqual(compute_health(None, 75, "Inside min/max", min_value=80, max_value=120), "Yellow")
		self.assertEqual(compute_health(None, 60, "Inside min/max", min_value=80, max_value=120), "Red")
		self.assertEqual(compute_health(None, 70, "Outside min/max", min_value=80, max_value=120), "Green")
		self.assertEqual(compute_health(None, 116, "Outside min/max", min_value=80, max_value=120), "Yellow")
		self.assertEqual(compute_health(None, 110, "Outside min/max", min_value=80, max_value=120), "Red")

	def test_extract_variables(self):
		self.assertEqual(extract_variables("{Revenue} / {Cost} * 100"), ["Cost", "Revenue"])
		self.assertEqual(extract_variables(""), [])
		self.assertEqual(extract_variables("{ }"), [])

	def test_evaluate_formula(self):
		self.assertEqual(evaluate_formula("{a} * 2 + 1", {"a": 3}), 7.0)
		self.assertEqual(evaluate_formula("( {a} + {b} ) / {c}", {"a": 2, "b": 4, "c": 3}), 2.0)
		self.assertIsNone(evaluate_formula("{a} / {b}", {"a": 1, "b": 0}))
		self.assertIsNone(evaluate_formula("{a} + 1", {"a": None}))
		self.assertIsNone(evaluate_formula("missing + 1", {"missing": 1}))
		self.assertIsNone(evaluate_formula("{a} * 2 +", {"a": 1}))

	def test_formula_max_variables(self):
		variables = {f"m{index}": 1 for index in range(26)}
		formula = " + ".join("{" + name + "}" for name in variables)
		self.assertIsNone(evaluate_formula(formula, variables))

	def test_prorate_for_period(self):
		self.assertAlmostEqual(prorate_for_period(100, 3, 7), 300 / 7)
		self.assertEqual(prorate_for_period(100, 7, 7), 100.0)
		self.assertEqual(prorate_for_period(100, 8, 7), 100.0)
		self.assertIsNone(prorate_for_period(None, 3, 7))
		self.assertIsNone(prorate_for_period(100, 3, 0))

	def test_count_consecutive_off_track(self):
		self.assertEqual(count_consecutive_off_track(["On Track", "Off Track", "Off Track"]), 2)
		self.assertEqual(count_consecutive_off_track(["On Track", "On Track"]), 0)
		self.assertEqual(count_consecutive_off_track([]), 0)
		self.assertEqual(count_consecutive_off_track(["Off Track"]), 1)

	def test_scorecard_summary(self):
		self.assertEqual(
			scorecard_summary(["On Track", "Off Track", "On Track"]),
			{"total": 3, "on_track": 2, "off_track": 1},
		)
		self.assertEqual(scorecard_summary([]), {"total": 0, "on_track": 0, "off_track": 0})
		self.assertEqual(scorecard_summary([None]), {"total": 1, "on_track": 0, "off_track": 0})

	def test_default_agenda_sections(self):
		self.assertEqual(
			default_agenda_sections(),
			["Segue", "Scorecard Review", "Good News", "To-Dos", "IDS", "123s of the Week"],
		)

	def test_build_scorecard_report(self):
		report = build_scorecard_report(
			[
				{
					"name": "Revenue",
					"group": "Financials",
					"owner": "Administrator",
					"actual": 90,
					"target": 100,
					"status": "Off Track",
					"statuses": ["Off Track", "Off Track", "Off Track", "Off Track"],
				},
				{
					"name": "Close Rate",
					"status": "On Track",
					"statuses": ["On Track", "On Track"],
				},
			]
		)
		self.assertEqual(report["summary"], {"total": 2, "on_track": 1, "off_track": 1})
		self.assertEqual(report["trends"], [{"name": "Revenue", "consecutive_off_track": 4}])
		self.assertEqual(report["metrics"][0]["consecutive_off_track"], 4)
		self.assertEqual(report["metrics"][1]["consecutive_off_track"], 0)

	def test_build_scorecard_report_threshold(self):
		report = build_scorecard_report(
			[{"name": "Profit", "status": "Off Track", "statuses": ["Off Track", "Off Track"]}],
			trend_threshold=5,
		)
		self.assertEqual(report["trends"], [])

	def test_quarter_bounds(self):
		start, end = quarter_bounds(datetime.date(2026, 10, 15))
		self.assertEqual(start, datetime.date(2026, 10, 1))
		self.assertEqual(end, datetime.date(2026, 12, 31))

	def test_quarter_bounds_rolls_over_year(self):
		start, end = quarter_bounds(datetime.date(2026, 1, 5))
		self.assertEqual(start, datetime.date(2026, 1, 1))
		self.assertEqual(end, datetime.date(2026, 3, 31))

	def test_rollup_rock_summary(self):
		summary = rollup_rock_summary(
			[
				{"status": "In Progress", "progress": 50},
				{"status": "Complete", "progress": 100},
				{"status": "Not Started", "progress": 0},
			]
		)
		self.assertEqual(
			summary, {"total": 3, "active": 2, "complete": 1, "average_progress": 50.0}
		)

	def test_rollup_todo_summary_with_as_of(self):
		summary = rollup_todo_summary(
			[
				{"status": "In Progress", "due_date": datetime.date(2026, 11, 30)},
				{"status": "Complete", "due_date": datetime.date(2026, 10, 5)},
				{"status": "Not Started", "due_date": None},
			],
			as_of="2026-12-31",
		)
		self.assertEqual(
			summary, {"total": 3, "open": 2, "complete": 1, "overdue": 1}
		)

	def test_build_quarterly_review(self):
		review = build_quarterly_review(
			[{"status": "Complete", "progress": 100.0}],
			[{"status": "In Progress", "due_date": datetime.date(2026, 11, 30)}],
			[{"status": "On Track"}, {"status": "Off Track"}],
			as_of="2026-12-31",
		)
		self.assertEqual(review["rocks"]["total"], 1)
		self.assertEqual(review["todos"]["overdue"], 1)
		self.assertEqual(
			review["measurables"], {"total": 2, "on_track": 1, "off_track": 1}
		)