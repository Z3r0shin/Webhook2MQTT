from flask import Flask, request, Response
import threading
import logging
import paho.mqtt.client as mqtt
import json
import datetime
import os

# -------------Output Logger
# create logger
logger = logging.getLogger("Webhook2MQTT")
logger.setLevel(logging.INFO)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
# -------------Output Logger

mqtt_host = os.getenv("MQTT_HOST", "192.168.0.136")

mqtt_port = os.getenv("MQTT_PORT", "1883")

mqtt_path = os.getenv("MQTT_PATH", "webhook")

mqtt_user = os.getenv("MQTT_USER")

mqtt_pass = os.getenv("MQTT_PASS")

logger.info(f"Configured mqtt host {mqtt_host} with port {mqtt_port} ")

app = Flask(__name__)


def workit(params):
    logger.info("Executing Worker:")
    logger.info(params)
    params["timestamp"] = datetime.datetime.now().isoformat()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    # Set user/pass if set
    if mqtt_user and mqtt_pass:
        logger.debug(f"MQTT user and pass set, enabling authentication")
        client.username_pw_set(mqtt_user, mqtt_pass)
    client.connect(mqtt_server, int(mqtt_port), 60)
    client.publish(mqtt_path, json.dumps(params), qos=2, retain=True)
    client.disconnect()


@app.route("/", methods=["POST"])
def respond():
    logger.debug(request.headers)
    myparams = request.get_json()
    x = threading.Thread(target=workit, args=(myparams,))
    x.start()
    return Response(status=200)


if __name__ == "__main__":

    bind_host = os.getenv("BIND_HOST", "127.0.0.1")
    bind_port = os.getenv("BIND_PORT", 5050)
    app.run(host=bind_host, port=bind_port)

logger.info(f"MQTT Config: Host={mqtt_host}, Port={mqtt_port}, Path={mqtt_path}, User={mqtt_user}")
