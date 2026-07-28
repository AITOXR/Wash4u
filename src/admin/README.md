# Wash4You content admin

A small, **local** click-to-edit CMS for this static site. You edit the real
pages in your browser; it writes the changes back to `src/data/*.json`, rebuilds
the site, and (when you choose) publishes.

Nothing here runs on the internet — it binds to `127.0.0.1` only, and it never
changes the live site until you press **Publish** (and separately confirm the
"push live" checkbox).

## Run it

```bash
python3 src/admin/server.py
```

Then open **http://127.0.0.1:8765** and log in.

- Login is set in `src/admin/config.json` (default `admin` / `wash4you`).
- Requires Python 3 and Jinja2 (the same thing `src/build.py` needs) — no other
  dependencies.

## Editing

| You want to… | Do this |
|---|---|
| Change text (headline, paragraph, button label, list item) | Click it, type, click away. It highlights orange as "unsaved". |
| Change a photo (mascot, logo, a card image) | Hover the image → click **🖼 Change image** → pick a file. |
| Save your edits | Click **Save changes** in the top bar. The page rebuilds and reloads. |
| Add / edit / delete a blog post | Click **Blog** in the top bar. |
| Put it live | Click **Publish** (see below). |

Editable things glow teal on hover. `Enter` finishes a text edit; `Esc` cancels
it. The bar warns you before you leave with unsaved changes.

## How the binding works

Each editable element is rendered with a `data-cms="store:path"` attribute (only
in the admin's edit build — production HTML never contains it). `store` is a file
under `src/data/` and `path` is the key inside it. Example: clicking the home
headline edits `home.json → banner.headline_line1`. Images bound to a fixed file
(`data-cms-file`) overwrite that file under `src/assets/`.

Templates opt in with the `cms()` helper, e.g.
`<h2{{ cms('home:why.title') }}>{{ home.why.title }}</h2>`. To make a new field
editable, add a `cms('store:path')` call on its element in `src/templates/`.

## Publish

**Publish** runs the production build (`src/build.py` → `dist/`), overlays it onto
the repo root that the deploy serves, and commits. Two checkboxes:

- **Commit** (default on) — commits the rebuilt site to git locally.
- **Push to the live public site** (default off) — runs `git push`. Leave off to
  review the commit first; tick it only when you're ready to go live.

## Notes & limits

- **Security:** the static username/password is a convenience gate for a tool on
  your own machine, not internet-grade auth. Do not expose port 8765 to a
  network. Change the credentials in `config.json` before screen-sharing.
- Long-tail **location** and **service×area matrix** pages are generated from
  `src/data/generated/` and are not click-editable here.
- FAQ and review cards are rendered through shared macros and aren't inline-
  editable yet — edit `src/data/home.json` / `testimonials.json` directly for now.
- Saving reformats the touched JSON file to 2-space indent (kept deliberately to
  match the existing files and keep diffs small).
