import streamlit as st
import pandas as pd
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# Set up page configurations for a premium look
st.set_page_config(
    page_title="High-Dimensional Data Visualization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling and premium feel
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1E3A8A;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
    }
    h2 {
        color: #2563EB;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 600;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Load dataset
@st.cache_data
def load_data():
    # Load dataset with windows-1252 encoding to handle special characters correctly
    return pd.read_csv('Sample - Superstore.csv', encoding='windows-1252')

df = load_data()

# App Title & Navigation Sidebar
st.title("📊 High-Dimensional Data Visualization")
st.sidebar.title("🧭 Navigation")

sections = [
    "2.1 Mosaic Plot",
    "2.2 Trellis Display",
    "2.3 Heatmap",
    "2.4 Multivariate Scatter Plot",
    "2.5 Parallel Coordinate Plot",
    "2.6 Grand Tour (3D Scatter)",
    "2.7 Sunburst Chart (New)"
]
section = st.sidebar.selectbox("Choose a visualization", sections)

# Section 2.1: Mosaic Plot (Marimekko)
if section == "2.1 Mosaic Plot":
    st.header("2.1 Mosaic Plot (Marimekko)")
    st.write(
        "Shows the distribution of total **Sales** grouped by **Region** and **Customer Segment**. "
        "The width of each block corresponds to the region's overall contribution, "
        "and the height within each block represents segment proportions."
    )
    
    # Aggregate data
    mosaic_data = df.groupby(['Region', 'Segment'])['Sales'].sum().reset_index()
    mosaic_data['Formatted Sales'] = mosaic_data['Sales'].apply(lambda x: f"${x:,.2f}")
    
    # Altair normalized stacked bar chart acting as a Mosaic Plot
    mosaic_chart = alt.Chart(mosaic_data).mark_bar().encode(
        x=alt.X('Region:N', title='Region', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Sales:Q', stack='normalize', title='Proportion of Total Sales'),
        color=alt.Color('Segment:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(title='Segment')),
        tooltip=['Region', 'Segment', 'Formatted Sales']
    ).properties(
        height=500,
        title='Mosaic Plot: Sales Proportion by Region and Segment'
    ).interactive()
    
    st.altair_chart(mosaic_chart, use_container_width=True)
    
    st.info(
        "💡 **Observations:** Each bar shows the proportion of sales contributed by Consumer, Corporate, and Home Office. "
        "Notice which customer segments dominate across different regions."
    )

# Section 2.2: Trellis Display
elif section == "2.2 Trellis Display":
    st.header("2.2 Trellis Display")
    st.write(
        "Compare the relationship between **Sales** and **Profit** across different regions using small multiples. "
        "Trellis displays prevent overlapping data and facilitate pattern recognition across categories."
    )
    
    # Premium features: Range filters to handle high-dimensional outliers
    st.markdown("### 🔍 Filter Ranges (Handles Outliers)")
    col1, col2 = st.columns(2)
    with col1:
        sales_max = float(df['Sales'].max())
        sales_range = st.slider("Sales Range ($)", 0.0, 10000.0, (0.0, 3000.0))
    with col2:
        profit_range = st.slider("Profit Range ($)", -2000.0, 2000.0, (-1000.0, 1000.0))
        
    filtered_df = df[
        (df['Sales'] >= sales_range[0]) & (df['Sales'] <= sales_range[1]) &
        (df['Profit'] >= profit_range[0]) & (df['Profit'] <= profit_range[1])
    ]
    
    # Altair Trellis (Faceted) chart
    trellis_chart = alt.Chart(filtered_df).mark_circle(size=70, opacity=0.6).encode(
        x=alt.X('Sales:Q', title='Sales ($)'),
        y=alt.Y('Profit:Q', title='Profit ($)'),
        color=alt.Color('Segment:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(title='Segment')),
        tooltip=['Product Name', 'Sales', 'Profit', 'Segment', 'Sub-Category']
    ).facet(
        facet=alt.Facet('Region:N', title='Region'),
        columns=2
    ).properties(
        title='Trellis: Sales vs Profit by Region'
    )
    
    st.altair_chart(trellis_chart, use_container_width=True)
    st.info("💡 **Observations:** Notice how the correlation between Sales and Profit behaves across the East, West, Central, and South regions.")

# Section 2.3: Heatmap
elif section == "2.3 Heatmap":
    st.header("2.3 Heatmap")
    st.write(
        "Visualizes the average **Sales** amount across **Regions** and **Product Categories** using color intensity. "
        "Ideal for spotting which categories perform best in specific geographical markets."
    )
    
    # Aggregate data
    heat_data = df.groupby(['Region', 'Category'])['Sales'].mean().reset_index()
    heat_data.columns = ['Region', 'Category', 'avg_sales']
    
    # Altair Heatmap
    heatmap = alt.Chart(heat_data).mark_rect().encode(
        x=alt.X('Region:N', title='Region', axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Category:N', title='Product Category'),
        color=alt.Color('avg_sales:Q', scale=alt.Scale(scheme='blues'), legend=alt.Legend(title='Avg Sales ($)')),
        tooltip=[
            alt.Tooltip('Region:N', title='Region'),
            alt.Tooltip('Category:N', title='Category'),
            alt.Tooltip('avg_sales:Q', title='Avg Sales ($)', format='.2f')
        ]
    ).properties(
        height=400,
        title='Heatmap: Average Sales by Region and Category'
    )
    
    st.altair_chart(heatmap, use_container_width=True)
    st.info("💡 **Observations:** Darker blue cells indicate higher average sales. Identify which region-category combination represents the highest average order value.")

# Section 2.4: Multivariate Scatter Plot
elif section == "2.4 Multivariate Scatter Plot":
    st.header("2.4 Multivariate Scatter Plot")
    st.write(
        "Visualizes 5 dimensions of data simultaneously: "
        "**Sales** (x-axis), **Profit** (y-axis), **Segment** (color), **Ship Mode** (marker shape), and **Quantity** (marker size)."
    )
    
    st.markdown("### 🔍 Filter Ranges")
    col1, col2 = st.columns(2)
    with col1:
        sales_range = st.slider("Sales Range ($)", 0.0, 10000.0, (0.0, 4000.0), key="ms_sales")
    with col2:
        profit_range = st.slider("Profit Range ($)", -2000.0, 2000.0, (-1000.0, 1000.0), key="ms_profit")
        
    filtered_df = df[
        (df['Sales'] >= sales_range[0]) & (df['Sales'] <= sales_range[1]) &
        (df['Profit'] >= profit_range[0]) & (df['Profit'] <= profit_range[1])
    ]
    
    # Altair Multivariate Scatter
    multi_scatter = alt.Chart(filtered_df).mark_point(filled=True, opacity=0.7).encode(
        x=alt.X('Sales:Q', title='Sales ($)'),
        y=alt.Y('Profit:Q', title='Profit ($)'),
        color=alt.Color('Segment:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(title='Segment')),
        shape=alt.Shape('Ship Mode:N', legend=alt.Legend(title='Ship Mode')),
        size=alt.Size('Quantity:Q', scale=alt.Scale(range=[40, 300]), legend=alt.Legend(title='Quantity')),
        tooltip=['Product Name', 'Sales', 'Profit', 'Segment', 'Ship Mode', 'Quantity']
    ).properties(
        height=500,
        title='Multivariate Scatter: Sales vs Profit (Color=Segment, Shape=Ship Mode, Size=Quantity)'
    ).interactive()
    
    st.altair_chart(multi_scatter, use_container_width=True)
    st.info("💡 **Observations:** Hover over points for product details. Larger markers represent higher order quantities. See if you can identify clusters of high profitability.")

# Section 2.5: Parallel Coordinate Plot
elif section == "2.5 Parallel Coordinate Plot":
    st.header("2.5 Parallel Coordinate Plot")
    st.write(
        "Traces individual transactions across multiple numerical dimensions: **Sales**, **Profit**, **Quantity**, and **Discount**. "
        "The lines are colored by **Region** (East: 0, West: 1, Central: 2, South: 3). "
        "Use brushing (dragging on axes) to isolate specific ranges and trace patterns."
    )
    
    # Mapped categorical region to numbers for Plotly continuous color scale
    region_map = {'East': 0, 'West': 1, 'Central': 2, 'South': 3}
    
    # Use a representative sample of 1,000 orders to avoid overlapping noise and lag in browser
    sample_df = df.sample(n=1000, random_state=42).copy()
    sample_df['region_num'] = sample_df['Region'].map(region_map)
    
    fig = px.parallel_coordinates(
        sample_df,
        dimensions=['Sales', 'Profit', 'Quantity', 'Discount'],
        color='region_num',
        color_continuous_scale=px.colors.sequential.Plasma,
        labels={
            'Sales': 'Sales ($)',
            'Profit': 'Profit ($)',
            'Quantity': 'Quantity',
            'Discount': 'Discount',
            'region_num': 'Region (0=East, 1=West, 2=Central, 3=South)'
        },
        title='Parallel Coordinate Plot: Sales, Profit, Quantity, and Discount'
    )
    fig.update_layout(
        coloraxis_colorbar=dict(
            title='Region',
            tickvals=[0, 1, 2, 3],
            ticktext=['East', 'West', 'Central', 'South']
        ),
        margin=dict(t=80, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.info("💡 **Observations:** You can click and drag vertically on any axis to filter (brush). See if high discounts lead directly to negative profits.")

# Section 2.6: Grand Tour (3D Scatter)
elif section == "2.6 Grand Tour (3D Scatter)":
    st.header("2.6 Grand Tour: 3D Scatter Plot")
    st.write(
        "Interact with 3 dimensions (**Sales**, **Profit**, and **Quantity**) in a rotatable 3D space. "
        "Markers are colored by **Region**, shaped by **Segment**, and sized by **Quantity**."
    )
    
    # Take a sample of 1,000 rows to ensure snappy 3D rendering
    sample_df = df.sample(n=1000, random_state=42)
    
    fig_3d = px.scatter_3d(
        sample_df,
        x='Sales',
        y='Profit',
        z='Quantity',
        color='Region',
        symbol='Segment',
        size='Quantity',
        size_max=18,
        opacity=0.75,
        hover_data=['Product Name', 'Ship Mode', 'Category'],
        color_discrete_sequence=px.colors.qualitative.Dark2,
        title='3D Scatter Plot: Sales vs Profit vs Quantity'
    )
    fig_3d.update_layout(
        scene=dict(
            xaxis_title='Sales ($)',
            yaxis_title='Profit ($)',
            zaxis_title='Quantity'
        ),
        legend_title='Region',
        margin=dict(t=80, b=40)
    )
    
    st.plotly_chart(fig_3d, use_container_width=True)
    st.info("💡 **Observations:** Click and drag the chart to rotate it in 3D. Zoom with your scroll wheel. Look for outliers that extend far out on the Sales or Profit axes.")

# Section 2.7: Sunburst Chart (New)
elif section == "2.7 Sunburst Chart (New)":
    st.header("2.7 Hierarchical Sunburst Chart")
    st.write(
        "A premium visualization type displaying hierarchical data. "
        "This sunburst chart shows how **Sales** breakdown from **Region** -> **Product Category** -> **Sub-Category**. "
        "Click on any sector to zoom in and explore the sub-levels."
    )
    
    fig_sunburst = px.sunburst(
        df,
        path=['Region', 'Category', 'Sub-Category'],
        values='Sales',
        color='Region',
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title='Sunburst Chart: Hierarchical Sales Breakdown'
    )
    fig_sunburst.update_layout(
        margin=dict(t=80, b=40, l=40, r=40),
        height=600
    )
    
    st.plotly_chart(fig_sunburst, use_container_width=True)
    st.info("💡 **Observations:** Click on an inner region sector (e.g. West) to drill down into its categories. Click the center to go back up.")
