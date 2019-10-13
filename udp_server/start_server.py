import socket

CHUNK_SIZE = 2048

def start_server(server_address, storage_dir):
  print('UDP: start_server({}, {})'.format(server_address, storage_dir))
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  server_socket.bind(server_address)
  print("The server is ready to receive")
  while True:
    message, client_address = server_socket.recvfrom(CHUNK_SIZE)
    response = message.decode().upper()
    server_socket.sendto(response.encode(), client_address)
  server_socket.close()
