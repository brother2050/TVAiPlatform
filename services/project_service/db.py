import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from shared.database import get_db


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 项目 CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_project(name, author, source_text_path, split_mode, style_hint) -> dict:
    db = get_db()
    pid = gen_id("proj")
    ts = now_iso()
    db.execute(
        "INSERT INTO projects (id,name,author,source_text_path,split_mode,style_hint,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (pid, name, author, source_text_path, split_mode, style_hint, "created", ts, ts),
    )
    db.commit()
    return get_project(pid)


def get_project(pid: str) -> Optional[dict]:
    db = get_db()
    return db.fetchone("SELECT * FROM projects WHERE id=?", (pid,))


def list_projects(page=1, page_size=20, status=None) -> Tuple[List[dict], int]:
    db = get_db()
    offset = (page - 1) * page_size
    if status:
        total = db.fetchone("SELECT COUNT(*) as c FROM projects WHERE status=?", (status,))["c"]
        rows = db.fetchall("SELECT * FROM projects WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?", (status, page_size, offset))
    else:
        total = db.fetchone("SELECT COUNT(*) as c FROM projects")["c"]
        rows = db.fetchall("SELECT * FROM projects ORDER BY created_at DESC LIMIT ? OFFSET ?", (page_size, offset))
    return rows, total


def update_project(pid: str, **kwargs) -> Optional[dict]:
    db = get_db()
    kwargs["updated_at"] = now_iso()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [pid]
    db.execute(f"UPDATE projects SET {sets} WHERE id=?", tuple(vals))
    db.commit()
    return get_project(pid)


def delete_project(pid: str):
    db = get_db()
    db.execute("DELETE FROM projects WHERE id=?", (pid,))
    db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 段落 CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_segment(project_id, segment_index, title, content, summary) -> dict:
    db = get_db()
    sid = gen_id("seg")
    ts = now_iso()
    db.execute(
        "INSERT INTO segments (id,project_id,segment_index,title,content,summary,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (sid, project_id, segment_index, title, content, summary, "saved", ts, ts),
    )
    db.commit()
    return get_segment(sid)


def get_segment(sid: str) -> Optional[dict]:
    db = get_db()
    return db.fetchone("SELECT * FROM segments WHERE id=?", (sid,))


def get_segments_by_project(project_id: str) -> List[dict]:
    db = get_db()
    return db.fetchall("SELECT * FROM segments WHERE project_id=? ORDER BY segment_index", (project_id,))


def update_segment(sid: str, **kwargs) -> Optional[dict]:
    db = get_db()
    kwargs["updated_at"] = now_iso()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [sid]
    db.execute(f"UPDATE segments SET {sets} WHERE id=?", tuple(vals))
    db.commit()
    return get_segment(sid)


def delete_segments_by_project(project_id: str):
    db = get_db()
    db.execute("DELETE FROM segments WHERE project_id=?", (project_id,))
    db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 分镜 CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_shot(segment_id, shot_data: dict) -> dict:
    db = get_db()
    shid = gen_id("shot")
    ts = now_iso()
    characters_json = json.dumps(shot_data.get("characters", []), ensure_ascii=False)
    db.execute(
        """INSERT INTO shots (id,segment_id,shot_index,scene_description,prompt,negative_prompt,
           dialogue,narrator_text,speaker,camera,characters_json,duration_hint,status,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            shid, segment_id, shot_data.get("shot_index", 0),
            shot_data.get("scene_description", ""), shot_data.get("prompt", ""),
            shot_data.get("negative_prompt", "blurry, low quality, distorted, deformed"),
            shot_data.get("dialogue", ""), shot_data.get("narrator_text", ""),
            shot_data.get("speaker", ""), shot_data.get("camera", ""),
            characters_json, shot_data.get("duration_hint", 5.0),
            "pending", ts, ts,
        ),
    )
    db.commit()
    return get_shot(shid)


def get_shot(shid: str) -> Optional[dict]:
    db = get_db()
    return db.fetchone("SELECT * FROM shots WHERE id=?", (shid,))


def get_shots_by_segment(segment_id: str, status: Optional[str] = None) -> List[dict]:
    db = get_db()
    if status:
        return db.fetchall(
            "SELECT * FROM shots WHERE segment_id=? AND status=? AND is_current=1 ORDER BY shot_index",
            (segment_id, status),
        )
    return db.fetchall(
        "SELECT * FROM shots WHERE segment_id=? AND is_current=1 ORDER BY shot_index",
        (segment_id,),
    )


def update_shot(shid: str, **kwargs) -> Optional[dict]:
    db = get_db()
    kwargs["updated_at"] = now_iso()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [shid]
    db.execute(f"UPDATE shots SET {sets} WHERE id=?", tuple(vals))
    db.commit()
    return get_shot(shid)


def supersede_shots_by_segment(segment_id: str):
    """将段落下所有当前分镜标记为已废弃"""
    db = get_db()
    ts = now_iso()
    db.execute(
        "UPDATE shots SET is_current=0, status='superseded', updated_at=? WHERE segment_id=? AND is_current=1",
        (ts, segment_id),
    )
    db.commit()


def count_shots_by_status(segment_id: str) -> dict:
    db = get_db()
    rows = db.fetchall(
        "SELECT status, COUNT(*) as c FROM shots WHERE segment_id=? AND is_current=1 GROUP BY status",
        (segment_id,),
    )
    return {r["status"]: r["c"] for r in rows}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 分镜版本
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_shot_version(shot_id, version, image_path, prompt, negative_prompt, source) -> dict:
    db = get_db()
    vid = gen_id("ver")
    ts = now_iso()
    db.execute(
        "INSERT INTO shot_versions (id,shot_id,version,image_path,prompt,negative_prompt,source,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (vid, shot_id, version, image_path, prompt, negative_prompt, source, ts),
    )
    db.commit()
    return db.fetchone("SELECT * FROM shot_versions WHERE id=?", (vid,))


def get_shot_versions(shot_id: str) -> List[dict]:
    db = get_db()
    return db.fetchall("SELECT * FROM shot_versions WHERE shot_id=? ORDER BY version", (shot_id,))


def get_latest_version_number(shot_id: str) -> int:
    db = get_db()
    row = db.fetchone("SELECT MAX(version) as mv FROM shot_versions WHERE shot_id=?", (shot_id,))
    return row["mv"] if row and row["mv"] else 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 待处理项查询
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_pending_image_shots(project_id: str) -> List[dict]:
    db = get_db()
    return db.fetchall(
        """SELECT s.*, seg.project_id FROM shots s
           JOIN segments seg ON s.segment_id = seg.id
           WHERE seg.project_id=? AND s.pending_image_regen=1 AND s.is_current=1""",
        (project_id,),
    )


def get_pending_audio_shots(project_id: str) -> List[dict]:
    db = get_db()
    return db.fetchall(
        """SELECT s.*, seg.project_id FROM shots s
           JOIN segments seg ON s.segment_id = seg.id
           WHERE seg.project_id=? AND s.pending_audio_regen=1 AND s.is_current=1""",
        (project_id,),
    )


def get_pending_recompose_segments(project_id: str) -> List[dict]:
    db = get_db()
    return db.fetchall(
        "SELECT * FROM segments WHERE project_id=? AND pending_recompose=1",
        (project_id,),
    )


def clear_pending_image(shid: str):
    update_shot(shid, pending_image_regen=0)


def clear_pending_audio(shid: str):
    update_shot(shid, pending_audio_regen=0)