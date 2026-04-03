# The Global Mobility Divide

**Course:** GRAD-E1493 Data Journalism, Hertie School, Spring 2026  
**Author:** Chirag Ramesh      
**Date:** March 2026

---

## What this is

An interactive data journalism piece examining how visa-free travel rights diverged between 1969 and 2010 — with OECD nations gaining dramatically while African countries largely stagnated or declined. The piece argues that the modern visa system is the direct institutional heir of the colonial order, functioning as a tool of "remote control" that filters movement along lines of nationality, race, and economic status.

The story is built on appendix data from Mau et al. (2015), the first systematic empirical study of the global mobility divide.

## View the article

👉 To view the full interactive piece, download `article_short_vf.html` from this repository and open it in your web browser on your computer.

## Repository structure

```
├── article_short_vf.html        # Final self-contained interactive article
├── process_visa_data.py         # Python script: data processing pipeline
├── data/
│   ├── Visa_Network_Data_1969_2010.xls   # Source data: Mau et al. (2015) appendix
│   └── worldUltra-pixel-map.html         # Hex coordinates: amCharts Pixel Map export
└── README.md
```

## How to reproduce

1. Install dependencies:
   ```bash
   pip install xlrd pandas beautifulsoup4
   ```

2. Run the processing script:
   ```bash
   python process_visa_data.py
   ```
   This reads the XLS and hex coordinate files, merges them by ISO3 country code, and outputs `data/visa_data.json` with visa-free counts and Equal Earth hex coordinates for 164 countries.

3. The final article (`article_short_vf.html`) embeds this data inline as a JavaScript constant — it is fully self-contained and requires no server to run.

## Technical stack

- **Data processing:** Python (`xlrd`, `pandas`, `beautifulsoup4`)
- **Hex coordinates:** [amCharts Pixel Map Generator](https://pixelmap.amcharts.com/) — Equal Earth projection, World Ultra, 8px hexagon
- **Visualisation:** Pure HTML5 Canvas 2D API (no external JS libraries)
- **Projection:** Equal Earth (geoEqualEarth), isometric 3D extrusion
- **Rendering:** Painter's algorithm, boundary-only edge detection via neighbour map

## Data source

Mau, S., Gülzau, F., Laube, L., & Zaun, N. (2015). The Global Mobility Divide: How Visa Policies Have Evolved over Time. *Journal of Ethnic and Migration Studies, 41*(8).

**Raw data download:** [Visa Network Data — University of Bonn, Institute for Political Science and Sociology](https://www.fiw.uni-bonn.de/de/forschung/demokratieforschung/team/dr-lena-laube/visa-network-data)

Appendix values used directly — 164 countries, visa-free destination counts for 1969 and 2010.

## Key findings

- OECD countries gained an average of **+27** visa-free destinations between 1969 and 2010
- African citizens saw their mobility rights **decrease** over the same period
- An African citizen is **30× more likely** to be rejected for a Schengen visa than an Asia-Pacific citizen
- African applicants lost an estimated **$67.5 million** in non-refundable Schengen visa fees in 2024 alone
