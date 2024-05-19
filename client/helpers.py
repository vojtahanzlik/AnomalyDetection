import argparse
import logging
import sys


def get_logger(name):
    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(name)s] [%(levelname)-5.5s]  %(message)s")
    root_logger = logging.getLogger(name)
    # file_handler = logging.FileHandler(f"{name}.log")
    # file_handler.setFormatter(log_formatter)
    # root_logger.addHandler(file_handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)
    return root_logger


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', type=bool, nargs='?',
                        help='Saves results to csv, default True')

    parser.add_argument('--address', type=str, nargs='?',
                        help='Address of the grpc server to connect to of format ip:port, default localhost')

    parser.add_argument('--port', type=int, nargs='?',
                        help='Port for the flask server to listen on, default 5000')

    args = parser.parse_args()
    return args
