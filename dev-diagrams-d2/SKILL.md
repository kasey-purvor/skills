---
name: dev-diagrams-d2
description: Use when generating diagrams with D2 - covers syntax, layout engines, themes, and the MCP tool for rendering to PNG or SVG. Includes shapes, containers, classes, sequence diagrams, grid layouts, SQL tables, and common pitfalls
---

# D2 Diagrams

## Overview

Generate diagrams using D2 syntax, rendered to PNG or SVG via the mcp-d2-diagrams MCP server.

**Announce at start:** "Using D2 diagram skill."

## MCP Tool

```
mcp__mcp-d2-diagrams__generate_d2_diagram
  - d2: D2 diagram syntax (required)
  - output_path: absolute path including filename (required)
  - layout: dagre | elk (default: elk)
  - theme: integer 0+ (default: 0)
  - sketch: boolean (default: false)
  - pad: integer pixels of padding (default: 100)
  - scale: float output scale, -1 = auto (default: -1)
```

**IMPORTANT:** Before calling this tool, ask the user where they want the diagram saved if they haven't specified an output location.

### Output format

The file extension determines the format:
- `.png` — Use by default. Claude Code's Read tool displays PNGs visually.
- `.svg` — Use when embedding in Confluence, PDFs, web pages, or docs. Claude Code shows SVGs as raw XML (not useful for visual review). **Note:** `style.animated: true` on connections only produces visible animation in SVG (CSS keyframes). In PNG, animated connections render as static dashes.

### Output location

If the user hasn't specified a location, suggest:
- The current working directory for quick/throwaway diagrams
- A `diagrams/` subdirectory of the current project for project diagrams
- A path alongside related documentation if generating for a specific doc

## D2 Syntax Quick Reference

### Connections

```d2
# Basic connection
a -> b

# Labeled connection
a -> b: sends data

# Bidirectional
a <-> b: syncs

# Chained
a -> b -> c -> d

# Self-referencing
server -> server: health check
```

**CRITICAL PITFALL — labels + connections on the same line:**
```d2
# WRONG — D2 treats everything after "a:" as a label!
# This creates ONE node labeled "Service A -> b: Service B"
a: Service A -> b: Service B

# CORRECT — declare labels on separate lines, then connect
a: Service A
b: Service B
a -> b
```

D2 parses `id: <rest of line>` as a label assignment. Always declare labels separately from connections.

### Shapes

```d2
# Default (rectangle)
my_service

# With label
my_service: My Service

# Explicit shape
my_db: PostgreSQL {
  shape: cylinder
}

# Available shapes: rectangle, square, page, parallelogram, document,
# cylinder, queue, package, step, callout, stored_data, person,
# diamond, oval, circle, hexagon, cloud
```

**Special shapes** (different rendering behavior):

| Shape | Description | Notes |
|-------|-------------|-------|
| `sql_table` | Database table with columns | See SQL Tables section |
| `class` | UML class diagram | Fields with `+`/`-`/`#` visibility markers |
| `sequence_diagram` | Sequence diagram (top-level only) | See Sequence Diagrams section |
| `text` | Borderless text block | Pair with `\|md ... \|` for rich text |
| `code` | Monospace code block | Pair with `\|lang ... \|` for syntax |
| `image` | Icon-only display | **Requires** `icon` field or D2 errors |

**Node IDs with special characters** must be quoted: `"my-node"`, `"node with spaces"`. Underscores work unquoted.

### Containers (grouping)

```d2
# Nested container
backend: Backend {
  api: API Server
  db: Database {
    shape: cylinder
  }
  api -> db
}

frontend: Frontend {
  app: React App
}

frontend.app -> backend.api: REST
```

### Styles

```d2
my_node: Important {
  style: {
    fill: "#ff6b6b"
    stroke: "#333"
    font-color: "#fff"
    bold: true
    border-radius: 8
    opacity: 0.9
  }
}

my_connection -> target: critical {
  style: {
    stroke: red
    stroke-dash: 3
    stroke-width: 2
    animated: true
  }
}
```

### Classes (reusable styles)

```d2
classes: {
  service: {
    style: {
      fill: "#dbeafe"
      stroke: "#2563eb"
      border-radius: 8
    }
  }
  database: {
    shape: cylinder
    style: {
      fill: "#fef3c7"
      stroke: "#d97706"
    }
  }
}

auth: Auth Service {class: service}
api: API Gateway {class: service}
users_db: Users DB {class: database}
```

### Direction

```d2
# Default is top-down. Change with:
direction: right  # left-to-right layout
# Also: left, up, down
```

### Markdown Text

```d2
explanation: |md
  # API Gateway
  - Routes requests
  - **Rate limiting**
|
```

