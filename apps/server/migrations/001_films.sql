-- films move out of the filesystem.
--
-- workspace_id is here from the very first migration even though nothing sets
-- it to anything but the default workspace yet. adding tenancy later is a
-- migration across every row; adding a column nobody reads is free.

create table workspaces (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  slug        text not null unique,
  created_at  timestamptz not null default now()
);

-- everything before accounts exist belongs here, and keeps belonging here
insert into workspaces (id, name, slug)
values ('00000000-0000-0000-0000-000000000001', 'whippan', 'whippan');

create table films (
  id            uuid primary key default gen_random_uuid(),
  workspace_id  uuid not null references workspaces(id) on delete cascade,
  slug          text not null,
  title         text not null,
  -- how the editor's film menu groups the library
  grp           text not null default 'films'
                check (grp in ('films', 'reproductions', 'primitives')),
  -- the two layers, stored as documents because that is what they are. jsonb
  -- so the format can grow without a migration every time a field appears
  stage         jsonb not null,
  anim          jsonb not null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  -- unique per workspace, never globally, or two users can never both have a
  -- film called "launch"
  unique (workspace_id, slug)
);

create index films_workspace_updated on films (workspace_id, updated_at desc);

create table assets (
  id            uuid primary key default gen_random_uuid(),
  workspace_id  uuid not null references workspaces(id) on delete cascade,
  -- the path a document's `src` refers to, eg /assets/solder/home.png. still a
  -- path today; becomes a blob key when storage moves off disk
  src           text not null,
  mime          text,
  bytes         bigint not null default 0,
  created_at    timestamptz not null default now(),
  unique (workspace_id, src)
);
