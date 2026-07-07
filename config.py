import os

# Defines the server configuration

APP_CONFIG = {
    'CACHE_DIR': os.path.relpath('./cache'),
    'CACHE_FILES': True,
    'CACHE_MAX_BYTES': int(os.environ.get('CACHE_MAX_BYTES', 10 * 1024 ** 3)),  # 10 GB
    'CACHE_TTL_HOURS': int(os.environ.get('CACHE_TTL_HOURS', 0)),
    'CACHE_TARGET_RATIO': float(os.environ.get('CACHE_TARGET_RATIO', 0.85)),
    'AVAILABLE_FORMATS': {
        "json": "application/json",
        "png": "image/png",
        "tiff": "image/tiff"
    },
    'DEFAULT_FORMAT': "application/json"
}

# Catalog of supported HRRR products. One row per product holds both the wgrib2
# `search` selector used to fetch it and the colormap/label the PNG renderer
# draws it with, so the valid-product set, its GRIB selector and its rendering
# can't drift out of sync. parse.py validates against the keys; process_data.py
# reads ['search'] to fetch and ['cmap']/['label'] to render.
HRRR_PRODUCTS = {
    'wind_u':        {'search': ':[U|V]GRD:10 m',             'cmap': 'RdBu_r',   'label': 'Wind U Component (m/s)'},
    'wind_v':        {'search': ':[U|V]GRD:10 m',             'cmap': 'RdBu_r',   'label': 'Wind V Component (m/s)'},
    'wind_speed':    {'search': ':[U|V]GRD:10 m',             'cmap': 'viridis',  'label': 'Wind Speed (m/s)'},
    'wind_vector':   {'search': ':[U|V]GRD:10 m',             'cmap': 'viridis',  'label': 'Wind (u/v m/s)'},
    'temp_2m':       {'search': ':TMP:2 m above ground:',     'cmap': 'RdYlBu_r', 'label': 'Temperature (K)'},
    'pbl_height':    {'search': ':HPBL:surface:',             'cmap': 'plasma',   'label': 'PBL Height (m)'},
    'smoke_massden': {'search': ':MASSDEN:8 m above ground:', 'cmap': 'YlOrRd',   'label': 'Smoke Mass Density (µg/m³)', 'scale': 1e9, 'vmin': 0, 'vmax': 250},
    'precip_rate':   {'search': ':PRATE:surface:',            'cmap': 'Blues',    'label': 'Precip Rate (kg/m²/s)'},
    'rh_2m':         {'search': ':RH:2 m above ground:',      'cmap': 'YlGnBu',   'label': 'Relative Humidity (%)'},
    'wind_gust':     {'search': ':GUST:surface:',             'cmap': 'viridis',  'label': 'Wind Gust (m/s)'},
    'dewpoint_2m':   {'search': ':DPT:2 m above ground:',     'cmap': 'RdYlBu_r', 'label': 'Dewpoint (K)'},
}

# 10 m wind products (all from the same U/V GRIB); grouped for the shared handling
# scalars don't need: earth-relative rotation at regrid + band derivation in convert.
WIND_PRODUCTS = ('wind_u', 'wind_v', 'wind_speed', 'wind_vector')

NODATA = -9999