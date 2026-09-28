import frappe
from frappe.model.document import Document

from eos_core.eos_core.doctype.to_do.to_do import cascade_todo_transitions
from eos_core.scorecard_engine import rollup_todo_summary

ROCK_STATUSES = ("Not Started", "In Progress", "Complete", "Dropped")


class Rock(Document):
	def validate(self):
		if self.status not in ROCK_STATUSES:
			frappe.throw(f"Invalid rock status {frappe.bold(self.status)}.")
		if self.duration_end and self.duration_start and self.duration_end < self.duration_start:
			frappe.throw("Rock end date cannot be before the start date.")
		if self.status == "Complete":
			for milestone in self.milestones:
				if not milestone.completed:
					frappe.throw(
						f"Rock {frappe.bold(self.rock_name)} cannot be marked Complete while milestone "
						f"{frappe.bold(milestone.milestone_name)} is still open."
					)
		existing = frappe.db.get_value("Rock", {"rock_name": self.rock_name}, "name")
		if existing and (self.is_new() or existing != self.name):
			frappe.throw(f"A rock named {frappe.bold(self.rock_name)} already exists.")

	@property
	def progress(self):
		milestones = list(self.milestones)
		if not milestones:
			return 0
		completed = sum(1 for milestone in milestones if milestone.completed)
		return round(completed / len(milestones) * 100, 1)

	@frappe.whitelist()
	def mark_complete(self):
		for milestone in self.milestones:
			if not milestone.completed:
				frappe.throw(
					f"Milestone {frappe.bold(milestone.milestone_name)} must be Complete first."
				)
		todo_names = [
			todo.name
			for todo in frappe.get_all(
				"To Do",
				filters={
					"rock": self.name,
					"status": ["in", ("Not Started", "In Progress")],
				},
			)
		]
		self.status = "Complete"
		self.save(ignore_permissions=True)
		if todo_names:
			cascade_todo_transitions(todo_names, "Complete")
		frappe.msgprint(
			f"Rock {frappe.bold(self.rock_name)} completed; linked To-Dos closed."
		)

	@frappe.whitelist()
	def get_rock_summary(self, as_of=None):
		todos = frappe.get_all(
			"To Do", filters={"rock": self.name}, fields=["status", "due_date"]
		)
		return {
			"progress": self.progress,
			"milestones": {
				"total": len(self.milestones),
				"complete": sum(1 for milestone in self.milestones if milestone.completed),
			},
			"todos": rollup_todo_summary(todos, as_of=as_of),
			"linked_todos": len(todos),
		}
