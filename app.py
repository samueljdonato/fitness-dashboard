"""
Fitness Dashboard - Main Application
A Streamlit app for tracking and visualizing personal fitness data from Google Sheets
"""

import streamlit as st
import pandas as pd
import plotly.express as px
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
    # page_icon="💪",
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
        
        # Page selection - handle both main pages and dynamic workout pages
        selected_workout = get_workout_page_navigation()
        
        if selected_workout:
            # We're viewing a specific workout page
            st.write(f"**Current View:**")
            st.write(f"🎯 {selected_workout}")
            
            # Quick workout switcher
            if df is not None and not df.empty:
                other_workouts = [w for w in get_unique_workouts(df) if w != selected_workout]
                if other_workouts:
                    st.write("**Quick Switch:**")
                    selected_switch = st.selectbox(
                        "Switch to workout:",
                        ["← Select different workout..."] + other_workouts,
                        key="workout_switcher"
                    )
                    
                    if selected_switch != "← Select different workout...":
                        st.session_state.selected_workout = selected_switch
                        st.rerun()
            
            st.markdown("---")
            
            # Option to return to main navigation
            if st.button("← Back to Main Menu"):
                if 'selected_workout' in st.session_state:
                    del st.session_state.selected_workout
                st.rerun()
        else:
            # Main navigation with workout options
            page_options = ["📊 Summary", "🎯 Workout Types", "📈 Progress Tracking"]
            
            # Add individual workout pages if data is available
            if df is not None and not df.empty:
                unique_workouts = get_unique_workouts(df)
                st.write("**📋 Main Pages:**")
                page = st.selectbox(
                    "Choose a main page:",
                    page_options,
                    index=0,
                    key="main_page_selector"
                )
                
                # Add workout-specific navigation
                if unique_workouts:
                    st.markdown("---")
                    st.write("**🎯 Individual Workouts:**")
                    st.caption(f"Click any workout to view detailed analysis")
                    
                    # Sort workouts by number of sessions (most frequent first)
                    workout_data = [(workout, len(df[df['Workout'] == workout])) for workout in unique_workouts]
                    workout_data.sort(key=lambda x: x[1], reverse=True)
                    
                    # Create buttons for each workout type with session counts
                    for workout, session_count in workout_data:
                        button_label = f"📊 {workout} ({session_count} sessions)"
                        if st.button(button_label, key=f"nav_to_{workout}", use_container_width=True):
                            st.session_state.selected_workout = workout
                            st.rerun()
            else:
                # Fallback if no data loaded
                page = st.selectbox(
                    "Choose a page:",
                    page_options,
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
            page = "📊 Summary"  # Default if no page selected
        
        if page == "📊 Summary":
            show_summary_page()
        elif page == "🎯 Workout Types":
            show_workout_selection_page(df)
        elif page == "📈 Progress Tracking":
            show_progress_page()

# def show_home_page():
#     """Display the home/welcome page"""
    
#     st.header("Welcome to Your Fitness Dashboard! 🏋️‍♂️")
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         st.markdown("""
#         ### What This Dashboard Does
        
#         This personal fitness dashboard connects to your Google Sheets workout log to provide:
        
#         - **Real-time data sync** from your Google Sheets
#         - **Interactive visualizations** of your workout patterns
#         - **Detailed analysis** of specific workouts and movements
#         - **Progress tracking** over time
#         - **Mobile-friendly** interface for checking stats on the go
        
#         ### Getting Started
        
#         1. **Test Connection**: Use the button in the sidebar to verify your Google Sheets connection
#         2. **Explore Summary**: Check out your overall fitness metrics
#         3. **Dive Deep**: Analyze specific workouts and movements
#         4. **Track Progress**: Monitor your improvements over time
        
#         ### Privacy First 🔒
        
#         Your data never leaves your control - it flows directly from your Google Sheets to this dashboard.
#         """)
    
#     with col2:
#         st.info("""
#         **Quick Stats Preview**
        
#         Connect your Google Sheets to see:
#         - Total workouts logged
#         - Unique movements tracked  
#         - Personal records achieved
#         - Recent activity summary
#         """)
        
#         # Try to load basic stats if connection works
#         try:
#             df = load_workout_data()
#             if df is not None and not df.empty:
#                 st.success("✅ Google Sheets Connected!")
#                 st.metric("Total Records", len(df))
#         except Exception as e:
#             st.warning("⚠️ Google Sheets not connected yet")
#             st.caption("Use the connection test button to troubleshoot")

def show_summary_page():
    """Display the comprehensive fitness summary dashboard"""
    st.header("Fitness Summary Dashboard")
    
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
            
        # # DEBUG: Show actual column names first
        # st.write("**DEBUG - Actual columns in your data:**")
        # st.write(list(df.columns))
        # st.write("**DEBUG - First few rows:**")
        # st.dataframe(df.head(3), use_container_width=True)
        
        # Try to identify the correct column names
        # Look for common variations
        date_col = None
        workout_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if 'date' in col_lower:
                date_col = col
            elif 'workout' in col_lower:
                workout_col = col
                
        # st.write(f"**DEBUG - Found date column:** {date_col}")
        # st.write(f"**DEBUG - Found workout column:** {workout_col}")
        
        if date_col is None or workout_col is None:
            st.error("❌ Could not find 'date' and 'workout' columns. Please check your Google Sheets column names.")
            st.info("Expected columns: 'date' and 'workout' (case-sensitive)")
            return
            
        # Clean up data - remove rows with missing key info
        df_clean = df.dropna(subset=[date_col, workout_col])
        # Clean up "#REF!" values - replace with empty strings
        df_clean = df_clean.replace("#REF!", "")
        df = df.replace("#REF!", "")
        
        
        # Convert date column properly
        df_clean[date_col] = pd.to_datetime(df_clean[date_col])
        
        # === KEY METRICS ROW ===
        st.subheader("🎯 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_sessions = len(df_clean)
            st.metric("Total Sessions", total_sessions)
            
        with col2:
            unique_workouts = df_clean[workout_col].nunique()
            st.metric("Workout Types", unique_workouts)
            
        with col3:
            # Count unique movements across all movement columns
            unique_movements = set()
            movement_cols = [col for col in df.columns if 'movement' in str(col).lower()]
            for col in movement_cols:
                movements = df_clean[col].dropna().unique()
                unique_movements.update([m for m in movements if str(m) != 'nan' and str(m) != ''])
            st.metric("Unique Movements", len(unique_movements))
            
        with col4:
            # Date range
            if len(df_clean) > 0:
                date_range = (df_clean[date_col].max() - df_clean[date_col].min()).days
                st.metric("Training Span", f"{date_range} days")
            
        with col5:
            # Dropdown for recent activity timeframe
            days_options = {"Last 7 Days": 7, "Last 14 Days": 14, "Last 30 Days": 30}
            selected_period = st.selectbox(
                "Recent Activity",
                options=list(days_options.keys()),
                index=2,  # Default to "Last 30 Days"
                key="recent_activity_period"
            )
            
            # Calculate recent activity based on selection
            days = days_options[selected_period]
            recent_cutoff = df_clean[date_col].max() - pd.Timedelta(days=days)
            recent_sessions = len(df_clean[df_clean[date_col] >= recent_cutoff])
            st.metric(selected_period, f"{recent_sessions} sessions")

        # === WORKOUT FREQUENCY ANALYSIS ===
        st.subheader("🏋️ Workout Frequency")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Workout frequency bar chart
            workout_counts = df_clean[workout_col].value_counts()
            fig = px.bar(
                x=workout_counts.values,
                y=workout_counts.index,
                orientation='h',
                title="Sessions by Workout Type",
                labels={'x': 'Number of Sessions', 'y': 'Workout Type'},
                color=workout_counts.values,
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Workout type pie chart
            fig_pie = px.pie(
                values=workout_counts.values,
                names=workout_counts.index,
                title="Workout Distribution"
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        # === TRAINING TIMELINE ===
        st.subheader("📅 Training Timeline")
        
        # Group by date to handle multiple sessions per day
        daily_sessions = df_clean.groupby(df_clean[date_col].dt.date).size().reset_index()
        daily_sessions.columns = ['date', 'sessions']
        daily_sessions['date'] = pd.to_datetime(daily_sessions['date'])
        
        fig_timeline = px.scatter(
            daily_sessions,
            x='date',
            y='sessions',
            size='sessions',
            title="Workout Activity Over Time",
            labels={'sessions': 'Sessions per Day', 'date': 'Date'},
            color='sessions',
            color_continuous_scale='blues'
        )
        fig_timeline.update_layout(height=300)
        st.plotly_chart(fig_timeline, use_container_width=True)

 # === MOVEMENT ANALYSIS ===
        st.subheader("💪 Movement Analysis")
        
        # Extract all movements and their frequencies
        movement_frequency = {}
        movement_cols = [col for col in df.columns if 'movement' in str(col).lower()]
        
        for movement_col in movement_cols:
            if movement_col in df_clean.columns:
                movements = df_clean[movement_col].dropna()
                for movement in movements:
                    if str(movement) != 'nan' and movement and str(movement).strip():
                        movement_frequency[str(movement).strip()] = movement_frequency.get(str(movement).strip(), 0) + 1
        
        # Show top movements
        if movement_frequency:
            top_movements = sorted(movement_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # col1, col2 = st.columns(1)
            
            # with col1:
                # Top movements bar chart
            movements, counts = zip(*top_movements)
            fig_movements = px.bar(
                x=counts,
                y=movements,
                orientation='h',
                title="Most Frequent Movements (Top 10)",
                labels={'x': 'Times Performed', 'y': 'Movement'},
                color=counts,
                color_continuous_scale='plasma'
            )
            fig_movements.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_movements, use_container_width=True)
        
        #     with col2:
        #         # Recent sessions table (filtered)
        #         if selected_workout_filter == "All Workouts":
        #             table_title = "**Recent Sessions:**"
        #             recent_sessions_data = df_clean.nlargest(8, date_col)
        #         else:
        #             table_title = f"**Recent {selected_workout_filter} Sessions:**"
        #             recent_sessions_data = filtered_df.nlargest(8, date_col)
                
        #         st.write(table_title)
        #         recent_sessions = recent_sessions_data[[date_col, workout_col]].copy()
                
        #         # Add first movement if available
        #         if movement_cols:
        #             recent_sessions['first_movement'] = recent_sessions_data[movement_cols[0]]
                    
        #         recent_sessions[date_col] = recent_sessions[date_col].dt.strftime('%m/%d/%Y')
        #         st.dataframe(recent_sessions, use_container_width=True, hide_index=True)
        # else:
        #     st.info(f"No movement data found for {selected_workout_filter if selected_workout_filter != 'All Workouts' else 'any workouts'}")

        # === PROGRESS TRACKING PREVIEW ===
        st.subheader("📈 Progress Highlights")
        
        # Find movements with enough data for progress analysis
        progress_candidates = []
        for movement, freq in movement_frequency.items():
            if freq >= 3:  # At least 3 sessions
                progress_candidates.append(movement)
        
        if progress_candidates:
            # Let user select a movement to analyze
            selected_movement = st.selectbox(
                "Select a movement to analyze progress:",
                progress_candidates[:10]  # Limit to top 10 for dropdown
            )
            
            if selected_movement:
                # Extract progress data for this movement
                progress_data = []
                weight_cols = [col for col in df.columns if 'weight' in str(col).lower()]
                
                for idx, row in df_clean.iterrows():
                    for i, movement_col in enumerate(movement_cols):
                        if (movement_col in row and 
                            str(row[movement_col]).strip() == selected_movement and 
                            i < len(weight_cols)):
                            
                            weight_col = weight_cols[i] if i < len(weight_cols) else None
                            
                            if weight_col and pd.notna(row[weight_col]) and row[weight_col] != '':
                                try:
                                    weight_val = float(row[weight_col])
                                    progress_data.append({
                                        'date': row[date_col],
                                        'weight': weight_val,
                                        'workout': row[workout_col]
                                    })
                                except (ValueError, TypeError):
                                    continue
                
                if progress_data:
                    progress_df = pd.DataFrame(progress_data)
                    progress_df = progress_df.sort_values('date')
                    
                    # Create progress chart
                    fig_progress = px.line(
                        progress_df,
                        x='date',
                        y='weight',
                        title=f"{selected_movement} - Weight Progress",
                        labels={'weight': 'Weight (lbs)', 'date': 'Date'},
                        markers=True,
                        color_discrete_sequence=['#FF6B6B']
                    )
                    
                    fig_progress.update_layout(height=300)
                    st.plotly_chart(fig_progress, use_container_width=True)
                    
                    # Show progress stats
                    if len(progress_df) > 1:
                        weight_change = progress_df['weight'].iloc[-1] - progress_df['weight'].iloc[0]
                        change_color = "normal" if weight_change >= 0 else "inverse"
                        st.metric(
                            f"{selected_movement} Progress", 
                            f"{progress_df['weight'].iloc[-1]} lbs",
                            f"{weight_change:+.0f} lbs total",
                            delta_color=change_color
                        )
                else:
                    st.info(f"No weight data found for {selected_movement}")

        # Optional: Data quality check (can be hidden)
        with st.expander("🔧 Technical Details"):
            st.write(f"**Total sessions recorded:** {len(df)}")
            st.write(f"**Valid sessions:** {len(df_clean)}")
            if len(df_clean) > 0:
                st.write(f"**Training period:** {df_clean[date_col].min().strftime('%Y-%m-%d')} to {df_clean[date_col].max().strftime('%Y-%m-%d')}")
            st.write(f"**Movement types tracked:** {len([col for col in df.columns if 'movement' in str(col).lower()])}")
            st.write(f"**Workout types:** {', '.join(df_clean[workout_col].unique())}")
            
            # Show recent raw data
            if st.checkbox("Show recent data"):
                st.dataframe(df_clean.tail(5), use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        
        # Enhanced debugging info
        with st.expander("🔧 Debug Information"):
            st.write("**Error details:**")
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())

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

def show_progress_page():
    """Display progress tracking"""
    st.header("📈 Progress Tracking")
    st.info("🚧 Progress tracking will be implemented in Phase 2!")

if __name__ == "__main__":
    main()