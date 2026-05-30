import ee

ee.Initialize()

def analizar_parcela(poligono: list) -> dict:
    coords = [[p[1], p[0]] for p in poligono]
    region = ee.Geometry.Polygon(coords)

    sentinel = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(region)
        .filterDate('2024-09-01', '2024-12-01')
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .median())

    ndvi = sentinel.normalizedDifference(['B8', 'B4'])
    ndvi_valor = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=10
    ).getInfo().get('nd', 0)

    fuego = (ee.ImageCollection('MODIS/061/MOD14A1')
        .filterBounds(region)
        .filterDate('2024-01-01', '2024-12-31')
        .select('FireMask'))

    max_fire = fuego.max().reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=region,
        scale=500
    ).getInfo().get('FireMask', 0)

    zona_quemada = max_fire >= 7

    lst = (ee.ImageCollection('MODIS/061/MOD11A1')
        .filterBounds(region)
        .filterDate('2024-10-01', '2024-12-31')
        .select('LST_Day_1km')
        .mean())

    temp_k = lst.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000
    ).getInfo().get('LST_Day_1km', 0)

    temp_c = round((temp_k * 0.02) - 273.15, 1) if temp_k else 38.0

    return {
        "ndvi": round(float(ndvi_valor or 0), 3),
        "zona_quemada": bool(zona_quemada),
        "temp_suelo_c": temp_c
    }
