---
name: dev-confluence
description: Use when creating or editing Confluence pages, uploading attachments, or embedding images - covers Atlassian MCP, page formats, image upload workflow, and diagram preparation for Confluence
---

# Documentation & Confluence

## Overview

Covers creating and managing Confluence pages via the Atlassian MCP, including the image upload workflow and preparing diagrams for Confluence.

**Announce at start:** "Using Confluence skill for Atlassian page management."

For diagram generation, invoke `/dev-diagrams-mermaid` or `/dev-diagrams-d2`. For PDF export, invoke `/dev-markdown-to-pdf`.

## Available Tools

| Tool | Purpose | Auth |
|------|---------|------|
| `mcp__plugin_atlassian_atlassian__*` | Confluence pages, Jira | OAuth (automatic) |
| `mcp__mcp-mermaid__generate_mermaid_diagram` | Generate PNG diagrams | None |
| `mcp__mcp-markdown-to-pdf__convert_markdown_to_pdf` | Markdown → PDF | None |
| Confluence REST API (curl) | Upload attachments | `$ATLASSIAN_API_TOKEN` |

---

## Confluence

### Spaces

| Space | Key | Purpose |
|-------|-----|---------|
| Engineering | `Eng` | Technical/project documentation |
| Cloud Assist | `CA` | Company-wide documentation |

Cloud ID: `42f426c4-60ff-4fa8-9937-60a133f4ad4b`

### Creating/Updating Pages

Use the Atlassian MCP with `contentFormat: "markdown"` for text-only pages:

```
mcp__plugin_atlassian_atlassian__createConfluencePage
mcp__plugin_atlassian_atlassian__updateConfluencePage
```

For pages with images, use `contentFormat: "adf"` (see Image Workflow below).

### Image Workflow (Confluence)

The Atlassian MCP does not support attachment uploads. Use the REST API directly:

**Step 1: Upload attachment**
```bash
curl -s -X POST \
  "https://thecloudassist-team.atlassian.net/wiki/rest/api/content/{pageId}/child/attachment" \
  -u "kasey.purvor@thecloudassist.com:$ATLASSIAN_API_TOKEN" \
  -H "X-Atlassian-Token: nocheck" \
  -F "file=@{filepath}"
```

**Step 2: Extract file ID from response**
```
Response contains: "extensions": { "fileId": "abc-123-..." }
```

**Step 3: Embed in page using ADF**
```json
{
  "type": "mediaSingle",
  "attrs": { "layout": "center" },
  "content": [{
    "type": "media",
    "attrs": {
      "type": "file",
      "collection": "contentId-{pageId}",
      "id": "{fileId}"
    }
  }]
}
```

**Why file ID?** Filenames with spaces break markdown image syntax. File IDs are reliable.

---

## Diagrams for Confluence

Use `/dev-diagrams-mermaid` or `/dev-diagrams-d2` to generate diagrams, then upload them using the Image Workflow above.

### Confluence Sizing Requirements

Confluence pages have a narrow content width (~680px). Diagrams must be created with this in mind:

- **Use vertical/portrait orientation** — tall and narrow, not wide and short
- **Mermaid:** use `flowchart TB` (top-to-bottom), avoid `flowchart LR` at the top level
- **D2:** use `direction: down` (default), avoid `direction: right` for the root layout
- **Target an A4-like portrait aspect ratio** — diagrams that would fit on a printed page will fit in Confluence

### Render and Check Before Uploading

**Always visually review a diagram before uploading to Confluence:**

1. Generate the diagram PNG using the appropriate diagram skill
2. Read the PNG file to visually inspect it
3. Check: Does it fit a portrait/narrow layout? Is text readable? Are labels cut off?
4. If the diagram is too wide or poorly laid out, regenerate with adjusted settings
5. Only proceed to upload once the diagram looks right

### Filename Convention

- Use `snake_case.png` — no spaces in filenames
- Store source files (`.mmd` or `.d2`) alongside generated `.png` for editability

---

## Quick Reference

### Upload + Embed Workflow

```
1. Generate diagram    → /dev-diagrams-mermaid or /dev-diagrams-d2 (portrait orientation)
2. Visually check      → Read the PNG to confirm layout fits narrow Confluence width
3. Upload to page      → curl POST .../child/attachment
4. Get file ID         → From response: extensions.fileId
5. Update page (ADF)   → mediaSingle with file ID
```

### Page Content Formats

| Format | Use When |
|--------|----------|
| `markdown` | Text-only pages, simple tables, code blocks |
| `adf` | Pages with embedded images |

### Confluence Site Details

- Site: `thecloudassist-team.atlassian.net`
- Email: `kasey.purvor@thecloudassist.com`
- Token: `$ATLASSIAN_API_TOKEN` (env var)
