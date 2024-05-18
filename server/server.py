import csv
import pickle

from concurrent import futures
from datetime import datetime
from typing import List
from multiprocessing.pool import ThreadPool
import grpc
import numpy as np
from Classifier import ClassifierFactory
from helpers import get_logger
from messages_pb2 import AnomalyDetResponse
from messages_pb2_grpc import AnomalyDetectionServiceServicer, add_AnomalyDetectionServiceServicer_to_server
from mqtt_publisher import publish_data, mqtt_connect

pool = ThreadPool(processes=2)


def rpc_request_arr_to_np_arr(request):
    rows = request.rows
    cols = request.cols
    values = list(request.values)
    return np.array(values).reshape((rows, cols))


class AnomalyDetectionServer(AnomalyDetectionServiceServicer):
    def __init__(self, address: str = '0.0.0.0:8061'):
        self.address = address
        self.logger = get_logger(self.__class__.__name__)

        self.my_classifier = ClassifierFactory.load_classifier("models/DEVIATION_MODEL_TEST.pkl")

        self.num_of_features = 6
        self.num_of_input_rows = 8
        self.identifier_idx = 6
        self.timestamp_idx = 7

        self.publisher = mqtt_connect()

        self.prev_pred_input = None
        self.curr_num_of_segments = 0
        self.results = []

    def StreamData(self, request_iterator, context):
        self.logger.info("Received SendNumpyArray stream request")
        if not request_iterator:
            self.logger.error("Invalid request iterator")
            raise grpc.RpcError
        for request in request_iterator:
            msg_id = request.msg_id
            self.logger.info("Received SendNumpyArray request")
            array = rpc_request_arr_to_np_arr(request)
            self.logger.info("Request converted to np array")

            segments_lst = self.get_non_zero_segments(array)

            if len(segments_lst) != 0:
                for pred in self._process_non_zero_segments(segments_lst, msg_id):
                    yield pred

        self.prev_pred_input = None
        self.logger.info("STREAMING DONE")
        with open(f"results{self.my_classifier.__class__.__name__}_{self.address}.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["id", "duration", "pred", "arr_len"])
            for record in self.results:
                duration = record[1]
                res = record[2]
                arr_len = record[3]
                writer.writerow([record[0], duration, res, arr_len])

    def _process_non_zero_segments(self, non_zero_segments, msg_id):
        for segment in non_zero_segments:
            arr_identifier = int(np.max(segment[self.identifier_idx]))
            if self.prev_pred_input is None:
                curr_pred_input = segment
                self.curr_num_of_segments = 1
                self.prev_pred_input = curr_pred_input

            elif int(np.max(self.prev_pred_input[self.identifier_idx])) == arr_identifier:

                curr_pred_input = np.hstack((self.prev_pred_input, segment))

                self.curr_num_of_segments += 1
                self.prev_pred_input = curr_pred_input

            else:  # last segment of current identifier
                curr_pred_input = segment
                self.curr_num_of_segments = 1
                self.prev_pred_input = None


            res = self._attempt_prediction(curr_pred_input, arr_identifier, msg_id)
            yield res

    def _attempt_prediction(self, input_arr, arr_id: int, msg_id: int):
        arr_to_predict, timestamp_row = self._prep_arr_for_prediction(input_arr)
        arr_len = arr_to_predict.shape[0]

        start = datetime.now()
        try:
            res = self.my_classifier.predict(arr_to_predict)
        except Exception as e:
            print(e)
            print(arr_id)
            print(np.shape(arr_to_predict))
            print(np.shape(self.prev_pred_input))
            res = None

        stop = datetime.now()

        if res is not None:
            duration = stop - start

            duration = duration.total_seconds() * 1000
            self.logger.info(f"Prediction done in {duration} ms")
            self.results.append([arr_id, duration, res, arr_len])
            self.logger.info(f"Send SendNumpyArray response: result: {res}, id: {arr_id}"
                             f", time series length: {arr_len}")
            if self.curr_num_of_segments >= 3:
                pool.apply_async(publish_data, (self.publisher, arr_to_predict, res, arr_id, timestamp_row))
                self.curr_num_of_segments = 0
            return AnomalyDetResponse(id=arr_id, result=res, series_len=arr_len, msg_id=msg_id)

    def _prep_arr_for_prediction(self, arr):
        timestamp_row = arr[self.timestamp_idx, :]
        arr = np.delete(arr, self.identifier_idx, axis=0)
        arr = np.delete(arr, self.timestamp_idx - 1, axis=0)
        return arr.T, timestamp_row

    def get_non_zero_segments(self, array) -> List[tuple]:
        ids = self._extract_identifiers(array)
        if ids.size == 0:
            return []
        return self._split_by_ids(array, ids)

    def _split_by_ids(self, array, ids) -> list:
        ret = []

        for i in ids:
            non_zero_id_series = self._extract_non_zero_id_series(array, i)
            if len(non_zero_id_series) != 0:
                ret.append(non_zero_id_series)

        return ret

    def _extract_identifiers(self, array):
        identifier_arr = array[self.identifier_idx]
        self.logger.info("Extracted identifier array")
        unique_ids = np.unique(identifier_arr[identifier_arr != 0])
        return unique_ids

    def _extract_non_zero_id_series(self, data, id):
        non_zero_idxs = np.where(data[self.identifier_idx, :] == id)[0]
        if len(non_zero_idxs) == 0:
            return []
        start = non_zero_idxs[0]
        end = non_zero_idxs[-1]
        sliced_data = data[:, start:end + 1]
        return sliced_data

    def _append_to_time_series(self, array, time_series):
        return np.concatenate((time_series, array), axis=1)

    def serve(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=3))
        add_AnomalyDetectionServiceServicer_to_server(self, server)
        server.add_insecure_port(self.address)
        server.start()
        self.logger.info("GRPC server started")
        server.wait_for_termination()
        self.logger.info("GRPC server shut down successfully")
