# Claudepost

**[claudepost.com](https://claudepost.com)** — essays in data, written by humans
prompting AI coding agents. Each post shows the prompt that made it.

## Layout

```
index.html        home page (renders the post list from posts.js)
posts.js          manifest of posts — add one object per post
CONTRIBUTING.md   how to add a post (read this first)
_template/        minimal post skeleton you may copy
empires-1/        post: "The Shape of Empires" (2026-06-11)
CNAME             custom domain for GitHub Pages
```

Every post is a self-contained folder with an `index.html`. No build step, no
framework, no accounts. GitHub Pages serves `main` as-is.

## Add your post

Fork → create `your-slug/index.html` → append an entry to `posts.js` → PR.
Details and the few hard requirements (byline with prompter + model, the prompt
in a callout box) are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Develop

Open any `index.html` straight from disk — everything works over `file://`.
Posts that generate figures keep their generator script in their own folder
(see `empires-1/make_empire_plots.py`, run with
`uv run --with matplotlib --with numpy python empires-1/make_empire_plots.py`).
