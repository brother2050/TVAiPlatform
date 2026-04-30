# 工具 1：generate_image（生图）

## 基本信息

- **工具名称**：generate_image
- **描述**：调用外部生图引擎（如 ComfyUI / SD WebUI）生成图片
- **请求方式**：POST
- **请求 URL**：根据实际引擎配置

## URL 配置说明

不同引擎的 URL 不同：

| 引擎 | URL 示例 |
|:---|:---|
| ComfyUI | `http://localhost:8188/api/prompt` |
| SD WebUI | `http://localhost:7860/sdapi/v1/txt2img` |
| 自定义服务 | `http://localhost:8000/generate` |

> 注意：由于不同引擎的 API 格式差异较大，建议在引擎前面加一个薄适配层（Python 脚本），统一输入输出格式。或者直接使用 Dify 的 HTTP 请求节点，在节点内用代码做格式转换。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| prompt | string | 是 | - | 生图提示词（英文） |
| negative_prompt | string | 否 | blurry, low quality | 负面提示词 |
| width | number | 否 | 1024 | 图片宽度 |
| height | number | 否 | 576 | 图片高度 |
| steps | number | 否 | 30 | 采样步数 |
| seed | number | 否 | -1 | 随机种子（-1 为随机） |

## 请求体示例

```json
{
  "prompt": "A young man sitting at office desk, opening a mysterious letter, warm lighting, detailed, cinematic",
  "negative_prompt": "blurry, low quality, distorted, deformed, extra limbs",
  "width": 1024,
  "height": 576,
  "steps": 30,
  "seed": -1
}
响应格式
{
  "image_url": "/storage/projects/proj_001/segments/seg_001/shots/shot_001/v1.png",
  "seed": 12345
}
适配层建议

如果直接对接引擎 API 格式不匹配，可以写一个薄适配层：
Dify Tool → http://localhost:5001/api/adapter/image → 引擎 API
适配层接收统一格式的请求，转换为引擎特定格式，再将引擎响应转回统一格式。
