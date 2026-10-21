from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

NUMERIC_COLUMNS = ["Sales", "Profit", "Quantity", "Discount"]
DATE_COLUMNS = ["Order Date", "Ship Date"]
FILTER_COLUMNS = ["Region", "Category", "Segment", "Ship Mode", "State"]
REQUIRED_KPI_COLUMNS = ["Sales", "Profit", "Order ID", "Quantity"]


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read supported CSV, XLSX, or JSON files into a DataFrame."""
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(uploaded_file)
    if suffix == ".xlsx":
        return pd.read_excel(uploaded_file)
    if suffix == ".json":
        try:
            return pd.read_json(uploaded_file)
        except ValueError:
            uploaded_file.seek(0)
            data = json.load(uploaded_file)
            return pd.DataFrame(data)
    raise ValueError("Unsupported file type. Please upload CSV, XLSX, or JSON.")


def standardize_data(df: pd.DataFrame) -> pd.DataFrame:
    """Trim column names and text cells; coerce known numeric/date columns."""
    result = df.copy()
    result.columns = [str(column).strip() for column in result.columns]

    for column in result.select_dtypes(include=["object", "string"]).columns:
        result[column] = result[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )

    for column in NUMERIC_COLUMNS:
        if column in result.columns:
            cleaned = (
                result[column]
                .astype("string")
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
            )
            result[column] = pd.to_numeric(cleaned, errors="coerce")

    for column in DATE_COLUMNS:
        if column in result.columns:
            result[column] = pd.to_datetime(result[column], errors="coerce")

    return result


def clean_data(df: pd.DataFrame, missing_strategy: str, remove_duplicates: bool) -> pd.DataFrame:
    """Apply selected missing-value handling and duplicate removal."""
    result = df.copy()
    if remove_duplicates:
        result = result.drop_duplicates()

    if missing_strategy == "Drop rows with missing values":
        result = result.dropna()
    elif missing_strategy == "Fill numeric with median / text with mode":
        for column in result.columns:
            if pd.api.types.is_numeric_dtype(result[column]):
                if result[column].notna().any():
                    result[column] = result[column].fillna(result[column].median())
            else:
                modes = result[column].mode(dropna=True)
                if not modes.empty:
                    result[column] = result[column].fillna(modes.iloc[0])
    return result


def calculate_kpis(df: pd.DataFrame) -> tuple[float, float, int, float, float]:
    """Return total sales, profit, unique orders, quantity, and profit margin."""
    sales = float(df["Sales"].sum()) if "Sales" in df.columns else 0.0
    profit = float(df["Profit"].sum()) if "Profit" in df.columns else 0.0
    orders = int(df["Order ID"].nunique()) if "Order ID" in df.columns else 0
    quantity = float(df["Quantity"].sum()) if "Quantity" in df.columns else 0.0
    margin = profit / sales * 100 if sales != 0 else 0.0
    return sales, profit, orders, quantity, margin


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render up to five categorical filters and a date-range filter when available."""
    filtered = df.copy()
    st.sidebar.header("Interactive Filters")

    for column in FILTER_COLUMNS:
        if column in filtered.columns:
            values = sorted(filtered[column].dropna().astype(str).unique().tolist())
            selected = st.sidebar.multiselect(
                f"{column}", values, default=values, key=f"filter_{column}"
            )
            if selected:
                filtered = filtered[filtered[column].astype(str).isin(selected)]
            else:
                filtered = filtered.iloc[0:0]

    if "Order Date" in filtered.columns and pd.api.types.is_datetime64_any_dtype(filtered["Order Date"]):
        valid_dates = filtered["Order Date"].dropna()
        if not valid_dates.empty:
            date_range = st.sidebar.date_input(
                "Order date range",
                value=(valid_dates.min().date(), valid_dates.max().date()),
                min_value=valid_dates.min().date(),
                max_value=valid_dates.max().date(),
            )
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_date, end_date = date_range
                filtered = filtered[
                    filtered["Order Date"].notna()
                    & (filtered["Order Date"].dt.date >= start_date)
                    & (filtered["Order Date"].dt.date <= end_date)
                ]
    return filtered


st.title("📊 Sales Analytics Dashboard")
st.caption("Upload, validate, preprocess, filter, and analyze sales data.")

with st.sidebar:
    st.header("1. Upload Data")
    uploaded_file = st.file_uploader(
        "Upload CSV, Excel (.xlsx), or JSON",
        type=["csv", "xlsx", "json"],
    )

if uploaded_file is None:
    st.info("Upload a dataset from the sidebar to get started.")
    st.markdown(
        "Required columns for all five KPIs: `Sales`, `Profit`, `Order ID`, and `Quantity`. "
        "Filters and charts appear when their relevant columns exist."
    )
    st.stop()

# Keep file-reading errors separate from dashboard/visualization errors.
try:
    raw_df = read_uploaded_file(uploaded_file)
except Exception as exc:
    st.error(f"Could not read the uploaded file: {exc}")
    st.stop()

if raw_df.empty:
    st.error("The uploaded file contains no data rows.")
    st.stop()
if raw_df.shape[1] == 0:
    st.error("No columns were found in the uploaded file.")
    st.stop()

raw_df = raw_df.copy()
raw_df.columns = [str(column).strip() for column in raw_df.columns]

