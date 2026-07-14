# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app/frontend

COPY frontend/package*.json ./

# Detect package manager
RUN if [ -f package-lock.json ]; then \
        npm ci --no-audit --no-fund; \
    elif [ -f yarn.lock ]; then \
        yarn install --frozen-lockfile; \
    else \
        npm install --no-audit --no-fund; \
    fi

COPY frontend/ .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine AS production

# Create non-root user
RUN addgroup -g 1001 -S nginx || true && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx nginx || true

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/out /usr/share/nginx/html

RUN chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx/conf.d /usr/share/nginx/html

USER nginx

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

ARG VERSION=unknown
ARG COMMIT=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="ecommerce-frontend"
LABEL org.opencontainers.image.description="React frontend"
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.revision=$COMMIT
LABEL org.opencontainers.image.created=$BUILD_DATE

CMD ["nginx", "-g", "daemon off;"]
