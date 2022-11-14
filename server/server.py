import socket
import threading
from Member import Member
from Room import Room

class ServerMMS:


    def __init__(self, hostIp, port):
        self.host = hostIp
        self.port = port
        
        self.serverList = {}

        self.isListening = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))

    def start_server_thread(self):

        print(f"Starting Server at {self.host}:{self.port}")

        commad_handling_thread = threading.Thread(target=self.command_handling, args=())
        commad_handling_thread.start()

        # Starts Server
        self.server.listen()

        self.listen()


    # Sending Messages To All Connected Clients
    def broadcast(self,member: Member, message):
        self.serverList[member.serverId].broadcast_to_room(member.nick, message)

    def message(self, client, message:str):
        client.send(message.encode('ascii'))

    # Handling Messages From Clients
    def handle_messages(self, member: Member):
        while member.isConnected:
            try:
                # Broadcasting Messages
                message = member.client.recv(1024).decode('ascii')

                if(message == "!leave"):
                    self.leaveRoutine(member)
                elif(message == "!list"):
                    self.message(member.client, self.getServerList())
                else:
                    self.broadcast(member, message)
            except:
                # Print And Broadcast Nickname
                self.leaveRoutine(member)
                break   

    def leaveRoutine(self, member:Member):
        print(f"{member.nick} left room '{member.serverId}'")
        self.broadcast(member, f"{member.nick} has left!")

        # Removing And Closing Clients
        self.serverList[member.serverId].removeMember(member)
        member.client.close()

        if(self.serverList[member.serverId].roomcount == 0):
            self.serverList.pop(member.serverId)
        
        member.isConnected = False
        self.disconnectRoutine(member)
    
    def new_connect_handle(self, client, receivedMessage:str, address):
        messageList = receivedMessage.split(" ", 1)
        if(messageList[0] == "room"):
            roomId, nickname = self.getIdAndNickname(messageList[1])

            newMember =  Member(client, nickname, roomId, address)

            self.addNewUser(newMember)
            
            self.handle_messages(newMember)
            
        elif(messageList[0] == "list"):
            self.message(client, self.getServerList()) 
            client.close()
        elif(messageList[0] == "audioroom"):
            roomId, nickname, udpPort = self.getIdAndNicknameAndUDPPort(messageList[1])

            newMember =  Member(client, nickname, roomId, address, udpPort=int(udpPort))
            self.addNewUser(newMember, isAudioRoom=True)
            self.message(newMember.client, str(self.serverList[newMember.serverId].portNum))

            # From Here On The Room Object Handles Audio Transmission And The App Messages
            self.handle_messages(newMember)

    # Receiving / Listening Function
    def listen(self):
        while self.isListening:
            # Accept Connection
            client, address = self.server.accept()
            print(f"Connected with {address}")

            receivedMessage = client.recv(1024).decode('ascii')

            thread = threading.Thread(target=self.new_connect_handle, args=(client, receivedMessage,address))
            thread.start()
            


    def addNewUser(self, newMember: Member, isAudioRoom=False): # Bug: What if a join is done on an audioroom?
        if(newMember.serverId not in self.serverList):
             self.serverList[newMember.serverId] = Room(newMember, isAudioRoom)
        else:
            self.serverList[newMember.serverId].addMember(newMember)

        self.message(newMember.client, f"connected {newMember.serverId}")

        # Print And Broadcast Nickname
        print(f"{newMember.nick} joined room '{newMember.serverId}'")

        self.broadcast(newMember, f"{newMember.nick} joined! Say hello.")


    def getIdAndNickname(self, message: str):
        splitMsg = message.split(" ", 1)
        return splitMsg[0], splitMsg[1]

    def getIdAndNicknameAndUDPPort(self, message: str):
        splitMsg = message.split(" ", 2)
        return splitMsg[0], splitMsg[1], splitMsg[2]

    def getServerList(self):

        if(len(self.serverList) > 0):
            sList = "Room List:"

            for key, room in self.serverList.items():
                roomType = "AudioRoom" if room.isAudioRoom else "TextRoom"

                sList += f"\n{key} | {roomType} -> {room.roomcount} users"
            
            return sList
        else:
            return "No rooms!"
            
    def disconnectRoutine(self, member:Member):
        print(f"Disconnected {member.nick} with {member.address}")

    # Get Server Input
    def command_handling(self):
        while True:
            try:
                userInput = input("")
                print(userInput)
            except:
                exit()

