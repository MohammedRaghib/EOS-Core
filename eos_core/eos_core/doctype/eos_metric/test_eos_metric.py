import frappe
from frappe.tests import IntegrationTestCase


class TestEOSMetric(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Player")
		frappe.db.delete("Team")

	def test_auto_status_on_save(self):
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Auto Status",
				"owner": "Administrator",
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		)
		metric.append("entries", {"week_start_date": "2026-09-07", "actual_value": 80})
		metric.append("entries", {"week_start_date": "2026-09-14", "actual_value": 120})
		metric.insert()
		self.assertEqual(metric.entries[0].status, "Off Track")
		self.assertEqual(metric.entries[1].status, "On Track")
		self.assertEqual(metric.entries[0].metric, metric.name)

	def test_team_scoped_owner_rule(self):
		team = frappe.get_doc({"doctype": "Team", "team_name": "GM Leadership"}).insert()
		frappe.get_doc(
			{
				"doctype": "Player",
				"player_name": "GM Admin",
				"user": "Administrator",
				"team": team.name,
			}
		).insert()
		metric = frappe.get_doc(
			{
				"doctype": "EOS Metric",
				"metric_name": "GM Team Metric",
				"owner": "Administrator",
				"team": team.name,
				"target_value": 100,
				"operator": ">=",
				"frequency": "Weekly",
			}
		).insert()
		self.assertEqual(metric.team, team.name)
		other = frappe.get_doc({"doctype": "Team", "team_name": "GM Other"}).insert()
		with self.assertRaises(frappe.ValidationError):
			bad = frappe.get_doc(
				{
					"doctype": "EOS Metric",
					"metric_name": "GM Bad Metric",
					"owner": "Administrator",
					"team": other.name,
					"target_value": 100,
					"operator": ">=",
					"frequency": "Weekly",
				}
			)
			bad.insert()

	def tearDown(self):
		frappe.db.delete("Scorecard Entry")
		frappe.db.delete("EOS Metric")
		frappe.db.delete("Player")
		frappe.db.delete("Team")