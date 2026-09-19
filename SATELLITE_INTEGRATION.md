# 🛰️ Satellite Data Integration Roadmap

## Overview

This guide describes future work required to replace generated/estimated fields
with independently sourced USGS SRTM and Copernicus Sentinel-2 products.

> **Current status (v1.1):** GeoShield now has on-demand live remote-sensing
> adapters. SRTM elevation/slope is sampled from public AWS Open Data Skadi HGT
> tiles, and recent Sentinel-2 L2A NDVI is computed from red/NIR Cloud-Optimized
> GeoTIFF assets discovered through Element 84 Earth Search. The repository
> snapshot remains a deterministic fallback when an upstream is unavailable.
> Every response exposes provider, mode, observation age, and fallback reason.

---

## Step 1: Get Free Accounts

### USGS EarthExplorer (SRTM DEM)
1. Go to https://earthexplorer.usgs.gov/
2. Click **"Register"** at the top right
3. Fill in your details (free, no credit card)
4. Verify your email
5. **Time to register:** 3 minutes

### Copernicus Data Space (Sentinel-2 NDVI)
1. Go to https://dataspace.copernicus.eu/
2. Click **"Sign Up"**
3. Fill in your details (free, no credit card)
4. Verify your email
5. **Time to register:** 2 minutes

---

## Optional bulk workflow: Download SRTM DEM

### What is SRTM DEM?
- **30-meter resolution** elevation data for the entire Earth
- From this, we compute **real slope angle** and **aspect** for every coordinate
- This replaces our simulated terrain data

### How to Download:
1. Login to https://earthexplorer.usgs.gov/
2. **Search Criteria tab:**
   - Click **"Polygon"** under Coordinates
   - Enter NER bounding box:
     - Point 1: 21.0, 88.0
     - Point 2: 21.0, 98.0
     - Point 3: 30.0, 98.0
     - Point 4: 30.0, 88.0
   - Click **"Set"**
3. **Data Sets tab:**
   - Expand **"Digital Elevation"** → **"SRTM"**
   - Check **"SRTM 1 Arc-Second Global"**
   - Click **"Done"**
4. **Additional Criteria tab:**
   - Set Cloud Cover: 0-20%
5. **Results tab:**
   - Click **"Download Options"** for each tile
   - Select **"GeoTIFF"** format
   - Download all tiles covering NER (~10-15 tiles, ~500MB total)

### How to Integrate:
```python
import rasterio
import numpy as np

# Load DEM
with rasterio.open('srtm_ner_tile1.tif') as src:
    # Read elevation data
    elevation = src.read(1)
    
    # For each sensor station coordinates (lat, lng):
    row, col = src.index(longitude, latitude)
    station_elevation = elevation[row, col]
    
    # Compute slope from DEM using numpy gradient
    dy, dx = np.gradient(elevation)
    slope = np.arctan(np.sqrt(dx**2 + dy**2)) * (180 / np.pi)
    station_slope = slope[row, col]
```

---

## Optional bulk workflow: Download Sentinel-2 NDVI

### What is NDVI?
- **Normalized Difference Vegetation Index** — ranges from -1 to 1
- **High NDVI (>0.5)** = Dense forest = Lower landslide risk
- **Low NDVI (<0.2)** = Bare soil = Higher landslide risk
- **Resolution:** 10 meters (very detailed)

### How to Download:
1. Login to https://dataspace.copernicus.eu/
2. Click **"Explore"** tab
3. **Draw area:** NER bounding box (lat 21-30, lng 88-98)
4. **Filter:**
   - Collection: **Sentinel-2**
   - Product Type: **S2MSI2A** (Level-2A, surface reflectance)
   - Cloud Cover: < 20%
   - Date Range: Last 3 months
5. **Search results:**
   - Click on a scene → **"Preview"** to check quality
   - Click **"Download"** → Choose **"NDVI"** visualization
   - Or download raw bands B08 (NIR) and B04 (Red) to compute NDVI yourself

### How to Compute NDVI:
```python
import rasterio
import numpy as np

# Load bands
with rasterio.open('S2B_B08_10m.tif') as nir_src:
    nir = nir_src.read(1).astype(float)  # Near-Infrared

with rasterio.open('S2B_B04_10m.tif') as red_src:
    red = red_src.read(1).astype(float)  # Red

# NDVI = (NIR - Red) / (NIR + Red)
ndvi = (nir - red) / (nir + red + 1e-10)

# For each sensor station coordinates:
row, col = red_src.index(longitude, latitude)
station_ndvi = ndvi[row, col]
```

---

## Step 4: Update Training Data

Once you have real DEM and NDVI:

1. Create a script to extract values at each sensor station coordinate
2. Update the `seed_data.py` with real terrain values
3. Retrain the AI model with real features

```python
# Example: Update station data with real values
for station in stations:
    # Get real elevation and slope from DEM
    real_elevation = extract_from_dem(station.lat, station.lng, dem_file)
    real_slope = extract_slope_from_dem(station.lat, station.lng, dem_file)
    
    # Get real NDVI from Sentinel-2
    real_ndvi = extract_from_ndvi(station.lat, station.lng, ndvi_file)
    
    # Update database
    station.elevation = real_elevation
    station.slope_angle = real_slope
    station.vegetation_cover = real_ndvi * 100  # Convert to percentage
```

---

## Impact on System

| Data Source | Current (Simulated) | After Integration | Improvement |
|-------------|---------------------|-------------------|-------------|
| Slope Angle | Cached/generated fallback | Live SRTM point sampling | **LIVE INTEGRATED** |
| Elevation | Cached regional fallback | Live SRTM point sampling | **LIVE INTEGRATED** |
| Vegetation (NDVI) | Cached estimated fallback | Recent Sentinel-2 L2A point NDVI | **LIVE INTEGRATED** |
| Training Data | Mixed regional/generated prototype rows | Independently sourced and versioned terrain features | **HIGH** |

---

## Timeline

| Task | Time | Priority |
|------|------|----------|
| Confirm source licenses and coverage | Project task | HIGH |
| Download and checksum SRTM DEM | Project task | HIGH |
| Download and checksum Sentinel-2 scenes | Project task | HIGH |
| Add reproducible extraction pipeline | Project task | HIGH |
| Re-evaluate with grouped validation | Project task | HIGH |

---

## Where to Get Help

- **USGS Support:** https://earthexplorer.usgs.gov/
- **Copernicus Forum:** https://forum.dataspace.copernicus.eu/
- **NDVI Tutorial:** https://earthobservatory.nasa.gov/features/MeasuringVegetation
