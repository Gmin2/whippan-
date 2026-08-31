# backend

The plan for turning whippan from a local editor into a hosted product with
accounts. Written before any code, because the pieces here are painful to
change once there is data in them.

Decisions already taken: **Azure**, **Bicep**, **Better Auth**, a **platform API
key with a free allowance metered in generations**, **private workspaces with
the tenancy plumbing built in**, and **two model providers, OpenAI and Quiver**.

## 1. why this is not a three-box app

Most apps need a frontend, an API and a database. whippan needs two more, and
only for one reason: **exporting a film runs a native binary that saturates a
CPU core for seconds to minutes.**

```
   browser
      |
 [ editor ]            static files from `vite build`
      |  https
 [   api  ]            hono. auth, films, model calls, enqueue
    |  |  |
    |  |  +--------->  [ postgres ]   users, workspaces, films, job records
    |  |
    |  +------------>  [ blob ]       mp4s, uploaded images
    |  "render film X"
 [  queue  ]
      |
 [ renderer ]          rust + ffmpeg. wakes, renders, writes, sleeps
```

Blob and Queue are two features of one **Storage Account**, so it is five
resources, not six.

If the renderer shared the API container, one person exporting would make the
app unresponsive for everyone. And an HTTP request cannot wait minutes, which is
why the queue exists rather than a synchronous call.

## 2. what has to change in code that already exists

Three things are incompatible with running this in the cloud, all of them
current bugs waiting to happen rather than new work:

- **`ExportQueue` holds jobs in memory.** A container that scales to zero is a
  container that dies. Every in-flight render and every job record goes with it.
  Job state moves to Postgres; the in-process queue becomes a Storage Queue.
- **`FsStore` reads films from a directory.** Becomes `PgStore`. `DocStore`
  already isolates this: `list/get/put/has/assets` is the whole surface, so this
  is one new file and nothing else changes.
- **`apps/server/Dockerfile` contains neither the export binary nor ffmpeg**, so
  exports would fail from that image today. It becomes the API image only, and
  the renderer gets its own.

The retention sweeper in `ExportQueue` can be deleted outright: blob lifecycle
management expires old exports declaratively.

## 3. data

Postgres. Films stay as `jsonb` because `stage` and `anim` are already JSON
documents, and JSONB means the format can grow without a migration every time.

```sql
-- Better Auth owns: user, session, account, verification

workspaces   id, name, slug, created_at
members      workspace_id, user_id, role                 -- 'owner' | 'member'

films        id, workspace_id, slug, title, note,
             stage jsonb, anim jsonb,
             created_at, updated_at
             unique (workspace_id, slug)

assets       id, workspace_id, blob_key, mime, bytes, created_at

exports      id, workspace_id, film_id, status,          -- queued|running|done|failed|cancelled
             fps, supersample,
             frames, total_frames, bytes, blob_key,
             error, log,
             queued_at, started_at, finished_at

usage        workspace_id, month, kind, count            -- kind: film|screen|motion|vector
             primary key (workspace_id, month, kind)
```

**`workspace_id` is on every table from day one** even though the UI only shows
one personal workspace. Adding tenancy later is a brutal migration; adding a
column nobody reads is free. Slugs are unique **per workspace**, not globally,
or two users can never both have a film called `launch`.

## 4. auth

Better Auth, self-hosted, tables in our Postgres.

- email + password, plus Google and GitHub
- sessions in Postgres, cookie-based, `SameSite=Lax`, `Secure` in production
- the **organizations plugin** provides workspaces, so members and roles are not
  hand-rolled
- on signup: create the user, create their personal workspace, make them owner

The editor is a separate origin from the API, so cookies are cross-site. Either
serve both from one hostname behind Static Web Apps' API proxy, or set
`SameSite=None; Secure` with an explicit CORS allowlist. **Prefer one hostname**
— fewer cookie edge cases and no CORS preflight on every request.

`config.corsOrigins` already exists and already refuses `*` in production.

## 5. metering

One generation is one credit, whatever it cost us. A film, a screen, a motion
proposal and an SVG are all 1.

```
before the call   read usage for (workspace, month, kind); refuse over quota
after success     increment
on failure        nothing, so a failed call is free
```

Explainable in the UI as "14 of 20 left this month", enforceable before we spend
anything, and it matches what a user thinks they did. We absorb the variance
between a motion tweak and a whole film, which at this volume is noise.

A workspace may later add its own key to bypass the quota entirely; the column
exists, the UI comes later.

## 6. the render protocol

