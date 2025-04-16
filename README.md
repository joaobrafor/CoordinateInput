# CoordinateInput

A versatile QGIS plugin for generating point, line and polygon layers from user‑provided coordinates in UTM, Decimal Degrees or DMS formats.

## Features
- Accepts **UTM**, **decimal degrees** (e.g., `-55.7568`) and **DMS** (e.g., `15:50:50.000S`) inputs.
- Builds **point, line or polygon** geometries and groups vertices by *Feature ID*.
- **Import / export** coordinate tables via semicolon‑separated text (`.txt`) files.
- **Import vertices** directly from existing point, line or polygon layers.
- Automatic **CRS transformation** to the current project CRS (WGS 84 support by default).
- Handles optional **altitude (Z)**, **vertex names** and **boundary labels**.
- Interactive table tools: add, delete, reorder rows; auto‑detect and retain decimal precision.
- Outputs to **temporary layers**, **Shapefiles** or **GeoPackages**.

## Requirements
- QGIS 3.0 or later

## Installation
1. Download or clone this repository.
2. Copy the `CoordinateInput` folder to your QGIS plugins directory  
   (e.g., `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins` on Linux).
3. Restart QGIS and enable the plugin under **Plugins › Manage and Install Plugins**.

## Quick Usage
1. Open **Coordinate Input** from the toolbar or **Plugins** menu.
2. Enter coordinates manually or **import** them from a `.txt` file (semicolon‑separated).
3. Choose the desired geometry type (Point, Line, Polygon) and set an output file if needed.
4. Click **Process** to create the layer; it will be added automatically to the project.

## Support and Issues
- [Project Homepage](https://github.com/joaobrafor/CoordinateInput)
- [Issue Tracker](https://github.com/joaobrafor/CoordinateInput/issues)

## Author
- **João Ubaldo** – [joao@brafor.com.br](mailto:joao@brafor.com.br)

---

Licensed under the **MIT License**.
