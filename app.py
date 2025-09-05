"""
Fitness Dashboard - Main Application with Dynamic Workout Pages
A Streamlit app for tracking and visualizing personal fitness data from Google Sheets
"""

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import utility functions
from utils.data_loader import load_workout_data, test_connection, get_unique_workouts
from pages.workout_page_generator import (
    show_workout_selection_page, 
    show_individual_workout_page,
    get_workout_page_navigation
)

# Configure Streamlit page
st.set_page_config(
    page_title="Fitness Dashboard",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application function"""
    
    # App header
    st.title("💪 Personal Fitness Dashboard")
    st.markdown("---")
    
    # Load data first
    with st.spinner("Loading workout data..."):
        df = load_workout_data()
    
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
        
        # Refresh data button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.success("Cache cleared! Data will refresh on next load.")
            st.rerun()
        
        # Show data status
        if df is not None and not df.empty:
            st.success(f"✅ {len(df)} workout sessions loaded")
            unique_workouts = get_unique_workouts(df)
            st.info(f"📊 {len(unique_workouts)} workout types found")
        else:
            st.error("❌ No data loaded")
        
        st.markdown("---")
        
        # Page selection - but handle workout pages dynamically
        selected_workout = get_workout_page_navigation()
        
        if selected_workout:
            # We're viewing a specific workout page
            st.write(f"**Current View:**")
            st.write(f"🎯 {selected_workout}")
            
            # Option to return to workout selection
            if st.button("← Back to Workout Types"):
                if 'selected_workout' in st.session_state:
                    del st.session_state.selected_workout
                st.rerun()
        else:
            # Normal page navigation
            page = st.selectbox(
                "Choose a page:",
                ["🏠 Home", "📊 Summary", "🎯 Workout Types", "📈 Progress Tracking"],
                index=0
            )
        
        st.markdown("---")
        st.markdown("**System Info**")
        st.caption(f"Sheet: {os.getenv('GOOGLE_SHEET_NAME', 'Not configured')}")
        st.caption(f"Refresh: {os.getenv('REFRESH_INTERVAL', '60')}s")
        
        # Quick stats in sidebar
        if df is not None and not df.empty:
            st.markdown("**Quick Stats**")
            total_sessions = len(df)
            if 'Date' in df.columns and df['Date'].notna().any():
                date_range = (df['Date'].max() - df['Date'].min()).days
                st.caption(f"📅 {date_range} days tracked")
            st.caption(f"🏋️ {total_sessions} total sessions")
    
    # Handle page routing
    if df is None:
        show_connection_error()
        return
    
    if df.empty:
        show_no_data_message()
        return
    
    # Check if we're viewing a specific workout
    selected_workout = get_workout_page_navigation()
    
    if selected_workout:
        # Show individual workout page
        show_individual_workout_page(df, selected_workout)
    else:
        # Show normal pages
        if 'page' not in locals():
            page = "🏠 Home"  # Default if no page selected
        
        if page == "🏠 Home":
            show_home_page(df)
        elif page == "📊 Summary":
            show_summary_page(df)
        elif page == "🎯 Workout Types":
            show_workout_selection_page(df)
        elif page == "📈 Progress Tracking":
            show_progress_page(df)

def show_connection_error():
    """Show connection error page"""
    st.error("❌ Failed to Connect to Google Sheets")
    
    st.markdown("""
    ### Troubleshooting Steps:
    
    1. **Check your Google Sheets connection** using the sidebar button
    2. **Verify your service account credentials** are properly configured
    3. **Ensure your sheet is shared** with the service account email
    4. **Check your environment variables** in the .env file
    
    ### Need Help?
    - Check the README.md for setup instructions
    - Verify your Google Cloud Console settings
    - Test with a simple sheet first
    """)

def show_no_data_message():
    """Show no data message"""
    st.warning("📝 No Data Found")
    
    st.markdown("""
    ### Your Google Sheets appears to be empty or has no readable data.
    
    **Please check:**
    - Your sheet contains workout data
    - Column headers are properly formatted
    - The 'master_tracker' worksheet exists (or update your .env file)
    - Data starts from row 2 (headers in row 1)
    
    **Expected format:**
    - `date` column with workout dates
    - `workout` column with workout type names
    - `movement_1`, `weight_1`, `rep_1`, `set_1` columns for exercises
    """)

def show_home_page(df: pd.DataFrame):
    """Display the home/welcome page"""
    
    st.header("Welcome to Your Fitness Dashboard! 🏋️‍♂️")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### What This Dashboard Does
        
        This personal fitness dashboard connects to your Google Sheets workout log to provide:
        
        - **🔄 Real-time data sync** from your Google Sheets
        - **📊 Interactive visualizations** of your workout patterns  
        - **🎯 Dedicated pages** for each workout type with deep analysis
        - **📈 Progress tracking** for individual movements and PRs
        - **📱 Mobile-friendly** interface for checking stats on the go
        
        ### Quick Navigation
        
        1. **📊 Summary**: Overview of all your fitness data
        2. **🎯 Workout Types**: Dedicated analysis for each workout type
        3. **📈 Progress Tracking**: Long-term trends and improvements
        
        ### Privacy First 🔒
        
        Your data never leaves your control - it flows directly from your Google Sheets to this dashboard.
        """)
    
    with col2:
        st.info("""
        **Your Fitness Data**
        """)
        
        # Show current stats
        if not df.empty:
            unique_workouts = get_unique_workouts(df)
            
            st.metric("Total Sessions", len(df))
            st.metric("Workout Types", len(unique_workouts))
            
            if 'Date' in df.columns and df['Date'].notna().any():
                latest_workout = df['Date'].max()
                days_since = (pd.Timestamp.now() - latest_workout).days
                st.metric("Days Since Last Workout", days_since)
            
            # Show workout types
            st.markdown("**Your Workout Types:**")
            for workout in unique_workouts[:5]:  # Show first 5
                st.write(f"• {workout}")
            
            if len(unique_workouts) > 5:
                st.write(f"• ... and {len(unique_workouts) - 5} more")
            
            st.markdown("---")
            if st.button("🎯 Explore Workout Types", use_container_width=True):
                st.session_state.page = "🎯 Workout Types"
                st.rerun()

