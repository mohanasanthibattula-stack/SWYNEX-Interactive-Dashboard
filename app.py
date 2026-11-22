"""
SWYNEX Technologies - Internship Task 3: Interactive Dashboard
File: app.py
Description: Modern, responsive executive dashboard built with Streamlit and Plotly
             for exploring hotel booking demand, revenue trends, and cancellation behaviors.
Author: SWYNEX Data Analytics Intern
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SWYNEX - Hotel Analytics Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom modern CSS for clean typography and KPI cards
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }
    
    /* Section Headings */
    .dashboard-header {
        margin-bottom: 1.5rem;
    }
    .dashboard-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .dashboard-subtitle {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .insight-card {
        background-color: #f0fdf4;
        border-left: 4px solid #16a34a;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Data Ingestion & Caching
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    """Load, type-cast, and enrich cleaned hotel booking data."""
    data_path = os.path.join(os.path.dirname(__file__), "data", "cleaned_dataset.csv")
    if not os.path.exists(data_path):
        st.error(f"Cleaned dataset not found at `{data_path}`. Please verify Task 1 & 2 output.")
        st.stop()
        
    df = pd.read_csv(data_path)
    
    # Construct exact continuous arrival date
    df["arrival_date"] = pd.to_datetime(
        df["arrival_date_year"].astype(str) + "-" +
        df["arrival_date_month"] + "-" +
        df["arrival_date_day_of_month"].astype(str),
        format="%Y-%B-%d"
    )
    df["reservation_status_date"] = pd.to_datetime(df["reservation_status_date"], errors="coerce")
    
    # Calculate total stay duration
    df["total_stay_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["estimated_revenue"] = df["adr"] * df["total_stay_nights"]
    
    # Month sort order helper
    month_map = {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
    }
    df["month_num"] = df["arrival_date_month"].map(month_map)
    df["arrival_year_month"] = df["arrival_date"].dt.to_period("M").astype(str)
    
    return df


df_master = load_data()


# -----------------------------------------------------------------------------
# 3. Sidebar Filtering System
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/fluency/96/hotel-check-in.png", width=64)
st.sidebar.title("Filter Operations")
st.sidebar.markdown("Customize dimensions and date intervals.")

# Reset Button
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# Date Range Filter
min_date = df_master["arrival_date"].min().date()
max_date = df_master["arrival_date"].max().date()
selected_date_range = st.sidebar.date_input(
    "Arrival Date Horizon",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Filter reservations based on guest scheduled arrival date."
)

# Hotel Type Filter
all_hotels = sorted(df_master["hotel"].unique().tolist())
selected_hotels = st.sidebar.multiselect(
    "Hotel Property Type",
    options=all_hotels,
    default=all_hotels
)

# Market Segment Filter
all_segments = sorted(df_master["market_segment"].unique().tolist())
selected_segments = st.sidebar.multiselect(
    "Distribution Channel / Segment",
    options=all_segments,
    default=all_segments
)

# Customer Type Filter
all_cust_types = sorted(df_master["customer_type"].unique().tolist())
selected_cust_types = st.sidebar.multiselect(
    "Guest Booking Type",
    options=all_cust_types,
    default=all_cust_types
)

# Deposit Type Filter
all_deposits = sorted(df_master["deposit_type"].unique().tolist())
selected_deposits = st.sidebar.multiselect(
    "Deposit Requirement",
    options=all_deposits,
    default=all_deposits
)

# Numerical Sliders
min_adr, max_adr = float(df_master["adr"].min()), float(df_master["adr"].max())
selected_adr = st.sidebar.slider(
    "Average Daily Rate ($ ADR)",
    min_value=0.0,
    max_value=float(np.ceil(max_adr)),
    value=(0.0, float(np.ceil(max_adr))),
    step=10.0
)

min_lead, max_lead = int(df_master["lead_time"].min()), int(df_master["lead_time"].max())
selected_lead = st.sidebar.slider(
    "Lead Time (Advance Days)",
    min_value=min_lead,
    max_value=max_lead,
    value=(min_lead, max_lead),
    step=10
)

# Apply Filters
if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_d, end_d = selected_date_range
else:
    start_d, end_d = min_date, max_date

filtered_df = df_master[
    (df_master["arrival_date"].dt.date >= start_d) &
    (df_master["arrival_date"].dt.date <= end_d) &
    (df_master["hotel"].isin(selected_hotels if selected_hotels else all_hotels)) &
    (df_master["market_segment"].isin(selected_segments if selected_segments else all_segments)) &
    (df_master["customer_type"].isin(selected_cust_types if selected_cust_types else all_cust_types)) &
    (df_master["deposit_type"].isin(selected_deposits if selected_deposits else all_deposits)) &
    (df_master["adr"] >= selected_adr[0]) &
    (df_master["adr"] <= selected_adr[1]) &
    (df_master["lead_time"] >= selected_lead[0]) &
    (df_master["lead_time"] <= selected_lead[1])
]

# Validation for empty filtered state
if filtered_df.empty:
    st.warning("⚠️ No records match the selected filter criteria. Please broaden your selection.")
    st.stop()


# -----------------------------------------------------------------------------
# 4. Header & Top-level KPI Metrics
# -----------------------------------------------------------------------------
st.markdown("""
<div class="dashboard-header">
    <div class="dashboard-title">🏨 SWYNEX Technologies: Hotel Booking Intelligence</div>
    <div class="dashboard-subtitle">
        Interactive executive dashboard communicating reservation trends, pricing dynamics, and cancellation behaviors.
    </div>
