FROM julia:1.13.1

ENV JULIA_DEPOT_PATH=/opt/julia-depot
RUN mkdir -p $JULIA_DEPOT_PATH && \
    chown nobody:nogroup $JULIA_DEPOT_PATH

WORKDIR /app
COPY Manifest.toml Project.toml /app/

USER nobody
RUN julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'

ADD src /app/src

RUN julia --project=. -e 'using Inspector'

EXPOSE 9301
STOPSIGNAL SIGINT

CMD ["julia", "--project=.", "-m", "Inspector"]
