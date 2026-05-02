# =============================================================================
# library-frontend/Dockerfile
# Multi-stage build for Next.js 14
#
# Stages:
#   deps      — install node_modules (cached layer)
#   builder   — run `next build` to produce .next/standalone
#   runtime   — minimal final image, only the built output
# =============================================================================

# ── Stage 1: Install dependencies ─────────────────────────────────────────────
FROM node:20-alpine AS deps

# libc6-compat is required for some native Node modules on Alpine
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy only package files first — Docker caches this layer until they change
COPY package.json package-lock.json* ./

#RUN npm ci --frozen-lockfile
RUN npm install


# ── Stage 2: Build the Next.js app ────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy installed node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy the full source
COPY . .

# NEXT_PUBLIC_* variables must be available at BUILD time (baked into JS bundles)
# Pass a placeholder here; override at runtime via environment in docker-compose
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Enable Next.js standalone output — produces a self-contained server bundle
# (requires `output: 'standalone'` in next.config.mjs — see note below)
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build


# ── Stage 3: Runtime ──────────────────────────────────────────────────────────
FROM node:20-alpine AS runtime

RUN apk add --no-cache curl

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# ── Security: non-root user ───────────────────────────────────────────────────
RUN addgroup --gid 1001 appgroup \
 && adduser  --uid 1001 --ingroup appgroup --disabled-password appuser

# Copy the Next.js build output
# If standalone output is enabled in next.config.mjs, use the leaner copy:
#   COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
#   COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
#   COPY --from=builder --chown=appuser:appgroup /app/public ./public
#
# Standard copy (works with or without standalone mode):
COPY --from=builder --chown=appuser:appgroup /app/public       ./public
COPY --from=builder --chown=appuser:appgroup /app/.next        ./.next
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/package.json ./package.json

USER appuser

EXPOSE 3000

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# ── Start the Next.js production server ───────────────────────────────────────
CMD ["npm", "run", "start"]
