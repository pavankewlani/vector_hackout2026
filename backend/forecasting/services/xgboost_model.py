from xgboost import XGBRegressor
from .evaluator import evaluate
from .preprocessing import feature_frame, readings_frame

def train_xgboost(readings, target, test_fraction=0.2):
    frame = feature_frame(readings_frame(readings))
    if len(frame) < 72:
        raise ValueError("Insufficient historical data for ML training.")
    features = [column for column in frame.columns if column != target]
    split = int(len(frame) * (1 - test_fraction))
    model = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, objective="reg:squarederror", n_jobs=2)
    model.fit(frame[features].iloc[:split], frame[target].iloc[:split])
    predicted = model.predict(frame[features].iloc[split:])
    return model, features, evaluate(frame[target].iloc[split:], predicted)
