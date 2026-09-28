import frappe
from frappe.tests import IntegrationTestCase


class TestPlayer(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Player")
		frappe.db.delete("Team")

	def test_same_user_may_hold_a_seat_in_several_teams(self):
		team_a = frappe.get_doc({"doctype": "Team", "team_name": "DP Team A"}).insert()
		team_b = frappe.get_doc({"doctype": "Team", "team_name": "DP Team B"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "DP Admin A",
				"user": "Administrator",
				"team": team_a.name,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "DP Admin B",
				"user": "Administrator",
				"team": team_b.name,
			}
		).insert()
		self.assertEqual(
			frappe.db.count("Player", {"user": "Administrator"}),
			2,
		)

	def test_duplicate_seat_in_same_team_rejected(self):
		team = frappe.get_doc({"doctype": "Team", "team_name": "DP Team C"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "DP Admin C",
				"user": "Administrator",
				"team": team.name,
			}
		).insert()
		with self.assertRaises(frappe.ValidationError) as context:
			frappe.get_doc(
				{
					"doctype": "Player",
					"player_name": "DP Admin C Duplicate",
					"user": "Administrator",
					"team": team.name,
				}
			).insert()
		self.assertIn("DP Admin C", str(context.exception))

	def test_resaving_a_seat_is_allowed(self):
		team = frappe.get_doc({"doctype": "Team", "team_name": "DP Team D"}).insert()
		player = frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "DP Admin D",
				"user": "Administrator",
				"team": team.name,
			}
		).insert()
		player.job_title = "CTO"
		player.save()
		self.assertEqual(player.job_title, "CTO")

	def test_player_without_team_is_allowed(self):
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "DP SeATless",
				"user": "Administrator",
			}
		).insert()
		self.assertEqual(
			frappe.db.count("Player", {"player_name": "DP SeATless"}),
			1,
		)

	def tearDown(self):
		frappe.db.delete("Player")
		frappe.db.delete("Team")
