# 🌬️ Melbourne Air Quality Pedestrian Traffic Analysis

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Vercel](https://vercelbadge.vercel.app/api/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis)
![Tests](https://github.com/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/github/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis/graph/badge.svg?token=8IC644IYWG)](https://codecov.io/github/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis)

## 📑 Table of Contents
- [Introduction](#-introduction)
- [Dataset](#-dataset)
    - [Data Sources](#-data-sources)
    - [Dataset Statistics](#-dataset-statistics)
- [Quick Start](#-quick-start)
    - [Option 1: View Live Visualization](#-option-1-view-live-visualization)
    - [Option 2: Run Locally](#-option-2-run-locally)
- [Highlights](#-highlights)
- [Key Features](#️-key-features)
    - [Filters](#-filters)
    - [Visual Insights](#-visual-insights)
    - [Data Processing Pipeline](#-data-processing-pipeline)
    - [Testing & CI](#-testing--ci)
    - [Intended Users](#-intended-users)
- [Tech Stack](#️-tech-stack)
- [Requirements](#-requirements)
- [How to Use](#-how-to-use)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Visualization](#️-visualization-preview)
- [Limitations](#️-limitations)
- [Future Improvements](#️-future-improvements)
- [Contributing](#️-want-to-contribute)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

## 📚 Introduction

Urban air quality has a direct impact on how people interact with city spaces. In dense metropolitan areas like Melbourne, fluctuations in air pollution levels can influence pedestrian movement patterns, public health outcomes, and urban livability.

This project analyzes the relationship between **air quality indicators** and **pedestrian traffic** across Melbourne by combining:
- 🌡️ Environmental monitoring data (765k+ records)
- 🚶 High-resolution pedestrian count data (8.7k+ records across 80+ locations)

The resulting **interactive dashboard** enables users to explore these dynamics across multiple time scales, from hourly trends to long-term seasonal shifts.

> 🎓 This project originated from one of my Master's unit, FIT5147 (Data Exploration and Visualization) at Monash University and and I extended it with production-grade infrastructure, including automated testing, CI/CD, and cloud deployment.

🔗 Old Live App: [https://archeltaneka.github.io/portfolio-air-quality-visualization/old/dvp.html](https://archeltaneka.github.io/portfolio-air-quality-visualization/old/dvp.html)

🔗 New Live App: [https://melbourne-air-quality-pedestrian-tr.vercel.app/](https://melbourne-air-quality-pedestrian-tr.vercel.app/)

## 📂 Dataset

### 📊 Data Sources
- [Air Quality Data: Environment Protection Authority (EPA) 2022](https://apps.epa.vic.gov.au/datavic/Data_Vic/AirWatch/2022_All_sites_air_quality_hourly_avg_AIR-I-F-V-VH-O-S1-DB-M2-4-0.xlsx)
- [Pedestrian Traffic Data: City of Melbourne 2022](https://www.pedestrian.melbourne.vic.gov.au/datadownload/January_2022.csv)

### 📈 Dataset Statistics
| Metric | Value |
|--------|-------|
| Air Quality Records | ~765,000 |
| Pedestrian Observations | ~8,700 |
| Monitored Locations | 80+ areas |
| Temporal Coverage | Full year 2022 |
| Temporal Resolution | Hourly |
| Pollutants Tracked | 5 (CO, NO₂, O₃, PM2.5, PM10) |
| Processing Time | ~2 minutes |

## ⚡ Quick Start

### Option 1: View Live Visualization
Visit the deployed web application: [melbourne-air-quality-pedestrian-tr.vercel.app](https://melbourne-air-quality-pedestrian-tr.vercel.app/)

### Option 2: Run Locally
```bash
# Clone and navigate
git clone https://github.com/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis
cd melbourne-air-quality-pedestrian-traffic-analysis

# Install dependencies
pip install -r requirements.txt

# Run data pipeline (downloads & processes data)
python data.py

# Start web server
cd web
python -m http.server 8000
# Open http://localhost:8000 in your browser
```

## 🚀 Highlights

- Cleaned and processed ~765k worth of air quality and ~8.7k worth of pedestrian traffic data on 80+ different areas around Melbourne using a custom wrangling pipeline.
- Enabled multi-scale analysis (hourly → seasonal) without recomputing raw datasets.
- Created an interactive visualization to explore seasonal trends in air quality, particularly harmful pollutants.
- Added automated tests + GitHub Actions CI + coverage reporting.
- Fully deployed to Vercel.

## 🖥️ Key Features

### 🔍 Filters

Explore the dataset on a more granular level:
- Monthly
- Daily
- Hourly

### 📊 Visual Insights

Includes:
- Pollutant levels
- Pedestrian counts
- Correlation between pollutants and pedestrian counts

### 🔄 Data Processing Pipeline

1. Download air quality and pedestrian activity raw data from the EPA Victoria and City of Melbourne official websites.
2. Data is preprocessed (cleaned, standardized, and aligned temporally).
3. Area names are normalized and mapped for geocoding.
4. Aggregated datasets are generated for visualization.
5. Frontend consumes preprocessed outputs for interactive exploration.

### 🧪 Testing & CI

- Unit tests for all data-processing functions
    - Validates datetime parsing and alignment
    - Ensures consistent area name normalization
    - Verifies null handling and aggregation logic
    - Prevents schema regressions via unit tests
- Pytest + Coverage
- GitHub Actions automated workflow
- Codecov integration
- All deployments are gated by CI. The frontend is only deployed if all unit tests pass.

### 👥 Intended Users

- Urban planners and policymakers
- Public health researchers
- Data scientists exploring spatio-temporal environmental data

## 🛠️ Tech Stack

- Python
- HTML
- CSS
- JavaScript
- D3.js
- Vercel

## 📃 Requirements
- Python 3.10+
- A local web server (e.g., `python -m http.server` or [VS Code Live Server](https://github.com/ritwickdey/vscode-live-server-plus-plus))

## 📦 How To Use

1. Clone the repo and install necessary dependencies
```
git clone https://github.com/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis
cd melbourne-air-quality-pedestrian-traffic-analysis
pip install -r requirements.txt
```

2. Run the data pipeline
```
python ./data.py
```
This will:
- Download raw data from EPA Victoria and City of Melbourne
- Clean and process ~765k air quality records
- Process ~8.7k pedestrian count records
- Generate analysis-ready datasets in `web/data/`
- Takes approximately 1-2  minutes on first run

3. Run the web app `web/index.html` by using live server or similar tools

4. Running tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_air_quality.py -v

# View coverage report
open htmlcov/index.html
```

**Test Coverage:**
- ✅ Data downloaders
- ✅ Air quality processing
- ✅ Pedestrian count processing
- ✅ Area mapping & geocoding
- ✅ Data pipeline integration

## 🏗️ Architecture

The diagram below shows the end-to-end data flow from raw ingestion to deployed visualization.

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                             │
├─────────────────────────────────────────────────────────────┤
│  EPA Victoria API          City of Melbourne API            │
│  (Air Quality)             (Pedestrian Counts)              │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
               ▼                      ▼
         ┌──────────────────────────────────┐
         │     Data Download Layer          │
         │     (downloader.py)              │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │   Data Processing Pipeline       │
         ├──────────────────────────────────┤
         │  • air_quality.py (cleaning)     │
         │  • pedestrian_count.py (agg)     │
         │  • area_mapping.py (geocoding)   │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │    Processed Datasets            │
         │    (JSON/CSV in web/data/)       │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │   Interactive Dashboard          │
         │   (D3.js + HTML/CSS/JS)          │
         │   Deployed on Vercel             │
         └──────────────────────────────────┘
```

## 🗂 Project Structure
```
melbourne-air-quality-pedestrian-traffic-analysis/
├── README.md
├── requirements.txt             # Python dependencies
├── data.py                      # Main data pipeline orchestrator
│
├── data/                           # Raw & processed data
│   ├── air_quality/                # EPA Victoria air quality data
│   ├── pedestrian/                 # City of Melbourne pedestrian counts
│   ├── area_mapping/               # Geocoded location mappings
│   └── processed/                  # Final analysis-ready datasets
│
├── src/                            # Source code modules
│   ├── __init__.py
│   ├── downloader.py               # Download raw data from APIs
│   ├── air_quality.py              # Clean & aggregate air quality data
│   ├── pedestrian_count.py         # Process pedestrian count data
│   └── area_mapping.py             # Geocode areas using Nominatim
│
├── tests/                          # Unit & integration tests
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_downloader.py          # Test data downloads
│   ├── test_air_quality.py         # Test air quality processing
│   ├── test_pedestrian_count.py    # Test pedestrian data processing
│   └── test_area_mapping.py        # Test geocoding logic
│
├── web/                            # Frontend application
│   ├── index.html                  # Main dashboard page
│   ├── css/                        # Stylesheets
│   │   └── main.css
│   ├── js/                         # D3.js visualizations
│   │   └── main.js
│   └── data/                       # Preprocessed CSV files for visualization
│
└── .github/
    └── workflows/
        └── tests.yml               # CI/CD pipeline
```

## 🖼️ Visualization Preview

<img width="800" height="800" alt="image" src="https://github.com/user-attachments/assets/1c9f05e8-9975-4ebd-9aef-24427aaf9a4c" />

<img width="800" height="800" alt="image" src="https://github.com/user-attachments/assets/5b90c42d-2e10-4183-9303-0804d2e67e3d" />

<img width="800" height="800" alt="image" src="https://github.com/user-attachments/assets/a5be3ed5-4ecf-4086-a2b9-0b4e139bd668" />

## ⚠️ Limitations

- Analysis identifies correlation, not causation.
- Only take air pollutants into account, weather variables (rain, temperature, etc.) are not modeled.
- Pedestrian counters may not capture total foot traffic.
- The pipeline assumes stable source schemas. Structural changes in upstream datasets would require updates to the ingestion layer.

## 🔮 Future Improvements

- Integrate weather data (temperature, rainfall, etc.)
- Support multi-year trend comparisons
- Add spatial clustering of high-risk zones

## 🤝 Contributing

All forms of contributions are welcome!

## 📄 License

MIT License © 2025 Archel Taneka

## 🙏 Acknowledgments

- **Data Sources**:
  - [Environment Protection Authority Victoria](https://www.epa.vic.gov.au/)
  - [City of Melbourne Open Data](https://data.melbourne.vic.gov.au/)
- **Course**: FIT5147 – Data Exploration and Visualization, Monash University
- **Geocoding**: [Nominatim](https://nominatim.org/) (OpenStreetMap)
- **Visualization**: [D3.js](https://d3js.org/), [Leaflet.js](https://leafletjs.com/)
- **Deployment**: [Vercel](https://vercel.com/)

