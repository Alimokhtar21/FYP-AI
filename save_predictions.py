import argparse
from datetime import date
import json
import os
import glob

import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
import numpy as np
import pandas as pd

from models.linear_regression import LinearRegression
from models.svr import SupportVectorRegression
from models.linear_index_regression import LinearIndexRegression
from models.svr_index_regression import SupportVectorIndexRegression
from models.dnn_regression import DenseNeuralNetwork

from build_dataset import build_predict_dataset, get_stock_data

from train_models import SAVED_MODELS_DIR_MAP

def get_saved_predictions(stock_code, location="local"):
    """Gets saved predictions directly

    Args:
        stock_code: Stock code specifying a stock.
        location: local or cloud, for now only local has been implemented

    Returns:
        A dict with all predictions and models information.

        Format:
        {
            "predictions": [
                [p11, p12, ...],
                [p21, p22, ...],
                ...
            ],
            "models": [m1_info, m2_info, ...]
        }
    """

    if not os.path.isdir("./saved_predictions/" + stock_code):
        return {}

    else:
        list_of_predictions = glob.glob("./saved_predictions/" + stock_code + "/*.json")
        latest_prediction = max(list_of_predictions)
        with open(latest_prediction) as prediction:
            return json.load(prediction)

def get_predictions(stock_code):
    """Gets the predictions of a stock from all trained models.

    1. Get all saved models.
    2. Build the predict data based on the model's input options.
    3. Predict stock price.

    Args:
        stock_code: Stock code specifying a stock.

    Returns:
        A dict with all predictions and models information.

        Format:
        {
            "predictions": [
                [p11, p12, ...],
                [p21, p22, ...],
                ...
            ],
            "models": [m1_info, m2_info, ...]
        }
    """

    predictions_all = []
    snakes_all = []
    upper_all = []
    lower_all = []
    models_all = []
    past_predictions_all = []

    # linear model predictions
    models = LinearRegression.get_all_models(stock_code, SAVED_MODELS_DIR_MAP[LinearRegression.MODEL]) or []
    for model_idx, model in enumerate(models):
        print("Linear Regression Model {}".format(model_idx + 1))
        x = build_predict_dataset(model.input_options, model.model_options["predict_n"])
        prediction = model.predict(x)
        predictions_all.append(prediction.tolist())
        snakes_all.append(None)
        upper_all.append(None)
        lower_all.append(None)
        past_predictions_all.append(None)
    models_all += [{"modelName": model.get_model_display_name()} for model in models]

    # svr model predictions
    models = SupportVectorRegression.get_all_models(stock_code, SAVED_MODELS_DIR_MAP[SupportVectorRegression.MODEL]) or []
    for model_idx, model in enumerate(models):
        print("Support Vector Regression Model {}".format(model_idx + 1))
        x = build_predict_dataset(model.input_options, model.model_options["predict_n"])
        prediction = model.predict(x)
        predictions_all.append(prediction.tolist())
        snakes_all.append(None)
        upper_all.append(None)
        lower_all.append(None)
        past_predictions_all.append(None)
    models_all += [{"modelName": model.get_model_display_name()} for model in models]

    # linear index model predictions
    models = LinearIndexRegression.get_all_models(stock_code, SAVED_MODELS_DIR_MAP[LinearIndexRegression.MODEL]) or []
    for model_idx, model in enumerate(models):
        print("Linear Index Regression Model {}".format(model_idx + 1))
        x = build_predict_dataset(model.input_options, model.model_options["predict_n"])
        prediction = model.predict(x)
        predictions_all.append(prediction.tolist())
        snakes_all.append(None)
        upper_all.append(None)
        lower_all.append(None)
        past_predictions_all.append(None)
    models_all += [{"modelName": model.get_model_display_name()} for model in models]

    # svr index model predictions
    models = SupportVectorIndexRegression.get_all_models(stock_code, SAVED_MODELS_DIR_MAP[SupportVectorIndexRegression.MODEL]) or []
    for model_idx, model in enumerate(models):
        print("Support Vector Index Regression Model {}".format(model_idx + 1))
        x = build_predict_dataset(model.input_options, model.model_options["predict_n"])
        prediction = model.predict(x)
        predictions_all.append(prediction.tolist())
        snakes_all.append(None)
        upper_all.append(None)
        lower_all.append(None)
        past_predictions_all.append(None)
    models_all += [{"modelName": model.get_model_display_name()} for model in models]

    # neural network predictions
    models = DenseNeuralNetwork.get_all_models(stock_code, SAVED_MODELS_DIR_MAP[DenseNeuralNetwork.MODEL]) or []

    for model_idx, model in enumerate(models):
        print("Neural Network Model {}".format(model_idx + 1))

        predict_n = model.model_options["predict_n"]

        if predict_n == 1:
            last_predictions = []

            for _ in range(10):
                # get predict input
                x = build_predict_dataset(model.input_options, predict_n, previous=np.array(last_predictions))
                # predict
                prediction = model.predict(x)
                last_predictions.append(prediction.tolist()[0])

            predictions_all.append(last_predictions)

            # build full test set
            x_test, y_test = build_predict_dataset(model.input_options, predict_n, predict=False)
            # predict full test set
            prediction_test = model.predict(x_test)
            past_predictions_all.append(prediction_test.flatten().tolist())

            # get stock data
            stock_data = get_stock_data(model.input_options["stock_codes"])

            # predict snakes test set
            snakes = np.array([[] for _ in range(10)])
            for _ in range(10):
                snakes_x = []
                for snake_idx in range(10):
                    snakes_x += build_predict_dataset(
                        model.input_options,
                        predict_n,
                        stock_data=stock_data,
                        previous=snakes[snake_idx],
                        skip_last=10 + snake_idx * 10
                    ).tolist()
                snakes_prediction = model.predict(np.array(snakes_x))
                snakes = np.concatenate((snakes, snakes_prediction), axis=1)
            snakes = np.flipud(snakes)
            snakes_all.append(snakes.tolist())

            # calculate upper bound and lower bound
            snakes_y = stock_data[model.input_options["stock_code"]][model.input_options["column"]].values[-100:].reshape(10, 10)
            upper_all.append((last_predictions + np.std(snakes - snakes_y, axis=0)).tolist())
            lower_all.append((last_predictions - np.std(snakes - snakes_y, axis=0)).tolist())
        else:
            # get predict input
            x = build_predict_dataset(model.input_options, predict_n)
            # predict
            prediction = model.predict(x)
            predictions_all.append(prediction.tolist())

            # build snakes test set
            x_test, y_test = build_predict_dataset(model.input_options, predict_n, predict=False, test_set="snakes")
            # predict snakes test set
            prediction_test = model.predict(x_test)
            snakes_all.append(prediction_test.tolist())

            # calculate upper bound and lower bound
            upper_all.append((prediction[0] + np.std(prediction_test - y_test, axis=0)).tolist())
            lower_all.append((prediction[0] - np.std(prediction_test - y_test, axis=0)).tolist())

            # build full test set
            x_test, y_test = build_predict_dataset(model.input_options, predict_n, predict=False)
            # predict full test set
            prediction_test = model.predict(x_test)
            past_predictions_all.append(prediction_test[:, 0].tolist())

    models_all += [
        {
            "modelName": model.get_model_display_name(),
            "model": "dnn",
            "modelOptions": model.model_options,
            "inputOptions": model.input_options
        }
        for model in models
    ]

    return {
        "predictions": predictions_all,
        "snakes": snakes_all,
        "upper": upper_all,
        "lower": lower_all,
        "rollingPredict": past_predictions_all,
        "models": models_all
    }

