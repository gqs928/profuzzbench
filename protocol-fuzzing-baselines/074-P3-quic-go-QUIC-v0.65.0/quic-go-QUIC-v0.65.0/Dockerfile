ARG BASE_IMAGE=docker.io/library/ubuntu:26.04@sha256:065aa8626841f16057b78b027b464cd59c4fac36c204c72dcbf48d66f5fa8a96
FROM ${BASE_IMAGE}
ENV DEBIAN_FRONTEND=noninteractive \
    GOROOT=/usr/local/go \
    PATH=/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    GOTOOLCHAIN=local \
    GOMAXPROCS=2 \
    GOPROXY=https://proxy.golang.org,direct \
    GOSUMDB=sum.golang.org
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates git python3 tar \
    && rm -rf /var/lib/apt/lists/*
COPY source/go1.27.4.linux-amd64.tar.gz /tmp/go.tar.gz
COPY source/quic-go-v0.65.0.tar.gz /tmp/quic-go.tar.gz
RUN echo '7226736c2339719cda28fbf3a54d71aa63bcefe376e98cef00034268dab24840  /tmp/go.tar.gz' | sha256sum -c - \
    && echo '19cb9a7f8a6bf6f46cda4a00bd186894afae692aee0ce3baf055edf66064bf9c  /tmp/quic-go.tar.gz' | sha256sum -c - \
    && tar -xzf /tmp/go.tar.gz -C /usr/local \
    && mkdir -p /opt/quic-go \
    && tar -xzf /tmp/quic-go.tar.gz -C /opt/quic-go --strip-components=1 \
    && rm /tmp/go.tar.gz /tmp/quic-go.tar.gz \
    && go version
WORKDIR /opt/quic-go
RUN go mod download \
    && go test -run '^$' ./internal/wire
COPY run.sh summarize_fuzz_log.py README.md ACCEPTANCE.md \
     PACKAGE-MANIFEST.md source-lock.json toolchain-lock.json /opt/benchmark/
RUN chmod 755 /opt/benchmark/run.sh
WORKDIR /opt/quic-go
CMD ["/bin/bash"]
