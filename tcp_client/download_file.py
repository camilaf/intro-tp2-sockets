import socket
import os

CHUNK_SIZE = 2048

SUCCESS = 0
ERROR = 1

def download_file(server_address, name, dst):
  print('TCP: download_file({}, {}, {})'.format(server_address, name, dst))

  # Create the socket to communicate with the tcp server
  client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client_socket.connect(server_address)

  request = "download"
  client_socket.send(request.encode())
  response = client_socket.recv(CHUNK_SIZE)
  if response.decode() != "Start download":
    print("The connection experimented a problem")
    return ERROR

  # Send name of the file that we want to download
  client_socket.send(name.encode())
  response = client_socket.recv(CHUNK_SIZE).decode()
  if response == "File not found":
    print("Closing connection due to the non-existence of the file")
    client_socket.close()
    return ERROR

  dirname = os.path.dirname(dst)
  if not os.path.exists(dirname):
    os.makedirs(dirname)
  file = open(dst, "wb")
  bytes_received = 0
  file_size = int(response)
  client_socket.send("Size received".encode())
  while bytes_received < file_size:
    chunk = client_socket.recv(CHUNK_SIZE)
    bytes_received += len(chunk)
    file.write(chunk)

  client_socket.send(str(bytes_received).encode())
  file.close()
  client_socket.close()
