import streamlit as st
import pandas as pd
import os
import streamlit.components.v1 as components
from datetime import datetime
from pathlib import Path

# === Styling ===
primary_color = "#2596be"

st.set_page_config(page_title="SKU Performance Forecast", layout="wide")
st.markdown(f"""
    <style>
        .main-header {{
            color: {primary_color};
            font-size: 32px;
            font-weight: bold;
        }}
        .metric-box {{
            background-color: skyblue;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            margin-bottom: 10px;
            text-align: center;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .metric-box h4 {{
            margin: 0;
            font-size: 16px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .metric-box h2 {{
            margin: 8px 0 0;
            font-size: 28px;
        }}
        .dataframe th, .dataframe td {{
            text-align: center !important;
        }}
    </style>
""", unsafe_allow_html=True)

# === Load Data ===
BASE_DIR = Path(__file__).parent
data_path = BASE_DIR / "Data" / "seasonality_prediction.csv"
df = pd.read_csv(data_path)

# === Sidebar Filters ===
st.sidebar.title("Selection Panel")

# Main Category
st.sidebar.markdown("<p style='margin-bottom: 4px; font-weight: 500;'>Select Category</p>", unsafe_allow_html=True)
selected_category = st.sidebar.selectbox("Select Category", df['Main_categ'].unique(), label_visibility="collapsed")
filtered_df = df[df['Main_categ'] == selected_category]

# SKU Parent
st.sidebar.markdown("<p style='margin-bottom: 4px; font-weight: 500;'>Select SKU</p>", unsafe_allow_html=True)
selected_sku_base = st.sidebar.selectbox("Select SKU", filtered_df['SKU without Size'].unique(), label_visibility="collapsed")
sku_data = filtered_df[filtered_df['SKU without Size'] == selected_sku_base].copy()

# === Month & Year Selector ===
st.sidebar.markdown("---")
st.sidebar.markdown("#### Select Forecast Period")
st.sidebar.markdown("<span style='font-size: 13px; color: grey;'>Choose the month and year you want to predict</span>", unsafe_allow_html=True)

months_map = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}

month_list = list(months_map.keys())
year_list = list(range(2023, datetime.now().year + 2))

selected_month_name = st.sidebar.selectbox("Month", month_list, index=datetime.now().month - 1)
selected_year = st.sidebar.selectbox("Year", year_list, index=year_list.index(datetime.now().year))

selected_month = months_map[selected_month_name]
selected_forecast_label = f"{selected_month_name} {selected_year}"

# Week selector
months = sorted([col for col in df.columns if col.startswith("Predicted_Week_")])
st.sidebar.markdown("##### Select Weeks")
selected_months = st.sidebar.multiselect("Optional", options=months, default=months)

# Festival Toggle
st.sidebar.markdown("##### Festival Toggle")
col_f1, col_f2 = st.sidebar.columns([4, 1])
festival_toggle = col_f1.toggle("🎉 Festival Weeks ON", value=True)

tooltip_html = """
<span style='position: relative; cursor: help;'>
  ℹ️
  <span style='visibility: hidden; width: 240px; background-color: #2596be; color: white; text-align: left;
               border-radius: 6px; padding: 8px; position: absolute; z-index: 1; top: -5px; left: 20px;
               opacity: 0; transition: opacity 0.3s; font-size: 12px;'>
    Enable this if the selected month includes a major sale or festival period.
  </span>
</span>

<script>
  const infoIcon = window.parent.document.querySelectorAll('span[style*="cursor: help"]');
  if(infoIcon.length > 0){
    infoIcon.forEach(el => {
      const tooltip = el.querySelector('span:nth-child(2)');
      el.onmouseover = () => tooltip.style.visibility = tooltip.style.opacity = 'visible';
      el.onmouseout = () => tooltip.style.visibility = tooltip.style.opacity = 'hidden';
    });
  }
</script>
"""
col_f2.markdown(tooltip_html, unsafe_allow_html=True)

