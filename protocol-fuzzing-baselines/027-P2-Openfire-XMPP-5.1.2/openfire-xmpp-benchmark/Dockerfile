FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
ARG DEBIAN_FRONTEND=noninteractive
ARG AFLNET_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d
ARG OPENFIRE_SHA256=0f45006e319fb36bf869ef9ca3a3bef930a1bd683a792883b0b0b4c9a3974680
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates openjdk-21-jre-headless python3 procps build-essential file git graphviz-dev libtool libtool-bin make patch pkg-config zlib1g-dev && rm -rf /var/lib/apt/lists/*
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet.tar.gz
COPY aflnet-xmpp.patch aflnet-dumb-mode-network.patch aflnet-dumb-mode-state-feedback.patch xmpp_aflnet.c parser-test.c /opt/benchmark/
RUN echo "$AFLNET_SHA256  /tmp/aflnet.tar.gz" | sha256sum -c - && mkdir -p "$AFLNET" && tar -xzf /tmp/aflnet.tar.gz -C "$AFLNET" && sed -i 's/\r$//' "$AFLNET/Makefile" "$AFLNET/aflnet.h" "$AFLNET/afl-fuzz.c" "$AFLNET/afl-replay.c" "$AFLNET/aflnet-replay.c" && git -C "$AFLNET" init -q && git -C "$AFLNET" apply --unidiff-zero --check /opt/benchmark/aflnet-xmpp.patch && git -C "$AFLNET" apply --unidiff-zero /opt/benchmark/aflnet-xmpp.patch && git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-network.patch && git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-network.patch && git -C "$AFLNET" apply --check /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && git -C "$AFLNET" apply /opt/benchmark/aflnet-dumb-mode-state-feedback.patch && cp /opt/benchmark/xmpp_aflnet.c "$AFLNET/xmpp_aflnet.c" && cd "$AFLNET" && make clean && make -j1 all && make xmpp_aflnet.o && cc -O2 -I"$AFLNET" /opt/benchmark/parser-test.c xmpp_aflnet.o -o /tmp/xmpp-parser-test && /tmp/xmpp-parser-test && rm -f /tmp/xmpp-parser-test
RUN groupadd --system bench && useradd --system --gid bench --create-home --shell /bin/bash bench
COPY source/openfire_5_1_2.tar.gz /tmp/openfire.tar.gz
RUN echo "$OPENFIRE_SHA256  /tmp/openfire.tar.gz" | sha256sum -c - && mkdir -p /opt/openfire && tar -xzf /tmp/openfire.tar.gz -C /opt/openfire --strip-components=1 && chmod 0755 /opt/openfire/bin/openfire.sh && rm -f /tmp/openfire.tar.gz
COPY configs/openfire-demoboot.xml /opt/openfire/conf/openfire-demoboot.xml
COPY seeds/ /opt/benchmark/seeds/
COPY xmpp.dict /opt/benchmark/xmpp.dict
COPY server.sh server-foreground.sh fuzz.sh protocol_smoke.py replay_queue.py /opt/benchmark/
RUN chmod 0755 /opt/benchmark/server.sh /opt/benchmark/server-foreground.sh /opt/benchmark/fuzz.sh /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py && chown -R bench:bench /opt/openfire /opt/benchmark /opt/aflnet
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 OPENFIRE_HOME=/opt/openfire OPENFIRE_OPTS="-Xms128m -Xmx768m -XX:+UseSerialGC"
WORKDIR /opt/benchmark
USER bench
CMD ["bash", "/opt/benchmark/server-foreground.sh"]
