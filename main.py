# -*- coding: utf-8 -*-
"""stock_price_prediction.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/github/kangwonlee/stock-price-prediction-transformer/blob/main/stock_price_prediction.ipynb
"""

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LayerNormalization, MultiHeadAttention, Dropout, GlobalAveragePooling1D

"""## Load and prepare the dataset


"""

import yfinance as yf


def main():
    ticker = 'TSLA'
    time_step = 100
    training_ratio = 0.67
    predict_price(ticker, time_step, training_ratio)


def predict_price(ticker, time_step, training_ratio):
    scaler, data_scaled = get_scaled_data(ticker)

    """
    ## Parameters
    """

    training_size = int(len(data_scaled) * training_ratio)
    test_size = len(data_scaled) - training_size

    # separate data into training and test
    train_data = data_scaled[0:training_size,:]
    test_data  = data_scaled[training_size:len(data_scaled),:]

    X_train, y_train = create_dataset(train_data, time_step)
    X_test, y_test = create_dataset(test_data, time_step)

    """
    ## Reshape input for the model
    """

    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
    X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

    model = define_model(X_train)

    """## Model Summary"""

    model.summary()

    """## Train the model"""

    model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=50, batch_size=64, verbose=1
    )

    """
    ## Make predictions
    """

    # Make predictions
    train_predict = model.predict(X_train)
    test_predict = model.predict(X_test)

    # Inverse transform predictions
    train_predict = scaler.inverse_transform(train_predict)
    test_predict = scaler.inverse_transform(test_predict)

    # Evaluate the model (Optional: Calculate RMSE or other metrics)
    train_rmse = math.sqrt(mean_squared_error(y_train, scaler.inverse_transform(train_predict.reshape(-1, 1))))
    test_rmse = math.sqrt(mean_squared_error(y_test, scaler.inverse_transform(test_predict.reshape(-1, 1))))

    print(f"Train RMSE: {train_rmse}")
    print(f"Test RMSE: {test_rmse}")

    visualize_predictions(ticker, scaler, data_scaled, time_step, train_predict, test_predict)


def get_scaled_data(ticker):
    df = yf.download(ticker, start="2010-06-29", end="2022-03-25", period='1d')

    data = df[['Close']].values

    scaler = MinMaxScaler(feature_range=(0, 1))
    data_scaled = scaler.fit_transform(data)
    return scaler,data_scaled


def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []

    for i in range(len(dataset) - time_step - 1):
        a = dataset[i:(i + time_step), 0]
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])

    return np.array(dataX), np.array(dataY)


def transformer_encoder(inputs, head_size, num_heads, ff_dim, dropout=0):
    """
    ## Transformer Block
    """

    x = LayerNormalization(epsilon=1e-6)(inputs)
    x = MultiHeadAttention(key_dim=head_size, num_heads=num_heads, dropout=dropout)(x, x)
    x = Dropout(dropout)(x)
    res = x + inputs

    x = LayerNormalization(epsilon=1e-6)(res)
    x = Dense(ff_dim, activation="relu")(x)
    x = Dropout(dropout)(x)
    x = Dense(inputs.shape[-1])(x)

    return x + res


def define_model(X_train):
    """
    ## Model Definition
    """

    inputs = Input(shape=(X_train.shape[1], X_train.shape[2]))
    x = transformer_encoder(inputs, head_size=256, num_heads=4, ff_dim=4, dropout=0.1)
    x = GlobalAveragePooling1D(data_format='channels_first')(x)
    x = Dropout(0.1)(x)
    x = Dense(20, activation="relu")(x)
    outputs = Dense(1, activation="linear")(x)

    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer="adam", loss="mean_squared_error")

    return model


def visualize_predictions(ticker, scaler, data_scaled, time_step, train_predict, test_predict):
    """
    ## Plotting the results
    """

    # Adjust the time_step offset for plotting
    trainPredictPlot = np.empty_like(data_scaled)
    trainPredictPlot[:, :] = np.nan
    trainPredictPlot[time_step:len(train_predict)+time_step, :] = train_predict

    # Shift test predictions for plotting
    testPredictPlot = np.empty_like(data_scaled)
    testPredictPlot[:, :] = np.nan
    testPredictPlot[len(train_predict)+(time_step*2)+1:len(data_scaled)-1, :] = test_predict

    # Plot baseline and predictions
    plt.figure(figsize=(12, 6))
    plt.semilogy(scaler.inverse_transform(data_scaled), label='Actual Stock Price')
    plt.semilogy(trainPredictPlot, label='Train Predict')
    plt.semilogy(testPredictPlot, label='Test Predict')
    plt.title(f'Stock Price Prediction using Transformer {ticker}')
    plt.xlabel('Time')
    plt.ylabel('Stock Price')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'{ticker}_result.png', dpi=300)


if '__main__' == __name__:
    main()
