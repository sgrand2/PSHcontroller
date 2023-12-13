tshark -i any -f "tcp port 502" -Y "modbus.func_code == 0x05"
