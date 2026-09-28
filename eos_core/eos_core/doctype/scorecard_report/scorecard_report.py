import frappe
from frappe.model.document import Document
from frappe.utils import format_datetime, get_datetime, now_datetime

from eos_core.scorecard_engine import build_scorecard_report

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
		metric_names = self._collect_metric_names()
		blocks = []
		for metric_name in metric_names:
			block = self._build_metric_block(metric_name)
			if block:
				blocks.append(block)
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
					"owner": metric["owner"],
					"actual_value": metric["actual"],
					"target_value": metric["target"],
					"status": metric["status"],
					"trend": metric["consecutive_off_track"],
				},
			)

	def _collect_metric_names(self):
		team_metric_names = frappe.get_all(
			"EOS Metric",
			filters={"archived": 0, "team": self.team},
			pluck="name",
		)
		global_metric_names = frappe.get_all(
			"EOS Metric",
			filters={"archived": 0, "team": ["is", "not set"]},
			pluck="name",
		)
		return list(dict.fromkeys(team_metric_names + global_metric_names))

	def _build_metric_block(self, metric_name):
		metric = frappe.db.get_value(
			"EOS Metric",
			metric_name,
			["owner", "group", "target_value", "operator", "unit"],
			as_dict=True,
		)
		if not metric:
			return None
		group_name = frappe.db.get_value("Measurable Group", metric.group, "group_name") or ""
		entries = self._entries_up_to(metric_name)
		latest = entries[-1] if entries else None
		return {
			"name": metric_name,
			"group": group_name,
			"owner": metric.owner,
			"actual": latest.actual_value if latest else None,
			"target": metric.target_value,
			"operator": metric.operator,
			"unit": metric.unit,
			"status": latest.status if latest else None,
			"statuses": [entry.status for entry in entries],
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
		recipient = self.recipient_user or self._default_recipient()
		if not recipient:
			frappe.throw(f"No recipient configured for team {frappe.bold(self.team)}.")
		template_path = frappe.get_app_path("eos_core", "templates", EMAIL_TEMPLATE)
		with open(template_path) as f:
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
					"owner": row.owner,
					"actual": row.actual_value,
					"target": row.target_value,
					"status": row.status,
					"trend": row.trend,
				}
				for row in self.get("report_metrics", [])
			],
		}