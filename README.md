# Fitness Dashboard

A personal fitness tracking dashboard built with Streamlit that connects to Google Sheets for real-time workout data visualization and analysis.

## Features

- **Real-time data sync** from Google Sheets
- **Summary dashboard** with key fitness metrics
- **Workout deep-dive** pages with detailed analysis
- **Mobile-responsive** design
- **Privacy-focused** - all data stays under your control

## Tech Stack

- **Frontend/Backend:** Streamlit
- **Data Source:** Google Sheets API
- **Data Processing:** Pandas, Plotly
- **Authentication:** Google Service Account

## Project Structure

```
fitness-dashboard/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (not tracked)
├── config/
│   └── service_account.json  # Google credentials (not tracked)
├── utils/
│   ├── data_loader.py    # Google Sheets data loading
│   └── visualizations.py # Reusable chart components
└── pages/
    ├── summary.py        # Summary dashboard page
    └── workout_details.py # Detailed workout analysis
```

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd fitness-dashboard
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Google Sheets API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create Service Account and download JSON credentials
5. Place credentials file in `config/service_account.json`
6. Share your Google Sheet with the service account email

### 3. Environment Configuration

Create a `.env` file with your configuration:

```env
GOOGLE_SHEET_NAME="Your Workout Log"
REFRESH_INTERVAL=60
```

### 4. Run the Application

```bash
streamlit run app.py
```

## Development Roadmap

- [x] Phase 1: Project setup and Google Sheets integration
- [ ] Phase 2: Basic dashboard with summary metrics
- [ ] Phase 3: Detailed workout analysis pages
- [ ] Phase 4: Mobile optimization and deployment
- [ ] Phase 5: Heart rate and Peloton integration

## Contributing

This is a personal project, but feel free to fork and adapt for your own use!

## Privacy

All fitness data remains in your Google Sheets and local environment. No data is sent to external services beyond Google's API for sheet access.