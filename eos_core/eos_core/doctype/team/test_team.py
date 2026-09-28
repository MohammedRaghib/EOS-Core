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

	def test_dangling_grandparent_raises_validation_error(self):
		org = frappe.get_doc({"doctype": "Organization", "organization_name": "GM Dangling Org"}).insert()
		grandparent = frappe.get_doc(
			{"doctype": "Team", "team_name": "GM Dangling Grandparent", "organization": org.name}
		).insert()
		parent = frappe.get_doc(
			{
				"doctype": "Team",
				"team_name": "GM Dangling Parent",
				"organization": org.name,
				"parent_team": grandparent.name,
			}
		).insert()
		child = frappe.get_doc(
			{
				"doctype": "Team",
				"team_name": "GM Dangling Child",
				"organization": org.name,
				"parent_team": parent.name,
			}
		).insert()

		frappe.delete_doc("Team", grandparent.name, force=True)

		with self.assertRaises(frappe.ValidationError) as context:
			child.team_name = "GM Dangling Child Renamed"
			child.save()
		self.assertIn(grandparent.name, str(context.exception))

	def tearDown(self):
		frappe.db.delete("Player")
		frappe.db.delete("Team")
		frappe.db.delete("Organization")