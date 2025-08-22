import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("booth")
    if logger.handlers:
        return logger
    logger.setLevel(level)

    handler = logging.StreamHandler(stream=sys.stdout)
    fmt = logging.Formatter(
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
