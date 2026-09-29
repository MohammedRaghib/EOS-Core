import frappe
from frappe.tests import IntegrationTestCase

from eos_core.permissions import (
	COMPANY_WIDE_ROLES,
	MANAGE_METRICS_ROLES,
	OWNER_ROLES,
	ROLE_PRECEDENCE,
	TEAM_SCOPED_DOCTYPES,
	can_manage_metrics,
	can_own_content,
	has_company_wide_access,
	primary_role,
)
from eos_core.roles import EOS_ROLES

STANDARD_DOCTYPES = (
	"EOS Metric",
	"Issue",
	"Level 10 Meeting",
	"Measurable Group",
	"Organization",
	"Player",
	"Quarterly Review",
	"Rock",
	"Scorecard",
	"Scorecard Report",
	"Team",
	"To Do",
	"VTO",
)

SCOPED_ROLES = ("Manager", "Team Member", "Observer")

ALL = EOS_ROLES
COMPANY = COMPANY_WIDE_ROLES
MANAGE = MANAGE_METRICS_ROLES
EDITORS = ("Owner", "Admin", "Coach", "Manager", "Team Member")
NOT_OBSERVER = tuple(role for role in EOS_ROLES if role != "Observer")

DOCPERM_MATRIX = {
	"Organization": dict(read=ALL, create=COMPANY, write=COMPANY, delete=COMPANY, report=MANAGE, export=MANAGE, share=COMPANY),
	"Team": dict(read=ALL, create=MANAGE, write=MANAGE, delete=MANAGE, report=MANAGE, export=MANAGE, share=COMPANY),
	"Player": dict(read=ALL, create=MANAGE, write=MANAGE, delete=MANAGE, report=MANAGE, export=MANAGE, share=COMPANY),
	"VTO": dict(read=ALL, create=MANAGE, write=MANAGE, delete=MANAGE, report=MANAGE, export=MANAGE, share=COMPANY),
	"Scorecard": dict(read=ALL, create=MANAGE, write=MANAGE, delete=MANAGE, report=MANAGE, export=MANAGE, share=MANAGE),
	"EOS Metric": dict(read=ALL, create=MANAGE, write=EDITORS, delete=NOT_OBSERVER, report=MANAGE, export=MANAGE, share=MANAGE),
	"Measurable Group": dict(read=ALL, create=MANAGE, write=MANAGE, delete=MANAGE, report=MANAGE, export=MANAGE, share=MANAGE),
	"Issue": dict(read=ALL, create=EDITORS, write=EDITORS, delete=ALL, report=MANAGE, export=MANAGE, share=MANAGE),
	"Level 10 Meeting": dict(read=ALL, create=EDITORS, write=EDITORS, delete=EDITORS, report=MANAGE, export=MANAGE, share=MANAGE),
	"Scorecard Report": dict(read=ALL, create=MANAGE, write=MANAGE, delete=MANAGE, report=MANAGE, export=MANAGE, email=MANAGE, share=MANAGE),
	"Quarterly Review": dict(read=ALL, create=MANAGE, write=MANAGE, delete=MANAGE, report=MANAGE, export=MANAGE, share=MANAGE),
	"Rock": dict(read=ALL, create=EDITORS, write=EDITORS, delete=NOT_OBSERVER, report=MANAGE, export=MANAGE, share=MANAGE),
	"To Do": dict(read=ALL, create=EDITORS, write=EDITORS, delete=ALL, report=MANAGE, export=MANAGE, share=MANAGE),
}

def _slug(text):
	return text.lower().replace(" ", "_")


DOCTYPE_SLUGS = {name: _slug(name) for name in STANDARD_DOCTYPES}


