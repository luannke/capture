import time

from src.core.defaults import get_metadata, move, create_folder, folder_utils, file_utils, create_nfo
from src.core.init import load_argument
from src.utils.logger import setup_logger

logger = setup_logger()


def main():
    """main entry"""
    start_time = time.perf_counter()

    argument, cfg = load_argument()
    logger.info(f"searching: {argument[2]}")

    filed_folder = cfg.resource.failed_folder
    failed = create_folder(argument[0], filed_folder)

    target = dict(zip(argument[1], argument[2]))
    for file, number in target.items():
        data = get_metadata(file=file, number=number, cfg=cfg)
        print(data)
        if not data:
            move(src=file, dest=failed)
            return
        created_folder = folder_utils(argument[0], data, cfg.resource)

        new_file_path = file_utils(created_folder, file, data, cfg.resource)
        # img_utils(created_folder, data, cfg)
        create_nfo(new_file_path, data)

    end_time = time.perf_counter()
    logger.debug(f"search video in {end_time - start_time} seconds")


if __name__ == "__main__":
    main()
