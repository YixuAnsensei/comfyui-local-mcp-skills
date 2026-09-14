# ComfyUI 本地 MCP + Skills（中文）

> 用 **本地** ComfyUI，从 Claude Code、Cursor 或任何支持 MCP 的 AI harness 直接驱动
> —— 专为 **低显存机器（8GB）** 和 MiniMax H3 这类重型视频模型调校。
> 一份可直接粘贴的 MCP 配置 + 一个纯 REST 兜底 skill。

[English](./README.md) · [致谢与来源](./docs/ATTRIBUTION.md) · [MIT](./LICENSE)

---

## 一句话上手 —— 用本仓库最快的方式

**别从头读。把仓库 clone 下来，直接丢给你的 AI agent（Claude Code / Cursor / Codex），
对它说：**

> "这是一个叫 comfyui-local-mcp-skills 的仓库。读 README 和 docs/ATTRIBUTION.md，
> 然后帮我把本地 ComfyUI 接上它。我的 ComfyUI 在 `http://127.0.0.1:8188`。
> 一步步带我配好，每一步都验证一下。"

agent 会帮你粘贴 MCP 配置、装好 skill、并冒烟测试连通性。下面所有内容就是它（或你）
会照着做的参考手册。

---

## 这是什么

一套小而精的 **本地优先** 工具包，让 AI 编程 agent 通过 REST API 驱动你自己的 ComfyUI：

- **`mcp/`** —— 可直接粘贴的 MCP server 配置（Claude Code / Cursor / 通用）。
  MCP server 本体是社区项目
  [`artokun/comfyui-mcp`](https://github.com/artokun/comfyui-mcp)（MIT）。我们把它
  配置成跑 **本地** ComfyUI，并把官方
  [Comfy-Org `comfy-mcp`](https://github.com/Comfy-Org/comfy-mcp) 作为对照方案写进文档。
- **`skills/comfy_local/`** —— 一个 **模型无关、纯 REST 的兜底 skill**，即使 MCP server
  掉线，agent 仍能跑 ComfyUI。附带一个零依赖 Python 客户端（`scripts/comfy.py`）、
  一份 8GB 显存模型清单、以及最小可用的工作流骨架。
- **`examples/`** —— 一个可立即提交的最小 API 格式工作流。
- **`docs/ATTRIBUTION.md`** —— 精确说明哪些是借鉴的、哪些是我们写的。

### 为什么不用官方 MCP？

Comfy-Org 现在也发布了一方的本地 MCP（`comfy-mcp`）和云端 MCP。两者都不错。我们把
**artokun** 版作为这里的默认，因为它能 **逐节点** 编辑实时画布、并内置模型族专家知识
—— 当你想把 20GB 视频模型塞进 8GB 笔记本显卡时，这点很关键。`comfy_local` skill 则是
"双保险"兜底，**只需要 Python 标准库**。两条路都给你接好了，按需选。

---

## 前置要求

- 一个运行中的 **本地 ComfyUI**（Desktop 或手动安装），默认 `http://127.0.0.1:8188`。
- **Node.js**（用于 `npx comfyui-mcp`）—— 仅走 MCP 路线时需要。
- **Python 3.8+** —— skill 只用标准库。
- 一个支持 MCP 的 harness：Claude Code、Claude Desktop、Cursor、Codex 等。

---

## 快速开始

### 1. 注册 MCP server

加到你的客户端配置（如 `~/.claude.json` 或 `claude_desktop_config.json`）：

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

更多客户端（Cursor、通用）见 [`mcp/README.md`](./mcp/README.md)。

### 2. 安装兜底 skill

```bash
cp -r skills/comfy_local ~/.claude/skills/
```

### 3. 冒烟测试

```bash
# 服务器是否活着 + GPU/显存
python skills/comfy_local/scripts/comfy.py stats

# 服务器到底看到了哪些模型？
python skills/comfy_local/scripts/comfy.py models checkpoints
python skills/comfy_local/scripts/comfy.py models diffusion_models
```

### 4. 跑第一个任务

打开 `examples/txt2img_minimal.json`，把 `REPLACE_WITH_YOUR_CHECKPOINT.safetensors`
换成第 3 步里真实存在的文件名，然后：

```bash
python skills/comfy_local/scripts/comfy.py submit \
  --workflow examples/txt2img_minimal.json --download output/
```

---

## `comfy_local` skill —— 黄金法则

这些是写进 `SKILL.md` 的血泪规则，专门防止 ComfyUI-agent 的经典翻车：

1. **永远不要假设模型文件名。** 先 `GET /models/{type}`，只挑磁盘上真实存在的。
2. **永远不要假设某个节点类存在。** 首次用前 `GET /object_info/{NodeType}`；404 就
   告诉用户去 ComfyUI Manager 装。
3. **永远提交 API 格式 JSON**，不要提交 UI graph 格式 —— `/prompt` 会拒收后者。
4. **永远轮询 `/history/{prompt_id}`** 判断完成，而不是 `/queue`。
5. **永远接一个保存节点**（`SaveImage` / `SaveVideo` / `VHS_VideoCombine`），否则啥也拿不到。
6. **下载大模型前先确认**（动辄 1–20 GB）。
7. **本地 = 无鉴权、无 API key。** 一旦你在加 header，就是把本地和云端搞混了。

---

## 低显存（8GB）实战笔记

从真的在 8GB 笔记本显卡上跑重型视频模型里总结出来的：

- 全精度 14B 视频模型 **必 OOM**。用 GGUF Q5/Q8 或 fp8 量化版。
- ComfyUI Desktop 的自动模型卸载已经帮你处理了 `--lowvram`。
- **分辨率是显存的主导因素。** 0.9MP 画布会 OOM 的，0.4MP（480p）能稳跑 ——
  attention/latent 开销随像素涨，不只是权重。
- block-swap / offload 降低的是 **常驻** 显存，不是加载时的 **峰值**。
- 装不下的任务，offload 到 **fal.ai**（自带 key），而不是买更大的卡 —— 见
  `references/models.md`。

---

## 目录结构

```
comfyui-local-mcp-skills/
├── README.md              ← 英文主文档
├── README.zh-CN.md        ← 你在这里（中文）
├── LICENSE                ← MIT（我们的文件）
├── mcp/
│   └── README.md          ← 可直接粘贴的 MCP 配置
├── skills/
│   └── comfy_local/
│       ├── SKILL.md
│       ├── scripts/comfy.py
│       └── references/{models,workflows}.md
├── examples/
│   └── txt2img_minimal.json
└── docs/
    └── ATTRIBUTION.md     ← 借鉴 vs 自研
```

---

## 致谢（该给的 credit 一个不少）

这是一件 **缝合** 的活，不是从零发明。真正的重活是这些人干的：

- **[artokun/comfyui-mcp](https://github.com/artokun/comfyui-mcp)**（MIT）—— MCP server
  本体。觉得有用请去 ⭐ 它。
- **[Comfy-Org](https://github.com/Comfy-Org)** —— 官方 `comfy-mcp`、`comfy-skills`
  和 agent-tools 文档。
- **[comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)** —— 我们共同
  说的那套 API 的服务端。
- **MiniMax** —— 本工具包调校所依托的 H3 模型族。

完整来源地图见 [`docs/ATTRIBUTION.md`](./docs/ATTRIBUTION.md)。

## 许可证

本仓库自研/整理的文件为 MIT。第三方组件保留各自许可证（见 `LICENSE` 与
`docs/ATTRIBUTION.md`）。
