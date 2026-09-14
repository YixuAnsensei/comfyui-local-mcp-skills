---
name: comfy_local
description: Headless control of a locally-running ComfyUI server (default http://127.0.0.1:8188) via REST API. Model-agnostic — runs ANY workflow JSON, edits ANY node's parameters, lists installed nodes/models, uploads inputs, polls job status, downloads outputs. Use when the user wants to generate images/video/audio with ComfyUI, manage models, or batch-generate. Designed as a pure-file fallback for the artokun/comfyui-mcp MCP server (if MCP fails, this skill still works with just curl/python).
argument-hint: [what to generate or which ComfyUI op to perform]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit, WebFetch
---

# ComfyUI Local — Model-Agnostic Headless Control

You drive a **local ComfyUI** instance over REST. Default URL `http://127.0.0.1:8188` (override via `$COMFYUI_URL` env). No auth on localhost. **No model lock-in**: this skill never hardcodes a checkpoint name — it always asks the running server what's actually installed.

## Read These First (when needed)

- `references/models.md` — where to download models for 8GB-VRAM rigs (Wan 2.1 GGUF, LTX-Video, FLUX GGUF) and HuggingFace repo map.
- `references/workflows.md` — minimal proven API-format workflow templates (txt2img FLUX, LTX t2v, Wan 2.1 i2v). Use as **starting points**, never as the only option. Always discover the user's installed models first and substitute.
- `scripts/comfy.py` — a drop-in python helper that wraps submit / poll / download / list. Prefer calling this over hand-rolled curl.

## Golden Rules (do not violate)

1. **Never assume a model filename.** Always `GET /object_info/{Loader}` or `GET /models/{type}` first, then pick from what's actually on disk. If a workflow specifies `ckpt_name: "flux1-dev.safetensors"` but the user doesn't have it, swap to one they do — or open `references/models.md` and download (confirm with user first; files are 1-20 GB).
2. **Never assume a node class_type exists.** `GET /object_info/{NodeType}` before first use; if 404, the user must install the custom node via ComfyUI Manager. Tell them which one.
3. **Always submit API-format JSON, not graph-format.** API format is a flat dict keyed by string node IDs, each node = `{"class_type": "...", "inputs": {...}}`, references as `["node_id", output_index]`. Graph format (with `nodes`/`links` arrays) is for the UI only and WILL be rejected by `/prompt`.
4. **Always poll `/history/{prompt_id}`**, not `/queue`. `/history` is the completion signal. Empty body = still running. Populated = done.
5. **Always wire a save/output node.** A workflow whose final tensor goes nowhere produces nothing retrievable. Verify at least one `SaveImage` / `SaveVideo` / `VHS_VideoCombine` exists before submitting.
6. **Confirm before downloading large models.** Show user the list + URLs first.
7. **Local has no auth, no redirects, no API key.** If you find yourself adding headers, you're confusing local with cloud — stop.

## Core API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /system_stats` | GET | Confirm server alive; read GPU/VRAM/version |
| `GET /object_info` | GET | All installed node classes with inputs/outputs |
| `GET /object_info/{NodeType}` | GET | Single node's input spec (use before first use) |
| `GET /models/{type}` | GET | List models of a type: `checkpoints`, `loras`, `vae`, `diffusion_models`, `text_encoders`, `clip`, `clip_vision`, `controlnet`, `upscale_models`, `latent_upscale_models` |
| `POST /prompt` | POST | Queue a workflow `{"prompt": {...}}` → `{"prompt_id": "..."}` |
| `GET /queue` | GET | Queue status (running + pending) |
| `GET /history` | GET | All history |
| `GET /history/{prompt_id}` | GET | Poll THIS for completion |
| `GET /view?filename=X&subfolder=Y&type=output` | GET | Download output file |
| `POST /upload/image` | POST | Multipart upload (image, subfolder, type) |
| `POST /interrupt` | POST | Cancel current generation |
| `POST /free` | POST | `{"unload_models": true}` free VRAM |

## Standard Operating Procedure

### Step 0 — Confirm server alive
```bash
curl -s -m 3 $COMFYUI_URL/system_stats | python -c "import json,sys; d=json.load(sys.stdin); print(d['system']['comfyui_version'], d['devices'][0]['name'])"
```
If this fails → tell user to start ComfyUI Desktop. Stop.

### Step 1 — Discover what's installed
For image work:
```bash
curl -s $COMFYUI_URL/models/checkpoints | python -c "import json,sys; print('\n'.join(json.load(sys.stdin)))"
curl -s $COMFYUI_URL/models/diffusion_models | python -c "import json,sys; print('\n'.join(json.load(sys.stdin)))"
```
For video work also pull `vae`, `text_encoders`, `loras`. **Pick models the user actually has.** If none, route to `references/models.md` and confirm a download plan.

### Step 2 — Validate node inputs
```bash
curl -s $COMFYUI_URL/object_info/KSampler | python -c "import json,sys; d=json.load(sys.stdin); print(list(d['KSampler']['input']['required'].keys()))"
```
This catches the classic "template parameter name vs actual API name" divergences (e.g. `LTXVPreprocess.img_compression` not `num_latent_frames`).

### Step 3 — Build / load the API-format workflow
- If user has a workflow file: `Read` it. If it's graph-format (has `nodes` array + `links`), it CANNOT be POSTed directly — convert via ComfyUI Desktop's "Save (API Format)" menu, or rebuild API format by hand using `references/workflows.md` as scaffolding.
- If building from scratch: load the matching template from `references/workflows.md`, then **substitute model filenames with ones discovered in Step 1**, and **substitute node parameter names with values validated in Step 2**.

### Step 4 — Edit specific node parameters
To change a node's input without rewriting the whole workflow, edit the JSON in place with python or the Edit tool. Example: set prompt text in node "6":
```python
wf["6"]["inputs"]["text"] = USER_PROMPT
```
For seed: `wf["9"]["inputs"]["seed"] = 42`. For batch determinism use `"control_after_generate": "fixed"`.

### Step 5 — Submit & poll
Prefer the helper:
```bash
python scripts/comfy.py submit --workflow wf.json --timeout 1800 --download output/
```
This calls `/prompt`, polls `/history/{id}` every 5s, then downloads each output via `/view` into `output/`.

### Step 6 — Report
After completion, list the saved files with full paths. **Do not** inline-preview large mp4s — just report where they are.

## 8GB-VRAM Reality

This skill is tuned for low-VRAM rigs (8GB is the reference target). Pitfalls:
- Full-precision 14B video models (Wan 2.2 14B fp16) WILL OOM. Use GGUF Q5/Q8 or fp8 quantized variants only. See `references/models.md`.
- `--lowvram` semantics are automatic in ComfyUI Desktop (model offloading). No manual flag needed.
- LTX-Video native runs comfortably. Wan 2.1 480p GGUF Q5 is a realistic quality ceiling on 8GB.
- For jobs that OOM locally, offload to a **fal.ai cloud API** (bring your own key) rather than buying a bigger GPU. See `references/models.md` → "Cloud fallback".

## When MCP is also installed (artokun/comfyui-mcp)

If `comfyui-mcp` is registered in your MCP client config and its tools are available in the session (e.g. `mcp__comfyui__enqueue_workflow`, `mcp__comfyui__list_models`, `mcp__comfyui__modify_workflow`), **prefer MCP tools** — they're richer (validate, visualize, modify node-by-node). Use this skill when (a) MCP is offline / not loaded by the harness, or (b) you need the python helper for batch loops. Both paths speak the same REST API under the hood.

## Fallback Path: fal.ai cloud (bring your own key, no ComfyUI account)

For jobs that OOM locally, install the `ComfyUI-fal-API` custom nodes and set a `FAL_KEY` env var. When that path is desired, substitute the heavy local DiT node with a `FalAPI Video Generation` node in the workflow, populate `api_key` from `$FAL_KEY`. This bypasses Comfy account billing entirely — only fal bills. Details in `references/models.md`.

## Error Handling Cheat Sheet

| Symptom | Cause | Fix |
|---------|-------|-----|
| Connection refused | ComfyUI not running | Start ComfyUI Desktop, retry |
| 400 from `/prompt` with `node_errors` | Invalid node input | Read body, fix the named input. Usually wrong param name or model not on disk |
| `KeyError` for `class_type` | Custom node not installed | Read `object_info` to confirm absence, tell user to install via ComfyUI Manager |
| Job queued but never completes | OOM or model missing on disk | `GET /system_stats` for VRAM; check ComfyUI Desktop console log |
| Output file not retrievable | No save node wired | Re-validate workflow has `SaveImage` / `SaveVideo` |
| Polling returns `{}` forever | Still running, or 4xx silently failed | Check `/queue` for the prompt_id; if absent and `/history` empty, it errored at queue time |

## What This Skill Does NOT Do

- Does not install ComfyUI itself (user already has Desktop).
- Does not auto-install custom nodes — only tells user which to install.
- Does not hardcode any model — always discovers from server.
- Does not call Comfy Cloud or use a Comfy account key.
