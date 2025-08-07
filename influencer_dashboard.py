import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import base64
from io import StringIO

# --- Data Ingestion Manager Class  ---
class DataIngestionManager:
    """Handles data upload, validation, and processing for the dashboard"""
    
    def __init__(self):
        self.required_schemas = {
            'influencers': ['influencer_id', 'name', 'category', 'gender', 'follower_count', 'platform', 'tier'],
            'posts': ['influencer_id', 'platform', 'date', 'reach', 'likes', 'comments', 'brand', 'product', 'campaign_type'],
            'tracking_data': ['influencer_id', 'campaign', 'orders', 'revenue', 'date', 'campaign_type'],
            'payouts': ['influencer_id', 'basis', 'rate', 'total_payout']
        }
    
    def validate_schema(self, df, data_type):
        """Validate if uploaded data matches required schema"""
        required_cols = self.required_schemas.get(data_type, [])
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return False, f"Missing required columns: {missing_cols}"
        
        return True, "Schema validation passed"
    
    def clean_data(self, df, data_type):
        """Clean and standardize uploaded data"""
        df_clean = df.copy()
        
        # Common cleaning steps
        df_clean = df_clean.dropna(subset=self.required_schemas[data_type])
        
        # Type-specific cleaning
        if data_type == 'influencers':
            df_clean['follower_count'] = pd.to_numeric(df_clean['follower_count'], errors='coerce')
            df_clean = df_clean.dropna(subset=['follower_count'])
            
        elif data_type == 'posts':
            df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
            numeric_cols = ['reach', 'likes', 'comments']
            for col in numeric_cols:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            df_clean = df_clean.dropna(subset=['date'] + numeric_cols)
            
        elif data_type == 'tracking_data':
            df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
            df_clean['orders'] = pd.to_numeric(df_clean['orders'], errors='coerce')
            df_clean['revenue'] = pd.to_numeric(df_clean['revenue'], errors='coerce')
            df_clean = df_clean.dropna(subset=['date', 'orders', 'revenue'])
            
        elif data_type == 'payouts':
            df_clean['rate'] = pd.to_numeric(df_clean['rate'], errors='coerce')
            df_clean['total_payout'] = pd.to_numeric(df_clean['total_payout'], errors='coerce')
            df_clean = df_clean.dropna(subset=['rate', 'total_payout'])
        
        return df_clean

