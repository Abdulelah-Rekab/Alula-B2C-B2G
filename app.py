"""
Alula B2C/B2G Heatmap Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Alula B2C/B2G Heatmap Dashboard",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple clean styling
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding: 1rem 2rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_b2c_data():
    """Load and preprocess the B2C data."""
    df = pd.read_csv('RACB2C_January2026')
    
    df['request_creation_time'] = pd.to_datetime(df['request_creation_time'], format='mixed')
    df['date'] = df['request_creation_time'].dt.date
    df['hour'] = df['request_creation_time'].dt.hour
    df['day_name'] = df['request_creation_time'].dt.day_name()
    df['day_of_week'] = df['request_creation_time'].dt.dayofweek
    
    df['zone_origin'] = df['zone_origin'].replace('', 'Unknown').fillna('Unknown')
    df['zone_destination'] = df['zone_destination'].replace('', 'Unknown').fillna('Unknown')
    
    df['lat_origin'] = pd.to_numeric(df['lat_origin'], errors='coerce')
    df['long_origin'] = pd.to_numeric(df['long_origin'], errors='coerce')
    df['lat_destination'] = pd.to_numeric(df['lat_destination'], errors='coerce')
    df['long_destination'] = pd.to_numeric(df['long_destination'], errors='coerce')
    
    df['source'] = 'B2C'
    
    return df


@st.cache_data
def load_b2g_data():
    """Load and preprocess the B2G data."""
    df = pd.read_csv('RACB2G_January2026')
    
    df['request_creation_time'] = pd.to_datetime(df['request_creation_time'], format='mixed')
    df['date'] = df['request_creation_time'].dt.date
    df['hour'] = df['request_creation_time'].dt.hour
    df['day_name'] = df['request_creation_time'].dt.day_name()
    df['day_of_week'] = df['request_creation_time'].dt.dayofweek
    
    # Map B2G column names to standardized names
    df = df.rename(columns={
        'origin_lat': 'lat_origin',
        'origin_lng': 'long_origin',
        'destination_lat': 'lat_destination',
        'destination_lng': 'long_destination',
        'origin_zone': 'zone_origin',
        'destination_zone': 'zone_destination'
    })
    
    df['zone_origin'] = df['zone_origin'].replace('', 'Unknown').fillna('Unknown')
    df['zone_destination'] = df['zone_destination'].replace('', 'Unknown').fillna('Unknown')
    
    df['lat_origin'] = pd.to_numeric(df['lat_origin'], errors='coerce')
    df['long_origin'] = pd.to_numeric(df['long_origin'], errors='coerce')
    df['lat_destination'] = pd.to_numeric(df['lat_destination'], errors='coerce')
    df['long_destination'] = pd.to_numeric(df['long_destination'], errors='coerce')
    
    df['source'] = 'B2G'
    
    return df


# Fixed Alula center coordinates
ALULA_CENTER_LAT = 26.6
ALULA_CENTER_LON = 37.95


def create_heatmap(df, point_type='origin'):
    """Create a density heatmap for origin or destination points."""
    if point_type == 'origin':
        lat_col, lon_col = 'lat_origin', 'long_origin'
        zone_col = 'zone_origin'
    else:
        lat_col, lon_col = 'lat_destination', 'long_destination'
        zone_col = 'zone_destination'
    
    map_df = df[[lat_col, lon_col, zone_col, 'request_status']].dropna()
    
    if map_df.empty:
        return None
    
    fig = px.density_mapbox(
        map_df,
        lat=lat_col,
        lon=lon_col,
        hover_data=[zone_col, 'request_status'],
        radius=15,
        zoom=10,
        mapbox_style="open-street-map"
    )
    
    fig.update_layout(
        mapbox=dict(center=dict(lat=ALULA_CENTER_LAT, lon=ALULA_CENTER_LON), zoom=10),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig


def create_scatter_map(df):
    """Create a scatter map showing both origins and destinations."""
    origins = df[['lat_origin', 'long_origin', 'zone_origin', 'request_status', 'source']].copy()
    origins.columns = ['lat', 'lon', 'zone', 'status', 'service']
    origins['type'] = 'Origin'
    origins = origins.dropna(subset=['lat', 'lon'])
    
    destinations = df[['lat_destination', 'long_destination', 'zone_destination', 'request_status', 'source']].copy()
    destinations.columns = ['lat', 'lon', 'zone', 'status', 'service']
    destinations['type'] = 'Destination'
    destinations = destinations.dropna(subset=['lat', 'lon'])
    
    combined = pd.concat([origins, destinations], ignore_index=True)
    
    if combined.empty:
        return None
    
    fig = px.scatter_mapbox(
        combined,
        lat='lat',
        lon='lon',
        color='type',
        hover_data=['service', 'zone', 'status'],
        color_discrete_map={'Origin': 'green', 'Destination': 'red'},
        mapbox_style="open-street-map",
        zoom=10
    )
    
    fig.update_layout(
        mapbox=dict(center=dict(lat=ALULA_CENTER_LAT, lon=ALULA_CENTER_LON)),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_hourly_heatmap(df):
    """Create hourly heatmap showing request patterns by day and hour."""
    heatmap_data = df.groupby(['day_name', 'hour']).size().reset_index(name='count')
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_pivot = heatmap_data.pivot(index='day_name', columns='hour', values='count').fillna(0)
    heatmap_pivot = heatmap_pivot.reindex([d for d in day_order if d in heatmap_pivot.index])
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=[f'{h:02d}:00' for h in heatmap_pivot.columns],
        y=heatmap_pivot.index,
        colorscale='Blues',
        hoverongaps=False,
        hovertemplate='Day: %{y}<br>Hour: %{x}<br>Requests: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Daily Heatmap: Requests by Day and Hour',
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week',
        height=350,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


def create_daily_heatmap(df):
    """Create daily request patterns heatmap."""
    daily_data = df.groupby(['date', 'hour']).size().reset_index(name='count')
    daily_pivot = daily_data.pivot(index='date', columns='hour', values='count').fillna(0)
    daily_pivot.index = [str(d) for d in daily_pivot.index]
    
    fig = go.Figure(data=go.Heatmap(
        z=daily_pivot.values,
        x=[f'{h:02d}:00' for h in daily_pivot.columns],
        y=daily_pivot.index,
        colorscale='Blues',
        hoverongaps=False,
        hovertemplate='Date: %{y}<br>Hour: %{x}<br>Requests: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Hourly Heatmap: Requests by Date and Hour',
        xaxis_title='Hour of Day',
        yaxis_title='Date',
        height=500,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


def create_zone_heatmap(df):
    """Create heatmap showing origin vs destination zones."""
    zone_matrix = df.groupby(['zone_origin', 'zone_destination']).size().reset_index(name='count')
    zone_pivot = zone_matrix.pivot(index='zone_origin', columns='zone_destination', values='count').fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=zone_pivot.values,
        x=zone_pivot.columns,
        y=zone_pivot.index,
        colorscale='Blues',
        hoverongaps=False,
        hovertemplate='Origin: %{y}<br>Destination: %{x}<br>Requests: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Route Heatmap: Origin vs Destination',
        xaxis_title='Destination Zone',
        yaxis_title='Origin Zone',
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(tickangle=45)
    )
    
    return fig


def main():
    st.title("Alula B2C/B2G Heatmap Dashboard")
    st.caption("January 2026")
    
    # Load data
    try:
        b2c_df = load_b2c_data()
        b2g_df = load_b2g_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Data source selector
    data_source = st.sidebar.radio(
        "Data Source",
        options=["B2C", "B2G", "Both"],
        index=0
    )
    
    # Select data based on source
    if data_source == "B2C":
        df = b2c_df
    elif data_source == "B2G":
        df = b2g_df
    else:
        df = pd.concat([b2c_df, b2g_df], ignore_index=True)
    
    # Date range
    min_date = df['date'].min()
    max_date = df['date'].max()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Hour range
    hour_range = st.sidebar.slider("Hour Range", 0, 23, (0, 23), format="%d:00")
    
    # Status filter
    all_statuses = df['request_status'].unique().tolist()
    selected_statuses = st.sidebar.multiselect("Request Status", all_statuses, default=all_statuses)
    
    # Apply filters
    if len(date_range) == 2:
        filtered_df = df[
            (df['date'] >= date_range[0]) &
            (df['date'] <= date_range[1]) &
            (df['hour'] >= hour_range[0]) &
            (df['hour'] <= hour_range[1]) &
            (df['request_status'].isin(selected_statuses))
        ]
    else:
        filtered_df = df[df['request_status'].isin(selected_statuses)]
    
    # Metrics row
    st.subheader("Key Metrics")
    metric_cols = st.columns(5)
    
    with metric_cols[0]:
        st.metric("Total Requests", len(filtered_df))
    
    with metric_cols[1]:
        completed = len(filtered_df[filtered_df['request_status'] == 'Completed'])
        st.metric("Completed", completed)
    
    with metric_cols[2]:
        seat_unavail = len(filtered_df[filtered_df['request_status'] == 'Seat Unavailable'])
        st.metric("Seat Unavailable", seat_unavail)
    
    with metric_cols[3]:
        cancelled = len(filtered_df[filtered_df['request_status'] == 'Cancelled'])
        st.metric("Cancelled", cancelled)
    
    with metric_cols[4]:
        not_accepted = len(filtered_df[filtered_df['request_status'] == 'Not Accepted'])
        st.metric("Not Accepted", not_accepted)
    
    st.markdown("---")
    
    # Map tabs
    st.subheader("Geographic View")
    map_tabs = st.tabs(["Origin vs Destination", "Origins Heatmap", "Destinations Heatmap"])
    
    with map_tabs[0]:
        fig = create_scatter_map(filtered_df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        else:
            st.warning("No data available.")
    
    with map_tabs[1]:
        fig = create_heatmap(filtered_df, 'origin')
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        else:
            st.warning("No data available.")
    
    with map_tabs[2]:
        fig = create_heatmap(filtered_df, 'destination')
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        else:
            st.warning("No data available.")
    
    st.markdown("---")
    
    # Time-based heatmaps
    st.subheader("Temporal Heatmaps")
    time_cols = st.columns(2)
    
    with time_cols[0]:
        hourly_fig = create_hourly_heatmap(filtered_df)
        st.plotly_chart(hourly_fig, use_container_width=True)
    
    with time_cols[1]:
        zone_fig = create_zone_heatmap(filtered_df)
        st.plotly_chart(zone_fig, use_container_width=True)
    
    # Daily heatmap
    daily_fig = create_daily_heatmap(filtered_df)
    st.plotly_chart(daily_fig, use_container_width=True)


if __name__ == "__main__":
    main()