```
POST /api/films/:slug/export
  -> insert exports row (queued)
  -> put {exportId} on the storage queue
  -> 202 { id }

renderer job (KEDA wakes it on queue depth)
  -> claim the row, mark running
  -> pull stage/anim from postgres
  -> run the export binary, parse "progress N/M" into the row
  -> upload the mp4 to blob, mark done with blob_key and bytes
  -> on crash: the message reappears after its visibility timeout and is retried
     twice, then the row is marked failed

GET /api/exports/:id        -> the row, as the client already expects
GET /api/exports/:id/file   -> 302 to a short-lived SAS url
```

The client's existing polling loop and progress bar work unchanged, because the
shape of `JobView` does not change.

**Concurrency is the queue's**, not a number in our config: `parallelism` on the
job replica. Cancellation sets the row to `cancelled`; the renderer checks it
between frames and exits.

## 7. storage layout

One storage account, two blob containers and one queue.

```
blob/assets/<workspace>/<uuid>.<ext>      user uploads
blob/exports/<workspace>/<exportId>.mp4   rendered films
queue/renders                             {"exportId": "..."}
```

Both containers private. Everything reaches the browser through a **short-lived
SAS url** the API mints, never a public container.

Lifecycle rule: delete `exports/` blobs older than 7 days. That replaces the
retention sweeper.

## 8. images

Two of them, built from the repo root because the renderer needs `assets/fonts`
and `assets/sfx`.

- **`api`** — node:22-alpine, the compiled Hono service. Small.
- **`renderer`** — the release `export` binary (4.5MB), ffmpeg, and
  `assets/fonts` + `assets/sfx` (1.6MB). Roughly 150-200MB with ffmpeg.

The renderer resolves fonts relative to its working directory, so `WORKDIR` must
be the directory holding `assets/`.

## 9. infrastructure

Bicep, because it needs no tool beyond the `az` CLI, has no state file to lose,
and is what every Azure error message assumes.

```
infra/
  main.bicep        composes the modules, takes the env name
  data.bicep        postgres flexible (burstable B1ms), storage account,
                    blob containers, queue, lifecycle rule, key vault
  api.bicep         container app, minReplicas 0, secrets from key vault
  renderer.bicep    container apps JOB, keda queue trigger, parallelism 1
  registry.bicep    container registry
  deploy.sh         az login -> build both images -> push -> az deployment
  README.md         what each parameter is and how to run it once
```

Postgres is Burstable and always on. With credits that is the right trade: true
scale-to-zero Postgres does not exist on Azure, and chasing it buys nothing but
connection-pooling pain.

The renderer is where scale-to-zero actually earns its keep, and Container Apps
Jobs does it natively.

## 10. secrets

Key Vault, referenced by the container apps rather than baked into images.

```
OPENAI_API_KEY        text: motion, screen, film
QUIVERAI_API_KEY      vectors
DATABASE_URL          postgres
STORAGE_CONNECTION    blob + queue
BETTER_AUTH_SECRET    session signing
GOOGLE_CLIENT_ID/SECRET, GITHUB_CLIENT_ID/SECRET
```

`src/index.ts` already loads a local `.env` with the real environment winning,
so nothing changes for local development.

## 11. models

Two providers, deliberately.

- **OpenAI** for motion, screen and film. The three contracts in
  `ai/providers.ts` carry over as rules, but they were written and verified
  against Claude, so they need a tuning pass and stricter JSON handling.
- **Quiver Arrow 1.1** for vectors.

**No image generation.** Of 6298 nodes across the 31 films, exactly **7 are
images**, all in one film. More importantly a bitmap is motion-dead: it can be
moved, faded and scaled and nothing else. A Quiver SVG becomes a path node the
engine can fill, stroke and morph with `dseq`. Paper needs raster generation
because its output is a static page; ours moves. If a raster is ever wanted,
`gpt-image-1` is behind the OpenAI key already present.

What users actually need for real product shots is **upload**, which is the
`assets` path, not generation.

## 12. order of work

Each rung leaves the app working.

1. Postgres + `PgStore` behind the existing `DocStore`, migrating `docs/` in.
   No auth yet. Proves the swap in isolation.
2. Better Auth, workspaces, and `workspace_id` on films. Editor gets sign in.
3. Blob for assets and exports, still rendering in-process.
4. Split the renderer out: queue, job image, `exports` table. Delete the
   in-memory queue.
5. Metering and quotas on the model routes.
6. Bicep and `deploy.sh`, deployed to a staging environment.
7. Swap Anthropic for OpenAI and re-tune the three contracts.

## 13. deliberately not doing

- **Kubernetes.** Container Apps *is* Kubernetes with the cluster managed. Raw
  AKS means node pools billing 24/7, upgrades, ingress and RBAC, for two
  containers and one developer. Revisit at six or eight services.
- **Teams, invites and sharing.** The schema supports them; the UI does not
  ship them.
- **Payments.** Metering first; a paywall means nothing until the numbers are
  real.
- **Multi-cloud.** The AWS credits stay unspent. Portability costs discipline
  now for an option that may never be taken.
