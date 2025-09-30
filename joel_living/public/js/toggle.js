
    document.body.addEventListener("click", function (e) {
        handleToggle(e);
        
    });

    document.body.addEventListener("touchstart", function (e) {
        handleToggle(e);
    });

    function handleToggle(e) {
        if (e.target.closest(".sidebar-toggle-btn")) {
            const side = document.querySelector(".workspace-sidebar, .desk-sidebar, .layout-side-section");
            const main = document.querySelector(".layout-main-section");

            if (!side || !main) return;

            if (getComputedStyle(side).display === "none") {
                side.style.display = "";
                main.style.width = "";
                console.log("Sidebar shown ✔️");
            } else {
                side.style.display = "none";
                main.style.width = "100%";
                console.log("Sidebar hidden ✔️");
            }
        }
    }

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

$(document).ready(function () {
    
    // Force private uploads for Sales Agent
    if (frappe.user.has_role("Sales Agent")) {
        $(".search-bar").hide();
        $(document).off("keydown.frappe");
    }

    // Override FileUploader to force private uploads
    const OrigFileUploader = frappe.ui.FileUploader;
    frappe.ui.FileUploader = class CustomFileUploader extends OrigFileUploader {
        constructor(opts) {
            opts.is_private = 1;
            opts.make_attachments_public = 0;
            super(opts);
        }
    };

    // Function to show only "My Device" and hide private/public buttons
    function cleanFileUploadModal(modal) {
        const $modal = $(modal);

        // Hide private checkbox
        $modal.find("label.frappe-checkbox:has(input[type=checkbox])").hide();

        // Hide footer buttons
        $modal.find(".modal-footer .btn-modal-secondary").hide();

        // Show only "My Device" button
        $modal.find(".btn-file-upload").each(function () {
            const btnText = $(this).find('div.mt-1').text().trim().toLowerCase();
            $(this).toggle(btnText === "my device");
        });
    }

    // Use MutationObserver on the modal body to catch Vue re-renders
    $(document).on("shown.bs.modal", ".modal", function () {
        const modal = this;

        // Initial clean-up
        cleanFileUploadModal(modal);

        // Observe changes inside modal body (for re-renders)
        const observer = new MutationObserver(() => cleanFileUploadModal(modal));
        observer.observe(modal, { childList: true, subtree: true });

        // Stop observing when modal is hidden
        $(modal).on("hidden.bs.modal", function () {
            observer.disconnect();
        });
    });
});
