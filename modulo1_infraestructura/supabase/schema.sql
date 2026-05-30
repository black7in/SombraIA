-- Activar extensión geoespacial
CREATE EXTENSION IF NOT EXISTS postgis;

-- Tabla de parcelas con geometría
CREATE TABLE parcelas_geo (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  firestore_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  geom GEOMETRY(POLYGON, 4326) NOT NULL,
  area_ha FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice espacial para queries rápidas
CREATE INDEX parcelas_geo_geom_idx ON parcelas_geo USING GIST(geom);

-- Función: parcelas dentro de radio (km) de un punto
CREATE OR REPLACE FUNCTION parcelas_cercanas(
  lat FLOAT, lng FLOAT, radio_km FLOAT
)
RETURNS TABLE(firestore_id TEXT, distancia_m FLOAT) AS $$
  SELECT
    firestore_id,
    ST_Distance(
      geom::geography,
      ST_Point(lng, lat)::geography
    ) AS distancia_m
  FROM parcelas_geo
  WHERE ST_DWithin(
    geom::geography,
    ST_Point(lng, lat)::geography,
    radio_km * 1000
  )
  ORDER BY distancia_m;
$$ LANGUAGE sql;
