import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from babel.numbers import format_currency
from pathlib import Path
        
# Mengatur title pada tab browser
st.set_page_config(page_title="E-Commerce Dashboard")

# Load dataset
datetime_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "shipping_limit_date",
    ]

# Dapatkan path absolut dari lokasi file dashboard.py
BASE_DIR = Path(__file__).resolve().parent
data_path = BASE_DIR / "all_data.csv"
logo_path = BASE_DIR.parent / "logo.jpg"

# Load dataset
all_df = pd.read_csv(data_path)

# Konversi column Date
all_df[datetime_cols] = all_df[datetime_cols].apply(pd.to_datetime)

# Sidebar filter Date
rounded_css = """
<style>
    .rounded-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius: 50%;
        width: 80%;
    }
</style>
"""
st.sidebar.markdown(rounded_css, unsafe_allow_html=True)
st.sidebar.image(str(logo_path), use_container_width=True, caption="Logo")
start_date, end_date = st.sidebar.date_input(
    "Time Period",
    [all_df["order_approved_at"].min(), all_df["order_approved_at"].max()],
    min_value=all_df["order_approved_at"].min(),
    max_value=all_df["order_approved_at"].max()
)

# Filter Date
all_df_filtered = all_df[(all_df["order_approved_at"] >= pd.Timestamp(start_date)) &  (all_df["order_approved_at"] <= pd.Timestamp(end_date))]
daily_orders = all_df_filtered.resample("D", on="order_approved_at").agg({"order_id": "nunique"}).reset_index()
daily_revenue = all_df_filtered.resample("D", on="order_approved_at").agg({"payment_value": "sum"}).reset_index()
total_orders = daily_orders["order_id"].sum()
total_revenue = format_currency(daily_revenue["payment_value"].sum(), "IDR", locale="id_ID")

# Menampilkan title pada halaman
st.header("E-Commerce Dashboard")

# Menampilkan metrik utama
col1, col2 = st.columns(2)
col1.metric("Total Orders", total_orders)
col2.metric("Total Revenue", total_revenue)

# # Visualisasi pesanan harian
# st.subheader("Daily Orders")
# fig, ax = plt.subplots(figsize=(10, 5))
# sns.lineplot(data=daily_orders, x="order_approved_at", y="order_id", marker="o", ax=ax)
# ax.set_title("Orders Over Time")
# ax.set_xlabel("Date")
# ax.set_ylabel("Number of Orders")
# st.pyplot(fig)

# # Visualisasi pendapatan harian
# st.subheader("Daily Revenue")
# fig, ax = plt.subplots(figsize=(10, 5))
# sns.lineplot(data=daily_revenue, x="order_approved_at", y="payment_value", marker="o", ax=ax)
# ax.set_title("Revenue Over Time")
# ax.set_xlabel("Date")
# ax.set_ylabel("Revenue")
# st.pyplot(fig)


# Section Bagaimana tren jumlah pesanan per bulan?
with st.container():
    st.subheader("Monthly Order Trends")
    
    all_df['month_year'] = all_df['order_purchase_timestamp'].dt.to_period('M')
    monthly_df = all_df.groupby('month_year')['order_id'].count().reset_index()
    monthly_df.rename(columns={'order_id': 'order_count'}, inplace=True)
    monthly_df['month_year'] = monthly_df['month_year'].astype(str)

    fig = px.line(monthly_df, x='month_year', y='order_count')
    fig.update_xaxes(title='Month')
    fig.update_yaxes(title='Number of Orders')
    fig.update_layout(
        plot_bgcolor='#ffffff',
    )
    st.plotly_chart(fig, use_container_width=True)

# Sections Metode pembayaran apa yang paling banyak digunakan?
with st.container():
    st.subheader("Most Preferred Payment Method")

    payment_counts = all_df['payment_type'].value_counts()

    fig = px.bar(x=payment_counts.index, y=payment_counts.values)
    fig.update_layout(xaxis_title='Metode Pembayaran', yaxis_title='Jumlah Transaksi')
    fig.update_layout(
        plot_bgcolor='#ffffff',
    )
    st.plotly_chart(fig, use_container_width=True)

