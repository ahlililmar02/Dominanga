import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ollama
import numpy as np

df = pd.read_csv('dominanga5mnt.csv')

# Load data
#file_path = r"C:\Users\ahlil\Downloads\dominanga5mnt.csv"
#df = pd.read_csv(file_path)[['date', 'headwater_level', 'mv_power']]
df['date'] = pd.to_datetime(df['date'])

# Ensure it's sorted by date (assuming latest date is last row)
df = df.sort_values(by="date", ascending=True)

st.set_page_config(
    page_title="PLTMH Dominanga",
    page_icon=':ocean:',
    layout="wide",  # Ensures the content spans the full width
    initial_sidebar_state="expanded",
)

st.title(":ocean: PLTMH Dominanga")
st.write("")
st.write("")

#st.markdown("<h1 style='text-align: left; font-size: 26px;'>Current Value</h1>", unsafe_allow_html=True)



# Layout with Columns for Scorecards
col1, col2, col3 = st.columns([2, 1, 1])  # Adjust column width as needed
def get_indicator(value, previous_value):
    if pd.isna(value) or pd.isna(previous_value) or previous_value == 0:
        return "<span style='color: grey;font-size: 14px;vertical-align: right;'>= (N/A)</span>"  # No comparison available
    elif value > previous_value:
        change = ((value - previous_value) / abs(previous_value)) * 100
        return f"<span style='color: green;font-size: 14px;vertical-align: right;'>▲ {change:.2f}%</span>"  # Increased
    elif value < previous_value:
        change = ((previous_value - value) / abs(previous_value)) * 100
        return f"<span style='color: red; font-size: 14px;vertical-align: right;'>▼ {change:.2f}%</span>"  # Decreased
    else:
        return "<span style='color: grey;font-size: 14px;vertical-align: right;'>= 0.00%</span>"  # No change
    
def styled_text(title, value, classification, indicator=""):
    """Displays text with a properly centered indicator next to the value."""
    st.markdown(
        f"""
        <div style="text-align: left;">
            <p style="font-size: 16px; line-height: 1;">{title}</p>
            <div style="display: flex; align-items: center; gap: 6px;">
                <p style="font-size: 28px; font-weight: bold; margin: 0; line-height: 1;">{value}</p>
                <span style="font-size: 14px; font-weight: normal; display: flex; align-items: center; line-height: 1;">{indicator}</span>
            </div>
            <p style="font-size: 14px; color: grey; margin-top: 2px;">{classification}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Get the most recent values
# Last row contains the most recent values
latest_data = df.iloc[-1]   # Most recent data
previous_data = df.iloc[-2]

with col1:
    date_display = latest_data["date"].strftime('%b %d, %Y, %I:%M %p')
    st.markdown(
        f"""
        <div style="text-align: left;">
            <p style="font-size: 16px;  line-height: 1;">Time</p>
            <div style="display: flex; align-items: center; gap: 6px;">
            <p style="font-size: 28px; font-weight: bold; margin: 0; line-height: 1;">{date_display}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    mv_power_display = "No data" if pd.isna(latest_data['mv_power']) else f"{latest_data['mv_power']}"
    mv_class_display = latest_data['mv_class'] if pd.notna(latest_data['mv_class']) else "None"
    
    previous_mv_power = previous_data['mv_power'] if 'mv_power' in previous_data else None
    mv_indicator = get_indicator(latest_data['mv_power'], previous_mv_power)

    styled_text("Active Power", mv_power_display, mv_class_display, mv_indicator)

with col3:
    hl_class_display = latest_data['hl_class'] if pd.notna(latest_data['hl_class']) else "N/A"

    previous_headwater_level = previous_data['headwater_level'] if 'headwater_level' in previous_data else None
    hl_indicator = get_indicator(latest_data['headwater_level'], previous_headwater_level)

    styled_text("Head Water Level", f"{latest_data['headwater_level']:.2f}", hl_class_display, hl_indicator)

st.write("")
st.write("")

## Sidebar controls
with st.sidebar:
    st.header("Analysis Controls")
    # Date range selection
    date_range = st.date_input(
        "Select Date Range", 
        [df['date'].min(), df['date'].max()],
        min_value=df['date'].min(),
        max_value=df['date'].max()
    )

df_filtered = df[(df['date'] >= pd.to_datetime(date_range[0])) & 
                (df['date'] <= pd.to_datetime(date_range[1]))]

# Calculate scorecard values
avg_mv_power = df_filtered['mv_power'].mean()
min_mv_power = df_filtered['mv_power'].min()
max_mv_power = df_filtered['mv_power'].max()

# Layout with 4:1 ratio for the chart and scorecards
col_chart, col_space, col_scorecards = st.columns([2.8, 0.2, 1])
# Left side: Time Series Chart
with col_chart:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['headwater_level'],
                             mode='lines', name='headwater_level', line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df_filtered['date'], y=df_filtered['mv_power'],
                             mode='lines', name='mv_power', line=dict(color="red"), yaxis='y2'))
    
    fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis=dict(title="Head Water Level (m)", side="left"),
        yaxis2=dict(title="Active Power (mW)", overlaying='y', side="right"),
        margin=dict(l=0, r=40, t=20, b=30),
        height=400  # Adjust height to match scorecards
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.write("")

