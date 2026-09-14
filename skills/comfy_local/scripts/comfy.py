#!/usr/bin/env python3
"""
comfy.py — minimal local ComfyUI REST client for the comfy_local skill.

Submits an API-format workflow, polls /history/{id} until done,
downloads every output file into a target dir. Model-agnostic.

Usage:
  python comfy.py stats                          # confirm server + GPU/VRAM
  python comfy.py models {type}                   # list models of a type
  python comfy.py nodes [NodeType]                # list all node classes / single node spec
  python comfy.py submit --workflow wf.json [--timeout 1800] [--download ./output]
  python comfy.py upload --image path.png [--subfolder input]
  python comfy.py interrupt                       # cancel current job
  python comfy.py free                            # unload models, free VRAM

Env:
  COMFYUI_URL  default http://127.0.0.1:8188
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

BASE = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")


def _get(path):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=15) as r:
        return json.loads(r.read())


def _post(path, body_bytes, headers=None):
    req = urllib.request.Request(
        f"{BASE}{path}", data=body_bytes,
        headers=headers or {"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def cmd_stats(_):
    d = _get("/system_stats")
    s = d["system"]
    print(f"ComfyUI {s.get('comfyui_version')}  os={s.get('os')}")
    for i, dev in enumerate(d.get("devices", [])):
        vram_total = dev.get("vram_total", 0) / 1e9
        vram_free = dev.get("vram_free", 0) / 1e9
        print(f"  gpu[{i}]: {dev.get('name')}  vram {vram_free:.1f}/{vram_total:.1f} GB free")


def cmd_models(args):
    path = f"/models/{args.type}"
    try:
        data = _get(path)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} for {path}: {e.read().decode(errors='ignore')[:200]}")
        sys.exit(1)
    if isinstance(data, dict):
        names = list(data.keys())
    else:
        names = list(data)
    print(f"\n".join(names) if names else "(empty)")


def cmd_nodes(args):
    if args.NodeType:
        try:
            d = _get(f"/object_info/{args.NodeType}")
            node = d[args.NodeType]
            print(f"== {args.NodeType} ==")
            print("category:", node.get("category"))
            print("inputs:")
            req_in = node["input"].get("required", {})
            for k, v in req_in.items():
                print(f"  {k}: {v}")
            opt_in = node["input"].get("optional", {})
            for k, v in opt_in.items():
                print(f"  (opt) {k}: {v}")
            print("outputs:", node.get("output", []))
        except urllib.error.HTTPError as e:
            print(f"Node not found or server error: {e.code}")
            print("Hint: is the custom node installed?")
            sys.exit(1)
    else:
        d = _get("/object_info")
        print("\n".join(sorted(d.keys())))


def _submit(prompt_obj):
    body = json.dumps({"prompt": prompt_obj}).encode("utf-8")
    out = json.loads(_post("/prompt", body))
    return out["prompt_id"], out.get("number")


def _history(prompt_id):
    try:
        d = _get(f"/history/{prompt_id}")
        return d.get(prompt_id)
    except urllib.error.HTTPError:
        return None


def _download(filename, subfolder, file_type, dest_dir):
    q = f"?filename={urllib.parse.quote(filename)}&subfolder={urllib.parse.quote(subfolder or '')}&type={file_type}"
    url = f"{BASE}/view{q}"
    with urllib.request.urlopen(url, timeout=60) as r:
        blob = r.read()
    safe = filename.replace("/", "_")
    p = Path(dest_dir) / safe
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(blob)
    return str(p), len(blob)


def cmd_submit(args):
    wf = json.loads(Path(args.workflow).read_text(encoding="utf-8"))
    pid, num = _submit(wf)
    print(f"queued prompt_id={pid}  number={num}")
    start = time.time()
    last_print = 0
    while time.time() - start < args.timeout:
        h = _history(pid)
        if h is not None:
            status = h.get("status", {})
            if status.get("status_str") == "error":
                print("ERROR during execution:", json.dumps(status, ensure_ascii=False)[:1000])
                sys.exit(2)
            outputs = h.get("outputs", {})
            print(f"COMPLETED in {time.time()-start:.1f}s  {len(outputs)} output node(s)")
            if args.download:
                for node_id, node_out in outputs.items():
                    for cat in ("images", "gifs", "videos", "audio"):
                        for item in node_out.get(cat, []):
                            fn = item.get("filename")
                            sf = item.get("subfolder", "")
                            tp = item.get("type", "output")
                            try:
                                path, size = _download(fn, sf, tp, args.download)
                                print(f"  [{cat}] saved {path} ({size} bytes)")
                            except Exception as e:
                                print(f"  [{cat}] FAILED {fn}: {e}")
            else:
                for node_id, node_out in outputs.items():
                    for cat in ("images", "gifs", "videos", "audio"):
                        for item in node_out.get(cat, []):
                            print(f"  [{cat}] {item.get('filename')} subfolder={item.get('subfolder','')} type={item.get('type','output')}")
            return
        if time.time() - last_print > 10:
            elapsed = time.time() - start
            print(f"  ...waiting {elapsed:.0f}s (polling /history/{pid})")
            last_print = time.time()
        time.sleep(5)
    print(f"TIMEOUT after {args.timeout}s. Job may still be running on the ComfyUI queue.")
    print(f"  Poll manually: curl $COMFYUI_URL/history/{pid}")
    sys.exit(3)


def cmd_upload(args):
    import mimetypes
    path = Path(args.image)
    if not path.exists():
        print(f"file not found: {path}")
        sys.exit(1)
    boundary = "----comfy_boundary" + str(int(time.time() * 1000))
    parts = []
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'
        f"Content-Type: {mimetypes.guess_type(path.name)[0] or 'application/octet-stream'}\r\n\r\n"
        .encode())
    parts.append(path.read_bytes())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(f'Content-Disposition: form-data; name="subfolder"\r\n\r\n{args.subfolder}\r\n'.encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(f'Content-Disposition: form-data; name="type"\r\n\r\ninput\r\n'.encode())
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        f"{BASE}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    print(json.dumps(out, ensure_ascii=False))


def cmd_interrupt(_):
    _post("/interrupt", b"")
    print("interrupt sent")


def cmd_free(_):
    _post("/free", json.dumps({"unload_models": True, "free_memory": True}).encode())
    print("models unloaded, vram free requested")


def main():
    ap = argparse.ArgumentParser(prog="comfy.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stats", help="print server version + GPU/VRAM").set_defaults(func=cmd_stats)
    p_models = sub.add_parser("models", help="list models of a type")
    p_models.add_argument("type", help="e.g. checkpoints, loras, vae, diffusion_models, text_encoders, clip, controlnet, upscale_models")
    p_models.set_defaults(func=cmd_models)
    p_nodes = sub.add_parser("nodes", help="list all node classes, or one node's spec")
    p_nodes.add_argument("NodeType", nargs="?")
    p_nodes.set_defaults(func=cmd_nodes)

    p_sub = sub.add_parser("submit", help="queue API-format workflow, poll, download")
    p_sub.add_argument("--workflow", required=True, help="path to API-format .json")
    p_sub.add_argument("--timeout", type=int, default=1800)
    p_sub.add_argument("--download", help="dir to save outputs into; omit to only print output locations")
    p_sub.set_defaults(func=cmd_submit)

    p_up = sub.add_parser("upload", help="upload image to /input folder (multipart)")
    p_up.add_argument("--image", required=True)
    p_up.add_argument("--subfolder", default="input")
    p_up.set_defaults(func=cmd_upload)

    sub.add_parser("interrupt", help="cancel current generation").set_defaults(func=cmd_interrupt)
    sub.add_parser("free", help="unload models, free VRAM").set_defaults(func=cmd_free)

    ns = ap.parse_args()
    try:
        ns.func(ns)
    except urllib.error.URLError as e:
        print(f"Cannot reach ComfyUI at {BASE}: {e}")
        print("Is ComfyUI Desktop running? Check the port matches COMFYUI_URL env (default 8188).")
        sys.exit(1)


if __name__ == "__main__":
    main()
