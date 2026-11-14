ARG NODE_IMAGE=node:24-bookworm-slim@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9
FROM ${NODE_IMAGE}

ARG HARAKA_VERSION=3.4.0
ARG HARAKA_COMMIT=2e1ea5b643c7a2e8e6cfaec2cb742edd6dc66dcf
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732

ENV AFL_PATH=/opt/aflnet AFL_NO_UI=1 AFL_SKIP_CPUFREQ=1 AFL_NO_AFFINITY=1
WORKDIR /work

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    build-essential ca-certificates coreutils graphviz libgraphviz-dev make pkg-config python3 \
    && rm -rf /var/lib/apt/lists/*

COPY source/Haraka-2e1ea5b.tar.gz /tmp/Haraka-2e1ea5b.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY source/Haraka-package-lock.json /tmp/Haraka-package-lock.json
COPY config/ /work/config/config/
COPY seeds/ /work/seeds/
COPY smtp.dict /work/smtp.dict
COPY haraka-fuzz-helper.c /tmp/haraka-fuzz-helper.c
COPY smoke.py summarize-v8-coverage.js run.sh validate.sh capture-build.sh /work/

RUN set -eux; cd /tmp; sha256sum -c SHA256SUMS; \
    mkdir -p /src/Haraka /opt/aflnet /work/build-evidence /work/results; \
    tar -xzf /tmp/Haraka-2e1ea5b.tar.gz --strip-components=1 -C /src/Haraka; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/aflnet.c; \
    AFL_NO_X86=1 CFLAGS='-O3 -funroll-loops -Wall -D_GNU_SOURCE -include libgen.h -D_FORTIFY_SOURCE=2 -g -Wno-pointer-sign -Wno-unused-result -DTRUE=1 -DFALSE=0' \
      make -C /opt/aflnet -j2 afl-fuzz afl-gcc afl-showmap afl-as; \
    cp /tmp/Haraka-package-lock.json /src/Haraka/package-lock.json; \
    npm ci --prefix /src/Haraka --omit=dev; \
    test "$(node -p "require('/src/Haraka/package.json').version")" = "${HARAKA_VERSION}"; \
    printf 'target_version=%s\ntarget_commit=%s\n' "${HARAKA_VERSION}" "${HARAKA_COMMIT}" > /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\nnode_version=%s\nnpm_version=%s\n' "${AFLNET_COMMIT}" "$(node --version)" "$(npm --version)" >> /work/build-evidence/build-lock.txt; \
    printf 'npm_lock_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /src/Haraka/package-lock.json | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_binary_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /opt/aflnet/afl-fuzz | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    printf 'helper_source_sha256=' >> /work/build-evidence/build-lock.txt; sha256sum /tmp/haraka-fuzz-helper.c | awk '{print $1}' >> /work/build-evidence/build-lock.txt; \
    AFL_QUIET=1 AFL_PATH=/opt/aflnet /opt/aflnet/afl-gcc -O2 -g -Wall -Wextra -Werror /tmp/haraka-fuzz-helper.c -o /opt/aflnet/haraka-fuzz-helper; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh; \
    chown -R node:node /work/config /work/seeds

USER node
ENTRYPOINT ["/bin/bash"]
