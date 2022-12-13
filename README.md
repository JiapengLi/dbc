# DBC

After involved in Car OBD area, I get to know about DBC (*DBC file is a proprietary format that describes the data over a CAN bus*). But the whole DBC thing is a kind of mess, you can only get something to work, but always not all. So I decide to develop this project to change it, the target of this project is to **open source a full functional DBC file to support ISO15031-4 and SAE J1979DA**. 

I hope to make it easy to design an OBD simulator for developers or even certification labs with the dbc file provided by this project.

Let's go!

## Features

- Full support **ISO15031-5-2015** & **SAE J1979DA-202203** 
  - J1979DA `Supported IDs 0x00` for ISO15031-5 `Service 01 - 0A`
  - Support 0x7DF message encoding
  - Support ISOTP message decoding (longer than 8)
- Mixed big endian and little endian encoding to make the dbc file more easier to read
- Auto generate dbc file from excel template (it is possible to generate other format database with minimum development)
- 

### Remark

- Service 01 PID13 and PID1D conflicts, use different variable name
- Service 01, 02 shares same PID definition, but service 02 need one extra `frame#` byte, which means DATA_x of Service 02 is 8 bits larger than Service 01.
- **String** fields parse is not supported by dbc file (let me know if it does), the dbc file here will decode string into **a very long integer** and a conversion is necessary to be done at application layer, although this feature should be be programming language independent, but I suspect language like C may not support such feature well (also could be implementation related). **cantools library just supports this feature fine.**
- Supported IDs map is not extracted by `libobdii.dbc`, it leaves to 

## ISO15031-5

### Diagnostic service definition for ISO 15765-4

| Service |   ID   | Comment                                                      | Development Status             |
| :-----: | :----: | ------------------------------------------------------------ | ------------------------------ |
|   01    |  PID   | Request current powertrain diagnostic data                   | Full Supported                 |
|   02    |  PID   | Request powertrain freeze frame data                         | Supported (without piggy-back) |
|   03    |  DTC   | Request emission-related diagnostic trouble codes (SAE J2012) | Supported (Max 30 DTCs)        |
|   04    |   -    | Clear/Reset emission-related diagnostic information. The purpose of this service is to provide a means for the external test equipment to command ECUs to clear all emission-related diagnostic information. | Full Supported                 |
|   05    |   -    | Service 05 is not supported for ISO 15765-4. The functionality of Service 05 16 is implemented in Service 06 . | Obsoleted                      |
|   06    |  MID   | Request on-board monitoring test results for specific monitored systems |                                |
|   07    |  DTC   | Request emission-related diagnostic trouble codes detected during current or last completed driving cycle |                                |
|   08    |  TID   | Request control of on-board system, test, or component       |                                |
|   09    | INFTYP | Request vehicle information                                  |                                |
|   0A    |  DTC   | Request emission-related diagnostic trouble codes with permanent status |                                |

*Service is also referred as **SID**.* 



## How to Use `libobdii.dbc`

### Service 03 DTC Parse

ISO15031-5-2015 example: `"\x08\x43\x06\x01\x43\x01\x96\x02\x34\x02\xCD\x03\x57\x0A\x24"` will be parsed into below options, `\x08` is just used to cheat on dbc parser library, it is a fake isotp header fill. `DTCNUM` should be used to traverse the valid value in dbc parsed message.

```
{
    "LEN": 8,
    "SID": "03",
    "DTCNUM": 6,
    "DTC0_TYPE": "P",
    "DTC0_VAL": 323,
    "DTC1_TYPE": "P",
    "DTC1_VAL": 406,
    "DTC2_TYPE": "P",
    "DTC2_VAL": 564,
    "DTC3_TYPE": "P",
    "DTC3_VAL": 717,
    "DTC4_TYPE": "P",
    "DTC4_VAL": 855,
    "DTC5_TYPE": "P",
    "DTC5_VAL": 2596,
    "DTC6_TYPE": "P",
    "DTC6_VAL": 0,
...
    "DTC29_TYPE": "P",
    "DTC29_VAL": 0
}
```



## DBC Specification

![J1939 EEC1 EngSpeed RPM CAN DBC File Database Format Message Signal](https://img.jiapeng.me/CAN-DBC-File-Format-Explained-Intro-Basics_2.png)

*Source: https://canlogger1000.csselectronics.com/img/CAN-DBC-File-Format-Explained-Intro-Basics_2.png*

### Cons

#### DBC Big Endian is Counterintuitive

J1979DA defines value which is longer than 8 bits through big endianess, this makes it necessary to use big endianess in dbc file to make it parse data correctly. However, I don't like the way how dbc spec to use big endian data, it is counterintuitive. Let me try to explain it a little bit. 

For an 8 bytes CAN message, ISO15031-5 defines it in a sequence like this `ISOTP HEADER, Service, PID, A, B, C, D, E`, and thus we can transform it to a very large data (64bits) like this:

![image-20221129144157483](https://img.jiapeng.me/image-20221129144157483.png)

You can see from above picture, the big endian format of a can message is not a true big endian, it is **big endian in byte sequence**, and **still little endian in bit sequence**. This makes big endian dbc SG_ hard to understand (and we can't by pass it).

For example :

| Field | Little Endian | Big Endian |
| ----- | ------------- | ---------- |
| PID   | `16|8@1+`     | `23|8@0+`  |
| A     | `24|8@1+`     | `31|8@0+`  |
| B     | `32|8@1+`     | `39|8@0+`  |
| AB    | N/A           | `31|16@0+` |
| BA    | `24|16@1+`    | N/A        |

You can see, a field in `AB` format is must be defined with big endian.

A real example, RPM dbc parser  looks like below:

**J1979DA Description:**

| SAE J1979/ ISO 15031-5 PID | Description | External test equipment SI (Metric) / English display | Data Byte | Min. Value | Max. Value     | Scaling/bit   | External test equipment SI (Metric) / English display | Comment                                                      |
| -------------------------- | ----------- | ----------------------------------------------------- | --------- | ---------- | -------------- | ------------- | ----------------------------------------------------- | ------------------------------------------------------------ |
| 0x0C                       | Engine RPM  | RPM                                                   | A,B       | 0 min-1    | 16383.75 min-1 | ¼ rpm per bit | RPM: xxxxx min-1                                      | Engine RPM shall display revolutions per minute of the engine crankshaft. |

**DBC SG_:**

```
 SG_ RPM m12 : 31|16@0+ (0.25,0) [0|0] "rpm" TOOL
```

#### Limited Data Types

DBC SG_ can support number based types like int / float (double) / enum.

DBC SG_ doesn't support **string** or **array** (list) format.

#### Fixed length message

DBC BO_ expected a fixed length message? It is not good if so.

## Development

Generate dbc file:

```
python3 util/dbc.py gen dbc.xlsx > libobdii.dbc
```

dbc file verification:

```
python3 util/dbc.py check libobdii.dbc
```

## Acknowledgement

### Projects

This project refers or reuses below projects, thanks to all these projects' maintainers!

- https://github.com/cantools/cantools
- https://github.com/kdschlosser/vector_dbc
- https://github.com/commaai/opendbc
- https://www.csselectronics.com/pages/obd2-dbc-file
- VS Code DBC Language Syntax by Landon Harris

### Documentations

- http://mcu.so/Microcontroller/Automotive/DBC_File_Format_Documentation.pdf
- http://socialledge.com/sjsu/index.php/DBC_Format
- https://github.com/stefanhoelzl/CANpy/blob/master/docs/DBC_Specification.md

