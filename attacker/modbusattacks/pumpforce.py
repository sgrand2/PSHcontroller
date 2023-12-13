from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
import time
    

client = ModbusTcpClient('192.168.1.5', port=502)
#sensor_client = ModbusTcpClient(sensor_server, port=sensor_server_port)
client.connect()

while True:
    #for reg in range(1,10):
    #    rq = client.write_register(reg, random.randint(0,10))
    #rr = client.read_holding_registers(1,10)
    #print(rr.registers)
    #rq = client.write_coil(1, True)
    #rq = client.write_coil(1, True)
    client.write_coil(0x00, 1)
    #time.sleep(2)
    #rq = client.write_coil(1, False)
    time.sleep(2)

client.close()
