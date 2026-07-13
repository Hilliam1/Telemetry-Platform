CREATE TABLE IF NOT EXISTS log_events (
    id SERIAL PRIMARY KEY,
    source_host TEXT,
    source_type TEXT,
    provider_name TEXT,
    event_id BIGINT,
    event_record_id BIGINT,
    severity TEXT,
    time_created TIMESTAMP,
    message TEXT,
    raw_data TEXT,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS host_metrics (
    id SERIAL PRIMARY KEY,
    host_name TEXT,
    cpu_percent NUMERIC,
    memory_percent NUMERIC,
    disk_percent NUMERIC,
    boot_time TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS process_events (
    id SERIAL PRIMARY KEY,
    source_host TEXT,
    process_guid TEXT,
    process_id BIGINT,
    image TEXT,
    command_line TEXT,
    parent_image TEXT,
    parent_command_line TEXT,
    user_name TEXT,
    sha256 TEXT,
    created_at TIMESTAMP,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collector_runs (
    id SERIAL PRIMARY KEY,
    source_host TEXT,
    status TEXT,
    events_inserted INT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

