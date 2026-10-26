# Go spellchecker as shared library for Python (same Debian release as python:3.14 for glibc compatibility)
FROM golang:1.26-trixie AS spellchecker
WORKDIR /build
COPY spellchecker/go.mod spellchecker/*.go ./
RUN --mount=type=cache,target=/root/.cache/go-build \
    go build -buildmode=c-shared -o libspellchecker.so .
# precompute the dictionary index, the workers only mmap it (fast startup, shared memory)
COPY res/languages ./languages
RUN --mount=type=cache,target=/root/.cache/go-build \
    go run . build-index languages dictionaries.idx


FROM python:3.14 AS base

# Copy the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /checker
RUN uv venv --system-site-packages
COPY uv.lock pyproject.toml .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY res ./res
COPY gunicorn.conf.py ./
COPY src ./src
COPY spellchecker/__init__.py ./src/spellchecker/
COPY --from=spellchecker /build/libspellchecker.so /build/dictionaries.idx ./src/spellchecker/
RUN uv sync --frozen --no-dev


FROM base as checked
RUN uv pip install "mypy>=2.3.1"
ENV UV_NO_SYNC=1
WORKDIR /checker
RUN uv run mypy
RUN uv run --no-sync gunicorn --check-config --preload -c gunicorn.conf.py checker_main:app
CMD [ "uv", "run", "--no-sync", "gunicorn", "-c", "gunicorn.conf.py", "checker_main:app" ]


FROM base
ENV UV_NO_SYNC=1
WORKDIR /checker
CMD [ "uv", "run", "--no-sync", "gunicorn", "-c", "gunicorn.conf.py", "checker_main:app" ]
