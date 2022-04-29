# Global imports
import logging


def set_logger(log_file: str, log_level: int) -> None:

    root_log = logging.getLogger()
    root_log.setLevel(log_level)

    if log_file:
        file_handler = logging.FileHandler(
            filename=log_file, mode="w", encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="[{asctime}][{levelname}][{funcName}] {message}", style="{"
            )
        )
        root_log.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(
        logging.Formatter(fmt="[{levelname}] {message}", style="{")
    )
    root_log.addHandler(stream_handler)
