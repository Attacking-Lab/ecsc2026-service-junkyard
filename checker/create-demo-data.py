import random
from pathlib import Path

from flag_image_generator import gen_string_image, image_to_bitmap
from flag_text_generator import gen_text_with_flag_checked


# TODO check file permissions align

def create_flagstore_1(target: Path, filename: str) -> None:
    b = target / filename
    b.mkdir(parents=True, exist_ok=True)

    img, _ = gen_string_image("ECSC{TESTFLAG_DEMOFLAG_11111111111111}")
    (b / "data.bmp").write_bytes(image_to_bitmap(img))
    (b / "base.meta").write_bytes(b"\x01\x0bdemo-user-1")
    (b / "00000000-8406-007d-3134-78a92bb63938.meta").write_bytes(
        b"\x01\x0bdemo-user-1\x04\x42\x00\x05\x00\x57\x03\x29\x00"
    )
    (b / "00000000-f2ee-74fc-a61e-d0cd537e8b8a.meta").write_bytes(
        b"\x01\x0bdemo-user-1\x04\x42\x00\x05\x00\x57\x03\x29\x00\x02"
    )


def create_flagstore_2(target: Path, filename: str) -> None:
    random.seed(5)

    b = target / filename
    b.mkdir(parents=True, exist_ok=True)

    _, text = gen_text_with_flag_checked("ECSC{TESTFLAG_DEMOFLAG_22222222222222}")
    (b / "data.txt").write_text(text)
    (b / "base.meta").write_bytes(b"\x01\x0bdemo-user-2")


def create_flagstore_3(target: Path, filename: str) -> None:
    b = target / filename
    b.mkdir(parents=True, exist_ok=True)

    img, _ = gen_string_image("ECSC{TESTFLAG_DEMOFLAG_33333333333333}")
    (b / "data.bmp").write_bytes(image_to_bitmap(img))
    (b / "base.meta").write_bytes(b"\x01\x0bdemo-user-3")


def main() -> None:
    target = Path(__file__).parent.parent / "service" / "_samples"
    target.mkdir(parents=True, exist_ok=True)
    create_flagstore_1(target, "00000000-0001-0001-0001-000100010001")
    create_flagstore_2(target, "00000000-0002-0002-0002-000200020002")
    create_flagstore_3(target, "00000000-0003-0003-0003-000300030003")
    print("[DONE]")


if __name__ == '__main__':
    main()
