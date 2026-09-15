import frappe
from frappe.model.document import Document

from eos_core.scorecard_engine import compute_status


class EOSMetric(Document):
	def validate(self):
		for entry in self.get("entries", []):
			entry.metric = entry.metric or self.metric_name
			if entry.actual_value is not None:
				entry.status = compute_status(self.target_value, entry.actual_value, self.operator)