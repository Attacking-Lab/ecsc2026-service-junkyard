FROM debian:trixie

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc make cmake libevent-dev uuid-dev && \
    DEBIAN_FRONTEND=noninteractive apt-get clean

WORKDIR /src
COPY CMakeLists.txt /src/CMakeLists.txt
COPY *.c /src/
COPY *.h /src/

RUN ls -lah && cmake -DCMAKE_BUILD_TYPE=MinSizeRel . && \
    make -j2 && \
    make install && \
    make clean

EXPOSE 9302

ENTRYPOINT ["annotator"]
