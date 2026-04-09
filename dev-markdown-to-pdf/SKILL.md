---
name: dev-markdown-to-pdf
description: Use when converting markdown content to PDF files - covers the MCP tool, styling options, and image embedding
---

# Markdown to PDF

## Overview

Convert markdown content to styled PDF files via the mcp-markdown-to-pdf MCP server.

**Announce at start:** "Using markdown-to-PDF skill."

## MCP Tool

```
mcp__mcp-markdown-to-pdf__convert_markdown_to_pdf
  - content: markdown text (required)
  - output_path: absolute path ending in .pdf (required)
  - basedir: directory containing referenced images (required)
  - css: custom CSS to apply
  - highlight_style: code highlighting theme (default: github)
  - pdf_options: { format, margin, printBackground }
```

**IMPORTANT:** Before calling this tool, confirm with the user:
1. Where to save the PDF (`output_path`)
2. The base directory containing any referenced images (`basedir`)

## Image References

If the markdown contains relative image paths like `![](images/foo.png)`, the `basedir` parameter must be the parent folder containing `images/`.

Example:
```
Markdown references: ![](images/architecture.png)
basedir should be:   /home/kasey/dev_wsl/my-project/
So it resolves to:   /home/kasey/dev_wsl/my-project/images/architecture.png
```

## PDF Options

| Option | Default | Examples |
|--------|---------|----------|
| `format` | A4 | A4, Letter, Legal, Ledger, Tabloid |
| `margin` | 30mm 40mm 30mm 20mm | "20mm", "10mm 20mm 30mm 40mm" |
| `printBackground` | true | Include background colors/images |

## Code Highlighting Themes

`github` (default), `monokai`, `solarized-light`, `solarized-dark`

## Related Skills

- For generating diagrams to embed: `/dev-diagrams-mermaid` or `/dev-diagrams-d2`
- For publishing to Confluence instead of PDF: `/dev-confluence`
