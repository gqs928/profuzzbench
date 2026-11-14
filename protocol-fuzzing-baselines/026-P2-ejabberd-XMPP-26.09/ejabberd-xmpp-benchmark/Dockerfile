FROM ubuntu:20.04@sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214 AS aflnet-builder

ARG DEBIAN_FRONTEND=noninteractive
ARG UBUNTU_SNAPSHOT=20260928T000000Z
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 && \
    apt-get install -y -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 --no-install-recommends ca-certificates && \
    sed -i -E "s#https?://(archive|security)\.ubuntu\.com/ubuntu/?#https://snapshot.ubuntu.com/ubuntu/$UBUNTU_SNAPSHOT/#g" /etc/apt/sources.list && \
    apt-get update -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 && \
    apt-get install -y -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 --no-install-recommends \
      autoconf automake build-essential file git graphviz-dev \
      libtool libtool-bin make patch pkg-config python3 python3-minimal \
      time zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-xmpp.patch aflnet-dumb-mode-network.patch \
     aflnet-dumb-mode-state-feedback.patch \
     xmpp_aflnet.c parser-test.c /opt/benchmark/

RUN echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && \
    mkdir -p "$AFLNET" && \
    tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && \
    sed -i 's/\r$//' "$AFLNET/Makefile" "$AFLNET/aflnet.h" \
      "$AFLNET/afl-fuzz.c" "$AFLNET/afl-replay.c" "$AFLNET/aflnet-replay.c" && \
    git -C "$AFLNET" init -q && \
    git -C "$AFLNET" apply --unidiff-zero --check /opt/benchmark/aflnet-xmpp.patch && \
    git -C "$AFLNET" apply --unidiff-zero /opt/benchmark/aflnet-xmpp.patch && \
    git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-network.patch && \
    git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-network.patch && \
    git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && \
    git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && \
    cp /opt/benchmark/xmpp_aflnet.c "$AFLNET/xmpp_aflnet.c" && \
    cd "$AFLNET" && make clean && make -j2 all && make xmpp_aflnet.o && \
    cc -O2 -I"$AFLNET" /opt/benchmark/parser-test.c xmpp_aflnet.o -o /tmp/xmpp-parser-test && \
    /tmp/xmpp-parser-test && \
    rm -f /tmp/xmpp-parser-test

FROM erlang:29.0.6-slim@sha256:04f8492a880e591288974ba5d5572e2a833fa3f9c62deceed207f2336d8d072b

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBIAN_SNAPSHOT=20260901T000000Z
ARG EJABBERD_VERSION=26.09
ARG EJABBERD_SHA256=2853a0ccafc0343ba47a3a848267fd9971c521d594a29c4caa8114bc511f10ab

ENV DEBIAN_FRONTEND=noninteractive \
    AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    AFL_SKIP_BIN_CHECK=1 \
    AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
    ERL_CRASH_DUMP=/tmp/erl_crash.dump

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY --from=aflnet-builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt

RUN if [[ -f /etc/apt/sources.list.d/debian.sources ]]; then \
      sed -i -E "s#https?://deb\.debian\.org/debian-security/?#http://snapshot.debian.org/archive/debian-security/$DEBIAN_SNAPSHOT/#g; s#https?://deb\.debian\.org/debian/?#http://snapshot.debian.org/archive/debian/$DEBIAN_SNAPSHOT/#g" \
        /etc/apt/sources.list.d/debian.sources; \
      echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99snapshot; \
    fi; \
    apt-get update -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 && \
    apt-get install -y -o Acquire::Retries=10 -o Acquire::https::Pipeline-Depth=0 -o Acquire::https::Timeout=120 --no-install-recommends \
      autoconf automake build-essential ca-certificates git libexpat1-dev \
      libgvc6 libglib2.0-0t64 libncurses-dev libpam0g-dev libpixman-1-0 \
      libssl-dev libyaml-dev libcgraph6 openssl patch pkg-config \
      python3 time zlib1g-dev graphviz && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 bench && useradd --uid 1000 --gid bench \
      --create-home --shell /bin/bash bench