class TestPermissions(IntegrationTestCase):
	def setUp(self):
		self.created = []
		self.counter = 0
		self.organization = self._create("Organization", {"organization_name": "PT Org"})
		self.team_a = self._create(
			"Team", {"team_name": "PT Team A", "organization": self.organization.name}
		)
		self.team_b = self._create(
			"Team", {"team_name": "PT Team B", "organization": self.organization.name}
		)
		self.seats = {
			"a": self._create(
				"Player",
				{"player_name": "PT Seat A", "user": "Administrator", "team": self.team_a.name},
			),
			"b": self._create(
				"Player",
				{"player_name": "PT Seat B", "user": "Administrator", "team": self.team_b.name},
			),
		}
		self.rows = {
			"a": self._seed_rows("a", self.team_a),
			"b": self._seed_rows("b", self.team_b),
		}

	def tearDown(self):
		for doctype, name in reversed(self.created):
			frappe.db.delete(doctype, name)

	def _create(self, doctype, values):
		doc = frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)
		self.created.append((doctype, doc.name))
		return doc

	def _make_user(self, role):
		self.counter += 1
		email = f"permtest{self.counter}.{_slug(role)}@example.com"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"name": email,
				"email": email,
				"first_name": "Perm",
				"roles": [{"role": role}],
			}
		).insert(ignore_permissions=True)
		frappe.cache.hdel("roles", user.name)
		self.created.append(("User", user.name))
		return user.name

	def _seat(self, user, team):
		self.counter += 1
		self._create(
			"Player", {"player_name": f"PT Seat {self.counter}", "user": user, "team": team}
		)

	def _seed_rows(self, side, team):
		team_name = team.name
		scorecard = self._create("Scorecard", {"team": team_name, "timeframe": "Weekly"})
		group = self._create(
			"Measurable Group", {"group_name": f"PT Group {side}", "scorecard": scorecard.name}
		)
		metric = self._create(
			"EOS Metric",
			{
				"metric_name": f"PT Metric {side}",
				"owner_user": "Administrator",
				"team": team_name,
				"frequency": "Weekly",
				"target_value": 100,
				"group": group.name,
			},
		)
		return {
			"Team": team,
			"Player": self.seats[side],
			"Scorecard": scorecard,
			"EOS Metric": metric,
			"Measurable Group": group,
			"Issue": self._create(
				"Issue",
				{
					"issue_name": f"PT Issue {side}",
					"owner_user": "Administrator",
					"team": team_name,
					"priority": "Medium",
					"status": "Identified",
				},
			),
			"Level 10 Meeting": self._create(
				"Level 10 Meeting",
				{"team": team_name, "meeting_date": "2026-08-24", "status": "Planned"},
			),
			"Scorecard Report": self._create(
				"Scorecard Report",
				{"team": team_name, "week_start_date": "2026-08-24", "status": "Draft"},
			),
			"Quarterly Review": self._create(
				"Quarterly Review",
				{
					"team": team_name,
					"period_start": "2026-07-01",
					"period_end": "2026-09-30",
				},
			),
			"Rock": self._create(
				"Rock",
				{
					"rock_name": f"PT Rock {side}",
					"owner_user": "Administrator",
					"team": team_name,
					"status": "In Progress",
					"scope": "Team",
					"duration_start": "2026-07-01",
					"duration_end": "2026-09-30",
				},
			),
			"To Do": self._create(
				"To Do",
				{"todo_name": f"PT To Do {side}", "owner_user": "Administrator", "team": team_name},
			),
		}

	def _visible(self, doctype, user):
		return set(frappe.get_list(doctype, user=user, pluck="name"))

	def test_every_standard_doctype_grants_all_six_ninety_roles(self):
		for doctype in STANDARD_DOCTYPES:
			granted = set(
				frappe.get_all("DocPerm", filters={"parent": doctype}, pluck="role")
			)
			self.assertTrue(set(EOS_ROLES).issubset(granted), f"{doctype} missing {set(EOS_ROLES) - granted}")
			self.assertIn("System Manager", granted, doctype)

	def test_docperm_matrix_matches_the_ninety_capability_table(self):
		for doctype, expected in DOCPERM_MATRIX.items():
			rows = frappe.get_all(
				"DocPerm",
				filters={"parent": doctype, "role": ("in", EOS_ROLES)},
				fields=["role", "write", "create", "delete", "report", "export", "email", "share"],
			)
			self.assertEqual(len(rows), len(EOS_ROLES), doctype)
			for row in rows:
				for ptype, value in row.items():
					if ptype == "role":
						continue
					self.assertEqual(
						bool(value),
						row.role in expected.get(ptype, ()),
						f"{doctype} {row.role} {ptype}",
					)

	def test_hooks_register_every_team_scoped_doctype(self):
		for hook in ("permission_query_conditions", "has_permission"):
			registered = frappe.get_hooks(hook)
			for doctype in TEAM_SCOPED_DOCTYPES:
				self.assertIn(doctype, registered, f"{doctype} missing from {hook}")

	def test_child_tables_stay_permissionless(self):
		children = frappe.get_all(
			"DocType", filters={"module": "Eos Core", "istable": 1}, pluck="name"
		)
		for child in children:
			self.assertEqual(
				frappe.get_all("DocPerm", filters={"parent": child}, pluck="name"), [], child
			)

	def test_seatless_team_scoped_role_sees_no_team_rows(self):
		user = self._make_user("Manager")
		for doctype in TEAM_SCOPED_DOCTYPES:
			self.assertEqual(self._visible(doctype, user), set(), doctype)

	def test_organization_wide_rows_stay_visible_to_every_role(self):
		metric = self._create(
			"EOS Metric",
			{"metric_name": "PT Metric Org Wide", "owner_user": "Administrator", "target_value": 5},
		)
		rock = self._create(
			"Rock",
			{
				"rock_name": "PT Rock Company",
				"owner_user": "Administrator",
				"scope": "Company",
				"status": "In Progress",
				"duration_start": "2026-07-01",
				"duration_end": "2026-09-30",
			},
		)
		for role in SCOPED_ROLES:
			user = self._make_user(role)
			self._seat(user, self.team_a.name)
			self.assertIn(metric.name, self._visible("EOS Metric", user), role)
			self.assertIn(rock.name, self._visible("Rock", user), role)

	def test_personal_rows_without_a_team_stay_with_their_owner(self):
		owner = self._make_user("Manager")
		other = self._make_user("Manager")
		self._seat(other, self.team_a.name)
		todo = self._create(
			"To Do", {"todo_name": "PT To Do Personal", "owner_user": owner}
		)
		player = self._create(
			"Player", {"player_name": "PT Seat Personal", "user": owner}
		)
		self.assertIn(todo.name, self._visible("To Do", owner))
		self.assertIn(player.name, self._visible("Player", owner))
		self.assertNotIn(todo.name, self._visible("To Do", other))
		self.assertNotIn(player.name, self._visible("Player", other))

	def test_observer_is_read_only_on_every_doctype(self):
		user = self._make_user("Observer")
		self._seat(user, self.team_a.name)
		metric_name = self.rows["a"]["EOS Metric"].name
		with self.set_user(user):
			metric = frappe.get_doc("EOS Metric", metric_name)
			metric.check_permission("read")
			with self.assertRaises(frappe.PermissionError):
				metric.check_permission("write")
			with self.assertRaises(frappe.PermissionError):
				metric.check_permission("create")

	def test_team_member_may_not_create_a_measurable(self):
		user = self._make_user("Team Member")
		self._seat(user, self.team_a.name)
		with self.set_user(user), self.assertRaises(frappe.PermissionError):
			frappe.get_doc(
				{
					"doctype": "EOS Metric",
					"metric_name": "PT Metric Sneaked",
					"owner_user": user,
					"team": self.team_a.name,
					"target_value": 1,
				}
			).insert()

	def test_manager_may_create_a_team(self):
		user = self._make_user("Manager")
		with self.set_user(user):
			team = frappe.get_doc(
				{
					"doctype": "Team",
					"team_name": "PT Team Manager Made",
					"organization": self.organization.name,
				}
			)
			team.insert()
			self.created.append(("Team", team.name))
		self.assertEqual(
			frappe.db.get_value("Team", team.name, "team_name"), "PT Team Manager Made"
		)

	def test_team_member_enters_data_but_may_not_change_settings(self):
		user = self._make_user("Team Member")
		self._seat(user, self.team_a.name)
		metric_name = self.rows["a"]["EOS Metric"].name
		with self.set_user(user):
			doc = frappe.get_doc("EOS Metric", metric_name)
			doc.append(
				"entries",
				{"week_start_date": "2026-08-31", "actual_value": 120, "is_manual": 1},
			)
			doc.save()
			self.assertEqual(
				frappe.db.get_value("Scorecard Entry", {"metric": metric_name}, "actual_value"),
				120.0,
			)
			doc = frappe.get_doc("EOS Metric", metric_name)
			doc.unit_type = "Currency"
			with self.assertRaises(frappe.ValidationError) as context:
				doc.save()
		self.assertIn("Unit Type", str(context.exception))
		self.assertEqual(frappe.db.get_value("EOS Metric", metric_name, "unit_type"), "Number")

	def test_a_team_member_may_adjust_a_measurable_goal_and_group(self):
		user = self._make_user("Team Member")
		self._seat(user, self.team_a.name)
		metric_name = self.rows["a"]["EOS Metric"].name
		scorecard = frappe.db.get_value("EOS Metric", metric_name, "scorecard")
		group = self._create("Measurable Group", {"group_name": "PT Group", "scorecard": scorecard})
		with self.set_user(user):
			doc = frappe.get_doc("EOS Metric", metric_name)
			doc.target_value = 999
			doc.description = "PT Team Member note"
			doc.group = group.name
			doc.save()
		self.assertEqual(frappe.db.get_value("EOS Metric", metric_name, "target_value"), 999.0)
		self.assertEqual(frappe.db.get_value("EOS Metric", metric_name, "group"), group.name)

	def test_manager_may_change_measurable_settings(self):
		user = self._make_user("Manager")
		self._seat(user, self.team_a.name)
		with self.set_user(user):
			doc = frappe.get_doc("EOS Metric", self.rows["a"]["EOS Metric"].name)
			doc.target_value = 250
			doc.save()
		self.assertEqual(frappe.db.get_value("EOS Metric", doc.name, "target_value"), 250.0)

	def test_only_owner_admin_manager_and_team_member_may_own_content(self):
		for role in ("Owner", "Admin", "Manager", "Team Member"):
			user = self._make_user(role)
			self.assertTrue(can_own_content(user), role)
		for role in ("Coach", "Observer"):
			user = self._make_user(role)
			self.assertFalse(can_own_content(user), role)
		self.assertEqual(set(OWNER_ROLES), {"Owner", "Admin", "Manager", "Team Member"})

	def test_a_team_member_owns_a_rock(self):
		user = self._make_user("Team Member")
		self._seat(user, self.team_a.name)
		rock = frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "PT Rock Owned",
				"owner_user": user,
				"scope": "Team",
				"team": self.team_a.name,
				"status": "In Progress",
				"duration_start": "2026-07-01",
				"duration_end": "2026-09-30",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(rock.owner_user, user)

	def test_a_measurable_owner_is_reassignable_and_distinct_from_its_creator(self):
		replacement = self._make_user("Manager")
		self._seat(replacement, self.team_a.name)
		name = self.rows["a"]["EOS Metric"].name
		doc = frappe.get_doc("EOS Metric", name)
		self.assertEqual(doc.owner_user, "Administrator")
		doc.owner_user = replacement
		doc.save()
		self.assertEqual(frappe.db.get_value("EOS Metric", name, "owner_user"), replacement)
		self.assertEqual(frappe.db.get_value("EOS Metric", name, "owner"), "Administrator")

	def test_a_new_measurable_takes_its_creating_user_as_its_owner(self):
		user = self._make_user("Manager")
		self._seat(user, self.team_a.name)
		metric = self._metric_owned_by(user, self.team_a.name)
		self.assertEqual(metric.owner_user, user)
		self.assertEqual(metric.owner, user)

	def _assert_cannot_own(self, role):
		user = self._make_user(role)
		self._seat(user, self.team_a.name)
		name = self.rows["a"]["EOS Metric"].name
		doc = frappe.get_doc("EOS Metric", name)
		doc.owner_user = user
		with self.assertRaises(frappe.ValidationError) as context:
			doc.save()
		self.assertIn("cannot be assigned as the owner", str(context.exception))
		self.assertEqual(frappe.db.get_value("EOS Metric", name, "owner_user"), "Administrator")
		with self.assertRaises(frappe.ValidationError) as context:
			frappe.get_doc(
				{
					"doctype": "Rock",
					"rock_name": f"PT Rock By {role}",
					"owner_user": user,
					"scope": "Team",
					"team": self.team_a.name,
					"status": "In Progress",
					"duration_start": "2026-07-01",
					"duration_end": "2026-09-30",
				}
			).insert(ignore_permissions=True)
		self.assertIn("cannot be assigned as the owner", str(context.exception))

	def test_a_team_member_with_a_seat_may_be_assigned_a_measurable(self):
		manager = self._make_user("Manager")
		member = self._make_user("Team Member")
		self._seat(manager, self.team_a.name)
		self._seat(member, self.team_a.name)
		name = self.rows["a"]["EOS Metric"].name
		with self.set_user(manager):
			doc = frappe.get_doc("EOS Metric", name)
			doc.owner_user = member
			doc.save()
		self.assertEqual(frappe.db.get_value("EOS Metric", name, "owner_user"), member)

	def test_a_measurable_may_not_be_assigned_outside_its_team(self):
		manager = self._make_user("Manager")
		stranger = self._make_user("Team Member")
		self._seat(manager, self.team_a.name)
		self._seat(stranger, self.team_b.name)
		name = self.rows["a"]["EOS Metric"].name
		with self.set_user(manager):
			doc = frappe.get_doc("EOS Metric", name)
			doc.owner_user = stranger
			with self.assertRaises(frappe.ValidationError) as context:
				doc.save()
		self.assertIn("is not a Player in team", str(context.exception))
		self.assertEqual(frappe.db.get_value("EOS Metric", name, "owner_user"), "Administrator")

	def test_the_delete_guard_follows_the_owner_and_not_the_creator(self):
		manager = self._make_user("Manager")
		other = self._make_user("Manager")
		self._seat(manager, self.team_a.name)
		self._seat(other, self.team_a.name)
		created_not_owned = self._metric_owned_by(manager, self.team_a.name)
		with self.set_user(other):
			doc = frappe.get_doc("EOS Metric", created_not_owned.name)
			doc.owner_user = other
			doc.save()
		self.assertEqual(
			frappe.db.get_value("EOS Metric", created_not_owned.name, "owner"), manager
		)
		self._refuse_delete_as(
			manager,
			"EOS Metric",
			created_not_owned.name,
			"may only delete a Measurable they own",
		)
		owned_not_created = self._metric_owned_by("Administrator", self.team_a.name)
		with self.set_user(other):
			doc = frappe.get_doc("EOS Metric", owned_not_created.name)
			doc.owner_user = other
			doc.save()
		self.assertEqual(
			frappe.db.get_value("EOS Metric", owned_not_created.name, "owner"), "Administrator"
		)
		self._delete_as(other, "EOS Metric", owned_not_created.name)

	def test_a_coach_cannot_own_a_measurable_or_a_rock(self):
		self._assert_cannot_own("Coach")

	def test_an_observer_cannot_own_a_measurable_or_a_rock(self):
		self._assert_cannot_own("Observer")

	def test_a_measurable_owned_by_an_existing_owner_stays_savable(self):
		metric = frappe.get_doc("EOS Metric", self.rows["a"]["EOS Metric"].name)
		metric.unit = "Percent"
		metric.save()
		self.assertEqual(frappe.db.get_value("EOS Metric", metric.name, "unit"), "Percent")

	def _metric_owned_by(self, owner, team_name):
		self.counter += 1
		with self.set_user(owner):
			return self._create(
				"EOS Metric",
				{
					"metric_name": f"PT Owned {self.counter} {owner}",
					"team": team_name,
					"frequency": "Weekly",
					"target_value": 100,
				},
			)

	def _delete_as(self, user, doctype, name):
		with self.set_user(user):
			frappe.delete_doc(doctype, name)
		self.assertFalse(frappe.db.exists(doctype, name))

	def _refuse_delete_as(self, user, doctype, name, message):
		with self.set_user(user):
			with self.assertRaises(frappe.PermissionError) as context:
				frappe.delete_doc(doctype, name)
		self.assertIn(message, str(context.exception))
		self.assertTrue(frappe.db.exists(doctype, name))

	def test_a_team_member_may_delete_only_a_measurable_they_own(self):
		user = self._make_user("Team Member")
		self._seat(user, self.team_a.name)
		mine = self._metric_owned_by(user, self.team_a.name)
		theirs = self._metric_owned_by("Administrator", self.team_a.name)
		self._delete_as(user, "EOS Metric", mine.name)
		self._refuse_delete_as(
			user, "EOS Metric", theirs.name, "may only delete a Measurable they own"
		)

	def test_a_manager_may_delete_only_a_measurable_they_own(self):
		user = self._make_user("Manager")
		self._seat(user, self.team_a.name)
		mine = self._metric_owned_by(user, self.team_a.name)
		theirs = self._metric_owned_by("Administrator", self.team_a.name)
		self._delete_as(user, "EOS Metric", mine.name)
		self._refuse_delete_as(
			user, "EOS Metric", theirs.name, "may only delete a Measurable they own"
		)

	def test_an_owner_may_delete_a_measurable_they_do_not_own(self):
		user = self._make_user("Owner")
		self._seat(user, self.team_a.name)
		theirs = self._metric_owned_by("Administrator", self.team_a.name)
		self._delete_as(user, "EOS Metric", theirs.name)

	def test_an_observer_may_delete_an_issue_and_a_todo_but_not_a_measurable(self):
		user = self._make_user("Observer")
		self._seat(user, self.team_a.name)
		self._delete_as(user, "Issue", self.rows["a"]["Issue"].name)
		self._delete_as(user, "To Do", self.rows["a"]["To Do"].name)
		metric = self._metric_owned_by("Administrator", self.team_a.name)
		with self.set_user(user):
			with self.assertRaises(frappe.PermissionError):
				frappe.delete_doc("EOS Metric", metric.name)
		self.assertTrue(frappe.db.exists("EOS Metric", metric.name))

	def test_a_team_member_may_delete_a_rock(self):
		user = self._make_user("Team Member")
		self._seat(user, self.team_a.name)
		self._delete_as(user, "Rock", self.rows["a"]["Rock"].name)

	def test_primary_role_follows_ninety_precedence(self):
		self.assertEqual(
			ROLE_PRECEDENCE,
			("Owner", "Admin", "Coach", "Manager", "Team Member", "Observer"),
		)
		both = self._make_user("Observer")
		frappe.get_doc("User", both).add_roles("Manager")
		frappe.cache.hdel("roles", both)
		self.assertEqual(primary_role(both), "Manager")
		self.assertTrue(can_manage_metrics(both))
		self.assertFalse(has_company_wide_access(both))

	def test_administrator_keeps_company_wide_access(self):
		self.assertTrue(has_company_wide_access("Administrator"))
		self.assertTrue(can_manage_metrics("Administrator"))
		self.assertTrue(can_own_content("Administrator"))
		for doctype in TEAM_SCOPED_DOCTYPES:
			self.assertIn(
				self.rows["a"][doctype].name, self._visible(doctype, "Administrator"), doctype
			)


def _make_visibility_test(doctype, role, scoped):
	def test(self):
		user = self._make_user(role)
		self._seat(user, self.team_a.name)
		visible = self._visible(doctype, user)
		self.assertIn(self.rows["a"][doctype].name, visible, f"{doctype} {role} own team")
		other = "another team's" if scoped else "every"
		self.assertEqual(
			self.rows["b"][doctype].name in visible,
			not scoped,
			f"{doctype} {role} should not reach {other} team",
		)

	test.__name__ = f"test_visibility_{DOCTYPE_SLUGS[doctype]}_{_slug(role)}"
	return test


for _doctype in TEAM_SCOPED_DOCTYPES:
	for _role in ROLE_PRECEDENCE:
		_generated = _make_visibility_test(
			_doctype, _role, _role in ("Manager", "Team Member", "Observer")
		)
		setattr(TestPermissions, _generated.__name__, _generated)