with col_space:
    st.markdown("<br><br>", unsafe_allow_html=True)

# Right side: Scorecards (inside a bordered box)
with col_scorecards:
    st.write("")
    st.markdown(f"""
        <style>
            .scorecard-item {{
                font-size: 18px;
                margin-bottom: 8px;
            }}
            .scorecard-value {{
                font-size: 24px;
                font-weight: bold;
            }}
        </style>
        <div style="text-align: left;">
            <div class="scorecard-item">Average Power<br><span class="scorecard-value">{avg_mv_power:.2f}</span></div>
            <div class="scorecard-item">Maximum Power<br><span class="scorecard-value">{max_mv_power:.2f}</span></div>
            <div class="scorecard-item">Minimum Power<br><span class="scorecard-value">{min_mv_power:.2f}</span></div>
        </div>
    """, unsafe_allow_html=True)

import plotly.express as px

df_table = df_filtered[['date', 'mv_power', 'headwater_level', 'class_detect']].sort_values(by='date', ascending=False)

# Create columns with a 2:1 ratio
col1, col2 = st.columns([2, 2])

# Display the table in col1
with col1:
    st.write("#### Recent Data")
    st.write("")
    st.dataframe(df_table, hide_index=True)

# Create a donut chart for mv_class distribution
with col2:
    st.write("#### Power Class Distribution")
    fig = px.pie(df_filtered, names='mv_class', hole=0.5, width=400, height=400)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🤖 AI-Powered Analysis")

if st.button("Run AI Analysis"):
    with st.spinner("Analyzing operational data..."):
        # Get anomaly counts
        anomaly_counts = df_filtered['class_detect'].value_counts().to_dict()
        
        # Calculate comprehensive statistics
        stats = f"""
        COMPLETE PLANT STATUS ANALYSIS ({date_range[0]} to {date_range[1]}):
        
        [POWER GENERATION]
        - Current MV Power: {df_filtered['mv_power'].iloc[-1]:.1f} MW
        - 24h Avg Power: {df_filtered['mv_power'].mean():.1f} MW
        - Power Factor: {df_filtered['mv_power_factor'].iloc[-1]:.2f}
        - Apparent Power: {df_filtered['mv_app_power'].iloc[-1]:.2f} MVA
        
        [WATER SYSTEM]
        - Current Headwater: {df_filtered['headwater_level'].iloc[-1]:.2f} m
        - Current Damwater: {df_filtered['damwater_level'].iloc[-1]:.2f} m
        - Avg Headwater: {df_filtered['headwater_level'].mean():.2f} m
        
        [ANOMALY DETECTION]
        - 'Power < Water Level': {anomaly_counts.get('Power < Water Level', 0)} cases
        - 'Power << Water Level': {anomaly_counts.get('Power << Water Level', 0)} cases
        - 'Power Not Detected': {anomaly_counts.get('Power Not Detected', 0)} cases
        - 'Water Level Not Detected': {anomaly_counts.get('Water Level Not Detected', 0)} cases
        """
        
        # Prepare detailed engineering prompt
        messages = [{
            "role": "user",
            "content": f"""As Chief Plant Engineer, analyze these operational parameters:
            {stats}
            
            Provide concise analysis in this format:
            
            1. POWER ANALYSIS:
               - Current efficiency status
               - Power vs Head Water Level pattern (note that head water level is the main component for power)
               - Apparent vs power comparison
            
            2. ANOMALY ANALYSIS:
               - Most critical anomaly type
               - Possible causes for each anomaly class
            
            3. RECOMMENDED ACTIONS:
               - Alert for immediate operational adjustments
               - Maintenance suggestions
            
            Use bullet points. Reference exact values from the data.
            """
        }]
        
        response = ollama.chat(model="deepseek-r1:1.5b", messages=messages)
        
        if "message" in response and "content" in response["message"]:
            st.write("### 🏭 PLANT ANALYSIS REPORT")
            st.write(response["message"]["content"])
            
            # Display critical anomalies
            anomaly_mask = df_filtered['class_detect'].isin([
                'Power < Water Level',
                'Power << Water Level',
                'Power Not Detected',
                'Water Level Not Detected'
            ])
            
            if anomaly_mask.any():
                st.write("### ⚠️ ANOMALY EVENT LOG")
                st.dataframe(
                    df_filtered[anomaly_mask][['date', 'class_detect', 'mv_power', 'headwater_level']]
                    .sort_values('date', ascending=False)
                    .head(10)  # Show only last 10 anomalies
                )
        else:
            st.error("Analysis failed. Please check your Ollama connection.")