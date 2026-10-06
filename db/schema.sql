-- RAY | رَيّ – database architecture (PostgreSQL / Supabase)
-- -----------------------------------------------------------------------------------------------
-- Status in this version:
--   * ACTIVE (written by the app when Supabase is configured): field_observations, field_validations
--     (+ Storage bucket "farmer-images"). Locally the same two tables live in SQLite (src/storage.py).
--   * READY (schema only, filled later): users, farms, zones, crops, crop_growth_stages, diseases, pests,
--     disease_images, farmer_images, satellite_observations, weather_observations, iot_devices,
--     iot_observations, analysis_results, data_sources.
--   Reference data for crops/diseases/pests/images/sources currently live in data/knowledge/*.json
--   and can be loaded into these tables without changing their structure.
--
-- Apply in Supabase: SQL Editor → paste this file → Run. Then Storage → create a PRIVATE bucket "farmer-images".
-- The app uses the service key server-side only; RLS is enabled with no public policies, so anonymous
-- browser clients cannot read farmer data.
-- -----------------------------------------------------------------------------------------------

create extension if not exists "pgcrypto";

-- ---------- reference / provenance ----------
create table if not exists data_sources (
  id              text primary key,                 -- e.g. 'ucipm_stripe_rust', 'era5_land', 'sentinel2_l2a'
  title           text not null,
  publisher       text,
  url             text,
  date_retrieved  date,
  usage_license   text
);

create table if not exists crops (
  id                    text primary key,           -- 'cereals', 'fodder', 'date_palm', ...
  name_en               text not null,
  name_ar               text not null,
  crop_type             text,
  growth_period_days    text,
  water_requirement     text,                       -- as published (e.g. '450–650 mm per growing period')
  water_source_id       text references data_sources(id),
  relevant_indicators   text[],
  notes                 text
);

create table if not exists crop_growth_stages (
  id            uuid primary key default gen_random_uuid(),
  crop_id       text references crops(id) on delete cascade,
  stage_name_en text not null,
  stage_name_ar text,
  start_day     int,
  end_day       int,
  kc            numeric,                            -- crop coefficient, only when sourced
  source_id     text references data_sources(id)
);

create table if not exists diseases (
  id                text primary key,
  name_en           text not null,
  name_ar           text not null,
  scientific_name   text,
  crop_ids          text[],
  symptoms_en       text,
  symptoms_ar       text,
  visual_tags       text[],
  conditions        text,
  inspection_steps  jsonb,
  similar_ids       text[],
  source_id         text references data_sources(id),
  notes             text
);

create table if not exists pests (like diseases including all);

create table if not exists disease_images (
  id            uuid primary key default gen_random_uuid(),
  problem_id    text not null,                      -- diseases.id or pests.id
  image_url     text not null,
  source_page   text not null,
  license       text not null,
  author        text,
  date_retrieved date
);

-- ---------- people, farms, zones ----------
create table if not exists users (
  id          uuid primary key default gen_random_uuid(),
  created_at  timestamptz default now(),
  role        text check (role in ('farmer','agronomist','admin')) default 'farmer',
  display_name text                                 -- optional; no personal data is required by RAY
);

create table if not exists farms (
  id          text primary key,                     -- e.g. 'hail-27.399-42.526'
  name        text,
  owner_id    uuid references users(id),
  centre_lat  double precision,
  centre_lon  double precision,
  bbox        double precision[4],                  -- min_lon, min_lat, max_lon, max_lat
  created_at  timestamptz default now()
);

create table if not exists zones (
  farm_id   text references farms(id) on delete cascade,
  zone_id   text,                                   -- 'A1' … (grid today; pivot/field boundaries later)
  crop_id   text references crops(id),
  geometry  jsonb,                                  -- GeoJSON polygon
  primary key (farm_id, zone_id)
);

-- ---------- observations ----------
create table if not exists satellite_observations (
  id            uuid primary key default gen_random_uuid(),
  farm_id       text references farms(id),
  zone_id       text,
  sensor        text not null,                      -- 'Sentinel-2 L2A', 'Landsat 8/9 ST', 'Sentinel-1 GRD'
  acquired_on   date not null,
  ndvi numeric, ndre numeric, ndmi numeric, lst_c numeric,
  vv_db numeric, vh_db numeric,
  clear_fraction numeric, veg_fraction numeric,
  source_id     text references data_sources(id),
  created_at    timestamptz default now()
);

create table if not exists weather_observations (
  id               uuid primary key default gen_random_uuid(),
  farm_id          text references farms(id),
  observed_on      date not null,
  air_temp_c numeric, air_temp_max_c numeric, rel_humidity_pct numeric, precip_mm numeric,
  wind_speed_ms numeric, wind_dir_deg numeric,
  source           text not null,                   -- 'ERA5-Land' | 'NCM' (when licensed)
  station_id       text
);

create table if not exists iot_devices (
  id          text primary key,
  farm_id     text references farms(id),
  zone_id     text,
  kind        text,                                 -- 'soil_moisture', 'soil_temp', 'air_temp', 'humidity', 'flow_meter'
  installed_on date,
  notes       text
);

create table if not exists iot_observations (
  id          bigserial primary key,
  device_id   text references iot_devices(id),
  observed_at timestamptz not null,
  variable    text not null,
  value       numeric,
  unit        text
);

create table if not exists analysis_results (
  id              uuid primary key default gen_random_uuid(),
  farm_id         text references farms(id),
  zone_id         text,
  satellite_date  date,
  rule_class      text,                             -- HEALTHY / MODERATE / HIGH / NO_CROP / NO_DATA
  rule_score      numeric,
  rule_points     jsonb,
  anomaly_share   numeric,                          -- Isolation Forest unusual-pixel share
  thresholds      jsonb,
  model_version   text,
  created_at      timestamptz default now()
);

-- ACTIVE: written by the app (src/storage.py)
create table if not exists field_observations (
  id                 uuid primary key default gen_random_uuid(),
  created_at         timestamptz default now(),
  session_id         text,                          -- random per browser session (no personal data)
  farm_id            text,
  farm_name          text,
  data_mode          text,                          -- 'real' | 'demo'
  zone_id            text,
  crop_id            text,
  satellite_date     date,
  satellite_class    text,
  satellite_score    numeric,
  lat                double precision,              -- zone centre (not the user's GPS)
  lon                double precision,
  symptoms           jsonb,
  soil_condition     text,
  spread             text,
  photo_path         text,                          -- path in the private Storage bucket
  photo_screening    jsonb,
  possible_causes    jsonb,
  candidate_problems jsonb,
  notes              text
);

create table if not exists farmer_images (
  id              uuid primary key default gen_random_uuid(),
  observation_id  uuid references field_observations(id) on delete cascade,
  storage_path    text not null,
  exif_removed    boolean default true,
  created_at      timestamptz default now()
);

-- ACTIVE: ground truth for future calibration / supervised learning
create table if not exists field_validations (
  id                 uuid primary key default gen_random_uuid(),
  created_at         timestamptz default now(),
  session_id         text,
  observation_id     uuid references field_observations(id) on delete cascade,
  ray_prediction     text,                          -- top cause RAY suggested (e.g. 'water')
  field_check        text,                          -- e.g. 'soil_dry' | 'soil_not_dry' | 'not_checked'
  actual_cause       text,                          -- water / heat / disease / pest / nutrient / other / none
  actual_problem_id  text,                          -- diseases.id / pests.id when identified
  action_taken       text,                          -- what the farmer did (repair, irrigation change, treatment …)
  notes              text
);

create index if not exists idx_obs_session on field_observations(session_id, created_at desc);
create index if not exists idx_obs_farm_zone on field_observations(farm_id, zone_id);
create index if not exists idx_val_obs on field_validations(observation_id);
create index if not exists idx_sat_farm_date on satellite_observations(farm_id, acquired_on);
create index if not exists idx_wx_farm_date on weather_observations(farm_id, observed_on);
create index if not exists idx_iot_dev_time on iot_observations(device_id, observed_at);

-- Row Level Security: on, with no public policies (the app writes with the server-side service key).
alter table field_observations enable row level security;
alter table field_validations  enable row level security;
alter table farmer_images      enable row level security;
alter table users              enable row level security;
alter table farms              enable row level security;
alter table zones              enable row level security;
alter table iot_devices        enable row level security;
alter table iot_observations   enable row level security;
alter table analysis_results   enable row level security;
alter table satellite_observations enable row level security;
alter table weather_observations   enable row level security;
