import frappe
from frappe.model.document import Document

from eos_core.scorecard_engine import compute_status


class EOSMetric(Document):
	def validate(self):
		self.validate_owner_team()
		for entry in self.get("entries", []):
			entry.metric = entry.metric or self.metric_name
			if entry.actual_value is not None:
				entry.status = compute_status(self.target_value, entry.actual_value, self.operator)

	def validate_owner_team(self):
		if not self.team or not self.owner:
			return
		if frappe.db.exists("Player", {"user": self.owner, "team": self.team}):
			return
		if not frappe.db.exists("Player", {"user": self.owner}):
			frappe.throw(
				f"Owner {frappe.bold(self.owner)} has no Player record in team {frappe.bold(self.team)}."
			)
		frappe.throw(
			f"Owner {frappe.bold(self.owner)} is not a Player in team {frappe.bold(self.team)}."
		)