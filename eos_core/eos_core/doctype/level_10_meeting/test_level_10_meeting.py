import frappe
from frappe.tests import IntegrationTestCase

from eos_core.scorecard_engine import default_agenda_sections


class TestLevel10Meeting(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Meeting To Do")
		frappe.db.delete("Meeting Agenda Item")
		frappe.db.delete("Level 10 Meeting")
		frappe.db.delete("Team")

	def test_default_agenda_and_name(self):
		frappe.get_doc({"doctype": "Team", "team_name": "L10 Team"}).insert()
		meeting = frappe.get_doc(
			{
				"doctype": "Level 10 Meeting",
				"team": "L10 Team",
				"meeting_date": "2026-09-14",
			}
		).insert()
		self.assertEqual(
			[item.section for item in meeting.agenda_items], default_agenda_sections()
		)
		self.assertEqual(meeting.status, "Planned")
		self.assertEqual(meeting.name, "L10 Team-2026-09-14")

	def test_unique_team_date(self):
		frappe.get_doc({"doctype": "Team", "team_name": "L10 Dupe Team"}).insert()
		frappe.get_doc(
			{
				"doctype": "Level 10 Meeting",
				"team": "L10 Dupe Team",
				"meeting_date": "2026-09-14",
			}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Level 10 Meeting",
					"team": "L10 Dupe Team",
					"meeting_date": "2026-09-14",
				}
			).insert()

	def test_status_transitions(self):
		frappe.get_doc({"doctype": "Team", "team_name": "L10 Status Team"}).insert()
		meeting = frappe.get_doc(
			{
				"doctype": "Level 10 Meeting",
				"team": "L10 Status Team",
				"meeting_date": "2026-09-14",
			}
		).insert()
		meeting.status = "In Progress"
		meeting.save()
		meeting.status = "Complete"
		meeting.save()
		meeting.status = "In Progress"
		with self.assertRaises(frappe.ValidationError):
			meeting.save()

	def tearDown(self):
		frappe.db.delete("Meeting To Do")
		frappe.db.delete("Meeting Agenda Item")
		frappe.db.delete("Level 10 Meeting")
		frappe.db.delete("Team")