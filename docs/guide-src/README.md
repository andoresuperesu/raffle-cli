# Guide source

The sources of the beginner's guide, in two languages: [`../how-raffle-cli-was-built.pdf`](../how-raffle-cli-was-built.pdf) (English) and [`../como-se-construyo-raffle-cli.pdf`](../como-se-construyo-raffle-cli.pdf) (Español).

| File | What it is |
| --- | --- |
| `build.py` | Entry point: `python build.py <repo> <out.html> <en\|es>`. Loads the content module for the language and renders the HTML. |
| `common.py` | Shared by both languages: pulls code snippets out of `src/` and `tests/` with `ast` (so they can never drift from the real code), callout helpers, derived numbers (line counts, test counts, slot-machine timings), CSS, HTML rendering. |
| `guide_en.py` / `guide_es.py` | The prose of each edition: one `add(...)` per paragraph, table or snippet. Same structure in both. |
| `diagrams.py` | Tiny SVG helpers (`box`, `arrow`, `text`) and every diagram. Labels pass through `tr()`, which translates them when building Spanish. |
| `diagrams_es.py` | The Spanish labels for the diagrams (English text → Spanish). |
| `pdf.mjs` | Prints the HTML to an A4 PDF with page numbers using headless Chromium. |
| `build.sh` | Runs both steps for English, Spanish, or both. |

## Rebuild

Needs [uv](https://docs.astral.sh/uv/), Node.js and Playwright with Chromium:

```bash
npm install -g playwright && npx playwright install chromium   # once
docs/guide-src/build.sh                          # rewrites both PDFs in docs/
docs/guide-src/build.sh es                       # only the Spanish one
docs/guide-src/build.sh en /tmp/preview.pdf      # or write somewhere else
```

Edit the text in `guide_en.py` and `guide_es.py` (keep them in step), a diagram in `diagrams.py` (and its Spanish labels in `diagrams_es.py`; the build prints any label that has no translation), then rebuild. The guide quotes the code by function name (for example `code("raffle.py", "Raffle.draw")`): if you rename or delete one, the build fails loudly instead of showing stale code. Whenever you change the code the guide describes, rebuild and commit the PDF.
