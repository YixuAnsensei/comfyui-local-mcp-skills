# 8GB VRAM 最小可用工作流模板(API 格式)

以下均为可直接 POST 给 `/prompt` 的 API 格式(JSON)。**用前务必先 `GET /models/{type}` 查服务器实际装了什么模型,再把 `unet_name` / `ckpt_name` / `vae_name` / `clip_name` 等字段替换成真实文件名**——这里只是结构模板。

## 1. FLUX GGUF 文生图(8G 最稳)

8GB 量化版 FLUX 跑 txt2img,~2-4 min/张。

```python
PROMPT = "cinematic photo of a misty mountain village at dawn"
PREFIX = "20260802_village"

wf = {
    "1": {"class_type": "UNETLoader", "inputs": {
        "unet_name": "flux1-dev-Q4_K_S.gguf",  # ← 替换为用户实际有的
        "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5xxl_fp16.safetensors", "type": "flux"}},
    "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "clip_l.safetensors", "type": "flux"}},
    "4": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "t5xxl_fp16.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"}},
    "5": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["4", 0]}},
    "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "8": {"class_type": "KSampler", "inputs": {
        "seed": 42,
        "control_after_generate": "fixed",
        "steps": 20, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1,
        "model": ["1", 0], "positive": ["6", 0], "negative": ["6", 0], "latent_image": ["7", 0]}},
    "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["5", 0]}},
    "10": {"class_type": "SaveImage", "inputs": {"filename_prefix": PREFIX, "images": ["9", 0]}},
}
```

## 2. LTX-Video 文生视频(8G 最快的视频入门)

~30-60s 跑 4s 768x512 视频。

```python
PROMPT = "a cat walking in a sunny garden, cinematic"
PREFIX = "video/20260802_cat"  # video/ 前缀让它存到 output/video/

wf = {
    "1": {"class_type": "CheckpointLoaderSimple", "inputs": {
        "ckpt_name": "ltx-video-2b-v0_9_1.safetensors"}},  # ← 替换
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5xxl_fp16.safetensors", "type": "t5"}},
    "5": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality", "clip": ["2", 0]}},
    "7": {"class_type": "EmptyLatentVideo", "inputs": {"width": 768, "height": 512, "length": 97, "batch_size": 1}},
    "8": {"class_type": "LTXVConditioning", "inputs": {
        "positive": ["5", 0], "negative": ["6", 0], "frame_rate": 24.0, "latents": ["7", 0]}},
    "9": {"class_type": "KSampler", "inputs": {
        "seed": 42, "control_after_generate": "fixed",
        "steps": 30, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1,
        "model": ["1", 0], "positive": ["8", 0], "negative": ["8", 1], "latent_image": ["8", 0]}},
    "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["1", 2]}},
    "11": {"class_type": "SaveAnimatedWEBP", "inputs": {
        "images": ["10", 0], "filename_prefix": PREFIX, "fps": 24.0, "lossless": False, "quality": 80, "method": "default"}},
}
```

## 3. Wan 2.1 I2V(8G 画质最优,但慢,~10-20 min)

最简版,真正跑要接 CLIPLoader(umt5_xxl)+ VAELoader(wan_2.1_vae)+ LTX/Q5 GGUF 国内常见复刻。详细高频模板见社区 workflow,如 `Comfy-Org/Wan_2.1_ComfyUI_repackaged` README 自带 workflow。

骨架:
```python
"1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8.safetensors", "type": "wan"}},
"3": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
"75": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.1-i2v-14b-480p-Q5_K_M.gguf", "weight_dtype": "default"}},
"89": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["1", 0]}},
# ... LoadImage + VAE Encode Image + KSampler + VAEDecode + SaveVideo (或 SaveAnimatedWEBP)
```

完整模板强烈建议从 Civitai 找一个标注 "Wan 2.1 I2V GGUF 8G" 的高赞工作流拖入 ComfyUI Desktop,然后 "Save (API Format)" 导出 .json 本地保留。**不要从头手搓**,组件多容易错。

## 后处理节点(可拼接到任何视频工作流末尾)

- **RIFE 补帧**:`RIFE VFI` 节点(source → 输入帧序列,fps ×2/×4)
- **超分**:`Upscale Image (using model)` 节点 + `RealESRGAN_x4` 模型
- **导出 mp4 4K**:`VHS_VideoCombine` 节点,format=video/h264-mp4

## 批量模式

参考 helper `scripts/comfy.py` 的 `submit` + 修改 seed 循环:

```python
import subprocess, json
prompts = ["...", "..."]
for i, p in enumerate(prompts):
    wf_template["9"]["inputs"]["seed"] = 42 + i
    wf_template["6"]["inputs"]["text"] = p
    json.dump(wf_template, open(f"wf_{i}.json", "w"))
    subprocess.run(["python", "comfy.py", "submit", "--workflow", f"wf_{i}.json",
                    "--download", "output/"])
```
