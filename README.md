# Sales Analytics Dashboard

An interactive sales data analysis application built using Python, Streamlit, Pandas, and Plotly.

## Features

- Upload CSV, Excel (.xlsx), and JSON datasets.
- Validate dataset dimensions, column names, data types, missing values, and duplicate records.
- Handle missing values and duplicate records.
- Convert recognized numeric and date columns.
- Apply interactive filters for Region, Category, and Segment.
- Display five dynamic KPIs:
  - Total Sales
  - Total Profit
  - Total Orders
  - Total Quantity Sold
  - Profit Margin
- Visualize sales and profit through interactive charts.
- Display descriptive statistical summaries.
- Download filtered data as CSV.

## Installation

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
streamlit run app.py
```

## Technologies Used

- Python
- Streamlit
- Pandas
- Plotly
- OpenPyXL

## Deployment

The application can be deployed using Streamlit Community Cloud by connecting this GitHub repository and selecting `app.py` as the main file.