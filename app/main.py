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
logger.setLevel(logging.DEBUG)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
# -------------Output Logger

# Environment variables
mqtt_host = os.getenv("MQTT_HOST", "127.0.0.1")
mqtt_port = os.getenv("MQTT_PORT", "1883")
mqtt_path = os.getenv("MQTT_PATH", "webhook")
mqtt_user = os.getenv("MQTT_USER")
mqtt_pass = os.getenv("MQTT_PASS")

logger.info(f"Configured MQTT host: {mqtt_host}, Port: {mqtt_port}, Path: {mqtt_path}, User: {mqtt_user}")

app = Flask(__name__)

def workit(params):
    try:
        logger.info("Executing Worker:")
        logger.info(f"Received params: {params}")

        # Add timestamp
        params["timestamp"] = datetime.datetime.now().isoformat()

        # Initialize MQTT client
        logger.info("Initializing MQTT client")
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Webhook2MQTT")

        # Set username/password if provided
        if mqtt_user and mqtt_pass:
            logger.info(f"Setting MQTT username ({mqtt_user}) and password ({mqtt_pass})")
            client.username_pw_set(mqtt_user, mqtt_pass)

        # Connect to the broker
        logger.info(f"Connecting to MQTT broker at {mqtt_host}:{mqtt_port}")
        client.connect(mqtt_host, int(mqtt_port), 60)

        # Initialize message_info to prevent scope issues
        message_info = None

        # Publish message
        logger.info(f"Publishing to topic {mqtt_path}")
        try:
            message_info = client.publish(mqtt_path, json.dumps(params), qos=1, retain=True)
        except Exception as publish_error:
            logger.error(f"Error while publishing message: {publish_error}")
            
        if message_info == mqtt.MQTT_ERR_SUCCESS:
            logger.info("Message queued successfully")
        elif message_info:
            logger.error(f"Message failed with return code: {message_info.rc}")
        logger.info("Message published successfully")
        
        # Disconnect
        logger.info("Disconnecting MQTT client")
        client.disconnect()
        
    except Exception as e:
        logger.error(f"Error in workit: {e}")

@app.route("/", methods=["POST"])
def respond():
    try:
        logger.info("Received POST request")
        logger.debug(f"Headers: {request.headers}")

        # Parse JSON payload
        myparams = request.get_json()
        if not myparams:
            logger.warning("Empty or invalid JSON payload received")
            return Response("Invalid JSON payload", status=400)

        # Start worker thread
        x = threading.Thread(target=workit, args=(myparams,))
        x.start()
        return Response(status=200)
    except Exception as e:
        logger.error(f"Error in respond: {e}")
        return Response("Internal Server Error", status=500)

if __name__ == "__main__":
    bind_host = os.getenv("BIND_HOST", "0.0.0.0")  # Bind to all interfaces
    bind_port = os.getenv("BIND_PORT", "1357")
    logger.info(f"Starting Flask server on {bind_host}:{bind_port}")
    app.run(host=bind_host, port=int(bind_port))
