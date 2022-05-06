import threading
from client import Client

if __name__ == "__main__":
    print("Starting app...\n")
    newClient = Client()


    command_handling = threading.Thread(target=newClient.command_handling)
    command_handling.start()
