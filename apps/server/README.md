# @whippan/server

The film API. Boards reads and writes documents through this rather than
touching a filesystem itself, so the editor runs the same locally and deployed.

## routes

| method | path | does |
|---|---|---|
| GET | `/healthz` | liveness |
| GET | `/api/films` | the registry every client lists from |
| GET | `/api/films/:slug` | `{ stage, anim }` for one film |
| PUT | `/api/films/:slug` | replace a film; validated, atomic |

`PUT` refuses anything that is not recognisably a document — no scenes, a scene
without an id, a missing `tracks` array, a size that is not `[w, h]`. The engine
fails *silently* on a malformed document, so the API has to fail loudly instead.

## configuration

| env | default | meaning |
|---|---|---|
| `PORT` | `8903` | listen port |
| `DOCS_DIR` | the repo's `docs/` | where films are stored |
| `CORS_ORIGINS` | `*` in dev, empty in prod | comma-separated allowed origins |
| `NODE_ENV` | `development` | `production` tightens the CORS default |

## storage

`DocStore` (`src/store/types.ts`) is the only thing the API knows about
storage. `FsStore` covers local development and any container with a volume.
Object storage or a database is a new implementation of that interface and no
change to the routes.

## running

```sh
pnpm --filter @whippan/server dev     # tsx watch on :8903
pnpm --filter @whippan/server build && pnpm --filter @whippan/server start
docker build -t whippan-api . && docker run -p 8903:8903 -v "$PWD/../../docs:/data/docs" whippan-api
```
