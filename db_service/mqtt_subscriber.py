import os, time
from influxdb_client_3 import InfluxDBClient3, Point
import paho.mqtt.client as mqtt
import json

#set INFLUXDB_TOKEN=C-seWzRsZrVkx6rtbBDuV1w1h0HT0A23nWKxK7XX-o0qgkJJBXA_-ydFdexcFed3PhrV24TsZNboD4erC0KRhw==
token = os.environ.get("INFLUXDB_TOKEN")
org = "FEL"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"

influx_client = InfluxDBClient3(host='localhost', port=8086, database='predictions')


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("anomaly/predictions")


def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    json_body = [
        {
            "measurement": "anomaly_detection",
            "tags": {
                "prediction_id": str(data['prediction_id'])
            },
            "fields": {
                "result": data['result'],
                "series_length": data['series_length'],
                "series_data": str(data['series_data'])
            }
        }
    ]
    influx_client.write_points(json_body)


mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect("broker.hivemq.com", 1883)
mqtt_client.loop_forever()
