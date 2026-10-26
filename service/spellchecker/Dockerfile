FROM golang:1.26 AS build
WORKDIR /src
ADD go.mod /src/go.mod
ADD main.go /src/main.go
ADD meta.go /src/meta.go
ADD LanguageTool.go /src/LanguageTool.go
ADD spellchecker.go /src/spellchecker.go
RUN go build -o /src/spellchecker

FROM debian:trixie
COPY --from=build /src/spellchecker /
USER nobody
CMD ["/spellchecker"]
