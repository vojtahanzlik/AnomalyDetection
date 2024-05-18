import csv
import datetime
import time
from abc import ABC, abstractmethod
from collections import deque
from typing import Iterator
from flask_socketio import SocketIO
import grpc
from grpc._channel import _MultiThreadedRendezvous

from messages_pb2 import NumpyArray
from messages_pb2_grpc import AnomalyDetectionServiceStub
from helpers import get_logger

messages_timestamps = dict()


class ClientBase(ABC):

    def __init__(self, socket: SocketIO, address='localhost:8061'):
        self.stub = None
        self.logger = get_logger(self.__class__.__name__)
        self.address = address
        self.connect(address)
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
                    messages_timestamps[response.msg_id].append(datetime.datetime.now())

                    if self.stop_stream:
                        break
                    time_series_identifier = int(response.id)
                    time_series_len = int(response.series_len)
                    pred = bool(response.result)

                    self.predictions.append(
                        {'id': time_series_identifier,
                         'result': pred,
                         'series_len': time_series_len,
                         'timestamp': time.time()
                         }
                    )
                    self.logger.info(f"Server response: result: {pred} id: {time_series_identifier}"
                                     f" time series length: {time_series_len}")

                    self.socket.emit('update_predictions', list(self.predictions))

            except _MultiThreadedRendezvous as e:
                self.logger.exception(e)
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    self.connect(self.address)
            self.stream_in_progress = False

            with open(f"results{self.address}.csv", 'w', newline='') as file:
                writer = csv.writer(file)
                for key in messages_timestamps:
                    timestamps = messages_timestamps[key]
                    if len(timestamps) > 1:
                        duration = timestamps[1] - timestamps[0]
                        writer.writerow([key, duration.total_seconds() * 1000])

    def connect(self, address):
        channel = grpc.insecure_channel(address)
        self.stub = AnomalyDetectionServiceStub(channel)

    def stop_streaming(self):
        self.stop_stream = True
        self.stream_in_progress = False
