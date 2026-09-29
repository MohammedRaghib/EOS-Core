import frappe

TABLES = ("EOS Metric", "Scorecard Report Metric")


def execute():
	for table in TABLES:
		if not frappe.db.has_column(table, "owner_user"):
			continue
		frappe.db.sql(
			f"update `tab{table}` set `owner_user` = `owner` "
			f"where (`owner_user` is null or `owner_user` = '') "
			f"and `owner` is not null and `owner` != ''"
		)
