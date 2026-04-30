import json
import redis
from typing import Optional, Dict, Any


_redis_client: Optional[redis.Redis] = None
_redis_enabled = True


def get_redis() -> Optional[redis.Redis]:
    global _redis_client, _redis_enabled
    if not _redis_enabled:
        return None
    if _redis_client is None:
        from shared.config import get_config
        cfg = get_config()["redis"]
        _redis_enabled = cfg.get("enabled", True)
        if not _redis_enabled:
            return None
        _redis_client = redis.Redis(
            host=cfg["host"],
            port=cfg["port"],
            db=cfg["db"],
            password=cfg.get("password") or None,
            decode_responses=True,
        )
        try:
            _redis_client.ping()
        except redis.ConnectionError:
            _redis_client = None
            _redis_enabled = False
            return None
    return _redis_client


def cache_set(key: str, value: Dict[str, Any], expire: int = 3600):
    r = get_redis()
    if r:
        r.set(key, json.dumps(value, ensure_ascii=False), ex=expire)


def cache_get(key: str) -> Optional[Dict[str, Any]]:
    r = get_redis()
    if r:
        data = r.get(key)
        if data:
            return json.loads(data)  # type: ignore[arg-type]
    return None


def cache_delete(key: str):
    r = get_redis()
    if r:
        r.delete(key)


def queue_push(queue_name: str, data: Dict[str, Any]):
    r = get_redis()
    if r:
        r.xadd(queue_name, {"data": json.dumps(data, ensure_ascii=False)})


def queue_pop(queue_name: str, consumer: str = "default", timeout: int = 1000) -> Optional[Dict[str, Any]]:
    r = get_redis()
    if r:
        try:
            r.xgroup_create(queue_name, consumer, id="0", mkstream=True)
        except redis.ResponseError:
            pass
        result = r.xreadgroup(consumer, "worker", {queue_name: ">"}, count=1, block=timeout)
        if result:
            for stream, messages in result:  # type: ignore[misc]
                for msg_id, fields in messages:  # type: ignore[misc]
                    r.xack(queue_name, consumer, msg_id)
                    return json.loads(fields["data"])  # type: ignore[arg-type]
    return None  # type: ignore[return-value]