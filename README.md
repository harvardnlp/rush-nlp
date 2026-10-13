# Rush NLP website

This site is built by a small Python static-site generator. The original page
content, Markdown, YAML data, and static assets are retained in this repository.

## Build locally

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python site.py
.venv/bin/python -m http.server 4000 --directory docs
```

The generated site is written to `docs/`, which GitHub Pages publishes. Update the existing files in `_data/`,
Markdown, or the page source files, then build again.
