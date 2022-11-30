import json, time
import fire

import cantools
from pprint import pprint

import pandas as pd
import numpy as np

def padding(msg):
    return msg + (64 - len(msg)) * b'\x00'

def val2str(v):
    fstr = f"{float(v):.15f}"
    if '.' not in fstr:
        return fstr
    return fstr.rstrip('0').rstrip('.')

DBCHEADER='''VERSION "v0.0.1"


NS_ :
	NS_DESC_
	CM_
	BA_DEF_
	BA_
	VAL_
	CAT_DEF_
	CAT_
	FILTER
	BA_DEF_DEF_
	EV_DATA_
	ENVVAR_DATA_
	SGTYPE_
	SGTYPE_VAL_
	BA_DEF_SGTYPE_
	BA_SGTYPE_
	SIG_TYPE_REF_
	VAL_TABLE_
	SIG_GROUP_
	SIG_VALTYPE_
	SIGTYPE_VALTYPE_
	BO_TX_BU_
	BA_DEF_REL_
	BA_REL_
	BA_DEF_DEF_REL_
	BU_SG_REL_
	BU_EV_REL_
	BU_BO_REL_
	SG_MUL_VAL_

BS_:

BU_:
'''

DBC_BO_7E8='''
BO_ 2024 RX: 64 ECU
 SG_ LEN : 0|8@1+ (1,0) [0|0] "" TOOL
 SG_ SID M : 8|8@1+ (1,0) [0|0] "" TOOL'''

DBC_BO_7DF='''
BO_ 2015 TX: 8 TOOL
 SG_ LEN : 0|8@1+ (1,0) [0|0] "" TOOL
 SG_ SID M : 8|8@1+ (1,0) [0|0] "" TOOL
 SG_ PID m1 : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ MID m6 : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ TID m8 : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ ITID m9 : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ RESERVED m3 : 24|8@1+ (1,0) [0|0] "" TOOL
 SG_ FRMNO m2 : 24|8@1+ (1,0) [0|0] "" TOOL

SG_MUL_VAL_ 2015 PID SID 1-1, 2-2;
SG_MUL_VAL_ 2015 MID SID 6-6;
SG_MUL_VAL_ 2015 TID SID 8-8;
SG_MUL_VAL_ 2015 ITID SID 9-9;
SG_MUL_VAL_ 2015 RESERVED SID 3-3, 4-4, 7-7, 10-10;
SG_MUL_VAL_ 2015 FRMNO SID 2-2;

VAL_ 2015 SID 1 "current data" 2 "freeze data" 3 "DTC" 4 "clear DTC" 5 "oxygen sensor monitoring test results" 6 "on-board monitoring test results" 7 "pending DTC" 8 "Request control of on-board system, test, or component" 9 "vehicle information" 10 "permanent DTC";'''

SUPPORTED_IDS_NAME = {
    1: "PID",
    2: "PID",
    6: "MID",
    8: "TID",
    9: "ITID",
}

def gen_Sxx_xID():
    SG_, SG_MUL_VAL_, VAL_ = "", "", ""
    val_ = ""
    for i in range(1, 11):
        service = i
        sid = service+0x40
        val_ += f' {sid} "{service:02X}" {service} "{service:02X}"'
        if service not in SUPPORTED_IDS_NAME.keys():
            continue
        idname = SUPPORTED_IDS_NAME[service]
        name = f"S{service:02X}_{idname}"
        sg_ = f' SG_ {name} m{service}M : 16|8@1+ (1,0) [0|0] "" TOOL'
        SG_ += f'{sg_}\n'
        sg_mul_val = f'SG_MUL_VAL_ 2024 {name} SID {sid}-{sid};'
        SG_MUL_VAL_ += f'{sg_mul_val}\n'

    VAL_ += f'VAL_ 2024 SID{val_} 127 "SIDNR";\n'

    return SG_, SG_MUL_VAL_, VAL_