# === Main View ===
st.markdown("<div class='main-header'>📈 DemandSense</div>", unsafe_allow_html=True)
st.markdown(f"### SKU - `{selected_sku_base}`")

if sku_data.empty:
    st.warning("No data available for selected SKU.")
else:
    pred_cols = selected_months if selected_months else [col for col in df.columns if col.startswith("Predicted_Week_")]
    sku_data['Total_Predicted'] = sku_data[pred_cols].sum(axis=1)
    sku_data['Priority_Message'] = sku_data.apply(lambda row: 
        f"Critical - Reorder by {pd.to_datetime(row['SOH Date']).date()}" if 'critical' in row['Priority'].lower() else
        f"Urgent - Attention by {pd.to_datetime(row['SOH Date']).date()}" if 'urgent' in row['Priority'].lower() else
        f"✅ No Action Needed – Relax, stock available till {pd.to_datetime(row['SOH Date']).date()}", axis=1)

    total_pred = sku_data['Total_Predicted'].sum()
    total_stocks = sku_data['Stocks'].sum()
    avg_soh = sku_data['SOH days'].mean()
    num_sizes = sku_data['Size'].nunique()
    max_priority = sku_data['Priority'].iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.markdown(f"<div class='metric-box'><h4>Total Predicted</h4><h2 style='color:{primary_color};'>{int(total_pred)}</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-box'><h4>Sizes Available</h4><h2 style='color:{primary_color};'>{num_sizes}</h2></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-box'><h4>Total Stocks</h4><h2 style='color:{primary_color};'>{int(total_stocks)}</h2></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='metric-box'><h4>Avg. SOH Days</h4><h2 style='color:{primary_color};'>{int(avg_soh)}</h2></div>", unsafe_allow_html=True)
    col5.markdown(f"<div class='metric-box'><h4>Max Priority</h4><h2 style='color:{primary_color};'>{max_priority}</h2></div>", unsafe_allow_html=True)

    soh_date = pd.to_datetime(sku_data['SOH Date'].values[0]).date()
    priority = sku_data['Priority'].values[0].lower()
    st.markdown("<br>", unsafe_allow_html=True)
    if "critical" in priority:
        st.error(f"❗ **Critical**: Top priority action needed. Stock available only till **{soh_date}**.")
    elif "urgent" in priority:
        st.warning(f"⚠️ **Urgent**: Requires attention. Reorder advised after **{soh_date}**.")
    else:
        st.info(f"✅ **No Action Needed**: Relax, stock available till **{soh_date}**.")

    def highlight_priority(row):
        return [
            'color: red; font-weight: bold;' if row['Priority'].lower() == 'critical' and col == 'Priority' else
            'color: orange; font-weight: bold;' if row['Priority'].lower() == 'urgent' and col == 'Priority' else
            'color: green; font-weight: bold;' if 'no' in row['Priority'].lower() and col == 'Priority' else
            '' for col in row.index
        ]

    table_df = sku_data[['SKU Code', 'Size', 'Total_Predicted', 'Priority', 'SOH days', 'Stocks', 'SOH Date', 'Priority_Message']].copy()
    table_df['SOH Date'] = pd.to_datetime(table_df['SOH Date']).dt.date
    table_df['Total_Predicted'] = table_df['Total_Predicted'].astype(int)
    table_df['SOH days'] = table_df['SOH days'].astype(int)
    table_df['Stocks'] = table_df['Stocks'].astype(int)

    st.markdown("### 📦 Size-wise Forecast for Selected SKU")
    styled_table = table_df.style.apply(highlight_priority, axis=1)
    st.dataframe(styled_table, width='stretch')

    with st.expander("🔍 Weekly Predicted Breakdown"):
        week_df = sku_data[['SKU Code', 'Size'] + pred_cols].copy()
        week_df[pred_cols] = week_df[pred_cols].astype(int)
        week_df = week_df.set_index(['SKU Code', 'Size'])
        st.dataframe(week_df, width='stretch')
