frappe.ui.form.on("Admin Settings", {
    onload(frm) {
        render_user_restrictions(frm);
    },
    refresh(frm) {
        render_user_restrictions(frm);
    }
});

function parseArrayField(val) {
    if (!val && val !== "") return [];
    try {
        if (Array.isArray(val)) return val.map(String).filter(Boolean);
        if (typeof val === "string") {
            const s = val.trim();
            if (!s) return [];
            if ((s.startsWith("[") && s.endsWith("]")) || (s.startsWith("{") && s.endsWith("}"))) {
                const parsed = JSON.parse(s);
                if (Array.isArray(parsed)) return parsed.map(String).filter(Boolean);
                if (typeof parsed === "string") return [parsed.trim()];
                return [];
            }
            return s.split(",").map(x => x.trim()).filter(Boolean);
        }
        return [String(val).trim()];
    } catch (e) {
        console.error("parseArrayField error", e, val);
        return [];
    }
}

function render_user_restrictions(frm) {
    const container = frm.fields_dict.user_lead_restrictions_html.$wrapper;
    container.empty();

    let html = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <h4 style="margin:0; font-weight:500;">User Lead Restrictions</h4>
        <button class="btn btn-sm btn-success add-row">Add Restriction</button>
    </div>
    <table class="table table-bordered" style="border-collapse:collapse; width:100%; font-size:14px;">
        <thead>
            <tr style="background:#f9f9f9;">
                <th style="padding:8px; text-align:left;">User</th>
                <th style="padding:8px; text-align:left;">Lead Categories</th>
                <th style="padding:8px; text-align:left;">Main Lead Sources</th>
                <th style="padding:8px; width:130px;">Actions</th>
            </tr>
        </thead>
        <tbody>`;

    (frm.doc.user_lead_restrictions || []).forEach(row => {
        const categories = parseArrayField(row.lead_category)
            .map(c => `<span style="display:inline-block; background:#e0f0ff; color:#007bff; padding:2px 6px; margin:1px; border-radius:4px; font-size:12px;">${c}</span>`).join(" ");
        const sources = parseArrayField(row.main_lead_source)
            .map(s => `<span style="display:inline-block; background:#f0f0f0; color:#555; padding:2px 6px; margin:1px; border-radius:4px; font-size:12px;">${s}</span>`).join(" ");

        html += `<tr>
            <td style="padding:8px;">${row.user || ""}</td>
            <td style="padding:8px;">${categories}</td>
            <td style="padding:8px;">${sources}</td>
            <td style="padding:8px;">
                <button class="btn btn-xs btn-primary edit-row" data-user="${row.user}">Edit</button>
                <button class="btn btn-xs btn-danger delete-row" data-user="${row.user}">Delete</button>
            </td>
        </tr>`;
    });

    html += `</tbody></table>`;

    container.html(html);

    container.find(".add-row").on("click", () => open_user_restriction_prompt(frm, null));
    container.find(".edit-row").on("click", function () {
        const user = $(this).data("user");
        const row = frm.doc.user_lead_restrictions.find(r => r.user === user);
        open_user_restriction_prompt(frm, row);
    });
    container.find(".delete-row").on("click", function () {
        const user = $(this).data("user");
        const index = frm.doc.user_lead_restrictions.findIndex(r => r.user === user);
        if (index !== -1) {
            frm.get_field("user_lead_restrictions").grid.grid_rows[index].remove();
            frm.refresh_field("user_lead_restrictions");
            frm.save().then(() => frappe.msgprint("Deleted successfully!"));
        }
    });
}

function open_user_restriction_prompt(frm, row = null) {
    const categories_list = ["New", "Reshuffled Leads", "Meta Leads", "Google Leads",
        "Website Leads", "Fresh Lead", "Lucky Lead", "Data Lead"];

    frappe.call({
        method: "frappe.client.get_list",
        args: { doctype: "Main Lead Source", fields: ["name"], limit_page_length: 0 },
        callback: function(r) {
            const sources_list = (r.message || []).map(d => d.name);
            const selected_categories = row ? parseArrayField(row.lead_category) : [];
            const selected_sources = row ? parseArrayField(row.main_lead_source) : [];

            let category_html = "<label>Lead Categories:</label><br>";
            categories_list.forEach(cat => {
                const checked = selected_categories.includes(cat) ? "checked" : "";
                category_html += `<label style="margin-right:10px; margin-bottom:4px;">
                    <input type="checkbox" value="${cat}" ${checked}> ${cat}
                </label>`;
            });

            let source_html = "<label>Main Lead Sources:</label><br>";
            sources_list.forEach(src => {
                const checked = selected_sources.includes(src) ? "checked" : "";
                source_html += `<label style="margin-right:10px; margin-bottom:4px;">
                    <input type="checkbox" value="${src}" ${checked}> ${src}
                </label>`;
            });

            const d = new frappe.ui.Dialog({
                title: row ? "Edit Restriction" : "Add Restriction",
                fields: [
                    { fieldname: "user", label: "User", fieldtype: "Link", options: "User", default: row ? row.user : "", reqd: 1, read_only: row ? 1 : 0 },
                    { fieldname: "categories_html", label: "Categories", fieldtype: "HTML", options: category_html },
                    { fieldname: "sources_html", label: "Sources", fieldtype: "HTML", options: source_html }
                ],
                primary_action_label: "Save",
                primary_action: function(values) {
                    const selected_cats = [];
                    d.fields_dict.categories_html.$wrapper.find("input[type=checkbox]:checked").each(function() {
                        selected_cats.push($(this).val());
                    });

                    const selected_srcs = [];
                    d.fields_dict.sources_html.$wrapper.find("input[type=checkbox]:checked").each(function() {
                        selected_srcs.push($(this).val());
                    });

                    if (!row && frm.doc.user_lead_restrictions.some(r => r.user === values.user)) {
                        frappe.msgprint("User already exists in restrictions.");
                        return;
                    }

                    let target_row = row || frm.add_child("user_lead_restrictions");
                    if (!row) frappe.model.set_value(target_row.doctype, target_row.name, "user", values.user);

                    // Store as JSON
                    frappe.model.set_value(target_row.doctype, target_row.name, "lead_category", JSON.stringify(selected_cats));
                    frappe.model.set_value(target_row.doctype, target_row.name, "main_lead_source", JSON.stringify(selected_srcs));

                    frm.refresh_field("user_lead_restrictions");
                    render_user_restrictions(frm);

                    frm.save().then(() => frappe.msgprint("Saved successfully!"));
                    d.hide();
                }
            });

            d.show();
        }
    });
}
