ARG BUILDER_IMAGE=golang:1.27-alpine3.24@sha256:fa3d596898d9f126af7c01d14ee7597bab3f39cccf392ef36b69fe77cd681f18
FROM $BUILDER_IMAGE

ARG MEDIAMTX_VERSION=v1.21.3
ARG MEDIAMTX_ARCHIVE_SHA256=b6d0f252adb85be5d1a3897a22883af335b54218b6cc66c831e3dd1cc03c6f36
ARG AFLNET_COMMIT=0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732
ARG AFLNET_ARCHIVE_SHA256=251f24bf2dddb8118eab56ef2b90c92b06f67c096c62543659eaaf31a31d955d

ENV AFLNET=/opt/aflnet \
    AFL_PATH=/opt/aflnet \
    AFL_SKIP_CPUFREQ=1 \
    AFL_NO_AFFINITY=1 \
    AFL_NO_UI=1 \
    GOTOOLCHAIN=local

RUN apk add --no-cache bash build-base ca-certificates coreutils graphviz-dev graphviz make pkgconf python3

COPY source/mediamtx-v1.21.3.tar.gz /tmp/mediamtx-v1.21.3.tar.gz
COPY source/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz
COPY source/aflnet-commit.txt /tmp/aflnet-commit.txt
COPY source/aflnet-commit.txt /work/aflnet-commit.txt
COPY source/SHA256SUMS /tmp/SHA256SUMS
COPY source-lock.json /work/source-lock.json
COPY rtmp_aflnet.c patch_aflnet_rtmp.py build_aflnet.sh rtmp-fuzz-helper.c rtmp_parser_test.c rtmp_proxy.py rtmp_protocol.py /work/
RUN set -eux; \
    cd /tmp; sha256sum -c SHA256SUMS; \
    mkdir -p /src/mediamtx /opt/aflnet /opt/mediamtx /work/build-evidence /work/results; \
    tar -xzf /tmp/mediamtx-v1.21.3.tar.gz --strip-components=1 -C /src/mediamtx; \
    tar -xzf /tmp/aflnet-0f51f9edf837c2f3d8f0ea98dc3b6c19b4562732.tar.gz -C /opt/aflnet; \
    sed -i 's/\r$//' /opt/aflnet/Makefile /opt/aflnet/aflnet.h /opt/aflnet/afl-fuzz.c /opt/aflnet/afl-replay.c /opt/aflnet/aflnet-replay.c; \
    bash /work/build_aflnet.sh

WORKDIR /src/mediamtx
RUN go mod download && go mod verify && go generate ./...
RUN printf '%s\n' "$MEDIAMTX_VERSION" > internal/core/VERSION

COPY mediamtx.yml rtmp.dict rtmp_protocol.py rtmp_proxy.py rtmp_smoke.py run.sh validate.sh capture-build.sh /work/
COPY seeds/ /work/seeds/

RUN set -eux; \
    CGO_ENABLED=0 go build -cover -coverpkg=./... -trimpath -o /opt/mediamtx/mediamtx .; \
    install -m 0644 /src/mediamtx/LICENSE /opt/mediamtx/LICENSE; \
    cp /work/mediamtx.yml /opt/mediamtx/mediamtx.yml; \
    printf 'target_version=%s\n' "$MEDIAMTX_VERSION" > /work/build-evidence/build-lock.txt; \
    printf 'target_archive_sha256=%s\n' "$MEDIAMTX_ARCHIVE_SHA256" >> /work/build-evidence/build-lock.txt; \
    printf 'builder_image=%s\n' 'golang:1.27-alpine3.24@sha256:fa3d596898d9f126af7c01d14ee7597bab3f39cccf392ef36b69fe77cd681f18' >> /work/build-evidence/build-lock.txt; \
    printf 'go_version=' >> /work/build-evidence/build-lock.txt; go version >> /work/build-evidence/build-lock.txt; \
    printf 'go_module_go_directive=' >> /work/build-evidence/build-lock.txt; sed -n 's/^go /go /p' go.mod >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_commit=%s\n' "$AFLNET_COMMIT" >> /work/build-evidence/build-lock.txt; \
    printf 'aflnet_archive_sha256=%s\n' "$AFLNET_ARCHIVE_SHA256" >> /work/build-evidence/build-lock.txt; \
    printf 'target_binary_sha256=' > /work/build-evidence/target-binary.sha256; sha256sum /opt/mediamtx/mediamtx >> /work/build-evidence/target-binary.sha256; \
    printf 'go_sum_sha256=' > /work/build-evidence/go-sum.sha256; sha256sum /src/mediamtx/go.sum >> /work/build-evidence/go-sum.sha256; \
    printf 'go_build_info:\n' > /work/build-evidence/go-version-info.txt; go version -m /opt/mediamtx/mediamtx >> /work/build-evidence/go-version-info.txt; \
    printf 'aflnet_version:\n' > /work/build-evidence/aflnet-version.txt; /opt/aflnet/afl-fuzz -h >> /work/build-evidence/aflnet-version.txt 2>&1 || true; \
    /opt/mediamtx/mediamtx --version > /work/build-evidence/target-version.txt 2>&1; \
    chmod +x /work/run.sh /work/validate.sh /work/capture-build.sh /work/rtmp_proxy.py /work/rtmp_smoke.py

WORKDIR /work
ENTRYPOINT ["/bin/bash"]
