import datetime
import unittest

from eos_core.scorecard_engine import (
	STATUS_INDICATORS,
	aggregate_entries_for_period,
	aggregate_values,
	advance_period,
	build_quarterly_review,
	build_scorecard_report,
	build_scorecard_review_lines,
	compute_achievement,
	compute_status,
	compute_status_indicator,
	completed_period_statuses,
	count_consecutive_off_track,
	default_agenda_sections,
	evaluate_formula,
	extract_variables,
	is_period_complete,
	normalise_view_by,
	period_bounds,
	period_label,
	prorate_for_period,
	quarter_bounds,
	recent_completed_period_starts,
	rollup_periods,
	rollup_rock_summary,
	rollup_todo_summary,
	scorecard_summary,
	sort_metrics_by_group,
	validate_formula_syntax,
	week_overlap_days,
	week_overlap_ratio,
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

	def test_compute_achievement_zero_actual(self):
		self.assertEqual(compute_achievement(100, 0, "<="), 100.0)
		self.assertEqual(compute_achievement(-100, 0, "<="), 0.0)
		self.assertEqual(compute_achievement(100, 0, ">="), 0.0)
		self.assertEqual(compute_achievement(100, 0, "=="), 0.0)

	def test_status_indicator_all_on_track(self):
		self.assertEqual(compute_status_indicator(["On Track"] * 3), "Green")
		self.assertEqual(compute_status_indicator(["On Track"] * 9), "Green")

	def test_status_indicator_one_miss_is_yellow(self):
		self.assertEqual(compute_status_indicator(["On Track", "Off Track", "On Track"]), "Yellow")
		self.assertEqual(compute_status_indicator(["On Track", "On Track", "Off Track"]), "Yellow")

	def test_status_indicator_all_missed_is_red(self):
		self.assertEqual(compute_status_indicator(["Off Track"] * 3), "Red")
		self.assertEqual(compute_status_indicator(["Off Track", "Off Track", "Off Track", "On Track"]), "Yellow")

	def test_status_indicator_uses_only_last_three(self):
		self.assertEqual(
			compute_status_indicator(["Off Track", "Off Track", "Off Track", "On Track", "On Track", "On Track"]),
			"Green",
		)

	def test_status_indicator_no_recent_data(self):
		self.assertEqual(compute_status_indicator([]), "No Recent Data")
		self.assertEqual(compute_status_indicator([None, None]), "No Recent Data")
		self.assertEqual(compute_status_indicator(None), "No Recent Data")

	def test_status_indicator_partial_history(self):
		self.assertEqual(compute_status_indicator(["On Track", "On Track"]), "Green")
		self.assertEqual(compute_status_indicator(["On Track", "Off Track"]), "Yellow")
		self.assertEqual(compute_status_indicator(["Off Track"]), "Red")

	def test_status_indicator_single_on_track_does_not_clear_red(self):
		self.assertEqual(compute_status_indicator(["Off Track", "Off Track", "On Track"]), "Yellow")

	def test_status_indicator_only_returns_declared_indicators(self):
		cases = [
			[],
			[None],
			["On Track"],
			["Off Track"],
			["On Track", "Off Track"],
			["On Track"] * 3,
			["Off Track"] * 3,
			["On Track", "On Track", "Off Track"],
			[None, "On Track", None],
			["On Track"] * 9,
		]
		for statuses in cases:
			self.assertIn(compute_status_indicator(statuses), STATUS_INDICATORS)

	def test_status_indicators_cover_every_documented_state(self):
		self.assertEqual(set(STATUS_INDICATORS), {"Green", "Yellow", "Red", "No Recent Data"})

	def test_is_period_complete(self):
		week = datetime.date(2026, 9, 21)
		self.assertFalse(is_period_complete(week, datetime.date(2026, 9, 27)))
		self.assertTrue(is_period_complete(week, datetime.date(2026, 9, 28)))
		self.assertFalse(is_period_complete(week, datetime.date(2026, 9, 21)))
		self.assertTrue(is_period_complete("2026-09-21", "2026-10-01"))
		self.assertFalse(is_period_complete(None, datetime.date(2026, 9, 28)))

	def test_completed_period_statuses_excludes_in_progress(self):
		entries = [
			{"week_start_date": "2026-08-31", "status": "On Track"},
			{"week_start_date": "2026-09-07", "status": "Off Track"},
			{"week_start_date": "2026-09-14", "status": "On Track"},
			{"week_start_date": "2026-09-21", "status": "Off Track"},
			{"week_start_date": "2026-09-28", "status": "Off Track"},
		]
		completed = completed_period_statuses(entries, today="2026-09-28")
		self.assertEqual(completed, ["Off Track", "On Track", "Off Track"])
		self.assertEqual(compute_status_indicator(completed), "Yellow")

	def test_completed_period_statuses_sorted_oldest_first(self):
		entries = [
			{"week_start_date": datetime.date(2026, 9, 14), "status": "Off Track"},
			{"week_start_date": datetime.date(2026, 9, 7), "status": "On Track"},
		]
		completed = completed_period_statuses(entries, today="2026-09-21")
		self.assertEqual(completed, [None, "On Track", "Off Track"])

	def test_completed_period_statuses_ignores_missing_dates(self):
		entries = [
			{"status": "On Track"},
			{"week_start_date": None, "status": "Off Track"},
			{"week_start_date": "2026-08-31", "status": "On Track"},
		]
		completed = completed_period_statuses(entries, today="2026-09-07")
		self.assertEqual(completed, [None, None, "On Track"])

	def test_completed_period_statuses_fills_gaps_with_none(self):
		entries = [
			{"week_start_date": "2026-08-17", "status": "Off Track"},
			{"week_start_date": "2026-08-24", "status": "On Track"},
			{"week_start_date": "2026-08-31", "status": "On Track"},
		]
		completed = completed_period_statuses(entries, today="2026-09-14")
		self.assertEqual(completed, ["On Track", "On Track", None])
		self.assertEqual(compute_status_indicator(completed), "Yellow")

	def test_recent_completed_period_starts_excludes_current_week(self):
		self.assertEqual(
			recent_completed_period_starts("2026-09-28"),
			[
				datetime.date(2026, 9, 7),
				datetime.date(2026, 9, 14),
				datetime.date(2026, 9, 21),
			],
		)
		self.assertEqual(
			recent_completed_period_starts("2026-09-27"),
			[
				datetime.date(2026, 8, 31),
				datetime.date(2026, 9, 7),
				datetime.date(2026, 9, 14),
			],
		)

	def test_empty_completed_intervals_count_against_indicator(self):
		self.assertEqual(compute_status_indicator([None, "On Track", "On Track"]), "Yellow")
		self.assertEqual(compute_status_indicator([None, None, "Off Track"]), "Red")
		self.assertEqual(compute_status_indicator([None, None, None]), "No Recent Data")
		self.assertEqual(compute_status_indicator(["On Track"] * 3), "Green")

	def test_indicator_uses_monday_aligned_weekly_grid(self):
		entries = [
			{"week_start_date": "2026-08-17", "status": "On Track"},
			{"week_start_date": "2026-08-24", "status": "On Track"},
			{"week_start_date": "2026-08-30", "status": "On Track"},
		]
		completed = completed_period_statuses(entries, today="2026-09-07")
		self.assertEqual(completed, ["On Track", "On Track", None])
		self.assertEqual(compute_status_indicator(completed), "Yellow")

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
		over_limit_formula = " + ".join("{" + f"m{index}" + "}" for index in range(26))
		self.assertIsNone(evaluate_formula(over_limit_formula, {"m0": 1, "m1": 1, "m2": 1}))

	def test_validate_formula_syntax(self):
		self.assertTrue(validate_formula_syntax("{a} + {b}"))
		self.assertTrue(validate_formula_syntax("{a} * 2 - {b} / 4"))
		self.assertTrue(validate_formula_syntax("{a} / (1 - {b})"))
		self.assertTrue(validate_formula_syntax("2 + 2"))
		self.assertFalse(validate_formula_syntax(""))
		self.assertFalse(validate_formula_syntax("{a} + foo"))
		self.assertFalse(validate_formula_syntax('{a} + __import__("os")'))
		self.assertFalse(validate_formula_syntax("{a}{b}"))
		self.assertFalse(validate_formula_syntax("{a} * 2 +"))
		self.assertFalse(validate_formula_syntax("{a} + {b"))

	def test_prorate_for_period(self):
		self.assertAlmostEqual(prorate_for_period(100, 3, 7), 300 / 7)
		self.assertEqual(prorate_for_period(100, 7, 7), 100.0)
		self.assertEqual(prorate_for_period(100, 8, 7), 100.0)
		self.assertIsNone(prorate_for_period(None, 3, 7))
		self.assertIsNone(prorate_for_period(100, 3, 0))

	def test_prorate_for_period_rejects_negative_input(self):
		self.assertIsNone(prorate_for_period(100, -3, 7))
		self.assertIsNone(prorate_for_period(100, 3, -7))
		self.assertIsNone(prorate_for_period(100, 0, 7))
		self.assertIsNone(prorate_for_period(100, -3, -7))

	def test_week_overlap_days_splits_by_calendar_day(self):
		self.assertEqual(week_overlap_days("2026-10-27", "2026-10-01", "2026-10-31"), 5)
		self.assertEqual(week_overlap_days("2026-10-27", "2026-11-01", "2026-11-30"), 2)
		self.assertEqual(week_overlap_days("2026-10-19", "2026-10-01", "2026-10-31"), 7)
		self.assertEqual(week_overlap_days("2026-09-28", "2026-11-01", "2026-11-30"), 0)
		self.assertEqual(week_overlap_days("2026-12-28", "2026-12-01", "2026-12-31"), 4)
		self.assertEqual(week_overlap_days("2026-12-28", "2027-01-01", "2027-01-31"), 3)

	def test_week_overlap_ratio_is_bounded(self):
		self.assertAlmostEqual(
			week_overlap_ratio("2026-10-27", "2026-10-01", "2026-10-31"), 5 / 7
		)
		self.assertAlmostEqual(
			week_overlap_ratio("2026-10-27", "2026-11-01", "2026-11-30"), 2 / 7
		)
		self.assertEqual(week_overlap_ratio("2026-10-19", "2026-10-01", "2026-10-31"), 1.0)
		self.assertEqual(week_overlap_ratio("2026-08-03", "2026-10-01", "2026-10-31"), 0.0)

	def test_week_overlap_days_ignores_unparseable_dates(self):
		self.assertEqual(week_overlap_days(None, "2026-10-01", "2026-10-31"), 0)
		self.assertEqual(week_overlap_days("2026-10-27", None, "2026-10-31"), 0)
		self.assertEqual(week_overlap_days("2026-10-27", "2026-10-01", "not-a-date"), 0)

	def test_aggregate_entries_for_period_splits_straddling_week(self):
		entries = [
			{"week_start_date": "2026-10-19", "actual_value": 70},
			{"week_start_date": "2026-10-26", "actual_value": 70},
			{"week_start_date": "2026-11-02", "actual_value": 70},
		]
		october = aggregate_entries_for_period(entries, "2026-10-01", "2026-10-31", "Total")
		november = aggregate_entries_for_period(entries, "2026-11-01", "2026-11-30", "Total")
		self.assertAlmostEqual(october, 70 + 60)
		self.assertAlmostEqual(november, 10 + 70)

	def test_aggregate_entries_for_period_honours_rollup(self):
		entries = [
			{"week_start_date": "2026-10-19", "actual_value": 70},
			{"week_start_date": "2026-10-26", "actual_value": 70},
		]
		average = aggregate_entries_for_period(entries, "2026-10-01", "2026-10-31", "Average")
		self.assertAlmostEqual(average, (70 + 60) / 2)

	def test_aggregate_entries_for_period_skips_unscored_entries(self):
		entries = [
			{"week_start_date": "2026-10-19", "actual_value": None},
			{"week_start_date": "2026-10-26", "actual_value": 70},
		]
		total = aggregate_entries_for_period(entries, "2026-10-01", "2026-10-31", "Total")
		self.assertAlmostEqual(total, 60)

	def test_aggregate_entries_for_period_without_contributors(self):
		entries = [{"week_start_date": "2026-08-03", "actual_value": 70}]
		self.assertIsNone(aggregate_entries_for_period(entries, "2026-10-01", "2026-10-31", "Total"))
		self.assertIsNone(aggregate_entries_for_period([], "2026-10-01", "2026-10-31", "Total"))
		self.assertIsNone(aggregate_entries_for_period(None, "2026-10-01", "2026-10-31", "Total"))

	def test_normalise_view_by_accepts_scorecard_timeframes(self):
		self.assertEqual(normalise_view_by("Weekly"), "Week")
		self.assertEqual(normalise_view_by("Monthly"), "Month")
		self.assertEqual(normalise_view_by("Quarterly"), "Quarter")
		self.assertEqual(normalise_view_by("Annual"), "Year")
		self.assertEqual(normalise_view_by("Month"), "Month")
		self.assertIsNone(normalise_view_by("Fortnight"))
		self.assertIsNone(normalise_view_by(None))

	def test_period_bounds_per_view(self):
		self.assertEqual(
			period_bounds("2026-10-27", "Week"),
			(datetime.date(2026, 10, 27), datetime.date(2026, 11, 2)),
		)
		self.assertEqual(
			period_bounds("2026-10-27", "Month"),
			(datetime.date(2026, 10, 1), datetime.date(2026, 10, 31)),
		)
		self.assertEqual(
			period_bounds("2026-11-02", "Quarter"),
			(datetime.date(2026, 10, 1), datetime.date(2026, 12, 31)),
		)
		self.assertEqual(
			period_bounds("2026-02-05", "Year"),
			(datetime.date(2026, 1, 1), datetime.date(2026, 12, 31)),
		)
		self.assertIsNone(period_bounds("2026-10-27", "Decade"))
		self.assertIsNone(period_bounds(None, "Month"))

	def test_advance_period_rolls_over_year(self):
		self.assertEqual(advance_period("2026-10-27", "Week"), datetime.date(2026, 11, 3))
		self.assertEqual(advance_period("2026-10-01", "Month"), datetime.date(2026, 11, 1))
		self.assertEqual(advance_period("2026-12-01", "Month"), datetime.date(2027, 1, 1))
		self.assertEqual(advance_period("2026-10-01", "Quarter"), datetime.date(2027, 1, 1))
		self.assertEqual(advance_period("2026-07-01", "Quarter"), datetime.date(2026, 10, 1))
		self.assertEqual(advance_period("2026-01-01", "Year"), datetime.date(2027, 1, 1))

	def test_period_label_matches_ninety_headers(self):
		self.assertEqual(period_label("2026-10-01", "Month"), "October 2026")
		self.assertEqual(period_label("2026-10-01", "Quarter"), "Q4 2026")
		self.assertEqual(period_label("2026-01-01", "Quarter"), "Q1 2026")
		self.assertEqual(period_label("2026-01-01", "Year"), "2026")
		self.assertEqual(period_label("2026-10-27", "Week"), "2026-10-27")

	def test_rollup_periods_covers_range(self):
		periods = rollup_periods("Month", "2026-10-27", "2026-12-15")
		self.assertEqual(
			[period["label"] for period in periods],
			["October 2026", "November 2026", "December 2026"],
		)
		self.assertEqual(periods[0]["period_start"], "2026-10-01")
		self.assertEqual(periods[0]["period_end"], "2026-10-31")
		self.assertEqual(periods[0]["view_by"], "Month")

	def test_rollup_periods_rolls_across_year_boundary(self):
		periods = rollup_periods("Quarter", "2026-11-02", "2027-02-02")
		self.assertEqual(
			[period["label"] for period in periods],
			["Q4 2026", "Q1 2027"],
		)

	def test_rollup_periods_rejects_unknown_view(self):
		self.assertEqual(rollup_periods("Decade", "2026-10-01", "2026-12-31"), [])
		self.assertEqual(rollup_periods("Month", None, "2026-12-31"), [])

	def test_sort_metrics_by_group_uses_group_order(self):
		metrics = [
			{"name": "C", "group": "Third", "group_key": "g3"},
			{"name": "A", "group": "First", "group_key": "g1"},
			{"name": "B", "group": "Second", "group_key": "g2"},
		]
		sorted_metrics = sort_metrics_by_group(metrics, {"g1": 0, "g2": 1, "g3": 2})
		self.assertEqual([metric["name"] for metric in sorted_metrics], ["A", "B", "C"])

	def test_sort_metrics_by_group_places_ungrouped_last(self):
		metrics = [
			{"name": "Loose", "group": "", "group_key": None},
			{"name": "A", "group": "First", "group_key": "g1"},
			{"name": "Loose Two", "group": None, "group_key": None},
		]
		sorted_metrics = sort_metrics_by_group(metrics, {"g1": 0})
		self.assertEqual(
			[metric["name"] for metric in sorted_metrics], ["A", "Loose", "Loose Two"]
		)

	def test_sort_metrics_by_group_treats_missing_order_as_zero(self):
		metrics = [
			{"name": "B", "group": "Second", "group_key": "g2"},
			{"name": "A", "group": "First", "group_key": "unknown"},
		]
		sorted_metrics = sort_metrics_by_group(metrics, {"g2": 1})
		self.assertEqual([metric["name"] for metric in sorted_metrics], ["A", "B"])

	def test_sort_metrics_by_group_is_stable_within_a_group(self):
		metrics = [
			{"name": "One", "group": "First", "group_key": "g1"},
			{"name": "Two", "group": "First", "group_key": "g1"},
			{"name": "Three", "group": "First", "group_key": "g1"},
		]
		sorted_metrics = sort_metrics_by_group(metrics, {"g1": 0})
		self.assertEqual(
			[metric["name"] for metric in sorted_metrics], ["One", "Two", "Three"]
		)

	def test_sort_metrics_by_group_handles_empty_input(self):
		self.assertEqual(sort_metrics_by_group([], {}), [])
		self.assertEqual(sort_metrics_by_group(None, {}), [])

	def test_build_scorecard_review_lines_groups_and_annotates(self):
		metrics = [
			{"name": "C", "group": "Ops", "group_key": "g2", "status_indicator": "Red"},
			{"name": "A", "group": "Growth", "group_key": "g1", "status_indicator": "Green"},
			{"name": "B", "group": "Growth", "group_key": "g1", "status_indicator": None},
			{"name": "D", "group": "", "group_key": None, "status_indicator": "No Recent Data"},
		]
		lines = build_scorecard_review_lines(metrics, {"g1": 0, "g2": 1})
		self.assertEqual(
			lines,
			[
				"Growth",
				"  A (Green)",
				"  B",
				"Ops",
				"  C (Red)",
				"Ungrouped",
				"  D (No Recent Data)",
			],
		)

	def test_build_scorecard_review_lines_without_metrics(self):
		self.assertEqual(build_scorecard_review_lines([], {}), [])
		self.assertEqual(build_scorecard_review_lines(None, {}), [])

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
