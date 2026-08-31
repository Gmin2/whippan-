-- 001 created a `workspaces` table before better-auth was chosen. its
-- organization plugin brings its own, with invitations and roles already
-- handled, so that is the one to keep. this repoints everything at it and
-- drops ours rather than carrying two ideas of the same thing.

insert into organization (id, name, slug, "createdAt")
     values ('00000000-0000-0000-0000-000000000001', 'whippan', 'whippan', now())
on conflict (id) do nothing;

-- organization.id is text, ours was uuid, so the column type changes with it
alter table films  drop constraint films_workspace_id_fkey;
alter table assets drop constraint assets_workspace_id_fkey;

alter table films  alter column workspace_id type text using workspace_id::text;
alter table assets alter column workspace_id type text using workspace_id::text;

alter table films add constraint films_workspace_fk
  foreign key (workspace_id) references organization(id) on delete cascade;
alter table assets add constraint assets_workspace_fk
  foreign key (workspace_id) references organization(id) on delete cascade;

drop table workspaces;
