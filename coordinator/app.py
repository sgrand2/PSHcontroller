import logging
import datetime as dt
import threading

import click
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse


def setup(sensor_server, sensor_server_port, gate_server, gate_server_port, pump_server, pump_server_port):
    logging.debug("setting up modbus relay server clients")
    sensor_client = ModbusTcpClient(sensor_server, port=sensor_server_port)
    gate_client = ModbusTcpClient(gate_server, port=gate_server_port)
    pump_client = ModbusTcpClient(pump_server, port=pump_server_port)

    sensor_client.connect()
    gate_client.connect()
    pump_client.connect()

    return [sensor_client, gate_client, pump_client]


def teardown(clients):
    logging.debug("cleaning up modbus relay server clients")
    clients[1].write_coil(0x00, 0)
    clients[2].write_coil(0x00, 0)
    for c in clients:
        c.close()


def run_control_loop(sensor_server, sensor_server_port, gate_server, gate_server_port, pump_server, pump_server_port):
    clients = setup(sensor_server, sensor_server_port, gate_server, gate_server_port, pump_server, pump_server_port)
    previous_action = 0

    try:

        # poll in loop and set values in loop (mindful of day.night cycles; this is PSH after all)
        while True:
            import time
            time.sleep(1)

            # for now make every even minute represent daytime and every odd minute represent nighttime
            is_day = dt.datetime.now().minute % 2 == 0

            try:
                sr = clients[0].read_discrete_inputs(0x00)
            except ModbusException as e:
                logging.critical(f"{e}")
                teardown(clients)
                exit(1)

            if sr.isError():
                logging.critical(f"modbus library error: {sr}")
                teardown(clients)
                exit(1)

            if isinstance(sr, ExceptionResponse):
                logging.critical(f"modbus error response: {sr}")
                teardown(clients)
                exit(1)

            water_level_high = sr.bits[0] == 1
            if is_day:
                # open gate, stop pump
                if previous_action == 1:
                    logging.debug("(DAY, ___) --> opening gate, stopping pump")
                else:
                    logging.info("(DAY, ___) --> opening gate, stopping pump")
                clients[1].write_coil(0x00, 1)
                clients[2].write_coil(0x00, 0)
                previous_action = 1

            elif not is_day and not water_level_high:
                # close gate, run pump
                if previous_action == 2:
                    logging.debug("(NIGHT, LOW) --> closing gate, starting pump")
                else:
                    logging.info("(NIGHT, LOW) --> closing gate, starting pump")
                clients[1].write_coil(0x00, 0)
                clients[2].write_coil(0x00, 1)
                previous_action = 2

            else: #(not day and water level is high)
                # close gate, stop pump
                if previous_action == 3:
                    logging.debug("(NIGHT, HIGH) --> closing gate, stopping pump")
                else:
                    logging.info("(NIGHT, HIGH) --> closing gate, stopping pump")
                clients[1].write_coil(0x00, 0)
                clients[2].write_coil(0x00, 0)
                previous_action = 3

    finally:
        teardown(clients)



@click.command()
@click.option("--log", "-l", default="info", help="The log level to use when sending logs to stdout (default: INFO; options: DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option("--sensor-server", "-ss", default="192.168.0.3", help="The address of the Modbus/TCP server to query for water level sensor state (default: 192.168.0.3)")
@click.option("--sensor-server-port", "-sp", default=502, help="The port to direct Modbus traffic to for the water level sensor server (default: 502)")
@click.option("--gate-server", "-gs", default="192.168.0.4", help="The address of the Modbus/TCP server to manipulate the water gate state (default: 192.168.0.4)")
@click.option("--gate-server-port", "-gp", default=502, help="The port to direct Modbus traffic to for the water level sensor server (default: 502)")
@click.option("--pump-server", "-ps", default="192.168.0.5", help="The address of the Modbus/TCP server to manipulate the water pump state (default: 192.168.0.5)")
@click.option("--pump-server-port", "-pp", default=502, help="The port to direct Modbus traffic to for the water level sensor server (default: 502)")
@click.option("--hmi-host", "-ha", default="0.0.0.0", help="The address to use when creating a socket for the HMI (default: 0.0.0.0)")
@click.option("--hmi-port", "-hp", default=80, help="The port to use when creating a socket for the HMI (default: 80)")
def main(**args):
    # set up logging
    log_level = getattr(logging, args['log'].upper())
    logging.basicConfig(level=log_level)
    logging.info(f"logging level set to {args['log'].upper()}")

    # start constituent threads
    control_loop_thread = threading.Thread(target=run_control_loop, args=(args['sensor_server'], args['sensor_server_port'], args['gate_server'], args['gate_server_port'], args['pump_server'], args['pump_server_port']))
    control_loop_thread.start()

    control_loop_thread.join()


if __name__ == "__main__":
    main()
