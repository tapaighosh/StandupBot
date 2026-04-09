-- StandupBot — Database Initialization Script
-- This runs automatically when the PostgreSQL container starts for the first time.
-- Creates the test database for running pytest.

CREATE DATABASE standupbot_test;
GRANT ALL PRIVILEGES ON DATABASE standupbot_test TO standupbot;
