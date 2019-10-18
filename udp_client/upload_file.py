import socket

CHUNK_SIZE = 1024
DELIMITER = ';'
SOCKET_TIMEOUT = 2
WINDOW = 10
MAX_TIMEOUTS_WAIT = 10

SUCCESS = 0
ERROR = 1

def upload_file(server_address, src, name):
  print('UDP: upload_file({}, {}, {})'.format(server_address, src, name))
  try:
    file = open(src, "r")
  except IOError:
    print("File does not exist")
    return 0

  client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  client_socket.settimeout(SOCKET_TIMEOUT)
  chunks = prepare_chunks(file)
  # We send the upload message to the server and wait for the response
  status, response = send_message("upload" + DELIMITER + name + DELIMITER + str(len(chunks)), server_address, client_socket)
  if status != SUCCESS:
    return status
  if response != "Start upload":
    print("The connection experimented a problem")
    return ERROR

  send_file(client_socket, server_address, chunks)
  client_socket.close()

def send_message(message, server_address, client_socket):
  for _ in range(MAX_TIMEOUTS_WAIT):
    client_socket.sendto(message.encode(), server_address)
    try:
      response, addr = client_socket.recvfrom(CHUNK_SIZE)
      return SUCCESS, response.decode()
    except socket.timeout:
      print('Socket timed out attempting to send message!')
  return ERROR, ''

def prepare_chunks(file):
  chunks = {}
  chunk_id = 0
  while True:
    header = str(chunk_id) + DELIMITER
    chunk = file.read(CHUNK_SIZE - len(header))
    if not chunk:
      break

    chunks[str(chunk_id)] = header + chunk
    chunk_id += 1
  return chunks

def send_file(client_socket, server_address, chunks):
  chunks_sent = 0
  total_chunks = len(chunks)
  timeouts_count = 0
  while chunks_sent < total_chunks and timeouts_count < MAX_TIMEOUTS_WAIT:
    chunk_keys = list(chunks.keys())
    chunks_left = total_chunks - chunks_sent
    chunks_to_send = chunks_left if chunks_left < WINDOW else WINDOW
    print("Sending {} chunks in a window".format(chunks_to_send))
    for i in range(chunks_to_send):
      client_socket.sendto(chunks[chunk_keys[i]].encode(), server_address)
    for _ in range(chunks_to_send):
      try:
        response, addr = client_socket.recvfrom(CHUNK_SIZE)
        ack = response.decode()
        print('Received ack {}'.format(ack))
        timeouts_count = 0
        # If it's a new ack
        if ack in chunk_keys:
          chunks_sent += 1
          chunks.pop(ack)

      except socket.timeout:
        timeouts_count += 1
        print('Timeout while waiting for ack!')
        continue
  if timeouts_count >= MAX_TIMEOUTS_WAIT:
    return ERROR
  print("All chunks sent")
  return SUCCESS
