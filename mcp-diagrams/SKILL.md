---
name: dev-diagrams
description: Use when the user asks for a diagram, wants to visualise architecture/data/flow, or when a diagram would clarify a design discussion. Entry point that helps choose the right diagram type and tool before generating anything.
---

# Diagrams

## Overview

Entry point for all diagram work. Helps choose the right diagram type for the situation, then delegates to the appropriate tool skill for generation.

**Do not jump straight to generating a diagram.** First understand what the user is trying to understand, then recommend a diagram type, then load the tool skill.

## Standard Diagram Types

| Diagram | What It Shows | Best For |
|---------|--------------|----------|
| **Data Flow Diagram (DFD)** | How data moves and transforms through a system. Levels 0-3+: each level decomposes processes into sub-processes | Pipeline/batch systems, ETL, data-heavy architectures |
| **UML Component Diagram** | Modules, their interfaces, and dependency direction | Module boundaries, API contracts, layered architectures |
| **UML Sequence Diagram** | Temporal interactions between components for a specific scenario | Complex multi-step workflows, API call chains, auth flows |
| **UML Activity Diagram** | Flowchart with decisions, parallel paths, and joins | Branching logic, state machines, concurrent workflows |
| **UML Class Diagram** | Classes, methods, attributes, and relationships | Detailed code structure, OOP design, type hierarchies |
| **Entity-Relationship Diagram** | Data structures and relationships between them | Database design, data models, schema documentation |
| **C4 Model** (4 levels) | Context > Container > Component > Code. Progressive zoom from system boundary to individual classes | Large systems, multi-service architectures, team handoffs |

### Typical Subsets by Project Type

These are common starting points, not rules. Different projects and moments call for different diagrams. Discuss with the user what would be most useful.

| Project Type | Common Diagrams |
|-------------|----------------|
| Web/API services | Component + Sequence + ER |
| Data pipelines / batch processing | DFD + Component + ER |
| Enterprise / formal handoffs | Full C4 stack + Class + Activity |
| CLI tools / single-process apps | Component + DFD (Level 1-2) + ER |

### DFD Levels

Data Flow Diagrams use progressive decomposition:

- **Level 0 (Context):** The whole system as one process. Shows external entities (users, databases, APIs) and data flowing in/out. Answers: "what does this system interact with?"
- **Level 1:** Decompose into major processes (e.g., preflight, processing, aggregation) with data stores and flows between them. Answers: "what are the major stages?"
- **Level 2:** Decompose each Level 1 process into sub-processes (individual components). Answers: "what components handle each stage?"
- **Level 3+:** Individual functions within components. Answers: "how does this component work internally?"

Start at Level 1. Go deeper only if the user needs more detail for a specific area.

## Choosing a Diagram Type

When the user asks for a diagram, understand the intent before choosing a type:

| User wants to understand... | Recommended diagram |
|---------------------------|-------------------|
| What components exist and how they connect | Component diagram or architecture overview |
| How data moves through the system | DFD (start at Level 1) |
| What happens during a specific workflow | Sequence diagram (temporal order) or Activity diagram (branching decisions) |
| What the data structures look like | ER diagram |
| What classes/functions exist and how they relate | Class diagram |
| Where a new feature fits in the existing system | Scoped architecture diagram with data flow annotations (hybrid) |
| How an integration component wires existing components together | Hybrid diagram (see below) |

If the user doesn't know what they need, ask: **"What are you trying to understand — the structure (what exists and how it connects), the flow (how data moves through the system), or the behaviour (what happens when a specific thing occurs)?"**

Don't default to a standard combination. Explain what each option would show for their specific situation and let the user decide. Offer to generate a quick example if they're unsure.

### Hybrid Diagrams for Integration Components

When scoping an **integration component** (e.g., an orchestrator, controller, or coordinator that wires existing leaf components together), standard diagram types each show only part of the picture. A component diagram shows interfaces but not data flow. A DFD shows data flow but not component structure. A sequence diagram shows temporal order but gets unwieldy with many components.

A **hybrid diagram** combines component layout with embedded process descriptions and colour-coded data flow annotations. It shows:

- The integration component's **internal phases** (e.g., preflight, setup, worker loop, aggregation) with step lists inside each
- **Which external components** each phase touches, with arrows labelled by method/data
- **Colour-coded connections** by phase so you can visually trace which phase owns which interactions
- **External systems** (databases, APIs, filesystem) at the edges

This is not a standard diagram type — you won't find it in UML or DFD textbooks. It's a practical brainstorming aid that emerged from chunk-scoping sessions where no single standard diagram captured the full picture of an integration component. Use it when:

- The component being scoped **coordinates many existing components** rather than introducing new data structures
- You need to show both **internal structure and external interfaces** in one view
- The audience needs to understand **which phase is responsible for which interactions**

## Diagram Tools

### D2 (default)

D2 is the default diagramming tool. Better layout engines (elk handles complex nesting well), better styling, cleaner syntax. Handles architecture diagrams, flowcharts, sequence diagrams, ER diagrams, and more.

Load `dev-diagrams-d2` for syntax reference and the MCP rendering tool (`generate_d2_diagram`).

### Mermaid (only for GitHub markdown)

Mermaid's only advantage is native rendering in GitHub markdown — diagrams in `.md` files render inline when viewed on GitHub, with no PNG generation needed. Layout quality is worse than D2 and it does not render natively in Confluence (confirmed — Confluence shows Mermaid as plain text code blocks).

Use Mermaid only when the diagram lives in a markdown file that will primarily be viewed on GitHub. For all other uses, D2 is better.

Load `dev-diagrams-mermaid` for syntax reference and the MCP rendering tool (`generate_mermaid_diagram`).

### Publishing to Confluence

Confluence does not render Mermaid or D2 natively. The workflow is: generate a PNG using D2, then upload via the Confluence image attachment API. Load `dev-confluence` when ready to publish.
