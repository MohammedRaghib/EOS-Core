import frappe

ROLE_PRECEDENCE = ("Owner", "Admin", "Coach", "Manager", "Team Member", "Observer")
COMPANY_WIDE_ROLES = ("Owner", "Admin", "Coach")
OWNER_ROLES = ("Owner", "Admin", "Manager", "Team Member")
DELETE_OWN_CONTENT_ROLES = ("Manager", "Team Member")
MANAGE_METRICS_ROLES = ("Owner", "Admin", "Coach", "Manager")

TEAM_SCOPED_DOCTYPES = (
	"EOS Metric",
	"Issue",
	"Level 10 Meeting",
	"Measurable Group",
	"Player",
	"Quarterly Review",
	"Rock",
	"Scorecard",
	"Scorecard Report",
	"Team",
	"To Do",
)

DIRECT_TEAM_DOCTYPES = (
	"Scorecard",
	"Scorecard Report",
	"Level 10 Meeting",
	"Quarterly Review",
)
ORG_WIDE_TEAM_DOCTYPES = ("EOS Metric", "Issue")
OWNER_FALLBACK = {"To Do": "owner_user", "Player": "user"}
ROCK_COMPANY_SCOPE = "Company"

TEAM_MEMBER_EDITABLE_FIELDS = frozenset(
	{"entries", "description", "group", "max_value", "min_value", "target_value"}
)

SYSTEM_FIELDS = frozenset(
	{
		"modified",
		"modified_by",
		"creation",
		"docstatus",
		"idx",
		"parent",
		"parentfield",
		"parenttype",
		"_user_tags",
		"_comments",
		"_assign",
		"_seen",
	}
)


def eos_roles(user=None):
	roles = frappe.get_roles(user or frappe.session.user)
	return [role for role in ROLE_PRECEDENCE if role in roles]


def primary_role(user=None):
	roles = eos_roles(user)
	return roles[0] if roles else None


def is_privileged(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def has_company_wide_access(user=None):
	if is_privileged(user):
		return True
	return primary_role(user) in COMPANY_WIDE_ROLES


def can_manage_metrics(user=None):
	if is_privileged(user):
		return True
	return primary_role(user) in MANAGE_METRICS_ROLES


def can_own_content(user=None):
	if is_privileged(user):
		return True
	role = primary_role(user)
	return role is None or role in OWNER_ROLES


def assigned_teams(user=None):
	user = user or frappe.session.user
	teams = frappe.get_all("Player", filters={"user": user}, pluck="team")
	return {team for team in teams if team}


def team_clause(field, teams):
	if not teams:
		return "1 = 0"
	escaped = ", ".join(frappe.db.escape(team) for team in sorted(teams))
	return f"{field} in ({escaped})"


def team_query_condition(user=None, doctype=None):
	if doctype and doctype not in TEAM_SCOPED_DOCTYPES:
		return None
	user = user or frappe.session.user
	if has_company_wide_access(user):
		return None
	teams = assigned_teams(user)
	own = frappe.db.escape(user)
	if doctype == "Team":
		return team_clause("`tabTeam`.`name`", teams)
	if doctype == "Measurable Group":
		member = team_clause("`team`", teams)
		return (
			f"`tabMeasurable Group`.`scorecard` in "
			f"(select `name` from `tabScorecard` where {member} or `team` is null)"
		)
	if doctype in DIRECT_TEAM_DOCTYPES:
		return team_clause(f"`tab{doctype}`.`team`", teams)
	if doctype in ORG_WIDE_TEAM_DOCTYPES:
		member = team_clause(f"`tab{doctype}`.`team`", teams)
		return f"({member} or `tab{doctype}`.`team` is null)"
	if doctype == "Rock":
		member = team_clause("`tabRock`.`team`", teams)
		company = f"`tabRock`.`scope` = {frappe.db.escape(ROCK_COMPANY_SCOPE)}"
		return f"({member} or (`tabRock`.`team` is null and ({company} or `tabRock`.`owner_user` = {own})))"
	if doctype in OWNER_FALLBACK:
		member = team_clause(f"`tab{doctype}`.`team`", teams)
		field = OWNER_FALLBACK[doctype]
		return f"({member} or (`tab{doctype}`.`team` is null and `tab{doctype}`.`{field}` = {own}))"
	return None


def doc_in_assigned_teams(doc, teams, user):
	if doc.doctype == "Team":
		return doc.name in teams
	if doc.doctype == "Measurable Group":
		team = frappe.db.get_value("Scorecard", doc.get("scorecard"), "team")
		return not team or team in teams
	team = doc.get("team")
	if team:
		return team in teams
	if doc.doctype == "Rock":
		return doc.get("scope") == ROCK_COMPANY_SCOPE or doc.get("owner_user") == user
	if doc.doctype in OWNER_FALLBACK:
		return doc.get(OWNER_FALLBACK[doc.doctype]) == user
	return True


def has_permission(doc, ptype, user=None, debug=None):
	user = user or frappe.session.user
	if doc.doctype not in TEAM_SCOPED_DOCTYPES:
		return True
	if doc.is_new() or not doc.get("name"):
		return True
	if has_company_wide_access(user):
		return True
	return doc_in_assigned_teams(doc, assigned_teams(user), user)


def changed_setting_fields(doc):
	before = doc.get_doc_before_save()
	if not before:
		return []
	return [
		field.fieldname
		for field in doc.meta.fields
		if field.fieldname not in TEAM_MEMBER_EDITABLE_FIELDS
		and field.fieldname not in SYSTEM_FIELDS
		and field.fieldtype not in ("Table", "Table MultiSelect")
		and not field.is_virtual
		and doc.get(field.fieldname) != before.get(field.fieldname)
	]


def validate_data_entry_only(doc):
	if doc.is_new() or frappe.flags.ignore_permissions:
		return
	if can_manage_metrics():
		return
	changed = changed_setting_fields(doc)
	if not changed:
		return
	labels = ", ".join(doc.meta.get_field(fieldname).label for fieldname in changed)
	frappe.throw(
		f"{primary_role() or 'Your role'} may enter data on a Measurable but may not change {labels}. "
		f"Changing {labels} is restricted to Measurable Manager roles."
	)


def validate_content_owner(doc, fieldname, label):
	owner = doc.get(fieldname)
	if not owner or can_own_content(owner):
		return
	role = primary_role(owner) or owner
	frappe.throw(
		f"{role} cannot be assigned as the owner of a {label}. "
		f"Ownership is limited to {', '.join(OWNER_ROLES)}."
	)


def must_delete_only_own_content(user=None):
	if is_privileged(user):
		return False
	return primary_role(user) in DELETE_OWN_CONTENT_ROLES


def validate_content_deletion(doc, label, owner_field="owner"):
	if not must_delete_only_own_content():
		return
	if doc.get(owner_field) == frappe.session.user:
		return
	role = primary_role() or "Your role"
	frappe.throw(
		f"{role} may only delete a {label} they own. Deleting a {label} owned by someone else "
		f"is limited to Owner, Admin and Coach.",
		frappe.PermissionError,
	)

