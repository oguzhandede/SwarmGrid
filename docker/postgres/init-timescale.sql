-- TimescaleDB initialization for SwarmGrid
-- This script creates hypertables for time-series data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Note: The Telemetries table is created by EF Core migrations.
-- After the table is created, run the following to convert it to a hypertable:
-- 
-- SELECT create_hypertable('Telemetries', 'Timestamp', 
--     chunk_time_interval => INTERVAL '1 day',
--     if_not_exists => TRUE
-- );
--
-- To compress older data:
-- ALTER TABLE Telemetries SET (
--     timescaledb.compress,
--     timescaledb.compress_segmentby = 'ZoneId,CameraId'
-- );
-- SELECT add_compression_policy('Telemetries', INTERVAL '7 days');
--
-- For retention (optional - deletes old data):
-- SELECT add_retention_policy('Telemetries', INTERVAL '90 days');

-- Function to enable hypertable on Telemetries after EF migration
CREATE OR REPLACE FUNCTION enable_telemetry_hypertable()
RETURNS void AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'Telemetries' AND table_schema = 'public'
    ) THEN
        PERFORM create_hypertable('"Telemetries"', 'Timestamp', 
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
        RAISE NOTICE 'Telemetries hypertable created/verified';
    ELSE
        RAISE NOTICE 'Telemetries table not found yet - run EF migrations first';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- This will be called after EF migrations run
-- SELECT enable_telemetry_hypertable();
