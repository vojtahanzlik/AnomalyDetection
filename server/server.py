import pickle

from concurrent import futures
from typing import List
from multiprocessing.pool import ThreadPool
import grpc
import numpy as np
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
        with open("models/featureClassifier_2604.pkl", 'rb') as f:
            loaded_object = pickle.load(f)
            self.my_classifier = loaded_object
            self.logger.info(f"Loaded classifier: {self.my_classifier.__class__.__name__}")

        self.identifier_idx = 6
        self.input_rows_num = 7

        self.publisher = mqtt_connect()

    def StreamData(self, request_iterator, context):
        self.logger.info("Received SendNumpyArray stream request")
        if not request_iterator:
            self.logger.error("Invalid request iterator")
            raise grpc.RpcError

        for request in request_iterator:
            self.logger.info("Received SendNumpyArray request")
            array = rpc_request_arr_to_np_arr(request)
            self.logger.info("Request converted to np array")

            segments_lst = self.get_non_zero_segments(array)

            for pred in self._attempt_prediction(segments_lst):
                yield pred

        self.logger.info("STREAMING DONE")

    def _attempt_prediction(self, data_segments: List[tuple]):
        for segment in data_segments:
            arr_to_predict = self._prep_arr_for_prediction(segment[0])
            arr_identifier = segment[1]
            arr_len = arr_to_predict.shape[0]
            res = self.my_classifier.predict_partial_signal(arr_to_predict)
            if res is not None:
                yield AnomalyDetResponse(id=arr_identifier, result=res, series_len=arr_len)
                self.logger.info(f"Send SendNumpyArray response: result: {res}, id: {arr_identifier}"
                                 f", time series length: {arr_len}")
                pool.apply_async(publish_data, (self.publisher, arr_to_predict, res, arr_identifier))

    def _prep_arr_for_prediction(self, arr):
        arr = np.delete(arr, self.identifier_idx, axis=0)
        return arr.T

    def get_non_zero_segments(self, array) -> List[tuple]:
        ids = self._extract_identifiers(array)
        if ids.size == 0:
            return []
        return self._split_by_ids(array, ids)

    def _split_by_ids(self, array, ids) -> List[tuple]:
        ret = []

        for i in ids:
            non_zero_id_series = self._extract_non_zero_id_series(array, i)
            if len(non_zero_id_series) != 0:
                ret.append((non_zero_id_series, int(i)))

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
        self.logger.info("Server started")
        server.wait_for_termination()
        self.logger.info("Server shut down successfully")
