import frappe
from frappe.model.document import Document


SECTION_DEFS = [
    {
        "doctype": "VTO Core Focus",
        "fields": {
            "purpose": "",
            "niche": "",
            "ten_year_target": "",
        },
    },
    {
        "doctype": "VTO Marketing Strategy",
        "fields": {
            "threes_uniques": "",
            "process": "",
            "three_week_guarantee": "",
            "proven_process": "",
            "unaffiliated_strategy": "",
        },
    },
    {
        "doctype": "VTO 3 Year Picture",
        "fields": {
            "target_revenue": 0.0,
            "target_profit": 0.0,
            "target_employees": 0,
            "vivid_description": "",
        },
    },
    {
        "doctype": "VTO 1 Year Plan",
        "fields": {
            "target_revenue": 0.0,
            "target_profit": 0.0,
            "goals": "",
            "ten_rocks": "",
        },
    },
    {
        "doctype": "VTO Quarterly Rocks",
        "fields": {
            "quarter_date": None,
            "rocks": "",
        },
    },
]


class VTO(Document):
    def validate(self):
        existing = frappe.db.exists(
            "VTO",
            {"organization": self.organization, "name": ["!=", self.name]},
        )
        if existing:
            frappe.throw(
                f"A V/TO already exists for organization {frappe.bold(self.organization)}."
            )

    def before_insert(self):
        if not self.core_focus and not self.marketing_strategy:
            self.populate_sections()

    def populate_sections(self):
        for section_def in SECTION_DEFS:
            self.append(section_def["doctype"], section_def["fields"])
