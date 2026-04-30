## 文件 18：docs/troubleshooting.md

```markdown
# 问题排查指南

## 服务启动问题

### 端口被占用

```
错误：Address already in use
```

解决：
```bash
# 查找占用端口的进程
lsof -i :5005
lsof -i :5003

# 杀掉进程
kill <PID>

# 或使用停止脚本
./scripts/stop-all.sh
```

### Python 模块找不到

```
错误：ModuleNotFoundError: No module named 'shared'
```

解决：确保从项目根目录启动，且虚拟环境已激活。
```bash
cd /path/to/project-root
source venv/bin/activate
python -m services.project_service.app
```

### 数据库初始化失败

```
错误：database is locked
```

解决：
- 确认没有其他进程在使用数据库文件
- 删除 `data/app.db` 重新初始化

---

## 生图引擎问题

### 引擎调用超时

```
错误：timeout
```

排查：
1. 确认引擎是否在运行
2. 确认引擎地址是否正确
3. 确认引擎当前是否在处理其他任务（排队中）
4. 增大超时时间（生图可能需要 60-120 秒）

### 引擎返回格式不匹配

```
错误：KeyError: 'image_url'
```

排查：
1. 查看引擎实际返回的 JSON 格式
2. 修改 Dify 工作流中的代码节点，适配实际格式
3. 或在引擎前加适配层统一格式

### 引擎拒绝生成（安全过滤）

```
错误：NSFW content detected
```

解决：
1. 修改提示词，避免敏感描述
2. 在引擎端调整安全过滤级别
3. 使用更中性的描述替代

---

## TTS 引擎问题

### TTS 生成的音频无声或异常

排查：
1. 确认输入文本不为空
2. 确认 speaker ID 有效
3. 用引擎自带的测试页面验证
4. 检查音频文件是否正确保存

### TTS 中文发音不准确

解决：
1. 确认 TTS 引擎支持中文
2. 尝试不同的 TTS 引擎（Fish Speech / CosyVoice）
3. 调整文本预处理（如添加拼音标注）

---

## 视频合成问题

### FFmpeg 报错

```
错误：No such file or directory
```

排查：
1. 确认 FFmpeg 已安装：`ffmpeg -version`
2. 确认图片和音频文件路径正确
3. 确认文件存在且可读

### 合成后没有声音

排查：
1. 确认音频文件存在且不为空
2. 确认音频文件格式正确（WAV / MP3）
3. 检查 FFmpeg 合成命令的音频映射

### 字幕不显示

排查：
1. 确认字幕文件已生成（.ass 或 .srt）
2. 确认字幕时间轴与视频对齐
3. 确认系统安装了中文字体
4. 尝试使用 SRT 替代 ASS

### 转场效果失败

```
错误：xfade filter not found
```

排查：
1. 确认 FFmpeg 版本 >= 4.3（xfade 在 4.3 引入）
2. 升级 FFmpeg：`sudo apt update && sudo apt install ffmpeg`
3. 如果无法升级，将转场类型设为 `none`

---

## Dify 工作流问题

### 工作流执行中断

排查：
1. 在 Dify 界面查看工作流运行日志
2. 找到失败的节点
3. 检查该节点的输入变量是否有值
4. 检查对应的 HTTP 请求是否成功

### LLM 返回非 JSON 格式

解决：
1. 在提示词中强调"严格按 JSON 格式输出，不要输出任何其他内容"
2. 在代码节点中增加容错处理（正则提取 JSON）
3. 增加重试逻辑
4. 换一个更听话的模型

### 变量传递失败

排查：
1. 确认上游节点的输出变量名与下游节点的引用名一致
2. 确认变量类型匹配（字符串 vs 数字 vs 对象）
3. 在关键节点后添加"日志"节点查看变量值
```

---
