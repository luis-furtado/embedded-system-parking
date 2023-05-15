from time import sleep
from threading import Thread
import socket
import json
import os
import datetime

# DEFINE HOSTS
HOST_CENTRAL = "localhost"
HOST_FIRST_FLOOR = "localhost"
HOST_SECOND_FLOOR = "localhost"

# DEFINE PORTS, BASED ON REGISTRATION: 180042661
PORT_CENTRAL = 10344
PORT_FIRST_FLOOR = 10345
PORT_SECOND_FLOOR = 10346

# SPACES STORAGE
spaces = [[0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0]]
previousSpaces = [[0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0]]

# AMOUNT OF VEHICLES
amountOfVehicles = 0
firstFloorAmountOfVehicles = 0
secondFloorAmountOfVehicles = 0
totalAmount = 0

terminalCommand = False
isNotFull = True

vehicles = []
idVehicle = 0

def rmvVehicle():
        global vehicles
        global totalAmount
        global previousSpaces

        for i in range(8):

            if spaces[0][i] == 0 and previousSpaces[0][i] == 1:

                pos = i
                for j in range(len(vehicles)):

                    if vehicles[j][2] == pos and vehicles[j][3] == 1:
                        vehicle = vehicles.pop(j)
                        pay = int((datetime.datetime.now() - vehicle[1]).seconds / 60) * 0.15
                        totalAmount += pay
                        break

                previousSpaces[0] = spaces[0]
                break

        for i in range(8):

            if spaces[1][i] == 0 and previousSpaces[1][i] == 1:

                pos = i
                for j in range(len(vehicles)):
                    if vehicles[j][2] == pos and vehicles[j][3] == 2:
                        vehicle = vehicles.pop(j)
                        pay = int((datetime.datetime.now() - vehicle[1]).seconds / 60) * 0.15
                        totalAmount += pay
                        break

                previousSpaces[1] = spaces[1]
                break

def addVehicle():
    global vehicles
    global previousSpaces

    for i in range(8):

        if spaces[0][i] == 1 and previousSpaces[0][i] == 0:
            pos = i

            for j in range(len(vehicles)):
                if vehicles[j][0] == idVehicle:
                    vehicles[j][2] = pos
                    vehicles[j][3] = 1
                    break

            previousSpaces[0] = spaces[0]

            break

        if spaces[1][i] == 1 and previousSpaces[1][i] == 0:

            pos = i

            for j in range(len(vehicles)):
                if vehicles[j][0] == idVehicle:
                    vehicles[j][2] = pos
                    vehicles[j][3] = 2
                    break
            previousSpaces[1] = spaces[1]

            break

def verifyData(data):
    global amountOfVehicles
    global firstFloorAmountOfVehicles
    global secondFloorAmountOfVehicles
    global spaces
    global vehicles
    global idVehicle

    if data["type"] == "spaces":
        if data["id_floor"] == 1:
            spaces[0] = data["spaces"]
        else:
            spaces[1] = data["spaces"]

    elif data["type"] == "IN":
        if data["id_floor"] == 1:
            firstFloorAmountOfVehicles += 1
            idVehicle += 1
            vehicles.append([idVehicle, datetime.datetime.now(), -1, -1])
        else:
            secondFloorAmountOfVehicles += 1
            firstFloorAmountOfVehicles -= 1

    else:
        if data["id_floor"] == 1:
            firstFloorAmountOfVehicles -= 1
            rmvVehicle()  
        else: 
            secondFloorAmountOfVehicles -= 1
            firstFloorAmountOfVehicles += 1
    
    addVehicle()

def sendDataToClient(host, port, command):

    # CONFIGURE SOCKET 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)

    # WHILE NOT CONEECT, TRY CONNECT WITH OTHER SERVERS TO SEND DATA 
    connected = False
    while not connected:
        try:
            sock.connect(server_address)
            connected = True
        except:
            connected = False
            sleep(1)

    try:
        message = json.dumps(command)
        sock.sendall(message.encode("utf8"))

    except socket.error as e:
        print("Erro no socket. Detalhes: %s" % str(e))

    except Exception as e:
        print("Ocorreu uma excessão no sistema. Detalhes: %s" % str(e))

    finally:
        sock.close()

def checkParkingAvailability():
    global amountOfVehicles
    global isNotFull
    amountOfVehicles = firstFloorAmountOfVehicles + secondFloorAmountOfVehicles

    if secondFloorAmountOfVehicles == 8:
        sendDataToClient(HOST_SECOND_FLOOR, PORT_SECOND_FLOOR, {"isFull": 1})
        isNotFull = False
    if amountOfVehicles == 16:
        sendDataToClient(HOST_FIRST_FLOOR, PORT_FIRST_FLOOR, {"isFull": 1})
        isNotFull = False
    if secondFloorAmountOfVehicles < 8 and terminalCommand is False and isNotFull is False:
        sendDataToClient(HOST_SECOND_FLOOR, PORT_SECOND_FLOOR, {"isFull": 0})
        isNotFull = True
    if amountOfVehicles < 16 and terminalCommand is False and isNotFull is False:
        isNotFull = True
        sendDataToClient(HOST_FIRST_FLOOR, PORT_FIRST_FLOOR, {"isFull": 0})

def updateInterface():
    os.system("clear")
    
    print("Vagas do segundo andar: ", spaces[1])
    print("Vagas do primeiro andar: ", spaces[0])
    print("Quantidade total de carros no estacionamento: ", amountOfVehicles)
    print("Quantidade total de carros no primeiro andar: ", firstFloorAmountOfVehicles)
    print("Quantidade total de carros no segundo andar: ", secondFloorAmountOfVehicles)
    print("Valor total arrecadado: ", totalAmount)
    print("Comando: Digite (1) Para -> Fechar estacionamento")
    print("Comando: Digite (2) Para -> Fechar segundo andar")
    print("Comando: Digite (3) Para -> Abrir estacionamento")
    print("Comando: Digite (4) Para -> Abrir segundo andar")

def sendCommand():
    global terminalCommand

    while True:
        terminalInput = int(input())

        if terminalInput == 1:
            sendDataToClient(HOST_FIRST_FLOOR, PORT_FIRST_FLOOR, {"isFull": 1})
            terminalCommand = True
        elif terminalInput == 2:
            sendDataToClient(HOST_SECOND_FLOOR, PORT_SECOND_FLOOR, {"isFull": 1})
            terminalCommand = True
        elif terminalInput == 3:
            sendDataToClient(HOST_FIRST_FLOOR, PORT_FIRST_FLOOR, {"isFull": 0})
            terminalCommand = False
        elif terminalInput == 4:
            sendDataToClient(HOST_SECOND_FLOOR, PORT_SECOND_FLOOR, {"isFull": 0})
            terminalCommand = False
        else:
            pass
    

def startServer():
    global spaces

    # DEFINE PORT AND HOST
    port = PORT_CENTRAL
    host = HOST_CENTRAL

    # CONFIGURE SOCK OPTIONS AND START
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    data_payload = 2048
    address = (host, port)
    sock.bind(address)
    sock.listen(2)

    while True:
        updateInterface()
        checkParkingAvailability()

        client, address = sock.accept()
        data = client.recv(data_payload).decode("utf8")

        if data:
            data = json.loads(data)

            verifyData(data)    
           
            client.send("Received".encode("utf8"))


server = Thread(target=startServer)
server.daemon = True
server.start()

terminal = Thread(target=sendCommand)
terminal.daemon = True
terminal.start()

try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("Ctrl+c")