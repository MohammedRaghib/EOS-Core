import frappe
from frappe.tests import IntegrationTestCase

from eos_core.scorecard_engine import default_agenda_sections


class TestLevel10Meeting(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Meeting To Do")
		frappe.db.delete("Meeting Agenda Item")
		frappe.db.delete("Level 10 Meeting")
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Player")
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

	def test_scorecard_review_lists_measurables_in_group_order(self):
		self._seed_scorecard()
		meeting = frappe.get_doc(
			{
				"doctype": "Level 10 Meeting",
				"team": "L10 Review Team",
				"meeting_date": "2026-09-28",
			}
		).insert()
		notes = self._section_notes(meeting)
		self.assertEqual(
			notes.splitlines(),
			[
				"Lead Generation",
				"  L10 Leads (Green)",
				"  L10 Revenue (Green)",
				"Operations",
				"  L10 Uptime (Red)",
				"Ungrouped",
				"  L10 Ad Hoc (No Recent Data)",
			],
		)

	def test_scorecard_review_section_only_is_prefilled(self):
		self._seed_scorecard()
		meeting = frappe.get_doc(
			{
				"doctype": "Level 10 Meeting",
				"team": "L10 Review Team",
				"meeting_date": "2026-09-28",
			}
		).insert()
		other = [item for item in meeting.agenda_items if item.section != "Scorecard Review"]
		self.assertTrue(other)
		for item in other:
			self.assertIsNone(item.notes)

	def test_scorecard_review_notes_left_empty_without_metrics(self):
		frappe.get_doc({"doctype": "Team", "team_name": "L10 Bare Team"}).insert()
		meeting = frappe.get_doc(
			{
				"doctype": "Level 10 Meeting",
				"team": "L10 Bare Team",
				"meeting_date": "2026-09-28",
			}
		).insert()
		self.assertIsNone(self._section_notes(meeting))

	def test_existing_agenda_items_are_not_replaced(self):
		self._seed_scorecard()
		meeting = frappe.get_doc(
			{
				"doctype": "Level 10 Meeting",
				"team": "L10 Review Team",
				"meeting_date": "2026-09-28",
				"agenda_items": [{"section": "Segue"}],
			}
		).insert()
		self.assertEqual([item.section for item in meeting.agenda_items], ["Segue"])

	def _section_notes(self, meeting):
		item = next(row for row in meeting.agenda_items if row.section == "Scorecard Review")
		return item.notes

	def _seed_scorecard(self):
		frappe.get_doc({"doctype": "Team", "team_name": "L10 Review Team"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "L10 Review Leader",
				"user": "Administrator",
				"team": "L10 Review Team",
			}
		).insert()
		scorecard = frappe.get_doc(
			{"doctype": "Scorecard", "team": "L10 Review Team", "timeframe": "Weekly"}
		).insert()
		lead = frappe.get_doc(
			{
				"doctype": "Measurable Group",
				"group_name": "Lead Generation",
				"scorecard": scorecard.name,
				"order": 0,
			}
		).insert()
		operations = frappe.get_doc(
			{
				"doctype": "Measurable Group",
				"group_name": "Operations",
				"scorecard": scorecard.name,
				"order": 1,
			}
		).insert()
		entries = {
			"L10 Leads": (110, lead),
			"L10 Revenue": (120, lead),
			"L10 Uptime": (60, operations),
			"L10 Ad Hoc": (None, None),
		}
		for metric_name, (value, group) in entries.items():
			metric = frappe.get_doc(
				{
					"doctype": "EOS Metric",
					"metric_name": metric_name,
					"owner": "Administrator",
					"team": "L10 Review Team",
					"target_value": 100,
					"operator": ">=",
					"frequency": "Weekly",
					"group": group.name if group else None,
				}
			).insert()
			if value is not None:
				for week in ("2026-09-07", "2026-09-14", "2026-09-21"):
					metric.append("entries", {"week_start_date": week, "actual_value": value})
				metric.save()

	def tearDown(self):
		frappe.db.delete("Meeting To Do")
		frappe.db.delete("Meeting Agenda Item")
		frappe.db.delete("Level 10 Meeting")
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Player")
		frappe.db.delete("Team")
