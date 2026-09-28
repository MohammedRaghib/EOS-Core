import frappe
from frappe.model.document import Document

VALID_STATUS_TRANSITIONS = {
	"Identified": ["Discussing", "Solved", "Dropped"],
	"Discussing": ["Solved", "Dropped"],
	"Solved": [],
	"Dropped": [],
}


class Issue(Document):
	def validate(self):
		self.validate_status_transition()
		self.validate_solution_required()

	def validate_status_transition(self):
		if not self.is_new():
			previous = frappe.db.get_value("Issue", self.name, "status")
			if (
				previous
				and previous != self.status
				and self.status not in VALID_STATUS_TRANSITIONS.get(previous, [])
			):
				frappe.throw(
					f"Cannot transition from {frappe.bold(previous)} to {frappe.bold(self.status)}."
				)

	def validate_solution_required(self):
		if self.status == "Solved" and not self.solution:
			frappe.throw("Solved issues require a Solution.")


def create_issue_from_metric(metric_name, week_start_date=None, owner_user=None):
	metric = frappe.db.get_value(
		"EOS Metric",
		metric_name,
		["team", "frequency", "target_value", "operator"],
		as_dict=True,
	)
	if not metric:
		frappe.throw(f"Metric {frappe.bold(metric_name)} not found.")

	filters = {"metric": metric_name}
	if week_start_date:
		filters["week_start_date"] = week_start_date

	entry = frappe.get_all(
		"Scorecard Entry",
		filters=filters,
		fields=["week_start_date", "actual_value", "status"],
		order_by="week_start_date desc",
		limit=1,
	)
	if not entry:
		frappe.throw(f"No entries found for metric {frappe.bold(metric_name)}.")
	entry = entry[0]

	if entry.status == "On Track":
		frappe.throw("Cannot create an Issue from an On Track entry.")

	consecutive = count_consecutive_from_db(metric_name, entry.week_start_date)

	owner = owner_user
	if not owner:
		leader_user = leader_user_for_metric(metric)
		if leader_user:
			owner = leader_user
		else:
			owner = frappe.session.user or "Administrator"

	description_lines = [
		f"Metric: {metric_name}",
		f"Team: {metric.team or 'Organization-wide'}",
		f"Frequency: {metric.frequency}",
		f"Target: {metric.target_value} ({metric.operator})",
		f"Actual ({entry.week_start_date}): {entry.actual_value}",
		f"Status: {entry.status}",
	]
	if consecutive:
		description_lines.append(f"Consecutive Off Track: {consecutive} period(s)")

	return frappe.get_doc(
		{
			"doctype": "Issue",
			"issue_name": f"{metric_name} — {entry.week_start_date}",
			"status": "Identified",
			"priority": "Medium",
			"owner_user": owner,
			"team": metric.team,
			"source": "Scorecard",
			"originating_metric": metric_name,
			"description": "\n".join(description_lines),
		}
	).insert()


def leader_user_for_metric(metric):
	if not metric.team:
		return None
	leader_player = frappe.db.get_value("Team", metric.team, "leader")
	if not leader_player:
		return None
	return frappe.db.get_value("Player", leader_player, "user")


def count_consecutive_from_db(metric_name, as_of=None):
	filters = {"metric": metric_name}
	if as_of:
		filters["week_start_date"] = ["<=", as_of]
	statuses = frappe.get_all(
		"Scorecard Entry",
		filters=filters,
		fields=["status"],
		order_by="week_start_date asc",
		pluck="status",
	)
	from eos_core.scorecard_engine import count_consecutive_off_track

	return count_consecutive_off_track(statuses)