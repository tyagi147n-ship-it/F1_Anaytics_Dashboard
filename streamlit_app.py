# ============================================================
# STREAMLIT APP: Formula 1 Analytics Dashboard
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import os 
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
# ── PAGE CONFIGURATION ────────────────────────────────────────

st.set_page_config(
    page_title="F1 Analytics Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────────

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #E10600;
        text-align: center;
        padding: 10px 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


# ── DATA LOADING ──────────────────────────────────────────────

@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "Data", "Processed")

    master            = pd.read_csv(os.path.join(DATA_DIR, "processedmaster_df.csv"))
    driver_stats      = pd.read_csv(os.path.join(DATA_DIR, "processeddriver_season_stats.csv"))
    constructor_stats = pd.read_csv(os.path.join(DATA_DIR, "processedconstructor_season_stats.csv"))
    pit_agg           = pd.read_csv(os.path.join(DATA_DIR, "processedpit_agg.csv"))
    pit_stops         = pd.read_csv(os.path.join(DATA_DIR, "processedpit_stops_clean.csv"))

    return master, driver_stats, constructor_stats, pit_agg, pit_stops


master, driver_stats, constructor_stats, pit_agg, pit_stops = load_data()
st.dataframe(pd.DataFrame(driver_stats.columns, columns=["Columns"]))

# Create is_winner cleanly — does NOT overwrite any original column
master['is_winner'] = (master['positionOrder'] == 1).astype(int)
master['did_finish'] = (master['positionOrder'] > 0).astype(int)
master['positions_gained'] = (
    master['grid'] - master['positionOrder']
)
# ── HEADER ────────────────────────────────────────────────────

st.markdown('<p class="main-header">🏎️ Formula 1 Analytics Dashboard</p>',
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">Exploring driver performance, constructor dominance, and pit stop strategy</p>',
            unsafe_allow_html=True)
st.markdown("---")


# ── SIDEBAR FILTERS ───────────────────────────────────────────

with st.sidebar:

    logo_path = os.path.join(
        BASE_DIR,
        "Images",
        "download.png"
    )

    st.image(logo_path, width=150)

    st.header("🔧 Filters")

    year_min = int(master['year'].min())
    year_max = int(master['year'].max())

    year_range = st.slider(
        "Select Year Range",
        min_value=year_min,
        max_value=year_max,
        value=(2010, year_max),
        step=1
    )
st.markdown("---")

all_constructors = sorted(master['constructor_name'].dropna().unique().tolist())
default_teams    = ['Mercedes', 'Red Bull', 'Ferrari', 'McLaren']
valid_defaults   = [t for t in default_teams if t in all_constructors]

selected_constructors = st.multiselect(
        "Select Constructors",
        options=all_constructors,
        default=valid_defaults
    )

st.markdown("---")
st.caption("📊 Data: Ergast F1 API Dataset")
st.caption("Built with Streamlit + Plotly")



# ── APPLY FILTERS ─────────────────────────────────────────────

filtered = master[
    (master['year'] >= year_range[0]) &
    (master['year'] <= year_range[1])
].copy()

filtered_constr = filtered[
    filtered['constructor_name'].isin(selected_constructors)
] if selected_constructors else filtered


# ── KPI CARDS ─────────────────────────────────────────────────

st.subheader("📈 Key Metrics for Selected Period")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    total_races = filtered['raceId'].nunique()
    st.metric(label="🏁 Total Races", value=f"{total_races:,}")

with kpi2:
    total_drivers = filtered['driver_name'].nunique()
    st.metric(label="👤 Unique Drivers", value=f"{total_drivers:,}")

with kpi3:
    total_constructors = filtered['constructor_name'].nunique()
    st.metric(label="🏭 Constructors", value=f"{total_constructors:,}")

with kpi4:
    wins = (
        filtered[filtered['is_winner'] == 1]
        .groupby('driver_name')['is_winner']
        .sum()
    )

    top_driver = wins.idxmax() if not wins.empty else "N/A"

    st.metric(
        label="🏆 Most Wins",
        value=top_driver
    )
    st.markdown("---")
    # Bug 2 fixed: use is_winner column, not position
    wins = (
    filtered[filtered['is_winner'] == 1]
    .groupby('driver_name')['is_winner']
    .sum()
    )

    top_driver = wins.idxmax() if not wins.empty else "N/A"

    st.metric(label="🏆 Most Wins", value=top_driver)

    st.markdown("---")


