import frappe
from frappe.tests import IntegrationTestCase


class TestQuarterlyReview(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("VTO Quarterly Rocks")
		frappe.db.delete("To Do")
		frappe.db.delete("Rock Milestone")
		frappe.db.delete("Rock")
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Quarterly Review")
		frappe.db.delete("Player")
		frappe.db.delete("Team")
		frappe.db.delete("Organization")

	def test_snapshot_counts(self):
		org = frappe.get_doc({"doctype": "Organization", "organization_name": "QR Snapshot Org"}).insert()
		team = frappe.get_doc({"doctype": "Team", "team_name": "QR Snapshot Team", "organization": org.name}).insert()

		rock = frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Snapshot Rock",
				"status": "Complete",
				"owner_user": "Administrator",
				"duration_start": "2026-09-01",
				"duration_end": "2026-11-30",
			}
		)
		rock.append("milestones", {"milestone_name": "M1", "completed": 1})
		rock.append("milestones", {"milestone_name": "M2", "completed": 1})
		rock.insert()

		frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Snapshot Todo",
				"status": "In Progress",
				"owner_user": "Administrator",
				"team": team.name,
				"due_date": "2026-11-15",
			}
		).insert()

		frappe.get_doc(
			{"doctype": "Player", "player_name": "QR Snapshot Player", "user": "Administrator", "team": team.name}
		).insert()

		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "QR Snapshot Metric",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"unit": "count",
			}
		)
		metric.append(
			"entries",
			{"week_start_date": "2026-10-05", "actual_value": 80},
		)
		metric.insert()

		review = frappe.get_doc(
			{
				"doctype": "Quarterly Review",
				"team": team.name,
				"period_start": "2026-10-01",
				"period_end": "2026-12-31",
			}
		).insert()

		self.assertEqual(review.rock_total, 1)
		self.assertEqual(review.rock_complete, 1)
		self.assertEqual(review.rock_avg_progress, 100.0)
		self.assertEqual(review.todo_total, 1)
		self.assertEqual(review.todo_open, 1)
		self.assertEqual(review.measurable_total, 1)
		self.assertEqual(review.measurable_off_track, 1)

	def test_review_scopes_rocks_to_company_and_own_team(self):
		org = frappe.get_doc({"doctype": "Organization", "organization_name": "QR Scope Org"}).insert()
		team = frappe.get_doc({"doctype": "Team", "team_name": "QR Scope Team", "organization": org.name}).insert()
		other = frappe.get_doc({"doctype": "Team", "team_name": "QR Other Team", "organization": org.name}).insert()

		frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Company Rock",
				"status": "In Progress",
				"owner_user": "Administrator",
				"scope": "Company",
				"duration_start": "2026-10-01",
				"duration_end": "2026-12-31",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Team Rock",
				"status": "In Progress",
				"owner_user": "Administrator",
				"scope": "Team",
				"team": team.name,
				"duration_start": "2026-10-01",
				"duration_end": "2026-12-31",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Other Team Rock",
				"status": "In Progress",
				"owner_user": "Administrator",
				"scope": "Team",
				"team": other.name,
				"duration_start": "2026-10-01",
				"duration_end": "2026-12-31",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Out Of Period Rock",
				"status": "In Progress",
				"owner_user": "Administrator",
				"scope": "Company",
				"duration_start": "2026-01-01",
				"duration_end": "2026-03-31",
			}
		).insert()

		review = frappe.get_doc(
			{
				"doctype": "Quarterly Review",
				"team": team.name,
				"period_start": "2026-10-01",
				"period_end": "2026-12-31",
			}
		).insert()

		self.assertEqual(review.rock_total, 2)

	def test_company_rock_on_own_team_counted_once(self):
		org = frappe.get_doc({"doctype": "Organization", "organization_name": "QR Dedupe Org"}).insert()
		team = frappe.get_doc(
			{"doctype": "Team", "team_name": "QR Dedupe Team", "organization": org.name}
		).insert()
		frappe.get_doc(
			{
				"doctype": "Rock",
				"rock_name": "QR Both Scope Rock",
				"status": "In Progress",
				"owner_user": "Administrator",
				"scope": "Company",
				"team": team.name,
				"duration_start": "2026-10-01",
				"duration_end": "2026-12-31",
			}
		).insert()

		review = frappe.get_doc(
			{
				"doctype": "Quarterly Review",
				"team": team.name,
				"period_start": "2026-10-01",
				"period_end": "2026-12-31",
			}
		).insert()

		self.assertEqual(review.rock_total, 1)
		self.assertEqual(review.rock_active, 1)
		self.assertEqual(review.rock_complete, 0)

	def test_overdue_relative_to_period_end(self):
		org = frappe.get_doc({"doctype": "Organization", "organization_name": "QR Overdue Org"}).insert()
		team = frappe.get_doc({"doctype": "Team", "team_name": "QR Overdue Team", "organization": org.name}).insert()

		frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Overdue In Period",
				"status": "In Progress",
				"owner_user": "Administrator",
				"team": team.name,
				"due_date": "2026-11-30",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Due At Period End",
				"status": "In Progress",
				"owner_user": "Administrator",
				"team": team.name,
				"due_date": "2026-12-31",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "To Do",
				"todo_name": "QR Outside Window",
				"status": "In Progress",
				"owner_user": "Administrator",
				"team": team.name,
				"due_date": "2026-01-15",
			}
		).insert()

		review = frappe.get_doc(
			{
				"doctype": "Quarterly Review",
				"team": team.name,
				"period_start": "2026-10-01",
				"period_end": "2026-12-31",
			}
		).insert()

		self.assertEqual(review.todo_total, 2)
		self.assertEqual(review.todo_overdue, 1)

	def test_duplicate_period_rejected(self):
		org = frappe.get_doc({"doctype": "Organization", "organization_name": "QR Dup Org"}).insert()
		team = frappe.get_doc({"doctype": "Team", "team_name": "QR Dup Team", "organization": org.name}).insert()
		frappe.get_doc(
			{
				"doctype": "Quarterly Review",
				"team": team.name,
				"period_start": "2026-10-01",
				"period_end": "2026-12-31",
			}
		).insert()
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Quarterly Review",
					"team": team.name,
					"period_start": "2026-10-01",
					"period_end": "2026-12-31",
				}
			).insert()

	def tearDown(self):
		frappe.db.delete("VTO Quarterly Rocks")
		frappe.db.delete("To Do")
		frappe.db.delete("Rock Milestone")
		frappe.db.delete("Rock")
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Scorecard")
		frappe.db.delete("Quarterly Review")
		frappe.db.delete("Player")
		frappe.db.delete("Team")
		frappe.db.delete("Organization")