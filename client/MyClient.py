import os
from datetime import datetime
from time import sleep
from typing import Iterator
from flask_socketio import SocketIO
import numpy as np
from client import ClientBase
from messages_pb2 import NumpyArray
from opc_ua_client import run_opc_ua
import client

class MyClient(ClientBase):
    """
    A specific client implementation for connecting to an OPC UA server and streaming data.
    """
    def __init__(self, socket: SocketIO):
        super().__init__(socket)
        self.data_point_interval = 0.004

    def yield_test(self):
        """
        Simulates data received by OPC UA client.
        For local testing purposes.

        Returns:
            Iterator[np.ndarray]: An iterator of numpy arrays.
        """
        prev_last_timestamp = 0
        directory = "test_samples"
        for file in os.listdir(directory):
            filename = os.fsdecode(file)
            data = np.load(f"{directory}/{filename}")
            selected_rows = data[4:11, :]

            dt = datetime.now()
            first_timestamp = dt.timestamp()
            first_timestamp = max(first_timestamp, prev_last_timestamp + 1)
            num_of_datapoints = selected_rows.shape[1]
            last_timestamp = first_timestamp + (num_of_datapoints - 1) * self.data_point_interval

            prev_last_timestamp = last_timestamp
            timestamps = np.linspace(start=first_timestamp, stop=last_timestamp, num=num_of_datapoints)
            selected_rows = np.vstack((selected_rows, timestamps))

            split_arrays = np.array_split(selected_rows, 24, axis=1)
            for array in split_arrays:
                yield array
        yield None

    def _stream_messages(self) -> Iterator[NumpyArray]:
        """
        Streams generated data to the server.

        Returns:
            Iterator[NumpyArray]: An iterator of NumpyArray messages defined in protobuf file.
        """
        id = 0
        for array in self.yield_test():
            if client.stop_stream:
                self.logger.info("Stream closed")
                break
            if array is None:
                self.logger.info("Streaming round done")
                continue

            rows = array.shape[0]
            cols = array.shape[1]
            vals = array.flatten()
            client.messages_timestamps.update({id: [datetime.now()]})
            request = NumpyArray(values=vals, rows=rows, cols=cols, msg_id=id)
            id += 1
            yield request
