// Copyright (c) 2026, xball and contributors
// For license information, please see license.txt

frappe.ui.form.on("Photo Album", {
	refresh(frm) {
		render_share_link(frm);
	},
	privacy(frm) {
		render_share_link(frm);
	},
	share_token(frm) {
		render_share_link(frm);
	},
});

function render_share_link(frm) {
	const field = frm.get_field("share_link");
	if (!field?.$wrapper) {
		return;
	}
	const token = (frm.doc.share_token || "").trim();
	if (frm.doc.privacy !== "Public" || !token) {
		field.$wrapper.html(
			`<p class="text-muted">${__("This album is private. The share link is off.")}</p>`
		);
		return;
	}
	const url = `${window.location.origin}/album/${encodeURIComponent(token)}`;
	const safe = frappe.utils.escape_html(url);
	field.$wrapper.html(`
		<div class="ablum-share">
			<a href="${safe}" target="_blank" rel="noopener">${safe}</a>
			<button class="btn btn-default btn-sm ablum-copy" type="button" style="margin-left: 8px;">
				${__("Copy share link")}
			</button>
		</div>
	`);
	field.$wrapper.find(".ablum-copy").on("click", () => {
		frappe.utils.copy_to_clipboard(url);
		frappe.show_alert({ message: __("Share link copied"), indicator: "green" });
	});
}
