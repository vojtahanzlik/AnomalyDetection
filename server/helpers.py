import argparse
import logging
import sys
import threading
from collections import deque

import numpy as np


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
                        help='Address of the grpc server of format ip:port, default localhost')

    parser.add_argument('--model', type=str, nargs='?',
                        help='Name of a ml model located in the models folder, including file ext')
    args = parser.parse_args()
    return args


class UniqueQueue:

    def __init__(self):
        self.set = set()
        self.queue = deque()

    def enqueue(self, value):
        ret = False
        if value not in self.set:
            self.set.add(value)
            self.queue.append(value)
            ret = True
        return ret

    def dequeue(self):
        if len(self.queue) > 0:
            value = self.queue.popleft()
            self.set.remove(value)
            return value

    def peak(self):
        if len(self.queue) > 0:
            return self.queue[0]
        return -1

    def __len__(self):

        return len(self.queue)
