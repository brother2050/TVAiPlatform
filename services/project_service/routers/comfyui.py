"""
ComfyUI 生图/生视频 API 路由 v2
支持多服务端地址 + 直接传递 JSON 内容
"""

import os
import json
import copy
import ssl
import uuid
import time
import io
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/comfyui", tags=["comfyui"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 配置
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_COMFYUI_URL = "http://127.0.0.1:8188"

# 多服务端配置（可在 config.yml 中扩展）
COMFYUI_SERVERS: Dict[str, str] = {
    "local": DEFAULT_COMFYUI_URL,
    # "server2": "http://192.168.1.100:8188",
    # "gpu-server": "http://gpu-cluster:8188",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 底层 ComfyUI 客户端（内联，无外部依赖）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ComfyUIClient:
    """轻量级 ComfyUI 客户端"""

    MIME_MAP = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp",
        ".mp4": "video/mp4", ".avi": "video/avi", ".mov": "video/quicktime",
        ".mkv": "video/x-matroska", ".webm": "video/webm",
    }

    def __init__(self, base_url: str = DEFAULT_COMFYUI_URL):
        self.base = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())
        self._ssl_ctx = ssl.create_default_context()
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.CERT_NONE

    def _req(self, method, path, data=None, timeout=30):
        url = f"{self.base}{path}"
        headers = {"Content-Type": "application/json"} if data else {}
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=self._ssl_ctx) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(error_body)
                detail = json.dumps(err_json, indent=2, ensure_ascii=False)
            except Exception:
                detail = error_body
            raise HTTPException(status_code=e.code, detail=f"ComfyUI 错误: {detail[:500]}")

    def ping(self) -> bool:
        try:
            self._req("GET", "/system_stats", timeout=5)
            return True
        except Exception:
            return False

    def upload_image(self, filepath: str, subfolder: str = "") -> str:
        """上传图片到 ComfyUI"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")

        ext = path.suffix.lower()
        mime = self.MIME_MAP.get(ext, "application/octet-stream")
        file_bytes = path.read_bytes()

        boundary = uuid.uuid4().hex
        body = io.BytesIO()
        for key, val in [("subfolder", subfolder), ("type", "input"), ("overwrite", "true")]:
            body.write(f"--{boundary}\r\n".encode())
            body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
            body.write(f"{val}\r\n".encode())
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n".encode()
        )
        body.write(file_bytes)
        body.write(f"\r\n--{boundary}--\r\n".encode())

        url = f"{self.base}/upload/image"
        req = urllib.request.Request(url, data=body.getvalue(), method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

        with urllib.request.urlopen(req, timeout=120, context=self._ssl_ctx) as r:
            resp = json.loads(r.read().decode())
        return resp.get("name", path.name)

    def queue_prompt(self, workflow) -> dict:
        payload = {"prompt": workflow, "client_id": self.client_id}
        return self._req("POST", "/prompt", payload)

    def history(self, pid: str) -> dict:
        return self._req("GET", f"/history/{pid}")

    def interrupt(self):
        try:
            self._req("POST", "/interrupt", {})
        except Exception:
            pass

    def wait(self, pid: str, timeout=600, interval=2.0) -> dict:
        """等待任务完成"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                hist = self.history(pid)
            except Exception:
                time.sleep(interval)
                continue
            if pid in hist:
                entry = hist[pid]
                st = entry.get("status", {})
                if st.get("completed") or st.get("status_str") == "success" or entry.get("outputs"):
                    return entry
                if st.get("status_str") == "error":
                    raise HTTPException(status_code=500, detail=f"执行出错: {st.get('messages', [])}")
            time.sleep(interval)
        raise HTTPException(status_code=504, detail=f"超时（{timeout}s）")

    def download(self, filename: str, subfolder: str = "", ftype: str = "output", save_path=None):
        params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": ftype})
        url = f"{self.base}/view?{params}"
        if save_path is None:
            save_path = filename
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=120, context=self._ssl_ctx) as r:
            with open(save_path, "wb") as f:
                f.write(r.read())
        return save_path

    @staticmethod
    def extract_outputs(entry: dict) -> List[dict]:
        files = []
        for nid, out in entry.get("outputs", {}).items():
            for kind, label in [("images", "image"), ("videos", "video")]:
                for item in out.get(kind, []):
                    if isinstance(item, dict) and "filename" in item:
                        files.append({
                            "type": label, "filename": item["filename"],
                            "subfolder": item.get("subfolder", ""),
                            "ftype": item.get("type", "output"), "node": nid,
                        })
        return files


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 工作流解析器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WorkflowParser:
    """工作流参数解析"""

    IMAGE_KEYS = {
        "start_image", "end_image", "image", "image1", "image2", "image3",
        "input_image", "reference_image", "first_frame", "last_frame",
        "start_frame", "end_frame", "init_image", "img", "img1", "img2",
    }

    def __init__(self, workflow: dict):
        self.workflow = workflow
        self._analysis: Optional[dict] = None

    def analyze(self) -> dict:
        if self._analysis is not None:
            return self._analysis

        a = {
            "sampler_nodes": [], "latent_nodes": [], "text_nodes": [],
            "positive_text_nodes": [], "negative_text_nodes": [],
            "unlinked_text_nodes": [], "checkpoint_nodes": [],
            "video_latent_nodes": [], "frame_key_found": {},
        }

        for nid, node in self.workflow.items():
            if not isinstance(node, dict):
                continue
            ct = node.get("class_type", "")
            inp = node.get("inputs", {})
            if not isinstance(inp, dict):
                continue

            if "positive" in inp and "negative" in inp:
                a["sampler_nodes"].append({"id": nid, "inputs": inp, "class_type": ct})
            if "width" in inp and "height" in inp:
                a["latent_nodes"].append({"id": nid, "inputs": inp})
                for fk in ("video_frames", "length", "frames", "num_frames"):
                    if fk in inp:
                        a["video_latent_nodes"].append({"id": nid, "inputs": inp})
                        a["frame_key_found"][nid] = fk
                        break
            if "text" in inp:
                a["text_nodes"].append({"id": nid, "inputs": inp})
            if "ckpt_name" in inp or "unet_name" in inp:
                a["checkpoint_nodes"].append({"id": nid, "inputs": inp})

        pos_ids, neg_ids = set(), set()
        for s in a["sampler_nodes"]:
            for ref_field, id_set in [("positive", pos_ids), ("negative", neg_ids)]:
                t = s["inputs"].get(ref_field)
                if isinstance(t, list) and t:
                    id_set.add(str(t[0]))
                elif isinstance(t, (str, int)):
                    id_set.add(str(t))

        for t in a["text_nodes"]:
            if t["id"] in pos_ids:
                a["positive_text_nodes"].append(t)
            elif t["id"] in neg_ids:
                a["negative_text_nodes"].append(t)
            else:
                a["unlinked_text_nodes"].append(t)

        self._analysis = a
        return a

    def apply_overrides(self, ov: dict) -> dict:
        wf = copy.deepcopy(self.workflow)
        a = self.analyze()

        for key, nlist in [("positive", a["positive_text_nodes"]), ("negative", a["negative_text_nodes"])]:
            targets = nlist
            if not targets and key == "positive" and a["unlinked_text_nodes"]:
                targets = [a["unlinked_text_nodes"][0]]
            elif not targets and key == "negative" and len(a["unlinked_text_nodes"]) > 1:
                targets = [a["unlinked_text_nodes"][1]]
            for n in targets:
                if n["id"] in wf:
                    wf[n["id"]]["inputs"]["text"] = ov[key]

        w, h = ov.get("width"), ov.get("height")
        for n in a["latent_nodes"]:
            nid = n["id"]
            if nid not in wf:
                continue
            if w is not None:
                wf[nid]["inputs"]["width"] = w
            if h is not None:
                wf[nid]["inputs"]["height"] = h

        if "frames" in ov:
            for n in a["video_latent_nodes"]:
                nid = n["id"]
                if nid in wf:
                    fk = a["frame_key_found"].get(nid, "video_frames")
                    wf[nid]["inputs"][fk] = ov["frames"]

        for n in a["sampler_nodes"]:
            nid = n["id"]
            if nid not in wf:
                continue
            inp = wf[nid]["inputs"]
            for ok, sk in [("steps", "steps"), ("cfg", "cfg"), ("seed", "seed")]:
                if ok in ov:
                    inp[sk] = ov[ok]

        if "checkpoint" in ov:
            for n in a["checkpoint_nodes"]:
                nid = n["id"]
                if nid not in wf:
                    continue
                inp = wf[nid]["inputs"]
                if "ckpt_name" in inp:
                    inp["ckpt_name"] = ov["checkpoint"]
                elif "unet_name" in inp:
                    inp["unet_name"] = ov["checkpoint"]

        return wf


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 请求/响应模型
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GenerateRequest(BaseModel):
    """通用生成请求"""
    # 服务端选择
    server: Optional[str] = Field(default="local", description="服务端标识: local, server2 等")

    # 工作流（JSON 内容）
    workflow: Dict[str, Any] = Field(default=..., description="完整工作流 JSON 对象")

    # 参数覆盖
    positive: Optional[str] = Field(default=None, description="正向提示词")
    negative: Optional[str] = Field(default=None, description="负向提示词")
    width: Optional[int] = Field(default=None, description="宽度")
    height: Optional[int] = Field(default=None, description="高度")
    steps: Optional[int] = Field(default=None, description="采样步数")
    cfg: Optional[float] = Field(default=None, description="CFG 值")
    seed: int = Field(default=-1, description="种子，-1 随机")
    checkpoint: Optional[str] = Field(default=None, description="模型文件名")
    frames: Optional[int] = Field(default=None, description="视频帧数")
    batch_size: Optional[int] = Field(default=None, description="批次大小")

    # 输入图片（本地路径，自动上传）
    image: Optional[str] = Field(default=None, description="输入图片路径")
    start_image: Optional[str] = Field(default=None, description="起始图片路径")
    end_image: Optional[str] = Field(default=None, description="结束图片路径")
    init_image: Optional[str] = Field(default=None, description="初始化图片路径")

    # 输出配置
    output_dir: Optional[str] = Field(default=None, description="输出目录")
    timeout: int = Field(default=600, description="超时(秒)")
    wait_interval: float = Field(default=2.0, description="轮询间隔(秒)")
    auto_download: bool = Field(default=True, description="自动下载")


