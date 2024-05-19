import pickle

import numpy as np
import paho.mqtt.client as mqtt

from helpers import get_logger

logger = get_logger("Mqtt Publisher")


def on_connect(client, userdata, flags, reason_code, properties):
    """
    Callback for when the client receives a CONNACK response from the server.

    Args:
        client: The client instance for this callback.
        userdata: The private user data as set in Client().
        flags: Response flags sent by the broker.
        reason_code: The connection result.
        properties: The properties associated with the connection.
    """
    logger.info(f"Connected to MQTT broker with {reason_code}")


def on_publish(client, userdata, mid, reason_code, properties):
    """
    Callback for when a message that was to be sent using the publish() call has completed transmission to the broker.

    Args:
        client: The client instance for this callback.
        userdata: The private user data as set in Client().
        mid: The message ID for the publish request.
        reason_code: The result of the publishing.
        properties: The properties associated with the publish.
    """
    logger.info(f"Published data via MQTT")


def mqtt_connect():
    """
    Connects to the MQTT broker and starts the loop.

    Returns:
        mqtt.Client: The MQTT client instance.
    """
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_publish = on_publish
    mqtt_client.connect("broker.hivemq.com")
    mqtt_client.loop_start()
    return mqtt_client


def publish_data(client, identifier: int, curr_pred: bool):
    """
    Publishes data to the MQTT topic.

    Args:
        client (mqtt.Client): The MQTT client instance.
        identifier (int): The identifier of the data.
        curr_pred (bool): The current prediction value.
    """
    data_bundle = {
        'identifier': identifier,
        'curr_pred': curr_pred,
        'update': True
    }

    client.publish("anomaly/predictions", pickle.dumps(data_bundle))
