ARG BUILDER_IMAGE=alpine:3.24@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf
FROM ${BUILDER_IMAGE}

ARG NGINX_VERSION=1.30.6
ARG NGINX_MODULE_VERSION=1.2.2
ARG NGINX_MODULE_COMMIT=23e1873aa62acb58b7881eed2a501f5bf35b82e9
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732

ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1

RUN apk add --no-cache bash build-base ca-certificates coreutils gcovr graphviz graphviz-dev make openssl-dev pcre2-dev python3 zlib-dev

COPY source/nginx-1.30.6.tar.gz /tmp/nginx-1.30.6.tar.gz
COPY source/nginx-1.30.6.tar.gz.asc /tmp/nginx-1.30.6.tar.gz.asc
COPY source/pluknet.key /tmp/pluknet.key
COPY source/nginx-rtmp-module-v1.2.2.tar.gz /tmp/nginx-rtmp-module-v1.2.2.tar.gz
COPY source/module-commit.json /tmp/module-commit.json
COPY source/verification.txt /tmp/verification.txt
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/aflnet-commit.txt /tmp/aflnet-commit.txt
COPY source/aflnet-commit.txt /work/aflnet-commit.txt
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY source-lock.json /work/source-lock.json
COPY rtmp_aflnet.c patch_aflnet_rtmp.py build_aflnet.sh rtmp-fuzz-helper.c rtmp_parser_test.c rtmp_proxy.py rtmp_protocol.py /work/
COPY nginx.conf rtmp.dict rtmp_smoke.py replay_queue.py run.sh validate.sh capture-build.sh /work/
COPY seeds/ /work/seeds/

RUN set -eux; \
    cd /tmp; sha256sum -c SHA256SUMS; \
    mkdir -p /src/nginx /src/nginx-rtmp-module /opt/aflnet /work/build-evidence /work/results; \
    tar -xzf /tmp/nginx-1.30.6.tar.gz --strip-components=1 -C /src/nginx; \
    tar -xzf /tmp/nginx-rtmp-module-v1.2.2.tar.gz --strip-components=1 -C /src/nginx-rtmp-module; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    bash /work/build_aflnet.sh; \
    cd /src/nginx; \
    ./configure --prefix=/opt/nginx --sbin-path=/opt/nginx/sbin/nginx --conf-path=/opt/nginx/conf/nginx.conf --pid-path=/tmp/nginx.pid --lock-path=/tmp/nginx.lock --error-log-path=stderr --with-debug --with-cc-opt='-O0 -g --coverage' --with-ld-opt='--coverage' --add-module=/src/nginx-rtmp-module; \
    make -j2; \
    make install; \
    chmod -R a+rwX /opt/nginx/logs; \
    find /src/nginx/objs -type d -exec chmod a+w {} +; \
    apk info -vv > /work/build-evidence/alpine-packages.txt; \
    /opt/nginx/sbin/nginx -v 2> /work/build-evidence/nginx-version.txt; \
    grep -q "nginx/${NGINX_VERSION}" /work/build-evidence/nginx-version.txt; \
    python3 -c 'import json,sys; assert json.load(open("/tmp/module-commit.json"))["sha"] == sys.argv[1]' "$NGINX_MODULE_COMMIT"; \
    printf 'target_version=nginx-%s + nginx-rtmp-module-v%s (%s)\n' "$NGINX_VERSION" "$NGINX_MODULE_VERSION" "$NGINX_MODULE_COMMIT" > /work/build-evidence/build-lock.txt; \
    printf 'nginx_archive_sha256=%s\n' '3cf46f5ed7504d460125866b7bea99fb357f31d887e2e63b35503310e9b8b6c8' >> /work/build-evidence/build-lock.txt; \
    printf 'module_archive_sha256=%s\n' '07f19b7bffec5e357bb8820c63e5281debd45f5a2e6d46b1636d9202c3e09d78' >> /work/build-evidence/build-lock.txt; \
    printf 'builder_image=%s\n' 'alpine:3.24@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\n' "$AFLNET_COMMIT" >> /work/build-evidence/build-lock.txt; \
    printf 'nginx_binary_sha256=' > /work/build-evidence/nginx-binary.sha256; sha256sum /opt/nginx/sbin/nginx >> /work/build-evidence/nginx-binary.sha256; \
    printf 'module_commit=%s\n' "$NGINX_MODULE_COMMIT" > /work/build-evidence/module-commit.txt; \
    /opt/nginx/sbin/nginx -t -c /work/nginx.conf; \
    rm -f /opt/nginx/logs/access.log; \
    rm -f /tmp/nginx.pid /tmp/nginx.lock; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh /work/rtmp_proxy.py /work/rtmp_smoke.py /work/replay_queue.py

WORKDIR /work
ENTRYPOINT ["/bin/bash"]
