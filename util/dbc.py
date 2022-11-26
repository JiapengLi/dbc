import json, time
import fire

import cantools
from pprint import pprint

def fmt(msg):
    return msg + (64 - len(msg)) * b'\x00'

def check(dbcfile):
    db = cantools.database.load_file(dbcfile)
    pprint(db.messages)
    for m in db.messages:
        # print(m.__dict__)
        # example_message = db.get_message_by_name('RX')
        pprint(m.signals)
    # db.get_message_
    msg = db.decode_message(0x7E8, fmt(b"\x08\x41\x00\xFF\xFF\xFF\xFF\xAA"))
    pprint(msg)

    msg = db.decode_message(0x7E8, fmt(b"\x08\x42\x00\xFF\xF0\xFF\xFF\xAA"))
    pprint(msg)

    msg = db.decode_message(0x7E8, fmt(bytes.fromhex('14490201335657524136394d37344d303333393135')))
    pprint(msg)
    print(type(msg['S09_PID02_VIN']))

    pprint(int.to_bytes(msg['S09_PID02_VIN'], 17, 'little'))

if __name__ == '__main__':
    fire.Fire({
        "check": check,
    })

