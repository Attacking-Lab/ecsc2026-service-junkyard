import hashlib

from enochecker3 import GetflagCheckerTaskMessage, PutflagCheckerTaskMessage, ExploitCheckerTaskMessage, \
    PutnoiseCheckerTaskMessage, GetnoiseCheckerTaskMessage

type TaskMessage = PutflagCheckerTaskMessage | GetflagCheckerTaskMessage | ExploitCheckerTaskMessage | PutnoiseCheckerTaskMessage | GetnoiseCheckerTaskMessage

"""
enochecker_test uses ENO{base64} format flags. 
we support only ECSC{base64urlsafe} format flags and nothing else.
this module detects enochecker_test runs (via flag_regex) and patches flags/flag-regex etc on the fly.
"""


def fix_task[T: TaskMessage](task: T) -> T:
    if task.flag is not None:
        task.flag = task.flag.replace("/", "_").replace("+", "-")
        if task.flag.startswith("ENO"):
            task.flag = "ECSC{" + task.flag + "}"
    if task.flag_regex is not None:
        task.flag_regex = task.flag_regex.replace(r"+\/=", "_-")
        if task.flag_regex.startswith("ENO"):
            task.flag_regex = r"ECSC\{" + task.flag_regex + "}"
    return task


def exploit_flag(flag: str, task: ExploitCheckerTaskMessage) -> str:
    if task.flag_regex.startswith("ECSC\\{ENO"):
        if flag.startswith("ECSC{ENO"):
            flag = flag[5:-1]
        task.flag_regex = task.flag_regex[6:-1].replace("_-", r"+\/=")
    flag2 = flag.replace("_", "/").replace("-", "+")
    if hashlib.sha256(flag2.encode()).hexdigest() == task.flag_hash:
        return flag2
    return flag
