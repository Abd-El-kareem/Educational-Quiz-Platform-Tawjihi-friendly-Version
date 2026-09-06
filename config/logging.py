"""Non-blocking logging via QueueHandler + QueueListener.

A QueueHandler is attached to the root logger; a background QueueListener
drains records to stderr (INFO+) and an optional rotating file (WARNING+)
when LOG_FILE is configured. Request handling never blocks on log I/O.

Configured in ``core.apps.CoreConfig.ready`` (after settings load); the
returned listener is retained by the caller to keep it alive.
"""

import logging
import logging.handlers
import sys
from queue import Queue

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging(level="INFO", log_file=""):
    queue = Queue(-1)
    queue_handler = logging.handlers.QueueHandler(queue)
    queue_handler.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    targets = []
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    targets.append(console)

    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=1_048_576, backupCount=5
        )
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(formatter)
        targets.append(file_handler)

    listener = logging.handlers.QueueListener(queue, *targets)
    listener.start()

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [queue_handler]
    root.propagate = False
    return listener