def save_predictions_local(stock_code):
    """Saves predictions in local in saved_predictions/<stock_code>."""

    # get the predictions
    predictions = get_predictions(stock_code)

    # create the predictions folder for the stock if it does not exist
    if not os.path.isdir("./saved_predictions/" + stock_code):
        os.makedirs("./saved_predictions/" + stock_code)

    # save the predictions and models
    with open("./saved_predictions/" + stock_code + "/" + date.today().isoformat() + ".json", "w") as predictions_file:
        json.dump(predictions, predictions_file, indent=4)

def save_predictions_cloud(stock_code):
    """Saves predictions onto Firebase Cloud Storage in predictions/<stock_code>."""

    # initialize Firebase admin
    cred = credentials.Certificate("credentials/firebase-adminsdk.json")
    firebase_admin.initialize_app(cred, {
        "storageBucket": "cmms-fyp.appspot.com"
    })

    bucket = storage.bucket()

    # get the predictions
    predictions = get_predictions(stock_code)

    # upload the predictions and models to cloud
    predictions_json_str = json.dumps(predictions)
    blob = bucket.blob("predictions/" + stock_code + "/predictions.json")
    blob.upload_from_string(predictions_json_str, "application/json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save predictions.")
    parser.add_argument("storage", choices=["local", "cloud"], help="Storage")
    parser.add_argument("stock_code", help="Stock code")

    args = parser.parse_args()

    if args.storage == "local":
        save_predictions_local(args.stock_code)
    elif args.storage == "cloud":
        save_predictions_cloud(args.stock_code)
