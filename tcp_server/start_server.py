import socket

CHUNK_SIZE = 2048
DELIMITER = ';'
files = {}

def start_server(server_address, storage_dir):
  print('TCP: start_server({}, {})'.format(server_address, storage_dir))
  # Create the tcp socket and wait for connections
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_socket.bind(server_address)
  server_socket.listen(1)
  print("The server is ready to receive")
  while True:
    connection_socket, addr = server_socket.accept()
    print("Accepted connection from {}".format(addr))
    message = connection_socket.recv(CHUNK_SIZE).decode()
    if message == "upload":
      message = "Start upload"
      connection_socket.send(message.encode())
      handle_upload(connection_socket, storage_dir)
    elif message == "download":
      message = "Start download"
      connection_socket.send(message.encode())
      handle_download(connection_socket, storage_dir)
    connection_socket.close()
  server_socket.close()

def handle_upload(connection_socket, storage_dir):
  message = connection_socket.recv(CHUNK_SIZE).decode()
  file_size, file_name = message.split(DELIMITER, 1)

  response = "Size and name received"
  connection_socket.send(response.encode())
  print("Received file name: {} with size: {} bytes".format(file_name, file_size))

  bytes_received = 0
  data = ""
  file_size = int(file_size)
  while bytes_received < file_size:
    chunk = connection_socket.recv(CHUNK_SIZE)
    bytes_received += len(chunk)
    data += chunk.decode()

  file_path = storage_dir + "/" + file_name
  files[file_path] = data

  # Send received bytes
  connection_socket.send(str(bytes_received).encode())

def handle_download(connection_socket, storage_dir):
  file_name = connection_socket.recv(CHUNK_SIZE).decode()
  file_path = storage_dir + "/" + file_name
  file = files.get(file_path, None)
  if not file:
    message = "File not found"
    connection_socket.send(message.encode())
  else:
    file_size = len(file)
    print("Sending bytes of file: " + str(file_size))
    connection_socket.send(str(file_size).encode())
    # Receive start from client
    response = connection_socket.recv(CHUNK_SIZE).decode()

    if response != "Size received":
      print("Closing connection with client")
      return
    print("Sending file " + file_path)
    bytes_sent = 0
    while bytes_sent < file_size:
      chunk = file[bytes_sent : bytes_sent + CHUNK_SIZE]
      connection_socket.send(chunk.encode())
      bytes_sent += len(chunk)

    bytes_received = connection_socket.recv(CHUNK_SIZE)
    print("Received {} bytes".format(bytes_received.decode()))
