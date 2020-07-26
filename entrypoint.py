#!/usr/bin/env python

import time
import math
import os

from ambient_api.ambientapi import AmbientAPI
from prometheus_client import Info, Gauge
from prometheus_client import start_http_server

api = AmbientAPI()
gauges = []

if not api.api_key:
    raise Exception("You must specify an API Key")
if not api.application_key:
    raise Exception("You must specify an Application Key")

i = Info(
    "ambient_weather_exporter",
    "Prometheus exporter for Ambient Weather personal weather station",
).info({"version": "0"})


def new_gauge(prom_name):
    global gauges
    if "PROM_PREFIX" in os.environ:
        gauge = Gauge(f"{os.environ['PROM_PREFIX']}_{prom_name}", "")
    else:
        gauge = Gauge(prom_name, "")
    gauge._ambient_name = prom_name
    gauges = gauges + [gauge]
    return gauge


def get_device():
    devices = api.get_devices()
    if len(devices) == 0:
        print(
            "No devices found on Ambient Weather account. Check your credentials are correct."
        )
        exit(1)
    # FIXME: handle multiple devices
    device = devices[0]
    # print(device.info)
    # print(
    #     device.mac_address
    # )  # FIXME: add mac address as an instance parameter on all fields
    return device


def set_up_guages(device):
    response = device.last_data
    print(response)
    for key, value in response.items():
        if key in ["date", "dateutc", "loc", "tz"]:
            print("not creating guage for " + key)
            continue
        # create the prometheus gauge
        new_gauge(key)


def check_and_update(device):
    global previous_dateutc
    # fetch the weather data
    response = device.last_data
    print(response) # TODO: remove this

    # check if data is the same as last time
    if response["dateutc"] == previous_dateutc:
        print("Stale data from Ambient API")
        return
    print(response)
    for gauge in gauges:
        if gauge._ambient_name in response:
            gauge.set(response[gauge._ambient_name])
    # store the time from the last response
    previous_dateutc = response["dateutc"]

device = get_device()
set_up_guages(device)
start_http_server(8000)

previous_dateutc = ""
while True:
    check_and_update(device)
    print("sleeping 60")
    time.sleep(60)

