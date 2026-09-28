import ast
import re

MAX_FORMULA_VARIABLES = 25
VARIABLE_PATTERN = re.compile(r"{([^{}\n]+)}")
_SAFE_EXPRESSION = re.compile(r"^[\d\.\+\-\*\/\(\)\%\s]+$")

_COMPARISON_OPERATORS = (">=", "<=", "==")
_RANGE_OPERATORS = ("Inside min/max", "Outside min/max")

RANGE_OPERATORS = _RANGE_OPERATORS
ALL_OPERATORS = _COMPARISON_OPERATORS + _RANGE_OPERATORS
MATCHLESS_OPERATORS = ("==",)

STATUS_WINDOW = 3
STATUS_INDICATORS = ("Green", "Yellow", "Red", "No Recent Data")
SCORED_STATUSES = ("On Track", "Off Track")
WEEK_LENGTH_DAYS = 7

VIEW_BY_PERIODS = ("Week", "Month", "Quarter", "Year")
READ_ONLY_VIEW_BY = ("Month", "Quarter", "Year")
ROLLUP_RANGE_WEEKS = 13
VIEW_BY_ALIASES = {
	"Weekly": "Week",
	"Monthly": "Month",
	"Quarterly": "Quarter",
	"Annual": "Year",
}


def compute_status(target_value, actual_value, operator, min_value=None, max_value=None):
	if operator in _RANGE_OPERATORS:
		return _range_status(actual_value, operator, min_value, max_value)
	if actual_value is None:
		return None
	if target_value is None or target_value == 0:
		return "On Track"
	if operator == ">=":
		return "On Track" if actual_value >= target_value else "Off Track"
	if operator == "<=":
		return "On Track" if actual_value <= target_value else "Off Track"
	if operator == "==":
		return "On Track" if actual_value == target_value else "Off Track"
	return "Off Track"


def compute_status_indicator(statuses, window=STATUS_WINDOW):
	windowed = list(statuses or [])
	if window:
		windowed = windowed[-window:]
	if not any(status in SCORED_STATUSES for status in windowed):
		return "No Recent Data"
	if all(status == "On Track" for status in windowed):
		return "Green"
	if all(status != "On Track" for status in windowed):
		return "Red"
	return "Yellow"


def is_period_complete(period_start, today=None):
	period_start = _as_date(period_start)
	today = _as_date(today) or _today()
	if period_start is None:
		return False
	return _add_days(period_start, WEEK_LENGTH_DAYS - 1) < today


def completed_period_statuses(entries, today=None, window=STATUS_WINDOW):
	statuses = {}
	for entry in entries or []:
		period_start = _as_date(entry.get("week_start_date"))
		if period_start is not None:
			statuses[period_start] = entry.get("status")
	return [
		statuses.get(period_start)
		for period_start in recent_completed_period_starts(today, window)
	]


def compute_achievement(target_value, actual_value, operator, min_value=None, max_value=None):
	if actual_value is None:
		return None
	if operator in _RANGE_OPERATORS:
		return _range_achievement(actual_value, operator, min_value, max_value)
	if target_value is None or target_value == 0:
		return None
	if operator == ">=":
		return _clamp(actual_value / target_value * 100)
	if operator == "<=":
		if actual_value == 0:
			return 100.0 if target_value > 0 else 0.0
		return _clamp(target_value / actual_value * 100)
	if operator == "==":
		return _clamp((1 - abs(target_value - actual_value) / abs(target_value)) * 100)
	return None


def aggregate_values(values, rollup):
	values = [value for value in values if value is not None]
	if not values:
		return None
	if rollup == "Average":
		return sum(values) / len(values)
	return sum(values)


def extract_variables(formula):
	variables = set()
	for match in VARIABLE_PATTERN.findall(formula or ""):
		name = match.strip()
		if name:
			variables.add(name)
	return sorted(variables)


def evaluate_formula(formula, variables=None):
	variables = variables or {}
	if len(extract_variables(formula)) > MAX_FORMULA_VARIABLES:
		return None
	expression = formula or ""
	for name in extract_variables(expression):
		value = variables.get(name)
		if value is None:
			return None
		expression = expression.replace("{" + name + "}", str(value))
	if not expression or "{" in expression or "}" in expression:
		return None
	if not _SAFE_EXPRESSION.match(expression):
		return None
	try:
		tree = ast.parse(expression, mode="eval")
		return _eval_ast(tree.body)
	except (SyntaxError, ZeroDivisionError, ValueError, TypeError, OverflowError):
		return None


