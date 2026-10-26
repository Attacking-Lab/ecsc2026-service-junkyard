import os
import base64
from abc import abstractmethod, ABC
from fastapi import HTTPException

import meta
from config import FILE_STORAGE

import httpx

from users import user_repo


class Tool(ABC):
    @abstractmethod
    async def process_file(self, filename: str, username: str, metadata: str, userdata: dict) -> bytes:
        raise NotImplementedError()


class GenericHTTPTool(Tool):
    def __init__(self, url: str) -> None:
        self.url = url
        self.client = httpx.AsyncClient(limits=httpx.Limits(max_connections=None, max_keepalive_connections=10), timeout=10.0)

    async def process_file(self, filename: str, username: str, metadata: str, userdata: dict) -> bytes:
        response = await self.client.post(
            f"{self.url}/process",
            params={"filename": filename, "username": username, "meta": metadata},
            json=userdata
        )
        if response.status_code > 299:
            print("Internal error text: " + response.text)
        response.raise_for_status()
        return response.content


class UrlParamsHTTPTool(Tool):
    def __init__(self, url: str) -> None:
        self.url = url
        self.client = httpx.AsyncClient(limits=httpx.Limits(max_connections=None, max_keepalive_connections=10), timeout=10.0)

    async def process_file(self, filename: str, username: str, metadata: str, userdata: dict) -> bytes:
        params = {"filename": filename, "username": username, "meta": metadata}
        for k, v in userdata.items():
            k = k.lower()
            if k.isalpha() and k not in params:
                params[k] = v
        response = await self.client.post(f"{self.url}/process", params=params)
        response.raise_for_status()
        return response.content


class ConverterTool(Tool):
    def __init__(self, url: str) -> None:
        self.url = url
        self.client = httpx.AsyncClient(limits=httpx.Limits(max_connections=None, max_keepalive_connections=10), timeout=10.0)

    async def process_file(self, filename: str, username: str, metadata: str, userdata: dict) -> bytes:
        if not (FILE_STORAGE / filename / f"{metadata}.meta").read_bytes().startswith(meta.owner(username)):
            raise HTTPException(status_code=403, detail="Invalid owner")
        userdata["owner"] = await user_repo.get_user_details(username) or {}
        f1 = FILE_STORAGE / filename / "data.bmp"
        f2 = FILE_STORAGE / filename / "data.txt"
        if f1.exists() and userdata["action"] == "ITT":
            userdata["data"] = base64.b64encode(f1.read_bytes()).decode("utf-8")
        elif f2.exists() and userdata["action"] == "TTI":
            userdata["data"] = base64.b64encode(f2.read_bytes()).decode("utf-8")
        elif userdata["action"] == "GET":
            userdata["data"] = ""
        print("Posting to converter")
        response = await self.client.post(
            f"{self.url}/process",
            params={'filename': filename, 'username': username, 'meta': metadata},
            json=userdata
        )
        response.raise_for_status()
        return response.content


ALL_TOOLS: dict[str, Tool] = {
    "Inspector": GenericHTTPTool("http://inspector:9301"),
    "Censor": UrlParamsHTTPTool("http://annotator:9302/tool/censor"),
    "Cropper": UrlParamsHTTPTool("http://annotator:9302/tool/cropper"),
    "Spellchecker": GenericHTTPTool("http://spellchecker:9303/spellchecker"),
    "Reader": GenericHTTPTool("http://spellchecker:9303/reader"),
    "Converter": ConverterTool("http://converter:9305"),
} if "USE_DOCKER_NETWORK" in os.environ else {
    "Inspector": GenericHTTPTool("http://localhost:9301"),
    "Censor": UrlParamsHTTPTool("http://localhost:9302/tool/censor"),
    "Cropper": UrlParamsHTTPTool("http://localhost:9302/tool/cropper"),
    "Spellchecker": GenericHTTPTool("http://localhost:9303/spellchecker"),
    "Reader": GenericHTTPTool("http://localhost:9303/reader"),
    "Converter": ConverterTool("http://localhost:9305"),
}
