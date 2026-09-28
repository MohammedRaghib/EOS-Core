import frappe
from frappe.model.document import Document

from eos_core.scorecard_engine import build_quarterly_review


class QuarterlyReview(Document):
	def before_insert(self):
		self.populate_snapshot()

	def validate(self):
		if self.period_end and self.period_start and self.period_end < self.period_start:
			frappe.throw("Period end cannot be before the period start.")
		existing = frappe.db.get_value(
			"Quarterly Review",
			{"team": self.team, "period_start": self.period_start},
			"name",
		)
		if existing and (self.is_new() or existing != self.name):
			frappe.throw(
				f"A Quarterly Review already exists for team {frappe.bold(self.team)} for this period."
			)

	def populate_snapshot(self):
		if not self.team:
			return
		review = build_quarterly_review(
			self._rock_rows(), self._todo_rows(), self._measurable_rows(), as_of=self.period_end
		)
		rocks = review["rocks"]
		todos = review["todos"]
		measurables = review["measurables"]
		self.rock_total = rocks["total"]
		self.rock_active = rocks["active"]
		self.rock_complete = rocks["complete"]
		self.rock_avg_progress = rocks["average_progress"]
		self.todo_total = todos["total"]
		self.todo_open = todos["open"]
		self.todo_complete = todos["complete"]
		self.todo_overdue = todos["overdue"]
		self.measurable_total = measurables["total"]
		self.measurable_on_track = measurables["on_track"]
		self.measurable_off_track = measurables["off_track"]

	def _rock_rows(self):
		company_rocks = frappe.get_all(
			"Rock",
			filters={
				"scope": "Company",
				"duration_start": ["<=", self.period_end],
				"duration_end": [">=", self.period_start],
			},
			fields=["name", "status"],
		)
		team_rocks = frappe.get_all(
			"Rock",
			filters={
				"team": self.team,
				"duration_start": ["<=", self.period_end],
				"duration_end": [">=", self.period_start],
			},
			fields=["name", "status"],
		)
		by_name = {}
		for rock in company_rocks + team_rocks:
			by_name.setdefault(rock.name, rock)
		rows = []
		for rock in by_name.values():
			milestones = frappe.get_all(
				"Rock Milestone",
				filters={"parenttype": "Rock", "parent": rock.name},
				fields=["completed"],
			)
			progress = 0.0
			if milestones:
				progress = round(
					sum(1 for m in milestones if m.completed) / len(milestones) * 100, 1
				)
			rows.append({"status": rock.status, "progress": progress})
		return rows

	def _todo_rows(self):
		return frappe.get_all(
			"To Do",
			filters=[
				["team", "in", (self.team, None)],
				["due_date", ">=", self.period_start],
				["due_date", "<=", self.period_end],
			],
			fields=["status", "due_date"],
		)

	def _measurable_rows(self):
		metric_names = frappe.get_all(
			"EOS Metric",
			filters={"archived": 0, "team": ["in", (self.team, None)]},
			pluck="name",
		)
		rows = []
		for metric_name in metric_names:
			entry = frappe.get_all(
				"Scorecard Entry",
				filters={
					"metric": metric_name,
					"week_start_date": ["between", (self.period_start, self.period_end)],
				},
				fields=["status"],
				order_by="week_start_date desc",
				limit=1,
			)
			if entry:
				rows.append({"status": entry[0].status})
		return rows