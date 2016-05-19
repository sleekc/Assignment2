#!/usr/bin/env python3

# Send Grove sensor data periodically to AWS IoT.

import time
import datetime
import ssl
import json
import paho.mqtt.client as mqtt
import grovepi

# TODO: Name of our Raspberry Pi, also known as our "Thing Name"
deviceName = "g48pi"
# TODO: Public certificate of our Raspberry Pi, as provided by AWS IoT.
deviceCertificate = "tp-iot-certificate.pem.crt"
# TODO: Private key of our Raspberry Pi, as provided by AWS IoT.
devicePrivateKey = "tp-iot-private.pem.key"
# Root certificate to authenticate AWS IoT when we connect to their server.
awsCert = "aws-iot-rootCA.crt"
isConnected = False

# Assume we connected the Grove Light Sensor to analog port A0,
# Digital Humidity/Temperature Sensor (DHT11) to digital port D2,
# Sound Sensor to A2, Grove LED to digital port D4.
# If you are using the Grove Analog Temperature Sensor, connect it to analog port A1.
light_sensor = 0
sound_sensor = 2
dht_sensor = 2
led = 4
temp_sensor = 1


# This is the main logic of the program.  We connect to AWS IoT via MQTT, send sensor data periodically to AWS IoT,
# and handle any actuation commands received from AWS IoT.
def main():
    global isConnected
    # Create an MQTT client for connecting to AWS IoT via MQTT.
    client = mqtt.Client(deviceName + "_sr")  # Client ID must be unique because AWS will disconnect any duplicates.
    client.on_connect = on_connect  # When connected, call on_connect.
    client.on_message = on_message  # When message received, call on_message.
    client.on_log = on_log  # When logging debug messages, call on_log.

    # Set the certificates and private key for connecting to AWS IoT.  TLS 1.2 is mandatory for AWS IoT and is supported
    # only in Python 3.4 and later, compiled with OpenSSL 1.0.1 and later.
    client.tls_set(awsCert, deviceCertificate, devicePrivateKey, ssl.CERT_REQUIRED, ssl.PROTOCOL_TLSv1_2)

    # Connect to AWS IoT server.  Use AWS command line "aws iot describe-endpoint" to get the address.
    print("Connecting to AWS IoT...")
    client.connect("A1P01IYM2DOZA0.iot.us-west-2.amazonaws.com", 8883, 60)

    # Start a background thread to process the MQTT network commands concurrently, including auto-reconnection.
    client.loop_start()

    # Configure the Grove LED port for output.
    grovepi.pinMode(led, "OUTPUT")
    time.sleep(1)

    # Loop forever.
    while True:
        try:
            # If we are not connected yet to AWS IoT, wait 1 second and try again.
            if not isConnected:
                time.sleep(1)
                continue
            temp = grovepi.dht(dht_sensor, 0)[0]
            t = float(temp)
            # h = str(hum)

            if t <= 27:

                # Read Grove sensor values. Prepare our sensor data in JSON format.
                payload = {
                    "state": {
                        "reported": {
                            # Uncomment the next line if you're using the Grove Analog Temperature Sensor.
                            # "temperature": round(grovepi.temp(temp_sensor, '1.1'), 1),
                            # Comment out the next 2 lines if you're using the Grove Analog Temperature Sensor.
                            "temperature": grovepi.dht(dht_sensor, 0)[0],
                            # The first 0 means that the DHT module is DHT11.
                            "humidity": grovepi.dht(dht_sensor, 0)[1],
                            "light_level": grovepi.analogRead(light_sensor),
                            "sound_level": grovepi.analogRead(sound_sensor),
                            "timestamp": datetime.datetime.now().isoformat(),
                            "message": "OK"
                        }
                    }
                }

            elif t > 28:

                payload = {
                    "state": {
                        "reported": {
                            # Uncomment the next line if you're using the Grove Analog Temperature Sensor.
                            # "temperature": round(grovepi.temp(temp_sensor, '1.1'), 1),
                            # Comment out the next 2 lines if you're using the Grove Analog Temperature Sensor.
                            "temperature": grovepi.dht(dht_sensor, 0)[0],
                            # The first 0 means that the DHT module is DHT11.
                            "humidity": grovepi.dht(dht_sensor, 0)[1],
                            "light_level": grovepi.analogRead(light_sensor),
                            "sound_level": grovepi.analogRead(sound_sensor),
                            "timestamp": datetime.datetime.now().isoformat(),
                            "message": "Too hot!"
                        }
                    }
                }

            else:

                payload = {
                    "state": {
                        "reported": {
                            # Uncomment the next line if you're using the Grove Analog Temperature Sensor.
                            # "temperature": round(grovepi.temp(temp_sensor, '1.1'), 1),
                            # Comment out the next 2 lines if you're using the Grove Analog Temperature Sensor.
                            "temperature": grovepi.dht(dht_sensor, 0)[0],
                            # The first 0 means that the DHT module is DHT11.
                            "humidity": grovepi.dht(dht_sensor, 0)[1],
                            "light_level": grovepi.analogRead(light_sensor),
                            "sound_level": grovepi.analogRead(sound_sensor),
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    }
                }

            print("Sending sensor data to AWS IoT...\n" +
                  json.dumps(payload, indent=4, separators=(',', ': ')))

            # Publish our sensor data to AWS IoT via the MQTT topic, also known as updating our "Thing Shadow".
            client.publish("$aws/things/" + deviceName + "/shadow/update", json.dumps(payload))
            print("Sent to AWS IoT")

            # Wait 30 seconds before sending the next set of sensor data.
            time.sleep(30)

        except KeyboardInterrupt:
            break
        except IOError:
            print("Error")


# This is called when we are connected to AWS IoT via MQTT.
# We subscribe for notifications of desired state updates.
def on_connect(client, userdata, flags, rc):
    global isConnected
    isConnected = True
    print("Connected to AWS IoT")
    # Subscribe to our MQTT topic so that we will receive notifications of updates.
    topic = "$aws/things/" + deviceName + "/shadow/update/accepted"
    print("Subscribing to MQTT topic " + topic)
    client.subscribe(topic)


# This is called when we receive a subscription notification from AWS IoT.
def on_message(client, userdata, msg):
    # Convert the JSON payload to a Python dictionary.
    # The payload is in binary format so we need to decode as UTF-8.
    payload2 = json.loads(msg.payload.decode("utf-8"))
    print("Received message, topic: " + msg.topic + ", payload:\n" +
          json.dumps(payload2, indent=4, separators=(',', ': ')))


# Print out log messages for tracing.
def on_log(client, userdata, level, buf):
    print("Log: " + buf)


# Start the main program.
main()
