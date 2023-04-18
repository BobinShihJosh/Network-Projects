import socket
import threading
import random
from struct import pack, unpack



def run_protocol(message, client_ip, client_num):
    buffer_len = 1024
    student_id = 835
    timeout = 3
    header_len = 12 

    print("Stage A start, client num#", client_num) 
    payload_len, psecret, step, student_num = unpack('>IIHH', message[0:12])
    payload = message[header_len:header_len+payload_len].decode()
    if payload != 'hello world' + '\0':
        return
    num = random.randint(1, 20)
    the_len = random.randint(1, 20)
    udp_port = random.randint(20000, 65535)
    while udp_port in udp_ports:
        udp_port = random.randint(20000, 65535)
    udp_ports.append(udp_port)
    secretA = random.randint(0, 4294967295)
    header = pack('>IIHH', 16, secretA, 1, student_id)
    response = header + pack('>IIII', num, the_len, udp_port, secretA)

    sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock1.settimeout(timeout)
    sock1.sendto(response, client_ip)
    sock1.close()
    print("Stage A end, client num#", client_num)



    print("Stage B start, client num#", client_num)
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2.settimeout(timeout)
    sock2.bind((ip, udp_port))
    packets_received = 0
    received_id = 0
    while packets_received < num:
         
        message, client_ip = sock2.recvfrom(buffer_len)
        payload_len, psecret, step, student_num, packet_id = unpack('>IIHHI', message[0:16])
        
        if psecret != secretA or step != 1 or student_num != student_id:
            return
        payload = message[16:16+the_len]
        all_zero = all(int(elem) == 0 for elem in payload)
        true_payload_len = the_len
        if the_len%4 != 0:
            true_payload_len = the_len + (4-the_len%4)

        rand_num = random.random()
        if rand_num < 0.5 and packet_id == received_id and len(message)%4 == 0 and len(message[16:]) == true_payload_len and all_zero:
            packets_received += 1
            received_id += 1
            header = pack('>IIHH', 16, secretA, 1, 444)
            response = header + pack('>I', packet_id)
            sock2.sendto(response, client_ip)

    if packets_received == num:
        tcp_port = random.randint(20000, 65535)
        while tcp_port in tcp_ports:
            tcp_port = random.randint(20000, 65535)
        tcp_ports.append(tcp_port)
        secretB = random.randint(0, 4294967295)
        header = pack('>IIHH', 8, secretB, 2, student_id)
        response = header + pack('>II', tcp_port, secretB)
        sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock3.bind((ip, tcp_port))
        sock3.listen(5)
        sock2.sendto(response, client_ip)
        sock2.close()
    udp_ports.remove(udp_port)
    print("Stage B end, client num#", client_num)



    print("Stage C start, client num#", client_num)
    connection, client_address = sock3.accept()
    num2 = random.randint(1, 20)
    len2 = random.randint(1, 20)
    secretC = random.randint(0, 4294967295)
    c = chr(random.randint(33, 126)) 
    header = pack('>IIHH', 13, secretC, 2, student_id)
    message = header + pack('>III', num2, len2, secretC) + c.encode("ascii")
    connection.sendto(message, client_address)
    print("Stage C end, client num#", client_num)



    print("Stage D start, client num#", client_num)
    payloads_received = 0
    mess_len = len2 + header_len
    if len2%4 != 0:
        mess_len = len2 + (4-len2%4) + header_len
    sock3.settimeout(timeout)
    while payloads_received < num2:
        try:
            message = connection.recv(mess_len)
        except:
            return
        payload_len, psecret, step, student_num = unpack('>IIHH', message[0:12])
        if psecret != secretC or step != 1 or student_num != student_id:
            return
        payload = message[header_len:header_len + len2]
        all_c = all(chr(elem) == c for elem in payload)
        if len(message)%4 == 0 and len(message) == mess_len and all_c:
            payloads_received += 1

    secretD = random.randint(0, 4294967295)
    header = pack('>IIHH', 4, secretC, 2, student_id)
    response = header + pack('>I', secretD)
    connection.sendto(response, client_address)
    tcp_ports.remove(tcp_port)
    sock3.close()
    print("Stage D end, client num#", client_num)
    print(f"================== Complete client #{client_num} ==================")

ip ="127.0.0.1"
udp_port = 12239
udp_ports = []
tcp_ports = []

print("Start server")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, udp_port))
client_num = 0
while True:
    message, client_ip = sock.recvfrom(1024)
    client_thread = threading.Thread(target=run_protocol, args=(message, client_ip, client_num))
    client_num += 1
    client_thread.start()
sock.close()