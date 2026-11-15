Arsonists: Harmonized MODIS and VIIRS Burning-Activity Calendar for Spain
NASA Space Apps Challenge 2026, challenge: Harmonization of MODIS and VIIRS Hot Spots

Live app: https://arsonists-project-k64ztgf77tm6wh4gps3bvx.streamlit.app/

A harmonized fire-activity series for Spain (November 2000 to December 2025) that combines the long MODIS record with the finer-resolution VIIRS record, so that patterns, trends and anomalies can be read without worrying about which satellite saw them. A web app lets users pick a province and a date range, explore the fire calendar, and download the results.

The problem
When VIIRS (375 m) arrived in 2012, it detected far more fire pixels than MODIS (1 km). Counting raw hotspots makes it look as if fire activity jumped in 2012, when only the sensor changed. In Spain, Suomi NPP VIIRS saw about 3.9 times as many burning 1 km squares as Aqua MODIS over the overlap years, and that ratio was not constant (it ranged from 2.7 to 6.0 across months of the year).

What we built
A harmonization pipeline (Python notebooks) that cleans MODIS and VIIRS detections from NASA FIRMS and converts them into one consistent series.
A Streamlit web app that reads the harmonized data and gives emergency managers a view of fire history: which periods of the year burn most, which years stood out, and how a given year compares with the past.
Web app features
Select a province from a dropdown or by clicking the map, and choose a date range
Monthly calendar heatmap (years by months) and a daily calendar for a single year, with a sequential colour ramp
Harmonized series plotted against the raw Terra, Aqua and VIIRS series, so the effect of the harmonization is visible
"This year vs. the usual": any year compared with the historical monthly average
Map of individual hotspot detections, with an option to exclude the La Palma volcano and static industrial sources
CSV download of harmonized daily counts for the selected region and dates
CSV download of the matching individual hotspot detections
An "About the data" page describing the method and its limits
How the harmonization works
Data: NASA FIRMS archive downloads for Spain: MODIS C6.1 (Terra and Aqua, from Nov 2000), Suomi NPP VIIRS C2 (from Jan 2012) and NOAA-20 VIIRS C2 (from Apr 2018).

1. Cleaning. Duplicates and invalid values removed. Only presumed vegetation fires kept (type == 0). Low-confidence detections dropped, using a separate rule for each sensor (MODIS confidence 30 or higher; VIIRS nominal or high). The confidence scales are used only for this filter and are never compared between sensors. Each detection is assigned to one of Spain's 52 provinces.

Sensor	Rows before	Rows after	Removed
MODIS (Terra + Aqua)	104,608	100,225	4.2%
VIIRS NOAA-20	107,399	101,150	5.8%
VIIRS Suomi NPP	175,652	165,630	5.7%
2. Flagging non-vegetation heat sources. These are flagged (not deleted), so the app can show or hide them.

La Palma volcanic eruption: 30,263 detections inside a box around Cumbre Vieja between 19 Sep 2021 and 30 Jun 2022.
Static sources (industry): 3,908 detections in 1 km squares with detections in 15 or more different years.
This leaves 332,834 usable detections for harmonization.

3. Counting square-days instead of points. Each point is placed on a ~1 km grid, and we count the unique squares with at least one detection per day. This reduces the resolution effect: VIIRS produces about 1.8 points per square-day against 1.1 for MODIS. All counts in the app are burning square-days, not raw hotspots.

4. Matching VIIRS to MODIS. Counting squares was not enough on its own (Suomi VIIRS still saw ~3.9x more than Aqua). VIIRS also detects many small, low-intensity fires that MODIS misses. Keeping only VIIRS detections with fire radiative power of 6 MW or more stabilized the relationship (monthly correlation with Aqua 0.992). We tested alternatives first and rejected them: a single ratio, a log-log curve (about 14% yearly error) and a per-season curve (about 15%), which compressed the extreme years.

5. Scaling to Aqua-equivalent counts.