COPY source/ejabberd-26.09.tar.gz /tmp/ejabberd.tar.gz
COPY configs/ejabberd.yml /opt/benchmark/configs/ejabberd.yml
COPY seeds/ /opt/benchmark/seeds/
COPY xmpp.dict /opt/benchmark/xmpp.dict
COPY --from=aflnet-builder /opt/aflnet/afl-fuzz /opt/aflnet/afl-fuzz
COPY --from=aflnet-builder /opt/aflnet/afl-showmap /opt/aflnet/afl-showmap
COPY --from=aflnet-builder /opt/aflnet/afl-replay /opt/aflnet/afl-replay
COPY --from=aflnet-builder /opt/aflnet/aflnet-replay /opt/aflnet/aflnet-replay
COPY --from=aflnet-builder /opt/benchmark/aflnet-dumb-mode-network.patch /opt/benchmark/
COPY --from=aflnet-builder /opt/benchmark/aflnet-dumb-mode-state-feedback.patch /opt/benchmark/

RUN echo "$EJABBERD_SHA256  /tmp/ejabberd.tar.gz" | sha256sum -c - && \
    mkdir -p /tmp/ejabberd-source /opt/benchmark/tls /opt/ejabberd-reference \
      /opt/ejabberd-afl /opt/ejabberd-cover && \
    tar -xzf /tmp/ejabberd.tar.gz -C /tmp/ejabberd-source --strip-components=1 && \
    cd /tmp/ejabberd-source && \
    ./autogen.sh && \
    ./configure --with-rebar="$(pwd)/rebar3" && \
    if ! make prod > /tmp/ejabberd-build.log 2>&1; then tail -n 100 /tmp/ejabberd-build.log; exit 1; fi && \
    test -x _build/prod/rel/ejabberd/bin/ejabberdctl && \
    cp -a _build/prod/rel/ejabberd/. /opt/ejabberd-reference/ && \
    cp -a /opt/ejabberd-reference/. /opt/ejabberd-afl/ && \
    cp -a /opt/ejabberd-reference/. /opt/ejabberd-cover/ && \
    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 -subj "/CN=localhost" \
      -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
      -keyout /tmp/ejabberd.key -out /tmp/ejabberd.cert >/dev/null 2>&1 && \
    cat /tmp/ejabberd.cert /tmp/ejabberd.key > /opt/benchmark/tls/server.pem && \
    chmod 0644 /opt/benchmark/tls/server.pem && \
    { \
      echo "ejabberd_version=$EJABBERD_VERSION"; \
      echo "ejabberd_source_archive_sha256=$EJABBERD_SHA256"; \
      echo "erlang_image=erlang:29.0.6-slim@sha256:04f8492a880e591288974ba5d5572e2a833fa3f9c62deceed207f2336d8d072b"; \
      echo "otp_system_version=$(erl -noshell -eval 'io:format("~s", [erlang:system_info(system_version)]), halt().' )"; \
      echo "aflnet_commit=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732"; \
      echo "aflnet_archive_sha256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d"; \
      echo "aflnet_dumb_mode_network_patch_sha256=$(sha256sum /opt/benchmark/aflnet-dumb-mode-network.patch | cut -d ' ' -f1)"; \
      echo "aflnet_dumb_mode_state_feedback_patch_sha256=$(sha256sum /opt/benchmark/aflnet-dumb-mode-state-feedback.patch | cut -d ' ' -f1)"; \
      echo "xmpp_adapter_sha256=d5fa98fdf79ba8c8a4a033266b6bf71cdd9d9eaa5b26dd19bbb1e8a68c2d8c9b"; \
      echo "feedback_backend=AFLNet XMPP response-state feedback; no BEAM source-line coverage"; \
    } > /opt/benchmark/build-versions.txt; \
    chown -R bench:bench /opt/ejabberd-reference /opt/ejabberd-afl \
      /opt/ejabberd-cover /opt/benchmark /home/bench; \
    rm -rf /tmp/ejabberd-source /tmp/ejabberd.tar.gz /tmp/ejabberd.key \
      /tmp/ejabberd.cert /tmp/ejabberd-build.log

WORKDIR /opt/benchmark
COPY run.sh fuzz.sh validate.sh protocol_smoke.py coverage_replay.py /opt/benchmark/
RUN chmod 0755 /opt/benchmark/run.sh /opt/benchmark/validate.sh \
      /opt/benchmark/fuzz.sh /opt/benchmark/protocol_smoke.py \
      /opt/benchmark/coverage_replay.py && \
    chown -R bench:bench /opt/benchmark
USER bench
CMD ["bash", "/opt/benchmark/run.sh", "afl"]
