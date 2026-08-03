# VTR Press regression test suite

## Running

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## What's covered

| File | Covers |
|---|---|
| `test_reader.py` | YAML front matter parsing, HTML-comment skipping, error cases |
| `test_structure.py` | Markdown -> Book/Part/Chapter/Scene/Section AST construction, structural errors |
| `test_inline.py` | Bold/italic/code/link inline expansion, known limitations (no nesting, no escaping) |
| `test_typst_renderer.py` | Typst source generation: escaping, link URL escaping, running-header title stripping, page/section wiring |
| `test_epub_renderer.py` | EPUB zip structure, HTML escaping, cross-renderer notes |
| `test_integration.py` | End-to-end `publish()` / `publish_epub()` / `publish_all()`, and the shipped example manuscript |

## Design notes

- **No Typst binary required.** These tests assert against the generated
  Typst *source text* (string-level contract with `themes/classic/*.typ`),
  not compiled PDF output. If you want to also verify actual compiled
  PDFs (e.g. with PyMuPDF, like the header/footer isolation testing
  mentioned in project notes), that would be a separate, slower suite —
  happy to help set that up if useful.
- **Known limitations are pinned, not hidden.** Several tests document
  current quirky-but-real behavior (e.g. inline markers don't nest, an
  unterminated `**` degrades into an empty italic node) with a comment
  explaining *why* the assertion is what it is. If you fix one of these,
  update the test — don't just delete it.
- **`test_shipped_example_manuscript_parses` is a strict `xfail`.**
  `examples/sample-manuscript.md` currently uses heading levels one
  shallower than `parser/structure.py` expects, so it fails to parse.
  The test is marked `xfail(strict=True)` so the suite stays green, but
  will loudly fail (XPASS) the moment someone fixes the example file
  without removing the marker — a deliberate nudge to notice and clean
  up the marker rather than let it linger.
