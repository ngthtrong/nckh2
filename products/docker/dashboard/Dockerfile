# Dashboard điều phối: trang tĩnh (HTML/CSS/JS + Leaflet đóng gói sẵn) + nginx proxy API về backend.
#   docker build -f products/docker/dashboard/Dockerfile -t flood-rescue/dashboard .
FROM nginx:1.29-alpine

ENV BACKEND_URL=http://be:8000
COPY products/docker/dashboard/default.conf.template /etc/nginx/templates/default.conf.template
COPY products/be/templates/dashboard.html /usr/share/nginx/html/index.html
COPY products/be/static/ /usr/share/nginx/html/static/

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
