import hashlib
import hmac
import time
from base64 import b64encode, b64decode

import redis.asyncio as redis

from config import get_secret, get_redis

USER_VALID_SECONDS = 45 * 60


class UserRepository:
    def __init__(self, redis_client: redis.Redis):
        self.client = redis_client

    @classmethod
    def _hash(cls, password: str) -> bytes:
        return hashlib.sha256(password.encode("utf-8")).hexdigest().encode()

    async def create_user(self, username: str, password: str, first_name: str, last_name: str) -> bool:
        name_expires_in = await self.client.zscore(f"known_names", f'{first_name} {last_name}')
        if name_expires_in is not None and name_expires_in >= time.time():
            return False

        result = await self.client.set(f"user:{username}:hash", self._hash(password), ex=USER_VALID_SECONDS, nx=True)
        if not result:
            await self.client.srem(f"known_names", f'{first_name} {last_name}')
            return False

        await self.client.zadd(f"known_names", {f'{first_name} {last_name}': int(time.time()) + USER_VALID_SECONDS})
        await self._cleanup()

        await self.client.set(f"user:{username}:first_name", first_name, ex=USER_VALID_SECONDS)
        await self.client.set(f"user:{username}:last_name", last_name, ex=USER_VALID_SECONDS)
        return True

    async def _cleanup(self) -> None:
        await self.client.zremrangebyscore(f"known_names", 0, int(time.time()))

    async def validate_password(self, username: str, password: str) -> bool:
        result = await self.client.get(f"user:{username}:hash")
        return result and result == self._hash(password)

    def create_user_token(self, username: str) -> str:
        return b64encode(username.encode("utf-8")).decode() + "|" + \
            hmac.new(key=get_secret("user"), msg=username.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()

    def validate_user_token(self, token: str) -> str | None:
        if "|" not in token:
            return None
        username_b64, sig = token.split("|", 1)
        username = b64decode(username_b64)
        if username and hmac.new(key=get_secret("user"), msg=username, digestmod=hashlib.sha256).hexdigest() == sig:
            return username.decode("utf-8")
        return None

    async def add_file(self, username: str, filename: str):
        await self.client.sadd(f"user:{username}:files", filename)

    async def get_files(self, username: str) -> list[str]:
        return [x.decode("utf-8") for x in await self.client.smembers(f"user:{username}:files")]

    async def get_user_details(self, username: str) -> dict | None:
        first = await self.client.get(f"user:{username}:first_name")
        last = await self.client.get(f"user:{username}:last_name")
        if not first or not last:
            return None
        return {
            "first_name": first.decode("utf-8"),
            "last_name": last.decode("utf-8"),
            "username": username,
        }


user_repo = UserRepository(get_redis())
