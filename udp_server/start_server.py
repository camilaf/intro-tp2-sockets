import os, socket

CHUNK_SIZE = 2048
OFFSET = '60'
DELIMITER = ';'
WINDOW = 4
MAX_TIMEOUTS_WAIT = 10

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
                file_path = storage_dir + "/" + file_info
                if os.path.isfile(file_path):
                    print('Found file {}'.format(file_info))
                    file_size = os.path.getsize(file_path)
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
                status = send_file(server_socket, client_address, file_path, os.path.getsize(file_path), int(OFFSET))
                if status == SUCCESS:
                    print('Sending END')
                    server_socket.sendto('END'.encode(), client_address)
            else:
                continue
        return SUCCESS
    except Exception as e:
        print(e)
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
                    chunks[chunk_offset] = f.read(offset)
            print('Read {} from {}'.format(chunks, file_size))
            # Mando los chunks de a ventanas de WINDOW,
            # o sea mando una cantidad WINDOW de chunks de tamanio offset
            # y no sigo hasta asegurarme de que se recibieron bien todos
            status = send_chunks(server_socket, client_address, chunks, chunk_offset if chunk_offset < file_size else (file_size//offset)*offset)
            if (status != SUCCESS):
                return status
    return SUCCESS


def send_chunks(server_socket, client_address, chunks, last_offset):
    timeouts_count = 0
    must_transfer = True
    # seq num/offset de cada chunk que no tiene ack
    seq_nums = sorted(chunks.keys())
    while must_transfer and timeouts_count < MAX_TIMEOUTS_WAIT:
        # Mandamos todos los chunks de la lista que no
        # recibieron ack
        for seq_num in seq_nums:
            print('Send offset {} chunk {}'.format(seq_num, chunks[seq_num]))
            server_socket.sendto((str(seq_num) + DELIMITER + chunks[seq_num]).encode(), client_address)
        try:
            recv_attempts = len(seq_nums)
            # intento recibir todos los ack
            while recv_attempts > 0:
                response, addr = server_socket.recvfrom(CHUNK_SIZE)
                ack = int(response.decode())
                print('Received ack {} '.format(ack))
                timeouts_count = 0 # reset timeouts
                if ack < seq_nums[0]:
                    pass #ack viejo
                elif ack == seq_nums[0]:
                    seq_nums.pop(0)
                    recv_attempts -= 1
                else:
                    # si recibo un ack mas grande que el siguiente
                    # descarto los mas chicos (Ack acumulativo)
                    for pending_ack in seq_nums:
                        if ack >= pending_ack:
                            print('Discarding reTx of {}.'.format(pending_ack))
                            seq_nums.pop(0)
                            recv_attempts-=1
                must_transfer = len(seq_nums) > 0
                print('chunks not acked {}'.format(seq_nums))
        except socket.timeout:
            timeouts_count += 1
            print('Timeout while waiting for ack!')
            continue
        except Exception as e:
            print(e)
            return ERROR
    if timeouts_count >= MAX_TIMEOUTS_WAIT:
        return ERROR
    return SUCCESS

def recv_file(server_socket, client_address, total_chunks, dst):
    received_chunks = 0
    timeouts_count = 0
    chunks = {}
    while received_chunks < total_chunks and timeouts_count < MAX_TIMEOUTS_WAIT:
        try:
            response, addr = server_socket.recvfrom(CHUNK_SIZE)
            chunk_id, chunk = response.decode().split(DELIMITER, 1)
            print("Received chunk id {}".format(chunk_id))
            timeouts_count = 0
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
    file.close()