def gen_supported_id():
    SG_, SG_MUL_VAL_, VAL_ = "", "", ""

    for i in range(70):
        service = i % 10 + 1
        id = 32 * (i // 10)

        if service not in SUPPORTED_IDS_NAME.keys():
            continue
        idname = SUPPORTED_IDS_NAME[service]
        name = f'S{service:02X}_{idname}{id:02X}_SupportedIDs_{id + 1:02X}_{id + 32:02X}'
        sg_ = f' SG_ {name} m{id} : 24|32@1+ (1,0) [0|0] "" TOOL'
        SG_ += f'{sg_}\n'
        sg_mul_val = f'SG_MUL_VAL_ 2024 {name} S{service:02X}_{idname} {id}-{id};'
        SG_MUL_VAL_ += f'{sg_mul_val}\n'
    return SG_, SG_MUL_VAL_

def gen_service(service, dfpid, prefix=False):
    SG_, SG_MUL_VAL_, VAL_ = "", "", ""

    name_prefix = "" if service == 1 or not prefix else f"S{service:02X}_"
    start_oft = 0

    if service == 2:
        SG_ += f' SG_ FRNO m2 : 24|8@1+ (1,0) [0|0] "" TOOL\n'
        SG_MUL_VAL_ += "SG_MUL_VAL_ 2024 FRNO S02_PID 1-31, 33-63, 65-95, 97-127, 129-159, 161-191, 193-255;\n"
        start_oft = 8

    for i, row in dfpid.iterrows():
        if pd.isna(row['short_name']):
            continue
        mux_value = row['mux_value']
        mux_value_trim = str(mux_value).replace("M","")

        idname = SUPPORTED_IDS_NAME[service]
        mux_name = f"{name_prefix}{row['mux_name']}" if not pd.isna(row['mux_name']) else f"S{service:02X}_{idname}"
        name = f"{name_prefix}{row['short_name']}"

        start = int(row['start'])
        if start >= 24:
            start += start_oft

        bits = int(row['bits'])
        endian = int(row['endian'])
        sign = row['sign']
        scale = val2str(row['scale'])
        unit = row['unit'] if not pd.isna(row['unit']) else ""

        offset = val2str(row['offset'])
        min = val2str(row['min'])
        max = val2str(row['max'])
        #  SG_ DTC_CNT m1 : 24|7@1+ (1,0) [0|0] "" TOOL

        sg_ = f' SG_ {name} m{mux_value} : {start}|{bits}@{endian}{sign} ({scale},{offset}) [{min}|{max}] "{unit}" TOOL'
        SG_ += f'{sg_}\n'

        sg_mul_val = f'SG_MUL_VAL_ 2024 {name} {mux_name} {mux_value_trim}-{mux_value_trim};'
        SG_MUL_VAL_ += f'{sg_mul_val}\n'
    return SG_, SG_MUL_VAL_

def gen_dtc(service):
    SG_, SG_MUL_VAL_, VAL_ = "", "", ""
    sid = 3 + 0x40
    SG_ += f' SG_ DTCNUM m{sid} : 16|8@1+ (1,0) [0|0] "" TOOL\n'
    SG_MUL_VAL_ += f"SG_MUL_VAL_ 2024 DTCNUM SID {sid}-{sid};\n"

    oft = 31
    for i in range(0, 30):
        mux_value = sid
        mux_value_trim = str(mux_value).replace("M","")
        mux_name = "SID"

        endian = 0
        sign = '+'
        scale = 1
        unit = ""
        offset = 0
        min = 0
        max = 0

        name = f"DTC{i}_TYPE"
        start = oft + i * 16
        bits = 2
        sg_ = f' SG_ {name} m{mux_value} : {start}|{bits}@{endian}{sign} ({scale},{offset}) [{min}|{max}] "{unit}" TOOL'
        SG_ += f'{sg_}\n'
        sg_mul_val = f'SG_MUL_VAL_ 2024 {name} {mux_name} {mux_value_trim}-{mux_value_trim};'
        SG_MUL_VAL_ += f'{sg_mul_val}\n'
        val_ = f'VAL_ 2024 {name} 0 "P" 1 "C" 2 "B" 3 "U" ;'
        VAL_ += f"{val_}\n"

        name = f"DTC{i}_VAL"
        start = oft + i * 16 - 2
        bits = 14
        sg_ = f' SG_ {name} m{mux_value} : {start}|{bits}@{endian}{sign} ({scale},{offset}) [{min}|{max}] "{unit}" TOOL'
        SG_ += f'{sg_}\n'
        sg_mul_val = f'SG_MUL_VAL_ 2024 {name} {mux_name} {mux_value_trim}-{mux_value_trim};'
        SG_MUL_VAL_ += f'{sg_mul_val}\n'

    return SG_, SG_MUL_VAL_, VAL_

def gen_negative_response():
    SG_, SG_MUL_VAL_, VAL_ = "", "", ""
    sid = 0x7F
    SG_ += f' SG_ SIDRQ m{sid} : 16|8@1+ (1,0) [0|0] "" TOOL\n'
    SG_MUL_VAL_ += f"SG_MUL_VAL_ 2024 SIDRQ SID {sid}-{sid};\n"

    SG_ += f' SG_ RC m{sid} : 24|8@1+ (1,0) [0|0] "" TOOL\n'
    SG_MUL_VAL_ += f"SG_MUL_VAL_ 2024 RC SID {sid}-{sid};\n"
    val_ = f'VAL_ 2024 RC 33 "BRR" 34 "CNCORSE" 120 "RCR-RP" ;'
    VAL_ += f"{val_}\n"

    return SG_, SG_MUL_VAL_, VAL_

def gen(dbfile):
    # dfsid = pd.read_excel(dbfile, "SID")
    dfpid = pd.read_excel(dbfile, "PID")
    dfitid = pd.read_excel(dbfile, "ITID")

    SG_, SG_MUL_VAL_, VAL_ = "", "", ""

    # All services & pids multiplexor
    sg_, sg_mul_val_, val_ = gen_Sxx_xID()
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_
    VAL_ += val_

    # All services Supported IDs
    sg_, sg_mul_val_ = gen_supported_id()
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_

    # Negative response message format
    sg_, sg_mul_val_, val_ = gen_negative_response()
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_
    VAL_ += val_

    # service 01, Parameter IDs (PID)
    sg_, sg_mul_val_ = gen_service(1, dfpid, prefix=False)
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_

    # service 02, Parameter IDs (PID)
    sg_, sg_mul_val_ = gen_service(2, dfpid, prefix=True)
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_

    sg_, sg_mul_val_, val_ = gen_dtc(3)
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_
    VAL_ += val_

    # service 09, ITID
    sg_, sg_mul_val_ = gen_service(9, dfitid, prefix=False)
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_

    # dbc file header
    print(DBCHEADER)

    # BO_ 0x7DF
    print(DBC_BO_7DF)

    # BO_ 0x7E8
    print(DBC_BO_7E8)
    print(SG_)
    print(SG_MUL_VAL_)
    print(VAL_)


def gentx(dbfile):
    # dbc file header
    print(DBCHEADER)

    # BO_ 0x7E8
    print(DBC_BO_7DF)


def check_encode(db):
    print("encode by value:")
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": 1, "PID": 0x10, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 3, "SID": 2, "PID": 0x20, "FRMNO": 0, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 1, "SID": 3, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 1, "SID": 4, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": 6, "MID": 0x60, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 1, "SID": 7, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": 8, "TID": 0x80, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": 9, "ITID": 0x90, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": 10, }, strict=False)
    print(msg.hex())

    print()

    print("encode by name:")
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": "current data", "PID": 0x10, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 3, "SID": "freeze data", "PID": 0x20, "FRMNO": 0, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 1, "SID": "DTC", }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 1, "SID": "oxygen sensor monitoring test results", }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": "on-board monitoring test results", "MID": 0x60, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 1, "SID": "pending DTC", }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": "Request control of on-board system, test, or component", "TID": 0x80, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": "vehicle information", "ITID": 0x90, }, strict=False)
    print(msg.hex())
    msg = db.encode_message(0x7DF, {"RESERVED": 0, "LEN": 2, "SID": "permanent DTC", }, strict=False)
    print(msg.hex())

