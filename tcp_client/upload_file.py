import socket
import os

CHUNK_SIZE = 2048
DELIMITER = ';'

SUCCESS = 0
ERROR = 1

def upload_file(server_address, src, name):
  print('TCP: upload_file({}, {}, {})'.format(server_address, src, name))
  try:
    file = open(src, "rb")
  except IOError:
    print("File does not exist")
    return ERROR

  # Get the size of the file
  file.seek(0, os.SEEK_END)
  file_size = file.tell()
  file.seek(0, os.SEEK_SET)

  # Create the socket to communicate with the tcp server
  client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client_socket.connect(server_address)

  client_socket.send("upload".encode())
  response = client_socket.recv(CHUNK_SIZE)
  if response.decode() != "Start upload":
    print("The connection experimented a problem")
    return ERROR

  print("Sending size and name of the file")
  size_and_name_msg = str(file_size) + DELIMITER + name
  client_socket.send(size_and_name_msg.encode())
  response = client_socket.recv(CHUNK_SIZE)

  print("Sending file")
  chunk = file.read(CHUNK_SIZE)
  while chunk:
    client_socket.send(chunk)
    chunk = file.read(CHUNK_SIZE)

  bytes_received = client_socket.recv(CHUNK_SIZE)
  print("The server received {} bytes".format(bytes_received.decode()))
  file.close()
  client_socket.close()
