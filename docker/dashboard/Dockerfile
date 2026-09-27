# Dashboard điều phối: trang tĩnh (Leaflet + Tailwind CDN) + nginx proxy API về backend.
#   docker build -f docker/dashboard/Dockerfile -t flood-rescue/dashboard .
FROM nginx:1.29-alpine

ENV BACKEND_URL=http://be:8000
COPY docker/dashboard/default.conf.template /etc/nginx/templates/default.conf.template
COPY be/templates/dashboard.html /usr/share/nginx/html/index.html

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
