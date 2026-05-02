对，目前只有 API 文档，没有操作界面。加一个轻量前端。

---

## 方案：在 project_manager 中加 Web 页面

用 FastAPI 的 Jinja2 模板渲染，不需要额外前端框架。

### 安装依赖

```bash
pip install jinja2
```

### 新增文件：project_manager/templates/base.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}文章转视频{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, "Microsoft YaHei", sans-serif;
            background: #0f0f0f;
            color: #e0e0e0;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }

        /* 顶栏 */
        .header {
            background: #1a1a1a;
            border-bottom: 1px solid #333;
            padding: 16px 0;
            margin-bottom: 24px;
        }
        .header .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 20px; color: #fff; }
        .header a { color: #6aa6ff; text-decoration: none; margin-left: 20px; }
        .header a:hover { text-decoration: underline; }

        /* 卡片 */
        .card {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .card h2 { font-size: 16px; margin-bottom: 12px; color: #fff; }
        .card h3 { font-size: 14px; margin-bottom: 8px; color: #ccc; }

        /* 表格 */
        table { width: 100%; border-collapse: collapse; }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #2a2a2a;
            font-size: 14px;
        }
        th { color: #999; font-weight: normal; }
        td a { color: #6aa6ff; text-decoration: none; }
        td a:hover { text-decoration: underline; }

        /* 状态标签 */
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        .badge-pending { background: #333; color: #999; }
        .badge-rendered { background: #1a3a1a; color: #6c6; }
        .badge-completed { background: #1a2a4a; color: #6af; }
        .badge-confirmed { background: #2a2a1a; color: #ca6; }

        /* 按钮 */
        .btn {
            display: inline-block;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            font-size: 13px;
            cursor: pointer;
            text-decoration: none;
            color: #fff;
        }
        .btn-primary { background: #2563eb; }
        .btn-primary:hover { background: #1d4ed8; }
        .btn-success { background: #16a34a; }
        .btn-success:hover { background: #15803d; }
        .btn-warning { background: #d97706; }
        .btn-warning:hover { background: #b45309; }
        .btn-danger { background: #dc2626; }
        .btn-danger:hover { background: #b91c1c; }
        .btn-sm { padding: 4px 10px; font-size: 12px; }

        /* 图片缩略图 */
        .thumb {
            width: 160px;
            height: 90px;
            object-fit: cover;
            border-radius: 4px;
            border: 1px solid #333;
            background: #111;
        }
        .thumb-placeholder {
            width: 160px;
            height: 90px;
            border-radius: 4px;
            border: 1px dashed #333;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #555;
            font-size: 12px;
        }

        /* 进度条 */
        .progress-bar {
            height: 6px;
            background: #333;
            border-radius: 3px;
            overflow: hidden;
        }
        .progress-bar .fill {
            height: 100%;
            background: #2563eb;
            border-radius: 3px;
            transition: width 0.3s;
        }

        /* 表单 */
        input[type="text"], textarea, select {
            background: #111;
            border: 1px solid #333;
            color: #e0e0e0;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            width: 100%;
        }
        textarea { min-height: 200px; resize: vertical; }
        label { display: block; margin-bottom: 4px; font-size: 13px; color: #999; }
        .form-group { margin-bottom: 16px; }
        .form-row { display: flex; gap: 16px; }
        .form-row .form-group { flex: 1; }

        /* 网格 */
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }

        /* 消息 */
        .alert {
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 14px;
        }
        .alert-success { background: #1a3a1a; color: #6c6; border: 1px solid #2a5a2a; }
        .alert-error { background: #3a1a1a; color: #c66; border: 1px solid #5a2a2a; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>文章转视频</h1>
            <nav>
                <a href="/">项目列表</a>
                <a href="/ui/projects/new">新建项目</a>
            </nav>
        </div>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

### 新增文件：project_manager/templates/projects.html

```html
{% extends "base.html" %}
{% block title %}项目列表{% endblock %}
{% block content %}
<div class="card">
    <h2>项目列表</h2>
    {% if projects %}
    <table>
        <thead>
            <tr>
                <th>项目名称</th>
                <th>拆分模式</th>
                <th>段落数</th>
                <th>进度</th>
                <th>创建时间</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            {% for p in projects %}
            <tr>
                <td><a href="/ui/projects/{{ p.id }}">{{ p.name }}</a></td>
                <td>{{ p.split_mode }}</td>
                <td>{{ p.segment_count }}</td>
                <td>
                    <div class="progress-bar">
                        <div class="fill" style="width: {{ p.progress }}%"></div>
                    </div>
                    <small>{{ p.completed_count }}/{{ p.segment_count }}</small>
                </td>
                <td>{{ p.created_at[:16] }}</td>
                <td>
                    <a href="/ui/projects/{{ p.id }}" class="btn btn-sm btn-primary">查看</a>
                    <form method="post" action="/ui/projects/{{ p.id }}/delete" style="display:inline"
                          onsubmit="return confirm('确定删除？')">
                        <button type="submit" class="btn btn-sm btn-danger">删除</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="color:#666">暂无项目。<a href="/ui/projects/new">创建第一个项目</a></p>
    {% endif %}
</div>
{% endblock %}
```

### 新增文件：project_manager/templates/project_new.html

```html
{% extends "base.html" %}
{% block title %}新建项目{% endblock %}
{% block content %}
<div class="card">
    <h2>新建项目</h2>
    <form method="post" action="/ui/projects/new">
        <div class="form-group">
            <label>项目名称</label>
            <input type="text" name="name" placeholder="我的第一个项目" required>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>拆分模式</label>
                <select name="split_mode">
                    <option value="auto">自动拆分</option>
                    <option value="manual">手动拆分（用 ===SPLIT=== 标记）</option>
                </select>
            </div>
            <div class="form-group">
                <label>画风偏好（可选）</label>
                <input type="text" name="style_hint" placeholder="anime style, cinematic">
            </div>
        </div>
        <div class="form-group">
            <label>粘贴文本</label>
            <textarea name="source_text" placeholder="在这里粘贴你的文章..."></textarea>
        </div>
        <button type="submit" class="btn btn-primary">创建项目</button>
        <a href="/" class="btn" style="background:#333">取消</a>
    </form>
</div>
{% endblock %}
```

### 新增文件：project_manager/templates/project_detail.html

```html
{% extends "base.html" %}
{% block title %}{{ project.name }}{% endblock %}
{% block content %}
<div class="card">
    <h2>{{ project.name }}</h2>
    <div class="form-row" style="margin-bottom:12px">
        <div><small style="color:#666">ID：</small>{{ project.id }}</div>
        <div><small style="color:#666">模式：</small>{{ project.split_mode }}</div>
        <div><small style="color:#666">创建：</small>{{ project.created_at[:16] }}</div>
    </div>
    {% if project.style_hint %}
    <div style="margin-bottom:12px"><small style="color:#666">画风：</small>{{ project.style_hint }}</div>
    {% endif %}
</div>

{% for seg in segments %}
<div class="card">
    <h2>
        段落 {{ seg.segment_index }}：{{ seg.title }}
        <span class="badge badge-{{ seg.status }}">{{ seg.status }}</span>
    </h2>
    <p style="color:#999; font-size:13px; margin-bottom:12px">{{ seg.summary }}</p>
    <details style="margin-bottom:12px">
        <summary style="cursor:pointer; color:#6aa6ff; font-size:13px">展开段落全文</summary>
        <p style="margin-top:8px; font-size:14px; white-space:pre-wrap">{{ seg.content }}</p>
    </details>

    {% if seg.shots %}
    <h3>分镜列表（{{ seg.shots|length }} 个）</h3>
    <table>
        <thead>
            <tr>
                <th style="width:170px">图片</th>
                <th>画面描述</th>
                <th>台词/旁白</th>
                <th>说话人</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            {% for shot in seg.shots %}
            <tr>
                <td>
                    {% if shot.image_path %}
                    <img src="{{ shot.image_path }}" class="thumb" onerror="this.style.display='none'">
                    {% else %}
                    <div class="thumb-placeholder">未生成</div>
                    {% endif %}
                </td>
                <td>{{ shot.scene_description[:80] }}{% if shot.scene_description|length > 80 %}...{% endif %}</td>
                <td>{{ shot.dialogue or shot.narrator_text or '-' }}</td>
                <td>{{ shot.speaker or '-' }}</td>
                <td>
                    <form method="post" action="/ui/shots/{{ shot.id }}/regenerate" style="display:inline">
                        <button type="submit" class="btn btn-sm btn-warning">重生成</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p style="color:#666">暂无分镜</p>
    {% endif %}

    <div style="margin-top:12px">
        {% if seg.status == 'pending' %}
        <form method="post" action="/ui/segments/{{ seg.id }}/render" style="display:inline">
            <button type="submit" class="btn btn-success">渲染此段</button>
        </form>
        {% elif seg.status == 'rendered' %}
        <form method="post" action="/ui/segments/{{ seg.id }}/confirm" style="display:inline">
            <button type="submit" class="btn btn-primary">确认并合成</button>
        </form>
        {% elif seg.status == 'completed' %}
        {% if seg.video_path %}
        <a href="{{ seg.video_path }}" class="btn btn-primary" target="_blank">下载视频</a>
        {% endif %}
        <form method="post" action="/ui/segments/{{ seg.id }}/recompose" style="display:inline">
            <button type="submit" class="btn btn-warning">重新合成</button>
        </form>
        {% endif %}
    </div>
</div>
{% endfor %}
{% endblock %}
```

### 新增文件：project_manager/templates/shot_detail.html

```html
{% extends "base.html" %}
{% block title %}分镜详情{% endblock %}
{% block content %}
<div class="card">
    <h2>分镜详情</h2>
    <div class="grid-2">
        <div>
            {% if shot.image_path %}
            <img src="{{ shot.image_path }}" style="width:100%; border-radius:8px; border:1px solid #333"
                 onerror="this.style.display='none'">
            {% else %}
            <div class="thumb-placeholder" style="width:100%; height:300px">未生成图片</div>
            {% endif %}
        </div>
        <div>
            <div class="form-group">
                <label>画面描述</label>
                <p>{{ shot.scene_description }}</p>
            </div>
            <div class="form-group">
                <label>生图提示词</label>
                <p style="font-size:13px; color:#999">{{ shot.prompt }}</p>
            </div>
            <div class="form-group">
                <label>负面提示词</label>
                <p style="font-size:13px; color:#666">{{ shot.negative_prompt }}</p>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>台词</label>
                    <p>{{ shot.dialogue or '-' }}</p>
                </div>
                <div class="form-group">
                    <label>旁白</label>
                    <p>{{ shot.narrator_text or '-' }}</p>
                </div>
            </div>
            <div class="grid-2">
                <div class="form-group">
                    <label>说话人</label>
                    <p>{{ shot.speaker or '-' }}</p>
                </div>
                <div class="form-group">
                    <label>镜头</label>
                    <p>{{ shot.camera or '-' }}</p>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <h2>重新生成图片</h2>
    <form method="post" action="/ui/shots/{{ shot.id }}/regenerate_custom">
        <div class="form-group">
            <label>修改提示词（留空则使用原词）</label>
            <textarea name="new_prompt" style="min-height:80px">{{ shot.prompt }}</textarea>
        </div>
        <div class="form-group">
            <label>修改画面描述（留空则不改）</label>
            <textarea name="new_description" style="min-height:60px">{{ shot.scene_description }}</textarea>
        </div>
        <button type="submit" class="btn btn-warning">重新生成</button>
        <a href="/ui/projects/{{ shot.project_id }}" class="btn" style="background:#333">返回</a>
    </form>
</div>
{% endblock %}
```

### 修改 server.py，新增页面路由

在 `server.py` 文件顶部添加：

```python
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
import urllib.request

templates = Jinja2Templates(directory="templates")
```

然后在文件末尾 `if __name__` 之前，添加以下页面路由：

```python
# ==================== Web 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def ui_index(request: Request):
    """项目列表页面"""
    projects_list = []
    for pid, p in projects_db.items():
        segments = p.get("segments", [])
        completed = sum(1 for s in segments if s.get("status") == "completed")
        projects_list.append({
            "id": pid,
            "name": p.get("name", "未命名"),
            "split_mode": p.get("split_mode", "auto"),
            "segment_count": len(segments),
            "completed_count": completed,
            "progress": round(completed / len(segments) * 100) if segments else 0,
            "created_at": p.get("created_at", ""),
        })
    projects_list.sort(key=lambda x: x["created_at"], reverse=True)
    return templates.TemplateResponse("projects.html", {"request": request, "projects": projects_list})


@app.get("/ui/projects/new", response_class=HTMLResponse)
async def ui_new_project(request: Request):
    """新建项目页面"""
    return templates.TemplateResponse("project_new.html", {"request": request})


@app.post("/ui/projects/new")
async def ui_create_project(
    request: Request,
    name: str = Form(...),
    split_mode: str = Form(...),
    source_text: str = Form(...),
    style_hint: str = Form(""),
):
    """创建项目并跳转"""
    project = create_project(name, source_text, split_mode, style_hint)
    return RedirectResponse(url=f"/ui/projects/{project['id']}", status_code=303)


@app.get("/ui/projects/{project_id}", response_class=HTMLResponse)
async def ui_project_detail(request: Request, project_id: str):
    """项目详情页面"""
    project = projects_db.get(project_id)
    if not project:
        return HTMLResponse("项目不存在", status_code=404)

    segments = []
    for seg in project.get("segments", []):
        segments.append({
            "id": seg["id"],
            "segment_index": seg.get("segment_index", 0),
            "title": seg.get("title", ""),
            "content": seg.get("content", ""),
            "summary": seg.get("summary", ""),
            "status": seg.get("status", "pending"),
            "video_path": seg.get("video_path", ""),
            "shots": seg.get("shots", []),
        })
    segments.sort(key=lambda x: x["segment_index"])

    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "project": project,
        "segments": segments,
    })


@app.post("/ui/projects/{project_id}/delete")
async def ui_delete_project(project_id: str):
    """删除项目"""
    if project_id in projects_db:
        del projects_db[project_id]
        save_projects()
    return RedirectResponse(url="/", status_code=303)


@app.get("/ui/shots/{shot_id}", response_class=HTMLResponse)
async def ui_shot_detail(request: Request, shot_id: str):
    """分镜详情页面"""
    for pid, project in projects_db.items():
        for seg in project.get("segments", []):
            for shot in seg.get("shots", []):
                if shot["id"] == shot_id:
                    shot["project_id"] = pid
                    return templates.TemplateResponse("shot_detail.html", {
                        "request": request,
                        "shot": shot,
                    })
    return HTMLResponse("分镜不存在", status_code=404)


@app.post("/ui/shots/{shot_id}/regenerate")
async def ui_regenerate_shot(shot_id: str):
    """原词重生成（跳转 Dify 工作流或直接调引擎）"""
    # 这里直接调用本地生图引擎
    for pid, project in projects_db.items():
        for seg in project.get("segments", []):
            for shot in seg.get("shots", []):
                if shot["id"] == shot_id:
                    prompt = shot.get("prompt", "")
                    try:
                        req_data = json.dumps({
                            "prompt": prompt,
                            "negative_prompt": shot.get("negative_prompt", ""),
                            "width": 1024, "height": 576, "steps": 30, "seed": -1
                        }).encode()
                        req = urllib.request.Request(
                            "http://localhost:8188/api/prompt",
                            data=req_data,
                            method="POST",
                        )
                        req.add_header("Content-Type", "application/json")
                        with urllib.request.urlopen(req, timeout=120) as resp:
                            result = json.loads(resp.read().decode())
                            shot["image_path"] = result.get("image_url", "")
                            shot["version"] = shot.get("version", 1) + 1
                            save_projects()
                    except Exception as e:
                        pass  # 生图失败，保持原图
                    return RedirectResponse(url=f"/ui/shots/{shot_id}", status_code=303)
    return HTMLResponse("分镜不存在", status_code=404)


@app.post("/ui/shots/{shot_id}/regenerate_custom")
async def ui_regenerate_custom(
    request: Request,
    shot_id: str,
    new_prompt: str = Form(""),
    new_description: str = Form(""),
):
    """修改提示词后重生成"""
    for pid, project in projects_db.items():
        for seg in project.get("segments", []):
            for shot in seg.get("shots", []):
                if shot["id"] == shot_id:
                    prompt = new_prompt or shot.get("prompt", "")
                    if new_description and not new_prompt:
                        prompt = f"{new_description}, detailed, cinematic"
                    shot["prompt"] = prompt
                    try:
                        req_data = json.dumps({
                            "prompt": prompt,
                            "negative_prompt": shot.get("negative_prompt", ""),
                            "width": 1024, "height": 576, "steps": 30, "seed": -1
                        }).encode()
                        req = urllib.request.Request(
                            "http://localhost:8188/api/prompt",
                            data=req_data,
                            method="POST",
                        )
                        req.add_header("Content-Type", "application/json")
                        with urllib.request.urlopen(req, timeout=120) as resp:
                            result = json.loads(resp.read().decode())
                            shot["image_path"] = result.get("image_url", "")
                            shot["version"] = shot.get("version", 1) + 1
                            save_projects()
                    except Exception:
                        pass
                    return RedirectResponse(url=f"/ui/shots/{shot_id}", status_code=303)
    return HTMLResponse("分镜不存在", status_code=404)


@app.post("/ui/segments/{segment_id}/render")
async def ui_render_segment(segment_id: str):
    """渲染段落（调用合成服务）"""
    for pid, project in projects_db.items():
        for seg in project.get("segments", []):
            if seg["id"] == segment_id:
                # 标记为已渲染
                seg["status"] = "rendered"
                save_projects()
                return RedirectResponse(url=f"/ui/projects/{pid}", status_code=303)
    return HTMLResponse("段落不存在", status_code=404)


@app.post("/ui/segments/{segment_id}/confirm")
async def ui_confirm_segment(segment_id: str):
    """确认并合成"""
    for pid, project in projects_db.items():
        for seg in project.get("segments", []):
            if seg["id"] == segment_id:
                # 调用合成服务
                shots = seg.get("shots", [])
                compose_shots = []
                for shot in shots:
                    compose_shots.append({
                        "shot_id": shot["id"],
                        "shot_index": shot.get("shot_index", 0),
                        "image_path": shot.get("image_path", ""),
                        "audio_path": shot.get("audio_path", ""),
                        "audio_duration": shot.get("audio_duration", 5.0),
                        "dialogue": shot.get("dialogue", ""),
                        "narrator_text": shot.get("narrator_text", ""),
                        "speaker": shot.get("speaker", ""),
                    })
                compose_body = {
                    "segment_id": segment_id,
                    "shots": compose_shots,
                    "output_format": "horizontal_16_9",
                    "subtitle": {"enabled": True, "font_size": 24},
                    "transition": {"type": "fade", "duration": 0.5},
                    "title": {"enabled": False},
                }
                try:
                    req_data = json.dumps(compose_body).encode()
                    req = urllib.request.Request(
                        "http://localhost:5004/api/compositor/segment",
                        data=req_data,
                        method="POST",
                    )
                    req.add_header("Content-Type", "application/json")
                    with urllib.request.urlopen(req, timeout=300) as resp:
                        result = json.loads(resp.read().decode())
                        seg["video_path"] = result.get("video_path", "")
                        seg["video_duration"] = result.get("duration", 0)
                        seg["status"] = "completed"
                        save_projects()
                except Exception as e:
                    seg["status"] = "rendered"
                    save_projects()
                return RedirectResponse(url=f"/ui/projects/{pid}", status_code=303)
    return HTMLResponse("段落不存在", status_code=404)


@app.post("/ui/segments/{segment_id}/recompose")
async def ui_recompose_segment(segment_id: str):
    """重新合成"""
    for pid, project in projects_db.items():
        for seg in project.get("segments", []):
            if seg["id"] == segment_id:
                seg["status"] = "rendered"
                seg["pending_recompose"] = True
                save_projects()
                # 直接触发合成
                return await ui_confirm_segment(segment_id)
    return HTMLResponse("段落不存在", status_code=404)
```

### 最终目录结构

```
project_manager/
├── server.py
├── data/
│   └── projects.json
├── storage/
│   └── {project_id}/
└── templates/
    ├── base.html
    ├── projects.html
    ├── project_new.html
    ├── project_detail.html
    └── shot_detail.html
```

### 启动后访问

```
API 文档：http://localhost:5005/docs
Web 界面：http://localhost:5005/
```

---

## 页面功能总览

```
/                        → 项目列表（查看进度、删除项目）
/ui/projects/new         → 新建项目（粘贴文本、选模式）
/ui/projects/{id}        → 项目详情（段落列表、分镜缩略图、渲染/确认按钮）
/ui/shots/{id}           → 分镜详情（查看提示词、修改后重生成）

操作流程：
  1. 访问 / → 点击"新建项目"
  2. 粘贴文本 → 创建
  3. 进入项目详情 → 查看分镜图片
  4. 不满意 → 点"重生成"或进入分镜详情修改提示词
  5. 满意 → 点"确认并合成"
  6. 完成 → 点"下载视频"
```

现在有界面了，不用再对着 API 文档手动填参数。