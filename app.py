import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(
    page_title="Nasdaq Composite Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for extra polish beyond the base theme ---
st.markdown("""
    <style>
        /* Sidebar background slightly darker than main area for contrast */
        section[data-testid="stSidebar"] {
            background-color: #10141c;
            border-right: 1px solid #1f2937;
        }

        /* Sidebar title */
        .sidebar-title {
            font-size: 22px;
            font-weight: 700;
            color: #3B82F6;
            padding-bottom: 0px;
            margin-bottom: 0px;
        }
        .sidebar-subtitle {
            font-size: 13px;
            color: #8b949e;
            margin-top: 0px;
            padding-top: 0px;
            margin-bottom: 20px;
        }

        /* Radio buttons styled like nav links */
        div[role="radiogroup"] > label {
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 4px;
            transition: background-color 0.2s ease;
        }
        div[role="radiogroup"] > label:hover {
            background-color: #1c2333;
        }

        /* Main content headers */
        h1, h2, h3 {
            color: #E6EDF3;
        }

        /* Accent color for metrics */
        [data-testid="stMetricValue"] {
            color: #3B82F6;
        }
    </style>
""", unsafe_allow_html=True)

# --- Cached data loading: only re-pulls from Yahoo Finance once per hour ---
@st.cache_data(ttl=3600)
def load_nasdaq_data():
    df = yf.download("^IXIC", period="15y", auto_adjust=False, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index.name = "Date"
    df.reset_index(inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])

    # Derived columns used across the dashboard
    df["Daily_Return"] = df["Adj Close"].pct_change()
    df["MA50"] = df["Adj Close"].rolling(50).mean()
    df["MA100"] = df["Adj Close"].rolling(100).mean()
    df["MA200"] = df["Adj Close"].rolling(200).mean()
    return df


nasdaq_df = load_nasdaq_data()

# --- Major events (real scanner-derived dates) ---
EVENTS = [
    ('Debt Ceiling Crisis 2011', '2011-07-22', '2011-10-03', 'gray'),
    ('European Debt Crisis Resurgence', '2012-03-26', '2012-06-01', 'slategray'),
    ('Fiscal Cliff Uncertainty', '2012-09-14', '2012-11-15', 'slategray'),
    ('2015-16 Selloff', '2015-07-20', '2016-02-11', 'gray'),
    ('2018 Q4 Selloff', '2018-08-29', '2018-12-24', 'darkorange'),
    ('2019 Selloff', '2019-05-03', '2019-06-03', 'slategray'),
    ('COVID Crash', '2020-02-19', '2020-03-23', 'red'),
    ('COVID Recovery', '2020-03-23', '2021-11-19', 'green'),
    ('Sept 2020 Selloff', '2020-09-02', '2020-09-23', 'slategray'),
    ('Feb 2021 Selloff', '2021-02-12', '2021-03-08', 'slategray'),
    ('2022 Bear Market', '2021-11-19', '2022-12-28', 'firebrick'),
    ('AI-Driven Rally', '2023-01-01', str(nasdaq_df['Date'].max().date()), 'lightgreen'),
    ('Yen Carry Trade Unwind', '2024-07-10', '2024-08-07', 'purple'),
    ('Liberation Day Tariff Crash', '2024-12-16', '2025-04-08', 'darkred'),
    ('2026 Tariff Renewal Selloff', '2025-10-29', '2026-03-30', 'orangered'),
]

# --- Brief plain-language descriptions for each event, shown as a reference below the chart ---
EVENT_DESCRIPTIONS = {
    'Debt Ceiling Crisis 2011': "US Congress fought over raising the debt ceiling, leading to the first-ever US credit rating downgrade (S&P) and a sharp selloff on default fears.",
    'European Debt Crisis Resurgence': "Spain and Italy's bond yields spiked amid fears they couldn't manage their debt, with renewed talk of Greece exiting the Eurozone.",
    'Fiscal Cliff Uncertainty': "Automatic US tax hikes and spending cuts were set to hit simultaneously in 2013 unless Congress acted, spooking markets ahead of the presidential election.",
    '2015-16 Selloff': "China's economic slowdown and a surprise currency devaluation, combined with a collapse in oil prices, triggered a global growth scare.",
    '2018 Q4 Selloff': "The Fed's rate hikes combined with escalating US-China trade war tensions drove a sharp, fast decline into Christmas Eve 2018.",
    '2019 Selloff': "US-China trade talks broke down in May 2019, with both sides announcing new tariffs, reigniting trade war fears from the prior year.",
    'COVID Crash': "The fastest crash in the dataset — global lockdowns and total economic uncertainty from the COVID-19 pandemic triggered a ~30% decline in about a month.",
    'COVID Recovery': "Massive fiscal/monetary stimulus and near-zero interest rates fueled one of the strongest bull runs in market history, especially for tech stocks.",
    'Sept 2020 Selloff': "A sharp but short-lived pullback in high-flying tech stocks after their explosive COVID-recovery run, as valuations were questioned.",
    'Feb 2021 Selloff': "Rising government bond yields spooked growth/tech stocks, which are especially sensitive to higher expected interest rates.",
    '2022 Bear Market': "The Fed's aggressive rate hikes to fight decades-high inflation triggered the deepest and longest drawdown in the dataset — didn't fully recover until early 2024.",
    'AI-Driven Rally': "A small group of mega-cap tech companies (Nvidia, Microsoft, and others) led a powerful rally driven by enthusiasm for AI.",
    'Yen Carry Trade Unwind': "A surprise Bank of Japan rate hike combined with a weak US jobs report triggered a rapid global unwind of yen-funded trades, hitting momentum/tech stocks hard.",
    'Liberation Day Tariff Crash': "Sweeping new US tariff announcements in April 2025 sparked the largest global selloff since the COVID crash.",
    '2026 Tariff Renewal Selloff': "Fresh US trade policy threats against major trading partners reignited the same fears as the prior year's tariff shock.",
}





def build_price_trend_chart(df, events, log_scale=True, selected_event="None"):
    fig = go.Figure()

    y_min = df['Adj Close'].min() * 0.9
    y_max = df['Adj Close'].max() * 1.1

    # Shaded event region (only the selected one, drawn first so price line sits on top)
    if selected_event != "None":
        for name, start, end, color in events:
            if name == selected_event:
                fig.add_trace(go.Scatter(
                    x=[start, start, end, end],
                    y=[y_min, y_max, y_max, y_min],
                    fill='toself',
                    fillcolor=color,
                    opacity=0.5,
                    mode='none',
                    showlegend=False,
                    hoverinfo='skip',
                ))

    # Price line
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Adj Close'],
        mode='lines', name='Nasdaq Composite',
        line=dict(color='#E6EDF3', width=1.3),
    ))

    # Moving averages
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA50'], mode='lines',
                              name='50-day MA', line=dict(color='#3B82F6', width=1)))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA200'], mode='lines',
                              name='200-day MA', line=dict(color='#F59E0B', width=1.5)))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title='Nasdaq Composite - 15 Year Price Trend',
        xaxis_title='Date',
        yaxis_title='Price',
        yaxis_type='log' if log_scale else 'linear',
        hovermode='x unified',
        height=600,
        xaxis=dict(rangeslider=dict(visible=True), type='date'),
        legend=dict(orientation='h', y=1.02, x=0),
    )
    return fig


