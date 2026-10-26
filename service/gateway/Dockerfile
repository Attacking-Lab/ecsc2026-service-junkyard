FROM python:3.13-trixie

WORKDIR /src
COPY requirements.txt /src/requirements.txt
RUN pip install -r requirements.txt

COPY *.py /src/
COPY static /src/static

CMD ["fastapi", "run", "app.py", "--host", "0.0.0.0", "--port", "9300"]
