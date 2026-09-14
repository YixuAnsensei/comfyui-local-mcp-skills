# ComfyUI Local MCP + Skills

> Drive a **local** ComfyUI from Claude Code, Cursor, or any MCP-capable AI
> harness — tuned for **low-VRAM rigs (8GB)** and heavy video models like
> MiniMax H3. A ready-to-paste MCP config plus a pure-REST fallback skill.

[中文说明](./README.zh-CN.md) · [Attribution](./docs/ATTRIBUTION.md) · [MIT](./LICENSE)

---

## TL;DR — the fastest way to use this repo

**Don't read the whole thing. Clone it, then hand the folder to your AI agent
(Claude Code / Cursor / Codex) and say:**

> "Here's a repo called comfyui-local-mcp-skills. Read the README and
> docs/ATTRIBUTION.md, then set me up to control my local ComfyUI with it.
> My ComfyUI is on `http://127.0.0.1:8188`. Walk me through it and verify each
> step."

The agent will paste the MCP config, install the skill, and smoke-test the
connection for you. Everything below is the reference it (or you) will follow.

---

## What this is

A small, opinionated **local-first** bundle that lets an AI coding agent drive
your own ComfyUI over its REST API:

- **`mcp/`** — ready-to-paste MCP server configs (Claude Code / Cursor / generic).
  The MCP server itself is the community project
  [`artokun/comfyui-mcp`](https://github.com/artokun/comfyui-mcp) (MIT). We
  configure it for a *local* ComfyUI and document the official
  [Comfy-Org `comfy-mcp`](https://github.com/Comfy-Org/comfy-mcp) as the
  alternative.
- **`skills/comfy_local/`** — a **model-agnostic, pure-REST fallback skill** so
  your agent can still run ComfyUI even when the MCP server is offline. Ships a
  zero-dependency Python client (`scripts/comfy.py`), an 8GB-VRAM model
  shortlist, and minimal proven workflow skeletons.
- **`examples/`** — a minimal API-format workflow you can submit immediately.
- **`docs/ATTRIBUTION.md`** — exactly what we borrowed vs. what we wrote.

### Why not just the official MCP?

Comfy-Org now ships a first-party local MCP (`comfy-mcp`) and a hosted cloud
MCP. Both are great. We keep the **artokun** server as the default here because
it edits the live graph **node-by-node** and ships model-family expertise —
which matters when you're squeezing 20GB video models onto an 8GB laptop GPU.
The `comfy_local` skill is the belt-and-suspenders fallback that needs *nothing*
but Python's standard library. Pick either; this repo wires up both paths.

---

## Requirements

- A running **local ComfyUI** (Desktop or manual install), default
  `http://127.0.0.1:8188`.
- **Node.js** (for `npx comfyui-mcp`) — only if you use the MCP path.
- **Python 3.8+** — only the standard library is needed for the skill.
- An MCP-capable harness: Claude Code, Claude Desktop, Cursor, Codex, etc.

---

## Quick start

### 1. Register the MCP server

Add to your client config (e.g. `~/.claude.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "comfyui": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "comfyui-mcp@latest"],
      "env": { "COMFYUI_URL": "http://127.0.0.1:8188" }
    }
  }
}
```

More clients (Cursor, generic) in [`mcp/README.md`](./mcp/README.md).

### 2. Install the fallback skill

```bash
cp -r skills/comfy_local ~/.claude/skills/
```

### 3. Smoke-test

```bash
# server alive + GPU/VRAM
python skills/comfy_local/scripts/comfy.py stats

# what models does the server actually see?
python skills/comfy_local/scripts/comfy.py models checkpoints
python skills/comfy_local/scripts/comfy.py models diffusion_models
```

### 4. Run your first job

Open `examples/txt2img_minimal.json`, replace `REPLACE_WITH_YOUR_CHECKPOINT.safetensors`
with a filename from step 3, then:

```bash
python skills/comfy_local/scripts/comfy.py submit \
  --workflow examples/txt2img_minimal.json --download output/
```

---

## The `comfy_local` skill — golden rules

These are the hard-won rules baked into `SKILL.md`. They prevent the classic
ComfyUI-agent failures:

1. **Never assume a model filename.** Always `GET /models/{type}` first and pick
   what's actually on disk.
2. **Never assume a node class exists.** `GET /object_info/{NodeType}` before
   first use; if 404, tell the user to install it via ComfyUI Manager.
3. **Always submit API-format JSON**, never the UI graph format — `/prompt`
   rejects the latter.
4. **Always poll `/history/{prompt_id}`** for completion, not `/queue`.
5. **Always wire a save node** (`SaveImage` / `SaveVideo` / `VHS_VideoCombine`)
   or you get nothing back.
6. **Confirm before downloading large models** (they're 1–20 GB).
7. **Local = no auth, no API key.** If you're adding headers, you've confused
   local with cloud.

---

## Low-VRAM (8GB) field notes

Distilled from actually running heavy video models on an 8GB laptop GPU:

- Full-precision 14B video models **will OOM**. Use GGUF Q5/Q8 or fp8 variants.
- ComfyUI Desktop's automatic model offloading handles `--lowvram` for you.
- **Resolution is the dominant VRAM lever.** A 0.9MP canvas can OOM where 0.4MP
  (480p) runs fine — attention/latent cost scales with pixels, not just weights.
- Block-swap / offload lowers *resident* VRAM but not the *peak* during load.
- For jobs that won't fit, offload to **fal.ai** (bring your own key) instead of
  buying a bigger GPU — see `references/models.md`.

---

## Project layout

```
comfyui-local-mcp-skills/
├── README.md              ← you are here (EN)
├── README.zh-CN.md        ← 中文版
├── LICENSE                ← MIT (our files)
├── mcp/
│   └── README.md          ← paste-ready MCP configs
├── skills/
│   └── comfy_local/
│       ├── SKILL.md
│       ├── scripts/comfy.py
│       └── references/{models,workflows}.md
├── examples/
│   └── txt2img_minimal.json
└── docs/
    └── ATTRIBUTION.md     ← what's borrowed vs. ours
```

---

## Credit where credit is due

This is a **stitching job**, not an invention. The heavy lifting is done by:

- **[artokun/comfyui-mcp](https://github.com/artokun/comfyui-mcp)** (MIT) — the
  MCP server. ⭐ it if this helps you.
- **[Comfy-Org](https://github.com/Comfy-Org)** — official `comfy-mcp`,
  `comfy-skills`, and the agent-tools docs.
- **[comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)** — the
  server whose API we all speak.
- **MiniMax** — the H3 model family this toolkit was hardened on.

Full provenance map in [`docs/ATTRIBUTION.md`](./docs/ATTRIBUTION.md).

## License

MIT for the files authored/curated in this repo. Third-party components keep
their own licenses (see `LICENSE` and `docs/ATTRIBUTION.md`).
