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