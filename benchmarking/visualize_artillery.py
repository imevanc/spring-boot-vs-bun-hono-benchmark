#!/usr/bin/env python3

import json
import pandas as pd
import matplotlib.pyplot as plt

def load_and_parse_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def create_visualizations(data):
    # Set style to a built-in style
    plt.style.use('ggplot')

    # Create figure with subplots
    fig = plt.figure(figsize=(15, 20))

    # 1. Response Time Distribution
    plt.subplot(3, 1, 1)
    response_times = {
        'min': data['aggregate']['summaries']['http.response_time']['min'],
        'median': data['aggregate']['summaries']['http.response_time']['median'],
        'p95': data['aggregate']['summaries']['http.response_time']['p95'],
        'p99': data['aggregate']['summaries']['http.response_time']['p99'],
        'max': data['aggregate']['summaries']['http.response_time']['max']
    }
    plt.bar(response_times.keys(), response_times.values(), color='skyblue')
    plt.title('Response Time Distribution (ms)')
    plt.ylabel('Time (ms)')

    # 2. Endpoint Distribution
    plt.subplot(3, 1, 2)
    endpoints = {
        'compute': data['aggregate']['counters']['plugins.metrics-by-endpoint./compute.codes.200'],
        'echo': data['aggregate']['counters']['plugins.metrics-by-endpoint./echo.codes.200'],
        'users': data['aggregate']['counters']['plugins.metrics-by-endpoint./users/{{ userId }}.codes.200'],
        'health': data['aggregate']['counters']['plugins.metrics-by-endpoint./health.codes.200'],
        'stats': data['aggregate']['counters']['plugins.metrics-by-endpoint./stats.codes.200']
    }
    plt.pie(endpoints.values(), labels=endpoints.keys(), autopct='%1.1f%%')
    plt.title('Request Distribution by Endpoint')

    # 3. Time Series of Requests
    plt.subplot(3, 1, 3)
    timestamps = []
    requests = []

    for period in data['intermediate']:
        timestamps.append(pd.to_datetime(int(period['period']), unit='ms'))
        requests.append(period['counters']['http.requests'])

    plt.plot(timestamps, requests, marker='o', color='green')
    plt.title('Requests Over Time')
    plt.xlabel('Time')
    plt.ylabel('Number of Requests')
    plt.xticks(rotation=45)

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('artillery_results.png')

    # Create additional detailed response time graph
    plt.figure(figsize=(10, 6))
    endpoint_response_times = {
        'compute': data['aggregate']['summaries']['plugins.metrics-by-endpoint.response_time./compute']['mean'],
        'echo': data['aggregate']['summaries']['plugins.metrics-by-endpoint.response_time./echo']['mean'],
        'users': data['aggregate']['summaries']['plugins.metrics-by-endpoint.response_time./users/{{ userId }}']['mean'],
        'health': data['aggregate']['summaries']['plugins.metrics-by-endpoint.response_time./health']['mean'],
        'stats': data['aggregate']['summaries']['plugins.metrics-by-endpoint.response_time./stats']['mean']
    }
    plt.bar(endpoint_response_times.keys(), endpoint_response_times.values(), color='lightcoral')
    plt.title('Average Response Time by Endpoint')
    plt.ylabel('Response Time (ms)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('endpoint_response_times.png')

def main():
    try:
        # Load the data
        data = load_and_parse_data('bun-hono-results.json')

        # Create visualizations
        create_visualizations(data)

        # Print summary statistics
        print("\nTest Summary:")
        print(f"Total Requests: {data['aggregate']['counters']['http.requests']}")
        print(f"Total Users: {data['aggregate']['counters']['vusers.created']}")
        print(f"Failed Requests: {data['aggregate']['counters']['vusers.failed']}")
        print(f"Average Response Time: {data['aggregate']['summaries']['http.response_time']['mean']:.2f}ms")
        print(f"95th Percentile: {data['aggregate']['summaries']['http.response_time']['p95']}ms")

    except FileNotFoundError:
        print("Error: Could not find 'spring-boot-results.json'. Make sure the file exists in the current directory.")
    except KeyError as e:
        print(f"Error: Could not find expected data in JSON file. Missing key: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()