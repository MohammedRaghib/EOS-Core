import frappe
from frappe.model.document import Document

from eos_core.scorecard_engine import (
	build_scorecard_review_lines,
	completed_period_statuses,
	compute_status_indicator,
	default_agenda_sections,
	sort_metrics_by_group,
)

VALID_STATUS_TRANSITIONS = {
	"Planned": ["In Progress"],
	"In Progress": ["Complete"],
	"Complete": [],
}

SCORECARD_REVIEW_SECTION = "Scorecard Review"


class Level10Meeting(Document):
	def before_insert(self):
		if not self.get("agenda_items"):
			for section in default_agenda_sections():
				self.append(
					"agenda_items",
					{"section": section, "notes": self._section_notes(section)},
				)

	def _section_notes(self, section):
		if section != SCORECARD_REVIEW_SECTION:
			return None
		lines = build_scorecard_review_lines(self._scorecard_review_metrics())
		return "\n".join(lines) if lines else None

	def _scorecard_review_metrics(self):
		rows = frappe.get_all(
			"EOS Metric",
			filters={"archived": 0, "team": self.team},
			fields=["name", "group"],
			order_by="name asc",
		)
		details = self._group_details([row.group for row in rows])
		return sort_metrics_by_group(
			[
				{
					"name": row.name,
					"group": (details.get(row.group) or {}).get("group_name") or "",
					"group_key": row.group,
					"status_indicator": self._status_indicator(row.name),
				}
				for row in rows
			],
			{details_key: value["order"] for details_key, value in details.items()},
		)

	def _group_details(self, group_keys):
		group_keys = [key for key in group_keys if key]
		if not group_keys:
			return {}
		return {
			row.name: {"group_name": row.group_name, "order": row.order}
			for row in frappe.get_all(
				"Measurable Group",
				filters={"name": ["in", group_keys]},
				fields=["name", "group_name", "order"],
			)
		}

	def _status_indicator(self, metric_name):
		entries = frappe.get_all(
			"Scorecard Entry",
			filters={"metric": metric_name},
			fields=["week_start_date", "status"],
			order_by="week_start_date asc",
		)
		return compute_status_indicator(
			completed_period_statuses(entries, today=self.meeting_date)
		)

	def validate(self):
		self.validate_unique()
		self.validate_status_transition()

	def validate_unique(self):
		if self.is_new() and frappe.db.exists("Level 10 Meeting", self.name):
			frappe.throw(
				f"A Level 10 Meeting already exists for team {frappe.bold(self.team)} on {self.meeting_date}."
			)

	def validate_status_transition(self):
		if not self.is_new():
			previous = frappe.db.get_value("Level 10 Meeting", self.name, "status")
			if (
				previous
				and previous != self.status
				and self.status not in VALID_STATUS_TRANSITIONS.get(previous, [])
			):
				frappe.throw(
					f"Cannot transition from {frappe.bold(previous)} to {frappe.bold(self.status)}."
				)
