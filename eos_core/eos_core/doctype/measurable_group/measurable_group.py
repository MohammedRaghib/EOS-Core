import frappe
from frappe.model.document import Document

MAX_GROUPS_PER_SCORECARD = 20


class MeasurableGroup(Document):
	def validate(self):
		self.validate_limit_and_name()

	def validate_limit_and_name(self):
		if not self.scorecard:
			return
		name = self.name or ""
		rows = frappe.get_all(
			"Measurable Group",
			filters={"scorecard": self.scorecard, "name": ["!=", name]},
			fields=["name", "group_name"],
		)
		if len(rows) >= MAX_GROUPS_PER_SCORECARD:
			frappe.throw(
				f"A Scorecard may have at most {MAX_GROUPS_PER_SCORECARD} groups."
			)
		for row in rows:
			if row.group_name == self.group_name:
				frappe.throw(
					f"Group {frappe.bold(self.group_name)} already exists on this Scorecard."
				)