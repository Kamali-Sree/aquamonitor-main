# AquaMonitor

> AI-powered water quality prediction and fish health monitoring system for aquaculture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 14+](https://img.shields.io/badge/node.js-14+-green.svg)](https://nodejs.org/)
[![TensorFlow 2.15](https://img.shields.io/badge/tensorflow-2.15-orange.svg)](https://tensorflow.org/)

## Features

- **LSTM Water Quality Prediction** — Predicts water temperature, dissolved oxygen, and pH using a trained LSTM neural network fed by real-time weather data
- **Future Forecasting** — Forecast water quality for any date/time up to 1 year ahead
- **Manual Input Analysis** — Enter parameters directly for instant LSTM-based assessment
- **Multi-Species Support** — Species-specific optimal ranges for 8 aquaculture species
- **Farm Management** — Register farms, manage pond/tank/cage locations, run batch analysis (requires PostgreSQL)
- **Data Reports** — Historical charts with CSV export
- **Predator Detection** — TensorFlow Lite YOLO model identifies aquatic predators from uploaded images
- **Disease Detection** — TensorFlow Lite YOLO model classifies fish health into 3 categories: Healthy Fish, Bacterial Infections, Fungal/Parasitic Diseases

## Supported Species

| Species | Temperature (°C) | DO (mg/L) | pH |
|---------|------------------|-----------|----|
| General Fish | 20–28 | 5–12 | 6.5–8.5 |
| Tilapia | 25–32 | 3–15 | 6.0–9.0 |
| Catfish | 24–30 | 4–12 | 6.5–8.5 |
| Salmon | 10–18 | 7–14 | 6.5–8.0 |
| Trout | 10–16 | 7–14 | 6.5–8.0 |
| Carp | 20–28 | 4–12 | 6.5–9.0 |
| Shrimp | 26–32 | 4–10 | 7.0–8.5 |
| Prawn | 26–31 | 4–10 | 7.0–8.5 |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Node.js + Express.js |
| AI/ML | Python + TensorFlow/Keras (LSTM), TensorFlow Lite (YOLO) |
| Frontend | Vanilla JavaScript + Chart.js |
| Database | PostgreSQL (farm management) |
| Weather Data | Open-Meteo API |

## Project Structure

```
aquamonitor/
├── requirements.txt                    # Python dependencies
├── train_model_universal.py            # LSTM model training script
├── water_qual_universal.keras          # Trained LSTM model (generated — not in repo)
├── water_qual_universal_scaler.pkl     # Data scaler (generated — not in repo)
└── web-app/
    ├── server.js                       # Express server + all API endpoints
    ├── package.json                    # Node dependencies
    ├── setup-database.js               # PostgreSQL schema setup
    ├── predict_universal.py            # Location-based LSTM prediction
    ├── predict_manual_lstm.py          # Manual input LSTM analysis
    ├── predict_future_datetime.py      # Future date/time prediction
    ├── predict_predator_working.py     # Predator detection (TFLite)
    ├── predict_disease.py              # Disease detection (TFLite YOLO)
    ├── fetch_data_universal.py         # Open-Meteo weather data fetcher
    ├── third_yolo.tflite               # Predator detection model (not in repo)
    ├── FINAL_3class_fish_model_float32.tflite  # Disease detection model (not in repo)
    └── public/
        ├── home.html
        ├── dashboard.html              # Water quality prediction interface
        ├── data-reports.html           # Historical data + CSV export
        ├── multi-location.html         # Farm management
        ├── predator.html               # Predator detection
        ├── disease.html                # Disease detection
        ├── about.html
        ├── script.js                   # Main frontend logic
        ├── multi-location.js           # Farm management logic
        ├── csv-download.js             # CSV export helper
        └── styles.css
```

## Prerequisites

- Python 3.8+ with pip
- Node.js 14+ with npm
- PostgreSQL 12+ (only required for Farm Management)
- Internet connection (for Open-Meteo weather API)

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/aquamonitor.git
cd aquamonitor
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Train the LSTM model (first time only)
```bash
python train_model_universal.py
```
This takes 5–10 minutes and generates `water_qual_universal.keras` and `water_qual_universal_scaler.pkl` in the root folder.

### 4. Add TFLite model files
Place the following model files in the `web-app/` directory:
- `third_yolo.tflite` — predator detection model
- `FINAL_3class_fish_model_float32.tflite` — disease detection model

### 5. Install Node dependencies
```bash
cd web-app
npm install
```

### 6. Configure environment
Create `web-app/.env`:
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/aquamonitor
```

### 7. Setup database (Farm Management only)
```bash
node setup-database.js
```

### 8. Start the server
```bash
node server.js
```

Open `http://localhost:3000` in your browser.

## Pages

| Page | URL |
|------|-----|
| Home | `/home.html` |
| Dashboard | `/dashboard.html` |
| Data Reports | `/data-reports.html` |
| Farm Management | `/multi-location.html` |
| Predator Detection | `/predator.html` |
| Disease Detection | `/disease.html` |
| About | `/about.html` |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/predict` | Water quality prediction (location or manual) |
| POST | `/api/predict-future` | Future date/time water quality forecast |
| GET | `/api/fetch-data` | Historical weather/water data |
| POST | `/api/predict-predator` | Predator detection from image |
| POST | `/api/predict-disease` | Fish disease detection from image |
| POST | `/api/farm/register` | Register a new farm |
| POST | `/api/farm/login` | Farm login |
| GET | `/api/farm/:farmId/locations` | Get farm locations |
| POST | `/api/farm/:farmId/locations` | Add farm location |
| POST | `/api/farm/:farmId/analyze-enhanced` | Batch water quality analysis |

## LSTM Model Architecture

- Input: 24-hour meteorological sequences from Open-Meteo API
- Architecture: 64 LSTM units → Dropout (0.2) → Dense (32) → Output (3)
- Output: Water temperature, dissolved oxygen, pH
- Training data: 365 days of global weather patterns

## Disease Detection Classes

| Class | Description |
|-------|-------------|
| `Healthy_Fish` | No disease detected |
| `Bacterial_Infections` | Signs of bacterial infection |
| `Fungal_Parasitic_Diseases` | Fungal or parasitic infection |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 3000 in use | Kill existing process or change `PORT` in server.js |
| Model not found | Run `python train_model_universal.py` from root |
| Python errors | Run `pip install -r requirements.txt` |
| Database errors | Check PostgreSQL is running and `.env` credentials are correct |
| Charts not loading | Hard refresh browser (Ctrl+F5) |

## License

MIT — see [LICENSE](LICENSE)

## Acknowledgements

- [Open-Meteo](https://open-meteo.com/) for free global weather API
- [TensorFlow](https://tensorflow.org/) for ML framework
- [Chart.js](https://www.chartjs.org/) for data visualization
- [Express.js](https://expressjs.com/) for the web server
