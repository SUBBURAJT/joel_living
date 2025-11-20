// document.body.addEventListener("click", function (e) {
// 	handleToggle(e);
// });

// document.body.addEventListener("touchstart", function (e) {
// 	handleToggle(e);
// });

// function handleToggle(e) {
// 	if (e.target.closest(".sidebar-toggle-btn")) {
// 		const side = document.querySelector(
// 			".workspace-sidebar, .desk-sidebar, .layout-side-section"
// 		);
// 		const main = document.querySelector(".layout-main-section");

// 		if (!side || !main) return;

// 		if (getComputedStyle(side).display === "none") {
// 			side.style.display = "";
// 			main.style.width = "";
// 			console.log("Sidebar shown ✔️");
// 		} else {
// 			side.style.display = "none";
// 			main.style.width = "100%";
// 			console.log("Sidebar hidden ✔️");
// 		}
// 	}
// }

// $(document).ready(function () {
//     if (frappe.user.has_role("Sales Agent")) {

//          $(".search-bar").hide();
//         $(document).off("keydown.frappe");

//     }
//         // 🔹 Always force private uploads
//         const OrigFileUploader = frappe.ui.FileUploader;
//         frappe.ui.FileUploader = class CustomFileUploader extends OrigFileUploader {
//             constructor(opts) {
//                 opts.is_private = 1; // force every file private
//                 opts.make_attachments_public = 0;
//                 super(opts);
//             }
//         };

//         // 🔹 Function to apply hide rules
//         function applyFileUploadHacks(modal) {
//             // hide "Private" checkbox in preview
//             $(modal).find("label.frappe-checkbox:has(input[type=checkbox])").hide();

//             // hide "Set all private" / "Set all public" buttons
//             $(modal).find(".modal-footer .btn-modal-secondary:contains('Set all private')").hide();
//             $(modal).find(".modal-footer .btn-modal-secondary:contains('Set all public')").hide();

//             // keep only "My Device" option
//             $(modal).find(".btn-file-upload").each(function () {
//                 const txt = $(this).text().trim().toLowerCase();
//                 if (txt !== "my device") {
//                     $(this).hide();
//                 }
//             });
//         }

//         // 🔹 MutationObserver to catch re-renders
//         const observer = new MutationObserver(() => {
//             $(".modal:visible").each(function () {
//                 applyFileUploadHacks(this);
//             });
//         });

//         // 🔹 Run immediately when modal opens, then keep watching
//         $(document).on("shown.bs.modal", ".modal", function () {
//             applyFileUploadHacks(this); // immediate fix
//             observer.observe(this, { childList: true, subtree: true });
//         });

// });

// global formatter for Attachment fields: show only the filename
// custom_common.js
// custom_common.js
// (function() {
//     function filenameFromUrl(url) {
//         if (!url) return "";
//         // strip query/hash, take last segment
//         let fname = url.split("?")[0].split("#")[0].split("/").pop() || url;
//         return fname;
//     }

//     function updateAttachmentLinks(root=document) {
//         // Select anchor(s) that show the full file path
//         root.querySelectorAll && root.querySelectorAll('.attached-file-link').forEach(a => {
//             // only change if currently showing the href (full path) or still has a slash
//             let text = a.textContent && a.textContent.trim();
//             if (!text) return;
//             // Avoid overwriting custom labels: only replace if it looks like a path
//             if (text.includes('/') || text.startsWith('/private/files') || text.includes('files/')) {
//                 a.textContent = filenameFromUrl(a.getAttribute('href') || text);
//             }
//         });
//     }

//     // Run once after frappe is ready
//     frappe && frappe.ready ? frappe.ready(() => updateAttachmentLinks()) : updateAttachmentLinks();

//     // Observe DOM changes and update dynamically inserted attachments
//     const observer = new MutationObserver(mutations => {
//         for (const m of mutations) {
//             if (m.addedNodes && m.addedNodes.length) {
//                 m.addedNodes.forEach(node => {
//                     // if node itself contains attachments or children do
//                     if (node.querySelectorAll) {
//                         updateAttachmentLinks(node);
//                     }
//                 });
//             }
//         }
//     });

//     // observe the entire document body
//     if (document && document.body) {
//         observer.observe(document.body, { childList: true, subtree: true });
//     }
// })();


$(document).ready(function () {

    // ======================================================
    // 1️⃣  Restrict UI for Sales Agent
    // ======================================================
    if (frappe.session.user !== "Administrator") {
        if (frappe.user_roles.includes("Sales Agent")) {
            $(".search-bar").hide(); // Hide search bar
            $(document).off("keydown.frappe"); // Disable keyboard shortcuts
        }
    }

    // ======================================================
    // 2️⃣  Override FileUploader (Force Private Uploads)
    // ======================================================
    frappe.after_ajax(() => {
        if (!frappe.ui.FileUploader) {
            console.warn("⚠️ frappe.ui.FileUploader not yet available.");
            return;
        }

        const OrigFileUploader = frappe.ui.FileUploader;

        frappe.ui.FileUploader = class CustomFileUploader extends OrigFileUploader {
            constructor(opts) {
                opts.is_private = 1;
                opts.make_attachments_public = 0;
                super(opts);
            }
        };
    });

    // ======================================================
    // 3️⃣  Clean File Upload Modal UI
    // ======================================================
    function cleanFileUploadModal(modal) {
        const $modal = $(modal);

        // Only modify File Uploader modals
        if (!$modal.find(".file-uploader").length) {
            return; // Skip other modals like Confirm, Assign, etc.
        }

        // Hide private checkbox
        $modal.find("label.frappe-checkbox:has(input[type=checkbox])").hide();

        // Hide footer secondary buttons (not needed in file upload)
        $modal.find(".modal-footer .btn-modal-secondary").hide();

        // Show only "My Device" button
        $modal.find(".btn-file-upload").each(function () {
            const btnText = $(this).find("div.mt-1").text().trim().toLowerCase();
            $(this).toggle(btnText === "my device");
        });
    }

    // ======================================================
    // 4️⃣  Observe File Upload Modals only
    // ======================================================
    $(document).on("shown.bs.modal", ".modal:has(.file-uploader)", function () {
        const modal = this;

        // Initial clean-up
        cleanFileUploadModal(modal);

        // Observe changes inside modal body (for Vue re-renders)
        const observer = new MutationObserver(() => cleanFileUploadModal(modal));
        observer.observe(modal, { childList: true, subtree: true });

        // Stop observing when modal is closed
        $(modal).on("hidden.bs.modal", function () {
            observer.disconnect();
        });
    });
});