class QuickGenerateRequest(BaseModel):
    """快速生成请求（最小参数）"""
    server: Optional[str] = Field(default="local", description="服务端标识")
    workflow: Dict[str, Any] = Field(default=..., description="工作流 JSON 对象")
    positive: str = Field(default=..., description="正向提示词")
    negative: Optional[str] = Field(default=None, description="负向提示词")
    image: Optional[str] = Field(default=None, description="输入图片路径（可选）")
    output_dir: Optional[str] = Field(default=None, description="输出目录")


class GenerateResponse(BaseModel):
    success: bool
    server: str
    prompt_id: Optional[str] = None
    outputs: List[Dict] = Field(default_factory=list)
    downloaded_files: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class ServerInfo(BaseModel):
    id: str
    url: str
    status: str  # "online" | "offline"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 辅助函数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_server_url(server_id: str = "local") -> str:
    if server_id not in COMFYUI_SERVERS:
        raise HTTPException(
            status_code=400,
            detail=f"未知的服务端: {server_id}，可用: {list(COMFYUI_SERVERS.keys())}"
        )
    return COMFYUI_SERVERS[server_id]


def _build_overrides(req: GenerateRequest) -> Dict[str, Any]:
    """从请求构建 overrides"""
    ov = {}
    for key in ["positive", "negative", "width", "height", "steps", "cfg", "seed",
                "checkpoint", "frames", "batch_size", "image", "start_image",
                "end_image", "init_image"]:
        val = getattr(req, key, None)
        if val is not None:
            ov[key] = val
    return ov


