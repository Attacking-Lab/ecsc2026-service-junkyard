from pathlib import Path

from httpx import HTTPStatusError, RequestError, TimeoutException
from typing import Annotated
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File
from fastapi.params import Depends, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import FileResponse

from config import init_storage, Username, FILE_STORAGE, Password, PathComponent
from tools import ALL_TOOLS
import meta
from users import user_repo


class UserPassword(BaseModel):
    username: Username
    password: Password


class UserRegistration(BaseModel):
    username: Username
    password: Password
    first_name: str
    last_name: str


STATIC_FILES = Path(__file__).absolute().parent / "static"

api = FastAPI(debug=True)


def current_username(req: Request) -> str:
    token = req.cookies.get("token", "")
    username = user_repo.validate_user_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return username


@api.post("/login")
async def login(user_password: UserPassword, response: Response):
    if await user_repo.validate_password(user_password.username, user_password.password):
        token = user_repo.create_user_token(user_password.username)
        response.set_cookie(key="token", value=token)
        return {"ok": True, "message": "Login successful"}
    else:
        return {"ok": False, "message": "Login failed"}


@api.post("/register")
async def register(user: UserRegistration, response: Response):
    if await user_repo.create_user(user.username, user.password, user.first_name, user.last_name):
        token = user_repo.create_user_token(user.username)
        response.set_cookie(key="token", value=token)
        return {"ok": True, "message": "Registration successful"}
    else:
        return {"ok": False, "message": "Username or name already taken"}


@api.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="token")
    return {"ok": True, "message": "Logged out"}


@api.get("/me")
async def me(username: Username = Depends(current_username)):
    details = await user_repo.get_user_details(username)
    if not details:
        raise HTTPException(status_code=403, detail="User not found")
    return {
        "username": details["username"],
        "first_name": details["first_name"],
        "last_name": details["last_name"],
        "files": await user_repo.get_files(username),
    }


@api.post("/upload")
async def upload(file: UploadFile = File(...), username: Username = Depends(current_username)):
    content = await file.read(1024 * 1024)
    if len(await file.read(1)) > 0:
        raise HTTPException(status_code=413, detail="File too large")

    uuid = str(uuid4())
    (FILE_STORAGE / uuid).mkdir(exist_ok=False, parents=True)

    metaname = f"base.meta"

    if file.content_type.startswith("image/"):
        (FILE_STORAGE / uuid / "data.bmp").write_bytes(content)
    elif file.content_type.startswith("text/"):
        (FILE_STORAGE / uuid / "data.txt").write_bytes(content)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    (FILE_STORAGE / uuid / metaname).write_bytes(meta.owner(username))

    await user_repo.add_file(username, uuid)
    return {"ok": True, "filename": uuid}


@api.post("/publish/{filename}/{metadata:path}")
async def publish(filename: PathComponent, metadata: PathComponent, username: Username = Depends(current_username)):
    raw_meta = (FILE_STORAGE / filename / f"{metadata}.meta").read_bytes()
    if not raw_meta.startswith(meta.owner(username)):
        raise HTTPException(status_code=403, detail="Not authorized")
    raw_meta += meta.public()
    new_metadata = str(uuid4())
    (FILE_STORAGE / filename / f"{new_metadata}.meta").write_bytes(raw_meta)
    return new_metadata


@api.post("/process")
async def process(tool: str, filename: PathComponent, userdata: Annotated[dict, Body()], meta: PathComponent = "base",
                  username: Username = Depends(current_username)):
    try:
        result = await ALL_TOOLS[tool].process_file(filename, username, meta, userdata)
        return Response(content=result)
    except HTTPStatusError as e:
        raise HTTPException(status_code=500, detail={
            "status": e.response.status_code,
            "body": e.response.text
        })
    except TimeoutException:
        raise HTTPException(status_code=504, detail="Tool timed out")
    except RequestError:
        raise HTTPException(status_code=502, detail="Tool unreachable")


@api.get("/download/{filename}/{metadata}")
async def download(filename: PathComponent, metadata: PathComponent, username: Username = Depends(current_username)):
    try:
        if (FILE_STORAGE / filename / "data.bmp").exists():
            content = await ALL_TOOLS["Inspector"].process_file(filename, username, metadata, {})
            return Response(content=content, media_type="image/bmp")

        if (FILE_STORAGE / filename / "data.txt").exists():
            content = await ALL_TOOLS["Reader"].process_file(filename, username, metadata, {})
            return Response(content=content, media_type="text/plain")
    except HTTPStatusError as e:
        raise HTTPException(status_code=500, detail={
            "status": e.response.status_code,
            "body": e.response.text
        })
    except TimeoutException:
        raise HTTPException(status_code=504, detail="Tool timed out")
    except RequestError:
        raise HTTPException(status_code=502, detail="Tool unreachable")

    return Response(content="Not found", status_code=404)


@api.get("/metadata/{filename}/{metadata}")
async def get_metadata(filename: PathComponent, metadata: PathComponent,
                       username: Username = Depends(current_username)):
    if (FILE_STORAGE / filename / "data.bmp").exists():
        file_type = "image"
    elif (FILE_STORAGE / filename / "data.txt").exists():
        file_type = "text"
    else:
        return Response(content="Not found", status_code=404)
    try:
        result = {"type": file_type} | meta.parse_meta((FILE_STORAGE / filename / f"{metadata}.meta").read_bytes())
        if "owner" in result:
            details = await user_repo.get_user_details(result["owner"])
            if details:
                result |= details
        return result
    except FileNotFoundError:
        return Response(content="Not found", status_code=404)


app = FastAPI(debug=False)
for url in ["/", "/user", "/junk/{j}", "/junk/{j}/{m}"]:
    app.get(url)(lambda: FileResponse(STATIC_FILES / "index.html"))
app.mount("/api", api)
app.mount("/", StaticFiles(directory=STATIC_FILES, html=True), name="static")

if __name__ == "__main__":
    init_storage()
    uvicorn.run(app, host="127.0.0.1", port=9300)
