import socket

CHUNK_SIZE = 2048
SIZE = '1200'
OFFSET = '60'
DELIMITER = ';'

def start_server(server_address, storage_dir):
  print('UDP: start_server({}, {})'.format(server_address, storage_dir))
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  server_socket.bind(server_address)
  print("The server is ready to receive")
  while True:
    message, client_address = server_socket.recvfrom(CHUNK_SIZE)
    operation, file_info = message.decode().split(DELIMITER, 1)
    if operation == 'download':
      print(file_info) #TODO: buscar archivo, validaciones
      response = SIZE + DELIMITER + OFFSET
      server_socket.sendto(response.encode(), client_address)
      message, client_address = server_socket.recvfrom(CHUNK_SIZE)
      message = message.decode()
      print(message)
      server_socket.sendto('ok'.encode(), client_address)
  server_socket.close()