# Section Bagaimana rating rata-rata berdasarkan kategori produk?
with st.container():
    st.subheader("Customer Satisfaction Score")

    average_rating_by_category = all_df.groupby('product_category_name')['review_score'].mean().reset_index()
    average_rating_by_category = average_rating_by_category.rename(columns={'review_score': 'average_rating'})
    top_10_categories = average_rating_by_category.sort_values(by='average_rating', ascending=False).head(10)

    fig = px.bar(top_10_categories, 
        x='average_rating', 
        y='product_category_name', 
        orientation='h',
        title='Top 10 Product Categories by Average Rating',
        labels={'average_rating': 'Average Rating', 'product_category_name': 'Product Category'})
    fig.update_layout(
        plot_bgcolor='#ffffff',
    )
    st.plotly_chart(fig, use_container_width=True)

# Section "Bagaimana segmentasi pelanggan berdasarkan RFM Analysis?"
with st.container():
    st.subheader("Customer Segmentation Based on")

    all_df['total_price'] = all_df['price'] * all_df['order_item_id']
    all_df.rename(columns={'order_purchase_timestamp': 'order_date'}, inplace=True)

    rfm_df = all_df.groupby(by="customer_id", as_index=False).agg({
        "order_date": "max",
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = all_df["order_date"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    tab1, tab2, tab3 = st.tabs(["Recency", "Frequency", "Monetary"]) 

    with tab1:
        fig, ax = plt.subplots(figsize=(10, 6))

        # Bar plot for Recency
        colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]
        sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=False).head(5), hue="customer_id", palette=colors, dodge=False, ax=ax)
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.set_title("By Recency (days)", loc="center", fontsize=18)
        ax.tick_params(axis='x', labelsize=15)
        ax.legend([],[], frameon=False)
        st.pyplot(fig)
        

    with tab2:
        fig, ax = plt.subplots(figsize=(10, 6))

        # Bar plot for Frequency
        colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]
        sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), hue="customer_id", palette=colors, dodge=False, ax=ax)
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.set_title("By Frequency", loc="center", fontsize=18)
        ax.tick_params(axis='x', labelsize=15)
        ax.legend([],[], frameon=False)
        st.pyplot(fig)
        
    with tab3:
        fig, ax = plt.subplots(figsize=(10, 6))

        # Bar plot for Monetary
        colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]
        sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), hue="customer_id", palette=colors, dodge=False, ax=ax)
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.set_title("By Monetary", loc="center", fontsize=18)
        ax.tick_params(axis='x', labelsize=15)
        ax.legend([],[], frameon=False)
        st.pyplot(fig)

# Section Bagaimana distribusi geografis pesanan berdasarkan lokasi pelanggan?
with st.container():
    st.subheader("Geographical Distribution of Orders")

    order_distribution = all_df.groupby(['customer_city', 'customer_state'])['order_id'].count().reset_index()
    order_distribution.rename(columns={'order_id': 'order_count'}, inplace=True)
    st.dataframe(order_distribution)
    fig = px.choropleth(order_distribution,
                        locations='customer_state',
                        locationmode="country names",
                        color='order_count',
                        hover_name='customer_city',
                        title='Distribusi Geografis Pesanan',
                        color_continuous_scale='Viridis')

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        scope="world",
    )
    fig.update_layout(
            plot_bgcolor='#cacaca',
        )
    st.plotly_chart(fig, use_container_width=True)
    
with st.container():
    st.subheader("Top Product Categories by Sales Volume")
    
    sales_by_category = all_df.groupby('product_category_name')['price'].sum().reset_index()
    sales_by_category.rename(columns={'price': 'total_sales'}, inplace=True)
    sales_by_category = sales_by_category.sort_values(by='total_sales', ascending=False)

    # Select the top N categories (e.g., top 10)
    top_n = 10
    top_categories = sales_by_category.head(top_n)
    st.dataframe(top_categories)
    
    fig = plt.figure(figsize=(12, 6))
    sns.barplot(y=top_categories['product_category_name'], x=top_categories['total_sales'],
                dodge=False, legend=False)
    plt.xlabel("Total Sales")
    plt.ylabel("Category Name")
    plt.title(f"Top {top_n} Product Categories by Sales Volume")

    st.pyplot(fig )
    
st.markdown("> Created by Ahmad Zaky Humami MC009D5Y0493")
