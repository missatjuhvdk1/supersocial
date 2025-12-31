# ============================================
# Industry-Standard Bun + Next.js Dockerfile
# Multi-stage build optimized for production
# ============================================

# Stage 1: Dependencies installation (cached layer)
FROM oven/bun:1.1.38 AS deps
WORKDIR /app

# Install libc6-compat for Alpine compatibility (if needed)
# Bun image is Debian-based, so we're good

# Copy package files for dependency caching
COPY package.json bun.lock ./

# Install ALL dependencies (dev + prod) with frozen lockfile
# This ensures reproducible builds
RUN bun install --frozen-lockfile

# Stage 2: Production dependencies only
FROM oven/bun:1.1.38 AS prod-deps
WORKDIR /app

COPY package.json bun.lock ./

# Install only production dependencies
RUN bun install --frozen-lockfile --production

# Stage 3: Builder - Build the application
FROM oven/bun:1.1.38 AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application source
COPY . .

# Build-time environment variables
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build Next.js application with standalone output
RUN bun run build

# Stage 4: Production runner - minimal image
FROM oven/bun:1.1.38-slim AS runner
WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Security: Create non-root user
RUN groupadd --gid 1001 nodejs && \
    useradd --uid 1001 --gid nodejs --shell /bin/bash --create-home nextjs

# Copy public assets
COPY --from=builder /app/public ./public

# Create .next directory with proper ownership
RUN mkdir .next && chown nextjs:nodejs .next

# Copy standalone output (only necessary files)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Security: Switch to non-root user
USER nextjs

# Expose application port
EXPOSE 3000

# Health check - uses wget since it's lighter than curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD bun -e "fetch('http://localhost:3000/').then(r => r.ok ? process.exit(0) : process.exit(1)).catch(() => process.exit(1))"

# Start the application with Bun
CMD ["bun", "server.js"]