VIIRS (FRP of 6 or more) multiplied by about 0.72
Terra multiplied by about 0.915
NOAA-20 tracks Suomi NPP closely (ratio 1.03, correlation 0.997) and is used as a cross-check
6. One series, with the source on every row.

Period	Source used	source value
Nov 2000 to Jul 2002	Terra, scaled	Terra_scaled
Aug 2002 to Dec 2011	Aqua	Aqua
Jan 2012 to Dec 2025	Suomi NPP VIIRS (FRP 6+), scaled	VIIRS_scaled
Validation. Hiding one year at a time and predicting it from the others, the typical yearly error was about 7.3% for VIIRS to Aqua and about 8.8% for Terra to Aqua. The weakest years were 2012 and 2024.

Data files
Files in data/ (the raw FIRMS downloads are not included because of their size):

File	Contents	Used for
harmonized_daily_by_province.parquet	One row per province per day: raw Terra, Aqua and VIIRS counts, count_harmonized, source	Date-range selection, daily calendar, daily CSV
harmonized_monthly_by_province.parquet	Same, one row per province per month	Monthly heatmap, year comparison
clean_hotspots.parquet	Individual detections with date, lat/lon, FRP, sensor, province, volcanic and static_source flags	Hotspot map and hotspot CSV
spain_provinces.gpkg	Province boundaries (Natural Earth, 52 provinces)	Map and province selection
data_quality_summary.csv	Row counts at each cleaning step	"About the data" page
Important: the harmonized files count burning square-days after filtering and scaling. The hotspot file contains raw detections. Their totals will not match, and the app explains why.

Getting the raw data
Request Spain (CSV) on the FIRMS archive download page for MODIS, Suomi NPP VIIRS (375 m) and NOAA-20 VIIRS (375 m). Do one request per sensor with a valid start date for that sensor.
Put each sensor's files in its own folder under raw/.
A FIRMS MAP_KEY is only needed for the API (small samples, recent data). Never commit your key.
Repository structure
Arsonists-Project/
├── app/                 # Streamlit web app
├── notebooks/           # cleaning and harmonization notebooks, in run order
├── data/                # processed outputs (table above)
├── requirements.txt
└── README.md
Running it
The app locally

pip install -r requirements.txt
streamlit run app/streamlit_app.py
Reproducing the data: run the notebooks in notebooks/ in order (cleaning, then harmonization). They were developed in Google Colab with the raw FIRMS files and the province boundary in a shared Google Drive folder.

Tools
Python, pandas, NumPy, GeoPandas, pyarrow (Parquet), Google Colab, NASA FIRMS, Natural Earth, Streamlit, Plotly.

Limitations
Counts are burning square-days, not raw hotspots.
The FRP cut-off was chosen on the MODIS and VIIRS overlap years, so the validation is slightly optimistic.
The Terra scaling is measured from 2003 to 2025 and assumed to hold for 2000 to 2002, when Aqua did not exist.
Satellite orbits have drifted over the years, which can change overpass times.
Daily counts are noisier than monthly ones. The scaling factors were measured on monthly totals.
2000 and 2002 are partial years.
The data ends in December 2025.
The static-source filter works on 1 km squares, so a large site can spill into neighbouring squares with fewer years of detections.
Extending it
Run the same pipeline for other countries or regions (the method takes any region's cleaned FIRMS data)
Add 2026 and near-real-time data through the FIRMS API
Refine the static-source detection
Team (Arsonists)
Malak Wahba: data cleaning and harmonization, web app support
Salma Salah: data cleaning and harmonization
Maya El Naggar: web app development
Mai Wasseem: web app development
Acknowledgements
Fire data from NASA FIRMS (MODIS and VIIRS active fire products). Province boundaries from Natural Earth. Built for the NASA Space Apps Challenge 2026.

License
Code released under the MIT License. NASA FIRMS data is openly available; please acknowledge FIRMS when reusing it.
