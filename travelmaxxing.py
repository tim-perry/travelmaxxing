from datetime import datetime, timedelta
from dotenv import load_dotenv
from pandas import json_normalize
import requests
import pandas
import streamlit
import re
import time
import os

BATCH_SIZE = 50
LISTING_COUNT = 2

def extract_price(text):
    numbers = re.search(r'\d+(\.\d+)?', text)
    return float(numbers.group())

#Authentication
def authenticate(client_id, client_secret):
    url = "https://api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print("Authorization successful")
        return response.json().get('access_token')
    else:
        print("Authorization failed")
        return -1

#Flight Search API Call
def flight_search(origin, destination, earliest_departure, latest_return, min_duration, max_duration):
    latest_departure = datetime.fromisoformat(latest_return) - timedelta(days = min_duration)
    departure_date_range = earliest_departure + ',' + latest_departure.strftime("%Y-%m-%d")

    url = 'https://api.amadeus.com/v1/shopping/flight-dates'
    params = {
        "origin": origin,
        "destination": destination,
        "departureDate": departure_date_range,
        "duration": str(min_duration) + ',' + str(max_duration),
        "viewBy": "DURATION"
    }
    headers = {'Authorization': 'Bearer ' + token}
    call_time = time.time()
    response = requests.get(url, params=params, headers=headers)
    response_time = time.time()
    elapsed_time = response_time - call_time
    print(f"Flight search API call took {elapsed_time}s")
    return response.json()

#Get hotel IDs    
def get_hotel_ids(city_code):
    url = 'https://api.amadeus.com/v1/reference-data/locations/hotels/by-city'
    params = {
        "cityCode": city_code
    }
    headers = {'Authorization': 'Bearer ' + token}
    response = requests.get(url, params=params, headers=headers)
    response_json = response.json()
    hotel_ids = [hotel['hotelId'] for hotel in response_json['data']]
    return hotel_ids

#Hotel Search API Call
def hotel_search(hotel_ids, checkin_date, checkout_date):
    minimum_price = 0 
    cheapest_hotel = 'INIT'
    # Loop through the hotel_ids array in steps of batch_size
    for i in range(0, len(hotel_ids), BATCH_SIZE):
        batch = hotel_ids[i:i + BATCH_SIZE]
        params = {
            "hotelIds": batch,
            "adults": 2,
            "checkInDate": checkin_date,
            "checkOutDate": checkout_date,
            "bestRateOnly": 'true'
        }
        headers = {'Authorization': 'Bearer ' + token}
        call_time = time.time()
        response = requests.get('https://api.amadeus.com/v3/shopping/hotel-offers', params=params, headers=headers)
        response_time = time.time()
        elapsed_time = response_time - call_time
        print(f"Hotel search API call took {elapsed_time}s")
        try:
            for item in response.json()['data']:
                if cheapest_hotel == 'INIT' or extract_price(item['offers'][0]['price']['total']) <= minimum_price:
                    minimum_price = extract_price(item['offers'][0]['price']['total'])
                    cheapest_hotel = item['hotel']['hotelId']
        except:
            print(response.json())
            print('Error processing the above batch')
    return minimum_price, cheapest_hotel

#Load API keys
load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

#User input
origin = 'SYD'
destination = 'BNE'
earliest_departure = '2024-12-01'
latest_return = '2024-12-09'
min_duration = 3
max_duration = 5

#Authenticate and do API calls
token = authenticate(client_id, client_secret)
hotel_ids = get_hotel_ids(destination)
flights = flight_search(origin, destination, earliest_departure, latest_return, min_duration, max_duration)

#Setup dataframe for output
df = pandas.DataFrame(columns=['Start Date', 'End Date', 'Flight Price', 'Hotel Price', 'Hotel ID'])

#For cheapest n (LISTING_COUNT) flight itineraries, find the cheapest hotel for that date range
for i in range(min(len(flights), LISTING_COUNT)):
    flight_departure = flights['data'][i]['departureDate']
    flight_return = flights['data'][i]['returnDate']
    flight_price = extract_price(flights['data'][i]['price']['total'])
    hotel_price, hotel = hotel_search(hotel_ids, flight_departure, flight_return)
    total_price = flight_price + hotel_price

    row_df = pandas.DataFrame([{
        'Start Date': flight_departure,
        'End Date': flight_return,
        'Flight Price': flight_price,
        'Hotel Price': hotel_price,
        'Totel Price': total_price,
        'Hotel ID': hotel
    }])
    df = pandas.concat([df, row_df], ignore_index=True)

streamlit.dataframe(df)