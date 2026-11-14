FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
COPY source/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz /opt/benchmark/source/jre.tar.gz
COPY source/OpenJDK21U-jre_x64_linux_hotspot_21.0.13_9.tar.gz.sha256.txt /opt/benchmark/source/jre.sha256.txt
COPY source/apacheds-2.0.0.AM27.tar.gz /opt/benchmark/source/apacheds-2.0.0.AM27.tar.gz
COPY source/ApacheDS-2.0.0.AM27.tar.gz.sha512 /opt/benchmark/source/apacheds-2.0.0.AM27.tar.gz.sha512
COPY build/afl-fuzz /opt/benchmark/build/afl-fuzz
COPY build/ldap-ready-check /opt/benchmark/build/ldap-ready-check
COPY seeds/ /opt/benchmark/seeds/
COPY ldap.dict fuzz.sh server.sh /opt/benchmark/
RUN cd /opt/benchmark/source && echo "a535a1df9c6284d9618872984e026ae0352d1f7e9e0605425c0e6114f47351dd  jre.tar.gz" | sha256sum -c - && sha512sum -c apacheds-2.0.0.AM27.tar.gz.sha512 && mkdir -p /opt/java /opt/apacheds /opt/benchmark/build && tar -xzf jre.tar.gz --strip-components=1 -C /opt/java && tar -xzf apacheds-2.0.0.AM27.tar.gz --strip-components=1 -C /opt/apacheds && chmod 0755 /opt/benchmark/fuzz.sh /opt/benchmark/server.sh /opt/benchmark/build/afl-fuzz /opt/benchmark/build/ldap-ready-check
ENV ADS_HOME=/opt/apacheds JAVA_HOME=/opt/java PATH=/opt/java/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin JAVA_OPTS="-Xms128m -Xmx512m -XX:+ExitOnOutOfMemoryError"
EXPOSE 10389
ENTRYPOINT ["/opt/apacheds/bin/apacheds.sh"]
CMD ["run"]
