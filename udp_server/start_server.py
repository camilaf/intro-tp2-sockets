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

            message = message.decode()

            print('Received message {}'.format(message))
            if DELIMITER not in message:
                continue

            operation, file_info = message.split(DELIMITER, 1)

            if operation == 'download':
                print('Requested info to download file {}'.format(file_info))

                # Recibir el nombre del archivo y validar que existe
                # Informar al cliente del resultado
                if os.path.isfile(file_info):
                    print('Found file {}'.format(file_info))
                    file_size = os.path.getsize(file_info)
                    response = str(file_size) + DELIMITER + OFFSET
                    server_socket.sendto(response.encode(), client_address)
                else:
                    server_socket.sendto('File not found'.encode(), client_address)

            if operation == 'upload':
                name, total_chunks = file_info.split(DELIMITER, 1)
                print('Requested info to upload file {} with {} chunks'.format(name, total_chunks))
                server_socket.sendto("Start upload".encode(), client_address)
                server_socket.settimeout(2)
                recv_file(server_socket, client_address, int(total_chunks), storage_dir + '/' + name)

            elif operation == 'start transmission':
                print('Starting file transmission')

                server_socket.settimeout(2)
                status = send_file(server_socket, client_address, file_info, os.path.getsize(file_info), int(OFFSET))
                if status == SUCCESS:
                    print('Sending END')
                    server_socket.sendto('END'.encode(), client_address)
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
            chunk_offset = 0
            # mappeo a los offsets de cada chunk con lo que lei del archivo. e.g: { 0 : 'manuelita ', 4: 'se marcho ' }
            for j in range(WINDOW):
                chunk_offset = i + j*offset
                if chunk_offset < file_size:
                    chunks[str(chunk_offset)] = f.read(offset)
            print('Read {} from {}'.format(chunks, file_size))
            # Mando los chunks de a ventanas de WINDOW,
            # o sea mando una cantidad WINDOW de chunks de tamanio offset
            # y no sigo hasta asegurarme de que se recibieron bien todos
            status = send_chunks(server_socket, client_address, chunks, chunk_offset if chunk_offset < file_size else (file_size//offset)*offset)
            if (status != SUCCESS):
                return status
    return SUCCESS


def send_chunks(server_socket, client_address, chunks, last_offset):
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
                print('Received ack {} last_offset {}'.format(ack, last_offset))
                if int(ack) >= last_offset: # Ack acumulativo
                    return SUCCESS
                i = 0
                if ack in chunks:
                    chunks.pop(ack) # Borrar el ack si esta en el dict
                must_transfer = len(chunks) > 0
                print('chunks not acked {}'.format(chunks))
        except socket.timeout:
            i += 1
            print('Timeout while waiting for ack!')
            continue
    if i >= MAX_TIMEOUTS_WAIT:
        return ERROR
    return SUCCESS

def recv_file(server_socket, client_address, total_chunks, dst):
    received_chunks = 0
    timeouts_count = 0
    chunks = {}
    while received_chunks < total_chunks and timeouts_count < MAX_TIMEOUTS_WAIT:
        try:
            response, addr = server_socket.recvfrom(CHUNK_SIZE)
            chunk_id, chunk = response.decode().split(DELIMITER)
            print("Received chunk id {}".format(chunk_id))
            server_socket.sendto(chunk_id.encode(), client_address)
            if chunk_id not in chunks:
                chunks[chunk_id] = chunk
                received_chunks += 1
        except socket.timeout:
            timeouts_count += 1
            print('Timeout while waiting for ack!')
            continue
    if timeouts_count >= MAX_TIMEOUTS_WAIT:
        return ERROR
    write_file(dst, chunks)
    return SUCCESS

def write_file(dst, chunks):
    dirname = os.path.dirname(dst)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    file = open(dst, "w")
    size = len(chunks)
    for i in range(0, size):
        file.write(chunks[str(i)])

