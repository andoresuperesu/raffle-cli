# Guide source

The sources of [`../how-raffle-cli-was-built.pdf`](../how-raffle-cli-was-built.pdf).

| File | What it is |
| --- | --- |
| `build.py` | Writes all the prose (one `add(...)` per paragraph/table), pulls code snippets out of `src/` and `tests/` with `ast` (so they can never drift from the real code), computes the numbers it quotes (line counts, test counts, slot-machine timings) and outputs one HTML file. |
| `diagrams.py` | Tiny SVG helpers (`box`, `arrow`, `text`) and every diagram in the guide. |
| `pdf.mjs` | Prints the HTML to an A4 PDF with page numbers using headless Chromium. |
| `build.sh` | Runs both steps. |

## Rebuild

Needs [uv](https://docs.astral.sh/uv/), Node.js and Playwright with Chromium:

```bash
npm install -g playwright && npx playwright install chromium   # once
docs/guide-src/build.sh                      # rewrites docs/how-raffle-cli-was-built.pdf
docs/guide-src/build.sh /tmp/preview.pdf     # or write somewhere else
```

Edit the text in `build.py`, a diagram in `diagrams.py`, then rebuild. The guide quotes the code by function name (for example `code("raffle.py", "Raffle.draw")`): if you rename or delete one, the build fails loudly instead of showing stale code. Whenever you change the code the guide describes, rebuild and commit the PDF.
