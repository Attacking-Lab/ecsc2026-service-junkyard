cmake_minimum_required(VERSION 3.27)
project(annotator C)

set(CMAKE_C_STANDARD 11)

add_executable(annotator
        http_server.c
        http_routes.c
        http_routes.h
        tools.c
        tools.h
        metadata.h
        utils.h
)
# apt install libevent-dev uuid-dev
target_link_libraries(annotator PRIVATE event uuid)

install(TARGETS annotator)
