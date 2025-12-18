-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Sessions table
create table public.sessions (
  session_id uuid primary key default uuid_generate_v4(),
  user_id text,
  start_time timestamp with time zone default now(),
  end_time timestamp with time zone,
  duration_seconds integer,
  summary text
);

-- Session events table
create table public.session_events (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid references public.sessions(session_id) on delete cascade,
  event_type text not null, -- 'user_message', 'assistant_message', 'tool_call', 'tool_result', 'system'
  payload jsonb not null,
  created_at timestamp with time zone default now()
);

-- Index for faster queries
create index idx_session_events_session_id on public.session_events(session_id);
