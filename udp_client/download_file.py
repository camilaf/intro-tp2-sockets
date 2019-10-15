import time
import socket

CHUNK_SIZE = 2048
DELIMITER = ';'
MAX_TIMEOUTS = 5
SOCKET_TIMEOUT = 2

SUCCESS = 0
ERROR = 1


def download_file(server_address, name, dst):
    chunks = {}

    # TODO: Implementar UDP download_file client
    print('UDP: download_file({}, {}, {})'.format(server_address, name, dst))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(SOCKET_TIMEOUT)

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

    if (status == SUCCESS):
        print('Writing file...')
        write_file(file_size, chunks, offset, dst)

        #print('Send end transmission message')
        #response = end_download(server_address, client_socket)
        #print(response)

    client_socket.close()


def send_message(message, server_address, client_socket):
    for _ in range(MAX_TIMEOUTS):
        client_socket.sendto(message.encode(), server_address)
        try:
            response, addr = client_socket.recvfrom(CHUNK_SIZE)
            return (SUCCESS, response.decode())
        except socket.timeout:
            print('Socket timed out attempting to send message!')
    return (ERROR, '')


def recv_file(client_socket, server_address, file_size, chunks, offset):
    # Tengo que meter el chunk en el diccionario
    # Actualizar el ultimo recibido en general
    # Chequear que estamos recibiendo en orden los chunks
    # SI no es asi enviamos el ack del ultimo recibido en orden
    # Si estamos recibiendo en orden enviamos el ack del recibido y actualizasmos el ultimo recibido en orden
    # TODO NTH timeout si me desenchufan el server
    # TODO Garantia de entrega: timeout
    # ultimo recibido en orden, ultimo recibido en general
    #received_chunks = [-1*offset, -1*offset]
    total_received_size = 0
    timeouts = 0
    #offset_number = -1*offset
    offset_number = -1
    last_ordered_chunk = -1*offset

    while total_received_size < file_size:  # while no es fin or timeout
        try:
            print('Waiting to receive chunk...')

            response, addr = client_socket.recvfrom(offset)
            offset_number, chunk = response.decode().split(DELIMITER, 1)
            if chunk == 'END':
                print('Received END!')
                return SUCCESS

            timeouts = 0

            print('Received offset_number {} and chunk {}'.format(offset_number, chunk))
            offset_number = int(offset_number)

            if offset_number in chunks: # ya tenemos este chunk
                client_socket.sendto(str(offset_number).encode(), server_address)
                continue

            chunks[offset_number] = chunk
            total_received_size += offset
            print('total_received_size={}'.format(total_received_size))


            if (offset_number == 0):
                # Si offset_number es 0 entonces inicializo last_ordered_chunk = 0, 
                # seguro es la primera vez que lo recibo porque ya verifique arriba
                # que no esta en chunks.
                last_ordered_chunk = 0
            else:
                # sino, si offset_number es el que estaba esperando (last_ordered_chunk + offset) 
                # me fijo cual es el siguiente que falta en la secuencia
                if (last_ordered_chunk >= 0 and (offset_number == last_ordered_chunk + offset)): 
                    last_ordered_chunk = offset_number
                    #arranco del siguiente chunk al que acabo de recibir:
                    pos = offset_number + offset 
                    # me fijo si llego a total_received_size, sino agarro la siguiente 'pos' que no este en chunks:
                    while (pos < total_received_size and pos in chunks): 
                        pos += offset #incremento de a offset
                    last_ordered_chunk = pos - offset

            print('last_ordered_chunk = {}'.format(last_ordered_chunk))

            #print('Send ack for received chunk {}'.format(offset_number))
            client_socket.sendto(str(last_ordered_chunk if (last_ordered_chunk > 0) else 0).encode(), server_address)

        except socket.timeout:
            print('Receive chunk timed out!')
            if total_received_size < file_size and timeouts < MAX_TIMEOUTS:
                timeouts += 1
                print('Send ack for last available chunk offset {}'.format(last_ordered_chunk))
                client_socket.sendto(str(last_ordered_chunk if (last_ordered_chunk > 0) else 0).encode(), server_address)
            else:
                return ERROR
    return SUCCESS



def write_file(file_size, chunks, offset, dst):
    with open(dst, 'w') as f:
        for i in range(0, file_size, offset):
            f.write(chunks[i])


#def end_download(server_address, client_socket):
#    message = 'end'
#    must_transfer = True
#    while must_transfer:
#        client_socket.sendto(message.encode(), server_address)
#        try:
#            response, addr = client_socket.recvfrom(CHUNK_SIZE)
#            if response.decode() == 'ok':
#                return response
#        except socket.timeout:
#            must_transfer = True
