FROM ubuntu:24.04
ARG JRE_SHA256=a535a1df9c6284d9618872984e026ae0352d1f7e9e0605425c0e6114f47351dd
ENV AFLNET=/opt/aflnet AFL_PATH=/opt/aflnet AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1 AFL_NO_UI=1 AFL_SKIP_BIN_CHECK=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 AFL_NO_X86=1
COPY source/apache-activemq-6.4.0-bin.tar.gz source/apache-activemq-6.4.0-bin.tar.gz.sha512 source/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz source/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz.sha256.txt /opt/benchmark/source/
COPY build/afl-fuzz /opt/aflnet/afl-fuzz
COPY configs/activemq.xml /opt/benchmark/configs/activemq.xml
COPY seeds/ /opt/benchmark/seeds/
COPY stomp.dict server.sh server-foreground.sh fuzz.sh /opt/benchmark/
RUN cd /opt/benchmark/source && sha512sum -c apache-activemq-6.4.0-bin.tar.gz.sha512 && grep -q "$JRE_SHA256" OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz.sha256.txt && echo "$JRE_SHA256  OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz" | sha256sum -c - && mkdir -p /opt/java /opt/activemq /tmp/activemq-data /tmp/activemq-home && tar -xzf OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz -C /opt/java --strip-components=1 && tar -xzf apache-activemq-6.4.0-bin.tar.gz -C /opt/activemq --strip-components=1 && cp /opt/benchmark/configs/activemq.xml /opt/activemq/conf/activemq.xml && chmod 0755 /opt/benchmark/server.sh /opt/benchmark/server-foreground.sh /opt/benchmark/fuzz.sh && chmod 0755 /opt/aflnet/afl-fuzz
ENV ACTIVEMQ_HOME=/opt/activemq ACTIVEMQ_BASE=/opt/activemq ACTIVEMQ_CONF=/opt/activemq/conf ACTIVEMQ_DATA=/tmp/activemq-data HOME=/tmp/activemq-home JAVA_HOME=/opt/java PATH=/opt/java/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WORKDIR /opt/benchmark
CMD ["bash", "/opt/benchmark/server-foreground.sh"]
