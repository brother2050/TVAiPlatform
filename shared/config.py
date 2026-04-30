import os
import yaml
from typing import Optional

_config = None


def load_config(config_path: Optional[str] = None) -> dict:
    global _config
    if _config is not None:
        return _config

    if config_path is None:
        config_path = os.environ.get(
            "APP_CONFIG",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yml"),
        )

    if config_path is None:
        raise ValueError("配置文件路径未指定且 APP_CONFIG 环境变量未设置")

    with open(config_path, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)

    return _config


def get_config() -> dict:
    if _config is None:
        return load_config()
    return _config