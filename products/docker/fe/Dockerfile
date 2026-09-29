# App Flutter (products/fe/app) bản web + nginx proxy API về backend (cùng origin, không cần CORS).
#   docker build -f products/docker/fe/Dockerfile -t flood-rescue/fe .                   # build Flutter trong Docker
#   docker build -f products/docker/fe/Dockerfile --target prebuilt -t flood-rescue/fe .  # dùng products/fe/app/build/web có sẵn
# Target mặc định (runtime) tải Flutter SDK ~1,6 GB. Khi mạng chậm, build web trên máy
# (products/scripts/demo/build_web.sh) rồi dùng target prebuilt.
# Bản web không có AI on-device (onnxruntime cần dart:ffi) và không có SMS; app Android
# vẫn build bằng scripts/demo/run_app.sh và trỏ tới cổng backend 8000.
ARG FLUTTER_VERSION=3.47.5

FROM debian:bookworm-slim AS build
ARG FLUTTER_VERSION
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git unzip xz-utils \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${FLUTTER_VERSION}-stable.tar.xz" \
    | tar -xJ -C /opt \
    && git config --global --add safe.directory /opt/flutter
ENV PATH=/opt/flutter/bin:$PATH \
    PUB_CACHE=/root/.pub-cache
RUN flutter config --no-analytics --enable-web >/dev/null && flutter precache --web

WORKDIR /src
COPY products/fe/app/pubspec.yaml products/fe/app/pubspec.lock ./
RUN flutter pub get
COPY products/fe/app/ ./
# Để trống = gọi API cùng origin (nginx bên dưới proxy về backend).
ARG SERVER_URL=
RUN flutter build web --release --no-wasm-dry-run --dart-define=SERVER_URL=${SERVER_URL}

FROM nginx:1.29-alpine AS base
ENV BACKEND_URL=http://be:8000
COPY products/docker/fe/default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

FROM base AS prebuilt
COPY products/fe/app/build/web /usr/share/nginx/html

FROM base AS runtime
COPY --from=build /src/build/web /usr/share/nginx/html
