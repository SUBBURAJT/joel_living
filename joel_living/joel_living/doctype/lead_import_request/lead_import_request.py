# Copyright (c) 2025, Subburaj and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class LeadImportRequest(Document):
	pass



import frappe
import pandas as pd
import os

# @frappe.whitelist()
# def approve_request(docname):
#     doc = frappe.get_doc("Lead Import Request", docname)

#     added_count = 0
#     failed_count = 0
#     failed_rows = []
#     failed_reasons_set = set()

#     try:
#         # Get file path
#         file_doc = frappe.get_doc("File", {"file_url": doc.file})
#         filepath = file_doc.get_full_path()

#         # Read Excel
#         df = pd.read_excel(filepath)

#         # Import leads
#         for idx, row in df.iterrows():
#             try:
#                 lead = frappe.get_doc({
#                     "doctype": "Lead",
#                     "lead_name": row.get("First Name"),
#                     "source": row.get("Source"),
#                     "mobile_no": row.get("Mobile No"),
#                 })
#                 lead.insert(ignore_permissions=True)
#                 added_count += 1
#             except Exception as e:
#                 failed_count += 1
#                 failed_rows.append(row)
#                 failed_reasons_set.add(str(e))

#         # Save counts and reasons
#         doc.success_count = added_count
#         doc.failed_count = failed_count
#         doc.failed_reasons = ", ".join(failed_reasons_set)

#         # Generate Excel for failed leads if any
#         if failed_rows:
#             failed_df = pd.DataFrame(failed_rows)
#             failed_filepath = os.path.join(frappe.get_site_path("public", "files"), f"failed_leads_{docname}.xlsx")
#             failed_df.to_excel(failed_filepath, index=False)

#             # Attach file using File doctype
#             file_doc = frappe.get_doc({
#                 "doctype": "File",
#                 "file_name": f"failed_leads_{docname}.xlsx",
#                 "attached_to_doctype": "Lead Import Request",
#                 "attached_to_name": docname,
#                 "content": None,
#                 "file_url": f"/files/failed_leads_{docname}.xlsx",
#                 "is_private": 0
#             })
#             file_doc.save(ignore_permissions=True)
#             doc.failed_leads_file = file_doc.file_url

#         # Update status
#         if failed_count == 0:
#             doc.status = "Approved"
#         elif added_count > 0:
#             doc.status = "Partially Approved"
#         else:
#             doc.status = "Failed"

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         frappe.msgprint(f"Leads import finished: {added_count} added, {failed_count} failed.")

#         return {
#             "added": added_count,
#             "failed": failed_count,
#             "failed_reasons": doc.failed_reasons,
#             "failed_file": doc.failed_leads_file
#         }

#     except Exception as e:
#         doc.status = "Failed"
#         doc.save(ignore_permissions=True)
#         frappe.db.commit()
#         frappe.msgprint(f"Import Failed: {e}")
#         return {
#             "added": added_count,
#             "failed": len(df),
#             "failed_reasons": str(e),
#             "failed_file": None
#         }



import frappe
import pandas as pd
import os

@frappe.whitelist()
def approve_request(docname):
    # Update status to Importing...
    doc = frappe.get_doc("Lead Import Request", docname)
    doc.status = "Importing"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # Enqueue background job
    frappe.enqueue(
        "joel_living.joel_living.doctype.lead_import_request.lead_import_request.process_lead_import",
        queue="long",   # for large files
        timeout=3600,   # adjust for very large Excel
        docname=docname,
    )

    return {"status": "queued", "message": "Lead import started in background."}


