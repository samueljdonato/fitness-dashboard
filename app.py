"""
Fitness Dashboard - Main Application
A Streamlit app for tracking and visualizing personal fitness data from Google Sheets
"""

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import utility functions
from utils.data_loader import load_workout_data, test_connection

# Configure Streamlit page
st.set_page_config(
    page_title="Fitness Dashboard",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Import utility functions (after streamlit config)
try:
    from utils.data_loader import load_workout_data, test_connection
except ImportError as e:
    st.error(f"Error importing utilities: {e}")
    st.info("Make sure utils/__init__.py exists and utils modules are properly structured")
    st.stop()

def main():
    """Main application function"""
    
    # App header
    st.title("💪 Personal Fitness Dashboard")
    st.markdown("---")
    
    # Sidebar for navigation and controls
    with st.sidebar:
        st.header("Navigation")
        
        # Test connection button
        if st.button("🔗 Test Google Sheets Connection"):
            with st.spinner("Testing connection..."):
                success, message = test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                    st.stop()
        
        # Refresh data button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.success("Cache cleared! Data will refresh on next load.")
            st.rerun()
        
        # Page selection
        page = st.selectbox(
            "Choose a page:",
            ["🏠 Home", "📊 Summary", "🎯 Workout Details", "📈 Progress Tracking"],
            index=0
        )
        
        st.markdown("---")
        st.markdown("**Debug Info**")
        st.caption(f"Sheet: {os.getenv('GOOGLE_SHEET_NAME', 'Not configured')}")
        st.caption(f"Refresh: {os.getenv('REFRESH_INTERVAL', '60')}s")
    
    # Main content area
    if page == "🏠 Home":
        show_home_page()
    elif page == "📊 Summary":
        show_summary_page()
    elif page == "🎯 Workout Details":
        show_workout_details_page()
    elif page == "📈 Progress Tracking":
        show_progress_page()

def show_home_page():
    """Display the home/welcome page"""
    
    st.header("Welcome to Your Fitness Dashboard! 🏋️‍♂️")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### What This Dashboard Does
        
        This personal fitness dashboard connects to your Google Sheets workout log to provide:
        
        - **Real-time data sync** from your Google Sheets
        - **Interactive visualizations** of your workout patterns
        - **Detailed analysis** of specific workouts and movements
        - **Progress tracking** over time
        - **Mobile-friendly** interface for checking stats on the go
        
        ### Getting Started
        
        1. **Test Connection**: Use the button in the sidebar to verify your Google Sheets connection
        2. **Explore Summary**: Check out your overall fitness metrics
        3. **Dive Deep**: Analyze specific workouts and movements
        4. **Track Progress**: Monitor your improvements over time
        
        ### Privacy First 🔒
        
        Your data never leaves your control - it flows directly from your Google Sheets to this dashboard.
        """)
    
    with col2:
        st.info("""
        **Quick Stats Preview**
        
        Connect your Google Sheets to see:
        - Total workouts logged
        - Unique movements tracked  
        - Personal records achieved
        - Recent activity summary
        """)
        
        # Try to load basic stats if connection works
        try:
            df = load_workout_data()
            if df is not None and not df.empty:
                st.success("✅ Google Sheets Connected!")
                st.metric("Total Records", len(df))
        except Exception as e:
            st.warning("⚠️ Google Sheets not connected yet")
            st.caption("Use the connection test button to troubleshoot")

def show_summary_page():
    """Display the summary dashboard"""
    st.header("📊 Fitness Summary")
    
    try:
        # Load data
        with st.spinner("Loading workout data..."):
            df = load_workout_data()
            
        if df is None:
            st.error("❌ Failed to load data - check your Google Sheets connection")
            return
            
        if df.empty:
            st.warning("📝 No data found. Please check your Google Sheets has data.")
            return
            
        # Display basic metrics
        st.success(f"✅ Successfully loaded {len(df)} records")
        
        # Show column information
        st.subheader("📋 Data Structure")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Columns found:**")
            st.write(list(df.columns))
            
        with col2:
            st.write("**Data types:**")
            st.write(df.dtypes.to_dict())
        
        # Show data preview
        st.subheader("🔍 Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Basic statistics if we have numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            st.subheader("📈 Quick Stats")
            st.write(df[numeric_cols].describe())
        
        # Show unique values for key columns
        st.subheader("🏷️ Unique Values")
        for col in df.columns[:5]:  # Show first 5 columns
            unique_count = df[col].nunique()
            if unique_count < 20:  # Only show if reasonable number
                st.write(f"**{col}**: {unique_count} unique values")
                st.write(df[col].unique()[:10])  # Show first 10
            else:
                st.write(f"**{col}**: {unique_count} unique values (too many to display)")
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        
        # Additional debugging info
        with st.expander("🔧 Debug Information"):
            st.write("**Error details:**")
            st.code(str(e))
            st.write("**Environment variables:**")
            st.write({
                "GOOGLE_SHEET_NAME": os.getenv('GOOGLE_SHEET_NAME', 'Not set'),
                "GOOGLE_SHEET_WORKSHEET": os.getenv('GOOGLE_SHEET_WORKSHEET', 'Not set')
            })

def show_workout_details_page():
    """Display workout detail analysis"""
    st.header("🎯 Workout Details")
    st.info("🚧 Workout detail analysis will be implemented in Phase 2!")

def show_progress_page():
    """Display progress tracking"""
    st.header("📈 Progress Tracking")
    st.info("🚧 Progress tracking will be implemented in Phase 2!")

if __name__ == "__main__":
    main()