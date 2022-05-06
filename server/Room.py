from Member import Member
from operator import attrgetter
import socket
import threading
from config import ip

class Room:
    BUFF_SIZE = 65536

    def __init__(self, newMember, isAudioRoom) -> None:
        self.roomcount = 0
        self.memberlist = []
        self.isAudioRoom = isAudioRoom
        self.addMember(newMember)

        if(isAudioRoom):
            self.portNum = self.find_free_port()
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind((ip, self.portNum))

            self.start_audio_thread()

    def addMember(self, member: Member):
        self.roomcount += 1
        self.memberlist.append(member)

    def removeMember(self, member: Member):
        idx = self.memberlist.index(member)
        self.memberlist.pop(idx)
        self.roomcount -= 1

    def broadcast_to_room(self,dontSendToMe, message):
        encoded = message.encode('ascii')
        for member in self.memberlist:
            if(member.nick != dontSendToMe):
                try:
                    member.client.send(encoded)
                except:
                    "Do nothing...probably a crash"

    def start_audio_thread(self):
        thread = threading.Thread(target=self.get_and_send_audio, args=())
        thread.start()

    def get_and_send_audio(self):
        while self.roomcount > 0:
            try:
                frame,client_addr = self.server_socket.recvfrom(self.BUFF_SIZE)
                if(len(frame) > 10): # For Initial 'Hi' Message
                    self.send_to_room(frame, client_addr)
            except:
                "Wait For Data"

    def send_to_room(self, data, address):
        for member in self.memberlist:
            if(member.address[0] != address[0]):
                self.server_socket.sendto(data, (member.address[0], member.udpPort ))
            
            


    # Thank you Mr. Pawel Bylica
    def find_free_port(self):
        with socket.socket() as s:
            s.bind(('', 0))            # Bind to a free port provided by the host.
            port = s.getsockname()[1]
            s.close()
            return port # Return the port number assigned.
