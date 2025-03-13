import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import babel
from babel.numbers import format_currency

print("Python Version:", sys.version)
print("Streamlit Version:", st.__version__)
print("Pandas Version:", pd.__version__)
print("Matplotlib Version:", matplotlib.__version__)
print("Seaborn Version:", sns.__version__)
print("Babel Version:", babel.__version__)

st.set_page_config(page_title="E-Commerce Dashboard")

BASE_DIR = Path(__file__).resolve().parent
data_path = BASE_DIR / "all_data.csv"
logo_path = BASE_DIR.parent / "logo.jpg"

def remove_outliers(df, columns):
    """
    Menghilangkan outlier berdasarkan metode IQR (Interquartile Range).
    
    Parameters:
    df (pd.DataFrame): DataFrame yang akan diproses.
    columns (list): List nama kolom numerik yang akan difilter dari outlier.

    Returns:
    pd.DataFrame: DataFrame tanpa outlier.
    """
    df_cleaned = df.copy()
    for col in columns:
        Q1 = df_cleaned[col].quantile(0.25)
        Q3 = df_cleaned[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df_cleaned = df_cleaned[(df_cleaned[col] >= lower_bound) & (df_cleaned[col] <= upper_bound)]
    
    return df_cleaned

datetime_cols = [
    "order_date",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "shipping_limit_date",
    ]

all_data = pd.read_csv(data_path)
all_data[datetime_cols] = all_data[datetime_cols].apply(pd.to_datetime)

numeric_columns = ["price", "freight_value", "payment_value", "order_item_id"]
all_data = remove_outliers(all_data, numeric_columns)

st.sidebar.image(str(logo_path), use_container_width=True, caption="Logo")

start_date, end_date = st.sidebar.date_input(
    "Time Period",
    [all_data["order_approved_at"].min(), all_data["order_approved_at"].max()],
    min_value=all_data["order_approved_at"].min(),
    max_value=all_data["order_approved_at"].max()
)

all_data_filtered = all_data[(all_data["order_approved_at"] >= pd.Timestamp(start_date)) & (all_data["order_approved_at"] <= pd.Timestamp(end_date))]
all_data_filtered = all_data_filtered.copy()

daily_orders = all_data_filtered.resample("D", on="order_approved_at").agg({"order_id": "nunique"}).reset_index()
daily_revenue = all_data_filtered.resample("D", on="order_approved_at").agg({"payment_value": "sum"}).reset_index()

total_orders = daily_orders["order_id"].sum()
total_revenue = format_currency(daily_revenue["payment_value"].sum(), "IDR", locale="id_ID")

st.header("E-Commerce Dashboard")

# Menampilkan metrik utama
col1, col2 = st.columns(2)
col1.metric("Total Orders", total_orders)
col2.metric("Total Revenue", total_revenue)

# Sidebar menu untuk memilih tipe analisis
analysis_type = st.sidebar.selectbox(
    "Pilih Analisis",
    [
        "Daily Order & Revenue",
        "Monthly Order Trends",
        "Most Preferred Payment Method",
        "Customer Segmentation Based on RFM",
        "Top Product Categories by Sales Volume",
        "Product pricing impact on customer ratings"
    ]
)

colors5 = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]
colors10 = [
    "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4",
    "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"
    ]


# Default: Visualisasi Pesanan Harian & Pendapatan Harian
if analysis_type == "Daily Order & Revenue": 
    # Visualisasi pesanan harian
    st.subheader("Daily Orders")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=daily_orders, x="order_approved_at", y="order_id", marker="o", ax=ax)
    ax.set_title("Orders Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Orders")
    st.pyplot(fig)

    # Visualisasi pendapatan harian
    st.subheader("Daily Revenue")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=daily_revenue, x="order_approved_at", y="payment_value", marker="o", ax=ax)
    ax.set_title("Revenue Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue")
    st.pyplot(fig)

