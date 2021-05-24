import binascii
import socket
import time


def get_current_seconds():
    return int(round(time.time()))


def decimal_to_hex(n):
    return hex(n)[2:]


def send_udp_message(msg, address, port):
    msg = msg.replace(" ", "").replace("\n", "")
    server_address = (address, port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    try:
        sock.sendto(binascii.unhexlify(msg), server_address)
        response, _ = sock.recvfrom(4096)
    except:
        return None
    finally:
        sock.close()
    return binascii.hexlify(response).decode("utf-8")

