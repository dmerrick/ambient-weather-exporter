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

i = Info(
    "ambient_weather_exporter",
    "Prometheus exporter for Ambient Weather personal weather station",
).info({"version": "0"})



gauges = []

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
    print(device.info)
    print(
        device.mac_address
    )  # FIXME: add mac address as an instance parameter on all fields
    return device

def set_up_guages(device):
    last_data = device.last_data
    for key, value in last_data.items():
        if key in ["date", "dateutc", "loc","tz"]:
            print("skipping: " + key)
            continue
        # create the prometheus gauge
        new_gauge(key)

device = get_device()
set_up_guages(device)
print(gauges)

start_http_server(8001)

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
