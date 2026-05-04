"""预存音色管理模块"""

import json
import os
from typing import Optional, List, Dict
from pathlib import Path
from .models import PresetVoice, PresetVoiceCreate, InferCodeParams, RefineTextParams


class VoiceManager:
    """音色管理器"""

    DEFAULT_VOICES = [
        # ==================== 女声 ====================
        {
            "id": "default_female",
            "name": "默认女声",
            "description": "自然流畅的女声，适合大多数场景",
            "seed": 42,
            "infer_params": {"temperature": 0.3, "top_P": 0.7, "top_K": 20},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": True,
        },
        {
            "id": "female_warm_knowledge",
            "name": "温柔知性",
            "description": "温柔知性、清晰自然，适合知识科普、读书类内容",
            "seed": 2024,
            "infer_params": {"temperature": 0.25, "top_P": 0.75, "top_K": 22},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_sweet_natural",
            "name": "清甜自然",
            "description": "清甜自然、年轻活泼，适合生活Vlog、种草内容",
            "seed": 42,
            "infer_params": {"temperature": 0.35, "top_P": 0.7, "top_K": 18},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_mature_girl",
            "name": "成熟御姐",
            "description": "成熟御姐、有磁性，适合故事解说、情感类内容",
            "seed": 114514,
            "infer_params": {"temperature": 0.3, "top_P": 0.75, "top_K": 20},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_sweet_lively",
            "name": "甜美活泼",
            "description": "甜美活泼，适合娱乐、轻松内容",
            "seed": 88888,
            "infer_params": {"temperature": 0.4, "top_P": 0.65, "top_K": 15},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_standard_broadcast",
            "name": "标准播音",
            "description": "标准播音、端庄稳重，适合新闻、正式内容",
            "seed": 123456,
            "infer_params": {"temperature": 0.2, "top_P": 0.8, "top_K": 25},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_soft_gentle",
            "name": "软糯温柔",
            "description": "软糯温柔，适合ASMR、哄睡内容",
            "seed": 54321,
            "infer_params": {"temperature": 0.15, "top_P": 0.7, "top_K": 30},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_cold_literary",
            "name": "清冷文艺",
            "description": "清冷文艺，适合文艺短片旁白",
            "seed": 66666,
            "infer_params": {"temperature": 0.2, "top_P": 0.75, "top_K": 22},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_natural_conversation",
            "name": "自然口语",
            "description": "自然口语、亲切友好，适合对话类、聊天内容",
            "seed": 2048,
            "infer_params": {"temperature": 0.4, "top_P": 0.65, "top_K": 18},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_efficient",
            "name": "干练利落",
            "description": "干练利落，适合职场、效率类内容",
            "seed": 31415,
            "infer_params": {"temperature": 0.25, "top_P": 0.8, "top_K": 20},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        {
            "id": "female_youth_energy",
            "name": "青春活力",
            "description": "青春活力，适合校园、青春内容",
            "seed": 99999,
            "infer_params": {"temperature": 0.45, "top_P": 0.6, "top_K": 15},
            "refine_params": {"prompt": ""},
            "category": "female",
            "is_default": False,
        },
        # ==================== 男声 ====================
        {
            "id": "male_steady_magnetic",
            "name": "沉稳磁性",
            "description": "沉稳磁性，适合纪录片、深度解说",
            "seed": 789012,
            "infer_params": {"temperature": 0.25, "top_P": 0.75, "top_K": 22},
            "refine_params": {"prompt": ""},
            "category": "male",
            "is_default": False,
        },
        {
            "id": "male_young_sunny",
            "name": "年轻阳光",
            "description": "年轻阳光，适合科技评测、游戏内容",
            "seed": 219854,
            "infer_params": {"temperature": 0.4, "top_P": 0.65, "top_K": 18},
            "refine_params": {"prompt": ""},
            "category": "male",
            "is_default": False,
        },
        {
            "id": "male_deep_thick",
            "name": "低沉浑厚",
            "description": "低沉浑厚，适合悬疑故事、恐怖内容",
            "seed": 345678,
            "infer_params": {"temperature": 0.2, "top_P": 0.8, "top_K": 25},
            "refine_params": {"prompt": ""},
            "category": "male",
            "is_default": False,
        },
        {
            "id": "male_gentle_scholar",
            "name": "温和书生",
            "description": "温和书生，适合文化、历史内容",
            "seed": 567890,
            "infer_params": {"temperature": 0.25, "top_P": 0.75, "top_K": 20},
            "refine_params": {"prompt": ""},
            "category": "male",
            "is_default": False,
        },
        {
            "id": "male_standard_broadcast",
            "name": "标准男播音",
            "description": "标准男播音，适合新闻、知识类内容",
            "seed": 13579,
            "infer_params": {"temperature": 0.2, "top_P": 0.8, "top_K": 25},
            "refine_params": {"prompt": ""},
            "category": "male",
            "is_default": False,
        },
        {
            "id": "male_magnetic_uncle",
            "name": "磁性大叔",
            "description": "磁性大叔，适合财经、商业内容",
            "seed": 24680,
            "infer_params": {"temperature": 0.25, "top_P": 0.75, "top_K": 22},
            "refine_params": {"prompt": ""},
            "category": "male",
            "is_default": False,
        },
        {
            "id": "male_hot_blood",
            "name": "热血少年",
            "description": "热血少年，适合体育、热血内容",
            "seed": 77777,
            "infer_params": {"temperature": 0.45, "top_P": 0.6, "top_K": 15},
            "refine_params": {"prompt": ""},
            "category": "male",
            "is_default": False,
        },
    ]

    def __init__(self, storage_path: str = None):
        """初始化音色管理器
        
        Args:
            storage_path: 自定义音色存储路径
        """
        if storage_path is None:
            storage_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "storage", "voices"
            )
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.voices_file = self.storage_path / "preset_voices.json"
        
        self._presets: Dict[str, PresetVoice] = {}
        self._load_presets()

    def _load_presets(self):
        """加载预设音色"""
        # 先加载默认音色
        for voice_data in self.DEFAULT_VOICES:
            voice = self._parse_voice(voice_data)
            self._presets[voice.id] = voice

        # 加载自定义音色
        if self.voices_file.exists():
            try:
                with open(self.voices_file, "r", encoding="utf-8") as f:
                    custom_voices = json.load(f)
                    for voice_data in custom_voices:
                        voice = self._parse_voice(voice_data)
                        self._presets[voice.id] = voice
            except Exception as e:
                print(f"[VoiceManager] 加载自定义音色失败: {e}")

    def _parse_voice(self, data: dict) -> PresetVoice:
        """解析音色数据"""
        infer_params = None
        if data.get("infer_params"):
            infer_params = InferCodeParams(**data["infer_params"])

        refine_params = None
        if data.get("refine_params"):
            refine_params = RefineTextParams(
                prompt=data["refine_params"].get("prompt", "")
            )

        return PresetVoice(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            seed=data["seed"],
            infer_params=infer_params,
            refine_params=refine_params,
            category=data.get("category", "custom"),
            is_default=data.get("is_default", False),
        )

    def _save_custom_voices(self):
        """保存自定义音色到文件"""
        custom_voices = [
            voice.model_dump() for voice in self._presets.values()
            if voice.category == "custom"
        ]
        
        # 转换为 JSON 兼容格式
        for voice in custom_voices:
            if voice["infer_params"]:
                voice["infer_params"] = voice["infer_params"]
            else:
                voice["infer_params"] = None
            if voice["refine_params"]:
                voice["refine_params"] = voice["refine_params"]
            else:
                voice["refine_params"] = None

        with open(self.voices_file, "w", encoding="utf-8") as f:
            json.dump(custom_voices, f, ensure_ascii=False, indent=2)

    def get_preset(self, voice_id: str) -> Optional[PresetVoice]:
        """获取预存音色"""
        return self._presets.get(voice_id)

    def get_default_preset(self) -> Optional[PresetVoice]:
        """获取默认音色"""
        for voice in self._presets.values():
            if voice.is_default:
                return voice
        # 如果没有设置默认，返回第一个
        return next(iter(self._presets.values()), None)

    def list_presets(self, category: str = None) -> List[PresetVoice]:
        """列出所有预存音色"""
        voices = list(self._presets.values())
        if category:
            voices = [v for v in voices if v.category == category]
        return sorted(voices, key=lambda x: (not x.is_default, x.name))

    def list_categories(self) -> List[str]:
        """列出所有音色分类"""
        categories = set(v.category for v in self._presets.values())
        return sorted(categories)

    def create_preset(self, data: PresetVoiceCreate) -> PresetVoice:
        """创建自定义音色"""
        voice_id = f"custom_{data.name.lower().replace(' ', '_')}_{data.seed}"
        
        if voice_id in self._presets:
            raise ValueError(f"音色ID {voice_id} 已存在")

        infer_params = None
        refine_params = None

        if data.infer_params:
            infer_params = data.infer_params

        if data.refine_params:
            refine_params = data.refine_params

        voice = PresetVoice(
            id=voice_id,
            name=data.name,
            description=data.description,
            seed=data.seed,
            infer_params=infer_params,
            refine_params=refine_params,
            category=data.category,
            is_default=False,
        )

        self._presets[voice_id] = voice
        self._save_custom_voices()
        
        return voice

    def update_preset(self, voice_id: str, data: PresetVoiceCreate) -> Optional[PresetVoice]:
        """更新自定义音色"""
        if voice_id not in self._presets:
            return None

        voice = self._presets[voice_id]
        
        voice.name = data.name
        voice.description = data.description
        voice.seed = data.seed
        voice.infer_params = data.infer_params
        voice.refine_params = data.refine_params
        voice.category = data.category

        self._save_custom_voices()
        return voice

    def delete_preset(self, voice_id: str) -> bool:
        """删除自定义音色"""
        if voice_id not in self._presets:
            return False

        voice = self._presets[voice_id]
        if voice.is_default:
            raise ValueError("不能删除默认音色")

        del self._presets[voice_id]
        self._save_custom_voices()
        return True

    def get_all_as_dict(self) -> List[Dict]:
        """获取所有音色（用于API返回）"""
        return [v.model_dump() for v in self.list_presets()]


# 全局实例
_voice_manager: Optional[VoiceManager] = None


def get_voice_manager() -> VoiceManager:
    """获取音色管理器单例"""
    global _voice_manager
    if _voice_manager is None:
        _voice_manager = VoiceManager()
    return _voice_manager
