# coding=utf-8
import copy
import dataclasses
from dataclasses import field, dataclass
from pathlib import Path

import yaml

__all__ = ["Config"]


@dataclass
class Comm:
    main_mode: int = 1
    failed_move: bool = True
    enable_translate: bool = False
    translate_target: str = "zh-cn"
    priority: list = field(default_factory=list)
    cookie: dict = field(default_factory=dict)

    def __post_init__(self):
        self.priority = ["javbus", "javdb"]


@dataclass
class Resource:
    failed_folder: str = "failed"
    success_folder: str = "output"
    name_rule_folder: str = "actor/title"
    name_rule_file: str = "number-title"
    name_max_len: int = 50
    part_suffix: str = ""

    file_type: list = field(default_factory=list)
    exclude_folders: list = field(default_factory=list)
    sub_suffix: list = field(default_factory=list)
    leaked_suffix: list = field(default_factory=list)

    def __post_init__(self):
        self.file_type = [
            ".mp4",
            ".avi",
            ".rmvb",
            ".wmv",
            ".mov",
            ".mkv",
            ".flv",
            ".ts",
            ".webm",
            ".iso",
        ]
        self.exclude_folders = [
            "failed", "output", "escape"
        ]


@dataclass
class Network:
    enable_proxy: bool = False
    proxy_type: str = "socks5"
    proxy_host: str = ""
    timeout: int = 5
    total: int = 3
    delay: int = 1


@dataclass
class Debug:
    enable: bool = True


@dataclass
class Config:
    comm: Comm = field(default_factory=Comm)
    resource: Resource = field(default_factory=Resource)
    network: Network = field(default_factory=Network)
    debug: Debug = field(default_factory=Debug)

    def default_config(self):
        return copy.deepcopy(self)

    def merge_from_file(self, file=None):
        default = Path(__file__).parent.joinpath("config.yaml")
        if file is None or not file.exists():
            file = default if default.exists() else None
        if file is not None:
            try:
                self.merge(file)
            except KeyError:
                raise KeyError("error config")

    def merge(self, file: Path):
        cfg = self._from_file(file)
        self._main(cfg)

    @staticmethod
    def _from_file(file: Path):
        if file.suffix in {"", ".yaml", ".yml"}:
            with file.open() as f:
                cfg = yaml.safe_load(f.read())
            return cfg

    def _main(self, cfg):
        for key, val in cfg.items():
            if key in self._fields(self):
                self._sub(key, val)

    def _sub(self, key, val):
        sub_attr = getattr(self, key)
        for k, v in val.items():
            if k in self._fields(sub_attr):
                old = getattr(sub_attr, k)
                if type(old) != type(k):
                    raise ValueError
                setattr(sub_attr, old, v)

    @staticmethod
    def _fields(root):
        return [f.name for f in dataclasses.fields(root)]
