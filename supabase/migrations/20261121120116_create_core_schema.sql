-- QuantLab core schema (docs/adr/0009-esquema-relacional-e-persistencia.md).
--
-- * The database owns the schema; the Django models are unmanaged (D3).
-- * The browser may only READ through the Data API; every write goes through the
--   Django backend, which validates it (RULE 038).
-- * Experiments and runs are immutable: nobody but the table owner gets UPDATE.
-- * No secret lives here. The backend role is created WITHOUT a login; enable it
--   outside Git (docs/runbook-supabase.md).

-- ---------------------------------------------------------------------------
-- Backend role and private schema
-- ---------------------------------------------------------------------------
-- Django's own tables (django_migrations, ...) go to the `backend` schema, which is
-- not exposed by the Data API, so they never appear next to the domain tables.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'quantlab_backend') then
    create role quantlab_backend nologin;
  end if;
end
$$;

create schema if not exists backend;
revoke all on schema backend from public, anon, authenticated;
grant usage, create on schema backend to quantlab_backend;
grant usage on schema public to quantlab_backend;
alter role quantlab_backend set search_path = backend, public;

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------
create table public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null check (length(btrim(name)) > 0),
  description text,
  created_at timestamptz not null default now(),
  unique (id, user_id)
);

create table public.experiments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  project_id uuid not null,
  name text not null check (length(btrim(name)) > 0),
  hypothesis text not null check (length(btrim(hypothesis)) > 0),
  model text not null check (length(btrim(model)) > 0),
  parameters jsonb not null default '{}'::jsonb check (jsonb_typeof(parameters) = 'object'),
  -- 2^53 - 1: the largest integer a browser represents exactly (engine MAX_SEED).
  seed bigint not null check (seed between 0 and 9007199254740991),
  data_hash char(64) check (data_hash ~ '^[0-9a-f]{64}$'),
  engine_version text not null check (length(btrim(engine_version)) > 0),
  created_at timestamptz not null default now(),
  unique (id, user_id),
  -- A composite key keeps a project and its experiments under the same owner.
  foreign key (project_id, user_id)
    references public.projects (id, user_id) on delete cascade
);

create table public.experiment_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  experiment_id uuid not null,
  metrics jsonb not null check (jsonb_typeof(metrics) = 'object'),
  environment jsonb not null check (jsonb_typeof(environment) = 'object'),
  started_at timestamptz not null,
  execution_time_ms double precision not null check (execution_time_ms >= 0),
  created_at timestamptz not null default now(),
  foreign key (experiment_id, user_id)
    references public.experiments (id, user_id) on delete cascade
);

-- RULE 040: source, frequency and adjustment are mandatory, so adjusted and
-- unadjusted series are never mixed without being identified.
create table public.dataset_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  symbol text not null check (length(btrim(symbol)) > 0),
  source text not null check (length(btrim(source)) > 0),
  frequency text not null check (frequency in ('1d', '1wk', '1mo')),
  adjusted boolean not null,
  currency text,
  start_date date not null,
  end_date date not null,
  row_count integer not null check (row_count >= 0),
  data_hash char(64) not null check (data_hash ~ '^[0-9a-f]{64}$'),
  storage_path text,
  created_at timestamptz not null default now(),
  check (end_date >= start_date),
  unique (user_id, data_hash)
);

comment on table public.projects is 'Groups the studies of one researcher.';
comment on table public.experiments is 'Immutable experiment definition (mirrors quantlab.research.Experiment).';
comment on table public.experiment_runs is 'One execution of an experiment (mirrors quantlab.research.ExperimentRun).';
comment on table public.dataset_records is 'Provenance of a data set used by an experiment (RULE 040).';

-- Every foreign key is indexed, and so is user_id, which every policy filters on.
create index projects_user_id_idx on public.projects (user_id);
create index experiments_user_id_idx on public.experiments (user_id);
create index experiments_project_idx on public.experiments (project_id, user_id);
create index experiment_runs_user_id_idx on public.experiment_runs (user_id);
create index experiment_runs_experiment_idx on public.experiment_runs (experiment_id, user_id);
create index dataset_records_user_id_idx on public.dataset_records (user_id);

-- ---------------------------------------------------------------------------
-- Privileges
-- ---------------------------------------------------------------------------
-- Depending on the project's Data API settings, new tables in `public` may be
-- reachable by default, so privileges are revoked and granted explicitly.
revoke all on public.projects, public.experiments,
  public.experiment_runs, public.dataset_records from anon, authenticated;

-- The browser only reads. RLS limits the rows to the owner.
grant select on public.projects, public.experiments,
  public.experiment_runs, public.dataset_records to authenticated;

-- The backend writes. Experiments and runs are immutable: no UPDATE.
grant select, insert, update, delete on public.projects to quantlab_backend;
grant select, insert, update, delete on public.dataset_records to quantlab_backend;
grant select, insert, delete on public.experiments to quantlab_backend;
grant select, insert, delete on public.experiment_runs to quantlab_backend;

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
alter table public.projects enable row level security;
alter table public.experiments enable row level security;
alter table public.experiment_runs enable row level security;
alter table public.dataset_records enable row level security;

-- Owners read their own rows. `(select auth.uid())` is evaluated once per query.
create policy projects_owner_select on public.projects
  for select to authenticated using ((select auth.uid()) = user_id);
create policy experiments_owner_select on public.experiments
  for select to authenticated using ((select auth.uid()) = user_id);
create policy experiment_runs_owner_select on public.experiment_runs
  for select to authenticated using ((select auth.uid()) = user_id);
create policy dataset_records_owner_select on public.dataset_records
  for select to authenticated using ((select auth.uid()) = user_id);

-- The backend role sees every row and the Django code filters by owner (ADR 0009,
-- option D4). RLS stays the second layer for everything that reaches the Data API.
create policy projects_backend on public.projects
  for all to quantlab_backend using (true) with check (true);
create policy experiments_backend on public.experiments
  for all to quantlab_backend using (true) with check (true);
create policy experiment_runs_backend on public.experiment_runs
  for all to quantlab_backend using (true) with check (true);
create policy dataset_records_backend on public.dataset_records
  for all to quantlab_backend using (true) with check (true);
