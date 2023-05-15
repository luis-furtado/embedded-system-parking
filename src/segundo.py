from threading import Thread
import socket
import json
from time import sleep, time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# DEFINE HOSTS
HOST_CENTRAL = "localhost"
HOST_FIRST_FLOOR = "localhost"
HOST_SECOND_FLOOR = "localhost"

# DEFINE PORTS, BASED ON REGISTRATION: 180042661
PORT_CENTRAL = 10344
PORT_FIRST_FLOOR = 10345
PORT_SECOND_FLOOR = 10346

# ADDRESSES
ENDERECO_01 = 13
ENDERECO_02 = 6
ENDERECO_03 = 5

SENSOR_DE_VAGA = 20
SINAL_DE_LOTADO_FECHADO = 8

SENSOR_DE_PASSAGEM_1 = 16
SENSOR_DE_PASSAGEM_2 = 21

spaces = [0, 0, 0, 0, 0, 0, 0, 0]
tempo_do_sensor_1 = 0
tempo_do_sensor_2 = 0

def callbackPassageSensor( channel):
    global tempo_do_sensor_1, tempo_do_sensor_2

    if channel == SENSOR_DE_PASSAGEM_1:
        tempo_do_sensor_1 = time()
    elif channel == SENSOR_DE_PASSAGEM_2:
        tempo_do_sensor_2 = time()

    if tempo_do_sensor_1 != 0 and tempo_do_sensor_2 != 0:
        if tempo_do_sensor_1 < tempo_do_sensor_2:
            print("Veículo subiu")
            data_to_send = {"type": "IN", "id_floor": 2}
            sendMainServer(HOST_CENTRAL, PORT_CENTRAL, data_to_send)
        else:
            print("Veículo desceu")
            data_to_send = {"type": "OUT", "id_floor": 2}
            sendMainServer(HOST_CENTRAL, PORT_CENTRAL, data_to_send)

        tempo_do_sensor_1 = 0
        tempo_do_sensor_2 = 0

GPIO.setup(SENSOR_DE_PASSAGEM_1, GPIO.IN)
GPIO.setup(SENSOR_DE_PASSAGEM_2, GPIO.IN)

# LISTENERS OF GPIO
GPIO.add_event_detect(
    SENSOR_DE_PASSAGEM_1,
    GPIO.RISING,
    callback=callbackPassageSensor,
)
GPIO.add_event_detect(
    SENSOR_DE_PASSAGEM_2,
    GPIO.RISING,
    callback=callbackPassageSensor,
)

# SETUP GPIO OUT IN RESPECTIVE ADDRESSES    
GPIO.setup(ENDERECO_01, GPIO.OUT)
GPIO.setup(ENDERECO_02, GPIO.OUT)
GPIO.setup(ENDERECO_03, GPIO.OUT)
GPIO.setup(SENSOR_DE_VAGA, GPIO.IN)

def sensors():

    while True:
        sendSpacesToMain()

def readSpaces():
    global spaces

    for i in range(8):
        index = "{0:03b}".format(i)

        GPIO.output(ENDERECO_01, int(index[2]))
        GPIO.output(ENDERECO_02, int(index[1]))
        GPIO.output(ENDERECO_03, int(index[0]))

        sleep(0.05)

        spaces[i] = GPIO.input(SENSOR_DE_VAGA)

def sendSpacesToMain():
    readSpaces()
    payload = {"type": "spaces", "id_floor": 2, "spaces": spaces}
    sendMainServer(HOST_CENTRAL, PORT_CENTRAL, payload)
    sleep(0.8)

def sendMainServer(host, port, data):
    # CONFIGURE SOCKETS 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)
    is_connected = False

    try:
        while not is_connected:
            sock.connect(server_address)
            is_connected = True
    except socket.error as e:
        print("Erro do socket: %s" % str(e))
        sleep(1)

    try:
        dataJson = json.dumps(data)
        sock.sendall(dataJson.encode("utf8"))
        received = sock.recv(2048)
    except socket.error as e:
        print("Erro do socket: %s" % str(e))
        sleep(1)
    except Exception as e:
        print("Excessão não tratada: %s" % str(e))
    finally:
        print("Conexão com o servidor encerrada")
        sock.close()

def server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (HOST_SECOND_FLOOR, PORT_SECOND_FLOOR)
    sock.bind(server_address)
    sock.listen(1)
    GPIO.setup(SINAL_DE_LOTADO_FECHADO, GPIO.OUT)

    while True:
        connection, client_address = sock.accept()
        data = connection.recv(2048)
        if data:
            dataJson = json.loads(data)
            if dataJson["isFull"]:
                GPIO.output(SINAL_DE_LOTADO_FECHADO, GPIO.HIGH)
            else:
                GPIO.output(SINAL_DE_LOTADO_FECHADO, GPIO.LOW) 

            connection.send("Recebido".encode("utf8"))
            connection.close()

sensorsThread = Thread(target=sensors)
sensorsThread.daemon = True
sensorsThread.start()
sensorsThread.join()

serverThread = Thread(target=server)
serverThread.daemon = True
serverThread.start()
serverThread.join()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("Ctrl+c")
