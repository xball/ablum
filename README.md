# Album

Personal photo albums for Frappe 16. Photos stay on your server. You get a library, albums, person tags, and a map of photos that have a location.

This app does not depend on any other app.

## Install

Requires a Frappe v16 bench.

```bash
bench get-app https://github.com/xball/ablum.git
bench --site <site> install-app ablum
```

Give the **Album User** role to people who should use Album. System Manager already has access.

## Private and Public

Each album is **Private** unless you change it.

- **Private:** only logged-in Album Users and System Managers can see it. The share link does nothing.
- **Public:** anyone with the link `/album/<token>` can view that album. They cannot see your library, your other albums, or Desk, and they cannot change tags.

The image files stay private on disk. A public page loads a photo only after the token, the public setting, and membership in that album all match. Set the album back to Private and the link stops working.

## Photos

- **Thumbnails** is a grid of images.
- **Details** is one row per photo, with a small image, caption, date, people, and location.
- A person tag is a name, not a user account. Type a new name to create that person.
- Location comes from the photo's GPS data, or from a pin you drop on the Photo form. Photos without a location stay off the map.
