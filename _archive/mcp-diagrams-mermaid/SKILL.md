---
name: dev-diagrams-mermaid
description: Use when generating diagrams with Mermaid - covers syntax, diagram types, layout tips, and CLI rendering to high-res PNG/SVG
---

# Mermaid Diagrams

## Overview

Generate diagrams using Mermaid syntax, rendered via the `@mermaid-js/mermaid-cli` npx package.

**Announce at start:** "Using Mermaid diagram skill."

## Rendering

**Always use the CLI directly — do NOT use the `mcp__mcp-mermaid__generate_mermaid_diagram` MCP tool.** The MCP tool renders at a fixed low resolution (~1264x1004) with no scale or width control. The CLI supports `-w` (viewport width) and `-s` (Puppeteer scale factor) for high-res output.

### Workflow

1. **Save the `.mmd` source file first** using the Write tool
2. **Render with the CLI:**
```bash
npx @mermaid-js/mermaid-cli -i input.mmd -o output.png -w 6000 -s 4 -b white
```
3. Verify dimensions with `file output.png`

### CLI Options

```
npx @mermaid-js/mermaid-cli [options]
  -i, --input <file>       Input .mmd file (required)
  -o, --output <file>      Output file (.png, .svg, .pdf)
  -w, --width <pixels>     Viewport width (default: 800)
  -H, --height <pixels>    Viewport height (default: 600)
  -s, --scale <factor>     Puppeteer scale factor (default: 1)
  -t, --theme <theme>      default | forest | dark | neutral
  -b, --backgroundColor    CSS color (default: white)
```

**CRITICAL:** Do NOT pass `mmdc` as an argument. The package IS the binary:
- Correct: `npx @mermaid-js/mermaid-cli -i input.mmd -o output.png`
- Wrong: `npx @mermaid-js/mermaid-cli mmdc -i input.mmd -o output.png`

### Recommended settings

| Use case | Width | Scale | Result |
|----------|-------|-------|--------|
| Standard diagram | 4000 | 3 | ~12K px wide |
| Complex/dense diagram | 6000 | 4 | ~17K px wide |
| Simple/small diagram | 2000 | 2 | ~4K px wide |

**IMPORTANT:** Before rendering, ask the user where they want the diagram saved if they haven't specified an output location.

## Layout Tips

- Use `flowchart TB` (top-to-bottom) for vertical layouts — good for Confluence pages and narrow contexts
- Use `flowchart LR` (left-to-right) for pipelines and wide layouts
- Use `direction LR` within subgraphs if you need horizontal sections inside a vertical flow

## Filename Convention

- Use `snake_case.png`
- No spaces in filenames
- Store source `.mmd` alongside generated `.png` for editability

## Related Skills

- For D2 diagrams (better auto-layout for complex diagrams): `/dev-diagrams-d2`
- For uploading diagrams to Confluence: `/dev-confluence`
- For embedding diagrams in PDFs: `/dev-markdown-to-pdf`
