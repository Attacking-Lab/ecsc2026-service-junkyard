import random
import string
import time
from contextlib import contextmanager


def random_username() -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(random.randint(10, 15)))


def random_password() -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(10, 15)))


def random_filename(ext: str) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(random.randint(6, 20))) + "." + ext


def random_name() -> str:
    return random.choice(string.ascii_uppercase) + \
        "".join(random.choice(string.ascii_lowercase) for _ in range(random.randint(2, 10)))


TIMINGS: list[str] = []


@contextmanager
def timing(what: str = ''):
    start = time.monotonic()
    yield
    end = time.monotonic()
    line = f"[TIME] {end - start:5.3f} sec: {what}"
    print(line)
    TIMINGS.append(line)
