import frappe
from frappe.model.document import Document

VALID_TODO_TRANSITIONS = {
	"Not Started": ["In Progress", "Complete", "Dropped"],
	"In Progress": ["Complete", "Dropped"],
	"Complete": [],
	"Dropped": [],
}


class ToDo(Document):
	def validate(self):
		if not self.is_new():
			previous = frappe.db.get_value("To Do", self.name, "status")
			if (
				previous
				and previous != self.status
				and self.status not in VALID_TODO_TRANSITIONS.get(previous, [])
			):
				frappe.throw(
					f"Cannot transition from {frappe.bold(previous)} to {frappe.bold(self.status)}."
				)


def cascade_todo_transitions(todo_names, status):
	for name in todo_names:
		todo = frappe.get_doc("To Do", name)
		todo.status = status
		todo.save(ignore_permissions=True)
	return todo_names