**CRITICAL: Markdown blocks do not wrap text.** D2 measures markdown dimensions manually without an HTML renderer. Long lines grow infinitely wide and get clipped by parent containers. This is a known limitation ([d2-lang/d2#633](https://github.com/terrastruct/d2/issues/633), status: won't fix for now).

**You must manually break lines in all markdown blocks.** Keep each line to **no more than 8 words wide**. Do not write long flowing sentences — they will be truncated.

```d2
# WRONG — will be clipped
note: |md
  The **secret sauce**. Code inside the content that knows how to find and talk to the hosting platform.
|

# CORRECT — max 8 words per line
note: |md
  The **secret sauce**.
  Code inside the content
  that finds and talks
  to the hosting platform.
|
```

This applies to all `|md ... |` blocks regardless of layout engine (ELK, dagre). There is no `max-width`, `text-wrap`, or overflow property. The `width`/`height` properties on nodes will clip text, not wrap it.

### Sequence Diagrams

```d2
shape: sequence_diagram

alice: Alice
bob: Bob
server: Server

alice -> bob: Hey Bob
bob -> server: GET /api/data
server -> bob: 200 OK {style.stroke-dash: 3}
```

### Grid Layout

```d2
grid-rows: 2
grid-columns: 3

a: Cell 1
b: Cell 2
c: Cell 3
d: Cell 4
e: Cell 5
f: Cell 6
```

### Tooltip, Link, Near

```d2
server: Web Server {
  tooltip: "Handles HTTP on port 8080"  # SVG-only interactivity
  link: https://example.com
}

# Position an annotation at a fixed location
note: "Annotation" {
  shape: page
  near: top-center
}
# Constant values: top-left, top-center, top-right,
# center-left, center-right,
# bottom-left, bottom-center, bottom-right
```

**`near` only supports constant positions** — using `near: other_node` (object reference) fails on both ELK and dagre.

### Icons

```d2
# Using built-in icons (requires internet on first use)
server: Server {
  icon: https://icons.terrastruct.com/essentials%2F112-server.svg
}
```

### Multiple Connections Between Same Nodes

```d2
# Use unique IDs
a -> b: http
a -> b: grpc {
  style.stroke-dash: 3
}
```

### SQL Tables

```d2
users: {
  shape: sql_table
  id: int {constraint: primary_key}
  name: varchar
  email: varchar {constraint: unique}
}
```

## Layout Engines

| Engine | Flag | Best For |
|--------|------|----------|
| **ELK** (default) | `--layout=elk` | Complex nested diagrams, many connections |
| **dagre** | `--layout=dagre` | Simple hierarchies, faster rendering |

ELK is recommended for most cases. Dagre is faster but handles complex nesting poorly (nodes may escape container boundaries).

**Both engines** only support constant values for `near` (e.g., `top-center`). Neither supports `near: other_node`.

## Themes

| ID | Name | Use Case |
|----|------|----------|
| 0 | Default | General purpose |
| 1 | Neutral Grey | Professional docs |
| 3 | Flagship Terrastruct | Branded, colorful |
| 4 | Cool Classics | Blue-toned |
| 5 | Mixed Berry Blue | Dark blue |
| 6 | Grape Soda | Purple |
| 7 | Aubergine | Dark purple |
| 8 | Colorblind Clear | Accessibility |
| 100 | Terminal | Retro/dev |
| 101 | Terminal Grayscale | Monochrome |
| 102 | Terminal Dark | Dark terminal |
| 200 | Origami | Paper-like |

Use `sketch: true` for hand-drawn informal look (works with any theme).

## Filename Convention

- Use `snake_case.png` or `snake_case.svg`
- No spaces in filenames
- Store source `.d2` alongside generated output for editability

## Visual Verification (mandatory)

After generating a diagram to PNG, you **must** read the PNG file using the Read tool and visually inspect it before reporting completion. Check for:

1. **Text truncation** — Are any labels, annotations, or markdown blocks cut off? This is the most common issue (see Markdown Text section). Fix by shortening lines.
2. **Overlapping nodes** — Are any nodes or labels overlapping each other?
3. **Missing connections** — Do all expected arrows appear?
4. **Layout issues** — Are nodes escaping container boundaries? Is the overall layout readable?

If any issues are found, fix the D2 source and regenerate. Do not report the diagram as complete until it passes visual inspection.

**Note:** This only works for PNG output. SVG files render as raw XML in Claude Code and cannot be visually inspected — if generating SVG, mention to the user that visual verification was not possible.

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| Node renders with entire connection as its label | Combined label + connection on one line: `a: Label -> b` | Declare labels separately, then connect (see Connections pitfall above) |
| `reserved keywords are prohibited in edges` | Used `label` as a node ID in a connection | Rename to `label_text` or similar — `label` is a reserved D2 keyword |
| `image shape must include an "icon" field` | Used `shape: image` without `icon` | Add `icon: <url>` field to the node |
| `only supports constant values for "near"` | Used `near: other_node` (object reference) | Use constant like `near: top-center` — object refs unsupported |
| `unexpected text after double quoted string` | Sequence diagram label mixes quotes with other text: `"hello" (extra)` | Don't use quotes in sequence diagram message labels — use plain text only |
| Output file not created (no error) | Used `layers: { ... }` feature | Layers create a directory of files; MCP tool expects a single file — avoid `layers` |
| Node not found | Cross-container reference like `a.b -> c.d` | Ensure both nodes exist and IDs match exactly |
| Markdown text clipped/truncated | Long lines in `\|md ... \|` blocks | Manually break lines to ~40-50 chars (see Markdown Text section) |

## Related Skills

- For Mermaid diagrams (simpler syntax, fewer layout options): `/dev-diagrams-mermaid`
- For uploading diagrams to Confluence: `/dev-confluence`
- For embedding diagrams in PDFs: `/dev-markdown-to-pdf`
