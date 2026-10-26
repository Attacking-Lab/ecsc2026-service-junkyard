FROM debian:trixie

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends maven openjdk-21-jdk-headless && \
    DEBIAN_FRONTEND=noninteractive apt-get clean

# Only fetch native libraries (opencv, ffmpeg, openblas, ...) for the platform we run on,
# instead of every OS/arch the *-platform artifacts pull in by default.
ENV MAVEN_ARGS="-B -Djavacpp.platform=linux-x86_64"

RUN mkdir -p /src/converter/files
WORKDIR /src/converter
COPY converter/pom.xml /src/converter
# Dependencies end up in their own layer, which is only rebuilt when pom.xml changes.
# Running "compile" without sources fetches only the plugins we need (go-offline would fetch all of them).
RUN mvn dependency:copy-dependencies -DincludeScope=runtime -DoutputDirectory=lib compile

COPY converter/static /src/converter/static
COPY converter/src/ /src/converter/src
RUN mvn -o compile

EXPOSE 9305

ENTRYPOINT ["java","-cp","target/classes:lib/*","com.junkyard.app.App"]
