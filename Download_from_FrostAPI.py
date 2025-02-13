# -*- coding: utf-8 -*-
"""
Downloading historical rainfall data from Frost API
"""

# Libraries needed (pandas is not standard and must be installed in Python)
import requests
import pandas as pd

# Insert your own client ID here
client_id = 'a4012d62-c50b-4c44-9ebe-3244b7f18dfd'

# Define endpoint and parameters
endpoint = 'https://frost.met.no/observations/v0.jsonld'
parameters = {
    'sources': 'SN18205',      # For Løren
    'elements': 'sum(precipitation_amount P1M)',
    'referencetime': '2000-01-01/2024-12-31',
}
# Issue an HTTP GET request
response = requests.get(endpoint, parameters, auth=(client_id, ''))

#  Assign the JSON data to the variable `json_data`
json_data = response.json()

# Check if the request worked, print out any errors
if response.status_code == 200:
    print('Data retrieved successfully from Frost API!')
else:
    print(f'Error {response.status_code}: {json_data.get("error", {}).get("message", "Unknown error")}')

#  Ensure `json_data` is defined before accessing it
df = pd.DataFrame()
if 'data' in json_data:
    for item in json_data['data']:
        row = pd.DataFrame(item['observations'])
        row['referenceTime'] = item['referenceTime']
        row['sourceId'] = item['sourceId']
        df = pd.concat([df, row], ignore_index=True)
else:
    print("No data found in the API response.")

# Select relevant columns
columns = ['sourceId', 'referenceTime', 'elementId', 'value', 'unit']
df_filtered = df[columns].copy()

# Convert the referenceTime to datetime format
df_filtered['referenceTime'] = pd.to_datetime(df_filtered['referenceTime'])

# Display the first few rows
print(df_filtered.head())