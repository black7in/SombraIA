import pvlib
import pandas as pd

def calcular_horas_sol(lat: float, lng: float) -> dict:
    ubicacion = pvlib.location.Location(
        latitude=lat,
        longitude=lng,
        tz='America/La_Paz',
        altitude=400
    )

    tiempos = pd.date_range(
        start='2024-01-01',
        end='2024-12-31',
        freq='1h',
        tz='America/La_Paz'
    )

    posicion_solar = ubicacion.get_solarposition(tiempos)

    sol_directo = posicion_solar[posicion_solar['elevation'] > 10]
    horas_por_dia = len(sol_directo) / 365

    horas_criticas = sol_directo[
        (sol_directo.index.hour >= 10) &
        (sol_directo.index.hour <= 15)
    ]
    horas_criticas_dia = len(horas_criticas) / 365

    azimuth_medio = sol_directo['azimuth'].median()

    return {
        "horas_sol_dia": round(horas_por_dia, 1),
        "horas_criticas_dia": round(horas_criticas_dia, 1),
        "azimuth_medio": round(float(azimuth_medio), 1),
        "posicion_sombra_optima": _azimuth_a_posicion(azimuth_medio)
    }

def _azimuth_a_posicion(azimuth: float) -> str:
    if 45 <= azimuth < 135:
        return "norte"
    elif 135 <= azimuth < 225:
        return "este"
    elif 225 <= azimuth < 315:
        return "sur"
    else:
        return "oeste"