# --- Dashboard Code  ---
# Set page configuration
st.set_page_config(
    page_title="HealthKart Influencer ROI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2E8B57;
    }
    .insight-box {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for data storage
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.influencers_df = pd.DataFrame()
    st.session_state.posts_df = pd.DataFrame()
    st.session_state.tracking_df = pd.DataFrame()
    st.session_state.payouts_df = pd.DataFrame()

@st.cache_data
def generate_sample_data():
    """Generate comprehensive sample data for the dashboard with test/control groups"""
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Brands and products
    brands = ['MuscleBlaze', 'HKVitals', 'Gritzo']
    products = {
        'MuscleBlaze': ['Whey Protein', 'Creatine', 'Mass Gainer', 'BCAA'],
        'HKVitals': ['Multivitamin', 'Omega-3', 'Vitamin D', 'Calcium'],
        'Gritzo': ['Kids Protein', 'Kids Multivitamin', 'Growth Formula']
    }
    
    platforms = ['Instagram', 'YouTube', 'Twitter', 'TikTok']
    categories = ['Fitness', 'Nutrition', 'Lifestyle', 'Health', 'Sports']
    genders = ['Male', 'Female', 'Other']
    
    # Generate influencers data
    influencers_data = []
    for i in range(50):
        follower_count = random.randint(10000, 2000000)
        tier = 'Micro' if follower_count < 100000 else 'Macro' if follower_count < 500000 else 'Mega'
        influencer = {
            'influencer_id': f'INF_{i+1:03d}',
            'name': f'Influencer_{i+1}',
            'category': random.choice(categories),
            'gender': random.choice(genders),
            'follower_count': follower_count,
            'platform': random.choice(platforms),
            'tier': tier
        }
        influencers_data.append(influencer)
    
    influencers_df = pd.DataFrame(influencers_data)
    
    # Generate posts data
    posts_data = []
    for i in range(200):
        influencer = random.choice(influencers_data)
        brand = random.choice(brands)
        product = random.choice(products[brand])
        
        # Assign campaign type
        campaign_type = 'Test' if random.random() > 0.2 else 'Control'
        
        base_reach = min(influencer['follower_count'] * random.uniform(0.1, 0.3), influencer['follower_count'])
        
        post = {
            'post_id': f'POST_{i+1:03d}',
            'influencer_id': influencer['influencer_id'],
            'platform': influencer['platform'],
            'brand': brand,
            'product': product,
            'campaign_type': campaign_type,
            'date': datetime.now() - timedelta(days=random.randint(1, 90)),
            'url': f'https://{influencer["platform"].lower()}.com/post/{i+1}',
            'caption': f'Check out this amazing {product} from {brand}! #sponsored',
            'reach': int(base_reach),
            'likes': int(base_reach * random.uniform(0.02, 0.08)),
            'comments': int(base_reach * random.uniform(0.005, 0.02)),
            'shares': int(base_reach * random.uniform(0.001, 0.01))
        }
        posts_data.append(post)
    
    posts_df = pd.DataFrame(posts_data)
    
    # Generate tracking data (conversion data)
    tracking_data = []
    for i in range(500):
        post = random.choice(posts_data)
        
        conversion_rate = random.uniform(0.001, 0.005)
        orders = max(1, int(post['reach'] * conversion_rate))
        
        for order in range(orders):
            tracking = {
                'tracking_id': f'TRK_{len(tracking_data)+1:04d}',
                'source': 'influencer',
                'campaign': f'{post["brand"]}_{post["product"]}_campaign',
                'influencer_id': post['influencer_id'],
                'user_id': f'USER_{random.randint(1000, 9999)}',
                'brand': post['brand'],
                'product': post['product'],
                'date': post['date'] + timedelta(days=random.randint(0, 7)),
                'orders': 1,
                'revenue': random.uniform(500, 3000),
                'platform': post['platform'],
                'campaign_type': post['campaign_type']
            }
            tracking_data.append(tracking)
    
    tracking_df = pd.DataFrame(tracking_data)
    
    # Generate payouts data
    payouts_data = []
    for influencer in influencers_data:
        basis = random.choice(['post', 'order'])
        
        if basis == 'post':
            if influencer['follower_count'] < 100000:
                rate = random.uniform(5000, 15000)
            elif influencer['follower_count'] < 500000:
                rate = random.uniform(15000, 50000)
            else:
                rate = random.uniform(50000, 150000)
            
            posts_count = len(posts_df[posts_df['influencer_id'] == influencer['influencer_id']])
            total_payout = rate * posts_count
            orders = len(tracking_df[tracking_df['influencer_id'] == influencer['influencer_id']])
            
        else:  # per order
            rate = random.uniform(100, 500)
            orders = len(tracking_df[tracking_df['influencer_id'] == influencer['influencer_id']])
            total_payout = rate * orders
        
        payout = {
            'influencer_id': influencer['influencer_id'],
            'basis': basis,
            'rate': rate,
            'orders': orders,
            'total_payout': total_payout,
            'posts_count': len(posts_df[posts_df['influencer_id'] == influencer['influencer_id']])
        }
        payouts_data.append(payout)
    
    payouts_df = pd.DataFrame(payouts_data)
    
    return influencers_df, posts_df, tracking_df, payouts_df

def calculate_roas_metrics(posts_df, tracking_df, payouts_df):
    """Calculate ROAS and other key metrics"""
    
    # Merge data for comprehensive analysis
    performance_df = posts_df.merge(tracking_df.groupby('influencer_id').agg({
        'revenue': 'sum',
        'orders': 'sum',
        'campaign_type': 'first'
    }).reset_index(), on='influencer_id', how='left')
    
    performance_df = performance_df.merge(payouts_df[['influencer_id', 'total_payout']], 
                                        on='influencer_id', how='left')
    
    # Fill NaN values
    performance_df['revenue'] = performance_df['revenue'].fillna(0)
    performance_df['orders'] = performance_df['orders'].fillna(0)
    performance_df['total_payout'] = performance_df['total_payout'].fillna(0)
    
    # Calculate metrics
    performance_df['roas'] = np.where(performance_df['total_payout'] > 0, 
                                    performance_df['revenue'] / performance_df['total_payout'], 0)
    performance_df['cpo'] = np.where(performance_df['orders'] > 0,
                                   performance_df['total_payout'] / performance_df['orders'], 0)
    performance_df['engagement_rate'] = (performance_df['likes'] + performance_df['comments'] + performance_df['shares']) / performance_df['reach']
    
    return performance_df

def calculate_incremental_roas(tracking_df, payouts_df):
    """
    Calculates incremental ROAS based on Test vs. Control groups.
    Assumes campaigns are properly tagged in tracking_df.
    """
    test_revenue = tracking_df[tracking_df['campaign_type'] == 'Test']['revenue'].sum()
    control_revenue = tracking_df[tracking_df['campaign_type'] == 'Control']['revenue'].sum()
    
    test_spend = payouts_df.merge(
        tracking_df[tracking_df['campaign_type'] == 'Test'][['influencer_id']].drop_duplicates(),
        on='influencer_id'
    )['total_payout'].sum()
    
    if control_revenue > 0:
        incremental_lift = (test_revenue / control_revenue) - 1
    else:
        incremental_lift = 0
    
    if test_spend > 0:
        incremental_roas = (test_revenue - control_revenue) / test_spend
    else:
        incremental_roas = 0
    
    return incremental_roas, incremental_lift

def generate_ai_insights(filtered_df, influencers_df):
    """
    Generates dynamic, AI-like insights based on the filtered data.
    """
    insights = []
    
    # Insight 1: Compare ROAS by Influencer Tier
    tier_roas = filtered_df.merge(
        influencers_df[['influencer_id', 'tier']],
        on='influencer_id'
    ).groupby('tier').agg(
        total_revenue=('revenue', 'sum'),
        total_payout=('total_payout', 'sum')
    )
    tier_roas['roas'] = np.where(tier_roas['total_payout'] > 0, tier_roas['total_revenue'] / tier_roas['total_payout'], 0)
    
    if not tier_roas.empty:
        best_tier = tier_roas['roas'].idxmax()
        worst_tier = tier_roas['roas'].idxmin()
        if best_tier != worst_tier:
            roas_best = tier_roas.loc[best_tier, 'roas']
            roas_worst = tier_roas.loc[worst_tier, 'roas']
            
            # Simple simulation of a recommendation
            if roas_best > roas_worst * 1.5:
                insights.append(
                    f"**Performance Optimization:** {best_tier}-influencers show {roas_best:.2f}x ROAS vs {roas_worst:.2f}x for {worst_tier}-influencers. "
                    "Recommend reallocating budget to the {best_tier}-tier for optimal ROI."
                )
    
    # Insight 2: Platform Intelligence
    platform_roas = filtered_df.groupby('platform').agg(
        total_revenue=('revenue', 'sum'),
        total_payout=('total_payout', 'sum')
    )
    platform_roas['roas'] = np.where(platform_roas['total_payout'] > 0, platform_roas['total_revenue'] / platform_roas['total_payout'], 0)
    
    if not platform_roas.empty and len(platform_roas) > 1:
        top_platform = platform_roas.nlargest(1, 'roas').index[0]
        top_roas = platform_roas.loc[top_platform, 'roas']
        
        insights.append(
            f"**Platform Intelligence:** **{top_platform}** is the highest performing platform with a ROAS of {top_roas:.2f}x. "
            "Consider increasing budget allocation to this platform to maximize returns."
        )
    
    # Insight 3: Product Strategy
    product_roas = filtered_df.groupby('product').agg(
        total_revenue=('revenue', 'sum'),
        total_payout=('total_payout', 'sum')
    )
    product_roas['roas'] = np.where(product_roas['total_payout'] > 0, product_roas['total_revenue'] / product_roas['total_payout'], 0)
    
    if not product_roas.empty and len(product_roas) > 1:
        top_product = product_roas.nlargest(1, 'roas').index[0]
        top_product_roas = product_roas.loc[top_product, 'roas']
        
        insights.append(
            f"**Product Strategy:** **{top_product}** campaigns demonstrate the highest ROAS at {top_product_roas:.2f}x. "
            "Focus marketing efforts on this product for optimal ROI."
        )
    
    if not insights:
        insights.append("No specific insights generated for the current filtered data.")
        
    return insights

# --- Main Dashboard Application ---
def main():
    
    st.sidebar.title("Configuration")
    
    page_selection = st.sidebar.radio(
        "Go to",
        ("Dashboard", "Data Upload")
    )

    if page_selection == "Data Upload":
        data_upload_page()
    else:
        dashboard_page()

def data_upload_page():
    st.markdown('<h1 class="main-header"> Data Upload Interface</h1>', unsafe_allow_html=True)
    manager = DataIngestionManager()
    
    st.info("Upload your campaign data files to use them in the dashboard.")
    
    # File upload section
    upload_tabs = st.tabs(["Influencers", "Posts", "Tracking Data", "Payouts"])
    
    uploaded_dfs = {}
    for i, data_type in enumerate(['influencers', 'posts', 'tracking_data', 'payouts']):
        with upload_tabs[i]:
            uploaded_file = st.file_uploader(
                f"Upload {data_type} CSV file",
                type=['csv'],
                key=f'uploader_{data_type}',
                help=f"Required columns: {', '.join(manager.required_schemas[data_type])}"
            )
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    is_valid, message = manager.validate_schema(df, data_type)
                    
                    if is_valid:
                        st.success(f" Schema validation passed for {data_type}.")
                        df_clean = manager.clean_data(df, data_type)
                        uploaded_dfs[data_type] = df_clean
                        st.dataframe(df_clean.head(5))
                        st.session_state[f'{data_type}_df'] = df_clean
                    else:
                        st.error(f" {message}")
                except Exception as e:
                    st.error(f"Error processing {data_type} file: {str(e)}")
                    
    if uploaded_dfs:
        st.session_state.data_loaded = True
        st.success("All required files uploaded and validated. You can now switch to the Dashboard.")
    else:
        st.warning("No files uploaded yet. The dashboard will use sample data.")
        
    st.subheader(" Download Templates")
    templates = {
        'influencers': pd.DataFrame({
            'influencer_id': ['INF_001', 'INF_002'], 'name': ['John Doe', 'Jane Smith'],
            'category': ['Fitness', 'Nutrition'], 'gender': ['Male', 'Female'],
            'follower_count': [50000, 100000], 'platform': ['Instagram', 'YouTube'], 'tier': ['Micro', 'Macro']
        }).to_csv(index=False).encode('utf-8'),
        'posts': pd.DataFrame({
            'influencer_id': ['INF_001', 'INF_002'], 'platform': ['Instagram', 'YouTube'],
            'date': ['2025-07-01', '2025-07-02'], 'reach': [10000, 25000],
            'likes': [500, 1250], 'comments': [50, 125], 'brand': ['MuscleBlaze', 'HKVitals'],
            'product': ['Whey Protein', 'Multivitamin'], 'campaign_type': ['Test', 'Control']
        }).to_csv(index=False).encode('utf-8'),
        'tracking_data': pd.DataFrame({
            'influencer_id': ['INF_001', 'INF_002'], 'campaign': ['MB_Whey', 'HKV_Multi'],
            'orders': [10, 15], 'revenue': [15000, 22500], 'date': ['2025-07-01', '2025-07-02'],
            'campaign_type': ['Test', 'Control']
        }).to_csv(index=False).encode('utf-8'),
        'payouts': pd.DataFrame({
            'influencer_id': ['INF_001', 'INF_002'], 'basis': ['post', 'order'],
            'rate': [5000, 200], 'total_payout': [15000, 3000]
        }).to_csv(index=False).encode('utf-8')
    }
    
    col1, col2, col3, col4 = st.columns(4)
    for i, (template_type, csv_data) in enumerate(templates.items()):
        col = [col1, col2, col3, col4][i]
        with col:
            st.download_button(
                label=f" {template_type.title()}",
                data=csv_data,
                file_name=f"{template_type}_template.csv",
                mime='text/csv'
            )

def dashboard_page():
    st.markdown('<h1 class="main-header"> HealthKart Influencer ROI Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner('Loading campaign data...'):
        if st.session_state.data_loaded:
            influencers_df = st.session_state.influencers_df
            posts_df = st.session_state.posts_df
            tracking_df = st.session_state.tracking_df
            payouts_df = st.session_state.payouts_df
        else:
            # Use simulated data if none is uploaded
            influencers_df, posts_df, tracking_df, payouts_df = generate_sample_data()
        
        performance_df = calculate_roas_metrics(posts_df, tracking_df, payouts_df)
    
    # Sidebar filters
    st.sidebar.header(" Filters")
    
    brands = ['All'] + list(posts_df['brand'].unique())
    selected_brand = st.sidebar.selectbox('Select Brand', brands)
    
    platforms = ['All'] + list(posts_df['platform'].unique())
    selected_platform = st.sidebar.selectbox('Select Platform', platforms)
    
    date_range = st.sidebar.date_input(
        'Date Range',
        value=(posts_df['date'].min().date(), posts_df['date'].max().date()),
        min_value=posts_df['date'].min().date(),
        max_value=posts_df['date'].max().date()
    )
    
    tiers = ['All'] + list(influencers_df['tier'].unique())
    selected_tier = st.sidebar.selectbox('Influencer Tier', tiers)
    
    # Apply filters
    filtered_df = performance_df.copy()
    
    if selected_brand != 'All':
        filtered_df = filtered_df[filtered_df['brand'] == selected_brand]
    
    if selected_platform != 'All':
        filtered_df = filtered_df[filtered_df['platform'] == selected_platform]
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= date_range[0]) & 
            (filtered_df['date'].dt.date <= date_range[1])
        ]
    
    if selected_tier != 'All':
        tier_influencers = influencers_df[influencers_df['tier'] == selected_tier]['influencer_id'].tolist()
        filtered_df = filtered_df[filtered_df['influencer_id'].isin(tier_influencers)]

    # --- New Metrics and Sections ---
    st.header(" Campaign Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    total_revenue = filtered_df['revenue'].sum()
    total_spend = filtered_df['total_payout'].sum()
    overall_roas = total_revenue / total_spend if total_spend > 0 else 0
    
    with col1:
        st.metric(label="Total Revenue", value=f"₹{total_revenue:,.0f}")
    with col2:
        st.metric(label="Total Spend", value=f"₹{total_spend:,.0f}")
    with col3:
        st.metric(label="ROAS", value=f"{overall_roas:.2f}x")
    with col4:
        st.metric(label="Total Orders", value=f"{filtered_df['orders'].sum():,.0f}")
    
    # Incremental ROAS Section
    st.header(" Incremental ROAS Analysis")
    
    incremental_roas, incremental_lift = calculate_incremental_roas(tracking_df, payouts_df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Incremental ROAS", value=f"{incremental_roas:.2f}x")
    with col2:
        st.metric(label="Incremental Revenue Lift", value=f"{incremental_lift:.1%}")

    # Charts
    st.header(" Performance Analytics")
    col1, col2 = st.columns(2)
    
    with col1:
        brand_roas = filtered_df.groupby('brand').agg(
            revenue=('revenue', 'sum'),
            total_payout=('total_payout', 'sum')
        ).reset_index()
        brand_roas['roas'] = brand_roas['revenue'] / brand_roas['total_payout']
        fig_brand_roas = px.bar(
            brand_roas, x='brand', y='roas', title='ROAS by Brand', color='roas', color_continuous_scale='Greens'
        )
        st.plotly_chart(fig_brand_roas, use_container_width=True)
    
    with col2:
        platform_metrics = filtered_df.groupby('platform').agg(
            revenue=('revenue', 'sum'),
            total_payout=('total_payout', 'sum')
        ).reset_index()
        fig_platform = go.Figure()
        fig_platform.add_trace(go.Bar(name='Revenue', x=platform_metrics['platform'], y=platform_metrics['revenue']))
        fig_platform.add_trace(go.Bar(name='Spend', x=platform_metrics['platform'], y=platform_metrics['total_payout']))
        fig_platform.update_layout(title='Revenue vs Spend by Platform', barmode='group')
        st.plotly_chart(fig_platform, use_container_width=True)
    
    # AI Insights Engine
    st.header(" AI-Powered Insights")
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    insights = generate_ai_insights(filtered_df, influencers_df)
    for insight in insights:
        st.markdown(f"**- {insight}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # Detailed Data Table
    st.header(" Detailed Campaign Data")
    detailed_view = filtered_df.merge(
        influencers_df[['influencer_id', 'name', 'follower_count', 'category', 'tier']], 
        on='influencer_id'
    )
    display_columns = [
        'name', 'tier', 'brand', 'product', 'platform', 'date', 
        'reach', 'revenue', 'orders', 'total_payout', 'roas'
    ]
    st.dataframe(
        detailed_view[display_columns].round(2),
        use_container_width=True,
        height=400
    )
    
if __name__ == "__main__":
    main()