def compute_status(target_value, actual_value, operator):
	if actual_value is None:
		return None
	if target_value is None:
		return "On Track"
	if operator == ">=":
		return "On Track" if actual_value >= target_value else "Off Track"
	if operator == "<=":
		return "On Track" if actual_value <= target_value else "Off Track"
	if operator == "==":
		return "On Track" if actual_value == target_value else "Off Track"
	return "Off Track"


def compute_achievement(target_value, actual_value, operator):
	if actual_value is None or target_value is None or target_value == 0:
		return None
	if operator == ">=":
		return _clamp(actual_value / target_value * 100)
	if operator == "<=":
		return _clamp(target_value / actual_value * 100)
	if operator == "==":
		return _clamp((1 - abs(target_value - actual_value) / abs(target_value)) * 100)
	return None


def compute_health(target_value, actual_value, operator, tolerance=0.1):
	if actual_value is None or target_value is None or target_value == 0:
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


def _clamp(value):
	return min(100.0, max(0.0, value))