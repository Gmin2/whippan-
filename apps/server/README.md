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
| GET | `/api/assets` | images a document can reference |
| POST | `/api/films/:slug/export` | queue a render; body carries the document |
| GET | `/api/exports` | every job |
| GET | `/api/exports/:id` | one job, with progress |
| DELETE | `/api/exports/:id` | cancel |
| GET | `/api/exports/:id/file` | the finished mp4, streamed |

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
| `EXPORT_BIN` | `target/release/export` | the compiled native renderer |
| `EXPORT_CWD` | the repo root | the renderer resolves fonts relative to this |
| `EXPORT_DIR` | `out/exports` | where finished mp4s land |
| `EXPORT_CONCURRENCY` | `2` | parallel renders; rendering is CPU-bound |
| `EXPORT_TIMEOUT_MS` | `600000` | a runaway render is killed after this |
| `EXPORT_RETENTION_MS` | `21600000` | artifacts are swept after this |

## export

Rendering is a job, not a request: a 28-second film is well over a thousand
frames. `POST` queues one and returns immediately; poll the job for progress
and fetch the file when it is done.

The **document travels in the request body**, not just the slug, so the editor
renders what is on screen including unsaved edits.

Needs the native renderer built and `ffmpeg` on PATH:

```sh
cargo build --release -p whippan-engine --bin export
```

The server says at boot whether both are present rather than failing on the
first request. Cancellation signals the whole process group, because the
renderer spawns ffmpeg as a child and signalling only the parent would orphan
it; partial output including the pre-mux intermediate is removed.

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
