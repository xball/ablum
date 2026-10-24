// Copyright (c) 2026, xball and contributors
// For license information, please see license.txt

frappe.provide("ablum");

ablum.page = {
	start(wrapper, view) {
		if (wrapper._ablum) {
			wrapper._ablum.show(view);
			return;
		}
		wrapper._ablum = new AlbumPage(wrapper, view);
	},
};

class AlbumPage {
	constructor(wrapper, view) {
		this.wrapper = wrapper;
		this.view = view;
		this.mode = localStorage.getItem("ablum-list-mode") || "thumbnails";
		this.person = "";
		this.open_album = "";
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Album"),
			single_column: true,
		});
		this.body = $(`<div class="ablum-app"></div>`).appendTo(this.page.body);
		this.show(view);
	}

	show(view) {
		this.view = view;
		if (view !== "albums") {
			this.open_album = "";
		}
		this.reload();
	}

	reload() {
		const method =
			this.view === "map"
				? "ablum.album.api.map_photos"
				: this.view === "albums" && this.open_album
					? "ablum.album.api.album_photos"
					: this.view === "albums"
						? "ablum.album.api.albums"
						: "ablum.album.api.library";
		const args = this.view === "albums" && this.open_album ? { album: this.open_album } : {};
		frappe.call({
			method,
			args,
			callback: (response) => this.render(response.message || {}),
		});
	}

	render(data) {
		this.data = data;
		this.body.empty();
		this.body.append(this.toolbar());
		if (this.view === "map") {
			this.body.append(`<div class="ablum-map"></div>`);
			draw_map(this.body.find(".ablum-map").get(0), data.photos || [], (photo) => this.open_photo(photo));
			return;
		}
		if (this.view === "albums" && !this.open_album) {
			this.body.append(this.album_grid(data.albums || []));
			return;
		}
		const photos = this.filtered(data.photos || []);
		if (this.view === "library") {
			this.body.append(this.people_row(data.people || []));
		}
		this.body.append(this.photo_list(photos));
	}

	toolbar() {
		const bar = $(`<div class="ablum-toolbar"></div>`);
		[
			["library", __("Library"), "album-library"],
			["albums", __("Albums"), "album-albums"],
			["map", __("Map"), "album-map"],
		].forEach(([view, label, route]) => {
			const button = $(`<button class="btn btn-sm" type="button"></button>`).text(label);
			button.toggleClass("btn-primary", this.view === view);
			button.toggleClass("btn-default", this.view !== view);
			button.on("click", () => frappe.set_route(route));
			bar.append(button);
		});
		if (this.view !== "map" && !(this.view === "albums" && !this.open_album)) {
			["thumbnails", "details"].forEach((mode) => {
				const label = mode === "thumbnails" ? __("Thumbnails") : __("Details");
				const button = $(`<button class="btn btn-sm btn-default" type="button"></button>`).text(label);
				button.toggleClass("btn-primary", this.mode === mode);
				button.on("click", () => {
					this.mode = mode;
					localStorage.setItem("ablum-list-mode", mode);
					this.render(this.data);
				});
				bar.append(button);
			});
		}
		if (this.view === "library" && frappe.model.can_create("Photo")) {
			const add = $(`<button class="btn btn-sm btn-primary" type="button"></button>`).text(__("Add Photos"));
			add.on("click", () => this.add_photos());
			bar.append(add);
		}
		if (this.view === "albums" && !this.open_album && frappe.model.can_create("Photo Album")) {
			const add = $(`<button class="btn btn-sm btn-primary" type="button"></button>`).text(__("New Album"));
			add.on("click", () => this.new_album());
			bar.append(add);
		}
		if (this.open_album) {
			const back = $(`<button class="btn btn-sm btn-default" type="button"></button>`).text(__("All Albums"));
			back.on("click", () => {
				this.open_album = "";
				this.reload();
			});
			bar.append(back);
			const add = $(`<button class="btn btn-sm btn-default" type="button"></button>`).text(__("Add from library"));
			add.on("click", () => this.add_from_library());
			bar.append(add);
		}
		return bar;
	}

	people_row(people) {
		const row = $(`<div class="ablum-people"></div>`);
		const all = $(`<button class="btn btn-xs btn-default" type="button"></button>`).text(__("Everyone"));
		all.toggleClass("btn-primary", !this.person);
		all.on("click", () => {
			this.person = "";
			this.render(this.data);
		});
		row.append(all);
		people.forEach((person) => {
			const button = $(`<button class="btn btn-xs btn-default" type="button"></button>`).text(person);
			button.toggleClass("btn-primary", this.person === person);
			button.on("click", () => {
				this.person = person;
				this.render(this.data);
			});
			row.append(button);
		});
		return row;
	}

	filtered(photos) {
		if (!this.person || this.view !== "library") {
			return photos;
		}
		return photos.filter((photo) => (photo.people || []).includes(this.person));
	}

	photo_list(photos) {
		if (!photos.length) {
			return $(`<p class="text-muted ablum-empty"></p>`).text(__("No photos yet."));
		}
		if (this.mode === "details") {
			return this.detail_list(photos);
		}
		return this.thumbnail_list(photos);
	}

	thumbnail_list(photos) {
		const wrap = $(`<div></div>`);
		let current = "";
		let grid = null;
		photos.forEach((photo) => {
			const day = (photo.taken_on || "").slice(0, 10) || __("No date");
			if (day !== current) {
				current = day;
				wrap.append($(`<h4 class="ablum-day"></h4>`).text(day));
				grid = $(`<div class="ablum-grid"></div>`);
				wrap.append(grid);
			}
			const button = $(`<button class="ablum-tile" type="button"></button>`);
			button.append($(`<img alt="">`).attr("src", photo.image || ""));
			button.on("click", () => this.open_photo(photo));
			grid.append(button);
		});
		return wrap;
	}

	detail_list(photos) {
		const list = $(`<div class="ablum-details"></div>`);
		photos.forEach((photo) => {
			const row = $(`<button class="ablum-detail" type="button"></button>`);
			row.append($(`<img alt="">`).attr("src", photo.image || ""));
			const text = $(`<span class="ablum-detail-text"></span>`);
			text.append($(`<strong></strong>`).text(photo.caption || __("No caption")));
			text.append($(`<span></span>`).text(photo.taken_on || ""));
			text.append($(`<span></span>`).text((photo.people || []).join(", ")));
			const where =
				photo.latitude == null || photo.longitude == null
					? __("No location")
					: `${Number(photo.latitude).toFixed(5)}, ${Number(photo.longitude).toFixed(5)}`;
			text.append($(`<span></span>`).text(where));
			row.append(text);
			row.on("click", () => this.open_photo(photo));
			list.append(row);
		});
		return list;
	}

	album_grid(albums) {
		if (!albums.length) {
			return $(`<p class="text-muted ablum-empty"></p>`).text(__("No albums yet."));
		}
		const grid = $(`<div class="ablum-albums"></div>`);
		albums.forEach((album) => {
			const card = $(`<button class="ablum-album" type="button"></button>`);
			if (album.cover) {
				card.append($(`<img alt="">`).attr("src", album.cover));
			} else {
				card.append($(`<span class="ablum-cover-empty"></span>`).text(__("No cover")));
			}
			card.append($(`<strong></strong>`).text(album.title || ""));
			card.append($(`<span></span>`).text(`${album.privacy} · ${album.photo_count || 0}`));
			card.on("click", () => {
				this.open_album = album.name;
				this.reload();
			});
			grid.append(card);
		});
		return grid;
	}

	add_photos() {
		const input = document.createElement("input");
		input.type = "file";
		input.accept = "image/*";
		input.multiple = true;
		input.onchange = async () => {
			for (const file of input.files || []) {
				const form = new FormData();
				form.append("file", file, file.name);
				const response = await fetch("/api/method/ablum.album.api.upload_photo", {
					method: "POST",
					body: form,
					headers: {
						"X-Frappe-CSRF-Token": frappe.csrf_token,
						Accept: "application/json",
					},
				});
				const payload = await response.json();
				if (!response.ok || payload.exc) {
					frappe.msgprint(__("Could not add {0}.", [file.name]));
				}
			}
			this.reload();
		};
		input.click();
	}

	new_album() {
		const dialog = new frappe.ui.Dialog({
			title: __("New Album"),
			fields: [
				{ fieldtype: "Data", fieldname: "title", label: __("Title"), reqd: 1 },
				{
					fieldtype: "Select",
					fieldname: "privacy",
					label: __("Privacy"),
					options: "Private\nPublic",
					default: "Private",
				},
			],
			primary_action_label: __("Create"),
			primary_action: (values) => {
				frappe.call({
					method: "ablum.album.api.create_album",
					args: values,
					callback: () => {
						dialog.hide();
						this.reload();
					},
				});
			},
		});
		dialog.show();
	}

	add_from_library() {
		frappe.call({
			method: "ablum.album.api.library",
			callback: (response) => {
				const have = new Set((this.data.photos || []).map((photo) => photo.name));
				const choices = (response.message.photos || []).filter((photo) => !have.has(photo.name));
				if (!choices.length) {
					frappe.show_alert({ message: __("Every library photo is already in this album."), indicator: "orange" });
					return;
				}
				const dialog = new frappe.ui.Dialog({
					title: __("Add from library"),
					fields: choices.map((photo) => ({
						fieldtype: "Check",
						fieldname: photo.name,
						label: photo.caption || photo.taken_on || photo.name,
					})),
					primary_action_label: __("Add"),
					primary_action: (values) => {
						const photos = Object.keys(values).filter((name) => values[name]);
						frappe.call({
							method: "ablum.album.api.add_to_album",
							args: { album: this.open_album, photos },
							callback: () => {
								dialog.hide();
								this.reload();
							},
						});
					},
				});
				dialog.show();
			},
		});
	}

	open_photo(photo) {
		const dialog = new frappe.ui.Dialog({
			title: photo.caption || __("Photo"),
			size: "large",
			fields: [
				{ fieldtype: "HTML", fieldname: "preview" },
				{ fieldtype: "Small Text", fieldname: "caption", label: __("Caption"), default: photo.caption || "" },
				{ fieldtype: "Data", fieldname: "person_name", label: __("Tag a person") },
			],
			primary_action_label: __("Save"),
			primary_action: (values) => {
				frappe.call({
					method: "ablum.album.api.update_caption",
					args: { photo: photo.name, caption: values.caption || "" },
					callback: () => {
						const name = (values.person_name || "").trim();
						if (!name) {
							dialog.hide();
							this.reload();
							return;
						}
						frappe.call({
							method: "ablum.album.api.tag_person",
							args: { photo: photo.name, person_name: name },
							callback: () => {
								dialog.hide();
								this.reload();
							},
						});
					},
				});
			},
		});
		const preview = dialog.fields_dict.preview.$wrapper;
		preview.append($(`<img class="ablum-preview" alt="">`).attr("src", photo.image || ""));
		preview.append($(`<p class="text-muted"></p>`).text(photo.taken_on || ""));
		const people = $(`<div class="ablum-people"></div>`);
		(photo.people || []).forEach((person) => {
			const button = $(`<button class="btn btn-xs btn-default" type="button"></button>`).text(`${person} ×`);
			button.on("click", () => {
				frappe.call({
					method: "ablum.album.api.untag_person",
					args: { photo: photo.name, person },
					callback: () => {
						dialog.hide();
						this.reload();
					},
				});
			});
			people.append(button);
		});
		preview.append(people);
		const form_link = $(`<button class="btn btn-xs btn-default" type="button"></button>`).text(
			__("Set location on the photo")
		);
		form_link.on("click", () => {
			dialog.hide();
			frappe.set_route("Form", "Photo", photo.name);
		});
		preview.append(form_link);
		if (this.open_album) {
			const remove = $(`<button class="btn btn-xs btn-default" type="button" style="margin-left:8px;"></button>`).text(
				__("Remove from album")
			);
			remove.on("click", () => {
				frappe.call({
					method: "ablum.album.api.remove_from_album",
					args: { album: this.open_album, photo: photo.name },
					callback: () => {
						dialog.hide();
						this.reload();
					},
				});
			});
			preview.append(remove);
		}
		dialog.show();
	}
}

function draw_map(element, photos, on_click) {
	if (!element) {
		return;
	}
	frappe.require(["leaflet.bundle.js", "leaflet.bundle.css"]).then(() => {
		if (element._ablum_map) {
			element._ablum_map.remove();
		}
		const map = L.map(element).setView([20, 0], 2);
		L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
			maxZoom: 19,
			attribution: "&copy; OpenStreetMap",
		}).addTo(map);
		const markers = photos.map((photo) => {
			const marker = L.circleMarker([Number(photo.latitude), Number(photo.longitude)], {
				radius: 8,
				color: "#2563eb",
				fillColor: "#2563eb",
				fillOpacity: 0.9,
				weight: 1,
			}).addTo(map);
			marker.on("click", () => on_click(photo));
			return marker;
		});
		if (markers.length) {
			map.fitBounds(L.featureGroup(markers).getBounds().pad(0.3));
		}
		element._ablum_map = map;
		setTimeout(() => map.invalidateSize(), 200);
	});
}