def process_lead_import(docname):
    doc = frappe.get_doc("Lead Import Request", docname)

    added_count = 0
    failed_count = 0
    failed_rows = []
    failed_reasons_set = set()

    try:
        # Get file path
        file_doc = frappe.get_doc("File", {"file_url": doc.file})
        filepath = file_doc.get_full_path()

        # Read Excel
        df = pd.read_excel(filepath)

        # Import leads
        for _, row in df.iterrows():
            try:
                lead = frappe.get_doc({
                    "doctype": "Lead",
                    "first_name": row.get("First Name"),
                    "middle_name": row.get("Middle Name"),
                    "last_name": row.get("Last Name"),
                    "gender": row.get("Gender"),
                    "custom_main_lead_source": row.get("custom_main_lead_source"),
                    "job_title": row.get("Job Title"),
                    "custom_project": row.get("Project"),
                    "mobile_no": row.get("Mobile No"),
                    "email": row.get("Email"),
                    "country": row.get("Country"),
                    "state": row.get("State/Province"),
                    "city": row.get("City"),
                })
                lead.insert(ignore_permissions=True)
                added_count += 1
            except Exception as e:
                failed_count += 1
                failed_rows.append(row)
                failed_reasons_set.add(str(e))

        # Save counts and reasons
        doc.success_count = added_count
        doc.failed_count = failed_count
        doc.failed_reasons = ", ".join(failed_reasons_set)

        # Generate Excel for failed leads if any
        if failed_rows:
            failed_df = pd.DataFrame(failed_rows)
            failed_filepath = os.path.join(
                frappe.get_site_path("public", "files"),
                f"failed_leads_{docname}.xlsx"
            )
            failed_df.to_excel(failed_filepath, index=False)

            # Attach file
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": f"failed_leads_{docname}.xlsx",
                "attached_to_doctype": "Lead Import Request",
                "attached_to_name": docname,
                "file_url": f"/files/failed_leads_{docname}.xlsx",
                "is_private": 0
            })
            file_doc.save(ignore_permissions=True)
            doc.failed_leads_file = file_doc.file_url

        # Update status
        if failed_count == 0:
            doc.status = "Approved"
        elif added_count > 0:
            doc.status = "Partially Approved"
        else:
            doc.status = "Failed"

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.publish_realtime(
            "lead_import_progress",
            {"docname": docname, "status": doc.status, "added": added_count, "failed": failed_count},
            user=frappe.session.user
        )

    except Exception as e:
        doc.status = "Failed"
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.publish_realtime(
            "lead_import_progress",
            {"docname": docname, "status": "Failed", "error": str(e)},
            user=frappe.session.user
        )



@frappe.whitelist()
def reject_request(docname):
    doc = frappe.get_doc("Lead Import Request", docname)
    doc.status = "Rejected"
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint("Request Rejected")



from openpyxl import load_workbook

@frappe.whitelist()
def preview_excel(docname):
    doc = frappe.get_doc("Lead Import Request", docname)
    try:
        file_doc = frappe.get_doc("File", {"file_url": doc.file})
        filepath = file_doc.get_full_path()

        wb = load_workbook(filepath)
        ws = wb.active

        # Convert to HTML table
        html = "<table border='1' style='border-collapse: collapse; width:100%'>"

        for i, row in enumerate(ws.iter_rows(values_only=True)):
            html += "<tr>"
            for cell in row:
                tag = "th" if i == 0 else "td"
                html += f"<{tag} style='padding:4px'>{cell if cell else ''}</{tag}>"
            html += "</tr>"

        html += "</table>"
        return html

    except Exception as e:
        return f"<p style='color:red'>Error reading file: {e}</p>"


@frappe.whitelist()
def preview_failed_leads(docname):
    doc = frappe.get_doc("Lead Import Request", docname)
    if not doc.failed_leads_file:
        return "<p style='color:gray'>No failed leads</p>"

    try:
        # Get file path
        file_doc = frappe.get_doc("File", {"file_url": doc.failed_leads_file})
        filepath = file_doc.get_full_path()

        wb = load_workbook(filepath)
        ws = wb.active

        # Convert to HTML table
        html = "<table border='1' style='border-collapse: collapse; width:100%'>"
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            html += "<tr>"
            for cell in row:
                tag = "th" if i == 0 else "td"
                html += f"<{tag} style='padding:4px'>{cell if cell else ''}</{tag}>"
            html += "</tr>"
        html += "</table>"

        return html
    except Exception as e:
        return f"<p style='color:red'>Error reading failed leads file: {e}</p>"
    
    
    
@frappe.whitelist()
def reject_request(docname, reason=None):
    doc = frappe.get_doc("Lead Import Request", docname)
    doc.status = "Rejected"
    if reason:
        doc.rejected_reason = reason
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint("Request Rejected")


@frappe.whitelist()
def move_to_pending(docname):
    doc = frappe.get_doc("Lead Import Request", docname)
    doc.status = "Pending"
    doc.rejected_reason = ""  # clear previous reason if needed
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint("Lead Import Request is now Pending.")
