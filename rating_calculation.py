import argparse
import json

from train_models import train_models

from models.linear_index_regression import LinearIndexRegression
from models.svr_index_regression import SupportVectorIndexRegression
import matplotlib.pyplot as plt
import math

# Calculate the MAE of the prediction from the model
# Assume following format:
# actual prices = [price_0, price_1, ..., price_n] # n+1 day in total
# predicted prices = [price_1, ..., price_n] # (snakes), n day in total

def relative_mean_absolute_error(actual_prices, predicted_prices, t_0, time_interval):
    rmae = 0

    for i in range(time_interval):
        rmae += abs(predicted_prices[t_0 + i] / actual_prices[t_0 + i + 1] - 1 )
    rmae /= time_interval

    if rmae < 0:
        print ("error: [relative_mean_absolute_error Line 29] RMAE cannot be smaller than zero")
        exit(-1)
    return rmae 

def isSameDirection(actual_prices, predicted_prices, t_0, time_interval):
    return (actual_prices[t_0 + time_interval] - actual_prices[t_0] < 0) == (predicted_prices[t_0 + time_interval - 1] - actual_prices[t_0] < 0)


def isUnderestimated(actual_prices, predicted_prices, t_0, time_interval):
    # given that they are same direction 
    return abs(actual_prices[t_0 + time_interval] - actual_prices[t_0]) > abs(predicted_prices[t_0 + time_interval -1] - actual_prices[t_0])

# Calculate the rating based on RMAE
def model_rating(actual_prices, snakes, time_interval):
    
    predicted_prices = []

    for sublist in snakes:
        for item in sublist:
            predicted_prices.append(item)

    alpha = 0.2
    if predicted_prices == []:
        print(
            "[model_rating] predicted prices with a length of zero")
        return 0

    if len(actual_prices) - 1 != len(predicted_prices):
        print(
            "error: [model_rating] predicted price length inequal to actual price length")
        exit(-1)

    if len(predicted_prices)%time_interval != 0:
        # if length of predicted prices is not divisible by the time_interval, it is an error
        print(
            "error: [model_rating] predicted price length not divisible by time interval")
        exit(-1)


    rating = 0

    for i in range(len(predicted_prices)//time_interval):
        rmae = relative_mean_absolute_error(actual_prices, predicted_prices, i*time_interval, time_interval)

        error_rate = rmae if rmae < 1 else 1 

        if not isSameDirection(actual_prices, predicted_prices, i*time_interval, time_interval):
            reward = 0 
        elif isUnderestimated(actual_prices, predicted_prices, i*time_interval, time_interval):
            reward = 1.0
        else:
            reward = 0.8

        rating += (1 - alpha) * math.cos(error_rate) + alpha * reward 
    
    return rating/ (len(predicted_prices) / time_interval)

def direction(today_price, predicted_price):
    return 1 if predicted_price >= today_price else -1 

def calculate_traffic_light_score(models):
    traffic_light_score = 0
    for i in models:
        traffic_light_score += i["score"] * i["direction"]
    
    return (traffic_light_score/len(models))

    
