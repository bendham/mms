

class Member:

    def __init__(self, clientDetails, nickname, serverId, address) -> None:
        self.serverId = serverId
        self.client = clientDetails
        self.nick = nickname
        self.address = address
        self.isConnected = True