import socket
import threading
from pyaudio import PyAudio, paInt16, paInt32
from config import ip, port
import configparser
import sounddevice as sd


class Client:

	CHUNK_FRAME = 10*1024
	FORMAT_BYTES_PER_SAMPLE = paInt16
	CHANNELS = 2
	BUFF_SIZE = 65536

	RATE = 44100

	def __init__(self):
		self.isConnected = False
		
		self.config = configparser.ConfigParser()
		self.config.read('client_config.ini')

		self.nickname = self.config['client-details']['name']
		self.roomId = self.config['client-details']['room_id']

		self.welcome()
		self.setup_default_input_output()

		self.commandsBaisc = {"!help":"Lists these words", "!roomhelp":"Lists the commands only aplicable to a room", "!room":"lists the current room","!room newRoom":"Set the room you want to connect to. e.g. !room coolRoom","!list": "displays current rooms" , "!name":"prints your current nickname","!name newName":"set's your nickname",
						"!join": "connects you to the setroom. Can also do e.g. !join aRoomOfMyChoice", "!room":"lists the current room", "!leave":"leaves the current room", "!quit": "Quits Matthew's Messaging Service", "!joinaudio" : "joins the audio room", "!mute" : "toggles your mute state", "!pickmic":"choose your microphone", "!pickspeak": "choose your speaker"}

		self.commandsRoomCommands = { "!helproom":"Lists these words", "!members": "lists the current members in the room", "!count": "gives you the number of members for the current room", "!created": "when the room was created", "!whisper": "send direct message to member in room. e.g. !whisper freddy HI THERE", "!stats": "gives you the full shabang of stats!"}

		# Audio Stuff

		self.server_UDP_portnum = 0

		self.send_audio_buffer = []
		self.receive_audio_buffer = []
		self.isMuted = False
		self.needsAudioSetup = True

	def setup_default_input_output(self):
		idList = sd.default.device

		self.input_device_idx = idList[0]
		self.output_device_idx = idList[1]


	def setup_mic_stream(self):
		self.pyAudio_mic = PyAudio()
		self.stream_input = self.pyAudio_mic.open(format=self.FORMAT_BYTES_PER_SAMPLE,
						channels=self.CHANNELS,
						rate=self.RATE,
						input=True,
						input_device_index=self.input_device_idx,
						frames_per_buffer=self.CHUNK_FRAME)

	def setup_speaker_stream(self):
		self.pyAudio_speaker = PyAudio()
		self.stream_play_back = self.pyAudio_speaker.open(format=self.FORMAT_BYTES_PER_SAMPLE,
					channels=self.CHANNELS,
					rate=self.RATE,
					output=True,
					output_device_index=self.output_device_idx,
					frames_per_buffer=self.CHUNK_FRAME)

	def get_audio_from_mic_and_send(self):
		if(self.hasMic):
			self.stream_input.start_stream()
			while self.isConnected:
				if(not self.isMuted):
					data = self.stream_input.read(2205, exception_on_overflow=False)
					self.UDP_voice_socket.sendto(data, (ip, self.UDP_PORT))
			self.stream_input.close()

	def get_audio_from_server_and_play(self):
		if(self.hasSpeaker):
			self.stream_play_back.start_stream()
			while self.isConnected:
				frame = self.UDP_voice_socket.recv(self.BUFF_SIZE)
				self.stream_play_back.write(frame)
			self.stream_play_back.close()

	def setup_input_and_output(self):
		try:
			self.setup_mic_stream()
			self.hasMic = True
		except:
			self.hasMic = False
			self.disp("No Mic detected. No one will be able to hear you.")
		try:
			self.setup_speaker_stream()
			self.hasSpeaker = True
		except:
			self.hasSpeaker = False
			self.disp("No speakers detected. You will not be able to hear anyone.")

	def send_and_receive_audio(self):
		try:
			# Receive Message From Server
			message = self.client.recv(1024).decode('ascii')
			self.UDP_PORT = int(message)

			# Binds UDP Socket
			# self.UDP_voice_socket.sendto("Hi".encode('ascii'), (ip, self.UDP_PORT))


			# # Start TCP Text Message Handlers
			
			send_audio_thread = threading.Thread(target=self.get_audio_from_mic_and_send, args=())
			send_audio_thread.start()

			play_audio_thread = threading.Thread(target=self.get_audio_from_server_and_play, args=())
			play_audio_thread.start()

			self.needsAudioSetup = False
		except:
			# Close Connection When Error
			self.setDisconnectState()
	
	def list_audio_devices(self, deviceType):
		devices = sd.query_devices()

		if(isinstance(devices, dict) ):
			if(deviceType in devices["name"]):
					self.disp(f"{devices['hostapi']} {devices['name']}")
		else:
			idx = 0
			for device in devices:
				if(deviceType in device["name"]):
					current_sysmbol = ""
					if(idx == self.input_device_idx or idx == self.output_device_idx):
						current_sysmbol = "*"

					self.disp(f"{current_sysmbol} {idx} {device['name']}")
				idx += 1
			

		
		

	def connect(self, type="room"):

		if(not self.isConnected):
			# Connecting To Server
			self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.client.connect((ip, port))

			# Audio Transmission Set Up
			self.UDP_voice_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.UDP_voice_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,self.BUFF_SIZE)
			self.UDP_voice_socket.bind(('', self.find_free_port()))

			if(type=="room"):


				message = f"{type} {self.roomId} {self.nickname}"
				self.client.send(message.encode('ascii'))

				connect_message_array = self.client.recv(1024).decode('ascii').split(" ", 1)
				connect_message = connect_message_array[0]
				room_name = connect_message_array[1]

				if(connect_message == "connected"):
					self.isConnected = True
					self.disp("Connected!")
					self.disp_chat(f"\n---- In Room {room_name} ----\n")
					# Starting Threads For Receiving
					receive_thread = threading.Thread(target=self.receive)
					receive_thread.start()
				else:
					self.disp("Could not connect to server.")
			elif(type=="list"):
				
				 # Starting Threads For Receiving
				receive_thread = threading.Thread(target=self.receive_disconnect)
				receive_thread.start()

				self.client.send(type.encode('ascii'))
			elif(type=="audioroom"):
				self.disp("Connecting to audio server...")
				
				message = f"{type} {self.roomId} {self.nickname} {self.UDP_voice_socket.getsockname()[1]}"
				self.client.send(message.encode('ascii'))
				connect_message_array = self.client.recv(1024).decode('ascii').split(" ", 1)
				connect_message = connect_message_array[0]
				room_name = connect_message_array[1]
				if(connect_message == "connected"):
					self.isConnected = True
					self.disp("Connected!")
					self.disp_chat(f"\n---- In Room {room_name} ----\n")


					self.send_and_receive_audio()

					# Starting Threads For Receiving
					receive_thread = threading.Thread(target=self.receive)
					receive_thread.start()
				else:
					self.disp("Could not connect to server.")
				
		else:
			self.disp("Already connected bruv chill!")

		
	def receive_disconnect(self):

		while self.isConnected:

			try:
				# Receive Message From Server
				message = self.client.recv(1024).decode('ascii')
				self.disp_chat(message)
				self.setDisconnectState()
			except:
				# Close Connection When Error
				self.setDisconnectState()
				break
	
	def setDisconnectState(self):
		self.client.close()
		self.isConnected = False
		self.needsAudioSetup = False


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

					if(len(cmdList) == 1):
						self.connect()  
					elif len(cmdList) == 2:
						self.roomId = cmdList[1]
						self.config.set("client-details", "room_id", self.roomId)
						self.updateConfig()
						self.disp(f"Room set to '{self.roomId}'") 
						self.connect()   
				elif(cmd == "!leave"):
					if(self.isConnected):

						self.client.send("!leave".encode('ascii'))
						# self.client.shutdown(socket.SHUT_RDWR)
						# self.isConnected = False

						self.setDisconnectState()

						self.disp("You left")

						self.welcome()
					else:
						self.disp("You are not even connected!")
				elif(cmd == "!quit"):

					if(self.isConnected):
						self.client.close()
					
					self.isConnected = False

					self.disp("Bye, bye!")
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
					if(self.isConnected):
						self.client.send("!list".encode('ascii'))
					else:
						self.connect("list")
				elif(cmd == "!joinaudio"):
					self.setup_input_and_output()
					self.connect("audioroom")
				elif(cmd == "!mute"):
					self.isMuted = not self.isMuted

					if(self.isMuted):
						self.disp("Muted!")
					else:
						self.disp("Unmuted!")
				elif(cmd == "!pickmic"):
					if(len(cmdList) == 1):
						self.list_audio_devices("Microphone")
					elif len(cmdList) == 2:
						if(cmdList[1].isdigit()):
							self.input_device_idx = int(cmdList[1])
							self.disp("Chosen microphone updated")
						else:
							self.disp("Please enter an integer")
					else:
						command_good = False
				elif(cmd == "!pickspeak"):
					if(len(cmdList) == 1):
						self.list_audio_devices("Speakers")
					elif len(cmdList) == 2:
						if(cmdList[1].isdigit()):
							self.output_device_idx = int(cmdList[1])
							self.disp("Chosen speakers updated")
						else:
							self.disp("Please enter an integer")
					else:
						command_good = False
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
		self.disp(f"Use !help for commands")
		
	def help(self, cmd_dict):
		msg = ""
		for key, value in cmd_dict.items():
			msg += f"* {key} -> {value}\n"
		self.disp_chat(msg)

	def disp(self,message:str):
		print("> " + message)

	def disp_chat(self,message:str):
		print(message)

	# Thank you Mr. Pawel Bylica
	def find_free_port(self):
		with socket.socket() as s:
			s.bind(('', 0))            # Bind to a free port provided by the host.
			port = s.getsockname()[1]
			s.close()
			return port # Return the port number assigned.
