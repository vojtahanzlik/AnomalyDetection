import csv

from concurrent import futures
from datetime import datetime
from multiprocessing.pool import ThreadPool
import grpc
import numpy as np
from Classifier import ClassifierFactory
from helpers import get_logger
from messages_pb2 import AnomalyDetResponse
from messages_pb2_grpc import AnomalyDetectionServiceServicer, add_AnomalyDetectionServiceServicer_to_server

pool = ThreadPool(processes=2)


def rpc_request_arr_to_np_arr(request) -> np.ndarray:
    """
    Converts the gRPC request data to a numpy array.

    Args:
        request: The gRPC request containing array data.

    Returns:
        np.ndarray: The converted numpy array.
    """
    rows = request.rows
    cols = request.cols
    values = list(request.values)
    return np.array(values).reshape((rows, cols))


def add_to_buffer(buffer: dict, arr: np.ndarray, uid: int) -> bool:
    """
    Adds data to the buffer for a specific UID.

    Args:
        buffer (dict): The buffer dictionary.
        arr (np.ndarray): The array to add to the buffer.
        uid (int): The unique identifier.

    Returns:
        bool: True if the array was added, False otherwise.
    """
    buffer_arr = buffer[uid][0]
    if buffer_arr.shape[0] == arr.shape[0]:
        buffer[uid][0] = np.hstack((buffer_arr, arr))
        return True
    return False