def show_summary_page(df: pd.DataFrame):
    """Display the summary dashboard"""
    st.header("📊 Fitness Summary")
    
    try:        
        if df.empty:
            st.warning("📝 No data found. Please check your Google Sheets has data.")
            return
            
        # Display basic metrics
        st.success(f"✅ Successfully loaded {len(df)} workout sessions")
        
        # Import visualization functions
        from utils.data_loader import get_data_summary, extract_movements_from_workout
        
        # Get summary stats
        summary = get_data_summary(df)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", summary['total_records'])
        with col2:
            st.metric("Workout Types", summary['unique_workouts'])
        with col3:
            st.metric("Unique Movements", summary.get('unique_movements', 0))
        with col4:
            st.metric("Total Movement Entries", summary.get('total_movement_entries', 0))
        
        # Show data structure info
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Data Overview")
            st.write("**Date Range:**", summary['date_range'])
            st.write("**Columns found:**", len(summary['columns']))
            
            # Show workout types
            unique_workouts = get_unique_workouts(df)
            st.write("**Workout Types:**")
            for workout in unique_workouts:
                workout_count = len(df[df['Workout'] == workout])
                st.write(f"• {workout}: {workout_count} sessions")
        
        with col2:
            st.subheader("🔍 Data Preview")
            # Show a sample of the processed data
            display_cols = ['Date', 'Workout']
            if 'Start_Time' in df.columns:
                display_cols.append('Start_Time')
            
            preview_df = df[display_cols].head(10)
            if 'Date' in preview_df.columns:
                preview_df['Date'] = preview_df['Date'].dt.strftime('%Y-%m-%d')
            if 'Start_Time' in preview_df.columns:
                preview_df['Start_Time'] = preview_df['Start_Time'].dt.strftime('%H:%M')
            
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
        
        # Movement analysis
        st.subheader("🏋️ Movement Analysis")
        movements_df = extract_movements_from_workout(df)
        
        if not movements_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Most common movements overall
                movement_counts = movements_df['movement'].value_counts().head(10)
                
                import plotly.express as px
                fig = px.bar(
                    x=movement_counts.values,
                    y=movement_counts.index,
                    orientation='h',
                    title="Most Common Movements (All Workouts)",
                    labels={'x': 'Times Performed', 'y': 'Movement'}
                )
                fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Workout frequency
                workout_counts = df['Workout'].value_counts().head(10)
                
                fig = px.bar(
                    x=workout_counts.values,
                    y=workout_counts.index,
                    orientation='h',
                    title="Most Frequent Workout Types",
                    labels={'x': 'Number of Sessions', 'y': 'Workout Type'}
                )
                fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Quick navigation to workout types
        st.markdown("---")
        st.subheader("🎯 Explore Individual Workouts")
        
        col1, col2, col3 = st.columns(3)
        unique_workouts = get_unique_workouts(df)
        
        for i, workout in enumerate(unique_workouts[:6]):  # Show first 6 workouts
            col = [col1, col2, col3][i % 3]
            
            with col:
                workout_sessions = len(df[df['Workout'] == workout])
                
                if st.button(
                    f"🎯 {workout}\n({workout_sessions} sessions)", 
                    key=f"quick_nav_{workout}",
                    use_container_width=True
                ):
                    st.session_state.selected_workout = workout
                    st.rerun()
        
        if len(unique_workouts) > 6:
            st.info(f"And {len(unique_workouts) - 6} more workout types available in the Workout Types page!")
        
    except Exception as e:
        st.error(f"❌ Error loading summary data: {str(e)}")
        
        # Additional debugging info
        with st.expander("🔧 Debug Information"):
            st.write("**Error details:**")
            st.code(str(e))
            st.write("**Environment variables:**")
            st.write({
                "GOOGLE_SHEET_NAME": os.getenv('GOOGLE_SHEET_NAME', 'Not set'),
                "GOOGLE_SHEET_WORKSHEET": os.getenv('GOOGLE_SHEET_WORKSHEET', 'Not set')
            })

