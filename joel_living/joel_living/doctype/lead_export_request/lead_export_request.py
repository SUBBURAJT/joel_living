# Copyright (c) 2025, Subburaj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd
from io import BytesIO
from datetime import datetime

class LeadExportRequest(Document):
    pass


@frappe.whitelist()
def create_export_request(leads):
    if isinstance(leads, str):
        leads = frappe.parse_json(leads)

    doc = frappe.get_doc({
        "doctype": "Lead Export Request",
        "status": "Pending Approval",
        "requested_by": frappe.session.user,
        "requested_on": frappe.utils.now(),
        "lead_list": frappe.as_json(leads)
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name


@frappe.whitelist()
def approve_export_request(docname):
    doc = frappe.get_doc("Lead Export Request", docname)

    try:
        leads = frappe.parse_json(doc.lead_list)

        # Fetch all required fields from Lead
        lead_docs = frappe.get_all(
            "Lead",
            filters={"name": ["in", leads]},
            fields=[
                "name", "lead_name", "gender", "custom_budget_range", "custom_budget_usd",
                "custom_budget_aed", "custom_priority_", "custom_lead_status as lead_status",
                "custom_project as project", "custom_developer", "custom_developer_representative",
                "custom_lead_stages", "custom_main_lead_source as main_lead_source",
                "custom_secondary_lead_sources as secondary_lead_sources",
                "custom_lead_type", "custom_lead_category as lead_category",
                "country", "state", "city",
                "email_id as email", "mobile_no", "phone_ext", "whatsapp_no as whatsapp"
            ]
        )

        if not lead_docs:
            frappe.throw("No leads found to export")

        # Prepare rows
        rows = []
        for ld in lead_docs:
            rows.append({
                "Lead ID": ld.get("name"),
                "Lead Name": ld.get("lead_name"),
                "Gender": ld.get("gender"),
                "Budget Range": ld.get("custom_budget_range"),
                "Budget Value (USD)": ld.get("custom_budget_usd"),
                "Budget converted to AED": ld.get("custom_budget_aed"),
                "Priority": ld.get("custom_priority_"),
                "Lead Status": ld.get("lead_status"),
                "Project": ld.get("project"),
                "Developer": ld.get("custom_developer"),
                "Developer Representative": ld.get("custom_developer_representative"),
                "Lead Stages": ld.get("custom_lead_stages"),
                "Main Lead Source": ld.get("main_lead_source"),
                "Secondary Lead Sources": ld.get("secondary_lead_sources"),
                "Lead Type": ld.get("custom_lead_type"),
                "Lead Category": ld.get("lead_category"),
                "Country": ld.get("country"),
                "State/Province": ld.get("state"),
                "City": ld.get("city"),
                "Email": ld.get("email"),
                "Mobile No": ld.get("mobile_no"),
                "Secondary Phone": ld.get("phone_ext"),
                "WhatsApp": ld.get("whatsapp")
            })

        # Generate Excel in memory
        df = pd.DataFrame(rows)
        from io import BytesIO
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        file_name = f"exported_leads_{docname}_{timestamp}.xlsx"

        # Check existing file attached
        existing_file = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Lead Export Request",
                "attached_to_name": docname
            },
            limit=1
        )

        if existing_file:
            file_doc = frappe.get_doc("File", existing_file[0].name)
            file_doc.file_name = file_name
            file_doc.content = output.getvalue()
            file_doc.save(ignore_permissions=True)
        else:
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": "Lead Export Request",
                "attached_to_name": docname,
                "is_private": 1,
                "content": output.getvalue()
            })
            file_doc.insert(ignore_permissions=True)

        # Update Lead Export Request
        doc.export_file = file_doc.file_url
        doc.status = "Approved"
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "file": doc.export_file}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Lead Export Failed")
        doc.status = "Failed"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "failed", "error": str(e)}



@frappe.whitelist()
def reject_export_request(docname, rejected_notes):
    doc = frappe.get_doc("Lead Export Request", docname)
    doc.status = "Rejected"
    doc.rejected_notes = rejected_notes
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "rejected"}
