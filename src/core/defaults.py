# coding: utf-8
import re
import shutil
from pathlib import Path

from lxml.etree import Element, SubElement, ElementTree

from src.core.init import PriorityQueue
from src.plugin.comm import Registry
from src.utils.logger import setup_logger

logger = setup_logger()

__all__ = [
    "get_metadata",
    "move",
    "create_folder",
    "check_data",
    "extra_tag",
    "folder_utils",
    "create_nfo",
    "file_utils"
]


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
        try:
            data = Registry.get(website, number, cfg)
            if check_data(data):
                return extra_tag(file, data, cfg.resource)
        except Exception as exc:
            logger.info(exc)


def folder_utils(search_path: Path, data, config) -> Path:
    """
    use metadata replace location_rule, create folder

    Args:
        config ():
        search_path (Path): search folder or file parent folder
        data (Metadata):

    Returns:
        Path: deepest folder path

    """
    # If the number of actors is more than 5, take the first two
    if len(data.actor) >= 5:
        data.actor = data.actor[:2]
    # replace data and create success folder
    target_path = search_path.joinpath(config.success_folder)
    folder_rule = replace_date(data, config.name_rule_folder)
    # split location rule by '/'
    level_names = folder_rule.split("/")
    # first level folder
    folder = mkdir(target_path.joinpath(level_names[0]))
    # continuously create folders
    for level in level_names[1:]:
        middle = folder.joinpath(level)
        folder = mkdir(middle)
    return folder


def file_utils(created_folder: Path, file: Path, data, config):
    """
    replace data, check length of name
    rename and move video

    Args:
        config:
        file (Path): original file path
        created_folder (Path): created folder
        data (Metadata):

    Returns:
        Path: new file path

    """
    naming_rule = check_length(config.name_rule_file, config.name_max_len)
    filename = replace_date(data, naming_rule)

    filename += ''.join(['-' + i for i in data.extra.values()]) + file.suffix
    return move(file, created_folder.joinpath(filename))


def create_nfo(file_path: Path, data):
    """
    Args:
        file_path: file path that have been moved and renamed
        data:
    """
    nfo_root = Element("movie")
    filename = file_path.parent.joinpath(file_path.with_suffix(".nfo"))
    nfo_fields = {
        "title": data.title,
        "studio": data.studio,
        "director": data.director,
        "actor": data.actor,
        "publisher": data.publisher,
        "runtime": data.runtime,
        "year": data.year,
        "tags": data.tags,
        "cover": data.cover,
    }
    # if extra metadata add into tags
    if data.extra.sub:
        nfo_fields["tags"].append("中文字幕")
    if data.extra.leaked:
        nfo_fields["tags"].append("流出")

    for field_name, values in nfo_fields.items():
        if not values:
            continue
        if not isinstance(values, list):
            values = [values]
        for value in values:
            SubElement(nfo_root, field_name).text = f"{value}"

    # lxml do not support Pathlib obj
    ElementTree(nfo_root).write(
        str(filename), encoding="utf-8", xml_declaration=True, pretty_print=True
    )


def move(src: Path, dest: Path):
    """
    move file
    capture all errors, prevent interruption

    Args:
        src (Path): source path
        dest (Path): dest path

    """
    assert src.exists()
    try:
        shutil.move(src, dest)
        return dest
    except Exception as exc:
        logger.warning(f"fail to move file: {str(exc)}")


def mkdir(dest: Path):
    """
    create folder, and return have created folder path
    capture all errors, prevent interruption

    Args:
        dest (Path): path need to create

    Returns:
        path: record path has created

    """
    if dest.exists():
        return dest
    try:
        dest.mkdir(exist_ok=True)
        return dest
    except Exception as exc:
        logger.warning(f"fail to create folder: {str(exc)}")


def create_folder(search_path: Path, folder: str):
    """
    create a folder according to the relative path and absolute path

    Args:
        search_path (Path): usually file's or folder's parents folder
        folder (): as name

    """
    folder = Path(folder).resolve()
    if not folder.is_absolute():
        return mkdir(search_path.parent.joinpath(folder))
    return mkdir(folder)


def replace_date(data, rule: str) -> str:
    """
    replace path or name with the metadata
    Args:
        rule (str): folder naming rule
        data (Metadata):

    Returns:
        str: folder path
    """
    # data name list that needs to be replaced

    # method one: for
    replaced = [i for i in data.keys() if i in rule and isinstance(data[i], str)]
    for s in replaced:
        rule = rule.replace(s, data[s].strip())
    # Remove illegal characters
    return re.sub(r'[?%*:|"<>]', "_", rule)


def check_data(data) -> bool:
    """
    check main metadata
    if not return False

    """
    if not data.title or data.title == "null":
        return False
    if not data.number or data.number == "null":
        return False
    return True


def extra_tag(file: Path, data, config):
    """
    Add information to metadata according to the file suffix

    Args:
        config ():
        file (Path): original file path
        data (Metadata):

    """
    filename = file.name

    if any(k in filename.lower() for k in config.leaked_suffix):
        data.extra.leaked = "Leaked"

    if config.part_suffix in filename.lower():
        searchobj = re.search(
            r"^" + config.part_suffix + r"\d", filename, flags=re.I
        )
        data.extra.part = searchobj.group() if searchobj else ''

    if any(k in filename.lower() for k in config.sub_suffix):
        data.extra.sub = "C"

    return data


def check_length(name: str, max_len: int) -> str:
    """
    check if the length of folder name or file name does exceed the limit
    try manual entry
    (Is there a limit now? It’s too long to look good, right?)
    Args:
        max_len:  length of name in config user defining
        name: name from plugin

    Returns:
        name:

    """
    if len(name) > max_len:
        logger.info(
            f"folder name is too long: {name}\ntry manual entry:\n"
        )
        choice = input("automatic clip name(y), or try manual entry: \n")
        return name[:max_len] if choice.lower() == "y" else check_length(choice, max_len)
    return name
