import frappe
from frappe.model.document import Document


class Team(Document):
	def validate(self):
		self.validate_parent_team()

	def validate_parent_team(self):
		if not self.parent_team:
			return
		identity = self.name or self.team_name
		organization = self.organization
		current = self.parent_team
		seen = set()
		while current:
			if current == identity:
				frappe.throw("Team cannot be its own parent")
			if current in seen:
				break
			seen.add(current)
			parent_org, parent_team = frappe.db.get_value("Team", current, ["organization", "parent_team"])
			if organization and parent_org and parent_org != organization:
				frappe.throw("Parent team belongs to a different organization")
			current = parent_team