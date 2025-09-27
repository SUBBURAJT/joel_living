# Copyright (c) 2025, Subburaj and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LeadExportRequest(Document):
	pass

import pandas as pd
import os

@frappe.whitelist()
def create_export_request(leads):
    if isinstance(leads, str):
        leads = frappe.parse_json(leads)

    doc = frappe.get_doc({
        "doctype": "Lead Export Request",
        "status": "Pending Approval",
        "requested_by": frappe.session.user,
        "requested_on": frappe.utils.now(),
        "lead_list": frappe.as_json(leads)   # Or populate child table
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name

@frappe.whitelist()
def approve_export_request(docname):
    doc = frappe.get_doc("Lead Export Request", docname)

    try:
        leads = frappe.parse_json(doc.lead_list)

        lead_docs = frappe.get_all(
            "Lead",
            filters={"name": ["in", leads]},
            fields=["name", "lead_name", "mobile_no", "email_id", "source"]
        )

        if not lead_docs:
            frappe.throw("No leads found to export")

        # Clean rows for pandas
        rows = []
        for ld in lead_docs:
            rows.append({
                "Lead ID": ld.get("name"),
                "Lead Name": ld.get("lead_name"),
                "Mobile No": ld.get("mobile_no"),
                "Email": ld.get("email_id"),
                "Source": ld.get("source")
            })

        # Convert to Excel
        import pandas as pd, os
        df = pd.DataFrame(rows)
        filepath = os.path.join(
            frappe.get_site_path("public", "files"),
            f"exported_leads_{docname}.xlsx"
        )
        df.to_excel(filepath, index=False)

        # Attach file
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"exported_leads_{docname}.xlsx",
            "attached_to_doctype": "Lead Export Request",
            "attached_to_name": docname,
            "file_url": f"/files/exported_leads_{docname}.xlsx",
            "is_private": 0
        })
        file_doc.save(ignore_permissions=True)

        # Update request
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
