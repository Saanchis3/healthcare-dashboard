import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff

# ======================
# Load Dataset
# ======================
DATA_PATH = "data/healthcare_dataset.csv"
df = pd.read_csv(DATA_PATH)

# Strip spaces from column names
df.columns = df.columns.str.strip()

# Keep only 2000 rows for performance
if len(df) > 2000:
    df = df.sample(n=2000, random_state=42)

# ======================
# Streamlit App
# ======================
st.set_page_config(page_title="Healthcare Dashboard", layout="wide")
st.title("🏥 Healthcare Data Dashboard")

# --------------------
# Detect columns dynamically
# --------------------
gender_col = [c for c in df.columns if "gender" in c.lower()][0]
condition_col = [c for c in df.columns if "condition" in c.lower()][0]
admission_col = [c for c in df.columns if "admission" in c.lower()][0]
discharge_col = [c for c in df.columns if "discharge" in c.lower()][0]
billing_col = [c for c in df.columns if "billing" in c.lower()][0]
insurance_col = [c for c in df.columns if "insurance" in c.lower()][0]
age_col = [c for c in df.columns if "age" in c.lower()][0]

# --------------------
# Sidebar filters
# --------------------
st.sidebar.header("🔍 Filter Data")
gender_filter = st.sidebar.multiselect(
    "Select Gender", options=df[gender_col].unique(), default=df[gender_col].unique()
)
condition_filter = st.sidebar.multiselect(
    "Select Medical Condition", options=df[condition_col].unique(), default=df[condition_col].unique()
)

df_filtered = df[(df[gender_col].isin(gender_filter)) & (df[condition_col].isin(condition_filter))]

# --------------------
# KPI CARDS
# --------------------
total_patients = len(df_filtered)
avg_age = round(df_filtered[age_col].mean(), 1)
avg_billing = round(df_filtered[billing_col].mean(), 2)

df_filtered[admission_col] = pd.to_datetime(df_filtered[admission_col])
df_filtered[discharge_col] = pd.to_datetime(df_filtered[discharge_col])
df_filtered["Stay Length"] = (df_filtered[discharge_col] - df_filtered[admission_col]).dt.days
avg_stay = round(df_filtered["Stay Length"].mean(), 1)

col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 Total Patients", total_patients)
col2.metric("🎂 Avg Age", f"{avg_age} yrs")
col3.metric("💰 Avg Billing", f"${avg_billing}")
col4.metric("🛌 Avg Stay", f"{avg_stay} days")

st.markdown("---")

# --------------------
# Charts + Insights
# --------------------
colorful_palette = px.colors.qualitative.Set3
template_mode = "plotly_white"  # default template

# 1️⃣ Gender Distribution with tie handling
df_gender_counts = df_filtered.groupby(gender_col).size().reset_index(name='Count')
df_gender_counts['Percentage'] = df_gender_counts['Count'] / len(df_filtered) * 100
df_gender_counts = df_gender_counts.sort_values(by='Count', ascending=False)

fig_gender = px.pie(
    df_gender_counts,
    names=gender_col,
    values='Count',
    title="Gender Distribution of Patients",
    color_discrete_sequence=colorful_palette,
    hover_data={'Count': True, 'Percentage': ':.1f'},
    template=template_mode
)
st.plotly_chart(fig_gender, use_container_width=True)

# Handle tie in insight
max_count = df_gender_counts['Count'].max()
most_genders = df_gender_counts[df_gender_counts['Count'] == max_count][gender_col].tolist()

if len(most_genders) == 1:
    st.markdown(
        f"**Insight:** Most patients are **{most_genders[0]}** "
        f"with {max_count} patients "
        f"({round(max_count/len(df_filtered)*100,1)}%)."
    )
else:
    genders_str = ", ".join(most_genders)
    st.markdown(
        f"**Insight:** Patient count is equal for: **{genders_str}** "
        f"with {max_count} patients each ({round(max_count/len(df_filtered)*100,1)}%)."
    )

# 2️⃣ Patients by Medical Condition
condition_counts_df = df_filtered[condition_col].value_counts().reset_index()
condition_counts_df.columns = ['Condition', 'Count']

fig_condition = px.bar(
    condition_counts_df,
    x='Condition',
    y='Count',
    title="Patients by Medical Condition",
    color_discrete_sequence=colorful_palette,
    template=template_mode
)
st.plotly_chart(fig_condition, use_container_width=True)
st.markdown(
    f"**Insight:** The most common condition is **{condition_counts_df['Condition'][0]}** "
    f"with {condition_counts_df['Count'][0]} cases."
)

# --------------------
# New Charts (Funnel, Sunburst, Donut)
# --------------------
patient_flow = {
    "Stage": ["Admitted", "Under Treatment", "Discharged"],
    "Count": [len(df_filtered), int(len(df_filtered)*0.8), int(len(df_filtered)*0.75)]
}
df_flow = pd.DataFrame(patient_flow)

fig_funnel = px.funnel(
    df_flow,
    y="Stage",
    x="Count",
    title="Patient Journey Funnel",
    color="Stage",
    color_discrete_sequence=colorful_palette,
    template=template_mode
)
st.plotly_chart(fig_funnel, use_container_width=True)

if "Department" in df_filtered.columns:
    fig_sunburst = px.sunburst(
        df_filtered,
        path=["Department", insurance_col],
        title="Insurance Distribution Across Departments",
        color_discrete_sequence=colorful_palette,
        template=template_mode
    )
    st.plotly_chart(fig_sunburst, use_container_width=True)

if "PaymentMethod" in df_filtered.columns:
    payment_counts = df_filtered["PaymentMethod"].value_counts().reset_index()
    payment_counts.columns = ["Payment Method", "Count"]

    fig_donut = px.pie(
        payment_counts,
        names="Payment Method",
        values="Count",
        hole=0.5,
        title="Distribution of Payment Methods",
        color_discrete_sequence=colorful_palette,
        template=template_mode
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# --------------------
# Extra Analytics
# --------------------
st.subheader("📊 Extra Analytics")

admissions_over_time = df_filtered.groupby(df_filtered[admission_col].dt.to_period("M")).size().reset_index(name="Count")
admissions_over_time[admission_col] = admissions_over_time[admission_col].astype(str)

fig_line = px.line(
    admissions_over_time,
    x=admission_col,
    y="Count",
    markers=True,
    title="Admissions Over Time",
    color_discrete_sequence=colorful_palette,
    template=template_mode
)
st.plotly_chart(fig_line, use_container_width=True)

billing_trend = df_filtered.groupby(df_filtered[admission_col].dt.to_period("M"))[billing_col].sum().reset_index()
billing_trend[admission_col] = billing_trend[admission_col].dt.to_timestamp()

fig_area_billing = px.area(
    billing_trend,
    x=admission_col,
    y=billing_col,
    title="Total Billing Amount Over Time",
    labels={admission_col: "Admission Month", billing_col: "Total Billing"},
    color_discrete_sequence=colorful_palette,
    template=template_mode
)
st.plotly_chart(fig_area_billing, use_container_width=True)

# --------------------
# Data Preview
# --------------------
st.subheader("📝 Sample Data Preview")
st.dataframe(df_filtered.head(20))