# --- Seasonality data prep ---
@st.cache_data(ttl=3600)
def compute_seasonality(df):
    data = df.copy()
    data['Year'] = data['Date'].dt.year
    data['Month'] = data['Date'].dt.month
    data['MonthName'] = data['Date'].dt.strftime('%b')
    data['DayOfWeek'] = data['Date'].dt.day_name()
    data['YearMonth'] = data['Date'].dt.to_period('M')

    # Monthly returns (first trading day to last trading day of each YearMonth)
    monthly = data.groupby('YearMonth')['Adj Close'].agg(['first', 'last'])
    monthly['Return_%'] = (monthly['last'] - monthly['first']) / monthly['first'] * 100
    monthly = monthly.reset_index()
    monthly['Month'] = monthly['YearMonth'].dt.month
    monthly['MonthName'] = monthly['YearMonth'].dt.strftime('%b')
    monthly['Year'] = monthly['YearMonth'].dt.year

    # Average return per calendar month, across all years
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_avg = monthly.groupby('MonthName')['Return_%'].agg(['mean', 'std', 'count']).reindex(month_order).reset_index()

    # Day-of-week average daily return
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    dow_avg = data.groupby('DayOfWeek')['Daily_Return'].mean().reindex(dow_order) * 100
    dow_avg = dow_avg.reset_index()
    dow_avg.columns = ['DayOfWeek', 'Avg_Return_%']

    return monthly, monthly_avg, dow_avg


