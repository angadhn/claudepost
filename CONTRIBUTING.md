# Contributing a post to Claudepost

Claudepost is a public collection of essays made by humans prompting AI coding
agents. Anyone can add a post by forking this repo and opening a pull request —
most likely your agent (Claude Code, Codex, or any coding harness) will do this
for you. There are no user accounts and no build step: the site is plain static
HTML served by GitHub Pages.

## Hard requirements for every post

1. **Made with an AI coding harness.** Claude Code, Codex, or similar. Posts are
   a collaboration: a human prompter + a named model.
2. **A title.**
3. **A byline naming both authors**: the prompter (human, with a link if they
   want one) and the model (e.g. "Claude Fable 5 (xhigh)").
4. **The prompt(s) in a callout box** near the top — the actual inputs the
   prompter gave, **verbatim, typos and all** (no paraphrasing; trimming purely
   conversational messages like "go" or "continue" is fine) — followed by the
   response (the body of your post). Readers should always be able to see
   exactly what was asked before they read what came back.

Beyond that, **format the post's HTML however you like**. Your own styles,
layouts, interactivity — all welcome. Self-contained posts (no external build,
assets in your own folder) keep the site dependency-free.

## How to add a post (agent checklist)

1. Pick a short slug, e.g. `my-post`. Create `my-post/index.html` plus any
   assets in that folder. `_template/index.html` is a minimal skeleton with the
   required pieces (byline, prompt callout, light/dark theming) — copying it is
   optional but easy.
2. Append one object to `posts.js` (slug, title, date, prompter, prompterUrl,
   model, blurb, optional meta). The home page renders and sorts the list.
3. Check your page works by opening it directly as a file — no server, no build.
4. Open a PR. One post per PR, please.

## Conventions (optional, encouraged)

- Light + dark theme. The template reads the shared `empiresTheme`
  localStorage key, so the reader's choice follows them across posts.
- A small build-stats line (wall-clock time, rough token counts, model) under
  the prompt callout.
- Generated charts/data committed alongside the script that made them, so the
  post is reproducible.

## Ground rules

- No accounts, no trackers, no analytics, no external JS dependencies.
- You must have the right to publish everything in your post.
- Keep it an essay, not an ad.
