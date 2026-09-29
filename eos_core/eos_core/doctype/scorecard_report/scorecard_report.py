import frappe
from frappe.model.document import Document
from frappe.utils import format_datetime, get_datetime, now_datetime

from eos_core.scorecard_engine import (
	build_scorecard_report,
	completed_period_statuses,
	sort_metrics_by_group,
)

TREND_THRESHOLD = 3
EMAIL_TEMPLATE = "emails/weekly_scorecard_report.html"


class ScorecardReport(Document):
	def before_insert(self):
		self.populate_snapshot()

	def validate(self):
		self.validate_unique()

	def validate_unique(self):
		if self.is_new() and frappe.db.exists("Scorecard Report", self.name):
			frappe.throw(
				f"A Scorecard Report already exists for team {frappe.bold(self.team)} on {self.week_start_date}."
			)

	def populate_snapshot(self):
		if not self.team:
			return
		metric_groups = self._collect_metric_groups()
		group_details = self._group_details(list(metric_groups.values()))
		blocks = []
		for metric_name, group_key in metric_groups.items():
			details = group_details.get(group_key) or {}
			block = self._build_metric_block(
				metric_name, group_key, details.get("group_name") or ""
			)
			if block:
				blocks.append(block)
		blocks = sort_metrics_by_group(blocks, self._group_orders(group_details))
		report = build_scorecard_report(blocks, trend_threshold=TREND_THRESHOLD)
		self.total_metrics = report["summary"]["total"]
		self.on_track = report["summary"]["on_track"]
		self.off_track = report["summary"]["off_track"]
		self.set("report_metrics", [])
		for metric in report["metrics"]:
			self.append(
				"report_metrics",
				{
					"metric": metric["name"],
					"group": metric["group"],
					"owner_user": metric["owner"],
					"actual_value": metric["actual"],
					"target_value": metric["target"],
					"status": metric["status"],
					"status_indicator": metric["status_indicator"],
					"trend": metric["consecutive_off_track"],
				},
			)

	def _collect_metric_groups(self):
		rows = frappe.get_all(
			"EOS Metric",
			filters={"archived": 0, "team": self.team},
			fields=["name", "group"],
			order_by="name asc",
		)
		global_rows = frappe.get_all(
			"EOS Metric",
			filters={"archived": 0, "team": ["is", "not set"]},
			fields=["name", "group"],
			order_by="name asc",
		)
		metric_groups = {}
		for row in rows + global_rows:
			metric_groups.setdefault(row.name, row.group)
		return metric_groups

	def _group_details(self, group_keys):
		group_keys = [key for key in group_keys if key]
		if not group_keys:
			return {}
		return {
			row.name: {"group_name": row.group_name, "order": row.order}
			for row in frappe.get_all(
				"Measurable Group",
				filters={"name": ["in", group_keys]},
				fields=["name", "group_name", "order"],
			)
		}

	def _group_orders(self, group_details):
		return {
			key: details["order"] for key, details in (group_details or {}).items()
		}

	def _build_metric_block(self, metric_name, group_key=None, group_name=""):
		metric = frappe.db.get_value(
			"EOS Metric",
			metric_name,
			["owner_user", "target_value", "operator", "unit"],
			as_dict=True,
		)
		if not metric:
			return None
		entries = self._entries_up_to(metric_name)
		latest = entries[-1] if entries else None
		return {
			"name": metric_name,
			"group": group_name,
			"group_key": group_key,
			"owner": metric.owner_user,
			"actual": latest.actual_value if latest else None,
			"target": metric.target_value,
			"operator": metric.operator,
			"unit": metric.unit,
			"status": latest.status if latest else None,
			"statuses": [entry.status for entry in entries],
			"completed_statuses": completed_period_statuses(entries, today=self.week_start_date),
		}

	def _entries_up_to(self, metric_name):
		filters = {"metric": metric_name}
		if self.week_start_date:
			filters["week_start_date"] = ["<=", self.week_start_date]
		return frappe.get_all(
			"Scorecard Entry",
			filters=filters,
			fields=["week_start_date", "actual_value", "status"],
			order_by="week_start_date asc",
		)

	@frappe.whitelist()
	def send_report(self):
		self.check_permission("email")
		recipient = self.recipient_user or self._default_recipient()
		if not recipient:
			frappe.throw(f"No recipient configured for team {frappe.bold(self.team)}.")
		template_path = frappe.get_app_path("eos_core", "templates", EMAIL_TEMPLATE)
		with open(template_path, encoding="utf-8") as f:
			template_str = f.read()
		html = frappe.render_template(template_str, self._email_context())
		frappe.sendmail(
			recipients=[recipient],
			subject=f"Weekly Scorecard Report — {self.team} ({self.week_start_date})",
			message=html,
			reference_doctype=self.doctype,
			reference_name=self.name,
		)
		self.status = "Sent"
		self.last_sent_on = now_datetime()
		self.save()

	def _default_recipient(self):
		leader_player = frappe.db.get_value("Team", self.team, "leader")
		if leader_player:
			return frappe.db.get_value("Player", leader_player, "user")
		return None

	def _email_context(self):
		return {
			"report": {
				"team": self.team,
				"week_start_date": self.week_start_date,
				"generated_on": format_datetime(get_datetime(now_datetime())),
			},
			"summary": {
				"total": self.total_metrics,
				"on_track": self.on_track,
				"off_track": self.off_track,
			},
			"trends": [
				{"name": row.metric, "consecutive_off_track": row.trend}
				for row in self.get("report_metrics", [])
				if row.trend >= TREND_THRESHOLD
			],
			"rows": [
				{
					"name": row.metric,
					"group": row.group,
					"owner": row.owner_user,
					"actual": row.actual_value,
					"target": row.target_value,
					"status": row.status,
					"status_indicator": row.status_indicator,
					"trend": row.trend,
				}
				for row in self.get("report_metrics", [])
			],
		}
