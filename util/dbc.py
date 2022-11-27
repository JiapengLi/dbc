import json, time
import fire

import cantools
from pprint import pprint

import pandas as pd

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
 SG_ RXACK : 12|4@1+ (1,0) [0|0] "" TOOL
 SG_ S01_PID m1M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S02_PID m2M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S03_PID m3M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S04_PID m4M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S05_PID m5M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S06_PID m6M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S07_PID m7M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S08_PID m8M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S09_PID m9M : 16|8@1+ (1,0) [0|0] "" TOOL
 SG_ S0A_PID m10M : 16|8@1+ (1,0) [0|0] "" TOOL'''

DBC_SG_MUL_VAL_HEADER='''SG_MUL_VAL_ 2024 S01_PID SERVICE 1-1;
SG_MUL_VAL_ 2024 S02_PID SERVICE 2-2;
SG_MUL_VAL_ 2024 S03_PID SERVICE 3-3;
SG_MUL_VAL_ 2024 S04_PID SERVICE 4-4;
SG_MUL_VAL_ 2024 S05_PID SERVICE 5-5;
SG_MUL_VAL_ 2024 S06_PID SERVICE 6-6;
SG_MUL_VAL_ 2024 S07_PID SERVICE 7-7;
SG_MUL_VAL_ 2024 S08_PID SERVICE 8-8;
SG_MUL_VAL_ 2024 S09_PID SERVICE 9-9;
SG_MUL_VAL_ 2024 S0A_PID SERVICE 10-10;'''

def gen(dbfile):
    dfsid = pd.read_excel(dbfile, "dbcsid")
    dfgen = pd.read_excel(dbfile, "dbcgen")
    dfs = [dfsid, dfgen]

    print(DBCHEADER)
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
    })

