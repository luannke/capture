from pathlib import Path

from src.core.config import Config
# from src.plugin.comm.registry import Registry
# from src.plugin.comm import *
from src.core.defaults import get_metadata

config = Config()
cfg = config.default_config()

# Registry.check_data("Javbus", "ABP-454", cfg)
# data = Registry.get("Javbus", "n1010", cfg)
# print(data)

data = get_metadata(Path("G:/test/n1010.mp4"), "n1010", cfg)
print(data.title)
print(data.number)
