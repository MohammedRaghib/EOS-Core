import frappe
from frappe.tests import IntegrationTestCase


class TestScorecard(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Team")

	def test_unique_team_timeframe(self):
		frappe.get_doc({"doctype": "Team", "team_name": "SC Team"}).insert()
		first = frappe.get_doc({"doctype": "Scorecard", "team": "SC Team", "timeframe": "Weekly"}).insert()
		self.assertEqual(first.name, "SC Team-Weekly")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "Scorecard", "team": "SC Team", "timeframe": "Weekly"}).insert()

	def test_group_limit_and_unique_name(self):
		frappe.get_doc({"doctype": "Team", "team_name": "SC Group Team"}).insert()
		scorecard = frappe.get_doc({"doctype": "Scorecard", "team": "SC Group Team", "timeframe": "Weekly"}).insert()
		for number in range(1, 21):
			frappe.get_doc(
				{
					"doctype": "Measurable Group",
					"group_name": f"SC Group {number}",
					"scorecard": scorecard.name,
				}
			).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Measurable Group",
					"group_name": "SC Group 21",
					"scorecard": scorecard.name,
				}
			).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Measurable Group",
					"group_name": "SC Group 1",
					"scorecard": scorecard.name,
				}
			).insert()

	def tearDown(self):
		frappe.db.delete("Measurable Group")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Team")
