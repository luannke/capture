# coding: utf-8


__all__ = ["search_video"]

from src.core.comm import check_data, extra_tag
from src.core.init import PriorityQueue


def search_video(path, cfg):
    """
    search video according to file type and exclude folder
    Returns: file path list

    """
    file_type = cfg.resource.file_type
    excluded = [path.joinpath(e) for e in cfg.resource.exclude_folders]
    files = []
    for file in path.rglob("*"):
        exs = [n for n in excluded if n in file.parents]
        if not exs and file.suffix.lower() in file_type:
            files.append(file)
    return files


def get_metadata(file, number, cfg):
    """
    get metadata from plugin according to number

    have been tested
    """
    # priority init， get sorted plugin
    priority = PriorityQueue.get(number, cfg.comm.priority)
    while not priority.empty():
        # noinspection PyBroadException
        website = priority.pop().capitalize()
        data = Registry.get(website, number, cfg)
        if check_data(data):
            return extra_tag(file, data, cfg.resource)
