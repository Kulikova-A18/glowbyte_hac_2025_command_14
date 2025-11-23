# constants.py

"""
Constants for the coal self-ignition prediction app.
"""

import os

# Data directory
DATA_DIR = "data"
DATA_WEATHER_DIR = "data/weather_data"

# File paths
FIRE_FILE = os.path.join(DATA_DIR, "fires", "fires.csv")
SUPPLIES_FILE = os.path.join(DATA_DIR, "supplies", "supplies.csv")
TEMP_FILE = os.path.join(DATA_DIR, "temperature", "temperature.csv")
WEATHER_DIR = os.path.join(DATA_DIR, "weather_data")

# Schedule file
SCHEDULE_FILE = "schedule.json"
