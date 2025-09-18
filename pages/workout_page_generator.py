"""
Dynamic Workout Page Generator
Automatically creates dedicated pages for each unique workout type found in the data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.data_loader import get_unique_workouts, extract_movements_from_workout

def get_workout_page_navigation():
    """Handle navigation to individual workout pages"""
    return st.session_state.get('selected_workout', None)

def show_workout_selection_page(df: pd.DataFrame):
    """Display a page with all available workout types for selection"""
    st.header("🎯 Workout Types")
    st.markdown("Select a workout type to dive into detailed analysis:")
    
    unique_workouts = get_unique_workouts(df)
    
    if not unique_workouts:
        st.warning("No workout types found in your data.")
        return
    
    # Create a grid layout for workout cards
    cols_per_row = 3
    rows = (len(unique_workouts) + cols_per_row - 1) // cols_per_row
    
    for row in range(rows):
        cols = st.columns(cols_per_row)
        
        for col_idx in range(cols_per_row):
            workout_idx = row * cols_per_row + col_idx
            
            if workout_idx < len(unique_workouts):
                workout = unique_workouts[workout_idx]
                
                with cols[col_idx]:
                    # Calculate stats for this workout
                    workout_df = df[df['Workout'] == workout]
                    session_count = len(workout_df)
                    
                    # Get date range
                    if 'Date' in workout_df.columns and workout_df['Date'].notna().any():
                        latest_date = workout_df['Date'].max()
                        earliest_date = workout_df['Date'].min()
                        days_span = (latest_date - earliest_date).days
                        last_session = (datetime.now() - latest_date.to_pydatetime()).days
                    else:
                        days_span = 0
                        last_session = 0
                    
                    # Create workout card
                    with st.container():
                        st.markdown(f"""
                        <div style="
                            border: 2px solid #f0f2f6;
                            border-radius: 10px;
                            padding: 15px;
                            margin: 10px 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                        ">
                            <h4 style="margin: 0; color: white;">{workout}</h4>
                            <p style="margin: 5px 0; opacity: 0.9;">📅 {session_count} sessions</p>
                            <p style="margin: 5px 0; opacity: 0.9;">⏱️ {days_span} days tracked</p>
                            <p style="margin: 5px 0; opacity: 0.9;">🔄 {last_session} days ago</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Analyze {workout}", key=f"select_{workout}", use_container_width=True):
                            st.session_state.selected_workout = workout
                            st.rerun()

def show_individual_workout_page(df: pd.DataFrame, workout_name: str):
    """Display detailed analysis page for a specific workout type"""
    
    # Filter data for this specific workout
    workout_df = df[df['Workout'] == workout_name].copy()
    
    if workout_df.empty:
        st.error(f"No data found for workout: {workout_name}")
        return
    
    # Page header
    st.header(f"🎯 {workout_name} Analysis")
    
    # Create tabs for different analysis types
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "📈 Progress Trends", 
        "🏋️ Movement Analysis", 
        "📅 Session History",
        "🎯 Goal Tracking"
    ])
    
    with tab1:
        show_workout_overview(workout_df, workout_name)
    
    with tab2:
        show_progress_trends(workout_df, workout_name)
    
    with tab3:
        show_movement_analysis(workout_df, workout_name)
    
    with tab4:
        show_session_history(workout_df, workout_name)
    
    with tab5:
        show_goal_tracking(workout_df, workout_name)

