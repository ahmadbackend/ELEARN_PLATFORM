# Frontend image: nginx serving the static SPA and fronting the Django backend, so the
# app and the API share one origin (no CORS, no cross-origin websocket).
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY proxy_headers.conf /etc/nginx/proxy_headers.conf
COPY . /usr/share/nginx/html/

# only the app itself belongs in the web root
RUN rm -rf /usr/share/nginx/html/Dockerfile \
           /usr/share/nginx/html/nginx.conf \
           /usr/share/nginx/html/proxy_headers.conf \
           /usr/share/nginx/html/.dockerignore

EXPOSE 80
