import frappe
from frappe.tests import IntegrationTestCase

from eos_core.eos_core.doctype.to_do.to_do import cascade_todo_transitions


class TestToDo(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("To Do")
		frappe.db.delete("Rock")

	def test_forward_transition(self):
		todo = frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Todo Forward",
				"status": "Not Started",
				"owner_user": "Administrator",
			}
		).insert()
		todo.status = "In Progress"
		todo.save()
		todo.status = "Complete"
		todo.save()
		self.assertEqual(todo.status, "Complete")

	def test_backward_transition_rejected(self):
		todo = frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Todo Backward",
				"status": "Complete",
				"owner_user": "Administrator",
			}
		).insert()
		todo.status = "Not Started"
		with self.assertRaises(frappe.ValidationError):
			todo.save()

	def test_cascade(self):
		todo_a = frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Cascade A",
				"status": "Not Started",
				"owner_user": "Administrator",
			}
		).insert()
		todo_b = frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Cascade B",
				"status": "In Progress",
				"owner_user": "Administrator",
			}
		).insert()
		cascade_todo_transitions([todo_a.name, todo_b.name], "Complete")
		self.assertEqual(todo_a.reload().status, "Complete")
		self.assertEqual(todo_b.reload().status, "Complete")

	def test_edit_without_status_change_allowed(self):
		todo = frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Noop Edit",
				"status": "In Progress",
				"owner_user": "Administrator",
				"notes": "first",
			}
		).insert()
		todo.notes = "second"
		todo.save()
		self.assertEqual(todo.reload().status, "In Progress")
		self.assertEqual(todo.reload().notes, "second")

	def tearDown(self):
		frappe.db.delete("To Do")
		frappe.db.delete("Rock")