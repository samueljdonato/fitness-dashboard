"""
Visualization Utilities
Reusable chart components for the fitness dashboard
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st

# Color schemes for consistency
FITNESS_COLORS = {
    'primary': '#FF6B6B',
    'secondary': '#4ECDC4', 
    'accent': '#45B7D1',
    'success': '#96CEB4',
    'warning': '#FFEAA7',
    'info': '#DDA0DD'
}

def create_metric_card(title: str, value: str, delta: str = None, help_text: str = None):
    """
    Create a styled metric display
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=help_text
    )

def create_workout_frequency_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create a horizontal bar chart showing workout frequency
    """
    if 'Workout' not in df.columns:
        st.warning("No 'Workout' column found for frequency chart")
        return go.Figure()
    
    workout_counts = df['Workout'].value_counts().head(10)
    
    fig = px.bar(
        x=workout_counts.values,
        y=workout_counts.index,
        orientation='h',
        title="Most Frequent Workouts (Top 10)",
        labels={'x': 'Number of Sessions', 'y': 'Workout Type'},
        color=workout_counts.values,
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_activity_timeline(df: pd.DataFrame) -> go.Figure:
    """
    Create a timeline showing workout activity over time
    """
    if 'Date' not in df.columns:
        st.warning("No 'Date' column found for timeline")
        return go.Figure()
    
    # Remove rows with invalid dates
    df_clean = df[df['Date'].notna()].copy()
    
    if df_clean.empty:
        st.warning("No valid dates found for timeline")
        return go.Figure()
    
    # Group by date to count workouts per day
    daily_workouts = df_clean.groupby('Date').size().reset_index(name='Workout_Count')
    
    fig = px.line(
        daily_workouts,
        x='Date',
        y='Workout_Count',
        title='Workout Activity Over Time',
        labels={'Workout_Count': 'Number of Workouts', 'Date': 'Date'}
    )
    
    fig.update_traces(line_color=FITNESS_COLORS['primary'])
    fig.update_layout(height=400)
    
    return fig

def create_movement_distribution(df: pd.DataFrame, workout_type: str = None) -> go.Figure:
    """
    Create a pie chart showing distribution of movements
    """
    if 'Movement' not in df.columns:
        st.warning("No 'Movement' column found for distribution chart")
        return go.Figure()
    
    # Filter by workout type if specified
    if workout_type and 'Workout' in df.columns:
        df = df[df['Workout'] == workout_type]
    
    movement_counts = df['Movement'].value_counts().head(8)  # Top 8 movements
    
    fig = px.pie(
        values=movement_counts.values,
        names=movement_counts.index,
        title=f"Movement Distribution{f' - {workout_type}' if workout_type else ''}"
    )
    
    fig.update_layout(height=400)
    
    return fig

def create_progress_chart(df: pd.DataFrame, movement: str, metric: str = 'Reps') -> go.Figure:
    """
    Create a scatter plot showing progress over time for a specific movement
    """
    if 'Movement' not in df.columns or 'Date' not in df.columns:
        st.warning("Required columns not found for progress chart")
        return go.Figure()
    
    # Filter for specific movement
    movement_data = df[
        (df['Movement'] == movement) & 
        (df['Date'].notna()) & 
        (df[metric].notna())
    ].copy()
    
    if movement_data.empty:
        st.warning(f"No data found for {movement}")
        return go.Figure()
    
    fig = px.scatter(
        movement_data,
        x='Date',
        y=metric,
        size='Sets' if 'Sets' in movement_data.columns else None,
        title=f"{movement} - {metric} Progress Over Time",
        labels={metric: metric, 'Date': 'Date'}
    )
    
    # Add trend line
    fig.add_traces(
        px.scatter(movement_data, x='Date', y=metric, trendline='ols').data[1:]
    )
    
    fig.update_layout(height=400)
    
    return fig

def create_summary_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary statistics table
    """
    if df.empty:
        return pd.DataFrame({'Metric': ['No data'], 'Value': ['N/A']})
    
    stats = []
    
    # Basic counts
    stats.append({'Metric': 'Total Records', 'Value': len(df)})
    
    if 'Workout' in df.columns:
        stats.append({'Metric': 'Unique Workouts', 'Value': df['Workout'].nunique()})
    
    if 'Movement' in df.columns:
        stats.append({'Metric': 'Unique Movements', 'Value': df['Movement'].nunique()})
    
    if 'Date' in df.columns:
        date_range = df['Date'].max() - df['Date'].min()
        stats.append({'Metric': 'Date Range (Days)', 'Value': date_range.days if pd.notna(date_range) else 'N/A'})
    
    # Numeric columns stats
    numeric_columns = df.select_dtypes(include=['number']).columns
    for col in numeric_columns:
        if col in ['Reps', 'Sets', 'Weight']:  # Focus on key metrics
            max_val = df[col].max()
            if pd.notna(max_val):
                stats.append({'Metric': f'Max {col}', 'Value': max_val})
    
    return pd.DataFrame(stats)

# Styling functions
def apply_fitness_theme():
    """
    Apply custom CSS styling for the fitness theme
    """
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(90deg, #FF6B6B 0%, #4ECDC4 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    
    .main-header {
        color: #2c3e50;
        text-align: center;
        padding: 2rem 0;
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .stPlotlyChart {
            height: 300px !important;
        }
        
        .stMetric > div {
            font-size: 0.8rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)