def check_decode(db):
    # db.get_message_
    msg = db.decode_message(0x7E8, padding(b"\x08\x41\x00\xFF\xFF\xFF\xFF\xAA"))
    pprint(msg)

    msg = db.decode_message(0x7E8, padding(b"\x08\x42\x00\xFF\xF0\xFF\xFF\xAA"))
    pprint(msg)

    msg = db.decode_message(0x7E8, padding(bytes.fromhex('14490201335657524136394d37344d303333393135')))
    print(msg)
    print(f"VIN: {int.to_bytes(msg['VIN'], 17, 'little').decode('utf-8')}")

    msg = db.decode_message(0x7E8, padding(b"\x08\x41\x01\x81\x07\xEF\x63\xAA"))
    print(msg)

    msg = db.decode_message(0x7E8, padding(b"\x08\x41\x19\xA0\x78\xEF\x63\xAA"))
    print(msg)

    msg = db.decode_message(0x7E8, padding(b"\x08\x42\x02\x00\x01\x30\xFF\xAA"))
    print(msg)

    msg = db.decode_message(0x7E8, padding(b"\x08\x43\x02\x00\x00\x00\xFF\x40\x00\x00\x01"))
    print(msg)

    msg = db.decode_message(0x7E8, padding(b"\x08\x43\x06\x01\x43\x01\x96\x02\x34\x02\xCD\x03\x57\x0A\x24"))
    print(msg)
    print(type(msg))
    # print(json.dumps(msg, indent=4))


    msg = db.decode_message(0x7E8, padding(b"\x08\x7F\x04\x22\x01\xFF\xFF\xAA"))
    print(msg)
    # msg = db.decode_message(0x7E8, padding(b"\x08\x41\x0E\x7F\x01\xFF\xFF\xAA"))
    # pprint(msg)
    # msg = db.decode_message(0x7E8, padding(b"\x08\x41\x0E\x00\x01\xFF\xFF\xAA"))
    # pprint(msg)

def check(dbcfile):
    db = cantools.database.load_file(dbcfile)
    pprint(db.messages)
    for m in db.messages:
        # print(m.__dict__)
        # example_message = db.get_message_by_name('RX')
        pprint(m.signals)

    # 0x7E8
    check_decode(db)

    # 0x7DF
    check_encode(db)

def checktx(dbcfile):
    db = cantools.database.load_file(dbcfile)
    pprint(db.messages)
    for m in db.messages:
        pprint(m.signals)
    check_encode(db)


def tree(dbcfile):
    db = cantools.database.load_file(dbcfile)
    pprint(db.messages)
    for m in db.messages:
        # print(m.__dict__)
        # example_message = db.get_message_by_name('RX')
        pprint(m.signals)
        pprint(m.signal_tree)

if __name__ == '__main__':
    fire.Fire({
        "check": check,
        "gen": gen,
        "gentx": gentx,
        "tree": tree,
        "test": checktx,
    })

