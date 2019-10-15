import os, socket

CHUNK_SIZE = 2048
OFFSET = '60'
DELIMITER = ';'
WINDOW = 4
MAX_TIMEOUTS_WAIT = 5

SUCCESS = 0
ERROR = 1


def start_server(server_address, storage_dir):
    print('UDP: start_server({}, {})'.format(server_address, storage_dir))
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_address)

    try:
        print('The server is ready to receive.')
        while True:
            server_socket.settimeout(None)
            print('Waiting for client to send message...')
            message, client_address = server_socket.recvfrom(CHUNK_SIZE)

            print('Received message {}'.format(message))
            operation, file_info = message.decode().split(DELIMITER, 1)

            if operation == 'download':
                print('Requested info to download file {}'.format(file_info))

                # Recibir el nombre del archivo y validar que existe
                # Informar al cliente del resultado
                if (os.path.isfile(file_info)):
                    print('Found file {}'.format(file_info))
                    file_size = os.path.getsize(file_info)
                    response = str(file_size) + DELIMITER + OFFSET
                    server_socket.sendto(response.encode(), client_address)
                else:
                    server_socket.sendto('File not found'.encode(), client_address)

            elif operation == 'start transmission':
                print('Starting file transmission')

                server_socket.settimeout(2)
                send_file(server_socket, client_address, file_info, os.path.getsize(file_info), int(OFFSET))
            else:
                continue
        return SUCCESS
    except:
        return ERROR
    finally:
        server_socket.close()


def send_file(server_socket, client_address, file_name, file_size, offset):
    with open(file_name) as f:
        for i in range(0, file_size, offset * WINDOW):
            chunks = {}
            # mappeo a los offsets de cada chunk con lo que lei del archivo. e.g: { 0 : 'manuelita ', 4: 'se marcho ' }
            for j in range(WINDOW):
                chunk_offset = i + j*offset
                if chunk_offset < file_size:
                    chunks[str(chunk_offset)] = f.read(offset)
            print('Read {} from {}'.format(chunks, file_size))
            # Mando los chunks de a ventanas de WINDOW,
            # o sea mando una cantidad WINDOW de chunks de tamanio offset
            # y no sigo hasta asegurarme de que se recibieron bien todos
            status = send_chunks(server_socket, client_address, chunks)
            if (status != SUCCESS):
                return status
    return SUCCESS


def send_chunks(server_socket, client_address, chunks):
    must_transfer = True
    i = 0
    while must_transfer and i < MAX_TIMEOUTS_WAIT:
        # Mandamos todos los chunks de la lista que no
        # recibieron ack
        for offset, chunk in chunks.items():
            print('Send offset {} chunk {}'.format(offset, chunk))
            server_socket.sendto((offset + DELIMITER + chunk).encode(), client_address)
        try:
            for _ in range(len(chunks)):
                response, addr = server_socket.recvfrom(CHUNK_SIZE)
                ack = response.decode()
                print('Received ack {}'.format(ack))
                if ack in chunks:
                    chunks.pop(ack) # Borrar el ack si esta en el dict
                must_transfer = len(chunks) > 0
                print('chunks not acked {}'.format(chunks))
        except socket.timeout:
            print('Timeout while waiting for ack!')
            continue
    if i >= MAX_TIMEOUTS_WAIT:
        return ERROR
    return SUCCESS


