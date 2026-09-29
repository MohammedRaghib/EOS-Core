import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate

from eos_core.scorecard_engine import (
	READ_ONLY_VIEW_BY,
	ROLLUP_RANGE_WEEKS,
	aggregate_entries_for_period,
	normalise_view_by,
	rollup_periods,
)


class Scorecard(Document):
	def validate(self):
		self.validate_immutable_identity()
		self.validate_unique()

	def validate_immutable_identity(self):
		if self.is_new():
			return
		for fieldname in ("team", "timeframe"):
			if not self.has_value_changed(fieldname):
				continue
			label = self.meta.get_field(fieldname).label
			frappe.throw(
				f"{frappe.bold(label)} is part of a Scorecard's name and cannot be changed after it "
				"is created. Open this Scorecard, or create a Scorecard for the other value."
			)

	def validate_unique(self):
		if not self.is_new():
			return
		existing = frappe.db.get_value(
			"Scorecard", self.name, ["team", "timeframe"], as_dict=True
		)
		if not existing:
			return
		frappe.throw(
			f"Scorecard {frappe.bold(self.name)} already exists with timeframe "
			f"{frappe.bold(existing.timeframe)}. Open that Scorecard instead of creating a new one."
		)

	@frappe.whitelist()
	def get_rollup_view(self, view_by=None, range_start=None, range_end=None):
		view = normalise_view_by(view_by or self.timeframe)
		if view not in READ_ONLY_VIEW_BY:
			frappe.throw(
				"View by must be Month, Quarter or Year to read a rolled-up view of weekly data."
			)
		if self.timeframe != "Weekly":
			frappe.throw(
				f"Only the Weekly Scorecard can be rolled up. Open the team's "
				f"{frappe.bold(self.timeframe)} Scorecard to read its own data."
			)
		period_end = getdate(range_end) if range_end else nowdate()
		period_start = (
			getdate(range_start)
			if range_start
			else add_days(period_end, -ROLLUP_RANGE_WEEKS * 7)
		)
		if period_start > period_end:
			frappe.throw("The start of the date range must not be after its end.")
		periods = rollup_periods(view, period_start, period_end)
		return {
			"scorecard": self.name,
			"team": self.team,
			"view_by": view,
			"read_only": True,
			"range_start": period_start.isoformat(),
			"range_end": period_end.isoformat(),
			"periods": periods,
			"metrics": [
				self._rollup_metric(metric, periods) for metric in self._rollup_metrics()
			],
		}

	def _rollup_metrics(self):
		return frappe.get_all(
			"EOS Metric",
			filters={"scorecard": self.name, "archived": 0},
			fields=["name", "owner", "group", "target_value", "rollup"],
			order_by="name asc",
		)

	def _rollup_metric(self, metric, periods):
		entries = frappe.get_all(
			"Scorecard Entry",
			filters={"metric": metric.name},
			fields=["week_start_date", "actual_value"],
			order_by="week_start_date asc",
		)
		return {
			"name": metric.name,
			"owner": metric.owner,
			"group": metric.group,
			"goal": metric.target_value,
			"rollup": metric.rollup,
			"values": [
				{
					"period_start": period["period_start"],
					"period_end": period["period_end"],
					"value": aggregate_entries_for_period(
						entries, period["period_start"], period["period_end"], metric.rollup
					),
				}
				for period in periods
			],
		}
