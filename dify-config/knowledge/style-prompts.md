
---

## 文件 16：dify-config/knowledge/style-prompts.md

```markdown
# 画风提示词模板库

在 Dify 知识库中导入此文件，供 LLM 在生成分镜提示词时参考。

## 国漫水墨风格

prompt 后缀：chinese ink painting style, watercolor texture, traditional chinese art, elegant brush strokes, muted earth tones

## 日系动漫风格

prompt 后缀：anime style, vibrant colors, clean lineart, cel shading, studio ghibli inspired

## 写实摄影风格

prompt 后缀：photorealistic, cinematic lighting, 8k resolution, DSLR photo, shallow depth of field, natural lighting

## 赛博朋克风格

prompt 后缀：cyberpunk style, neon lights, futuristic cityscape, dark atmosphere, high tech low life, holographic elements

## 奇幻童话风格

prompt 后缀：fairy tale style, soft pastel colors, whimsical illustration, magical atmosphere, storybook art

## 复古胶片风格

prompt 后缀：vintage film photography, grain texture, warm tones, retro aesthetic, kodak portra 400

## 使用方式

1. 将此文件导入 Dify 知识库
2. 在 LLM 生成提示词时，通过 RAG 检索匹配的风格模板
3. 将风格后缀追加到基础 prompt 后面
