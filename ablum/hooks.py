app_name = "ablum"
app_title = "Album"
app_publisher = "xball"
app_description = "Personal photo albums for Frappe 16"
app_email = "xball@users.noreply.github.com"
app_license = "mit"

add_to_apps_screen = [
	{
		"name": "ablum",
		"logo": "/assets/ablum/images/album.svg",
		"title": "Album",
		"route": "/desk/album-library",
	}
]

before_install = ["ablum.install.ensure_role"]
before_migrate = ["ablum.install.ensure_role"]

website_route_rules = [
	{"from_route": "/album/<token>", "to_route": "shared_album"},
]
