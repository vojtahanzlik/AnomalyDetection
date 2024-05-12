import os
import sys

from server import AnomalyDetectionServer

if __name__ == '__main__':
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    server = AnomalyDetectionServer()
    server.serve()
