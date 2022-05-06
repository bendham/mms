import socket
import threading

from config import ip, port
import configparser


class Client:

    def __init__(self):
        self.isConnected = False
        
        self.config = configparser.ConfigParser()
        self.config.read('client_config.ini')

        self.nickname = self.config['client-details']['name']
        self.roomId = self.config['client-details']['room_id']

        self.welcome()

        self.commandsBaisc = {"!help":"Lists these words", "!roomhelp":"Lists the commands only aplicable to a room", "!room":"lists the current room","!room newRoom":"Set the room you want to connect to. e.g. !room coolRoom","!list": "displays current rooms" , "!name":"prints your current nickname","!name newName":"set's your nickname",
                        "!join": "connects you to the setroom. Can also do e.g. !join aRoomOfMyChoice", "!room":"lists the current room", "!leave":"leaves the current room", "!quit": "Quits Matthew's Messaging Service"}

        self.commandsRoomCommands = { "!helproom":"Lists these words", "!members": "lists the current members in the room", "!count": "gives you the number of members for the current room", "!created": "when the room was created", "!whisper": "send direct message to member in room. e.g. !whisper freddy HI THERE", "!stats": "gives you the full shabang of stats!"}
    

    def connect(self, type="room"):

        if(not self.isConnected):
            self.isConnected = True

            # Connecting To Server
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((ip, port))

            
            if(type=="room"):
                self.disp_chat(f"\n---- In Room {self.roomId} ----\n")

                # Starting Threads For Receiving
                receive_thread = threading.Thread(target=self.receive)
                receive_thread.start()

                message = f"{type} {self.roomId} {self.nickname}"
                self.client.send(message.encode('ascii'))
            elif(type=="list"):
                
                 # Starting Threads For Receiving
                receive_thread = threading.Thread(target=self.receive_disconnect)
                receive_thread.start()

                self.client.send(type.encode('ascii'))
        else:
            self.disp("Already connected bruv chill!")

        
    def receive_disconnect(self):
        while self.isConnected:
            try:
                # Receive Message From Server
                message = self.client.recv(1024).decode('ascii')
                self.disp_chat(message)
                
                self.client.close()
                self.isConnected = False
            except:
                # Close Connection When Error
                self.client.close()
                break


    # Listening to Server and Sending Nickname
    def receive(self):
        while self.isConnected:
            try:
                # Receive Message From Server
                message = self.client.recv(1024).decode('ascii')
                self.disp_chat(message)
            except:
                # Close Connection When Error
                self.client.close()
                break

    # Sending Messages To Server
    def command_handling(self):
        while True:
            command_good = True
            
            try:
                userInput = input("")
                cmdList = userInput.split(" ")
                cmd = cmdList[0]

            except:
                cmd = -1
                exit()

            if(cmd in self.commandsBaisc.keys()):
                if(cmd == "!help"):
                    self.help(self.commandsBaisc)
                elif(cmd == "!roomhelp"):
                    self.help(self.commandsRoomCommands)
                elif(cmd == "!room"):
                    if(len(cmdList) == 1):
                        self.disp(f"'{self.roomId}' is your current selected room")
                    elif len(cmdList) == 2:
                        self.roomId = cmdList[1]
                        self.config.set("client-details", "room_id", self.roomId)
                        self.updateConfig()
                        self.disp(f"Room set to '{self.roomId}'") 
                    else:
                        command_good = False
                elif(cmd == "!join"):
                    self.connect()  
                elif(cmd == "!leave"):
                    if(self.isConnected):

                        self.client.send("!leave".encode('ascii'))
                        self.client.shutdown(socket.SHUT_RDWR)
                        self.isConnected = False

                        self.disp("You left")

                        self.welcome()
                    else:
                        self.disp("You are not even connected!")
                elif(cmd == "!quit"):

                    if(self.isConnected):
                        self.client.close()
                    
                    self.isConnected = False

                    self.disp("Bye, byte!")
                    exit()
                elif(cmd == "!name"):
                    if(len(cmdList) == 1):
                        self.disp(f"'{self.nickname}' is your current name")
                    elif len(cmdList) == 2:
                        self.nickname = cmdList[1]
                        self.config.set("client-details", "name", self.nickname)
                        self.updateConfig()
                        self.disp(f"Nickname set to '{self.nickname}'") 
                    else:
                        command_good = False   
                elif(cmd == "!list"):
                    self.connect("list")

                 
                else:
                    command_good = False

                if(not command_good):
                    self.disp("Error with that command!")
                
            else:
                if(self.isConnected):
                    message = f"{self.nickname}: {userInput}"
                    self.client.send(message.encode('ascii'))
                else:
                    self.disp("Not a command")
                
    def updateConfig(self):
        with open("client_config.ini", "w") as f:
            self.config.write(f)

    def welcome(self):
        self.disp(f"Hello {self.nickname}!")
        self.disp(f"Current Set Room: {self.roomId}")
        self.disp(f"Use !help for commands\n")
        


    def help(self, cmd_dict):
        msg = ""
        for key, value in cmd_dict.items():
            msg += f"* {key} -> {value}\n"
        self.disp_chat(msg)

    def disp(self,message:str):
        print("> " + message)

    def disp_chat(self,message:str):
        print(message)
