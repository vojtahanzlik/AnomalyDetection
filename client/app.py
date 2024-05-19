import threading

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from MyClient import MyClient
from mqtt_publisher import publish_data, mqtt_connect
from helpers import get_logger
from helpers import parse_args

app = Flask(__name__)
socketio = SocketIO(app)
publisher = mqtt_connect()
logger = get_logger("Web Server")


@app.route('/')
def index():
    return render_template('index.html')


def run_webserver(predictions, port: int):
    @socketio.on('connect')
    def test_connect():
        emit('update_predictions', list(predictions))
    port = port if port is not None else 5000
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)


@socketio.on('start_streaming')
def start_streaming(message):
    def stream():
        client.stream_data()

    logger.info("Start streaming event")
    threading.Thread(target=stream).start()


@socketio.on('stop_streaming')
def stop_streaming(message):
    client.stop_streaming()
    logger.info("Stop streaming event")


@socketio.on('wrong_prediction')
def handle_wrong_prediction(data):
    logger.info(f"Received wrong prediction signal for ID: {data['id']}")
    prediction_res = True if data['prediction_res'] == "true" else False
    publish_data(publisher, int(data['id']), prediction_res)


if __name__ == '__main__':
    args = parse_args()

    client = MyClient(socketio, save_res=args.save, address=args.address)
    run_webserver(client.predictions, args.port)
