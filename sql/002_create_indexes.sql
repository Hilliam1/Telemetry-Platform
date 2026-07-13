CREATE INDEX IF NOT EXISTS idx_log_events_source_type ON log_events(source_type);
CREATE INDEX IF NOT EXISTS idx_log_events_provider ON log_events(provider_name);
CREATE INDEX IF NOT EXISTS idx_log_events_event_id ON log_events(event_id);
CREATE INDEX IF NOT EXISTS idx_log_events_event_record_id ON log_events(event_record_id);
CREATE INDEX IF NOT EXISTS idx_log_events_time_created ON log_events(time_created);
CREATE INDEX IF NOT EXISTS idx_log_events_inserted_at ON log_events(inserted_at);

CREATE INDEX IF NOT EXISTS idx_host_metrics_host ON host_metrics(host_name);
CREATE INDEX IF NOT EXISTS idx_host_metrics_collected_at ON host_metrics(collected_at);

CREATE INDEX IF NOT EXISTS idx_process_events_image ON process_events(image);
CREATE INDEX IF NOT EXISTS idx_process_events_user ON process_events(user_name);
CREATE INDEX IF NOT EXISTS idx_process_events_created_at ON process_events(created_at);

CREATE INDEX IF NOT EXISTS idx_collector_runs_host ON collector_runs(source_host);
CREATE INDEX IF NOT EXISTS idx_collector_runs_started_at ON collector_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_collector_runs_status ON collector_runs(status);

