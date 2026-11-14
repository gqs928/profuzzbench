FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
ARG DEBIAN_FRONTEND=noninteractive
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates openjdk-21-jre-headless python3 procps build-essential file git graphviz-dev libtool libtool-bin make patch pkg-config zlib1g-dev && rm -rf /var/lib/apt/lists/*
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-amqp.patch aflnet-dumb-mode-network.patch aflnet-dumb-mode-state-feedback.patch amqp_aflnet.c parser-test.c /opt/benchmark/
RUN echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && mkdir -p "$AFLNET" && tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && sed -i 's/\r$//' "$AFLNET/Makefile" "$AFLNET/aflnet.h" "$AFLNET/afl-fuzz.c" "$AFLNET/afl-replay.c" "$AFLNET/aflnet-replay.c" && git -C "$AFLNET" init -q && git -C "$AFLNET" apply --unidiff-zero --check /opt/benchmark/aflnet-amqp.patch && git -C "$AFLNET" apply --unidiff-zero /opt/benchmark/aflnet-amqp.patch && git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-network.patch && git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-network.patch && git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && cp /opt/benchmark/amqp_aflnet.c "$AFLNET/amqp_aflnet.c" && cd "$AFLNET" && make clean && make -j1 all && make amqp_aflnet.o && cc -O2 -I"$AFLNET" /opt/benchmark/parser-test.c amqp_aflnet.o -o /tmp/amqp-parser-test && /tmp/amqp-parser-test && rm -f /tmp/amqp-parser-test
COPY source/apache-artemis-2.57.0-bin.tar.gz /tmp/apache-artemis-2.57.0-bin.tar.gz
COPY source/apache-artemis-2.57.0-bin.tar.gz.sha512 /tmp/apache-artemis-2.57.0-bin.tar.gz.sha512
RUN cd /tmp && sha512sum -c apache-artemis-2.57.0-bin.tar.gz.sha512 && tar -xzf /tmp/apache-artemis-2.57.0-bin.tar.gz -C /opt && mv /opt/apache-artemis-2.57.0 /opt/artemis && rm /tmp/apache-artemis-2.57.0-bin.tar.gz /tmp/apache-artemis-2.57.0-bin.tar.gz.sha512 && JAVA_ARGS='-Xms128M -Xmx768M -XX:+UseSerialGC' /opt/artemis/bin/artemis create /opt/artemis-instance --silent --user guest --password guest --role guest --allow-anonymous --disable-persistence --no-autotune --no-web
RUN groupadd --system bench && useradd --system --gid bench --create-home --shell /bin/bash bench
COPY seeds/ /opt/benchmark/seeds/
COPY amqp.dict generate_seeds.py protocol_smoke.py replay_queue.py server.sh server-foreground.sh fuzz.sh /opt/benchmark/
RUN chmod 0755 /opt/benchmark/generate_seeds.py /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py /opt/benchmark/server.sh /opt/benchmark/server-foreground.sh /opt/benchmark/fuzz.sh && chown -R bench:bench /opt/artemis-instance /opt/benchmark /opt/aflnet
ENV HOME=/tmp/artemis-home ARTEMIS_HOME=/opt/artemis JAVA_ARGS="-Xms128M -Xmx768M -XX:+UseSerialGC"
WORKDIR /opt/artemis-instance
USER bench
CMD ["bash", "/opt/benchmark/server-foreground.sh"]
