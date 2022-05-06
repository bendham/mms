from Member import Member
from operator import attrgetter

class Room:

    def __init__(self) -> None:
        self.roomcount = 0
        self.memberlist = []

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
