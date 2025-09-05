"""
Dynamic Workout Page Generator
Creates dedicated pages for each workout type with comprehensive tracking metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_loader import (
    get_unique_workouts, 
    get_workout_data, 
    extract_movements_from_workout,
    get_workout_summary_stats,
    get_movement_progress_data
)
from utils.visualizations import FITNESS_COLORS
import numpy as np
from datetime import datetime, timedelta

def show_workout_selection_page(df: pd.DataFrame):
    """
    Display the main workout selection page with all available workout types
    """
    st.header("🎯 Workout Analysis Hub")
    st.markdown("Select a workout type to dive deep into your training data and progress.")
    
    # Get unique workouts
    unique_workouts = get_unique_workouts(df)
    
    if not unique_workouts:
        st.warning("No workout types found in your data.")
        return None
    
    # Create workout type cards in a grid
    st.subheader(f"📋 Available Workout Types ({len(unique_workouts)})")
    
    # Calculate grid layout
    cols_per_row = 3
    rows = (len(unique_workouts) + cols_per_row - 1) // cols_per_row
    
    for row in range(rows):
        cols = st.columns(cols_per_row)
        
        for col_idx in range(cols_per_row):
            workout_idx = row * cols_per_row + col_idx
            
            if workout_idx < len(unique_workouts):
                workout_type = unique_workouts[workout_idx]
                
                with cols[col_idx]:
                    # Get basic stats for this workout
                    workout_df = get_workout_data(df, workout_type)
                    session_count = len(workout_df)
                    
                    # Get date range
                    if not workout_df.empty and 'Date' in workout_df.columns:
                        latest_date = workout_df['Date'].max()
                        if pd.notna(latest_date):
                            days_ago = (pd.Timestamp.now() - latest_date).days
                            last_session = f"{days_ago} days ago"
                        else:
                            last_session = "Unknown"
                    else:
                        last_session = "No date data"
                    
                    # Create workout card
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            border: 2px solid #e1e5e9;
                            border-radius: 10px;
                            padding: 1rem;
                            margin: 0.5rem 0;
                            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                            text-align: center;
                        ">
                            <h4 style="margin: 0; color: #2c3e50;">{workout_type}</h4>
                            <p style="margin: 0.5rem 0; color: #6c757d;">
                                📊 {session_count} sessions<br>
                                🕒 Last: {last_session}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Button to view this workout
                        if st.button(f"Analyze {workout_type}", key=f"btn_{workout_type}", use_container_width=True):
                            st.session_state.selected_workout = workout_type
                            st.rerun()
    
    # Overall stats summary
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    total_sessions = len(df)
    total_movements = len(extract_movements_from_workout(df))
    date_range_days = 0
    
    if 'Date' in df.columns and df['Date'].notna().any():
        date_range_days = (df['Date'].max() - df['Date'].min()).days
    
    with col1:
        st.metric("Total Sessions", total_sessions)
    with col2:
        st.metric("Workout Types", len(unique_workouts))
    with col3:
        st.metric("Total Movements", total_movements)
    with col4:
        st.metric("Days Tracked", date_range_days)
    
    return None

def show_individual_workout_page(df: pd.DataFrame, workout_type: str):
    """
    Display detailed analysis page for a specific workout type
    """
    # Back button
    if st.button("← Back to Workout Selection"):
        if 'selected_workout' in st.session_state:
            del st.session_state.selected_workout
        st.rerun()
    
    st.header(f"📊 {workout_type} - Deep Dive Analysis")
    
    # Get workout-specific data
    workout_df = get_workout_data(df, workout_type)
    movements_df = extract_movements_from_workout(workout_df)
    stats = get_workout_summary_stats(workout_df)
    
    if workout_df.empty:
        st.warning(f"No data found for workout type: {workout_type}")
        return
    
    # Summary metrics row
    st.subheader("📈 Overview Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Sessions", 
            stats.get('total_sessions', 0),
            help="Total number of workout sessions recorded"
        )
    
    with col2:
        avg_freq = stats.get('avg_frequency_per_week', 0)
        st.metric(
            "Avg/Week", 
            f"{avg_freq:.1f}",
            help="Average sessions per week"
        )
    
    with col3:
        st.metric(
            "Unique Movements", 
            stats.get('unique_movements', 0),
            help="Number of different exercises performed"
        )
    
    with col4:
        avg_movements = stats.get('avg_movements_per_session', 0)
        st.metric(
            "Avg Movements", 
            f"{avg_movements:.1f}",
            help="Average movements per session"
        )
    
    with col5:
        total_volume = stats.get('total_volume', 0)
        st.metric(
            "Total Volume", 
            f"{total_volume:,.0f}",
            help="Total weight × reps × sets (lbs)"
        )
    
    # Create tabs for different analysis views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Session Overview", 
        "🏋️ Movement Analysis", 
        "📈 Progress Tracking",
        "🎯 Personal Records",
        "📅 Schedule Patterns"
    ])
    
    with tab1:
        show_session_overview(workout_df, movements_df, stats)
    
    with tab2:
        show_movement_analysis(movements_df, workout_type)
    
    with tab3:
        show_progress_tracking(movements_df, workout_type)
    
    with tab4:
        show_personal_records(movements_df, workout_type)
    
    with tab5:
        show_schedule_patterns(workout_df, workout_type)

def show_session_overview(workout_df: pd.DataFrame, movements_df: pd.DataFrame, stats: dict):
    """Show overview of workout sessions"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Session frequency over time
        if not workout_df.empty and 'Date' in workout_df.columns:
            workout_df_clean = workout_df[workout_df['Date'].notna()].copy()
            
            if not workout_df_clean.empty:
                # Group by month for frequency chart
                workout_df_clean['month'] = workout_df_clean['Date'].dt.to_period('M')
                monthly_counts = workout_df_clean.groupby('month').size().reset_index(name='sessions')
                monthly_counts['month_str'] = monthly_counts['month'].astype(str)
                
                fig = px.bar(
                    monthly_counts,
                    x='month_str',
                    y='sessions',
                    title="Sessions per Month",
                    labels={'month_str': 'Month', 'sessions': 'Number of Sessions'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Movements per session distribution
        if not movements_df.empty:
            session_movement_counts = movements_df.groupby('session_id').size().reset_index(name='movement_count')
            
            fig = px.histogram(
                session_movement_counts,
                x='movement_count',
                nbins=10,
                title="Movements per Session Distribution",
                labels={'movement_count': 'Number of Movements', 'count': 'Number of Sessions'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent sessions table
    st.subheader("🕒 Recent Sessions")
    if not workout_df.empty and 'Date' in workout_df.columns:
        recent_sessions = workout_df.nlargest(10, 'Date')[['Date', 'Start_Time']].copy()
        
        # Add movement count for each session
        session_movement_counts = movements_df.groupby('session_id').size().to_dict()
        recent_sessions['Movements'] = recent_sessions.index.map(session_movement_counts).fillna(0).astype(int)
        
        # Format dates
        recent_sessions['Date'] = recent_sessions['Date'].dt.strftime('%Y-%m-%d')
        if 'Start_Time' in recent_sessions.columns:
            recent_sessions['Start_Time'] = recent_sessions['Start_Time'].dt.strftime('%H:%M')
        
        st.dataframe(recent_sessions, use_container_width=True, hide_index=True)

def show_movement_analysis(movements_df: pd.DataFrame, workout_type: str):
    """Show detailed analysis of movements"""
    
    if movements_df.empty:
        st.warning("No movement data available for analysis.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Most frequent movements
        movement_counts = movements_df['movement'].value_counts().head(10)
        
        fig = px.bar(
            x=movement_counts.values,
            y=movement_counts.index,
            orientation='h',
            title="Most Frequent Movements",
            labels={'x': 'Number of Times Performed', 'y': 'Movement'}
        )
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Average weight by movement (top 10)
        weight_by_movement = movements_df.groupby('movement')['weight'].agg(['mean', 'count']).reset_index()
        weight_by_movement = weight_by_movement[weight_by_movement['count'] >= 2]  # At least 2 sessions
        weight_by_movement = weight_by_movement.nlargest(10, 'mean')
        
        if not weight_by_movement.empty:
            fig = px.bar(
                weight_by_movement,
                x='mean',
                y='movement',
                orientation='h',
                title="Average Weight by Movement (Top 10)",
                labels={'mean': 'Average Weight (lbs)', 'movement': 'Movement'}
            )
            fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No weight data available for movements.")
    
    # Movement details table
    st.subheader("📋 Movement Summary Statistics")
    
    movement_stats = movements_df.groupby('movement').agg({
        'weight': ['count', 'mean', 'max'],
        'reps': ['mean', 'max'],
        'sets': ['mean', 'sum']
    }).round(2)
    
    # Flatten column names
    movement_stats.columns = ['Sessions', 'Avg Weight', 'Max Weight', 'Avg Reps', 'Max Reps', 'Avg Sets', 'Total Sets']
    movement_stats = movement_stats.sort_values('Sessions', ascending=False)
    
    st.dataframe(movement_stats, use_container_width=True)

def show_progress_tracking(movements_df: pd.DataFrame, workout_type: str):
    """Show progress tracking for movements"""
    
    if movements_df.empty:
        st.warning("No movement data available for progress tracking.")
        return
    
    # Movement selector
    unique_movements = sorted(movements_df['movement'].unique())
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_movement = st.selectbox(
            "Select movement to track progress:",
            unique_movements,
            help="Choose a movement to see detailed progress over time"
        )
    
    with col2:
        metric_type = st.selectbox(
            "Metric to track:",
            ["weight", "reps", "volume"],
            help="Choose what metric to visualize"
        )
    
    if selected_movement:
        # Get progress data for selected movement
        progress_data = get_movement_progress_data(movements_df, selected_movement)
        
        if progress_data.empty:
            st.warning(f"No data found for {selected_movement}")
            return
        
        # Create progress visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Progress over time chart
            if metric_type == "volume":
                y_values = progress_data['volume']
                y_label = "Volume (Weight × Reps × Sets)"
            else:
                y_values = progress_data[metric_type]
                y_label = metric_type.title()
            
            fig = px.scatter(
                progress_data,
                x='date',
                y=y_values,
                size='sets' if 'sets' in progress_data.columns else None,
                title=f"{selected_movement} - {y_label} Progress",
                labels={'date': 'Date', y_values.name: y_label}
            )
            
            # Add trend line if we have enough data points
            if len(progress_data) >= 3:
                z = np.polyfit(range(len(progress_data)), y_values.fillna(0), 1)
                p = np.poly1d(z)
                fig.add_traces(
                    go.Scatter(
                        x=progress_data['date'],
                        y=p(range(len(progress_data))),
                        mode='lines',
                        name='Trend',
                        line=dict(color='red', dash='dash')
                    )
                )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Progress statistics
            st.markdown("#### 📊 Progress Stats")
            
            # Calculate progress metrics
            if len(progress_data) >= 2:
                first_value = y_values.iloc[0]
                last_value = y_values.iloc[-1]
                
                if pd.notna(first_value) and pd.notna(last_value) and first_value != 0:
                    improvement = ((last_value - first_value) / first_value) * 100
                    st.metric(
                        f"Overall {y_label} Change",
                        f"{improvement:+.1f}%",
                        delta=f"{last_value - first_value:+.1f}"
                    )
                
                # Personal best
                max_value = y_values.max()
                max_date = progress_data.loc[y_values.idxmax(), 'date']
                
                st.metric(
                    f"Personal Best {y_label}",
                    f"{max_value:.1f}",
                    help=f"Achieved on {max_date.strftime('%Y-%m-%d')}"
                )
                
                # Recent average (last 3 sessions)
                recent_avg = y_values.tail(3).mean()
                st.metric(
                    f"Recent Avg {y_label}",
                    f"{recent_avg:.1f}",
                    help="Average of last 3 sessions"
                )
                
                # Session count
                st.metric(
                    "Total Sessions",
                    len(progress_data)
                )
        
        # Detailed session data
        st.subheader(f"📋 {selected_movement} - Session Details")
        
        display_data = progress_data[['date', 'weight', 'reps', 'sets', 'volume']].copy()
        display_data['date'] = display_data['date'].dt.strftime('%Y-%m-%d')
        display_data = display_data.sort_values('date', ascending=False)
        
        st.dataframe(display_data, use_container_width=True, hide_index=True)

def show_personal_records(movements_df: pd.DataFrame, workout_type: str):
    """Show personal records and achievements"""
    
    if movements_df.empty:
        st.warning("No movement data available for personal records.")
        return
    
    st.subheader("🏆 Personal Records")
    
    # Calculate PRs for each movement
    pr_data = []
    
    for movement in movements_df['movement'].unique():
        movement_data = movements_df[movements_df['movement'] == movement]
        
        # Weight PR
        max_weight_idx = movement_data['weight'].idxmax()
        if pd.notna(max_weight_idx):
            max_weight_row = movement_data.loc[max_weight_idx]
            pr_data.append({
                'Movement': movement,
                'Record Type': 'Max Weight',
                'Value': f"{max_weight_row['weight']:.1f} lbs",
                'Reps': max_weight_row.get('reps', 'N/A'),
                'Sets': max_weight_row.get('sets', 'N/A'),
                'Date': max_weight_row['date'].strftime('%Y-%m-%d') if pd.notna(max_weight_row['date']) else 'Unknown'
            })
        
        # Volume PR
        movement_data_volume = movement_data.copy()
        movement_data_volume['volume'] = (
            movement_data_volume['weight'].fillna(0) * 
            movement_data_volume['reps'].fillna(0) * 
            movement_data_volume['sets'].fillna(0)
        )
        
        max_volume_idx = movement_data_volume['volume'].idxmax()
        if pd.notna(max_volume_idx) and movement_data_volume.loc[max_volume_idx, 'volume'] > 0:
            max_volume_row = movement_data_volume.loc[max_volume_idx]
            pr_data.append({
                'Movement': movement,
                'Record Type': 'Max Volume',
                'Value': f"{max_volume_row['volume']:.0f}",
                'Reps': max_volume_row.get('reps', 'N/A'),
                'Sets': max_volume_row.get('sets', 'N/A'),
                'Date': max_volume_row['date'].strftime('%Y-%m-%d') if pd.notna(max_volume_row['date']) else 'Unknown'
            })
        
        # Rep PR (for given weight)
        max_reps_idx = movement_data['reps'].idxmax()
        if pd.notna(max_reps_idx):
            max_reps_row = movement_data.loc[max_reps_idx]
            pr_data.append({
                'Movement': movement,
                'Record Type': 'Max Reps',
                'Value': f"{max_reps_row['reps']:.0f} reps",
                'Reps': max_reps_row.get('reps', 'N/A'),
                'Sets': max_reps_row.get('sets', 'N/A'),
                'Date': max_reps_row['date'].strftime('%Y-%m-%d') if pd.notna(max_reps_row['date']) else 'Unknown'
            })
    
    # Display PRs
    if pr_data:
        pr_df = pd.DataFrame(pr_data)
        
        # Create tabs for different record types
        weight_prs = pr_df[pr_df['Record Type'] == 'Max Weight'].sort_values('Value', ascending=False)
        volume_prs = pr_df[pr_df['Record Type'] == 'Max Volume'].sort_values('Value', ascending=False)
        rep_prs = pr_df[pr_df['Record Type'] == 'Max Reps'].sort_values('Value', ascending=False)
        
        tab1, tab2, tab3 = st.tabs(["💪 Weight PRs", "📦 Volume PRs", "🔥 Rep PRs"])
        
        with tab1:
            if not weight_prs.empty:
                st.dataframe(weight_prs, use_container_width=True, hide_index=True)
            else:
                st.info("No weight records found.")
        
        with tab2:
            if not volume_prs.empty:
                st.dataframe(volume_prs, use_container_width=True, hide_index=True)
            else:
                st.info("No volume records found.")
        
        with tab3:
            if not rep_prs.empty:
                st.dataframe(rep_prs, use_container_width=True, hide_index=True)
            else:
                st.info("No rep records found.")
    
    else:
        st.info("No personal records data available.")
    
    # Recent achievements (last 30 days)
    st.subheader("🆕 Recent Achievements (Last 30 Days)")
    
    recent_cutoff = pd.Timestamp.now() - timedelta(days=30)
    recent_data = movements_df[movements_df['date'] >= recent_cutoff]
    
    if not recent_data.empty:
        # Find recent PRs by comparing to historical data
        achievements = []
        
        for movement in recent_data['movement'].unique():
            movement_recent = recent_data[recent_data['movement'] == movement]
            movement_historical = movements_df[
                (movements_df['movement'] == movement) & 
                (movements_df['date'] < recent_cutoff)
            ]
            
            if movement_historical.empty:
                continue  # No historical data to compare
            
            # Check for weight PRs
            recent_max_weight = movement_recent['weight'].max()
            historical_max_weight = movement_historical['weight'].max()
            
            if (pd.notna(recent_max_weight) and pd.notna(historical_max_weight) and 
                recent_max_weight > historical_max_weight):
                achievements.append({
                    'Achievement': f"New Weight PR: {movement}",
                    'Value': f"{recent_max_weight} lbs",
                    'Previous': f"{historical_max_weight} lbs",
                    'Improvement': f"+{recent_max_weight - historical_max_weight:.1f} lbs"
                })
        
        if achievements:
            st.dataframe(pd.DataFrame(achievements), use_container_width=True, hide_index=True)
        else:
            st.info("No new achievements in the last 30 days. Keep pushing! 💪")
    else:
        st.info("No recent workout data found.")

def show_schedule_patterns(workout_df: pd.DataFrame, workout_type: str):
    """Show workout schedule patterns and consistency"""
    
    if workout_df.empty or 'Date' not in workout_df.columns:
        st.warning("No date data available for schedule analysis.")
        return
    
    # Clean data
    workout_df_clean = workout_df[workout_df['Date'].notna()].copy()
    
    if workout_df_clean.empty:
        st.warning("No valid date data found.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Day of week analysis
        workout_df_clean['day_of_week'] = workout_df_clean['Date'].dt.day_name()
        day_counts = workout_df_clean['day_of_week'].value_counts()
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = day_counts.reindex([day for day in day_order if day in day_counts.index])
        
        fig = px.bar(
            x=day_counts.index,
            y=day_counts.values,
            title="Workouts by Day of Week",
            labels={'x': 'Day of Week', 'y': 'Number of Workouts'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Time of day analysis (if start_time available)
        if 'Start_Time' in workout_df_clean.columns:
            workout_df_clean['hour'] = workout_df_clean['Start_Time'].dt.hour
            time_counts = workout_df_clean['hour'].value_counts().sort_index()
            
            fig = px.bar(
                x=time_counts.index,
                y=time_counts.values,
                title="Workouts by Hour of Day",
                labels={'x': 'Hour of Day', 'y': 'Number of Workouts'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No start time data available for time analysis.")
    
    # Consistency metrics
    st.subheader("📊 Consistency Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics
    date_range = (workout_df_clean['Date'].max() - workout_df_clean['Date'].min()).days
    total_sessions = len(workout_df_clean)
    
    if date_range > 0:
        avg_sessions_per_week = (total_sessions / date_range) * 7
        
        # Calculate gaps between sessions
        workout_dates = sorted(workout_df_clean['Date'].unique())
        gaps = [(workout_dates[i] - workout_dates[i-1]).days for i in range(1, len(workout_dates))]
        avg_gap = np.mean(gaps) if gaps else 0
        max_gap = max(gaps) if gaps else 0
        
        with col1:
            st.metric("Avg Sessions/Week", f"{avg_sessions_per_week:.1f}")
        
        with col2:
            st.metric("Avg Days Between", f"{avg_gap:.1f}")
        
        with col3:
            st.metric("Longest Break", f"{max_gap} days")
        
        with col4:
            consistency_score = min(100, (avg_sessions_per_week / 3) * 100)  # Assuming 3 sessions/week is ideal
            st.metric("Consistency Score", f"{consistency_score:.0f}%")
    
    # Workout frequency heatmap
    st.subheader("📅 Workout Frequency Calendar")
    
    # Create a date range for the heatmap
    start_date = workout_df_clean['Date'].min()
    end_date = workout_df_clean['Date'].max()
    
    # Count workouts per day
    daily_counts = workout_df_clean.groupby(workout_df_clean['Date'].dt.date).size()
    
    # Create calendar data
    date_range_full = pd.date_range(start_date, end_date, freq='D')
    calendar_data = []
    
    for date in date_range_full:
        count = daily_counts.get(date.date(), 0)
        calendar_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%A'),
            'week': date.isocalendar()[1],
            'year': date.year,
            'count': count
        })
    
    calendar_df = pd.DataFrame(calendar_data)
    
    if not calendar_df.empty and len(calendar_df) <= 365:  # Only show if reasonable size
        # Create a simple heatmap using plotly
        calendar_df['week_of_year'] = pd.to_datetime(calendar_df['date']).dt.isocalendar().week
        calendar_df['day_of_week'] = pd.to_datetime(calendar_df['date']).dt.dayofweek
        
        # Pivot for heatmap
        heatmap_data = calendar_df.pivot(index='day_of_week', columns='week_of_year', values='count').fillna(0)
        
        fig = px.imshow(
            heatmap_data,
            title="Workout Frequency Heatmap (by week)",
            labels={'x': 'Week of Year', 'y': 'Day of Week', 'color': 'Workouts'},
            aspect='auto'
        )
        
        # Update y-axis labels
        day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        fig.update_yaxis(ticktext=day_labels, tickvals=list(range(7)))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Date range too large for calendar heatmap display.")

def get_workout_page_navigation():
    """
    Handle navigation between workout selection and individual workout pages
    """
    # Initialize session state
    if 'selected_workout' not in st.session_state:
        st.session_state.selected_workout = None
    
    return st.session_state.selected_workout