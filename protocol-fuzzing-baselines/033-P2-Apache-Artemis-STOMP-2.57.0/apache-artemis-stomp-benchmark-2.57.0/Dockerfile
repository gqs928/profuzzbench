FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
ARG ARTEMIS_SHA512=47d2193b4707bde8c856ee0f7ee623e87722559b8503aaef6ee015496499774a8c9b9492933cc0a52873e95dce73ff825222422996d2a8768a4936b015415e8c
ARG JRE_SHA256=a535a1df9c6284d9618872984e026ae0352d1f7e9e0605425c0e6114f47351dd
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 AFL_NO_X86=1
COPY source/apache-artemis-2.57.0-bin.tar.gz source/apache-artemis-2.57.0-bin.tar.gz.sha512 source/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz source/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz.sha256.txt /opt/benchmark/source/
COPY build/afl-fuzz /opt/aflnet/afl-fuzz
COPY seeds/ /opt/benchmark/seeds/
COPY stomp.dict protocol_smoke.py replay_queue.py server.sh server-foreground.sh fuzz.sh /opt/benchmark/
RUN cd /opt/benchmark/source && sha512sum -c apache-artemis-2.57.0-bin.tar.gz.sha512 && grep -q "$JRE_SHA256" OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz.sha256.txt && echo "$JRE_SHA256  OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz" | sha256sum -c - && mkdir -p /opt/java /opt/artemis && tar -xzf OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz -C /opt/java --strip-components=1 && tar -xzf apache-artemis-2.57.0-bin.tar.gz -C /opt/artemis --strip-components=1
ENV ARTEMIS_HOME=/opt/artemis JAVA_HOME=/opt/java JAVA_ARGS="-Xms128M -Xmx768M -XX:+UseSerialGC" PATH=/opt/java/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN /opt/artemis/bin/artemis create /opt/artemis-instance --silent --user admin --password admin --role admin --require-login --disable-persistence --no-autotune --no-web --no-amqp-acceptor --no-mqtt-acceptor --no-hornetq-acceptor && chmod 0755 /opt/benchmark/server.sh /opt/benchmark/server-foreground.sh /opt/benchmark/fuzz.sh /opt/aflnet/afl-fuzz
WORKDIR /opt/benchmark
CMD ["bash", "-lc", "nohup /opt/benchmark/server-foreground.sh >/tmp/artemis-stomp.log 2>&1 & echo $! >/tmp/artemis-stomp.pid; exec sleep infinity"]
