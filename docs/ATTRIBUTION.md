# Attribution & Provenance

This repo is a **curated local-first toolkit**, not a from-scratch invention.
Almost everything powerful in it comes from other people's work. This file says
exactly what we borrowed, what we wrote, and where to give credit (and stars).

## What we BORROWED (and who to thank)

### 1. The MCP server — `artokun/comfyui-mcp`
- Repo: https://github.com/artokun/comfyui-mcp
- License: **MIT**
- npm package: `comfyui-mcp`
- This is the actual MCP server we run against local ComfyUI. It is a
  "local-first, agent-native control plane" with ~178 tools, model-family
  skills, installer packs, and live-graph editing. **We did not write it.**
  We configure it (see `mcp/README.md`) and use it. If it helps you, star it —
  that is the single most useful thank-you.

### 2. Official Comfy-Org agent tooling (for comparison / context)
- Local MCP: https://github.com/Comfy-Org/comfy-mcp (pip `comfy-mcp`, first-party, public beta)
- Cloud MCP: https://github.com/Comfy-Org/comfy-cloud-mcp (`https://cloud.comfy.org/mcp`)
- Official skills: https://github.com/Comfy-Org/comfy-skills (MIT)
- Docs: https://docs.comfy.org/agent-tools/mcp
- We document these so users know the official path exists. Our repo is not a
  replacement for them; it is a low-VRAM / local-only opinionated bundle.

### 3. MiniMax H3 official skills + community prompt practice
- The H3 prompt-writing knowledge in this environment builds on MiniMax's
  official H3 skills and community practice (e.g. teskor-hub's H3 skill).
- We reference H3 because that is the model family this toolkit was hardened
  on, but the H3 model weights and their licensing belong to MiniMax.

### 4. ComfyUI itself
- https://github.com/comfyanonymous/ComfyUI — the server whose REST API every
  tool here speaks.

## What WE wrote / curated (the "ours" part)

- **`skills/comfy_local/`** — a model-agnostic, pure-REST fallback skill so a
  local ComfyUI can be driven by any MCP-capable harness even when the MCP
  server is offline. Includes:
  - `scripts/comfy.py` — a zero-dependency (stdlib-only) submit/poll/download
    client.
  - `references/models.md` — an 8GB-VRAM model shortlist + fal.ai cloud
    fallback notes.
  - `references/workflows.md` — minimal proven API-format workflow skeletons.
  - `SKILL.md` — the golden rules (never assume a model filename / node class;
    always discover from the running server; API-format only; poll /history).
- **`mcp/README.md`** — ready-to-paste local MCP configs for Claude Code /
  Cursor / generic clients, tuned for a local ComfyUI.
- **The low-VRAM field notes** — the 8GB-specific pitfalls (GGUF/fp8 only,
  block-swap, offload, resolution vs. VRAM) distilled from actually running
  heavy video models (incl. MiniMax H3) on an 8GB laptop GPU.
- **README (EN + 中文)** and this attribution file.

## License summary

| Component | Source | License |
|-----------|--------|---------|
| This repo's own files | Project Contributors | MIT (see `LICENSE`) |
| `comfyui-mcp` server | artokun | MIT |
| `comfy-mcp` / `comfy-skills` | Comfy-Org | see each repo |
| ComfyUI core | comfyanonymous | GPL-3.0 |
| MiniMax H3 weights | MiniMax | MiniMax license |

We are grateful to every author above. This bundle only stitches their work
into a local, low-VRAM-friendly workflow and documents the glue.
