# MCP server config examples

This repo does **not** ship its own MCP server binary. The MCP layer is the
excellent community project [`artokun/comfyui-mcp`](https://github.com/artokun/comfyui-mcp)
(MIT), which we run against a **local** ComfyUI. What we add on top is the
`comfy_local` skill (a pure-REST fallback) plus the low-VRAM / H3 field notes.

Below are ready-to-paste configs. Replace the path/port with your own.

---

## Claude Code / Claude Desktop (`claude_desktop_config.json` or `~/.claude.json`)

```json
{
  "mcpServers": {
    "comfyui": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "comfyui-mcp@latest"],
      "env": {
        "COMFYUI_URL": "http://127.0.0.1:8188"
      }
    }
  }
}
```

`comfyui-mcp` auto-detects a local ComfyUI install and port. `COMFYUI_URL` pins
it explicitly (recommended when you run more than one instance).

## Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "comfyui": {
      "command": "npx",
      "args": ["-y", "comfyui-mcp@latest"],
      "env": { "COMFYUI_URL": "http://127.0.0.1:8188" }
    }
  }
}
```

## Any other MCP client

The server is a stdio MCP server launched via `npx -y comfyui-mcp@latest`.
Point your client at that command and set `COMFYUI_URL`.

---

## Installing the `comfy_local` skill alongside the MCP

The skill is a plain folder. Drop it into your harness's skills directory:

- **Claude Code:** `~/.claude/skills/comfy_local/`
- **Project-scoped:** `<repo>/.claude/skills/comfy_local/`

```bash
cp -r skills/comfy_local ~/.claude/skills/
```

The skill needs **no** MCP server — it talks to ComfyUI over REST with only
Python's standard library (`scripts/comfy.py`). It is the fallback that keeps
working when the MCP is offline, and the batch-loop helper when it is online.

---

## Official Comfy-Org MCP (for comparison)

Comfy-Org also ships a first-party local MCP, `comfy-mcp` (pip), and a hosted
cloud MCP at `https://cloud.comfy.org/mcp`. It is a thinner "submit + fetch"
surface and (for cloud) needs a Comfy account/subscription. We keep using the
artokun server locally because it edits the live graph node-by-node and ships
model-family expertise — better for deep low-VRAM work. Both are valid; pick
what fits. See `docs/ATTRIBUTION.md`.
