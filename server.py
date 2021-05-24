import pickle
from socket import *
from answer import Answer, get_all_responses, get_current_seconds
import binascii

from utils import send_udp_message, decimal_to_hex

cache = dict()

cache[("1.0.0.127.in-addr.arpa", "000c")] = [Answer("000c", "03646e73056c6f63616c00", "100")]

prev_check_time = get_current_seconds()


def clear_cache():
    global prev_check_time
    current_time = get_current_seconds()
    if current_time - prev_check_time >= 120:
        keys_to_delete = []
        for k, v in cache.items():
            for item in v:
                if item.valid_till <= current_time:
                    del item
            if len(v) == 0:
                keys_to_delete.append(k)
        for k in keys_to_delete:
            del cache[k]
        prev_check_time = get_current_seconds()

    with open("backup", "wb+") as fs:
        pickle.dump(cache, fs)


def get_name(r, start_name_index=24):
    name = []

    offset = 0

    while True:
        index = start_name_index + offset

        raw = r[index:index + 4]

        if int(raw, 16) >= 49152:
            link = str(bin(int(raw, 16)))[2:]

            link = int(link[2:], 2) * 2

            rest, offset = get_name(r, link)
            name.append(rest)
            name.append(".")
            break

        length = int(r[index:index + 2], 16)

        if length == 0:
            break

        i = 2
        while i <= length * 2:
            decoded = chr(int(r[index + i:index + i + 2], 16))
            name.append(decoded)
            i += 2

        name.append(".")
        offset += length * 2 + 2

    name = "".join(name[:-1])

    return name, offset


def extract_name(r, ind):
    link = str(bin(int(r[ind:ind+4], 16)))[2:]
    link = int(link[2:], 2) * 2
    res, _ = get_name(r, link)
    return res


def parse_response(r):
    if r is None:
        return None

    header = r[0:24]
    question = r[24:]

    name, offset = get_name(r)

    t = question[offset - 8: offset - 4]

    dot_count = name.count(".")
    char_count = len(name) - dot_count
    question_len = char_count * 2 + (dot_count + 2) * 2

    answer = r[24 + question_len + 8:]

    an_count = int(header[12:16], 16)
    ns_count = int(header[16:20], 16)
    ar_count = int(header[20:24], 16)

    counts = [an_count, ns_count, ar_count]

    rest = answer

    for count in counts:
        answers = []

        prev_n = name
        n = name

        for i in range(count):
            n = extract_name(r, r.index(rest))
            t = rest[4:8]
            ttl = rest[12:20]
            data_len = rest[20:24]

            data_length = int(data_len, 16) * 2
            data = rest[24:24 + data_length]

            link = str(bin(int(data[-4:], 16)))[2:]
            if t == "0002" and data[-2:] != "00" and link[:2] == "11":
                link = int(link[2:], 2) * 2
                _, offset = get_name(r[link:], 0)
                ending = r[link:link+offset] + "00"
                data = data[:-4] + ending

            ans = Answer(t, data, ttl)

            rest = rest[24 + data_length:]

            if n != prev_n:
                cache[(n, t)] = [ans]
                answers = []
            else:
                answers.append(ans)

            prev_n = n

        if len(answers) != 0:
            cache[(n, t)] = answers

    with open("backup", "wb+") as fa:
        pickle.dump(cache, fa)

    return r


def parse_request(request):
    header = request[0:24]
    question = request[24:]

    name, _ = get_name(request)

    t = question[-8: -4]

    if (name, t) in cache:
        content, count = get_all_responses(cache[(name, t)])

        if count != 0:
            _id = header[0:4]
            flags = "8180"
            qd_count = header[8:12]
            an_count = decimal_to_hex(count).rjust(4, '0')
            ns_count = header[16:20]
            ar_count = header[20:24]

            new_header = _id + flags + qd_count + an_count + ns_count + ar_count

            print("name {} type '{}' record returned from cache".format(name, t))

            return new_header + question + content

    print("name {} type '{}' record returned from server".format(name, t))

    return parse_response(send_udp_message(request, "195.19.71.253", 53))


if __name__ == '__main__':
    try:
        with open("backup", "rb") as f:
            cache = pickle.load(f)
    except:
        print("backup file not found")

    host = 'localhost'
    port = 53
    addr = (host, port)

    udp_socket = socket(AF_INET, SOCK_DGRAM)
    udp_socket.bind(addr)

    print("started on {}".format(addr))
    while True:
        received, addr = udp_socket.recvfrom(1024)
        received = binascii.hexlify(received).decode("utf-8")

        response = parse_request(received)

        if response is not None:
            udp_socket.sendto(binascii.unhexlify(response), addr)
        clear_cache()
