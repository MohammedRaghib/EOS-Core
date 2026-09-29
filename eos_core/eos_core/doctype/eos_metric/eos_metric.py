import frappe
from frappe.model.document import Document

from eos_core.permissions import (
	validate_content_deletion,
	validate_content_owner,
	validate_data_entry_only,
)
from eos_core.scorecard_engine import (
	MAX_FORMULA_VARIABLES,
	compute_status,
	evaluate_formula,
	extract_variables,
	validate_formula_syntax,
)

RANGE_OPERATORS = ("Inside min/max", "Outside min/max")


class EOSMetric(Document):
	def validate(self):
		validate_data_entry_only(self)
		self.validate_owner_team()
		self.validate_owner_content_role()
		self.validate_range_target()
		self.ensure_scorecard()
		self.validate_group()
		self.validate_formula()
		self.apply_formula()
		for entry in self.get("entries", []):
			entry.metric = entry.metric or self.metric_name
			if entry.actual_value is not None and not entry.is_manual:
				entry.status = compute_status(
					self.target_value,
					entry.actual_value,
					self.operator,
					self.min_value,
					self.max_value,
				)

	def validate_owner_content_role(self):
		validate_content_owner(self, "owner", "Measurable")

	def on_trash(self):
		validate_content_deletion(self, "Measurable")

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

	def validate_range_target(self):
		if self.min_value == 0:
			self.min_value = None
		if self.max_value == 0:
			self.max_value = None
		if self.operator in RANGE_OPERATORS:
			if self.min_value is None and self.max_value is None:
				frappe.throw("Range operators require at least one of Min Value or Max Value.")
			if (
				self.min_value is not None
				and self.max_value is not None
				and self.min_value >= self.max_value
			):
				frappe.throw("Min Value must be lower than Max Value.")
		elif self.min_value is not None or self.max_value is not None:
			frappe.throw("Min Value and Max Value apply only to range operators.")

	def ensure_scorecard(self):
		if not self.team:
			return
		existing = frappe.db.get_value(
			"Scorecard",
			{"team": self.team, "timeframe": self.frequency},
			"name",
		)
		if not existing:
			scorecard = frappe.get_doc(
				{"doctype": "Scorecard", "team": self.team, "timeframe": self.frequency}
			)
			scorecard.insert()
			existing = scorecard.name
		self.scorecard = existing

	def validate_group(self):
		if not self.group:
			return
		group = frappe.db.get_value(
			"Measurable Group", self.group, ["group_name", "scorecard"], as_dict=True
		)
		if not group:
			frappe.throw(
				f"Group {frappe.bold(self.group)} no longer exists. "
				"Pick another group or clear the field before saving."
			)
		if group.scorecard != self.scorecard:
			frappe.throw(
				f"Group {frappe.bold(group.group_name)} belongs to a different Scorecard."
			)
		scorecard = frappe.db.get_value(
			"Scorecard", group.scorecard, ["team", "timeframe"], as_dict=True
		)
		if not scorecard:
			frappe.throw(
				f"Group {frappe.bold(group.group_name)} points to a Scorecard that no longer exists."
			)
		if scorecard.team != self.team or scorecard.timeframe != self.frequency:
			frappe.throw(
				f"Group {frappe.bold(group.group_name)} matches a different team or timeframe."
			)

	def validate_formula(self):
		if not self.is_smart:
			if self.formula:
				frappe.throw("Enable Formula Builder to keep a formula on this metric.")
			return
		if not self.formula:
			frappe.throw("Formula Builder requires a formula.")
		variables = extract_variables(self.formula)
		if len(variables) > MAX_FORMULA_VARIABLES:
			frappe.throw(
				f"A formula may reference at most {MAX_FORMULA_VARIABLES} metrics."
			)
		if self.metric_name in variables:
			frappe.throw("A formula cannot reference itself.")
		for variable in variables:
			target = frappe.db.get_value(
				"EOS Metric", variable, ["frequency", "archived"], as_dict=True
			)
			if not target:
				frappe.throw(
					f"Formula references missing metric {frappe.bold(variable)}."
				)
			if target.archived:
				frappe.throw(
					f"Formula references archived metric {frappe.bold(variable)}."
				)
			if target.frequency != self.frequency:
				frappe.throw(
					f"Formula references {frappe.bold(variable)} with a different frequency."
				)
		if not validate_formula_syntax(self.formula):
			frappe.throw("Formula is invalid or could not be evaluated.")

	def apply_formula(self):
		if not self.is_smart or not self.formula:
			return
		variables = extract_variables(self.formula)
		value_by_week = {}
		for variable in variables:
			rows = frappe.get_all(
				"Scorecard Entry",
				filters={"metric": variable},
				fields=["week_start_date", "actual_value"],
			)
			value_by_week[variable] = {
				str(row.week_start_date): row.actual_value for row in rows
			}
		for entry in self.get("entries", []):
			if entry.is_manual:
				continue
			entry_key = str(entry.week_start_date)
			inputs = {}
			for variable in variables:
				value = value_by_week[variable].get(entry_key)
				if value is None:
					inputs = None
					break
				inputs[variable] = value
			if inputs is None:
				continue
			entry.actual_value = evaluate_formula(self.formula, inputs)