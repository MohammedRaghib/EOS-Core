import frappe
from frappe.model.document import Document


class Player(Document):
	def validate(self):
		self.validate_unique_seat_in_team()

	def validate_unique_seat_in_team(self):
		if not self.user or not self.team:
			return
		existing = frappe.db.exists(
			"Player",
			{
				"user": self.user,
				"team": self.team,
				"name": ["!=", self.name],
			},
		)
		if existing:
			frappe.throw(
				f"{frappe.bold(self.user)} already holds a seat in team "
				f"{frappe.bold(self.team)} as {frappe.bold(existing)}. "
				"Edit that Player instead of adding a second one for the same team."
			)
