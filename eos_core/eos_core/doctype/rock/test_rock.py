import frappe
from frappe.tests import IntegrationTestCase


class TestRock(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("To Do")
		frappe.db.delete("Rock")
		frappe.db.delete("Team")

	def test_rock_name_unique(self):
		frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Rock",
				"status": "Not Started",
				"owner_user": "Administrator",
				"duration_start": "2026-09-01",
				"duration_end": "2026-11-30",
			}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Rock",
					"rock_name": "QR Rock",
					"status": "Not Started",
					"owner_user": "Administrator",
					"duration_start": "2026-09-01",
					"duration_end": "2026-11-30",
				}
			).insert()

	def test_complete_rejected_while_milestone_open(self):
		rock = frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Milestone Gate",
				"status": "Not Started",
				"owner_user": "Administrator",
				"duration_start": "2026-09-01",
				"duration_end": "2026-11-30",
			}
		)
		rock.append("milestones", {"milestone_name": "M1", "completed": 0})
		rock.insert()
		rock.status = "Complete"
		with self.assertRaises(frappe.ValidationError):
			rock.save()

	def test_invalid_status(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Rock",
					"rock_name": "QR Bad Status",
					"status": "Banana",
					"owner_user": "Administrator",
					"duration_start": "2026-09-01",
					"duration_end": "2026-11-30",
				}
			).insert()

	def test_mark_complete_closes_linked_todos(self):
		rock = frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Cascade",
				"status": "Not Started",
				"owner_user": "Administrator",
				"duration_start": "2026-09-01",
				"duration_end": "2026-11-30",
			}
		)
		rock.append("milestones", {"milestone_name": "M1", "completed": 1})
		rock.insert()
		todo = frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Cascade Task",
				"status": "Not Started",
				"owner_user": "Administrator",
				"rock": rock.name,
			}
		).insert()
		rock.mark_complete()
		self.assertEqual(todo.reload().status, "Complete")

	def test_summary_counts_linked_todos(self):
		rock = frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Summary",
				"status": "In Progress",
				"owner_user": "Administrator",
				"duration_start": "2026-09-01",
				"duration_end": "2026-11-30",
			}
		)
		rock.append("milestones", {"milestone_name": "M1", "completed": 1})
		rock.append("milestones", {"milestone_name": "M2", "completed": 0})
		rock.insert()
		frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Summary Open Task",
				"status": "In Progress",
				"owner_user": "Administrator",
				"rock": rock.name,
				"due_date": "2026-10-15",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Summary Done Task",
				"status": "Complete",
				"owner_user": "Administrator",
				"rock": rock.name,
				"due_date": "2026-10-15",
			}
		).insert()

		summary = rock.get_rock_summary(as_of="2026-09-28")
		later = rock.get_rock_summary(as_of="2026-11-01")

		self.assertEqual(summary["progress"], 50.0)
		self.assertEqual(summary["milestones"], {"total": 2, "complete": 1})
		self.assertEqual(summary["todos"], {"total": 2, "open": 1, "complete": 1, "overdue": 0})
		self.assertEqual(summary["linked_todos"], 2)
		self.assertEqual(later["todos"]["overdue"], 1)

	def tearDown(self):
		frappe.db.delete("To Do")
		frappe.db.delete("Rock")
		frappe.db.delete("Team")