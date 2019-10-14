import os, socket

CHUNK_SIZE = 2048
SIZE = '1200'
OFFSET = '60'
DELIMITER = ';'
WINDOW = 4
MAX_TIMEOUTS_WAIT = 5

def start_server(server_address, storage_dir):
    print('UDP: start_server({}, {})'.format(server_address, storage_dir))
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_address)
    server_socket.settimeout(2)

    print('The server is ready to receive')
    while True:

        message, client_address = server_socket.recvfrom(CHUNK_SIZE)
        operation, file_info = message.decode().split(DELIMITER, 1)

        if operation == 'download':
            print('Requested info to download file {}'.format(file_info))
            response = SIZE + DELIMITER + OFFSET

            server_socket.sendto(response.encode(), client_address)

            message, client_address = server_socket.recvfrom(CHUNK_SIZE)

            file_name = message.decode()

            # Recibir el nombre del archivo y validar que existe
            # Informar al cliente del resultado
            if (os.path.isfile(file_name)):
                print('Found file {}'.format(file_name))
                server_socket.sendto('ok'.encode(), client_address)
            else:
                server_socket.sendto('File not found'.encode(), client_address)

        elif operation == 'start transmission':
            print('Starting file transmission')
            send_file(server_socket, client_address, file_info)
        else:
            continue

    server_socket.close()


def send_file(server_socket, client_address, file_name):
    with open(file_name) as f:
        for i in range(0, file_size, CHUNK_SIZE * WINDOW):
            # mappeo a los offsets de cada chunk con lo que lei del archivo. e.g: { 0 : 'manuelita ', 4: 'se marcho ' }
            chunks = { str(i) : f.read(CHUNK_SIZE) for _ in range(WINDOW) } 
            print('Read {}'.format(chunks))
            # Mando los chunks de a ventanas de WINDOW,
            # o sea mando una cantidad WINDOW de chunks de tamanio CHUNK_SIZE
            # y no sigo hasta asegurarme de que se recibieron bien todos
            send_chunks(server_socket, client_address, chunks)


def send_chunks(server_socket, client_address, chunks):
    must_transfer = True
    # Mandamos todos los chunks de la lista
    for offset, chunk in chunks:
        client_socket.sendto(chunk.encode(), server_address)
    while must_transfer:
        try:
            response, addr = client_socket.recvfrom(CHUNK_SIZE)
            ack = response.decode()
            chunks.pop(ack, None) # Borrar el ack si esta en el dict
            must_transfer = chunks.empty()
        except socket.timeout:
            # Mandamos todos los no recibidos
            for offset, chunk in chunks:
                client_socket.sendto(chunk.encode(), server_address)


