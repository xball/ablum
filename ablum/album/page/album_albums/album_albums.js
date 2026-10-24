frappe.pages["album-albums"].on_page_load = function (wrapper) {
	frappe.require(["/assets/ablum/js/album_page.js", "/assets/ablum/css/album.css"], () => {
		ablum.page.start(wrapper, "albums");
	});
};
