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

# Stage 2: Production (Next.js runtime)
FROM node:20-alpine AS production

# Install wget for healthcheck
RUN apk add --no-cache wget

# Create non-root user
RUN addgroup -g 1001 -S nodejs || true && \
    adduser -S -D -H -u 1001 -h /home/nextjs -s /sbin/nologin -G nodejs nextjs || true

WORKDIR /app/frontend

# Install production dependencies
COPY frontend/package*.json ./
RUN if [ -f package-lock.json ]; then \
        npm ci --no-audit --no-fund --omit=dev; \
    else \
        npm install --no-audit --no-fund --omit=dev; \
    fi

# Copy built application
COPY --from=build /app/frontend/.next ./.next
COPY --from=build /app/frontend/public ./public
COPY --from=build /app/frontend/package.json ./package.json

# Set permissions
RUN chown -R nextjs:nodejs /app/frontend

USER nextjs

ENV PORT=80
ENV NODE_ENV=production

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

ARG VERSION=unknown
ARG COMMIT=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="ecommerce-frontend"
LABEL org.opencontainers.image.description="Next.js frontend"
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.revision=$COMMIT
LABEL org.opencontainers.image.created=$BUILD_DATE

CMD ["npm", "start"]