# Analisis: Tren Jumlah Pesanan Per Bulan
elif analysis_type == "Monthly Order Trends":
    st.subheader("Monthly Order Trends")

    all_data_filtered['month_year'] = all_data_filtered['order_date'].dt.to_period('M')

    monthly_df = all_data_filtered.groupby('month_year')['order_id'].count().reset_index()
    monthly_df.rename(columns={'order_id': 'order_count'}, inplace=True)
    monthly_df['month_year'] = monthly_df['month_year'].astype(str)

    fig = plt.figure(figsize=(10, 5))
    sns.lineplot(x=monthly_df['month_year'].astype(str), y='order_count', data=monthly_df, marker='o', label='Order Count')

    plt.xlabel("Month")
    plt.ylabel("Number of Orders")
    plt.title("Monthly Order Trends")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)

    st.pyplot(fig)


# Analisis: Metode Pembayaran Paling Populer
elif analysis_type == "Most Preferred Payment Method":
    st.subheader("Most Preferred Payment Method")

    payment_counts = all_data_filtered['payment_type'].value_counts()

    fig = plt.figure(figsize=(10, 5))
    sns.countplot(x='payment_type', data=all_data_filtered, order=payment_counts.index)

    plt.title("Most Preferred Payment Method")
    plt.xlabel("Payment Method")
    plt.ylabel("Order Count")
    plt.xticks(rotation=45)

    st.pyplot(fig)

# Analisis: Segmentasi Pelanggan Berdasarkan RFM
elif analysis_type == "Customer Segmentation Based on RFM":
    st.subheader("Customer Segmentation Based on RFM")

    all_data_filtered['total_price'] = all_data_filtered['price'] * all_data_filtered['order_item_id']
    all_data_filtered.rename(columns={'order_date': 'order_date'}, inplace=True)

    rfm_df = all_data_filtered.groupby(by="customer_id", as_index=False).agg({
        "order_date": "max",
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = all_data_filtered["order_date"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    tab1, tab2, tab3 = st.tabs(["Recency", "Frequency", "Monetary"]) 

    with tab1:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=False).head(5), hue="customer_id", palette=colors5, ax=ax)
        ax.set_ylabel("Recency")
        ax.set_xlabel("Customer ID")
        ax.set_title("By Recency (days)", fontsize=14)
        st.pyplot(fig)

    with tab2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), hue="customer_id", palette=colors5, ax=ax)
        ax.set_ylabel("Frequency")
        ax.set_xlabel("Customer ID")
        ax.set_title("By Frequency", fontsize=14)
        st.pyplot(fig)

    with tab3:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), hue="customer_id", palette=colors5, ax=ax)
        ax.set_ylabel("Monetary")
        ax.set_xlabel("Customer ID")
        ax.set_title("By Monetary", fontsize=14)
        st.pyplot(fig)

# Analisis: Kategori Produk dengan Penjualan Terbanyak
elif analysis_type == "Top Product Categories by Sales Volume":
    st.subheader("Top Product Categories by Sales Volume")
    
    category_sales = all_data_filtered.groupby('product_category_name')['order_id'].count().reset_index()
    category_sales = category_sales.sort_values(by='order_id', ascending=False)

    top_n = 10
    category_sales = category_sales.head(top_n)

    fig = plt.figure(figsize=(12, 6))

    sns.barplot(y=category_sales['product_category_name'], x=category_sales['order_id'], dodge=False, legend=False)
    plt.xlabel("Order Count")
    plt.ylabel("Product Category")
    plt.title(f"Top {top_n} Product Categories by Sales Volume")

    st.pyplot(fig)

elif analysis_type == "Product pricing impact on customer ratings":
    st.subheader("Product Pricing Impact on Customer Ratings")

    price_rating_df = all_data_filtered[["product_id", "price", "review_score"]].dropna()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x="review_score", y="price", data=price_rating_df, ax=ax, hue="review_score", palette=colors5, legend=False)

    ax.set_title("Product Pricing Impact on Customer Ratings", fontsize=14)
    ax.set_xlabel("Customer Rating", fontsize=12)
    ax.set_ylabel("Product Price (IDR)", fontsize=12)

    st.pyplot(fig)

st.markdown("> Created by Ahmad Zaky Humami MC009D5Y0493")
