import time
import socket

CHUNK_SIZE = 2048
DELIMITER = ';'
MAX_TIMEOUTS = 5

SUCCESS = 0
ERROR = 1


def download_file(server_address, name, dst):
    # TODO: Implementar UDP download_file client
    print('UDP: download_file({}, {}, {})'.format(server_address, name, dst))
    chunks = {}

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(2)

    response = send_message('download' + DELIMITER +
                            name, server_address, client_socket)
    if response == 'File not found':
        print('The requested file {} does not exist'.format(name))
        return 0
    file_size, offset = response.split(DELIMITER, 1)
    print('Received file_size {} and offset {}.'.format(file_size, offset))

    file_size = int(file_size)
    offset = int(offset)

    send_message('start transmission' + DELIMITER + name, server_address, client_socket)

    status = recv_file(client_socket, server_address, file_size, chunks, offset)

    if (status == SUCCESS):
        print('Writing file...')
        write_file(file_size, chunks, offset, dst)

        #print('Send end transmission message')
        #response = end_download(server_address, client_socket)
        #print(response)

    client_socket.close()
    pass


def send_message(message, server_address, client_socket):
    while True:
        client_socket.sendto(message.encode(), server_address)
        try:
            response, addr = client_socket.recvfrom(CHUNK_SIZE)
            return response.decode()
        except socket.timeout:
            print('Socket timed out attempting to send message!')


def recv_file(client_socket, server_address, file_size, chunks, offset):
    # Tengo que meter el chunk en el diccionario
    # Actualizar el ultimo recibido en general
    # Chequear que estamos recibiendo en orden los chunks
    # SI no es asi enviamos el ack del ultimo recibido en orden
    # Si estamos recibiendo en orden enviamos el ack del recibido y actualizasmos el ultimo recibido en orden
    # TODO NTH timeout si me desenchufan el server
    # TODO Garantia de entrega: timeout
    # ultimo recibido en orden, ultimo recibido en general
    received_chunks = [-1, -1]
    total_received_size = 0
    timeouts = 0
    offset_number = -1
    expected_offset_number = -1
    while total_received_size < file_size:  # while no es fin or timeout
        try:
            print('Waiting to receive chunk...')
            response, addr = client_socket.recvfrom(CHUNK_SIZE)
            offset_number, chunk = response.decode().split(DELIMITER, 1)
            if chunk == 'END':
                print('Received END!')
                return SUCCESS
            print('Received offset_number {} and chunk {}'.format(offset_number, chunk))
            chunks[offset_number] = chunk
            expected_offset_number = received_chunks[0] + offset
            total_received_size += CHUNK_SIZE
            timeouts = 0
        except socket.timeout:
            print('Receive chunk timed out!')
            if total_received_size < file_size and timeouts < MAX_TIMEOUTS:
                timeouts += 1
            else:
                return ERROR
        if offset_number > received_chunks[1]:
            received_chunks[1] = offset_number
        if expected_offset_number != offset_number:
            client_socket.sendto(str(expected_offset_number).encode(), server_address)
        else:
            received_chunks[0] = offset_number
            client_socket.sendto(str(offset_number).encode(), server_address)


def write_file(file_size, chunks, offset, dst):
    with open(dst, 'w') as f:
        for i in range(0, file_size, offset):
            f.write(chunks[i])


def end_download(server_address, client_socket):
    message = 'end'
    must_transfer = True
    while must_transfer:
        client_socket.sendto(message.encode(), server_address)
        try:
            response, addr = client_socket.recvfrom(CHUNK_SIZE)
            if response.decode() == 'ok':
                return response
        except socket.timeout:
            must_transfer = True