def validate_formula_syntax(formula):
	expression = formula or ""
	if not expression:
		return False
	for name in extract_variables(expression):
		expression = expression.replace("{" + name + "}", "0.0")
	if "{" in expression or "}" in expression:
		return False
	if not _SAFE_EXPRESSION.match(expression):
		return False
	try:
		ast.parse(expression, mode="eval")
	except (SyntaxError, ValueError, TypeError):
		return False
	return True


def prorate_for_period(value, elapsed, total):
	if value is None:
		return None
	if not elapsed or not total:
		return None
	if elapsed < 0 or total <= 0:
		return None
	if elapsed > total:
		elapsed = total
	return value * elapsed / total


def week_overlap_days(week_start, period_start, period_end):
	week_start = _as_date(week_start)
	period_start = _as_date(period_start)
	period_end = _as_date(period_end)
	if week_start is None or period_start is None or period_end is None:
		return 0
	week_end = _add_days(week_start, WEEK_LENGTH_DAYS - 1)
	overlap = (min(week_end, period_end) - max(week_start, period_start)).days + 1
	if overlap <= 0:
		return 0
	return min(overlap, WEEK_LENGTH_DAYS)


def week_overlap_ratio(week_start, period_start, period_end):
	overlap = week_overlap_days(week_start, period_start, period_end)
	if not overlap:
		return 0.0
	return overlap / WEEK_LENGTH_DAYS


def aggregate_entries_for_period(entries, period_start, period_end, rollup):
	values = []
	for entry in entries or []:
		overlap = week_overlap_days(
			entry.get("week_start_date"), period_start, period_end
		)
		prorated = prorate_for_period(
			entry.get("actual_value"), overlap, WEEK_LENGTH_DAYS
		)
		if prorated is not None:
			values.append(prorated)
	return aggregate_values(values, rollup)


def normalise_view_by(view_by):
	view = VIEW_BY_ALIASES.get(view_by, view_by)
	return view if view in VIEW_BY_PERIODS else None


