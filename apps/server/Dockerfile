# build
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json tsconfig.json ./
RUN pnpm install --no-frozen-lockfile
COPY src ./src
RUN pnpm build && pnpm prune --prod

# run
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
# films live on a mounted volume or an object store; never baked into the image
ENV DOCS_DIR=/data/docs
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
EXPOSE 8903
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://127.0.0.1:8903/healthz || exit 1
USER node
CMD ["node", "dist/index.js"]