def show_progress_page(df: pd.DataFrame):
    """Display overall progress tracking across all workouts"""
    st.header("📈 Overall Progress Tracking")
    
    from utils.data_loader import extract_movements_from_workout
    
    movements_df = extract_movements_from_workout(df)
    
    if movements_df.empty:
        st.warning("No movement data available for progress analysis.")
        return
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_volume = (movements_df['weight'].fillna(0) * 
                   movements_df['reps'].fillna(0) * 
                   movements_df['sets'].fillna(0)).sum()
    
    total_reps = movements_df['reps'].fillna(0).sum()
    unique_movements = movements_df['movement'].nunique()
    active_days = movements_df['date'].nunique()
    
    with col1:
        st.metric("Total Volume", f"{total_volume:,.0f}", help="Weight × Reps × Sets")
    with col2:
        st.metric("Total Reps", f"{total_reps:,.0f}")
    with col3:
        st.metric("Unique Movements", unique_movements)
    with col4:
        st.metric("Active Days", active_days)
    
    # Progress over time
    st.subheader("📊 Progress Over Time")
    
    # Monthly volume progression
    if 'date' in movements_df.columns and movements_df['date'].notna().any():
        monthly_data = movements_df.copy()
        monthly_data['month'] = monthly_data['date'].dt.to_period('M')
        monthly_data['volume'] = (monthly_data['weight'].fillna(0) * 
                                 monthly_data['reps'].fillna(0) * 
                                 monthly_data['sets'].fillna(0))
        
        monthly_summary = monthly_data.groupby('month').agg({
            'volume': 'sum',
            'session_id': 'nunique',
            'movement': 'count'
        }).reset_index()
        
        monthly_summary['month_str'] = monthly_summary['month'].astype(str)
        
        col1, col2 = st.columns(2)
        
        with col1:
            import plotly.express as px
            fig = px.line(
                monthly_summary,
                x='month_str',
                y='volume',
                title="Monthly Training Volume",
                labels={'month_str': 'Month', 'volume': 'Total Volume'},
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(
                monthly_summary,
                x='month_str',
                y='session_id',
                title="Monthly Workout Sessions",
                labels={'month_str': 'Month', 'session_id': 'Number of Sessions'},
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Top performers
    st.subheader("🏆 Top Performing Movements")
    
    movement_stats = movements_df.groupby('movement').agg({
        'weight': ['count', 'max', 'mean'],
        'reps': 'sum',
        'sets': 'sum'
    }).round(2)
    
    movement_stats.columns = ['Sessions', 'Max Weight', 'Avg Weight', 'Total Reps', 'Total Sets']
    movement_stats['Total Volume'] = (
        movement_stats['Avg Weight'] * 
        movement_stats['Total Reps']
    ).round(0)
    
    # Show top movements by different metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Most Frequent Movements**")
        top_frequent = movement_stats.nlargest(10, 'Sessions')[['Sessions', 'Total Volume']]
        st.dataframe(top_frequent, use_container_width=True)
    
    with col2:
        st.write("**Highest Volume Movements**")
        top_volume = movement_stats.nlargest(10, 'Total Volume')[['Total Volume', 'Sessions']]
        st.dataframe(top_volume, use_container_width=True)
    
    # Navigation to specific workouts
    st.markdown("---")
    st.subheader("🎯 Dive Deeper")
    st.markdown("For detailed progress analysis of specific movements, visit the individual workout pages:")
    
    unique_workouts = get_unique_workouts(df)
    
    # Create buttons for each workout type
    cols = st.columns(min(len(unique_workouts), 4))
    for i, workout in enumerate(unique_workouts):
        col_idx = i % 4
        with cols[col_idx]:
            if st.button(f"📊 {workout}", key=f"progress_nav_{workout}", use_container_width=True):
                st.session_state.selected_workout = workout
                st.rerun()

if __name__ == "__main__":
    main()