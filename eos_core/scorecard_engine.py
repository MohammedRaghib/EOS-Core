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
	scored = [status for status in statuses or [] if status in SCORED_STATUSES]
	if not scored:
		return "No Recent Data"
	recent = scored[-window:] if window else scored
	if all(status == "On Track" for status in recent):
		return "Green"
	if all(status == "Off Track" for status in recent):
		return "Red"
	return "Yellow"


def is_period_complete(period_start, today=None):
	period_start = _as_date(period_start)
	today = _as_date(today) or _today()
	if period_start is None:
		return False
	return _add_days(period_start, WEEK_LENGTH_DAYS - 1) < today


def completed_period_statuses(entries, today=None):
	today = _as_date(today) or _today()
	dated = [
		(_as_date(entry.get("week_start_date")), entry.get("status"))
		for entry in entries or []
		if entry.get("week_start_date")
	]
	completed = [pair for pair in dated if is_period_complete(pair[0], today)]
	completed.sort(key=lambda pair: pair[0])
	return [status for _, status in completed]


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
	if elapsed > total:
		elapsed = total
	return value * elapsed / total


def scorecard_summary(statuses):
	total = len(statuses)
	on_track = sum(1 for status in statuses if status == "On Track")
	off_track = sum(1 for status in statuses if status == "Off Track")
	return {
		"total": total,
		"on_track": on_track,
		"off_track": off_track,
	}


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
