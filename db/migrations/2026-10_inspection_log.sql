-- Migration for databases created with the earlier schema (plant-photo workflow).
-- Adds the non-photographic inspection-log columns. It deletes NOTHING: old photo_path / photo_screening /
-- symptoms columns, the farmer_images and field_validations tables and the "farmer-images" bucket stay as they are
-- (no longer written or read by the app). Remove them manually only after you have exported anything you need.
alter table field_observations add column if not exists inspection_date   date;
alter table field_observations add column if not exists condition         text;
alter table field_observations add column if not exists irrigation_issue  text;
alter table field_observations add column if not exists alt_causes        jsonb;
alter table field_observations add column if not exists soil_moisture_pct numeric;
alter table field_observations add column if not exists inspector         text;
