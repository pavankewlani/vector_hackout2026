def train_lstm(readings, target, sequence_length=24):
    try:
        import numpy as np
        from sklearn.preprocessing import MinMaxScaler
        from tensorflow.keras import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
    except ImportError as error:
        raise RuntimeError("TensorFlow is required to train LSTM models.") from error
    values = readings.values_list(target, flat=True)
    if len(values) < sequence_length + 48:
        raise ValueError("Insufficient historical data for ML training.")
    scaler = MinMaxScaler()
    normalized = scaler.fit_transform(np.array(values, dtype=float).reshape(-1, 1))
    sequences = np.array([normalized[index:index + sequence_length] for index in range(len(normalized) - sequence_length)])
    targets = normalized[sequence_length:]
    split = int(len(sequences) * 0.8)
    model = Sequential([LSTM(32, input_shape=(sequence_length, 1)), Dropout(0.1), Dense(1)])
    model.compile(optimizer="adam", loss="mse")
    model.fit(sequences[:split], targets[:split], epochs=5, batch_size=32, verbose=0, shuffle=False)
    predicted = scaler.inverse_transform(model.predict(sequences[split:], verbose=0))
    actual = scaler.inverse_transform(targets[split:])
    from .evaluator import evaluate
    return model, scaler, evaluate(actual, predicted)
