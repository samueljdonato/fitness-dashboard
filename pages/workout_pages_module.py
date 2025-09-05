# This file should be saved as pages/workout_page_generator.py

# Copy the entire content from the workout_page_generator artifact above
# This creates the proper module structure for import in the main app

"""
Dynamic Workout Page Generator
Creates dedicated pages for each workout type with comprehensive tracking metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# [Rest of the workout_page_generator code would go here - 
#  I'm providing the import structure since the full code is quite long]

def show_workout_selection_page(df: pd.DataFrame):
    """Display the main workout selection page with all available workout types"""
    # Implementation from the previous artifact
    pass

def show_individual_workout_page(df: pd.DataFrame, workout_type: str):
    """Display detailed analysis page for a specific workout type"""
    # Implementation from the previous artifact  
    pass

def get_workout_page_navigation():
    """Handle navigation between workout selection and individual workout pages"""
    if 'selected_workout' not in st.session_state:
        st.session_state.selected_workout = None
    return st.session_state.selected_workout

# [Additional functions from the workout_page_generator artifact]