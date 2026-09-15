import frappe
from frappe.model.document import Document

from eos_core.scorecard_engine import default_agenda_sections

VALID_STATUS_TRANSITIONS = {
	"Planned": ["In Progress"],
	"In Progress": ["Complete"],
	"Complete": [],
}


class Level10Meeting(Document):
	def before_insert(self):
		if not self.get("agenda_items"):
			for section in default_agenda_sections():
				self.append("agenda_items", {"section": section})

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
			if previous and self.status not in VALID_STATUS_TRANSITIONS.get(previous, []):
				frappe.throw(
					f"Cannot transition from {frappe.bold(previous)} to {frappe.bold(self.status)}."
				)