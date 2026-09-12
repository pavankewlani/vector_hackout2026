import pandas as pd

TARGETS = ["temperature", "wind_speed", "solar_radiation"]

def readings_frame(readings):
    frame = pd.DataFrame.from_records(readings.values("timestamp", "temperature", "humidity", "cloud_cover", "wind_speed", "solar_radiation"))
    if frame.empty:
        return frame
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame.sort_values("timestamp").drop_duplicates("timestamp").set_index("timestamp").astype(float)

def feature_frame(frame):
    if frame.empty:
        return frame
    result = frame.copy()
    result["hour"] = result.index.hour
    result["day_of_week"] = result.index.dayofweek
    result["month"] = result.index.month
    result["day_of_year"] = result.index.dayofyear
    for column in ["temperature", "humidity", "cloud_cover", "wind_speed", "solar_radiation"]:
        for lag in [1, 3, 6, 24]:
            result[f"{column}_lag_{lag}"] = result[column].shift(lag)
        result[f"{column}_rolling_mean_6"] = result[column].rolling(6).mean()
        result[f"{column}_rolling_mean_24"] = result[column].rolling(24).mean()
    return result.dropna()
