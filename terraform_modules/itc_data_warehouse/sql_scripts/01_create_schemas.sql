-- Create the "raw" schema
CREATE SCHEMA IF NOT EXISTS raw AUTHORIZATION postgres;

-- Create the "curated" schema
CREATE SCHEMA IF NOT EXISTS curated AUTHORIZATION postgres;

-- Create the "analytics" schema
CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION postgres;