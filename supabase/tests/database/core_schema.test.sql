-- pgTAP tests for the core schema (run with: npx supabase test db).
-- STATUS: written but NOT yet executed against the real Supabase stack (it needs Docker).
-- The same checks were run on an embedded Postgres 16 with stubs for the Supabase parts.
begin;

select plan(14);

-- Fixtures, created as the owner (RLS does not apply to it).
insert into auth.users (id) values
  ('00000000-0000-0000-0000-00000000000a'),
  ('00000000-0000-0000-0000-00000000000b');

insert into public.projects (id, user_id, name) values
  ('10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a', 'A'),
  ('10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', 'B');

insert into public.experiments (id, user_id, project_id, name, hypothesis, model, seed, engine_version) values
  ('20000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a',
   '10000000-0000-0000-0000-00000000000a', 'ea', 'ha', 'logistic_map', 7, '0.1.0');

-- 1-4: RLS is enabled everywhere.
select ok((select relrowsecurity from pg_class where oid = 'public.projects'::regclass), 'RLS on projects');
select ok((select relrowsecurity from pg_class where oid = 'public.experiments'::regclass), 'RLS on experiments');
select ok((select relrowsecurity from pg_class where oid = 'public.experiment_runs'::regclass), 'RLS on experiment_runs');
select ok((select relrowsecurity from pg_class where oid = 'public.dataset_records'::regclass), 'RLS on dataset_records');

-- 5-8: isolation and read-only access for signed-in users.
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-00000000000a","role":"authenticated"}', true);

select is((select count(*)::int from public.projects), 1, 'user A sees only the own project');
select throws_ok(
  $$ insert into public.projects (user_id, name) values ('00000000-0000-0000-0000-00000000000a', 'x') $$,
  '42501', null, 'the browser role cannot insert');
select throws_ok(
  $$ update public.projects set name = 'x' $$,
  '42501', null, 'the browser role cannot update');

select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-00000000000b","role":"authenticated"}', true);
select is((select count(*)::int from public.experiments), 0, 'user B does not see the experiment of A');

-- 9: anonymous users read nothing.
set local role anon;
select throws_ok($$ select * from public.projects $$, '42501', null, 'anon cannot read');

-- 10-13: the backend role, immutability and integrity.
set local role quantlab_backend;
select throws_ok(
  $$ update public.experiments set seed = 1 $$,
  '42501', null, 'the backend cannot update an experiment (immutable)');
select throws_ok(
  $$ insert into public.experiment_runs (user_id, experiment_id, metrics, environment, started_at, execution_time_ms)
     values ('00000000-0000-0000-0000-00000000000b', '20000000-0000-0000-0000-00000000000a', '{}', '{}', now(), 1) $$,
  '23503', null, 'a run cannot point at the experiment of another user');
select throws_ok(
  $$ insert into public.experiments (user_id, project_id, name, hypothesis, model, seed, engine_version)
     values ('00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000a', 'n', 'h', 'm', 9007199254740992, '0.1.0') $$,
  '23514', null, 'a seed above 2^53 - 1 is rejected');
select throws_ok(
  $$ insert into public.experiments (user_id, project_id, name, hypothesis, model, seed, engine_version, data_hash)
     values ('00000000-0000-0000-0000-00000000000a', '10000000-0000-0000-0000-00000000000a', 'n', 'h', 'm', 1, '0.1.0', 'XYZ') $$,
  '23514', null, 'a malformed data_hash is rejected');

-- 14: the password stays out of Git, so the role is created without a login.
reset role;
select is((select rolcanlogin from pg_roles where rolname = 'quantlab_backend'), false,
  'the backend role has no login until the password is set outside Git');

select * from finish();
rollback;
