import asyncio
import numpy
import uuid
from typing import Any

from httpx import AsyncClient
from client import JunkyardClient
from utils import random_username, random_password, random_name, random_filename
from flag_image_generator import gen_string_image, image_to_bitmap
import random
import string
from ocr import OcrEngine
from PIL import Image
import io

TEXT_LENGTH=40
NUM_REQUESTS=1

def random_string(length: int) -> str:
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def assert_valid_uuid(s: Any, message: str = "not a UUID") -> None:
    try:
        if not isinstance(s, str):
            raise ValueError()
        if s == "base":
            return
        uuid.UUID(s)
    except ValueError:
        print(f"not a UUID: {s!r}")
        raise Exception(message)


def bmp_to_numpy(bmp: bytes) -> numpy.ndarray:
    try:
        return numpy.array(Image.open(io.BytesIO(bmp)))
    except Exception as e:
        print(f"Cannot parse user provided bmp: {str(e)}")
        raise e

async def setup():
    client = JunkyardClient(AsyncClient(base_url="http://127.0.0.1:9300"))
    # register a client
    username, password, firstname, lastname = random_username(), random_password(), random_name(), random_name()
    print(f"Registering user {username!r} / {password!r}")
    await client.register(username, password, firstname, lastname)
    # # login
    await client.login(username, password)
    print("User logged in")
    # generate a file and upload it
    seed = random.randint(0, 2 ** 32 - 1)
    text = random_string(TEXT_LENGTH)
    flag_image, text_pos = gen_string_image(text, seed=seed)
    # filename is folder name which contains data.bmp
    print("Uploading file...")
    gateway_filename = await client.upload(random_filename("bmp"), image_to_bitmap(flag_image), "image/bmp")
    print("File upload done")
    print(f"Gateway filename: {gateway_filename}")
    assert_valid_uuid(gateway_filename, "filename is no UUID")
    print(f"Uploaded image {gateway_filename!r}")
    user_data = {
        "firstName": firstname,
        "lastName": lastname,
        "userName": username,
    }
    return (client, user_data, gateway_filename, text)

async def bench_itt(client, user_data, gateway_filename, text):
    print(text)
    # # do ocr once
    converter_filename = random_filename("bmp")
    converter_data = {"owner": user_data , "path": converter_filename, "action": "ITT", "data":gateway_filename}
    print(converter_data)
    result = await client.process("Converter", gateway_filename, "base", converter_data)
    stored_flag = result.decode("utf-8")
    print(stored_flag)
    print("Did not timeout")

async def bench_tti(client, user_data, gateway_filename, text):
    fn = random_filename("txt")
    print(fn, text)
    gateway_filename = await client.upload(fn, text, "text/plain")
    assert_valid_uuid(gateway_filename, "filename is no UUID")
    
    converter_filename = random_filename("txt")
    converter_data = {"owner": user_data , "path": converter_filename, "action": "TTI", "data":gateway_filename}
    print(converter_data)
    result = await client.process("Converter", gateway_filename, "base", converter_data)
    print(result)
    decoded_bmp = bmp_to_numpy(result)
    ocr = OcrEngine()
    recovered_data = ocr.match_all(decoded_bmp)
    print(recovered_data,text)
    stored_flag = result.decode("utf-8")
    print(stored_flag)
    print("Did not timeout")

async def main():
    client, user_data, gateway_filename, text = await setup()
    # results = await asyncio.gather(*(bench_itt(client, user_data, gateway_filename, text) for i in range(NUM_REQUESTS)))
    results = await asyncio.gather(*(bench_tti(client, user_data, gateway_filename, text) for i in range(NUM_REQUESTS)))

if __name__ == "__main__":
    asyncio.run(main())