# ── TABS ──────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧑‍💼 Driver Analysis",
    "🏭 Constructor Analysis",
    "🔄 Positions Gained",
    "⏱️ Pit Stop Analysis",
    "⚔️ Driver Comparison"
])


# ════════════════════════════════════════════════════════════════
# TAB 1: DRIVER ANALYSIS
# ════════════════════════════════════════════════════════════════

with tab1:
    st.header("Driver Performance Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top Race Winners")
        top_n = st.slider("Show top N drivers", 5, 20, 10, key="winner_slider")

        # Bug 3 fixed: sum is_winner, not position
        wins_data = (
            filtered[filtered['is_winner'] == 1]
            .groupby('driver_name')['is_winner']
            .sum()
            .sort_values(ascending=True)
            .tail(top_n)
            .reset_index()
        )
        wins_data.columns = ['Driver', 'Wins']

        fig_wins = px.bar(
            wins_data, x='Wins', y='Driver',
            orientation='h',
            color='Wins',
            color_continuous_scale='Reds',
            text='Wins'
        )
        fig_wins.update_layout(
            plot_bgcolor='white', height=400,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        fig_wins.update_traces(textposition='outside')
        st.plotly_chart(fig_wins, use_container_width=True)

    with col2:
        st.subheader("🥇 Driver Podium Rate (%)")

        podium_data = (
            filtered.groupby('driver_name')
            .agg(
                races   = ('resultId', 'count'),
                podiums = ('positionOrder', lambda x: (x <= 3).sum())
            )
            .reset_index()
        )
        podium_data = podium_data[podium_data['races'] >= 20]
        podium_data['podium_rate'] = (
            podium_data['podiums'] / podium_data['races'] * 100
        ).round(1)
        podium_data = podium_data.sort_values('podium_rate', ascending=True).tail(top_n)

        fig_podium = px.bar(
            podium_data, x='podium_rate', y='driver_name',
            orientation='h',
            color='podium_rate',
            color_continuous_scale='Oranges',
            text='podium_rate',
            labels={'podium_rate': 'Podium Rate (%)', 'driver_name': 'Driver'}
        )
        fig_podium.update_layout(
            plot_bgcolor='white', height=400,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        fig_podium.update_traces(textposition='outside')
        st.plotly_chart(fig_podium, use_container_width=True)

    # ── Points Trend ─────────────────────────────────────────
    st.subheader("📈 Season Points Trend")

    all_drivers = sorted(filtered['driver_name'].dropna().unique().tolist())

    top5_default = (
        filtered[filtered['is_winner'] == 1]
        .groupby('driver_name')['is_winner']
        .sum()
        .nlargest(5)
        .index.tolist()
    )
    valid_top5 = [d for d in top5_default if d in all_drivers]

    selected_drivers = st.multiselect(
        "Select drivers to compare",
        options=all_drivers,
        default=valid_top5[:5]
    )

    if selected_drivers:
        driver_season = driver_stats[
            (driver_stats['driver_name'].isin(selected_drivers)) &
            (driver_stats['year'] >= year_range[0]) &
            (driver_stats['year'] <= year_range[1])
        ]
        fig_trend = px.line(
            driver_season,
            x='year', y='total_points',
            color='driver_name', markers=True,
            title='Season Points by Driver',
            labels={'total_points': 'Points', 'year': 'Year', 'driver_name': 'Driver'}
        )
        fig_trend.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Select at least one driver above to see the trend chart.")


# ════════════════════════════════════════════════════════════════
# TAB 2: CONSTRUCTOR ANALYSIS
# ════════════════════════════════════════════════════════════════

with tab2:
    st.header("Constructor Performance Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Constructor Wins")

        constr_wins = (
            filtered[filtered['is_winner'] == 1]
            .groupby('constructor_name')['is_winner']
            .sum()
            .sort_values(ascending=True)
            .tail(12)
            .reset_index()
        )
        constr_wins.columns = ['Constructor', 'Wins']

        fig_cw = px.bar(
            constr_wins, x='Wins', y='Constructor',
            orientation='h', color='Wins',
            color_continuous_scale='Blues', text='Wins'
        )
        fig_cw.update_layout(
            plot_bgcolor='white', height=450, coloraxis_showscale=False
        )
        fig_cw.update_traces(textposition='outside')
        st.plotly_chart(fig_cw, use_container_width=True)

    with col2:
        st.subheader("⚙️ Constructor DNF Rate (%)")

        dnf_data = (
            filtered.groupby('constructor_name')
            .agg(
                total_starts = ('resultId', 'count'),
                # did_finish == 0 means DNF; positionOrder alone can't tell us this.
                # Use the did_finish column created in feature engineering.
                total_dnf    = ('did_finish', lambda x: (x == 0).sum())
            )
            .reset_index()
        )
        dnf_data = dnf_data[dnf_data['total_starts'] >= 30]
        dnf_data['dnf_rate'] = (
            dnf_data['total_dnf'] / dnf_data['total_starts'] * 100
        ).round(1)
        dnf_data = dnf_data.sort_values('dnf_rate').head(12)

        fig_dnf = px.bar(
            dnf_data, x='dnf_rate', y='constructor_name',
            orientation='h', color='dnf_rate',
            color_continuous_scale='RdYlGn_r', text='dnf_rate',
            labels={'dnf_rate': 'DNF Rate (%)', 'constructor_name': 'Constructor'}
        )
        fig_dnf.update_layout(
            plot_bgcolor='white', height=450, coloraxis_showscale=False
        )
        st.plotly_chart(fig_dnf, use_container_width=True)

    st.subheader("📈 Constructor Points Race by Season")

    if selected_constructors:
        constr_trend = constructor_stats[
            (constructor_stats['constructor_name'].isin(selected_constructors)) &
            (constructor_stats['year'] >= year_range[0]) &
            (constructor_stats['year'] <= year_range[1])
        ]
        fig_ct = px.line(
            constr_trend,
            x='year', y='total_points',
            color='constructor_name', markers=True,
            labels={'total_points': 'Points', 'constructor_name': 'Team'}
        )
        fig_ct.update_layout(plot_bgcolor='white', height=400)
        st.plotly_chart(fig_ct, use_container_width=True)
    else:
        st.info("Select constructors in the sidebar to compare their points trends.")


# ════════════════════════════════════════════════════════════════
# TAB 3: POSITIONS GAINED
# ════════════════════════════════════════════════════════════════

with tab3:
    st.header("Positions Gained Analysis — Overtaking & Racecraft")

    st.markdown("""
    > **What is this?** Positions Gained = Starting Grid − Finishing Position.
    > A positive number means the driver moved *forward* through the field.
    > This metric isolates **driver racecraft and overtaking ability** from car performance.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🔼 Average Positions Gained Per Race")

        min_races = st.slider(
            "Minimum races (for statistical reliability)",
            10, 50, 20, key="pg_slider"
        )

        pg_data = (
            filtered.groupby('driver_name')
            .agg(
                avg_gained = ('positions_gained', 'mean'),
                races      = ('resultId', 'count')
            )
            .reset_index()
        )
        pg_data = pg_data[pg_data['races'] >= min_races]
        pg_data['avg_gained'] = pg_data['avg_gained'].round(2)
        pg_data = pg_data.sort_values('avg_gained', ascending=False).head(20)

        fig_pg = px.bar(
            pg_data,
            x='driver_name', y='avg_gained',
            color='avg_gained', color_continuous_scale='RdYlGn',
            text='avg_gained',
            labels={'avg_gained': 'Avg Positions Gained', 'driver_name': 'Driver'}
        )
        fig_pg.update_layout(
            xaxis_tickangle=-45, plot_bgcolor='white',
            height=450, coloraxis_showscale=False
        )
        fig_pg.update_traces(textposition='outside')
        st.plotly_chart(fig_pg, use_container_width=True)

    with col2:
        st.subheader("🔎 Single Race Highlights")

        # Bug 4 fixed: select positions_gained directly, rename to display name
        best_single = (
            filtered[['driver_name', 'race_name', 'year',
                       'grid', 'positionOrder', 'positions_gained']]
            .dropna(subset=['positions_gained'])
            .sort_values('positions_gained', ascending=False)
            .head(10)
        )
        best_single = best_single.rename(columns={
            'driver_name':      'Driver',
            'race_name':        'Race',
            'year':             'Year',
            'grid':             'Start',
            'positionOrder':    'Finish',
            'positions_gained': '↑ Gained'
        })
        best_single['↑ Gained'] = best_single['↑ Gained'].astype(int)

        st.dataframe(
            best_single.reset_index(drop=True),
            use_container_width=True,
            height=350
        )

    st.subheader("🎯 Grid Position vs Finishing Position")
    st.markdown("Points below the diagonal line indicate positions gained; above means positions lost.")

    scatter_sample = filtered.dropna(subset=['grid', 'positionOrder']).sample(
        min(2000, len(filtered)), random_state=42
    )

    fig_scatter = px.scatter(
        scatter_sample,
        x='grid', y='positionOrder',
        color='constructor_name', opacity=0.5,
        title='Starting Grid vs Finishing Position',
        labels={
            'grid': 'Grid Position',
            'positionOrder': 'Finishing Position',
            'constructor_name': 'Constructor'
        },
        hover_data=['driver_name', 'race_name', 'year']
    )
    fig_scatter.add_shape(
        type='line', x0=1, y0=1, x1=22, y1=22,
        line=dict(color='red', width=1.5, dash='dash')
    )
    fig_scatter.add_annotation(
        x=18, y=15, text="No change line",
        showarrow=False, font=dict(color='red', size=10)
    )
    fig_scatter.update_layout(plot_bgcolor='white', height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 4: PIT STOP ANALYSIS
# ════════════════════════════════════════════════════════════════

with tab4:
    st.header("Pit Stop Strategy Analysis")

    pit_with_year = pd.merge(
        pit_agg,
        master[['raceId', 'driverId', 'year', 'constructor_name',
                'positionOrder', 'driver_name']].drop_duplicates(),
        on=['raceId', 'driverId'],
        how='left'
    )

    pit_filtered = pit_with_year[
        (pit_with_year['year'] >= year_range[0]) &
        (pit_with_year['year'] <= year_range[1])
    ]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⚡ Fastest Pit Crews by Constructor")

        crew = (
            pit_filtered.groupby('constructor_name')['avg_stop_time']
            .mean()
            .sort_values()
            .head(15)
            .reset_index()
        )
        crew.columns = ['Constructor', 'Avg Stop Time (s)']
        crew['Avg Stop Time (s)'] = crew['Avg Stop Time (s)'].round(3)

        fig_crew = px.bar(
            crew,
            x='Constructor', y='Avg Stop Time (s)',
            color='Avg Stop Time (s)',
            color_continuous_scale='RdYlGn_r',
            text='Avg Stop Time (s)'
        )
        fig_crew.update_layout(
            xaxis_tickangle=-45, plot_bgcolor='white',
            height=420, coloraxis_showscale=False
        )
        st.plotly_chart(fig_crew, use_container_width=True)

    with col2:
        st.subheader("📊 Stop Count vs Avg Finishing Position")

        stop_strategy = (
            pit_filtered[pit_filtered['total_stops'].between(1, 4)]
            .groupby('total_stops')['positionOrder']
            .agg(['mean', 'count'])
            .reset_index()
        )
        stop_strategy.columns = ['Stops', 'Avg Finish Position', 'Count']
        stop_strategy['Avg Finish Position'] = stop_strategy['Avg Finish Position'].round(2)

        fig_strat = px.bar(
            stop_strategy,
            x='Stops', y='Avg Finish Position',
            color='Avg Finish Position',
            color_continuous_scale='RdYlGn_r',
            text='Avg Finish Position',
            title='Strategy Analysis: Stops vs Finishing Position'
        )
        fig_strat.update_layout(
            plot_bgcolor='white', height=420, coloraxis_showscale=False
        )
        st.plotly_chart(fig_strat, use_container_width=True)

    st.subheader("⏱️ Pit Stop Duration Distribution by Year")

    pit_stops_with_year = pd.merge(
        pit_stops,
        master[['raceId', 'driverId', 'year', 'constructor_name']].drop_duplicates(),
        on=['raceId', 'driverId'],
        how='left'
    )

    pit_year_filtered = pit_stops_with_year[
        (pit_stops_with_year['year'] >= year_range[0]) &
        (pit_stops_with_year['year'] <= year_range[1]) &
        (pit_stops_with_year['duration'].between(2, 60))
    ]

    fig_box = px.box(
        pit_year_filtered,
        x='year', y='duration',
        title='Pit Stop Duration by Year (Shows how pit stops have evolved)',
        labels={'duration': 'Duration (seconds)', 'year': 'Year'}
    )
    fig_box.update_layout(plot_bgcolor='white', height=400)
    st.plotly_chart(fig_box, use_container_width=True)

# ==========================================================
# TAB 5: DRIVER COMPARISON
# ==========================================================

with tab5:

    st.header("⚔️ Driver Comparison")

    # Aggregate stats across all seasons
    agg = (
        driver_stats.groupby("driver_name")
        .agg(
            Wins=("total_wins", "sum"),
            Podiums=("total_podiums", "sum"),
            Points=("total_points", "sum"),
            Avg_Finish=("avg_position", "mean"),
            DNFs=("total_dnf", "sum"),
            Races=("races_entered", "sum")
        )
        .reset_index()
    )
    # Rates
    agg["Win_Rate"] = agg["Wins"] / agg["Races"]
    agg["Podium_Rate"] = agg["Podiums"] / agg["Races"]
    agg["Points_Per_Race"] = agg["Points"] / agg["Races"]
    agg["DNF_Rate"] = agg["DNFs"] / agg["Races"]

    # Driver Performance Index
    agg["DPI"] = (
    0.35 * agg["Win_Rate"] * 100
    + 0.30 * agg["Podium_Rate"] * 100
    + 0.20 * agg["Points_Per_Race"]
    - 0.10 * agg["DNF_Rate"] * 100
    + 0.05 * np.log1p(agg["Races"])
    )

    agg["DPI"] = agg["DPI"].round(2)

    agg["DPI"] = agg["DPI"].round(2)

    drivers = sorted(agg["driver_name"].unique())

    # Driver selectors
    col1, col2 = st.columns(2)

    with col1:
        driver1 = st.selectbox(
            "Select Driver 1",
            drivers,
            key="driver1"
        )

    with col2:
        driver2 = st.selectbox(
            "Select Driver 2",
            drivers,
            index=1,
            key="driver2"
        )

    # Prevent same driver selection
    if driver1 == driver2:
        st.error(
            "🚫 You selected the same driver twice.\n\n"
            "Please choose two different drivers."
        )
        st.stop()

    # Get stats for selected drivers
    d1 = agg[agg["driver_name"] == driver1].iloc[0]
    d2 = agg[agg["driver_name"] == driver2].iloc[0]
    # Driver Performance Index (DPI)
    agg["DPI"] = (
    0.4 * (agg["Wins"] / agg["Races"]) * 100
    + 0.3 * (agg["Podiums"] / agg["Races"]) * 100
    + 0.2 * (agg["Points"] / agg["Races"])
    - 0.1 * (agg["DNFs"] / agg["Races"]) * 100
    )

    d1 = agg[agg["driver_name"] == driver1].iloc[0]
    d2 = agg[agg["driver_name"] == driver2].iloc[0]

    st.subheader(f"🏁 {driver1} vs {driver2}")

    # Metric cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.metric(
            "🏆 Wins",
            int(d1["Wins"]),
            delta=int(d1["Wins"] - d2["Wins"])
        )

    with c2:
        st.metric(
            "🥇 Podiums",
            int(d1["Podiums"]),
            delta=int(d1["Podiums"] - d2["Podiums"])
        )

    with c3:
        st.metric(
            "⚡ Points",
            int(d1["Points"]),
            delta=int(d1["Points"] - d2["Points"])
        )

    with c4:
        st.metric(
            "💥 DNFs",
            int(d1["DNFs"]),
            delta=int(d2["DNFs"] - d1["DNFs"])
        )

    with c5:
        st.metric(
            "📍 Avg Finish",
            round(d1["Avg_Finish"], 2),
            delta=round(d2["Avg_Finish"] - d1["Avg_Finish"], 2)
        )
    with c6:
        st.metric(
        "⭐ DPI",
        round(d1["DPI"],2),
        delta=round(d1["DPI"]-d2["DPI"],2)
        )
    st.markdown("## 📡 Radar Chart")

    categories = [
    "Wins",
    "Podiums",
    "Points",
    "Avg Finish",
    "DPI"
    ]

   # Normalize values
    max_wins = agg["Wins"].max()
    max_podiums = agg["Podiums"].max()
    max_points = agg["Points"].max()
    max_dpi = agg["DPI"].max()

    driver1_values = [
    d1["Wins"]/max_wins,
    d1["Podiums"]/max_podiums,
    d1["Points"]/max_points,
    1 - d1["Avg_Finish"]/agg["Avg_Finish"].max(),
    d1["DPI"]/max_dpi
    ]

    driver2_values = [
    d2["Wins"]/max_wins,
    d2["Podiums"]/max_podiums,
    d2["Points"]/max_points,
    1 - d2["Avg_Finish"]/agg["Avg_Finish"].max(),
    d2["DPI"]/max_dpi
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
    r=driver1_values,
    theta=categories,
    fill='toself',
    name=driver1
    ))

    fig.add_trace(go.Scatterpolar(
    r=driver2_values,
    theta=categories,
    fill='toself',
    name=driver2
    ))

    fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0,1]
        )
    ),
    showlegend=True,
    height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("## 🏆 Driver Performance Index Rankings")

    top_dpi = (
    agg.sort_values("DPI", ascending=False)
       .head(10)
    )

    fig_dpi = px.bar(
    top_dpi,
    x="DPI",
    y="driver_name",
    orientation="h",
    color="DPI",
    title="🏆 Top 10 Drivers by Driver Performance Index"
    )

    fig_dpi.update_layout(
    yaxis=dict(categoryorder="total ascending"),
    height=600
    )

    st.plotly_chart(fig_dpi, use_container_width=True)
    
    # Head-to-head table
    
    comparison_df = pd.DataFrame({
        "Metric": ["Races", "Wins", "Podiums", "Points", "DNFs", "Avg Finish"],
        driver1: [
            int(d1["Races"]),
            int(d1["Wins"]),
            int(d1["Podiums"]),
            int(d1["Points"]),
            int(d1["DNFs"]),
            round(d1["Avg_Finish"], 2)
            ],
            driver2: [
            int(d2["Races"]),
            int(d2["Wins"]),
            int(d2["Podiums"]),
            int(d2["Points"]),
            int(d2["DNFs"]),
            round(d2["Avg_Finish"], 2)
            ]
        })
    comparison_df = pd.DataFrame({
    "Metric": ["Races", "Wins", "Podiums", "Points", "DNFs", "Avg Finish"],
    driver1: [
        int(d1["Races"]),
        int(d1["Wins"]),
        int(d1["Podiums"]),
        int(d1["Points"]),
        int(d1["DNFs"]),
        round(d1["Avg_Finish"], 2)
    ],
    driver2: [
        int(d2["Races"]),
        int(d2["Wins"]),
        int(d2["Podiums"]),
        int(d2["Points"]),
        int(d2["DNFs"]),
        round(d2["Avg_Finish"], 2)
    ]
})
    comparison_df = pd.DataFrame({
    "Metric": [
        "Races",
        "Wins",
        "Podiums",
        "Points",
        "DNFs",
        "Avg Finish"
    ],

    driver1: [
        int(d1["Races"]),
        int(d1["Wins"]),
        int(d1["Podiums"]),
        int(d1["Points"]),
        int(d1["DNFs"]),
        round(d1["Avg_Finish"], 2)
    ],

    driver2: [
        int(d2["Races"]),
        int(d2["Wins"]),
        int(d2["Podiums"]),
        int(d2["Points"]),
        int(d2["DNFs"]),
        round(d2["Avg_Finish"], 2)
    ]
})
# ==========================
# DISPLAY TABLE
# ==========================
    st.markdown("### 📊 Head-to-Head Comparison")
    fig_dpi = px.bar(
    top_dpi,
    x="DPI",
    y="driver_name",
    orientation="h",
    color="DPI",
    title="🏆 Top 10 Drivers by Driver Performance Index"
    )

    fig_dpi.update_layout(
    yaxis=dict(categoryorder="total ascending"),
    height=600
    )
    st.dataframe(comparison_df)
    st.write(comparison_df)

    
# ── FOOTER ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
    "**Data Source:** [Ergast Motor Racing API](http://ergast.com/mrd/) | "
    "**Built with:** Python, Streamlit, Plotly | "
    "**GitHub:** [Your Repo Link]"
    )
st.markdown("---")
st.markdown("""
Data Source: Ergast Motor Racing API | Built with: Python, Streamlit, Plotly | GitHub: [F1 Analytics Repo](https://github.com/UtsavThakur0208/F1-Analytics)
""")
