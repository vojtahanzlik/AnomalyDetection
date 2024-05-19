import os
import sys
from server import AnomalyDetectionServer
from helpers import parse_args

if __name__ == '__main__':
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    args = parse_args()
    server = AnomalyDetectionServer(address=args.address, save_res=args.save, model=args.model)
    server.serve()
