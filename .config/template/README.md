# Document templates (Word / Excel / PowerPoint)

Place branded Office templates here. Agent-created docs and MCP
`export_response_excel` / `export_response_word` **clone** these files when valid
(via `oracle_cpq_mcp.exporters.branded_documents`). This directory is
**read-only for agents and MCP** — only you (the user) should add or update
branding files here.

## Expected filenames (exact)

| Type | Filename | Notes |
|------|----------|--------|
| Word | `Word Template.docx` | Required for branded Word exports (header logo + Title/H1–H3 styles) |
| Excel | `Excel Template.xlsx` | Sample header cell in `A1` (font/fill/border) |
| PowerPoint | `PowerPoint Template.pptx` | Optional; used by `open_pptx_presentation` |

Zero-byte files and non-ZIP placeholders (e.g. an empty “New Microsoft Word Document.docx”) are **ignored**. Rename/copy your real branded package to the exact name above.

## How cloning works

1. Resolve the fixed filename under this folder (must be a non-empty ZIP).
2. Copy to a temp file and open the copy — never overwrite the template.
3. Clear **body** (Word) or **slides** (PowerPoint) only; keep headers/footers, logos, themes, masters, and style definitions.
4. Fill content using template styles: **Title**, **Heading 1**, **Heading 2**, **Heading 3**, **Normal**.
5. Write outputs under `data/{profile}/{env}/exports/` (or another non-template path).

## Mermaid diagrams in Word exports

`export_response_word` can embed flowcharts via optional `diagrams` (not Excel). Each
diagram needs a `title` plus Mermaid source and/or a pre-rendered PNG `image_path`.

- Mermaid is rendered **locally** with `mmdc` (`npm i -g @mermaid-js/mermaid-cli`) when
  available on PATH — not via public Kroki/mermaid.ink.
- Prefer PNG paths under `tmp/{profile}/{env}/` when pre-rendering.
- Diagram images and captions are **center-aligned** in the generated `.docx`; tall
  charts are height-capped so they stay on-page.
- Diagram images are inserted into the **generated** `.docx` clone only. Never write
  diagram assets into this template directory.

## Rules

- Do not put credentials or customer data in this folder — branding only.
- Agents and MCP must never create, overwrite, delete, or “fix” files here.
- Resolution uses `CPQ_CONFIG_DIR/template` (defaults to repo `.config/template`).
- If a template is missing or invalid, exporters fall back to a blank document and report `template.applied=false` in the tool response — they will not invent branding.
