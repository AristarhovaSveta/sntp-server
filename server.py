import socket
import struct
import time
import datetime

sys_epoch = datetime.date(*time.gmtime(0)[0:3])
ntp_epoch = datetime.date(1900, 1, 1)
delta = (sys_epoch - ntp_epoch).total_seconds()


def fraction(timestamp, n=32):
    return int(abs(timestamp - int(timestamp)) * 2 ** n)


def pack_response(recv_timestamp,
                  timestamp_seconds_from_request,
                  timestamp_fraction_from_request,
                  lie):
    leap = 0
    version = 3
    mode = 4
    stratum = 2
    poll = 10
    precision = 0
    root_delay = 0
    root_dispersion = 0
    reference_id = 0
    reference_timestamp = recv_timestamp
    originate_timestamp_seconds = timestamp_seconds_from_request
    originate_timestamp_fraction = timestamp_fraction_from_request
    receive_timestamp = recv_timestamp
    transmit_timestamp = time.time() + delta + lie
    try:
        packed = struct.pack(
            "!3B b 11I",
            leap << 6 | version << 3 | mode,
            stratum,
            poll,
            precision,
            root_delay,
            root_dispersion,
            reference_id,
            int(reference_timestamp),
            fraction(reference_timestamp),
            originate_timestamp_seconds,
            originate_timestamp_fraction,
            int(receive_timestamp),
            fraction(receive_timestamp),
            int(transmit_timestamp),
            fraction(transmit_timestamp))
    except struct.error:
        raise Exception("Invalid NTP packet fields.")
    return packed


def unpack_request(frame):
    try:
        unpacked = struct.unpack("!3B b 11I", frame)
    except struct.error:
        raise Exception("Invalid NTP packet.")
    return unpacked


def start():
    with open('config.txt', 'r') as f_conf:
        lie = f_conf.read()
    lie = int(lie)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 123))
    while True:
        data, address = sock.recvfrom(48)
        received_packet = unpack_request(data)
        receive_timestamp = time.time() + delta
        transmit_timestamp_seconds = received_packet[13]
        transmit_timestamp_fraction = received_packet[14]
        response_packet = pack_response(receive_timestamp,
                                        transmit_timestamp_seconds,
                                        transmit_timestamp_fraction,
                                        lie)
        sock.sendto(response_packet, address)


if __name__ == '__main__':
    start()
