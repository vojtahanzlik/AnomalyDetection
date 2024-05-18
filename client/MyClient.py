from datetime import datetime
from time import sleep
from typing import Iterator
from flask_socketio import SocketIO
import numpy as np
from client import ClientBase
from messages_pb2 import NumpyArray
from opc_ua_client import main
from client import messages_timestamps


class MyClient(ClientBase):

    def __init__(self, socket: SocketIO):
        super().__init__(socket)
        self.data_point_interval = 0.004

    def yield_test(self):
        prev_last_timestamp = 0
        for i in range(0, 8):
            data = np.load(f"test_samples/samples{i}.npy")
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

    def _stream_messages(self) -> Iterator[NumpyArray]:
        id = 0
        for array in main():
            if self.stop_stream:
                break
            if array is None:
                self.logger.info("Streaming round done")
                continue

            rows = array.shape[0]
            cols = array.shape[1]
            vals = array.flatten()

            messages_timestamps.update({id: [datetime.now()]})
            request = NumpyArray(values=vals, rows=rows, cols=cols, msg_id=id)
            id += 1
            yield request
