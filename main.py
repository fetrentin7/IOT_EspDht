import network
import time
import dht
from machine import Pin
from umqtt.simple import MQTTClient

SSID = "YOUR_SSID"
PASSWORD = "YOUR_PASSWORD"

BROKERS = ["broker.hivemq.com", "test.mosquitto.org"]
PORT = 1883

TOPIC_TEMP = b"mestrado/iot/aluno/fernando_trentin/temperatura"
TOPIC_HUM = b"mestrado/iot/aluno/fernando_trentin/umidade"

# DHT11 connected to D5 (GPIO14) on the ESP8266
sensor = dht.DHT11(Pin(14))

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

# One MQTT client per broker
clients = [
    MQTTClient(client_id=b"esp_fernando", server=b, port=PORT)
    for b in BROKERS
]
connected = [False] * len(BROKERS)


def connect_wifi():
    if not wifi.isconnected():
        print("Connecting to Wi-Fi...")
        wifi.connect(SSID, PASSWORD)
        while not wifi.isconnected():
            time.sleep(0.5)
        print("Wi-Fi connected!")


def connect_mqtt(i):
    try:
        clients[i].connect()
        print("MQTT connected:", BROKERS[i])
        return True
    except OSError as error:
        print("MQTT failed", BROKERS[i], error)
        return False


connect_wifi()

while True:
    connect_wifi()   # does nothing if already connected

    # Sensor reading (an error here doesn't drop the connection)
    try:
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
    except OSError as error:
        print("Sensor error:", error)
        time.sleep(10)
        continue

    print("Temperature:", temperature)
    print("Humidity:", humidity)

    # Publish to each broker
    for i in range(len(BROKERS)):
        if not connected[i]:
            connected[i] = connect_mqtt(i)
        if connected[i]:
            try:
                clients[i].publish(TOPIC_TEMP, str(temperature))
                clients[i].publish(TOPIC_HUM, str(humidity))
                print("Published to", BROKERS[i])
            except OSError as error:
                print("Lost connection to", BROKERS[i], error)
                connected[i] = False   # reconnect on the next cycle

    time.sleep(10)