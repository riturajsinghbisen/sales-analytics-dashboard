import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Sales Analytics Dashboard")
st.write("Upload and validate your sales dataset.")

uploaded_file = st.file_uploader(
    "Upload CSV, Excel, or JSON",
    type=["csv", "xlsx", "json"]
)

if uploaded_file is not None:
    try:
        extension = Path(uploaded_file.name).suffix.lower()

        if extension == ".csv":
            df = pd.read_csv(uploaded_file)
        elif extension == ".xlsx":
            df = pd.read_excel(uploaded_file)
        elif extension == ".json":
            df = pd.read_json(uploaded_file)

        st.success("Dataset uploaded successfully!")

        st.subheader("Dataset Preview")
        st.dataframe(df.head())

        st.subheader("Dataset Dimensions")
        col1, col2 = st.columns(2)
        col1.metric("Rows", df.shape[0])
        col2.metric("Columns", df.shape[1])

        st.subheader("Data Types")
        st.write(df.dtypes.astype(str))

        st.subheader("Missing Values")
        st.write(df.isnull().sum())

        st.subheader("Duplicate Records")
        st.metric("Duplicates", int(df.duplicated().sum()))
                # Data Preprocessing
        st.header("Data Preprocessing")

        # Work on a copy of the original data
        clean_df = df.copy()

        # Remove extra spaces from column names
        clean_df.columns = clean_df.columns.str.strip()

        # Remove extra spaces from text values
        for col in clean_df.select_dtypes(include=["object"]).columns:
            clean_df[col] = clean_df[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )

        # Convert common numeric columns
        numeric_cols = ["Sales", "Profit", "Quantity", "Discount"]

        for col in numeric_cols:
            if col in clean_df.columns:
                clean_df[col] = pd.to_numeric(
                    clean_df[col].astype(str).str.replace(",", "", regex=False),
                    errors="coerce"
                )

        # Convert date columns
        date_cols = ["Order Date", "Ship Date"]

        for col in date_cols:
            if col in clean_df.columns:
                clean_df[col] = pd.to_datetime(
                    clean_df[col],
                    errors="coerce"
                )

        # Handle missing values
        strategy = st.selectbox(
            "Choose missing-value handling",
            [
                "Keep missing values",
                "Fill with median/mode",
                "Drop rows with missing values"
            ]
        )

        if strategy == "Fill with median/mode":
            for col in clean_df.columns:
                if pd.api.types.is_numeric_dtype(clean_df[col]):
                    if clean_df[col].notna().any():
                        clean_df[col] = clean_df[col].fillna(
                            clean_df[col].median()
                        )
                else:
                    modes = clean_df[col].mode(dropna=True)
                    if not modes.empty:
                        clean_df[col] = clean_df[col].fillna(
                            modes.iloc[0]
                        )

        elif strategy == "Drop rows with missing values":
            clean_df = clean_df.dropna()

        # Remove duplicates
        remove_duplicates = st.checkbox(
            "Remove duplicate records",
            value=True
        )

        if remove_duplicates:
            clean_df = clean_df.drop_duplicates()

        st.subheader("Cleaned Dataset")
        st.write("Rows after preprocessing:", len(clean_df))
        st.write("Remaining missing values:", int(clean_df.isnull().sum().sum()))
        st.dataframe(clean_df.head())

                # ==================================
        # INTERACTIVE FILTERS
        # ==================================

        st.header("Interactive Filters")

        filtered_df = clean_df.copy()

        # Filter 1: Region
        if "Region" in filtered_df.columns:
            regions = sorted(
                filtered_df["Region"].dropna().unique().tolist()
            )

            selected_regions = st.multiselect(
                "Select Region",
                regions,
                default=regions
            )

            filtered_df = filtered_df[
                filtered_df["Region"].isin(selected_regions)
            ]

        # Filter 2: Category
        if "Category" in filtered_df.columns:
            categories = sorted(
                filtered_df["Category"].dropna().unique().tolist()
            )

            selected_categories = st.multiselect(
                "Select Category",
                categories,
                default=categories
            )

            filtered_df = filtered_df[
                filtered_df["Category"].isin(selected_categories)
            ]

        # Filter 3: Segment
        if "Segment" in filtered_df.columns:
            segments = sorted(
                filtered_df["Segment"].dropna().unique().tolist()
            )

            selected_segments = st.multiselect(
                "Select Segment",
                segments,
                default=segments
            )

            filtered_df = filtered_df[
                filtered_df["Segment"].isin(selected_segments)
            ]

        # ==================================
        # FIVE DYNAMIC KPIs
        # ==================================

        st.header("Sales Performance KPIs")

        total_sales = (
            filtered_df["Sales"].sum()
            if "Sales" in filtered_df.columns else 0
        )

        total_profit = (
            filtered_df["Profit"].sum()
            if "Profit" in filtered_df.columns else 0
        )

        total_orders = (
            filtered_df["Order ID"].nunique()
            if "Order ID" in filtered_df.columns else 0
        )

        total_quantity = (
            filtered_df["Quantity"].sum()
            if "Quantity" in filtered_df.columns else 0
        )

        profit_margin = (
            (total_profit / total_sales) * 100
            if total_sales != 0 else 0
        )

        # Display KPIs in five columns
        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Total Sales", f"${total_sales:,.2f}")
        col2.metric("Total Profit", f"${total_profit:,.2f}")
        col3.metric("Total Orders", f"{total_orders:,}")
        col4.metric("Total Quantity Sold", f"{total_quantity:,.0f}")
        col5.metric("Profit Margin", f"{profit_margin:.2f}%")

        st.subheader("Filtered Data Preview")
        st.dataframe(filtered_df.head(100), use_container_width=True)

                # ==================================
        # INTERACTIVE VISUALIZATIONS
        # ==================================

        st.header("Interactive Visualizations")

        # Chart 1: Sales by Category
        if "Category" in filtered_df.columns and "Sales" in filtered_df.columns:

            st.subheader("1. Sales by Category")

            category_sales = (
                filtered_df.groupby("Category", as_index=False)["Sales"]
                .sum()
            )

            fig1 = px.bar(
                category_sales,
                x="Category",
                y="Sales",
                color="Category",
                title="Total Sales by Category",
                hover_data={"Sales": ":,.2f"}
            )

            st.plotly_chart(fig1, use_container_width=True)

        # Chart 2: Profit by Region
        if "Region" in filtered_df.columns and "Profit" in filtered_df.columns:

            st.subheader("2. Profit by Region")

            region_profit = (
                filtered_df.groupby("Region", as_index=False)["Profit"]
                .sum()
            )

            fig2 = px.bar(
                region_profit,
                x="Region",
                y="Profit",
                color="Region",
                title="Total Profit by Region",
                hover_data={"Profit": ":,.2f"}
            )

            st.plotly_chart(fig2, use_container_width=True)

        # Chart 3: Monthly Sales Trend
        if "Order Date" in filtered_df.columns and "Sales" in filtered_df.columns:

            st.subheader("3. Monthly Sales Trend")

            date_df = filtered_df.dropna(subset=["Order Date"]).copy()
            date_df["Order Date"] = pd.to_datetime(
                date_df["Order Date"], errors="coerce"
            )
            date_df = date_df.dropna(subset=["Order Date"])

            if not date_df.empty:
                monthly_sales = (
                    date_df.set_index("Order Date")["Sales"]
                    .resample("MS")
                    .sum()
                    .reset_index()
                )

                fig3 = px.line(
                    monthly_sales,
                    x="Order Date",
                    y="Sales",
                    markers=True,
                    title="Monthly Sales Over Time"
                )

                st.plotly_chart(fig3, use_container_width=True)

        # Chart 4: Sales vs Profit
        if "Sales" in filtered_df.columns and "Profit" in filtered_df.columns:

            st.subheader("4. Sales vs Profit")

            color_column = (
                "Category" if "Category" in filtered_df.columns else None
            )

            fig4 = px.scatter(
                filtered_df,
                x="Sales",
                y="Profit",
                color=color_column,
                title="Relationship Between Sales and Profit",
                hover_data=[
                    col for col in ["Order ID", "Region"]
                    if col in filtered_df.columns
                ]
            )

            st.plotly_chart(fig4, use_container_width=True)

    except Exception as e:
        st.error(f"Unable to read the file: {e}")