class AnomalyDetectionServer(AnomalyDetectionServiceServicer):
    """
        gRPC server for anomaly detection service.

        Attributes:
            address (str): The address of the server.
            logger: Logger instance.
            my_classifier (ClassifierBase): The classifier used for anomaly detection.
            num_of_features (int): Number of features in the input array.
            num_of_input_rows (int): Number of rows in the input array.
            identifier_idx (int): Index of the identifier in the input array.
            timestamp_idx (int): Index of the timestamp in the input array.
            publisher (mqtt.Client): MQTT client instance.
            results (list): List of results.
        """
    def __init__(self, address: str = '0.0.0.0:8061', save_res: bool = False, model: str = "FEATURE.pkl"):
        self.address = address if address is not None else '0.0.0.0:8061'
        self.logger = get_logger(self.__class__.__name__)
        self.save_res = save_res if save_res is not None else True
        model = model if model is not None else "FEATURE.pkl"
        self.my_classifier = ClassifierFactory.load_classifier(f"models/{model}")

        self.num_of_features = 6
        self.num_of_input_rows = 8
        self.identifier_idx = 6
        self.timestamp_idx = 7

        self.results = []

    def StreamData(self, request_iterator, context):
        """
        Streams data from the client, processes it, and sends responses.

        Args:
            request_iterator: Iterator for the incoming requests.
            context: The gRPC context.

        Returns:
            Iterator[AnomalyDetResponse]: The responses containing anomaly detection results.
        """
        self.logger.info("Stream initiated")
        if not request_iterator:
            self.logger.error("Invalid request iterator")
            raise grpc.RpcError

        buffer = dict()
        current_ids = set()

        for request in request_iterator:
            for response in self.process_request(request, buffer, current_ids):
                yield response

        self.finalize_buffers(current_ids)
        if self.save_res:
            self.write_results_to_csv()
        self.results = []

    def process_request(self, request, buffer: dict, current_ids: set):
        """
        Processes each request, updating the buffer and yielding responses.

        Args:
            request: The incoming request.
            buffer: The buffer dictionary storing data arrays.
            current_ids: Set of current unique identifiers.
        """
        start = datetime.now()
        msg_id = request.msg_id
        self.logger.info("Received request")
        array = rpc_request_arr_to_np_arr(request)
        identifiers = array[self.identifier_idx]
        unique_ids = np.unique(identifiers)

        for uid in unique_ids:
            if uid == 0:
                continue
            response = self.process_unique_id(uid, identifiers, array, buffer, current_ids, msg_id)
            stop = datetime.now()
            duration = stop - start
            duration = duration.total_seconds() * 1000
            self.logger.info(f"Message processed in {duration} ms")
            if response:
                yield response
        self.handle_zero_identifiers(identifiers, buffer, current_ids)

    def process_unique_id(self, uid, identifiers: np.ndarray, array: np.ndarray,
                          buffer: dict, current_ids: set, msg_id: int):
        """
        Processes each unique identifier in the request updating the buffer and running prediction.

        Args:
            uid: The unique identifier.
            identifiers: Array of identifiers from the request.
            array: Data array from the request.
            buffer: The buffer dictionary storing data arrays.
            current_ids: Set of current unique identifiers.
            msg_id: The message ID of the request.
        """
        non_zero_indices = np.where(identifiers == uid)[0]
        uid = int(uid)
        if uid not in current_ids:
            if uid in buffer:
                add_to_buffer(buffer, array[:, non_zero_indices], uid)
            else:
                buffer[uid] = [array[:, non_zero_indices], None]
            current_ids.add(uid)
        else:
            add_to_buffer(buffer, array[:, non_zero_indices], uid)

        pred_res, arr_len = self._run_prediction(buffer[uid][0], uid)
        buffer[uid][1] = pred_res
        if pred_res is not None:
            self.logger.info(
                f"Send AnomalyDetResponse: result: {pred_res}, id: {uid}, time series length: {arr_len}")
            return AnomalyDetResponse(id=uid, result=pred_res, series_len=arr_len, msg_id=msg_id)

    def handle_zero_identifiers(self, identifiers: np.ndarray, buffer: dict, current_ids: set):
        """
        Handles cases where identifiers flip to zero, publishing data and clearing buffers.

        Args:
            identifiers: Array of identifiers from the request.
            buffer: The buffer dictionary storing data arrays.
            current_ids: Set of current unique identifiers.
        """
        zero_indices = np.where(identifiers == 0)[0]
        if zero_indices.size > 0:
            for uid in list(current_ids):
                non_zero_indices = np.where(identifiers == uid)[0]
                if non_zero_indices.size == 0:
                    timestamp_row = buffer[uid][0][self.timestamp_idx, :]
                    del buffer[uid]
                    current_ids.remove(uid)
                    self.logger.info(f"Buffer for identifier {uid} completed and cleared.")

    def finalize_buffers(self, current_ids: set):
        """
        Finalizes the buffers by logging completion for each identifier.

        Args:
            current_ids: Set of current unique identifiers.
        """
        for uid in current_ids:
            self.logger.info(f"Final buffer for identifier {uid} completed.")
        self.logger.info("STREAMING DONE")

    def write_results_to_csv(self):
        """
        Writes the results to a CSV file.
        """
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        safe_address = self.address.replace(':', '_')
        with open(
                f"results/results_{self.my_classifier.__class__.__name__}_{safe_address}_{timestamp}.csv", 'w', newline=''
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["id", "duration_ms", "pred", "arr_len"])
            for record in self.results:
                duration = record[1]
                res = record[2]
                arr_len = record[3]
                writer.writerow([record[0], duration, res, arr_len])
                file.flush()

    def _run_prediction(self, input_arr: np.ndarray, uid: int):
        """
        Prepares the input array for prediction, runs the prediction, and logs the results.

        Args:
            input_arr (np.ndarray): The input array for prediction.
            uid (int): The unique identifier for the current prediction.

        Returns:
            tuple: The prediction result and the length of the input array.
        """
        arr_to_predict = self._prep_arr_for_prediction(input_arr)
        arr_len = arr_to_predict.shape[0]

        try:
            start = datetime.now()
            res = self.my_classifier.predict(arr_to_predict)
            stop = datetime.now()
            duration = stop - start
            duration = duration.total_seconds() * 1000
            self.logger.info(f"Prediction done in {duration} ms")
            self.results.append([uid, duration, res, arr_len])
        except Exception as e:
            print(e)
            print(np.shape(arr_to_predict))
            res = None, arr_len

        if res is not None:
            return res, arr_len

    def _prep_arr_for_prediction(self, arr: np.ndarray):
        """
        Prepares the array for prediction by removing specific rows and transposing the array.

        Args:
            arr (np.ndarray): The input array to be prepared.

        Returns:
            np.ndarray: The prepared array.
        """
        arr = np.delete(arr, self.identifier_idx, axis=0)
        arr = np.delete(arr, self.timestamp_idx - 1, axis=0)
        return arr.T

    def serve(self):
        """
        Starts the gRPC server and waits for termination.

        The server listens for incoming connections and handles requests using the defined services.
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=3))
        add_AnomalyDetectionServiceServicer_to_server(self, server)
        server.add_insecure_port(self.address)
        server.start()
        self.logger.info(f"GRPC server started on address {self.address}")
        server.wait_for_termination()
        self.logger.info("GRPC server shut down successfully")