def build_monthly_seasonality_chart(monthly_avg):
    colors = ['#22C55E' if v >= 0 else '#EF4444' for v in monthly_avg['mean']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_avg['MonthName'],
        y=monthly_avg['mean'],
        error_y=dict(type='data', array=monthly_avg['std'], visible=True, color='#8b949e'),
        marker_color=colors,
        text=monthly_avg['mean'].round(2),
        texttemplate='%{text}%',
        textposition='outside',
        hovertemplate='%{x}<br>Avg Return: %{y:.2f}%<extra></extra>',
    ))
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title='Average Return by Calendar Month (Across 15 Years)',
        xaxis_title='Month',
        yaxis_title='Average Return (%)',
        height=500,
    )
    fig.add_hline(y=0, line_width=1, line_color='#8b949e')
    return fig


def build_seasonality_heatmap(monthly):
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    pivot = monthly.pivot(index='Year', columns='MonthName', values='Return_%')
    pivot = pivot.reindex(columns=month_order)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index.astype(str),
        colorscale='RdYlGn',
        zmid=0,
        text=pivot.values.round(1),
        texttemplate='%{text}',
        textfont=dict(size=10),
        hovertemplate='Year: %{y}<br>Month: %{x}<br>Return: %{z:.2f}%<extra></extra>',
        colorbar=dict(title='Return %'),
    ))
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title='Monthly Returns Heatmap by Year',
        height=550,
    )
    return fig


def build_dow_chart(dow_avg):
    colors = ['#22C55E' if v >= 0 else '#EF4444' for v in dow_avg['Avg_Return_%']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dow_avg['DayOfWeek'],
        y=dow_avg['Avg_Return_%'],
        marker_color=colors,
        text=dow_avg['Avg_Return_%'].round(3),
        texttemplate='%{text}%',
        textposition='outside',
    ))
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title='Average Daily Return by Day of Week',
        xaxis_title='Day of Week',
        yaxis_title='Average Daily Return (%)',
        height=450,
    )
    fig.add_hline(y=0, line_width=1, line_color='#8b949e')
    return fig
# --- Sidebar navigation ---
with st.sidebar:
    st.markdown('<p class="sidebar-title">📊 Nasdaq Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-subtitle">15-Year Market Analysis</p>', unsafe_allow_html=True)

    page = st.radio(
        label="Navigation",
        options=["Price and Trends", "Seasonality"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Data source: Yahoo Finance (yfinance)")
    st.caption("Built with Streamlit + Plotly")


# --- Main content, routed by sidebar selection ---
if page == "Price and Trends":
    st.title("Price and Trends")
    st.caption("Nasdaq Composite (^IXIC) — 15 year daily price history")

    col1, col2 = st.columns([1, 3])
    with col1:
        scale_choice = st.radio("Y-axis scale", ["Log", "Linear"], horizontal=True)
    with col2:
        event_names = ["None"] + [e[0] for e in EVENTS]
        selected_event = st.selectbox("Highlight a major event", event_names)

    fig = build_price_trend_chart(
        nasdaq_df,
        EVENTS,
        log_scale=(scale_choice == "Log"),
        selected_event=selected_event,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Quick stat callouts
    latest_price = nasdaq_df['Adj Close'].iloc[-1]
    start_price = nasdaq_df['Adj Close'].iloc[0]
    total_return = (latest_price - start_price) / start_price * 100

    m1, m2, m3 = st.columns(3)
    m1.metric("Current Price", f"{latest_price:,.2f}")
    m2.metric("15-Year Total Return", f"{total_return:,.1f}%")
    m3.metric("All-Time High", f"{nasdaq_df['Adj Close'].max():,.2f}")

    st.markdown("---")
    st.subheader("What are these events?")
    st.caption("Brief context on each major event shown in the dropdown above.")

    for name, start, end, color in EVENTS:
        with st.expander(f"{name}  ({start} → {end})"):
            st.write(EVENT_DESCRIPTIONS.get(name, "No description available."))

elif page == "Seasonality":
    st.title("Seasonality")
    st.caption("Do certain months or days of the week show consistent patterns?")

    monthly, monthly_avg, dow_avg = compute_seasonality(nasdaq_df)

    st.plotly_chart(build_monthly_seasonality_chart(monthly_avg), use_container_width=True)
    st.caption(
        "Each bar is a month's average return across all 15 years. The error bars show how much "
        "that month's return swings year to year — a small error bar means a more consistent pattern; "
        "a large one means the average is likely skewed by a single unusual year."
    )

    st.plotly_chart(build_seasonality_heatmap(monthly), use_container_width=True)
    st.caption(
        "Every cell is one month's actual return in one specific year. Use this to double-check the "
        "chart above — does a month look consistently good or bad across most years, or was it just one?"
    )

    st.plotly_chart(build_dow_chart(dow_avg), use_container_width=True)
    st.caption(
        "Average return by weekday. Any differences here are small and not reliable enough to trade on."
    )