def show_workout_overview(workout_df: pd.DataFrame, workout_name: str):
    """Display overview metrics and summary for the workout"""
    
    # Basic metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_sessions = len(workout_df)
    
    # Calculate date metrics if available
    if 'Date' in workout_df.columns and workout_df['Date'].notna().any():
        date_range = (workout_df['Date'].max() - workout_df['Date'].min()).days
        latest_session = workout_df['Date'].max()
        days_since_last = (pd.Timestamp.now() - latest_session).days
    else:
        date_range = 0
        days_since_last = 0
    
    with col1:
        st.metric("Total Sessions", total_sessions)
    with col2:
        st.metric("Days Tracked", date_range)
    with col3:
        st.metric("Days Since Last", days_since_last)
    
    # Extract movements for more detailed metrics
    movements_df = extract_movements_from_workout(workout_df)
    
    if not movements_df.empty:
        unique_movements = movements_df['movement'].nunique()
        total_volume = (movements_df['weight'].fillna(0) * 
                       movements_df['reps'].fillna(0) * 
                       movements_df['sets'].fillna(0)).sum()
        
        with col4:
            st.metric("Unique Movements", unique_movements)
        
        # Volume and frequency charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Session frequency over time
            if 'Date' in workout_df.columns:
                session_freq = workout_df.groupby(workout_df['Date'].dt.to_period('M')).size()
                
                fig = px.bar(
                    x=[str(period) for period in session_freq.index],
                    y=session_freq.values,
                    title=f"{workout_name} - Sessions per Month",
                    labels={'x': 'Month', 'y': 'Number of Sessions'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top movements in this workout
            movement_counts = movements_df['movement'].value_counts().head(8)
            
            fig = px.pie(
                values=movement_counts.values,
                names=movement_counts.index,
                title=f"Movement Distribution - {workout_name}"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent sessions preview
    st.subheader("📝 Recent Sessions")
    
    if 'Date' in workout_df.columns:
        recent_sessions = workout_df.nlargest(5, 'Date')
        display_cols = ['Date', 'Workout']
        
        # Add time column if available
        if 'Start_Time' in recent_sessions.columns:
            display_cols.append('Start_Time')
            recent_sessions = recent_sessions.copy()
            recent_sessions['Start_Time'] = recent_sessions['Start_Time'].dt.strftime('%H:%M')
        
        recent_sessions = recent_sessions.copy()
        recent_sessions['Date'] = recent_sessions['Date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(recent_sessions[display_cols], use_container_width=True, hide_index=True)

def show_progress_trends(workout_df: pd.DataFrame, workout_name: str):
    """Display progress trends and improvements over time"""
    
    st.subheader(f"📈 {workout_name} Progress Trends")
    
    movements_df = extract_movements_from_workout(workout_df)
    
    if movements_df.empty:
        st.warning("No movement data available for progress analysis.")
        return
    
    # Filtering options
    col1, col2 = st.columns(2)
    
    with col1:
        available_movements = sorted(movements_df['movement'].unique())
        selected_movements = st.multiselect(
            "Select movements to analyze:",
            available_movements,
            default=available_movements[:3]  # Default to first 3
        )
    
    with col2:
        time_period = st.selectbox(
            "Time period grouping:",
            ["Weekly", "Monthly", "Quarterly"],
            index=1
        )
    
    if not selected_movements:
        st.info("Please select at least one movement to analyze.")
        return
    
    # Filter data
    filtered_df = movements_df[movements_df['movement'].isin(selected_movements)].copy()
    
    # Group by time period
    period_map = {"Weekly": "W", "Monthly": "M", "Quarterly": "Q"}
    period_key = period_map[time_period]
    
    if 'date' in filtered_df.columns:
        filtered_df['period'] = filtered_df['date'].dt.to_period(period_key)
        
        # Calculate progress metrics
        progress_metrics = filtered_df.groupby(['movement', 'period']).agg({
            'weight': ['max', 'mean'],
            'reps': ['max', 'sum'],
            'sets': 'sum'
        }).reset_index()
        
        progress_metrics.columns = ['movement', 'period', 'max_weight', 'avg_weight', 'max_reps', 'total_reps', 'total_sets']
        progress_metrics['volume'] = progress_metrics['avg_weight'] * progress_metrics['total_reps']
        progress_metrics['period_str'] = progress_metrics['period'].astype(str)
        
        # Create progress charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Max weight progression
            fig = px.line(
                progress_metrics,
                x='period_str',
                y='max_weight',
                color='movement',
                title=f"Max Weight Progression ({time_period})",
                labels={'period_str': time_period, 'max_weight': 'Max Weight (lbs)'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Volume progression
            fig = px.line(
                progress_metrics,
                x='period_str',
                y='volume',
                color='movement',
                title=f"Volume Progression ({time_period})",
                labels={'period_str': time_period, 'volume': 'Total Volume'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Personal records table
        st.subheader("🏆 Personal Records")
        
        pr_data = []
        for movement in selected_movements:
            movement_data = filtered_df[filtered_df['movement'] == movement]
            
            if not movement_data.empty:
                max_weight_row = movement_data.loc[movement_data['weight'].idxmax()]
                max_reps_row = movement_data.loc[movement_data['reps'].idxmax()]
                max_volume_idx = (movement_data['weight'] * movement_data['reps'] * movement_data['sets']).idxmax()
                max_volume_row = movement_data.loc[max_volume_idx]
                
                pr_data.append({
                    'Movement': movement,
                    'Max Weight': f"{max_weight_row['weight']:.1f} lbs",
                    'Max Weight Date': max_weight_row['date'].strftime('%Y-%m-%d'),
                    'Max Reps': f"{max_reps_row['reps']:.0f} reps",
                    'Max Reps Date': max_reps_row['date'].strftime('%Y-%m-%d'),
                    'Best Volume': f"{max_volume_row['weight'] * max_volume_row['reps'] * max_volume_row['sets']:.0f}",
                    'Best Volume Date': max_volume_row['date'].strftime('%Y-%m-%d')
                })
        
        if pr_data:
            pr_df = pd.DataFrame(pr_data)
            st.dataframe(pr_df, use_container_width=True, hide_index=True)

def show_movement_analysis(workout_df: pd.DataFrame, workout_name: str):
    """Detailed analysis of individual movements within the workout"""
    
    st.subheader(f"🏋️ Movement Analysis - {workout_name}")
    
    movements_df = extract_movements_from_workout(workout_df)
    
    if movements_df.empty:
        st.warning("No movement data available for analysis.")
        return
    
    # Movement selector
    available_movements = sorted(movements_df['movement'].unique())
    selected_movement = st.selectbox("Select a movement for detailed analysis:", available_movements)
    
    if not selected_movement:
        return
    
    movement_data = movements_df[movements_df['movement'] == selected_movement].copy()
    
    # Movement metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_sessions = len(movement_data)
    max_weight = movement_data['weight'].max()
    total_reps = movement_data['reps'].sum()
    avg_sets = movement_data['sets'].mean()
    
    with col1:
        st.metric("Sessions Performed", total_sessions)
    with col2:
        st.metric("Max Weight", f"{max_weight:.1f} lbs")
    with col3:
        st.metric("Total Reps", f"{total_reps:.0f}")
    with col4:
        st.metric("Avg Sets", f"{avg_sets:.1f}")
    
    # Detailed analysis charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Weight progression over time
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=movement_data['date'],
            y=movement_data['weight'],
            mode='markers+lines',
            name='Weight Used',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f"{selected_movement} - Weight Progression",
            xaxis_title="Date",
            yaxis_title="Weight (lbs)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Reps distribution
        fig = px.histogram(
            movement_data,
            x='reps',
            nbins=20,
            title=f"{selected_movement} - Reps Distribution"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed session data
    st.subheader(f"📊 {selected_movement} - Session Details")
    
    session_details = movement_data.copy()
    session_details['volume'] = session_details['weight'] * session_details['reps'] * session_details['sets']
    session_details = session_details.sort_values('date', ascending=False)
    
    display_cols = ['date', 'weight', 'reps', 'sets', 'volume']
    display_df = session_details[display_cols].copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    display_df.columns = ['Date', 'Weight', 'Reps', 'Sets', 'Volume']
    
    st.dataframe(display_df.head(20), use_container_width=True, hide_index=True)

def show_session_history(workout_df: pd.DataFrame, workout_name: str):
    """Display chronological history of workout sessions"""
    
    st.subheader(f"📅 {workout_name} - Session History")
    
    if workout_df.empty:
        st.warning("No session data available.")
        return
    
    # Sort by date (most recent first)
    if 'Date' in workout_df.columns:
        sorted_df = workout_df.sort_values('Date', ascending=False)
    else:
        sorted_df = workout_df
    
    # Filtering options
    col1, col2 = st.columns(2)
    
    with col1:
        # Date range filter
        if 'Date' in sorted_df.columns and sorted_df['Date'].notna().any():
            min_date = sorted_df['Date'].min().date()
            max_date = sorted_df['Date'].max().date()
            
            date_range = st.date_input(
                "Select date range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                mask = (sorted_df['Date'].dt.date >= start_date) & (sorted_df['Date'].dt.date <= end_date)
                sorted_df = sorted_df[mask]
    
    with col2:
        # Results per page
        results_per_page = st.selectbox("Sessions per page:", [10, 20, 50, 100], index=1)
    
    # Pagination
    total_sessions = len(sorted_df)
    total_pages = (total_sessions + results_per_page - 1) // results_per_page
    
    if total_pages > 1:
        page = st.selectbox("Page:", range(1, total_pages + 1))
        start_idx = (page - 1) * results_per_page
        end_idx = start_idx + results_per_page
        display_df = sorted_df.iloc[start_idx:end_idx]
    else:
        display_df = sorted_df
    
    # Display sessions
    for idx, session in display_df.iterrows():
        with st.expander(f"Session {session.get('Date', 'Unknown Date')}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show session details
                session_info = []
                for col in sorted_df.columns:
                    if col not in ['Date', 'Workout'] and pd.notna(session[col]):
                        session_info.append(f"**{col}:** {session[col]}")
                
                if session_info:
                    st.write("\n\n".join(session_info))
                else:
                    st.write("No additional session details available.")
            
            with col2:
                # Quick stats if we can extract movements
                try:
                    session_df = pd.DataFrame([session])
                    movements = extract_movements_from_workout(session_df)
                    
                    if not movements.empty:
                        total_movements = len(movements)
                        total_volume = (movements['weight'].fillna(0) * 
                                       movements['reps'].fillna(0) * 
                                       movements['sets'].fillna(0)).sum()
                        
                        st.metric("Movements", total_movements)
                        st.metric("Total Volume", f"{total_volume:.0f}")
                except:
                    pass  # Skip if movement extraction fails

def show_goal_tracking(workout_df: pd.DataFrame, workout_name: str):
    """Goal setting and tracking interface for the workout"""
    
    st.subheader(f"🎯 Goal Tracking - {workout_name}")
    
    # This would be enhanced with persistent storage in a real app
    st.info("🚧 Goal tracking feature - Coming soon! This will allow you to set and track specific goals for your workouts.")
    
    movements_df = extract_movements_from_workout(workout_df)
    
    if movements_df.empty:
        st.warning("No movement data available for goal tracking.")
        return
    
    # Placeholder for goal setting interface
    st.subheader("Set New Goals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        available_movements = sorted(movements_df['movement'].unique())
        goal_movement = st.selectbox("Select movement for goal:", available_movements)
        
        goal_type = st.selectbox("Goal type:", ["Max Weight", "Total Volume", "Frequency"])
    
    with col2:
        goal_value = st.number_input("Target value:", min_value=0.0, step=1.0)
        goal_date = st.date_input("Target date:")
    
    if st.button("Set Goal"):
        st.success(f"Goal set: {goal_type} of {goal_value} for {goal_movement} by {goal_date}")
        st.info("Note: In the full version, goals would be saved and tracked over time.")
    
    # Show current performance for context
    if goal_movement:
        movement_data = movements_df[movements_df['movement'] == goal_movement]
        
        if not movement_data.empty:
            current_max = movement_data['weight'].max()
            current_volume = (movement_data['weight'] * movement_data['reps'] * movement_data['sets']).sum()
            sessions_count = len(movement_data)
            
            st.subheader(f"Current Performance - {goal_movement}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Max Weight", f"{current_max:.1f} lbs")
            with col2:
                st.metric("Total Volume (All Time)", f"{current_volume:.0f}")
            with col3:
                st.metric("Sessions Performed", sessions_count)