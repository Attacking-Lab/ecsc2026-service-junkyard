import multiprocessing
import os
import sys
import time
from os import environ

worker_class = "uvicorn.workers.UvicornWorker"
workers = int(environ.get("CHECKER_WORKERS", min(4, multiprocessing.cpu_count())))
bind = f"0.0.0.0:{environ.get('CHECKER_PORT', 8000)}"
timeout = 90
# TCP accept queue per socket (default 2048), capped by net.core.somaxconn in the container
backlog = 4096
# keep idle connections open longer than usual idle timeouts (to avoid reuse races)
keepalive = 75

_PRE_FORK_STARTS: float = 0.0


def pre_fork(server, worker):
    global _PRE_FORK_STARTS
    from text_utils import LANGUAGES
    if _PRE_FORK_STARTS == 0.0:
        _PRE_FORK_STARTS = time.monotonic()
    for lang in LANGUAGES.values():
        # loads the language files (but not the dictionaries which are life in Go land)
        lang.sentences, lang.weights
    print(
        f"[{os.getpid()}] Pre-fork completed {time.monotonic() - _PRE_FORK_STARTS:.2f} seconds after initial start",
        file=sys.stderr
    )


def post_fork(server, worker):
    from text_utils import init
    # only maps the precomputed index (< 1 ms), fails the worker boot if the index is missing/incomplete
    init()
    print(
        f"[{os.getpid()}] Post-fork completed {time.monotonic() - _PRE_FORK_STARTS:.2f} seconds after initial start",
        file=sys.stderr
    )
