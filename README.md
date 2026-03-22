# joshszep.com

This is the source code for my personal website, [joshszep.com](https://joshszep.com).

It is built using a custom static site generator written in Python.

## Build

Generate the deployable site into `output/`:

```bash
uv sync
uv run main.py
```

The generated `output/` directory contains a single `index.html` with inline HTML, CSS, and JavaScript, plus the copied image assets needed for deployment to Cloudflare Pages.
