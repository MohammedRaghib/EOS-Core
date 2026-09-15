import frappe
from frappe.tests import IntegrationTestCase


class TestTeam(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Player")
		frappe.db.delete("Team")
		frappe.db.delete("Organization")

	def test_cycle_prevented(self):
		with self.assertRaises(frappe.ValidationError):
			doc = frappe.get_doc(
				{"doctype": "Team", "team_name": "GM Cycle", "parent_team": "GM Cycle"}
			)
			doc.insert()

	def test_org_mismatch_prevented(self):
		org_a = frappe.get_doc({"doctype": "Organization", "organization_name": "GM Org A"}).insert()
		org_b = frappe.get_doc({"doctype": "Organization", "organization_name": "GM Org B"}).insert()
		parent = frappe.get_doc(
			{"doctype": "Team", "team_name": "GM Parent", "organization": org_a.name}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			child = frappe.get_doc(
				{
					"doctype": "Team",
					"team_name": "GM Child",
					"organization": org_b.name,
					"parent_team": parent.name,
				}
			)
			child.insert()

	def test_valid_hierarchy(self):
		org = frappe.get_doc({"doctype": "Organization", "organization_name": "GM Org"}).insert()
		leadership = frappe.get_doc(
			{"doctype": "Team", "team_name": "GM Leadership", "organization": org.name}
		).insert()
		dept = frappe.get_doc(
			{
				"doctype": "Team",
				"team_name": "GM Dept",
				"organization": org.name,
				"parent_team": leadership.name,
			}
		).insert()
		self.assertEqual(dept.parent_team, leadership.name)

	def tearDown(self):
		frappe.db.delete("Player")
		frappe.db.delete("Team")
		frappe.db.delete("Organization")