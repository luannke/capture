import re
import shutil
from pathlib import Path


def move(src: Path, dest: Path, flag: str = None):
    """
    move file
    capture all errors, prevent interruption

    Args:
        src (Path): source path
        dest (Path): dest path
        flag (str): folder flag

    """
    assert src.exists()
    try:
        shutil.move(src, dest)
        # console.print(f"move {src.name} to {flag} folder")
        return dest
    except Exception as exc:
        # console.print(f"fail to move file: {str(exc)}")
        ...


def mkdir(dest: Path):
    """
    create folder, and return have created folder path
    capture all errors, prevent interruption

    Args:
        dest (Path): path need to create

    Returns:
        path: record path has created

    """
    try:
        dest.mkdir(exist_ok=True)
        # console.print(f"succeed create folder: {dest.as_posix()}")
        return dest
    except Exception as exc:
        # console.print(f"fail to create folder: {str(exc)}")
        ...


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
    if not data.id or data.id == "null":
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