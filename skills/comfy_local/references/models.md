# 8GB VRAM 模型清单与 fal 混合方案

面向低显存机器(参考目标 8GB VRAM)。思路 = 本地轻量跑预览 + fal.ai 云端跑重活,全程不碰 Comfy 账号付费。

## 本地(8GB 可跑)首选模型

### 视频 — T2V / I2V
| 模型 | 文件 | 体积 | 8G 体验 |
|------|------|------|---------|
| **LTX-Video 0.9.1 / LTX 2.3** | `ltx-video-2b-...safetensors` | ~2-6 GB | ⭐ 最快,首选入门。GGUF 版可减轻显存 |
| **Wan 2.1 I2V 480P GGUF Q5** | `wan2.1-i2v-14b-480p-Q5_K_M.gguf` | ~8 GB | ⭐ 画质天花板(8G 范围内)。需要 `umt5_xxl` 文本编码器 + `wan_2.1_vae` |
| Wan 2.2 GGUF Q4 + Lightx2v | `wan2.2-t2v-14b-Q4_K_S.gguf` + lightning lora | ~7 GB | 可跑,需 lightx2v 加速节点 |
| HunyuanVideo GGUF Q4 | `hunyuan_video_13b...Q4.gguf` | ~8 GB | ⚠️ 勉强,推荐云端 |
| CogVideoX 1.5 2B/5B GGUF | `cogvideox-5b-Q4.gguf` | ~3-5 GB | 可跑,生态尚可 |

### 生图(首帧/基底)
| 模型 | 文件 | 体积 |
|------|------|------|
| **FLUX.1 GGUF Q4/Q5** | `flux1-dev-Q4_K_S.gguf` | ~6 GB | 写实与文字渲染强,8G 可跑 |
| SDXL / SD1.5 | `*.safetensors` | ~2-7 GB | 经典、低门槛 |

## HuggingFace 仓库速查(下模型用 curl -L)

| Repo | 含什么 |
|------|--------|
| `Comfy-Org/Wan_2.1_ComfyUI_repackaged` | Wan 2.1 t2v/i2v + umt5_xxl 文本编码器 + VAE |
| `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` | Wan 2.2 + lightning loras + VAE |
| `Lightricks/LTX-Video` | LTX-Video 官方 |
| `city96/LTX-Video` | LTX GGUF 量化 |
| `Kijai/LTX2.3_comfy` | LTX 2.3 fp8 |
| `Comfy-Org/HunyuanVideo_ComfyUI` | HunyuanVideo |

### 直接下载命令模板(⚠️ 体积大,先确认再下)
```bash
# convert HF blob URL to resolve URL, follow redirect
# 把 <MODELS_DIR> 换成你服务器真正在看的 diffusion_models 目录(用 GET /models/diffusion_models 确认)
curl -L --progress-bar -o "<MODELS_DIR>/diffusion_models/wan2.1-i2v-14b-480p-Q5_K_M.gguf" \
  "https://huggingface.co/city96/Wan2.1-GGUF/resolve/main/wan2.1-i2v-14b-480p-Q5_K_M.gguf"
```

## 本地目录布局(ComfyUI Desktop 示例)

Desktop 版把模型放在共享目录,典型路径:

```
<ComfyUI>/models/
├── diffusion_models/   # Wan/LTX/Hunyuan 主模型(GGUF 放这)
├── vae/                # wan_2.1_vae.safetensors, ltx vae
├── text_encoders/      # umt5_xxl_fp8, t5xxl_fp16, clip_l
├── loras/              # lightning loras 等
├── clip/               # 备用文本编码器目录
└── checkpoints/        # FLUX/SDXL 整合包(可选)
```

Desktop 常见实际根目录:`D:/Comfy-Desktop/ComfyUI-Installs/ComfyUI/models/` 或 `.../ComfyUI-Shared/models/`(取决于 extra_model_paths 配置)。用 `GET /models/{type}` 让服务器告诉你它真正在看哪里,别猜。

## Cloud Fallback — fal.ai(自带 key,不碰 Comfy 账号)

安装 `ComfyUI-fal-API` 自定义节点,用 `$FAL_KEY` 环境变量填 key。

何时切换到 fal:
- 本地 8G OOM(显存不够)
- 要跑 Wan 2.2 14B / full-precision 大模型
- 要批量跑(Batch 多 prompt)

用法:把工作流里本地 DiT 节点(KSampler + ModelLoader)替换成 `FalAPI Video Generation` 节点:
- 节点 `api_key` 填 `$FAL_KEY`(或环境变量)
- `model` 选 fal 托管的(kling / wan / hailuo / minimax / pika)
- 计费走 fal,~ $0.05-0.5/次,视模型

云端所有视频模型在 fal 用同一套 API,所以**一个 fal 节点 ≈ 接所有视频模型**,不用装一堆节点。

## Comfy Cloud — 本 skill 默认不走

本 skill 定位为纯本地 + fal 自带 key 路线,默认不调用任何 `cloud.comfy.org` 端点、不引用 `COMFY_API_KEY`、Partner Nodes 一律绕过(用 fal 自带 key 路线替代)。如果你要用官方 Comfy Cloud,请改用官方 `comfy-mcp` / `comfy-cloud-mcp`。