def _upload_input_images(client: ComfyUIClient, workflow: dict, overrides: dict) -> dict:
    """上传输入图片到 ComfyUI"""
    uploaded = {}
    for key in ["image", "start_image", "end_image", "init_image"]:
        if key in overrides and overrides[key]:
            filepath = overrides[key]
            if os.path.exists(filepath):
                try:
                    name = client.upload_image(filepath)
                    uploaded[key] = name
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"上传图片失败 ({key}): {e}")

    if uploaded:
        parser = WorkflowParser(workflow)
        workflow = parser.apply_overrides(uploaded)

    return workflow


def _download_outputs(client: ComfyUIClient, outputs: List[dict], output_dir: str) -> List[str]:
    """下载输出文件"""
    downloaded = []
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    for out in outputs:
        try:
            save_path = os.path.join(output_dir, out["filename"]) if output_dir else None
            path = client.download(out["filename"], out["subfolder"], out["ftype"], save_path)
            downloaded.append(path)
        except Exception as e:
            downloaded.append(f"ERROR: {e}")
    return downloaded


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API 路由
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/servers", response_model=List[ServerInfo])
async def list_servers():
    """列出所有 ComfyUI 服务端"""
    result = []
    for sid, url in COMFYUI_SERVERS.items():
        client = ComfyUIClient(url)
        status = "online" if client.ping() else "offline"
        result.append(ServerInfo(id=sid, url=url, status=status))
    return result


