import json, time
import fire

import cantools
from pprint import pprint

import pandas as pd
import numpy as np

def fmt(msg):
    return msg + (64 - len(msg)) * b'\x00'

def tree(dbcfile):
    db = cantools.database.load_file(dbcfile)
    pprint(db.messages)
    for m in db.messages:
        # print(m.__dict__)
        # example_message = db.get_message_by_name('RX')
        pprint(m.signals)
        pprint(m.signal_tree)

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
    print(type(msg['VIN']))

    pprint(int.to_bytes(msg['VIN'], 17, 'little'))

    msg = db.decode_message(0x7E8, fmt(b"\x08\x41\x01\xFF\xF0\xFF\xFF\xAA"))
    pprint(msg)

    msg = db.decode_message(0x7E8, fmt(b"\x08\x41\x02\x00\x01\xFF\xFF\xAA"))
    pprint(msg)

    msg = db.decode_message(0x7E8, fmt(b"\x08\x41\x03\x00\x01\xFF\xFF\xAA"))
    pprint(msg)

    msg = db.decode_message(0x7E8, fmt(b"\x08\x41\x0E\x80\x01\xFF\xFF\xAA"))
    pprint(msg)
    msg = db.decode_message(0x7E8, fmt(b"\x08\x41\x0E\x7F\x01\xFF\xFF\xAA"))
    pprint(msg)
    msg = db.decode_message(0x7E8, fmt(b"\x08\x41\x0E\x00\x01\xFF\xFF\xAA"))
    pprint(msg)

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

BO_ 2024 RX: 64 ECU
 SG_ RXLEN : 0|8@1+ (1,0) [0|0] "" TOOL
 SG_ SERVICE M : 8|4@1+ (1,0) [0|0] "" TOOL
 SG_ RXACK : 12|4@1+ (1,0) [0|0] "" TOOL'''

def val2str(v):
    fstr = f"{float(v):.15f}"
    if '.' not in fstr:
        return fstr
    return fstr.rstrip('0').rstrip('.')

def gen_Sxx_PID():
    SG_ = ""
    SG_MUL_VAL_ = ""
    for i in range(1, 11):
        service = i
        name = f"S{service:02X}_PID"
        sg_ = f' SG_ {name} m{service}M : 16|8@1+ (1,0) [0|0] "" TOOL'
        SG_ += f'{sg_}\n'
        sg_mul_val = f'SG_MUL_VAL_ 2024 {name} SERVICE {service}-{service};'
        SG_MUL_VAL_ += f'{sg_mul_val}\n'
    return SG_, SG_MUL_VAL_

def gen_sid():
    SG_ = ""
    SG_MUL_VAL_ = ""
    for i in range(70):
        service = i % 10 + 1
        pid = 32 * (i // 10)
        name = f'S{service:02X}_PID{pid:02X}_SupportedIDs_{pid + 1:02X}_{pid + 32:02X}'
        sg_ = f' SG_ {name} m{pid} : 24|32@1+ (1,0) [0|0] "" TOOL'
        SG_ += f'{sg_}\n'
        sg_mul_val = f'SG_MUL_VAL_ 2024 {name} S{service:02X}_PID {pid}-{pid};'
        SG_MUL_VAL_ += f'{sg_mul_val}\n'
    return SG_, SG_MUL_VAL_

def gen_pid(service, dfpid):
    SG_ = ""
    SG_MUL_VAL_ = ""
    name_prefix = "" if service == 1 else f"S{service:02X}_"
    for i, row in dfpid.iterrows():
        if pd.isna(row['short_name']):
            continue
        mux_value = row['mux_value']
        mux_value_trim = str(mux_value).replace("M","")

        mux_name = f"{name_prefix}{row['mux_name']}" if not pd.isna(row['mux_name']) else f"S{service:02X}_PID"
        name = f"{name_prefix}{row['short_name']}"

        start = int(row['start'])
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

def gen(dbfile):
    # dfsid = pd.read_excel(dbfile, "SID")
    dfpid = pd.read_excel(dbfile, "PID")
    dfitid = pd.read_excel(dbfile, "ITID")

    SG_, SG_MUL_VAL_ = "", ""

    # service & pid multiplexor
    sg_, sg_mul_val_ = gen_Sxx_PID()
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_

    # service 01 - 0A, Supported IDs
    sg_, sg_mul_val_ = gen_sid()
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_

    # service 01, Parameter IDs
    sg_, sg_mul_val_ = gen_pid(1, dfpid)
    SG_ += sg_
    SG_MUL_VAL_ += sg_mul_val_

    print(DBCHEADER)
    print(SG_)

    print(SG_MUL_VAL_)

    return

    index = 'SG_'
    for df in dfs:
        for i, row in df.iterrows():
            if pd.isna(row[index]):
                continue
            print(row[index])

    print(DBC_SG_MUL_VAL_HEADER)
    index = 'SG_MUL_VAL_'
    for df in dfs:
        for i, row in df.iterrows():
            if pd.isna(row[index]):
                continue
            print(row[index])

if __name__ == '__main__':
    fire.Fire({
        "check": check,
        "gen": gen,
        "tree": tree,
        "test": gen_Sxx_PID,
    })

