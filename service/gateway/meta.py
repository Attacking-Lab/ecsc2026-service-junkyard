def owner(s) -> bytes:
    byte_str = s.encode("utf-8")
    if len(byte_str) > 200:
        raise ValueError("Invalid owner")
    return b"\x01" + bytes([len(byte_str)]) + byte_str


def public() -> bytes:
    return b"\x02"


def parse_meta(meta: bytes) -> dict:
    result: dict = {"mods": []}
    pos = 0
    while pos < len(meta):
        match meta[pos]:
            case 1:
                result["owner"] = meta[pos + 2 : pos + 2 + meta[pos + 1]].decode("utf-8")
                pos += 2 + meta[pos + 1]
            case 2:
                result["mods"].append("published")
                pos += 1
            case 3:
                result["mods"].append("cropped")
                pos += 9
            case 4:
                result["mods"].append("censored")
                pos += 9
            case _:
                raise ValueError("Invalid meta")
    return result
