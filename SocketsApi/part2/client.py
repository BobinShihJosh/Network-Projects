import socket
import struct
import sys

# Constants
 

class Client:
    def __init__(self, name):
        self.name = name
    
    def send_request(self):
        step_num = 1
        student_num = 835
        initial_udp_portnum = 12239

        HEADERSIZE = 12
        server_hosts = ['attu2.cs.washington.edu', "127.0.0.1"]

        timeout = 0.5  
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        
        print('#################################   STAGE A   ##################################')
        # SEND 
        payload = bytes('hello world'+'\0', 'utf-8')
        print(payload)
        payload_length = len(payload)
        header = struct.pack('>IIHH', payload_length, 0, step_num, student_num)
        padding = b'\0' * (4 - payload_length % 4) 
        msg = header + payload #+ padding
        udp_sock.sendto(msg, (server_hosts[1], initial_udp_portnum))
        print(f'SEND: HEADER: {payload_length, 0, step_num, student_num} PAYLOAD: {payload}')


        # RECEIVE
        data, addr = udp_sock.recvfrom(1024)

        unpacked_recv_header = struct.unpack('>IIHH', data[:HEADERSIZE])
        num, length, udp_port, secretA = struct.unpack('>IIII', data[HEADERSIZE:])

        print(f"RECEIVED num {num}, len {length}, udp_port {udp_port}, secretA {secretA}")

        print('#################################   STAGE B   ##################################')
        # SEND
        udp_sock.settimeout(timeout)
        last_ack_id = 0 
        while last_ack_id < num:
            packet_id = struct.pack('>I', last_ack_id)
            payload = packet_id + b'\x00' * length 
            payload_length = length + 4
            
            header = struct.pack('>IIHH', payload_length, secretA, step_num, student_num)
            if length % 4 != 0:
                padding = b'\0' * (4 - payload_length % 4)
                msg = header + payload + padding
            else:
                msg = header + payload

            print(f'Sending packed {packet_id}... waiting for ack')
            udp_sock.sendto(msg, (server_hosts[1], udp_port))

            try:
                ack_packet, server_add = udp_sock.recvfrom(1024)
                ack_id = int.from_bytes(ack_packet[HEADERSIZE:], byteorder='big')
                print(ack_id)
                if ack_id == last_ack_id:
                    print(f'Succesfully sent: packet {ack_id}/{num}  \n')
                    last_ack_id += 1

            except socket.timeout:
                print('timeout... RESENDING\n') 

        # RECEIVE
        data, server_add = udp_sock.recvfrom(1024)

        recv_header = struct.unpack('>IIHH', data[:HEADERSIZE])
        recv_TCP_port = int.from_bytes(data[HEADERSIZE:HEADERSIZE+4], byteorder='big')
        recv_secretb = int.from_bytes(data[HEADERSIZE+4:], byteorder='big')

        print(f'RECEIVE, TCP PORT {recv_TCP_port}, SECRETB {recv_secretb}')
        print('#################################   STAGE C   ##################################')
        # close the UDP socket
        udp_sock.close()

        # open new TCP socket and connect to server
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((server_hosts[1], recv_TCP_port))

        # receive the tcp packet from server
        data = tcp_sock.recv(1024)
        recv_header = struct.unpack('>IIHH', data[:HEADERSIZE])
        num2 = int.from_bytes(data[HEADERSIZE:HEADERSIZE+4], byteorder='big')
        len2 = int.from_bytes(data[HEADERSIZE+4:HEADERSIZE+8], byteorder='big')
        secretC = int.from_bytes(data[HEADERSIZE+8:HEADERSIZE+12], byteorder='big')



        c = (data[HEADERSIZE+12:HEADERSIZE+13]).decode()
        print(data[HEADERSIZE+12:HEADERSIZE+13])
        print(f'PAYLOAD: {(num2, len2, secretC, c)}, HEADER: {recv_header}')

        print('#################################   STAGE D   ##################################')
        # Add padding for byte alignment
        padding = 0
        if len2 % 4 != 0:
            padding = 4 - len2 % 4
        # send num2 payloads of len2
        payload = bytes(c, 'utf-8') * (len2 + padding)
        print(f'Payload length {len2 + padding}  -- Payload {payload}')
        # Header
        header = struct.pack('>IIHH', len2, secretC, step_num, student_num)
        
        msg = header + payload

        curPacket = 0
        while curPacket < num2:
            tcp_sock.sendall(msg)
            
            print(f'{curPacket+1}/{num2} packets sent')
            curPacket += 1

        recv_data = tcp_sock.recv(1024)
        recv_header = struct.unpack('>IIHH', recv_data[:HEADERSIZE])
        recv_payload = struct.unpack('>I', recv_data[HEADERSIZE:])

        print(f'recv_header {recv_header}, recv payload {recv_payload}s')

        tcp_sock.close()
        print("PROTOCOL COMPLETE...\n")

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else "default"
    client = Client(name)
    client.send_request()