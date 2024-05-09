import pickle

import paho.mqtt.client as mqtt

from helpers import get_logger

logger = get_logger("Mqtt Publisher")


def on_connect(client, userdata, flags, reason_code, properties):
    logger.info("Connected with result code " + str(reason_code))


def on_publish(client, userdata, mid, reason_code, properties):
    logger.info(f"Published data via MQTT")


def mqtt_connect():
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_publish = on_publish
    mqtt_client.connect("broker.hivemq.com")
    mqtt_client.loop_start()
    return mqtt_client


def publish_data(client, array, prediction, identifier):
    data_bundle = {
        'array': array,
        'prediction': prediction,
        'identifier': identifier
    }

    client.publish("anomaly/predictions", pickle.dumps(data_bundle))

