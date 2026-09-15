import frappe
from frappe.model.document import Document


class Scorecard(Document):
	def validate(self):
		self.validate_unique()

	def validate_unique(self):
		if self.is_new():
			if frappe.db.exists("Scorecard", self.name):
				frappe.throw(
					f"A Scorecard already exists for team {frappe.bold(self.team)} and {self.timeframe} timeframe."
				)
			return
		if not (self.has_value_changed("team") or self.has_value_changed("timeframe")):
			return
		existing = frappe.db.get_value(
			"Scorecard",
			{"team": self.team, "timeframe": self.timeframe, "name": ["!=", self.name]},
			"name",
		)
		if existing:
			frappe.throw(
				f"A Scorecard already exists for team {frappe.bold(self.team)} and {self.timeframe} timeframe."
			)