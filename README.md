# Alula B2C/B2G Heatmap Dashboard

Interactive dashboard for visualizing daily and hourly request patterns for Alula ride-sharing service.

## Features

- **Data Source Selection**: Switch between B2C, B2G, or combined data
- **Geographic Heatmaps**: Origin and destination location visualization
- **Temporal Analysis**: Daily and hourly request pattern heatmaps
- **Route Analysis**: Origin vs destination zone heatmap
- **Key Metrics**: Completed, Seat Unavailable, Cancelled, Not Accepted counts
- **Filters**: Date range, hour range, and request status filtering

## Data

- `RACB2C_January2026` - B2C ride request data
- `RACB2G_January2026` - B2G ride request data

## Deployment

This app is deployed on Streamlit Cloud.

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```