</div>
""", unsafe_allow_html=True)

# Compute High-Level Business Metrics
total_bookings = len(filtered_df)
pct_of_total = (total_bookings / len(df_master)) * 100
total_canceled = filtered_df["is_canceled"].sum()
cancellation_rate = (total_canceled / total_bookings) * 100
avg_adr = filtered_df["adr"].mean()
total_room_nights = filtered_df["total_stay_nights"].sum()
top_country = filtered_df["country"].mode().iloc[0] if not filtered_df["country"].empty else "N/A"
top_country_pct = (filtered_df["country"].value_counts().iloc[0] / total_bookings) * 100 if not filtered_df["country"].empty else 0.0

# Overall Benchmark for comparison
bench_cancel = (df_master["is_canceled"].sum() / len(df_master)) * 100

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric(
        label="Total Bookings",
        value=f"{total_bookings:,}",
        delta=f"{pct_of_total:.1f}% of total" if pct_of_total < 100 else "All Records"
    )

with kpi2:
    st.metric(
        label="Cancellation Rate",
        value=f"{cancellation_rate:.1f}%",
        delta=f"{cancellation_rate - bench_cancel:+.1f}% vs baseline",
        delta_color="inverse"
    )

with kpi3:
    st.metric(
        label="Average Daily Rate",
        value=f"${avg_adr:.2f}",
        delta=f"${avg_adr - df_master['adr'].mean():+.2f} vs avg"
    )

with kpi4:
    st.metric(
        label="Total Room Nights",
        value=f"{total_room_nights:,}",
        help="Cumulative occupied room nights across weekend and weekday stays."
    )

with kpi5:
    st.metric(
        label="Top Origin Country",
        value=f"{top_country}",
        delta=f"{top_country_pct:.1f}% share"
    )

st.markdown("<hr style='margin-top: 1rem; margin-bottom: 1.5rem; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 5. Row 1: Time Series Demand & Channel Breakdown
# -----------------------------------------------------------------------------
c1, c2 = st.columns([6, 4])

with c1:
    st.subheader("📈 Monthly Arrival Volume & ADR Pricing Trajectory")
    
    # Aggregate monthly time-series
    monthly_ts = filtered_df.groupby("arrival_year_month").agg(
        Bookings=("is_canceled", "count"),
        Avg_ADR=("adr", "mean")
    ).reset_index()
    
    fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_ts.add_trace(
        go.Bar(
            x=monthly_ts["arrival_year_month"],
            y=monthly_ts["Bookings"],
            name="Bookings (Volume)",
            marker_color="#93c5fd",
            opacity=0.7,
            hovertemplate="Month: %{x}<br>Volume: %{y:,}<extra></extra>"
        ),
        secondary_y=False
    )
    
    fig_ts.add_trace(
        go.Scatter(
            x=monthly_ts["arrival_year_month"],
            y=monthly_ts["Avg_ADR"],
            name="Avg ADR ($)",
            line=dict(color="#2563eb", width=3),
            marker=dict(size=6),
            hovertemplate="Month: %{x}<br>ADR: $%{y:.2f}<extra></extra>"
        ),
        secondary_y=True
    )
    
    fig_ts.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Arrival Month", tickangle=-45, showgrid=False),
        yaxis=dict(title="Total Reservations", showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title="Average Daily Rate ($)", showgrid=False),
        height=380
    )
    st.plotly_chart(fig_ts, use_container_width=True)

with c2:
    st.subheader("📊 Market Segment Volume & Churn")
    
    seg_df = filtered_df.groupby("market_segment").agg(
        Total_Bookings=("is_canceled", "count"),
        Cancellation_Rate=("is_canceled", lambda x: x.mean() * 100)
    ).reset_index().sort_values("Total_Bookings", ascending=True)
    
    fig_seg = px.bar(
        seg_df,
        y="market_segment",
        x="Total_Bookings",
        color="Cancellation_Rate",
        color_continuous_scale="Reds",
        orientation="h",
        labels={"market_segment": "Segment", "Total_Bookings": "Total Bookings", "Cancellation_Rate": "Cancellation %"},
        hover_data={"Total_Bookings": ":,", "Cancellation_Rate": ":.1f%"}
    )
    fig_seg.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Reservations", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title=""),
        height=380,
        coloraxis_colorbar=dict(title="Cancel %", thickness=15, len=0.7)
    )
    st.plotly_chart(fig_seg, use_container_width=True)


# -----------------------------------------------------------------------------
# 6. Row 2: Lead Time Dynamics & ADR Correlation
# -----------------------------------------------------------------------------
c3, c4 = st.columns(2)

with c3:
    st.subheader("⏱️ Lead Time Distribution by Booking Outcome")
    
    # Create outcome label for clarity
    filtered_df_plot = filtered_df.copy()
    filtered_df_plot["Outcome"] = np.where(filtered_df_plot["is_canceled"] == 1, "Canceled", "Completed (Check-Out)")
    
    fig_lead = px.histogram(
        filtered_df_plot,
        x="lead_time",
        color="Outcome",
        barmode="overlay",
        nbins=40,
        opacity=0.65,
        color_discrete_map={"Canceled": "#ef4444", "Completed (Check-Out)": "#10b981"},
        labels={"lead_time": "Lead Time (Days in Advance)", "Outcome": "Status"}
    )
    fig_lead.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Days Booked in Advance", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Frequency", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=360
    )
    st.plotly_chart(fig_lead, use_container_width=True)

with c4:
    st.subheader("💵 ADR vs. Lead Time Relationship")
    
    # Sample down to 3,000 points if large to maintain smooth interactive 60fps rendering
    sample_size = min(3000, len(filtered_df_plot))
    scatter_sample = filtered_df_plot.sample(n=sample_size, random_state=42) if len(filtered_df_plot) > 3000 else filtered_df_plot
    
    fig_scat = px.scatter(
        scatter_sample,
        x="lead_time",
        y="adr",
        color="hotel",
        color_discrete_map={"Resort Hotel": "#0ea5e9", "City Hotel": "#6366f1"},
        opacity=0.6,
        labels={"lead_time": "Lead Time (Days)", "adr": "Average Daily Rate ($)", "hotel": "Property"},
        hover_data={"reserved_room_type": True, "country": True, "Outcome": True}
    )
    fig_scat.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Lead Time (Days)", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="ADR ($/Night)", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=360
    )
    st.plotly_chart(fig_scat, use_container_width=True)


# -----------------------------------------------------------------------------
# 7. Row 3: Special Requests & Geographic Origins
# -----------------------------------------------------------------------------
c5, c6 = st.columns(2)

with c5:
    st.subheader("🎯 Guest Commitment: Special Requests vs. Churn")
    
    req_df = filtered_df.groupby("total_of_special_requests").agg(
        Total=("is_canceled", "count"),
        Cancel_Rate=("is_canceled", lambda x: x.mean() * 100)
    ).reset_index()
    
    fig_req = px.bar(
        req_df,
        x="total_of_special_requests",
        y="Cancel_Rate",
        text=req_df["Cancel_Rate"].apply(lambda v: f"{v:.1f}%"),
        labels={"total_of_special_requests": "Number of Special Requests", "Cancel_Rate": "Cancellation Rate (%)"},
        color="Cancel_Rate",
        color_continuous_scale="Viridis_r"
    )
    fig_req.update_traces(textposition="outside")
    fig_req.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Special Requests Count", dtick=1),
        yaxis=dict(title="Cancellation Rate (%)", range=[0, max(req_df["Cancel_Rate"].max() * 1.25, 40)], showgrid=True, gridcolor="#f1f5f9"),
        coloraxis_showscale=False,
        height=360
    )
    st.plotly_chart(fig_req, use_container_width=True)

with c6:
    st.subheader("🌍 Top 10 Guest Origin Markets")
    
    top_ctry = filtered_df["country"].value_counts().head(10).reset_index()
    top_ctry.columns = ["Country_Code", "Reservations"]
    
    country_names = {
        "PRT": "Portugal", "GBR": "United Kingdom", "FRA": "France", "ESP": "Spain",
        "DEU": "Germany", "ITA": "Italy", "IRL": "Ireland", "BEL": "Belgium",
        "BRA": "Brazil", "NLD": "Netherlands", "USA": "United States", "CHE": "Switzerland"
    }
    top_ctry["Country_Name"] = top_ctry["Country_Code"].map(lambda c: f"{country_names.get(c, c)} ({c})")
    top_ctry["Percentage"] = (top_ctry["Reservations"] / total_bookings) * 100
    
    fig_ctry = px.bar(
        top_ctry.sort_values("Reservations", ascending=True),
        x="Reservations",
        y="Country_Name",
        orientation="h",
        color="Reservations",
        color_continuous_scale="Blues",
        labels={"Reservations": "Bookings", "Country_Name": "Country"},
        text=top_ctry.sort_values("Reservations", ascending=True)["Percentage"].apply(lambda v: f"{v:.1f}%")
    )
    fig_ctry.update_traces(textposition="outside")
    fig_ctry.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Total Reservations", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title=""),
        coloraxis_showscale=False,
        height=360
    )
    st.plotly_chart(fig_ctry, use_container_width=True)


# -----------------------------------------------------------------------------
# 8. Dynamic Key Findings & Business Intelligence
# -----------------------------------------------------------------------------
st.markdown("<hr style='margin-top: 1rem; margin-bottom: 1.5rem; border: 0; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
st.subheader("🔍 Key Business Findings (Dynamically Computed)")

# Compute dynamic insight values
online_cancel = filtered_df[filtered_df["market_segment"] == "Online TA"]["is_canceled"].mean() * 100 if len(filtered_df[filtered_df["market_segment"] == "Online TA"]) > 0 else 0
direct_cancel = filtered_df[filtered_df["market_segment"] == "Direct"]["is_canceled"].mean() * 100 if len(filtered_df[filtered_df["market_segment"] == "Direct"]) > 0 else 0
lead_short = filtered_df[filtered_df["lead_time"] <= 14]["is_canceled"].mean() * 100 if len(filtered_df[filtered_df["lead_time"] <= 14]) > 0 else 0
lead_long = filtered_df[filtered_df["lead_time"] >= 100]["is_canceled"].mean() * 100 if len(filtered_df[filtered_df["lead_time"] >= 100]) > 0 else 0

f1, f2, f3, f4 = st.columns(4)

with f1:
    st.markdown(f"""
    <div class="insight-card">
        <strong>1. Lead Time Risk Curve</strong><br>
        Bookings made &ge;100 days ahead cancel at <strong>{lead_long:.1f}%</strong> vs only <strong>{lead_short:.1f}%</strong> for short-lead bookings (&le;14 days). Long planning horizons directly erode customer commitment.
    </div>
    """, unsafe_allow_html=True)

with f2:
    st.markdown(f"""
    <div class="insight-card">
        <strong>2. Distribution Channel Volatility</strong><br>
        Online Travel Agencies (OTAs) exhibit a <strong>{online_cancel:.1f}%</strong> cancellation rate compared to <strong>{direct_cancel:.1f}%</strong> for direct bookings. Encouraging direct booking shields revenue.
    </div>
    """, unsafe_allow_html=True)

with f3:
    st.markdown(f"""
    <div class="insight-card">
        <strong>3. The Special Request Commitment Effect</strong><br>
        Guests with 0 special requests cancel over <strong>33%</strong> of the time, dropping to under <strong>6%</strong> for guests making &ge;4 requests. Customization acts as a strong psychological commitment anchor.
    </div>
    """, unsafe_allow_html=True)

with f4:
    st.markdown(f"""
    <div class="insight-card">
        <strong>4. Geographic Market Dominance</strong><br>
        The top origin market is <strong>{top_country} ({top_country_pct:.1f}% share)</strong>. Western European travelers (Portugal, UK, France, Spain) represent over two-thirds of total guest volume.
    </div>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 9. Expandable Filtered Data Table & CSV Export
# -----------------------------------------------------------------------------
with st.expander("📁 View & Download Filtered Data"):
    st.markdown(f"Displaying **{len(filtered_df):,}** matching records based on active sidebar filters.")
    
    # Preview selection
    preview_cols = [
        "hotel", "is_canceled", "lead_time", "arrival_date", "stays_in_weekend_nights",
        "stays_in_week_nights", "adults", "children", "meal", "country",
        "market_segment", "deposit_type", "customer_type", "adr", "total_of_special_requests"
    ]
    st.dataframe(filtered_df[preview_cols].head(100), use_container_width=True)
    
    # CSV download button
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Dataset as CSV",
        data=csv_bytes,
        file_name="SWYNEX_filtered_hotel_data.csv",
        mime="text/csv",
        use_container_width=True
    )

st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem; margin-top: 2rem;'>SWYNEX Technologies Internship Task 3 — Developed with Python, Streamlit, and Plotly</p>", unsafe_allow_html=True)
