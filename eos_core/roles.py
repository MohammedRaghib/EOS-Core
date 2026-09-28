import frappe

EOS_ROLES = [
	"Owner",
	"Admin",
	"Coach",
	"Manager",
	"Team Member",
	"Observer",
]


def ensure_roles():
	return [role_name for role_name in EOS_ROLES if _ensure_role(role_name)]


def _ensure_role(role_name):
	if frappe.db.exists("Role", role_name):
		return False
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": role_name,
			"desk_access": 1,
			"is_custom": 1,
		}
	).insert(ignore_permissions=True)
	return True