def period_bounds(anchor, view_by):
	anchor = _as_date(anchor)
	view = normalise_view_by(view_by)
	if anchor is None or view is None:
		return None
	if view == "Week":
		return anchor, _add_days(anchor, WEEK_LENGTH_DAYS - 1)
	if view == "Month":
		return (
			_date(anchor.year, anchor.month, 1),
			_last_day_of_month(anchor.year, anchor.month),
		)
	if view == "Quarter":
		start = _quarter_start(anchor.year, ((anchor.month - 1) // 3) * 3 + 1)
		return start, _quarter_end(start)
	return _date(anchor.year, 1, 1), _date(anchor.year, 12, 31)


def advance_period(period_start, view_by):
	start = _as_date(period_start)
	view = normalise_view_by(view_by)
	if start is None or view is None:
		return None
	if view == "Week":
		return _add_days(start, WEEK_LENGTH_DAYS)
	if view == "Month":
		if start.month == 12:
			return _date(start.year + 1, 1, 1)
		return _date(start.year, start.month + 1, 1)
	if view == "Quarter":
		month = start.month + 3
		year = start.year
		if month > 12:
			month -= 12
			year += 1
		return _quarter_start(year, month)
	return _date(start.year + 1, 1, 1)


def period_label(period_start, view_by):
	start = _as_date(period_start)
	view = normalise_view_by(view_by)
	if start is None or view is None:
		return None
	if view == "Week":
		return start.isoformat()
	if view == "Month":
		return f"{start.strftime('%B')} {start.year}"
	if view == "Quarter":
		return f"Q{((start.month - 1) // 3) + 1} {start.year}"
	return str(start.year)


def rollup_periods(view_by, range_start, range_end):
	bounds = period_bounds(range_start, view_by)
	last = period_bounds(range_end, view_by)
	if bounds is None or last is None:
		return []
	periods = []
	cursor = bounds[0]
	while cursor <= last[0]:
		period = period_bounds(cursor, view_by)
		if not period:
			break
		periods.append(
			{
				"view_by": normalise_view_by(view_by),
				"label": period_label(cursor, view_by),
				"period_start": cursor.isoformat(),
				"period_end": period[1].isoformat(),
			}
		)
		cursor = advance_period(cursor, view_by)
	return periods


def recent_completed_period_starts(today=None, window=STATUS_WINDOW):
	today = _as_date(today) or _today()
	current_start = _add_days(today, -today.weekday())
	starts = []
	for index in range(window, 0, -1):
		period_start = _add_days(current_start, -WEEK_LENGTH_DAYS * index)
		if is_period_complete(period_start, today):
			starts.append(period_start)
	return starts


def scorecard_summary(statuses):
	total = len(statuses)
	on_track = sum(1 for status in statuses if status == "On Track")
	off_track = sum(1 for status in statuses if status == "Off Track")
	return {
		"total": total,
		"on_track": on_track,
		"off_track": off_track,
	}


def sort_metrics_by_group(metrics, group_orders):
	group_orders = group_orders or {}
	decorated = []
	for index, metric in enumerate(metrics or []):
		group_key = metric.get("group_key") or metric.get("group")
		if not group_key:
			decorated.append((1, 0, index, metric))
		else:
			decorated.append((0, group_orders.get(group_key, 0), index, metric))
	decorated.sort(key=lambda item: item[:3])
	return [item[3] for item in decorated]


def build_scorecard_review_lines(metrics, group_orders=None):
	lines = []
	current_group = None
	for metric in sort_metrics_by_group(metrics, group_orders):
		group_name = metric.get("group")
		if group_name != current_group:
			lines.append(group_name or "Ungrouped")
			current_group = group_name
		indicator = metric.get("status_indicator")
		label = f"  {metric.get('name')}"
		lines.append(f"{label} ({indicator})" if indicator else label)
	return lines


def default_agenda_sections():
	return [
		"Segue",
		"Scorecard Review",
		"Good News",
		"To-Dos",
		"IDS",
		"123s of the Week",
	]


def _range_status(actual_value, operator, min_value, max_value):
	if actual_value is None:
		return None
	if operator == "Inside min/max":
		if min_value is None and max_value is None:
			return None
		if _range_satisfied(actual_value, operator, min_value, max_value):
			return "On Track"
		return "Off Track"
	if operator == "Outside min/max":
		if min_value is None and max_value is None:
			return None
		if _range_satisfied(actual_value, operator, min_value, max_value):
			return "On Track"
		return "Off Track"
	return None


def _eval_ast(node):
	if isinstance(node, ast.Constant):
		if isinstance(node.value, (int, float)):
			return node.value
		raise ValueError
	if isinstance(node, ast.BinOp):
		left = _eval_ast(node.left)
		right = _eval_ast(node.right)
		if isinstance(node.op, ast.Add):
			return left + right
		if isinstance(node.op, ast.Sub):
			return left - right
		if isinstance(node.op, ast.Mult):
			return left * right
		if isinstance(node.op, ast.Div):
			return left / right
		if isinstance(node.op, ast.Mod):
			return left % right
		raise ValueError
	if isinstance(node, ast.UnaryOp):
		operand = _eval_ast(node.operand)
		if isinstance(node.op, ast.UAdd):
			return operand
		if isinstance(node.op, ast.USub):
			return -operand
		raise ValueError
	raise ValueError


def _range_satisfied(actual_value, operator, min_value, max_value):
	if operator == "Inside min/max":
		if min_value is not None and actual_value < min_value:
			return False
		if max_value is not None and actual_value > max_value:
			return False
		return True
	if operator == "Outside min/max":
		if min_value is not None and actual_value < min_value:
			return True
		if max_value is not None and actual_value > max_value:
			return True
		return False
	return None


def _range_achievement(actual_value, operator, min_value, max_value):
	if operator == "Inside min/max":
		if min_value is None and max_value is None:
			return None
		if _range_satisfied(actual_value, operator, min_value, max_value):
			return 100.0
		if min_value is not None and actual_value < min_value:
			return _clamp(actual_value / min_value * 100) if min_value else 0.0
		if max_value is not None and actual_value > max_value:
			return _clamp(max_value / actual_value * 100) if max_value else 0.0
		return None
	if operator == "Outside min/max":
		if min_value is None and max_value is None:
			return None
		if _range_satisfied(actual_value, operator, min_value, max_value):
			return 100.0
		return 0.0
	return None


def count_consecutive_off_track(statuses):
	count = 0
	for status in reversed(list(statuses)):
		if status == "Off Track":
			count += 1
		else:
			break
	return count


def build_scorecard_report(metric_blocks, trend_threshold=3):
	metrics = []
	for block in metric_blocks:
		consecutive = count_consecutive_off_track(block.get("statuses", []))
		metrics.append(
			{
				"name": block.get("name"),
				"group": block.get("group"),
				"owner": block.get("owner"),
				"actual": block.get("actual"),
				"target": block.get("target"),
				"operator": block.get("operator"),
				"unit": block.get("unit"),
				"status": block.get("status"),
				"status_indicator": compute_status_indicator(block.get("completed_statuses")),
				"consecutive_off_track": consecutive,
			}
		)
	summary = scorecard_summary([metric["status"] for metric in metrics])
	trends = [
		{"name": metric["name"], "consecutive_off_track": metric["consecutive_off_track"]}
		for metric in metrics
		if metric["consecutive_off_track"] >= trend_threshold
	]
	return {"metrics": metrics, "summary": summary, "trends": trends}


def _clamp(value):
	return min(100.0, max(0.0, value))


def quarter_bounds(anchor):
	month = getattr(anchor, "month", None)
	if month is None:
		return (None, None)
	year = getattr(anchor, "year", None)
	if year is None:
		return (None, None)
	quarter_month = ((month - 1) // 3) * 3 + 1
	start = _quarter_start(year, quarter_month)
	end = _quarter_end(start)
	return start, end


def rollup_rock_summary(rock_rows):
	total = len(rock_rows)
	active = sum(1 for rock in rock_rows if rock.get("status") not in ("Complete", "Dropped"))
	complete = sum(1 for rock in rock_rows if rock.get("status") == "Complete")
	progress_values = [rock["progress"] for rock in rock_rows if rock.get("progress") is not None]
	avg_progress = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0
	return {
		"total": total,
		"active": active,
		"complete": complete,
		"average_progress": avg_progress,
	}


def rollup_todo_summary(todo_rows, as_of=None):
	as_of = as_of or _today()
	if isinstance(as_of, str):
		import datetime as _dt

		as_of = _dt.date.fromisoformat(as_of)
	total = len(todo_rows)
	open_todos = sum(1 for todo in todo_rows if todo.get("status") not in ("Complete", "Dropped"))
	complete = sum(1 for todo in todo_rows if todo.get("status") == "Complete")
	overdue = 0
	for todo in todo_rows:
		if todo.get("status") in ("Complete", "Dropped"):
			continue
		if todo.get("due_date") and todo["due_date"] < as_of:
			overdue += 1
	return {
		"total": total,
		"open": open_todos,
		"complete": complete,
		"overdue": overdue,
	}


def build_quarterly_review(rock_rows, todo_rows, measurable_rows, as_of=None):
	rocks = rollup_rock_summary(rock_rows)
	todos = rollup_todo_summary(todo_rows, as_of=as_of)
	measurable_statuses = [
		measurable.get("status")
		for measurable in measurable_rows
		if measurable.get("status") in ("On Track", "Off Track")
	]
	measurables = scorecard_summary(measurable_statuses)
	return {
		"rocks": rocks,
		"todos": todos,
		"measurables": measurables,
	}


def _quarter_start(year, quarter_month):
	return _date(year, quarter_month, 1)


def _quarter_end(start):
	month = start.month
	last_month = month + 2
	year = start.year
	if last_month > 12:
		last_month -= 12
		year += 1
	return _last_day_of_month(year, last_month)


def _last_day_of_month(year, month):
	if month == 12:
		return _date(year, 12, 31)
	return _date(year, month + 1, 1) - _timedelta_one_day()


def _timedelta_one_day():
	import datetime as _dt

	return _dt.timedelta(days=1)


def _date(year, month, day):
	import datetime as _dt

	return _dt.date(year, month, day)


def _as_date(value):
	if value is None:
		return None
	if isinstance(value, str):
		import datetime as _dt

		try:
			return _dt.date.fromisoformat(value)
		except ValueError:
			return None
	return value.date() if hasattr(value, "date") else value


def _add_days(value, days):
	import datetime as _dt

	return value + _dt.timedelta(days=days)


def _today():
	import datetime as _dt

	return _dt.date.today()
