# DBC

After involved in Car OBD area, I get to know about DBC (DBC file is a proprietary format that describes the data over a CAN bus). But the whole DBC thing is a kind of mess, you can only get something to work, but indeed not all. So I decide to change it, the target of this project is to **open source a full functional DBC file to support ISO15031-4 and J1979DA**. 

Let's go!

## Features

- [ ] Support ISOTP message encoding and decoding (longer than 8)
- [ ] Full support **ISO15031-5** & **J1979DA** 
  - [ ]  J1979DA `Supported IDs 0x00` for ISO15031-5 `Service 01 - 0A`
- [ ] 

With the help of this project, I hope to make it easy to design an OBD simulator for developer or even certification libraries.

## About DBC Specification



![File:Screenshot 2015-11-22 16.02.04.png](https://img.jiapeng.me/800px-Screenshot_2015-11-22_16.02.04.png)



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

