"""
Alula B2C/B2G Heatmap Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.figure_factory as ff

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

# Bounding box around AlUla region to filter outlier points
ALULA_BOUNDS = {
    'lat_min': 25.5, 'lat_max': 27.5,
    'lon_min': 37.0, 'lon_max': 39.0
}


def create_hexbin_map(df, point_type='origin', animation_col=None):
    """Create a hexbin heatmap with optional animation by day or hour."""
    if point_type == 'origin':
        lat_col, lon_col = 'lat_origin', 'long_origin'
    else:
        lat_col, lon_col = 'lat_destination', 'long_destination'
    
    cols = [lat_col, lon_col]
    if animation_col and animation_col in df.columns:
        cols.append(animation_col)
    
    map_df = df[cols].dropna(subset=[lat_col, lon_col]).copy()
    
    # Filter to AlUla region to avoid outlier points stretching the hex grid
    map_df = map_df[
        (map_df[lat_col].between(ALULA_BOUNDS['lat_min'], ALULA_BOUNDS['lat_max'])) &
        (map_df[lon_col].between(ALULA_BOUNDS['lon_min'], ALULA_BOUNDS['lon_max']))
    ]
    
    if map_df.empty:
        return None
    
    kwargs = dict(
        data_frame=map_df,
        lat=lat_col,
        lon=lon_col,
        nx_hexagon=15,
        opacity=0.5,
        min_count=1,
        color_continuous_scale='Cividis',
        mapbox_style='open-street-map',
        labels={'color': 'Point Count'},
        show_original_data=True,
        original_data_marker=dict(size=4, opacity=0.6, color='deeppink')
    )
    
    if animation_col and animation_col in map_df.columns:
        if animation_col == 'date':
            map_df['period'] = map_df['date'].astype(str)
            map_df = map_df.sort_values('period')
            kwargs['data_frame'] = map_df
            kwargs['animation_frame'] = 'period'
            kwargs['labels'] = {'color': 'Point Count', 'frame': 'Day'}
        elif animation_col == 'hour':
            map_df['period'] = map_df['hour'].astype(str).str.zfill(2) + ':00'
            map_df = map_df.sort_values('hour')
            kwargs['data_frame'] = map_df
            kwargs['animation_frame'] = 'period'
            kwargs['labels'] = {'color': 'Point Count', 'frame': 'Hour'}
    
    try:
        fig = ff.create_hexbin_mapbox(**kwargs)
    except Exception as e:
        return None
    
    fig.update_layout(
        map=dict(center=dict(lat=ALULA_CENTER_LAT, lon=ALULA_CENTER_LON), zoom=11),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    if animation_col and animation_col in map_df.columns:
        fig.layout.sliders[0].pad.t = 20
        fig.layout.updatemenus[0].pad.t = 40
    
    return fig


def create_hexbin_od_map(df, animation_col=None):
    """Create a hexbin map with both origin and destination points overlaid."""
    origin_cols = ['lat_origin', 'long_origin']
    dest_cols = ['lat_destination', 'long_destination']
    extra_cols = []
    if animation_col and animation_col in df.columns:
        extra_cols.append(animation_col)
    
    origins = df[origin_cols + extra_cols].dropna(subset=origin_cols).copy()
    origins = origins.rename(columns={'lat_origin': 'lat', 'long_origin': 'lon'})
    
    destinations = df[dest_cols + extra_cols].dropna(subset=dest_cols).copy()
    destinations = destinations.rename(columns={'lat_destination': 'lat', 'long_destination': 'lon'})
    
    combined = pd.concat([origins, destinations], ignore_index=True)
    
    # Filter to AlUla region to avoid outlier points stretching the hex grid
    combined = combined[
        (combined['lat'].between(ALULA_BOUNDS['lat_min'], ALULA_BOUNDS['lat_max'])) &
        (combined['lon'].between(ALULA_BOUNDS['lon_min'], ALULA_BOUNDS['lon_max']))
    ]
    
    if combined.empty:
        return None
    
    # Also filter origins/destinations for scatter overlay
    origins = origins[
        (origins['lat'].between(ALULA_BOUNDS['lat_min'], ALULA_BOUNDS['lat_max'])) &
        (origins['lon'].between(ALULA_BOUNDS['lon_min'], ALULA_BOUNDS['lon_max']))
    ]
    destinations = destinations[
        (destinations['lat'].between(ALULA_BOUNDS['lat_min'], ALULA_BOUNDS['lat_max'])) &
        (destinations['lon'].between(ALULA_BOUNDS['lon_min'], ALULA_BOUNDS['lon_max']))
    ]
    
    # Use only lat/lon columns for hexbin (no extra columns that could interfere)
    hexbin_df = combined[['lat', 'lon'] + extra_cols].copy()
    
    kwargs = dict(
        data_frame=hexbin_df,
        lat='lat',
        lon='lon',
        nx_hexagon=15,
        opacity=0.5,
        min_count=1,
        color_continuous_scale='Cividis',
        mapbox_style='open-street-map',
        labels={'color': 'Point Count'},
        show_original_data=True,
        original_data_marker=dict(size=4, opacity=0.6, color='deeppink')
    )
    
    if animation_col and animation_col in combined.columns:
        if animation_col == 'date':
            hexbin_df['period'] = hexbin_df['date'].astype(str)
            hexbin_df = hexbin_df.sort_values('period')
            kwargs['data_frame'] = hexbin_df
            kwargs['animation_frame'] = 'period'
            kwargs['labels'] = {'color': 'Point Count', 'frame': 'Day'}
        elif animation_col == 'hour':
            hexbin_df['period'] = hexbin_df['hour'].astype(str).str.zfill(2) + ':00'
            hexbin_df = hexbin_df.sort_values('hour')
            kwargs['data_frame'] = hexbin_df
            kwargs['animation_frame'] = 'period'
            kwargs['labels'] = {'color': 'Point Count', 'frame': 'Hour'}
    
    try:
        fig = ff.create_hexbin_mapbox(**kwargs)
    except Exception as e:
        return None
    
    # Add origin/destination scatter using Plotly v6 maplibre API (Scattermap, not Scattermapbox)
    if not animation_col:
        fig.add_trace(go.Scattermap(
            lat=origins['lat'], lon=origins['lon'],
            mode='markers', name='Origin',
            marker=dict(size=4, color='green', opacity=0.5)
        ))
        fig.add_trace(go.Scattermap(
            lat=destinations['lat'], lon=destinations['lon'],
            mode='markers', name='Destination',
            marker=dict(size=4, color='red', opacity=0.5)
        ))
    
    fig.update_layout(
        map=dict(center=dict(lat=ALULA_CENTER_LAT, lon=ALULA_CENTER_LON), zoom=11),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    if animation_col and animation_col in hexbin_df.columns:
        fig.layout.sliders[0].pad.t = 20
        fig.layout.updatemenus[0].pad.t = 40
    
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


def check_login():
    """Display login page and return True if authenticated."""
    if st.session_state.get("authenticated"):
        return True

    # Style the entire page for login — target Streamlit's own DOM elements
    st.markdown("""
    <style>
        /* Hide sidebar, header, and toolbar on login */
        [data-testid="stSidebar"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"] { display: none !important; }

        /* Dark background on the app container */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(160deg, #0c1117 0%, #151d2b 100%);
        }

        [data-testid="stMain"] {
            background: transparent !important;
        }

        .block-container {
            max-width: 420px !important;
            padding-top: 12vh !important;
            margin: 0 auto !important;
        }

        /* Title & subtitle */
        .login-brand {
            text-align: center;
            font-size: 0.65rem;
            letter-spacing: 3.5px;
            text-transform: uppercase;
            color: rgba(255, 255, 255, 0.30);
            margin-bottom: 0.2rem;
        }
        .login-heading {
            text-align: center;
            font-size: 1.5rem;
            font-weight: 600;
            color: #dce3ec;
            margin-bottom: 0;
        }
        .login-accent {
            width: 36px;
            height: 2px;
            background: #4a9eff;
            margin: 0.7rem auto 0.6rem auto;
            border-radius: 1px;
        }
        .login-sub {
            text-align: center;
            font-size: 0.82rem;
            color: rgba(255, 255, 255, 0.35);
            margin-bottom: 1.6rem;
        }

        /* Form styling */
        .stTextInput > label {
            color: rgba(255, 255, 255, 0.50) !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px !important;
            text-transform: uppercase !important;
        }
        .stTextInput input {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.10) !important;
            border-radius: 6px !important;
            color: #e0e6ef !important;
        }
        .stTextInput input:focus {
            border-color: #4a9eff !important;
            box-shadow: 0 0 0 1px #4a9eff !important;
        }

        /* Submit button */
        .stFormSubmitButton > button {
            background: #4a9eff !important;
            color: #fff !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.4px !important;
            padding: 0.5rem 1.2rem !important;
            margin-top: 0.6rem !important;
            transition: background 0.2s ease !important;
        }
        .stFormSubmitButton > button:hover {
            background: #3b8ae6 !important;
        }

        /* Hide the footer as well */
        footer { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-brand">Royal Commission for AlUla</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-heading">AlUla Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-accent"></div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">Enter your credentials to access the dashboard</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Username")
        password = st.text_input("Password", type="password", placeholder="Password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            valid_user = st.secrets["auth"]["username"]
            valid_pass = st.secrets["auth"]["password"]

            if username == valid_user and password == valid_pass:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid username or password.")

    return False


def main():
    # Gate access behind login
    if not check_login():
        return

    st.title("Alula B2C/B2G Heatmap Dashboard")
    st.caption("January 2026")

    # Logout button in sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

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
    map_tabs = st.tabs(["Origin vs Destination", "Origins Hexagon Heatmap", "Destinations Hexagon Heatmap"])
    
    with map_tabs[0]:
        anim_mode_od = st.radio("Animation", ["None", "By Day", "By Hour"], horizontal=True, key="anim_od")
        anim_col_od = {'None': None, 'By Day': 'date', 'By Hour': 'hour'}[anim_mode_od]
        fig = create_hexbin_od_map(filtered_df, animation_col=anim_col_od)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        else:
            st.warning("No data available.")
    
    with map_tabs[1]:
        anim_mode_o = st.radio("Animation", ["None", "By Day", "By Hour"], horizontal=True, key="anim_origin")
        anim_col_o = {'None': None, 'By Day': 'date', 'By Hour': 'hour'}[anim_mode_o]
        fig = create_hexbin_map(filtered_df, 'origin', animation_col=anim_col_o)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
        else:
            st.warning("No data available.")
    
    with map_tabs[2]:
        anim_mode_d = st.radio("Animation", ["None", "By Day", "By Hour"], horizontal=True, key="anim_dest")
        anim_col_d = {'None': None, 'By Day': 'date', 'By Hour': 'hour'}[anim_mode_d]
        fig = create_hexbin_map(filtered_df, 'destination', animation_col=anim_col_d)
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