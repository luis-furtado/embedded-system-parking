from threading import Thread
import socket
from time import sleep
import json
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
ENDERECO_01 = 22
ENDERECO_02 = 26
ENDERECO_03 = 19

# DEFAULTS PORTS
SENSOR_DE_VAGA = 18
SINAL_DE_LOTADO_FECHADO = 27
SENSOR_ABERTURA_CANCELA_ENTRADA = 23
SENSOR_FECHAMENTO_CANCELA_ENTRADA = 24
MOTOR_CANCELA_ENTRADA = 10
SENSOR_ABERTURA_CANCELA_SAIDA = 25
SENSOR_FECHAMENTO_CANCELA_SAIDA = 12
MOTOR_CANCELA_SAIDA = 17

def callbackAberturaCancelaEntrada(channel):
    GPIO.output(MOTOR_CANCELA_ENTRADA, GPIO.HIGH)
    payload = {"type": "IN", "id_floor": 1}
    sendMainServer(HOST_CENTRAL, PORT_CENTRAL, payload)

def callbackFechamentoCancelaEntrada(channel):
    GPIO.output(MOTOR_CANCELA_ENTRADA, GPIO.LOW)

def callbackAberturaCancelaSaida(channel):
    GPIO.output(MOTOR_CANCELA_SAIDA, GPIO.HIGH)
    payload = {"type": "OUT", "id_floor": 1}
    sendMainServer(HOST_CENTRAL, PORT_CENTRAL, payload)

def callbackFechamentoCancelaSaida(channel):
    GPIO.output(MOTOR_CANCELA_SAIDA, GPIO.LOW)

GPIO.setup(SENSOR_ABERTURA_CANCELA_ENTRADA, GPIO.IN)
GPIO.setup(SENSOR_FECHAMENTO_CANCELA_ENTRADA, GPIO.IN)
GPIO.setup(MOTOR_CANCELA_ENTRADA, GPIO.OUT)


# LISTENERS OF GPIO
GPIO.add_event_detect(
    SENSOR_ABERTURA_CANCELA_ENTRADA,
    GPIO.RISING,
    callback=callbackAberturaCancelaEntrada,
)
GPIO.add_event_detect(
    SENSOR_FECHAMENTO_CANCELA_ENTRADA,
    GPIO.FALLING,
    callback= callbackFechamentoCancelaEntrada,
)


GPIO.setup(ENDERECO_01, GPIO.OUT)
GPIO.setup(ENDERECO_02, GPIO.OUT)
GPIO.setup(ENDERECO_03, GPIO.OUT)
GPIO.setup(SENSOR_DE_VAGA, GPIO.IN)
GPIO.setup(SENSOR_ABERTURA_CANCELA_SAIDA, GPIO.IN)
GPIO.setup(SENSOR_FECHAMENTO_CANCELA_SAIDA, GPIO.IN)
GPIO.setup(MOTOR_CANCELA_SAIDA, GPIO.OUT)


# LISTENERS OF GPIO
GPIO.add_event_detect(
    SENSOR_ABERTURA_CANCELA_SAIDA,
    GPIO.RISING,
    callback=callbackAberturaCancelaSaida,
)
GPIO.add_event_detect(
    SENSOR_FECHAMENTO_CANCELA_SAIDA,
    GPIO.FALLING,
    callback=callbackFechamentoCancelaSaida,
)

spaces = [0, 0, 0, 0, 0, 0, 0, 0]

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
    payload = {"type": "spaces", "id_floor": 1, "spaces": spaces}
    sendMainServer(HOST_CENTRAL, PORT_CENTRAL, payload)
    sleep(0.8)

def sensors():
    while True:
        sendSpacesToMain()

def server():

    # CONFIGURE SOCKET
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (HOST_FIRST_FLOOR, PORT_FIRST_FLOOR)
    GPIO.setup(SINAL_DE_LOTADO_FECHADO, GPIO.OUT)
    sock.bind(server_address)
    sock.listen(1)

    while True:
        connection, client_address = sock.accept()
        data = connection.recv(2048).decode("utf8")
        if data:
            dataJson = json.loads(data)
            if dataJson["isFull"]:
                GPIO.output(SINAL_DE_LOTADO_FECHADO, GPIO.HIGH)
            else:
                GPIO.output(SINAL_DE_LOTADO_FECHADO, GPIO.LOW) 
            
            connection.send("Recebido".encode("utf8"))
            connection.close()



def sendMainServer(host, port, data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)
    is_connected = False

    try:
        while not is_connected:
            sock.connect(server_address)
            is_connected = True
    except socket.error as e:
        print("Socket connect error: %s" % str(e))
        sleep(1)

    try:
        dataJson = json.dumps(data)
        sock.sendall(dataJson.encode("utf8"))
        received = sock.recv(2048)
    except socket.error as e:
        print("Erro no socket: %s" % str(e))
        sleep(1)
    except Exception as e:
        print("Excessão não tratada. Detalhes:: %s" % str(e))
    finally:
        print("Fechando conexão com o servidor")
        sock.close()


sensorThread = Thread(target=sensors)
sensorThread.daemon = True
sensorThread.start()
sensorThread.join()

serverThread = Thread(target=server)
serverThread.daemon = True
serverThread.start()
serverThread.join()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("Ctrl+c")
