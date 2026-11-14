FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
ARG DEBIAN_FRONTEND=noninteractive
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates openjdk-21-jre-headless python3 procps build-essential file git graphviz-dev libtool libtool-bin make patch pkg-config zlib1g-dev && rm -rf /var/lib/apt/lists/*
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-amqp.patch aflnet-dumb-mode-network.patch aflnet-dumb-mode-state-feedback.patch amqp_aflnet.c parser-test.c /opt/benchmark/
RUN echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && mkdir -p "$AFLNET" && tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && sed -i 's/\r$//' "$AFLNET/Makefile" "$AFLNET/aflnet.h" "$AFLNET/afl-fuzz.c" "$AFLNET/afl-replay.c" "$AFLNET/aflnet-replay.c" && git -C "$AFLNET" init -q && git -C "$AFLNET" apply --unidiff-zero --check /opt/benchmark/aflnet-amqp.patch && git -C "$AFLNET" apply --unidiff-zero /opt/benchmark/aflnet-amqp.patch && git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-network.patch && git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-network.patch && git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && cp /opt/benchmark/amqp_aflnet.c "$AFLNET/amqp_aflnet.c" && cd "$AFLNET" && make clean && make -j1 all && make amqp_aflnet.o && cc -O2 -I"$AFLNET" /opt/benchmark/parser-test.c amqp_aflnet.o -o /tmp/amqp-parser-test && /tmp/amqp-parser-test && rm -f /tmp/amqp-parser-test
COPY source/apache-qpid-broker-j-10.1.1-bin.tar.gz /tmp/apache-qpid-broker-j-10.1.1-bin.tar.gz
COPY source/apache-qpid-broker-j-10.1.1-bin.tar.gz.sha512 /tmp/apache-qpid-broker-j-10.1.1-bin.tar.gz.sha512
RUN cd /tmp && sha512sum -c apache-qpid-broker-j-10.1.1-bin.tar.gz.sha512 && mkdir -p /opt/qpid && tar -xzf /tmp/apache-qpid-broker-j-10.1.1-bin.tar.gz -C /opt/qpid --strip-components=2 && rm /tmp/apache-qpid-broker-j-10.1.1-bin.tar.gz /tmp/apache-qpid-broker-j-10.1.1-bin.tar.gz.sha512 && sed -i 's/-Xmx512m -XX:MaxDirectMemorySize=1536m/-Xms128m -Xmx512m -XX:MaxDirectMemorySize=256m/' /opt/qpid/bin/qpid-server
RUN groupadd --system bench && useradd --system --gid bench --create-home --shell /bin/bash bench
COPY seeds/ /opt/benchmark/seeds/
COPY config/qpid-initial-config.json /opt/benchmark/qpid-initial-config.json
COPY amqp.dict generate_seeds.py protocol_smoke.py replay_queue.py server.sh server-foreground.sh fuzz.sh /opt/benchmark/
RUN chmod 0755 /opt/benchmark/generate_seeds.py /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py /opt/benchmark/server.sh /opt/benchmark/server-foreground.sh /opt/benchmark/fuzz.sh && chown -R bench:bench /opt/qpid /opt/benchmark /opt/aflnet
ENV HOME=/tmp/qpid-home QPID_HOME=/opt/qpid QPID_WORK=/tmp/qpid-work
WORKDIR /opt/qpid
USER bench
CMD ["bash", "/opt/benchmark/server-foreground.sh"]
