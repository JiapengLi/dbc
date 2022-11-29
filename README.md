# DBC

After involved in Car OBD area, I get to know about DBC (DBC file is a proprietary format that describes the data over a CAN bus). But the whole DBC thing is a kind of mess, you can only get something to work, but indeed not all. So I decide to change it, the target of this project is to **open source a full functional DBC file to support ISO15031-4 and J1979DA**. 

I hope to make it easy to design an OBD simulator for developers or even certification labs with the dbc file provided by this project.

Let's go!

## Features

- [ ] Support ISOTP message encoding and decoding (longer than 8)
- [ ] Full support **ISO15031-5-2015** & **J1979DA-202203** 
  - [ ]  J1979DA `Supported IDs 0x00` for ISO15031-5 `Service 01 - 0A`
- [ ] Mixed big endian and little endian encoding to make the dbc file more easier to read
- [ ] Auto generate dbc file from excel template (it is possible to generate other format database with minimum development)
- [ ] 

### Remark

- Service 01 PID13 and PID1D conflicts, use different variable name
- Service 01, 02 shares same PID definition, but service 02 need one extra `frame#` byte, which means DATA_x of Service 02 is 8 bits larger than Service 01
- 



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

DBC SG_ doesn't support string or array (list) format.

#### Fixed length message

DBC BO_ expected a fixed length message? It is not good if so.



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

