import ast
import re

MAX_FORMULA_VARIABLES = 25
VARIABLE_PATTERN = re.compile(r"{([^{}\n]+)}")
_SAFE_EXPRESSION = re.compile(r"^[\d\.\+\-\*\/\(\)\%\s]+$")


def compute_status(target_value, actual_value, operator, min_value=None, max_value=None):
	if actual_value is None:
		return None
	if operator in ("Inside min/max", "Outside min/max"):
		return "On Track" if _range_satisfied(actual_value, operator, min_value, max_value) else "Off Track"
	if target_value is None:
		return "On Track"
	if operator == ">=":
		return "On Track" if actual_value >= target_value else "Off Track"
	if operator == "<=":
		return "On Track" if actual_value <= target_value else "Off Track"
	if operator == "==":
		return "On Track" if actual_value == target_value else "Off Track"
	return "Off Track"


def compute_achievement(target_value, actual_value, operator, min_value=None, max_value=None):
	if actual_value is None:
		return None
	if operator in ("Inside min/max", "Outside min/max"):
		return _range_achievement(actual_value, operator, min_value, max_value)
	if target_value is None or target_value == 0:
		return None
	if operator == ">=":
		return _clamp(actual_value / target_value * 100)
	if operator == "<=":
		return _clamp(target_value / actual_value * 100)
	if operator == "==":
		return _clamp((1 - abs(target_value - actual_value) / abs(target_value)) * 100)
	return None


def compute_health(
	target_value, actual_value, operator, tolerance=0.1, min_value=None, max_value=None
):
	if actual_value is None:
		return None
	if operator == "Inside min/max":
		if min_value is None and max_value is None:
			return None
		if _range_satisfied(actual_value, operator, min_value, max_value):
			return "Green"
		if min_value is not None and actual_value < min_value:
			ratio = actual_value / min_value if min_value else 0.0
			return "Yellow" if ratio >= 1 - tolerance else "Red"
		if max_value is not None and actual_value > max_value:
			ratio = max_value / actual_value if actual_value else 0.0
			return "Yellow" if ratio >= 1 - tolerance else "Red"
		return None
	if operator == "Outside min/max":
		if _range_satisfied(actual_value, operator, min_value, max_value):
			return "Green"
		if min_value is not None and max_value is not None:
			width = max_value - min_value
			if width <= 0:
				return "Red"
			distance = min(actual_value - min_value, max_value - actual_value)
			return "Yellow" if distance / width <= tolerance else "Red"
		if min_value is not None:
			return "Yellow" if actual_value <= min_value * (1 + tolerance) else "Red"
		if max_value is not None:
			return "Yellow" if actual_value >= max_value * (1 - tolerance) else "Red"
		return None
	if target_value is None or target_value == 0:
		return None
	if operator == ">=":
		ratio = actual_value / target_value
		if ratio >= 1:
			return "Green"
		return "Yellow" if ratio >= 1 - tolerance else "Red"
	if operator == "<=":
		ratio = actual_value / target_value
		if ratio <= 1:
			return "Green"
		return "Yellow" if ratio <= 1 + tolerance else "Red"
	if operator == "==":
		deviation = abs(target_value - actual_value) / abs(target_value)
		if deviation == 0:
			return "Green"
		return "Yellow" if deviation <= tolerance else "Red"
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


def evaluate_formula(formula, variables):
	if not formula:
		return None
	tokens = extract_variables(formula)
	if len(tokens) > MAX_FORMULA_VARIABLES:
		return None
	payload = formula
	for token in tokens:
		value = variables.get(token)
		if value is None:
			return None
		payload = payload.replace("{" + token + "}", str(float(value)))
	if not _SAFE_EXPRESSION.match(payload):
		return None
	try:
		tree = ast.parse(payload, mode="eval")
	except SyntaxError:
		return None
	for node in ast.walk(tree):
		if isinstance(node, ast.Name):
			return None
	try:
		return eval(compile(tree, "<formula>", "eval"), {"__builtins__": {}})
	except Exception:
		return None


def prorate_for_period(value, covered_days, period_days):
	if value is None or not period_days or period_days <= 0:
		return None
	ratio = min(1.0, max(0.0, covered_days / period_days))
	return value * ratio


def count_consecutive_off_track(statuses):
	count = 0
	for status in reversed(list(statuses)):
		if status == "Off Track":
			count += 1
		else:
			break
	return count


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
		if min_value is not None and max_value is not None:
			mid = (min_value + max_value) / 2
			half = (max_value - min_value) / 2
			if half == 0:
				return 0.0
			return _clamp(abs(actual_value - mid) / half * 100)
		if min_value is not None:
			return _clamp(min_value / actual_value * 100) if min_value else 0.0
		if max_value is not None:
			return _clamp(actual_value / max_value * 100) if max_value else 0.0
		return None
	return None


def _clamp(value):
	return min(100.0, max(0.0, value))