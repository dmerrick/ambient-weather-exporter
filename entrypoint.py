#!/usr/bin/env python

import time
import math
import os

from ambient_api.ambientapi import AmbientAPI
from prometheus_client import Info, Gauge
from prometheus_client import start_http_server

# Overall stuff left to do:
#  - handle multiple and zero devices better
#  - push bugfixes upstream
#  - experiment with changing unit settings in my profile
#  - work build and device information into prom metrics
#  - local testing interface / method?

api = AmbientAPI()
if not api.api_key:
    raise Exception("You must specify an API Key")
if not api.application_key:
    raise Exception("You must specify an Application Key")

# devices = api.get_devices()
# if len(devices) == 0:
#    raise Exception("No weather devices found on your account. Exiting.")

i = Info(
    "ambient_weather_exporter",
    "Prometheus exporter for Ambient Weather personal weather station",
)
i.info({"version": "0"})



gauges = []

def new_gauge(prom_name):
    if "PROM_PREFIX" in os.environ:
        gauge = Gauge(f"{os.environ['PROM_PREFIX']}_{prom_name}", "")
    else:
        gauge = Gauge(prom_name, "")
    gauge._ambient_name = prom_name
    gauges + [gauge]
    return gauge


# Fields left to handle:
# dateutc
# lastRain
# date

# gauges = {
#     new_gauge("humidityin", "indoor_humidity", "Indoor Relative Humidity (RH%)"),
#     new_gauge(
#         "humidityin_absolute",
#         "indoor_humidity_absolute",
#         "Indoor Absolute Humidity (g/m^3)",
#     ),
#     new_gauge("baromrelin", "baromrelin", "Barometer FIXME 1"),
#     new_gauge("baromabsin", "baromabsin", "Barometer FIXME 2"),
#     new_gauge("humidity", "outdoor_humidity", "Outdoor Relative Humidity (RH%)"),
#     new_gauge("humidity2", "outdoor_humidity2", "Outdoor Relative Humidity (RH%)"),
#     new_gauge(
#         "humidity_absolute",
#         "outdoor_humidity_absolute",
#         "Outdoor Absolute Humidity (g/m^3)",
#     ),
#     new_gauge("winddir", "wind_direction", "Wind Direction (0-359 degrees)"),
#     new_gauge(
#         "windspeedmph", "wind_speed", "Wind Speed (MPH)"
#     ),  # FIXME: what if i change my prefs to m/s?
#     new_gauge("windgustmph", "wind_gust", "Wind Gust (MPH)"),
#     new_gauge("maxdailygust", "wind_gust_daily_max", "Maximum Daily Wind Gust (MPH)"),
#     # FIXME: should rain figures be Counters instead?
#     new_gauge(
#         "hourlyrainin", "rain_hourly", "Rainfall per hour (inches)"
#     ),  # FIXME: units?
#     new_gauge("eventrainin", "rain_event", "Rainfall per this event? FIXME. Inches."),
#     new_gauge("dailyrainin", "rain_daily", "Rainfall per day (inches)"),
#     new_gauge("weeklyrainin", "rain_weekly", "Rainfall per week (inches)"),
#     new_gauge("monthlyrainin", "rain_monthly", "Rainfall per month (inches)"),
#     new_gauge("totalrainin", "rain_total", "Rainfall total (inches)"),
#     new_gauge("solarradiation", "solar_radiation", "Solar Radiation (W/m2)"),
#     new_gauge("uv", "uv", "Ultravoilet Index"),
#     new_gauge(
#         "feelsLike",
#         "outdoor_temperature_heat_index_f",
#         "Outdoor Temperature Heat Index / Feels Like (Degrees F)",
#     ),
#     new_gauge(
#         "feelsLike_c",
#         "outdoor_temperature_heat_index",
#         "Outdoor Temperature Heat Index / Feels Like (Degrees C)",
#     ),
#     new_gauge(
#         "feelsLikein",
#         "outdoor_temperature_heat_index_in_f",
#         "Outdoor Temperature Heat Index / Feels Like (Degrees F)",
#     ),
#     new_gauge(
#         "feelsLikein_c",
#         "outdoor_temperature_heat_index_in",
#         "Outdoor Temperature Heat Index / Feels Like (Degrees C)",
#     ),
#     new_gauge(
#         "feelsLike2",
#         "outdoor_temperature_heat_index2_f",
#         "Outdoor Temperature Heat Index / Feels Like (Degrees F)",
#     ),
#     new_gauge(
#         "feelsLike2c",
#         "outdoor_temperature_heat_index2",
#         "Outdoor Temperature Heat Index / Feels Like (Degrees C)",
#     ),
#     new_gauge(
#         "dewPoint",
#         "outdoor_temperature_dew_point_f",
#         "Outdoor Temperature Dew Point (Degrees F)",
#     ),
#     new_gauge(
#         "dewPoint_c",
#         "outdoor_temperature_dew_point",
#         "Outdoor Temperature Dew Point (Degrees C)",
#     ),
#     new_gauge(
#         "dewPointin",
#         "outdoor_temperature_dew_point_in_f",
#         "Indoor Temperature Dew Point (Degrees F)",
#     ),
#     new_gauge(
#         "dewPointin_c",
#         "outdoor_temperature_dew_point_in",
#         "Indoor Temperature Dew Point (Degrees C)",
#     ),
#     new_gauge(
#         "dewPoint2",
#         "outdoor_temperature_dew_point2_f",
#         "Outdoor Temperature Dew Point (Degrees F)",
#     ),
#     new_gauge(
#         "dewPoint2c",
#         "outdoor_temperature_dew_point2",
#         "Outdoor Temperature Dew Point (Degrees C)",
#     ),
# }

def get_device():
    devices = api.get_devices()
    if len(devices) == 0:
        print(
            "No devices found on Ambient Weather account. Check your credentials are correct."
        )
        exit(1)
    # FIXME: handle multiple devices
    device = devices[0]
    print(device.info)
    print(
        device.mac_address
    )  # FIXME: add mac address as an instance parameter on all fields
    return device

def set_up_guages(device):
    last_data = device.last_data
    for key, value in last_data.items():
        if key in ["date", "dateutc", "loc"]:

            print("skipping: " + key)
            continue
        # create the prometheus gauge
        new_gauge(key)
        # if key.startswith("temp"):
        #     print("temperature found: " + key)

device = get_device()
set_up_guages(device)

start_http_server(8000)

while True:
    last_data = device.last_data
    now = time.time()
    if last_data["dateutc"] / 1000 < now - 120:
        raise Exception(
            "Stale data from Ambient API; dateutc={}, now={}".format(
                last_data["dateutc"], now
            )
        )
    print(last_data)
    for gauge in gauges:
        if gauge._ambient_name in last_data:
            gauge.set(last_data[gauge._ambient_name])
    print("sleeping 60")
    time.sleep(60)