@router.post("/servers/{server_id}/register")
async def register_server(server_id: str, url: str):
    """注册新的 ComfyUI 服务端"""
    if server_id in COMFYUI_SERVERS:
        return {"message": f"服务端 {server_id} 已存在，已更新", "url": url}
    COMFYUI_SERVERS[server_id] = url.rstrip("/")
    return {"message": f"服务端 {server_id} 注册成功", "url": url}


@router.get("/status")
async def check_status(server: str = Query("local", description="服务端标识")):
    """检查指定服务端状态"""
    url = _get_server_url(server)
    client = ComfyUIClient(url)
    ok = client.ping()
    return {
        "server": server,
        "url": url,
        "connected": ok,
        "status": "online" if ok else "offline"
    }


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """通用生成接口"""
    url = _get_server_url(req.server or "local")
    client = ComfyUIClient(url)

    # 解析 workflow（支持 JSON 字符串）
    workflow = req.workflow
    if isinstance(workflow, str):
        try:
            workflow = json.loads(workflow)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON 解析错误: {e}")

    # 构建参数
    overrides = _build_overrides(req)
    parser = WorkflowParser(workflow)
    workflow = parser.apply_overrides(overrides)

    # 上传输入图片
    workflow = _upload_input_images(client, workflow, overrides)

    # 提交任务
    try:
        result = client.queue_prompt(workflow)
        prompt_id = result.get("prompt_id")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交任务失败: {e}")

    # 等待完成
    if not prompt_id:
        raise HTTPException(status_code=500, detail="未获取到 prompt_id")
    try:
        entry = client.wait(prompt_id, timeout=req.timeout, interval=req.wait_interval)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=504, detail=f"等待超时: {e}")

    # 提取输出
    outputs = client.extract_outputs(entry)

    # 下载文件
    downloaded = []
    if req.auto_download and outputs:
        downloaded = _download_outputs(client, outputs, req.output_dir or "")

    return GenerateResponse(
        success=True,
        server=req.server or "local",
        prompt_id=prompt_id,
        outputs=outputs,
        downloaded_files=downloaded,
    )


@router.post("/quick", response_model=GenerateResponse)
async def quick_generate(req: QuickGenerateRequest):
    """快速生成接口"""
    full_req = GenerateRequest(
        server=req.server,
        workflow=req.workflow,
        positive=req.positive,
        negative=req.negative,
        image=req.image,
        output_dir=req.output_dir,
        timeout=600,
    )
    return await generate(full_req)


@router.post("/interrupt")
async def interrupt(server: str = Query("local", description="服务端标识")):
    """中断指定服务端的任务"""
    url = _get_server_url(server)
    client = ComfyUIClient(url)
    client.interrupt()
    return {"success": True, "server": server, "message": "已发送中断信号"}


@router.post("/history/{prompt_id}")
async def get_history(prompt_id: str, server: str = Query("local", description="服务端标识")):
    """查询任务历史"""
    url = _get_server_url(server)
    client = ComfyUIClient(url)
    try:
        return client.history(prompt_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
