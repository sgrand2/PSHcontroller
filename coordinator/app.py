import datetime as dt

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse


def setup():
    sensor_client = ModbusTcpClient("192.168.0.3", port=502)
    gate_client = ModbusTcpClient("192.168.0.4", port=502)
    pump_client = ModbusTcpClient("192.168.0.5", port=502)

    sensor_client.connect()
    gate_client.connect()
    pump_client.connect()

    return [sensor_client, gate_client, pump_client]


def teardown(clients):
    clients[1].write_coil(0x00, 0)
    clients[2].write_coil(0x00, 0)
    for c in clients:
        c.close()


def main():
    clients = setup()

    try:

        # poll in loop and set values in loop (mindful of day.night cycles; this is PSH after all)
        while True:
        
            # for now make every even minute represent daytime and every odd minute represent nighttime
            is_day = dt.datetime.now().minute % 2 == 0

            try:
                sr = clients[0].read_discrete_inputs(0x00)
            except ModbusException as e:
                print(f"ERROR: {e}")
                teardown(clients)
                exit(1)

            if sr.isError():
                print(f"ERROR: modbus library error: {sr}")
                teardown(clients)
                exit(1)

            if isinstance(sr, ExceptionResponse):
                print(f"ERROR: modbus error response: {sr}")
                teardown(clients)
                exit(1)

            water_level_high = sr.bits[0] == 1
            if is_day:
                # open gate, stop pump
                gate_client.write_coil(0x00, 1)
                pump_client.write_coil(0x00, 0)

            elif not is_day and not water_level_high:
                # close gate, run pump
                gate_client.write_coil(0x00, 0)
                pump_client.write_coil(0x00, 1)

            else: #(not day and water level is high)
                # close gate, stop pump
                gate_client.write_coil(0x00, 0)
                pump_client.write_coil(0x00, 0)

    finally:
        teardown(clients)
