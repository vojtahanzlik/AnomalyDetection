from datetime import datetime
import pickle

import certifi
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from pymongo.server_api import ServerApi

mongotoken = "7VsHwuoa6fEtZMsEgiFspBPo6j7x33DS3jxnjyNzCKRGtSDDDrZZldIwVsip3Chl"
uri = "mongodb+srv://deltarobot.sfzmqlm.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=DeltaRobot"
mongo_client = MongoClient(uri,
                           tls=True,
                           tlsCertificateKeyFile='X509-cert-3280764759596531256.pem',
                           server_api=ServerApi('1'),
                           tlsCAFile=certifi.where())
mongo_db = mongo_client['DeltaRobot']
mongo_collection = mongo_db['time_series_predictions']
#mongo_collection = mongo_db['force_torque_predictions']


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
    if data_bundle['update']:
        handle_label_update_message(data_bundle)
    else:
        handle_prediction_message(data_bundle)


def handle_label_update_message(data_bundle):
    identifier = data_bundle['identifier']
    curr_pred = data_bundle['curr_pred']

    filter = {"identifier": identifier}
    update = {
        "$set": {"human_label": not curr_pred}}

    result = mongo_collection.update_many(filter, update)
    print(f"Result of DB update: {result}")


def handle_prediction_message(data_bundle):
    array = data_bundle['array'].T
    array_len = array.shape[1]
    prediction = data_bundle['prediction']
    identifier = data_bundle['identifier']
    timestamps = data_bundle['timestamps']

    records = [
        {
            "identifier": identifier,
            "timestamp": datetime.fromtimestamp(timestamps[i]),
            "fields": {
                "Force_x": float(array[0][i]),
                "Force_y": float(array[1][i]),
                "Force_z": float(array[2][i]),
                "Torque_x": float(array[3][i]),
                "Torque_y": float(array[4][i]),
                "Torque_z": float(array[5][i]),
            },
            "prediction": prediction,
            "human_label": None
        } for i in range(array_len)
    ]

    result = mongo_collection.insert_many(records)
    print(f"Inserted {len(result.inserted_ids)} records into the database.")


if __name__ == '__main__':
    #result = mongo_collection.delete_many({})
    #print(result)
    c = mqtt_connect()
    c.loop_forever()
