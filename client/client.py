from abc import ABC, abstractmethod
from collections import deque
from typing import Iterator
from flask_socketio import SocketIO
import grpc
import paho.mqtt.client as mqtt

from messages_pb2 import NumpyArray
from messages_pb2_grpc import AnomalyDetectionServiceStub
from helpers import get_logger


class ClientBase(ABC):

    def __init__(self, socket: SocketIO, address='localhost:8061'):
        self.logger = get_logger(self.__class__.__name__)
        channel = grpc.insecure_channel(address)
        self.stub = AnomalyDetectionServiceStub(channel)
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect("broker.hivemq.com", 1883)
        self.socket = socket
        self.predictions = deque(maxlen=20)
        self.stop_stream = False
        self.stream_in_progress = False

    @abstractmethod
    def _stream_messages(self) -> Iterator[NumpyArray]:
        """Server request callback function"""
        pass

    def stream_data(self):
        if not self.stream_in_progress:
            try:
                self.stream_in_progress = True
                self.stop_stream = False
                response_iterator = self.stub.StreamData(self._stream_messages())
                for response in response_iterator:
                    if self.stop_stream:
                        break
                    time_series_identifier = int(response.id)
                    time_series_len = int(response.series_len)
                    pred = bool(response.result)

                    self.predictions.append({'id': time_series_identifier, 'result': pred, 'series_len': time_series_len})
                    self.logger.info(f"Server response: result: {pred} id: {time_series_identifier}"
                                     f" time series length: {time_series_len}")

                    self.socket.emit('update_predictions', list(self.predictions))
            except Exception as e:
                self.logger.exception(e)
            self.stream_in_progress = False

    def stop_streaming(self):
        self.stop_stream = True
        self.stream_in_progress = False