st.success(f"Loaded {uploaded_file.name} successfully.")
st.header("2. Data Validation")
col1, col2, col3 = st.columns(3)
col1.metric("Rows", f"{len(raw_df):,}")
col2.metric("Columns", f"{len(raw_df.columns):,}")
col3.metric("Duplicate records", f"{int(raw_df.duplicated().sum()):,}")

with st.expander("Column names and data types", expanded=True):
    schema = pd.DataFrame({"Column": raw_df.columns, "Data type": raw_df.dtypes.astype(str).values})
    st.dataframe(schema, use_container_width=True, hide_index=True)

with st.expander("Missing values by column", expanded=True):
    missing = raw_df.isna().sum().rename("Missing values").to_frame()
    missing["Missing (%)"] = (missing["Missing values"] / len(raw_df) * 100).round(2)
    st.dataframe(missing, use_container_width=True)

with st.expander("Raw data preview"):
    st.dataframe(raw_df.head(100), use_container_width=True)

st.header("3. Data Preprocessing")
standardized_df = standardize_data(raw_df)
left, right = st.columns(2)
with left:
    missing_strategy = st.selectbox(
        "Missing-value handling",
        [
            "Keep missing values",
            "Fill numeric with median / text with mode",
            "Drop rows with missing values",
        ],
    )
with right:
    remove_duplicates = st.checkbox("Remove duplicate records", value=True)

clean_df = clean_data(standardized_df, missing_strategy, remove_duplicates)
metric1, metric2, metric3 = st.columns(3)
metric1.metric("Rows after preprocessing", f"{len(clean_df):,}", delta=f"{len(clean_df) - len(raw_df):+,} vs original")
metric2.metric("Remaining missing cells", f"{int(clean_df.isna().sum().sum()):,}")
metric3.metric("Duplicate records remaining", f"{int(clean_df.duplicated().sum()):,}")
with st.expander("Cleaned data preview"):
    st.dataframe(clean_df.head(100), use_container_width=True)

st.header("4. Interactive Analysis")
filtered_df = apply_filters(clean_df)
if filtered_df.empty:
    st.warning("No rows match the current filters or cleaning settings. Adjust the filters or preprocessing options.")
    st.stop()

sales, profit, orders, quantity, margin = calculate_kpis(filtered_df)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", f"${sales:,.2f}")
k2.metric("Total Profit", f"${profit:,.2f}")
k3.metric("Total Orders", f"{orders:,}")
k4.metric("Total Quantity Sold", f"{quantity:,.0f}" if quantity.is_integer() else f"{quantity:,.2f}")
k5.metric("Profit Margin", f"{margin:.2f}%")

missing_kpi_columns = [column for column in REQUIRED_KPI_COLUMNS if column not in filtered_df.columns]
if missing_kpi_columns:
    st.warning("Some KPI values are zero because these required columns are missing: " + ", ".join(missing_kpi_columns))

st.header("5. Interactive Visualizations")
chart1, chart2 = st.columns(2)
with chart1:
    st.subheader("Sales by Category")
    if {"Category", "Sales"}.issubset(filtered_df.columns):
        category_sales = filtered_df.groupby("Category", dropna=False, as_index=False)["Sales"].sum()
        st.plotly_chart(px.bar(category_sales, x="Category", y="Sales", color="Category", title="Total sales by category"), use_container_width=True)
    else:
        st.info("This chart requires Category and Sales columns.")

with chart2:
    st.subheader("Profit by Region")
    if {"Region", "Profit"}.issubset(filtered_df.columns):
        region_profit = filtered_df.groupby("Region", dropna=False, as_index=False)["Profit"].sum()
        st.plotly_chart(px.bar(region_profit, x="Region", y="Profit", color="Region", title="Total profit by region"), use_container_width=True)
    else:
        st.info("This chart requires Region and Profit columns.")

chart3, chart4 = st.columns(2)
with chart3:
    st.subheader("Monthly Sales Trend")
    if {"Order Date", "Sales"}.issubset(filtered_df.columns):
        date_df = filtered_df.dropna(subset=["Order Date"]).copy()
        if not date_df.empty:
            monthly_sales = date_df.set_index("Order Date")["Sales"].resample("MS").sum().reset_index()
            st.plotly_chart(px.line(monthly_sales, x="Order Date", y="Sales", markers=True, title="Monthly sales over time"), use_container_width=True)
        else:
            st.info("No valid Order Date values are available for this chart.")
    else:
        st.info("This chart requires Order Date and Sales columns.")

with chart4:
    st.subheader("Sales vs Profit")
    if {"Sales", "Profit"}.issubset(filtered_df.columns):
        color_column = "Category" if "Category" in filtered_df.columns else None
        hover_columns = [column for column in ["Order ID", "Region"] if column in filtered_df.columns]
        st.plotly_chart(px.scatter(filtered_df, x="Sales", y="Profit", color=color_column, hover_data=hover_columns, title="Relationship between sales and profit"), use_container_width=True)
    else:
        st.info("This chart requires Sales and Profit columns.")

st.header("6. Statistical Summary")
numeric_df = filtered_df.select_dtypes(include="number")
if not numeric_df.empty:
    summary = numeric_df.describe().T.rename_axis("Column").reset_index()
    st.dataframe(summary, use_container_width=True, hide_index=True)
else:
    st.info("No numeric columns are available for statistical summaries.")

st.header("7. Download Results")
csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered data as CSV",
    data=csv_data,
    file_name="filtered_sales_data.csv",
    mime="text/csv",
)
