import threading
from server import ServerMMS
from config import ip, port

if __name__ == "__main__":

    myServer = ServerMMS(ip, port)

    thread = threading.Thread(target=myServer.start_server_thread)
    thread.start()

    command_thread = threading.Thread(target=myServer.command_handling)
    command_thread.start()
