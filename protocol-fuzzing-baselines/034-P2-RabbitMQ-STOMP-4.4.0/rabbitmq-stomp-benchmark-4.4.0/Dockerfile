FROM erlang:29.0.6-slim@sha256:04f8492a880e591288974ba5d5572e2a833fa3f9c62deceed207f2336d8d072b
ARG RABBITMQ_SHA256=68c22d5dafa15c0911463aeca73c362d638cd6fb8e407ad39512959c6cc37f0f
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 AFL_NO_X86=1
COPY source/rabbitmq-server-generic-unix-4.4.0.tar.xz /opt/benchmark/source/rabbitmq-server-generic-unix-4.4.0.tar.xz
COPY build/rabbitmq_server-4.4.0/ /opt/rabbitmq/rabbitmq_server-4.4.0/
COPY build/afl-fuzz /opt/aflnet/afl-fuzz
COPY configs/rabbitmq.conf /opt/benchmark/configs/rabbitmq.conf
COPY seeds/ /opt/benchmark/seeds/
COPY stomp.dict protocol_smoke.py replay_queue.py server.sh server-foreground.sh container-start.sh fuzz.sh /opt/benchmark/
RUN echo "$RABBITMQ_SHA256  /opt/benchmark/source/rabbitmq-server-generic-unix-4.4.0.tar.xz" | sha256sum -c - && useradd --uid 1000 --create-home --shell /bin/bash rabbitmq && mkdir -p /tmp/rabbit-home /tmp/rabbitmq && touch /tmp/rabbitmq/enabled_plugins && chown -R rabbitmq:rabbitmq /tmp/rabbit-home /tmp/rabbitmq /opt/rabbitmq /opt/benchmark /opt/aflnet
ENV HOME=/tmp/rabbit-home RABBITMQ_HOME=/opt/rabbitmq/rabbitmq_server-4.4.0 RABBITMQ_CONFIG_FILE=/opt/benchmark/configs/rabbitmq RABBITMQ_ENABLED_PLUGINS_FILE=/tmp/rabbitmq/enabled_plugins RABBITMQ_MNESIA_BASE=/tmp/rabbitmq/mnesia RABBITMQ_LOG_BASE=/tmp/rabbitmq/log RABBITMQ_PID_FILE=/tmp/rabbitmq/rabbitmq.pid RABBITMQ_NODENAME=rabbit@localhost ERL_EPMD_ADDRESS=127.0.0.1 PATH=/opt/rabbitmq/rabbitmq_server-4.4.0/sbin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
USER rabbitmq
RUN rabbitmq-plugins enable --offline rabbitmq_stomp && chmod 0755 /opt/benchmark/server.sh /opt/benchmark/server-foreground.sh /opt/benchmark/container-start.sh /opt/benchmark/fuzz.sh /opt/benchmark/protocol_smoke.py /opt/benchmark/replay_queue.py /opt/aflnet/afl-fuzz
WORKDIR /opt/benchmark
CMD ["bash", "/opt/benchmark/container-start.sh"]
