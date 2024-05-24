import os
from time import sleep

import grpc
from concurrent import futures

import logging

import numpy as np
from messages_pb2 import NumpyArray
from messages_pb2_grpc import DataBrokerService, add_DataBrokerServiceServicer_to_server

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
port = 8061


class DatabrokerServicer(DataBrokerService):

    def databroker(self, request, context):
        logger.debug("Connecting to databroker")

        directory = "test_samples"
        for file in os.listdir(directory):
            sleep(2)
            filename = os.fsdecode(file)
            data = np.load(f"{directory}/{filename}")
            selected_rows = data[4:11, :]

            split_arrays = np.array_split(selected_rows, 24, axis=1)
            for array in split_arrays:
                sleep(0.7)
                rows = array.shape[0]
                cols = array.shape[1]
                vals = array.flatten()
                response = NumpyArray(values=vals, rows=rows, cols=cols, id=0)
                logger.debug(response)
                yield response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_DataBrokerServiceServicer_to_server(DatabrokerServicer(), server)
    server.add_insecure_port('[::]:{}'.format(port))
    logger.debug("Start databroker server")
    server.start()
    server.wait_for_termination()
    logger.debug("Threads ended")


if __name__ == '__main__':
    logging.basicConfig()
    serve()
