FROM erlang:29.0.6-slim@sha256:04f8492a880e591288974ba5d5572e2a833fa3f9c62deceed207f2336d8d072b
ARG DEBIAN_FRONTEND=noninteractive
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG RABBITMQ_SHA256=68c22d5dafa15c0911463aeca73c362d638cd6fb8e407ad39512959c6cc37f0f
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 AFL_NO_X86=1
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates gnupg gpgv python3 procps xz-utils build-essential file git graphviz-dev libtool libtool-bin make patch pkg-config zlib1g-dev && rm -rf /var/lib/apt/lists/*
COPY source/rabbitmq-release-signing-key.asc source/rabbitmq-server-generic-unix-4.4.0.tar.xz.asc /opt/benchmark/source/
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-amqp.patch aflnet-dumb-mode-network.patch aflnet-dumb-mode-state-feedback.patch amqp_aflnet.c parser-test.c /opt/benchmark/
RUN echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && mkdir -p "$AFLNET" && tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && sed -i 's/\r$//' "$AFLNET/Makefile" "$AFLNET/aflnet.h" "$AFLNET/afl-fuzz.c" "$AFLNET/afl-replay.c" "$AFLNET/aflnet-replay.c" && git -C "$AFLNET" init -q && git -C "$AFLNET" apply --unidiff-zero --check /opt/benchmark/aflnet-amqp.patch && git -C "$AFLNET" apply --unidiff-zero /opt/benchmark/aflnet-amqp.patch && git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-network.patch && git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-network.patch && git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && cp /opt/benchmark/amqp_aflnet.c "$AFLNET/amqp_aflnet.c" && cd "$AFLNET" && make clean && make -j1 all && make amqp_aflnet.o && cc -O2 -I"$AFLNET" /opt/benchmark/parser-test.c amqp_aflnet.o -o /tmp/amqp-parser-test && /tmp/amqp-parser-test && rm -f /tmp/amqp-parser-test
COPY source/rabbitmq-server-generic-unix-4.4.0.tar.xz /tmp/rabbitmq.tar.xz
COPY source/rabbitmq-server-generic-unix-4.4.0.tar.xz.asc /tmp/rabbitmq.tar.xz.asc
RUN echo "$RABBITMQ_SHA256  /tmp/rabbitmq.tar.xz" | sha256sum -c - && gpg --dearmor -o /tmp/rabbitmq-keyring.gpg /opt/benchmark/source/rabbitmq-release-signing-key.asc && gpgv --keyring /tmp/rabbitmq-keyring.gpg /tmp/rabbitmq.tar.xz.asc /tmp/rabbitmq.tar.xz && mkdir -p /opt/rabbitmq && tar -xJf /tmp/rabbitmq.tar.xz -C /opt/rabbitmq && rm /tmp/rabbitmq.tar.xz /tmp/rabbitmq.tar.xz.asc /tmp/rabbitmq-keyring.gpg
RUN groupadd --system bench && useradd --system --gid bench --create-home --shell /bin/bash bench
COPY seeds/ /opt/benchmark/seeds/
COPY configs/rabbitmq.conf /opt/benchmark/configs/rabbitmq.conf
COPY amqp.dict generate_seeds.py protocol_smoke.py replay_queue.py server.sh fuzz.sh server-foreground.sh /opt/benchmark/
RUN chmod 0755 /opt/benchmark/generate_seeds.py /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py /opt/benchmark/server.sh /opt/benchmark/server-foreground.sh /opt/benchmark/fuzz.sh && chown -R bench:bench /opt/rabbitmq /opt/benchmark /opt/aflnet
ENV HOME=/tmp/rabbit-home RABBITMQ_HOME=/opt/rabbitmq/rabbitmq_server-4.4.0
USER bench
WORKDIR /opt/benchmark
CMD ["bash", "/opt/benchmark/server-foreground.sh"]
