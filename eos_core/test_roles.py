import frappe
from frappe.tests import IntegrationTestCase

from eos_core.roles import EOS_ROLES, ensure_roles


class TestRoles(IntegrationTestCase):
	def test_all_six_ninety_roles_exist(self):
		ensure_roles()
		for role_name in EOS_ROLES:
			self.assertTrue(frappe.db.exists("Role", role_name), role_name)

	def test_ensure_roles_creates_nothing_on_second_call(self):
		ensure_roles()
		self.assertEqual(ensure_roles(), [])

	def test_roles_are_marked_custom_with_desk_access(self):
		ensure_roles()
		for role_name in EOS_ROLES:
			role = frappe.db.get_value(
				"Role", role_name, ["is_custom", "desk_access", "disabled"], as_dict=True
			)
			self.assertEqual(role.is_custom, 1, role_name)
			self.assertEqual(role.desk_access, 1, role_name)
			self.assertEqual(role.disabled, 0, role_name)

	def test_role_list_matches_ninety_vocabulary(self):
		self.assertEqual(
			EOS_ROLES,
			["Owner", "Admin", "Coach", "Manager", "Team Member", "Observer"],
		)
