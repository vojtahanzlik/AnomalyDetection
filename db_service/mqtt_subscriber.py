import datetime
import pickle

import certifi
import paho.mqtt.client as mqtt
from influxdb_client_3 import InfluxDBClient3

token = "x4NKvlSG6Ll7FAaHI4TMnf1eOzjJgThBU07MRrNjacnLOZjrx_BpVBdFrWbUVBw1WeaQdBIZwGN2IOBICJB_RQ=="
org = "FEL"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"

influx_client = InfluxDBClient3(host=host, database="Delta_Robot_Sensor_Data",
                                org=org, token=token,
                                ssl_ca_cert=certifi.where())

time_step = 0.004


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with result code " + str(reason_code))
    mqtt_client = client
    mqtt_client.subscribe("anomaly/predictions")
    mqtt_client.on_message = on_message


def mqtt_connect():
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.connect("broker.hivemq.com")
    return mqtt_client


def on_message(client, userdata, msg):
    data_bundle = pickle.loads(msg.payload)
    array = data_bundle['array'].T
    array_len = array.shape[1]
    prediction = data_bundle['prediction']
    identifier = data_bundle['identifier']
    start_time = datetime.datetime.now()
    interval = datetime.timedelta(seconds=0.004)
    timestamps = [start_time + i * interval for i in range(array_len)]
    records = [
        {
            "measurement": "time_series_segments",
            "time": timestamps[i].isoformat() + "Z",
            "fields": {
                "field1": float(array[0][i]),
                "field2": float(array[1][i]),
                "field3": float(array[2][i]),
                "field4": float(array[3][i]),
                "field5": float(array[4][i]),
                "field6": float(array[5][i]),
                "prediction": prediction,
                "identifier": identifier
            }
        } for i in range(array_len)
    ]

    influx_client.write(record=records, database="Delta_Robot_Sensor_Data")
    print("Records written")


if __name__ == '__main__':
    c = mqtt_connect()
    c.loop_forever()
