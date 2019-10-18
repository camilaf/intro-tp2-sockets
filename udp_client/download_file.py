import os
import socket
import errno

CHUNK_SIZE = 2048
DELIMITER = ';'
MAX_TIMEOUTS = 10
SOCKET_TIMEOUT = 2

SUCCESS = 0
ERROR = 1


def download_file(server_address, name, dst):
    chunks = {}

    print('UDP: download_file({}, {}, {})'.format(server_address, name, dst))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(SOCKET_TIMEOUT)

    try:
        status, response = send_message('download' + DELIMITER + name, server_address, client_socket)

        if status != SUCCESS:
            return status

        if response == 'File not found':
            print('The requested file {} does not exist'.format(name))
            return ERROR

        file_size, offset = response.split(DELIMITER, 1)
        print('Received file_size {} and offset {}.'.format(file_size, offset))

        file_size = int(file_size)
        offset = int(offset)

        message = 'start transmission' + DELIMITER + name
        client_socket.sendto(message.encode(), server_address)
        print('Start transmission sent. Ready to receive file...')

        status = recv_file(client_socket, server_address, file_size, chunks, offset)

        if status == SUCCESS:
            print('Writing file...')
            write_file(file_size, chunks, offset, dst)
        return status
    finally:
        client_socket.close()


def send_message(message, server_address, client_socket):
    for _ in range(MAX_TIMEOUTS):
        client_socket.sendto(message.encode(), server_address)
        try:
            response, addr = client_socket.recvfrom(CHUNK_SIZE)
            return SUCCESS, response.decode()
        except socket.timeout:
            print('Socket timed out attempting to send message!')
    return ERROR, ''


def recv_file(client_socket, server_address, file_size, chunks, offset):
    # Tengo que meter el chunk en el diccionario
    # Actualizar el ultimo recibido en general
    # Chequear que estamos recibiendo en orden los chunks
    # SI no es asi enviamos el ack del ultimo recibido en orden
    # Si estamos recibiendo en orden enviamos el ack del recibido y actualizamos el ultimo recibido en orden
    total_received_size = 0
    timeouts = 0
    offset_number = -1
    last_ordered_chunk = -1*offset

    while total_received_size < file_size:  # while no es fin or timeout
        try:
            print('Waiting to receive chunk...')

            response, addr = client_socket.recvfrom(CHUNK_SIZE)
            offset_number, chunk = response.decode().split(DELIMITER, 1)

            timeouts = 0

            print('Received offset_number {} and chunk {}'.format(offset_number, chunk))
            offset_number = int(offset_number)

            if offset_number in chunks: # ya tenemos este chunk
                client_socket.sendto(str(last_ordered_chunk).encode(), server_address)
                continue

            chunks[offset_number] = chunk
            total_received_size += offset
            print('total_received_size={}'.format(total_received_size))

            #arranco del siguiente chunk al ultimo ordenado:
            pos = last_ordered_chunk + offset
            # me fijo si llego a total_received_size, sino agarro la siguiente 'pos' que no este en chunks:
            while pos < total_received_size and pos in chunks:
                pos += offset #incremento de a offset
            last_ordered_chunk = pos - offset

            print('last_ordered_chunk = {}'.format(last_ordered_chunk))

            if last_ordered_chunk >= 0:
                print('Send ack for last available chunk offset {}'.format(last_ordered_chunk))
                client_socket.sendto(str(last_ordered_chunk).encode(), server_address)

        except socket.timeout:
            print('Receive chunk timed out!')
            if total_received_size < file_size and timeouts < MAX_TIMEOUTS:
                timeouts += 1
                if last_ordered_chunk >= 0:
                    print('Send ack for last available chunk offset {}'.format(last_ordered_chunk))
                    client_socket.sendto(str(last_ordered_chunk).encode(), server_address)
            else:
                return ERROR

    timeouts = 0

    while timeouts < MAX_TIMEOUTS:
        try:
            response, addr = client_socket.recvfrom(CHUNK_SIZE)
            message = response.decode()
            if message == 'END':
                print('Received END')
                return SUCCESS
        except socket.timeout:
            timeouts += 1
            print('Resending last ack due to timeout waiting for end message.')
            client_socket.sendto(str(last_ordered_chunk).encode(), server_address)

    return SUCCESS



def write_file(file_size, chunks, offset, dst):
    if not os.path.exists(os.path.dirname(dst)):
        try:
            os.makedirs(os.path.dirname(dst))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    with open(dst, 'w') as f:
        for i in range(0, file_size, offset):
            f.write(chunks[i])

