import socket

CHUNK_SIZE = 2048

def upload_file(server_address, src, name):
  print('UDP: upload_file({}, {}, {})'.format(server_address, src, name))

  client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  message = "holi"
  client_socket.sendto(message.encode(), server_address)
  response, addr = client_socket.recvfrom(CHUNK_SIZE)
  print(response.decode())
  client_socket.close()
