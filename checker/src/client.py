import json
import logging
from contextlib import contextmanager
from typing import Any

import httpx
from enochecker3 import MumbleException, OfflineException
from httpx import AsyncClient, Response

from usernames import generate_international_name


# TODO logging
# TODO more strict type checks


class NameTakenMumble(MumbleException):
    pass


@contextmanager
def limit_stacktraces():
    try:
        yield
    except (OfflineException, httpx.ConnectError) as e:
        raise OfflineException(str(e)) from None


def assert_to_json(s: str | bytes) -> Any:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        raise MumbleException("Invalid JSON")


def assert_string(s: Any) -> str:
    if type(s) is not str:
        raise MumbleException("Expected string")
    return s


class JunkyardClient:
    def __init__(self, client: AsyncClient, url: str = ""):
        self.url = url
        self.client = client

    def _check(self, response: Response) -> None:
        if response.status_code != 200:
            print(response.text)
            logging.info(response.text)
            raise MumbleException(f"Request to {response.url} failed with status {response.status_code}")

    async def login(self, username: str, password: str) -> None:
        with limit_stacktraces():
            response = await self.client.post(self.url + "/api/login",
                                              json={"username": username, "password": password})
        self._check(response)
        if not response.json()["ok"]:
            raise MumbleException("Login failed")

    async def register(self, username: str, password: str) -> tuple[str, str]:
        for _ in range(3):
            firstname, lastname = generate_international_name()
            try:
                await self.register_with_names(username, password, firstname, lastname)
                return firstname, lastname
            except NameTakenMumble:
                pass
        raise MumbleException("Register failed")

    async def register_with_names(self, username: str, password: str, first_name: str, last_name: str) -> None:
        with limit_stacktraces():
            response = await self.client.post(self.url + "/api/register", json={
                "username": username,
                "password": password,
                "first_name": first_name,
                "last_name": last_name
            })
        self._check(response)
        if not response.json()["ok"]:
            if "already taken" in response.json()["message"]:
                raise NameTakenMumble("Register failed")
            raise MumbleException("Register failed")

    async def me(self) -> dict:
        with limit_stacktraces():
            response = await self.client.get(self.url + "/api/me")
        self._check(response)
        result = response.json()
        if "username" not in result or "files" not in result:
            raise MumbleException("Invalid me response")
        return result

    async def upload(self, filename: str, data: bytes, content_type: str) -> str:
        with limit_stacktraces():
            response = await self.client.post(self.url + "/api/upload", files={"file": (filename, data, content_type)})
        self._check(response)
        if not response.json()["ok"]:
            raise MumbleException("Upload failed")
        return response.json()["filename"]

    async def metadata(self, filename: str, meta: str) -> dict:
        with limit_stacktraces():
            response = await self.client.get(self.url + f"/api/metadata/{filename}/{meta}")
        self._check(response)
        return response.json()

    async def process(self, tool: str, filename: str, meta: str, userdata: dict | None = None) -> bytes:
        with limit_stacktraces():
            response = await self.process_unchecked(tool, filename, meta, userdata)
        self._check(response)
        return response.content

    async def process_unchecked(self, tool: str, filename: str, meta: str, userdata: dict | None = None) -> Response:
        with limit_stacktraces():
            return await self.client.post(
                self.url + "/api/process",
                params={"filename": filename, "meta": meta, "tool": tool},
                json=userdata if userdata is not None else {}
            )

    def clear(self) -> None:
        self.client.cookies.clear()

    async def publish(self, filename: str, meta: str) -> str:
        with limit_stacktraces():
            response = await self.client.post(self.url + f"/api/publish/{filename}/{meta}")
        self._check(response)
        return assert_string(assert_to_json(response.content))
