import frappe
from frappe.tests import IntegrationTestCase


class TestVTO(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("VTO Quarterly Rocks")
		frappe.db.delete("VTO 1 Year Plan")
		frappe.db.delete("VTO 3 Year Picture")
		frappe.db.delete("VTO Marketing Strategy")
		frappe.db.delete("VTO Core Focus")
		frappe.db.delete("VTO")
		frappe.db.delete("Organization")

	def test_one_vto_per_organization(self):
		org = frappe.get_doc({"doctype": "Organization", "organization_name": "QR VTO Org"}).insert()
		frappe.get_doc({"doctype": "VTO", "organization": org.name}).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "VTO", "organization": org.name}).insert()

	def test_sections_auto_populated(self):
		org = frappe.get_doc(
			{"doctype": "Organization", "organization_name": "QR VTO Sections Org"}
		).insert()
		vto = frappe.get_doc({"doctype": "VTO", "organization": org.name}).insert()
		self.assertEqual(len(vto.core_focus), 1)
		self.assertEqual(len(vto.marketing_strategy), 1)
		self.assertEqual(len(vto.three_year_picture), 1)
		self.assertEqual(len(vto.one_year_plan), 1)
		self.assertEqual(len(vto.quarterly_rocks), 1)
		self.assertEqual(vto.core_focus[0].purpose, "")
		self.assertEqual(vto.one_year_plan[0].target_revenue, 0.0)

	def tearDown(self):
		frappe.db.delete("VTO Quarterly Rocks")
		frappe.db.delete("VTO 1 Year Plan")
		frappe.db.delete("VTO 3 Year Picture")
		frappe.db.delete("VTO Marketing Strategy")
		frappe.db.delete("VTO Core Focus")
		frappe.db.delete("VTO")
		frappe.db.delete("Organization")