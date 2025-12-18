# 🌬️ Melbourne Air Quality Pedestrian Traffic Analysis

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Vercel](https://vercelbadge.vercel.app/api/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis)
![Tests](https://github.com/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/github/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis/graph/badge.svg?token=8IC644IYWG)](https://codecov.io/github/archeltaneka/melbourne-air-quality-pedestrian-traffic-analysis)

## 📚 Introduction

Urban air quality has a direct but often overlooked impact on how people interact with city spaces. In dense metropolitan areas like Melbourne, fluctuations in air pollution levels can influence pedestrian movement patterns, public health outcomes, and urban livability.

This project analyzes the relationship between air quality indicators and pedestrian traffic across Melbourne by combining environmental monitoring data with high-resolution pedestrian count data. By aligning temporal and spatial signals from both datasets, the analysis uncovers seasonal patterns, correlations between pollutant concentrations and foot traffic, and periods of elevated public exposure risk. The resulting interactive dashboard enables users to explore these dynamics across multiple time scales, from hourly trends to long-term seasonal shifts.

> The project actually originated from a course unit in the Master of Data Science program at Monash University (FIT5147 – Data Exploration and Visualization), and was subsequently extended with a production-grade data pipeline, automated testing, CI/CD integration, and cloud deployment.

🔗 Old Live App: [https://archeltaneka.github.io/portfolio-air-quality-visualization/old/dvp.html](https://archeltaneka.github.io/portfolio-air-quality-visualization/old/dvp.html)

🔗 New Live App: [https://melbourne-air-quality-pedestrian-tr.vercel.app/](https://melbourne-air-quality-pedestrian-tr.vercel.app/)

📂 Dataset: 

- [Air Quality Data: Environment Protection Authority (EPA) 2022](https://apps.epa.vic.gov.au/datavic/Data_Vic/AirWatch/2022_All_sites_air_quality_hourly_avg_AIR-I-F-V-VH-O-S1-DB-M2-4-0.xlsx)
- [Pedestrian Traffic Data: City of Melbourne 2022](https://www.pedestrian.melbourne.vic.gov.au/datadownload/January_2022.csv)

## 🚀 Highlights

- Cleaned and processed ~765k worth of air quality and ~8.7k worth of pedestrian traffic data on 80+ different areas around Melbourne using a custom wrangling pipeline.
- Flexible data aggregation on different temporal granularities: monthly, daily, and hourly.
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

### 🧠 Data Processing

- Automated data pipeline from download to analysis-ready datasets
- Feature extraction, cleaning, and transformations
- Consistent schema transformations

### 🔄 Data Processing Pipeline Overview

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
- The frontend is deployed via Vercel and automatically updated after successful CI checks.

## 🛠️ Tech Stack

- Python
- HTML
- CSS
- JavaScript
- D3.js
- Vercel

## 📃 Requirements
- Python 3.10+
- [Live Server](https://github.com/ritwickdey/vscode-live-server-plus-plus) (or similar tools)

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
This will download the raw data, process it, and save the preprocessed datasets in the `web/data` directory, which will be consumed by the frontend web app.

3. Run the web app `web/index.html` by using live server or similar tools


## 🗂 Project Structure

```
melbourne-air-quality-pedestrian-traffic-analysis/
├── README.md
├── data.py                     # data pipeline
├── data    
│   ├── air_quality             # raw air quality dataset
│   ├── pedestrian              # raw pedestrian dataset
├── requirements.txt
├── src
│   ├── air_quality.py          # air quality data processing
│   ├── area_mapping.py         # area mapping
│   ├── downloader.py           # data downloader
│   ├── pedestrian_count.py     # pedestrian count data processing
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── test_air_quality.py
    ├── test_area_mapping.py
    ├── test_downloader.py
    ├── test_pedestrian_count.py
```

## 🖼️ Visualization Preview

<img width="800" height="800" alt="image" src="https://github.com/user-attachments/assets/1c9f05e8-9975-4ebd-9aef-24427aaf9a4c" />

<img width="800" height="800" alt="image" src="https://github.com/user-attachments/assets/5b90c42d-2e10-4183-9303-0804d2e67e3d" />

<img width="800" height="800" alt="image" src="https://github.com/user-attachments/assets/a5be3ed5-4ecf-4086-a2b9-0b4e139bd668" />

## ⚠️ Limitations

- Analysis identifies correlation, not causation.
- Only take air pollutants into account, weather variables (rain, temperature, etc.) are not modeled.
- Pedestrian counters may not capture total foot traffic.
- When the raw datasets have different schemas, the data pipeline will fail.

## 🔮 Future Improvements

- Integrate weather data (temperature, rainfall, etc.)
- Add spatial clustering of high-risk zones
- Support multi-year trend comparisons

## 📄 License

MIT License © 2025 Archel Taneka

## ⚙️ Want to contribute?

PRs, suggestions, and issues are welcome.


