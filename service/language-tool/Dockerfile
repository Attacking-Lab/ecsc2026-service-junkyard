FROM debian:trixie AS builder

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y wget gcc libcurl4 make && \
    DEBIAN_FRONTEND=noninteractive apt-get clean

RUN wget -O/tmp/dmd.deb 'https://downloads.dlang.org/releases/2.x/2.113.0/dmd_2.113.0-0_amd64.deb' && \
    dpkg -i /tmp/dmd.deb && \
    rm /tmp/dmd.deb

WORKDIR /app
ADD res /app/res
ADD source /app/source
ADD dub.json /app/dub.json

RUN dub build -b release

ADD Makefile build-language.sh /app/


FROM httpd:trixie
RUN rm -f /usr/local/apache2/cgi-bin/*
COPY --from=builder /app/language-tool /usr/local/apache2/cgi-bin/language-tool
CMD ["sh", "-c", "rm -f /usr/local/apache2/logs/cgisock.1 && exec httpd-foreground -c 'LoadModule cgid_module modules/mod_cgid.so'"]
