# Import the dependencies.
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import numpy as np
import datetime as dt


#################################################
# Database Setup
#################################################

# Step 1: Connect to the database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
# Set up the Flask application
app = Flask(__name__)

# Define the homepage route that lists all available routes
@app.route("/")
def welcome():
    return (
        f"Welcome to the Climate Analysis API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/temp/start<br/>"
        f"/api/v1.0/temp/start/end<br/>"
    )


#################################################
# Flask Routes
#################################################
# Define additional routes for the analyses

# Route for precipitation data
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Query for the last 12 months of precipitation data
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    precipitation_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago).all()

    # Create a dictionary with the date as the key and the precipitation as the value
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

# Route for station data
@app.route("/api/v1.0/stations")
def stations():
    # Query for the list of stations
    results = session.query(Station.station).all()
    
    # Convert the query results to a list
    stations_list = [station[0] for station in results]
    
    return jsonify(stations_list)

# Route for temperature observations of the most active station
@app.route("/api/v1.0/tobs")
def tobs():
    # Identify the most active station
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]
    
    # Query for the last 12 months of temperature data for the most active station
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    temperature_data = session.query(Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= one_year_ago).all()

    # Convert the query results to a list
    temps_list = [temp[0] for temp in temperature_data]
    
    return jsonify(temps_list)

# Route for temperature statistics based on start date or start-end range
@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def temp(start, end=None):
    # Query to calculate the minimum, maximum, and average temperature
    if not end:
        temp_stats = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).filter(Measurement.date >= start).all()
    else:
        temp_stats = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    
    # Unpack the tuple result
    min_temp, max_temp, avg_temp = temp_stats[0]
    
    return jsonify({
        "Start Date": start,
        "End Date": end if end else "Latest",
        "Min Temperature": min_temp,
        "Max Temperature": max_temp,
        "Avg Temperature": avg_temp
    })

if __name__ == "__main__":
    app.run(debug=True)