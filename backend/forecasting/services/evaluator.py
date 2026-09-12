from math import sqrt
from sklearn.metrics import mean_absolute_error, mean_squared_error

def evaluate(actual, predicted):
    return {"mae": round(float(mean_absolute_error(actual, predicted)), 4), "rmse": round(float(sqrt(mean_squared_error(actual, predicted))), 4)}

def select_best(metrics):
    return min(metrics, key=lambda name: (metrics[name]["mae"], metrics[name]["rmse"]))
