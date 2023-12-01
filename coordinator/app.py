import logging
import threading
import datetime as dt
from pathlib import Path

import click
from flask import Flask, send_from_directory, request
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse


app = Flask("coordinator")
HMI_ROOT = '/opt/csci498/hmi'


# thread-safe variables for state sharing
manualControlEvent = threading.Event()
isDayEvent = threading.Event()
waterLevelHighEvent = threading.Event()
gateOpenEvent = threading.Event()
pumpOnEvent = threading.Event()

manualTargetGateOpenEvent = threading.Event()
manualTargetPumpOnEvent = threading.Event()


@app.route("/update")
def flask_update():
    # get management style
    if manualControlEvent.is_set():
        manualControl = 1
    else:
        manualControl = 0

    # get time of day
    if isDayEvent.is_set():
        timeOfDay = 1
    else:
        timeOfDay = 0

    # get water level state
    if waterLevelHighEvent.is_set():
        waterLevelHigh = 1
    else:
        waterLevelHigh = 0

    # get gate state
    if gateOpenEvent.is_set():
        gateOpen = 1
    else:
        gateOpen = 0

    # get pump state
    if pumpOnEvent.is_set():
        pumpOn = 1
    else:
        pumpOn = 0

    return {
        "manualControl": manualControl,
        "timeOfDay": timeOfDay,
        "waterLevelHigh": waterLevelHigh,
        "gateOpen": gateOpen,
        "pumpOn": pumpOn
    }


@app.route("/manual", methods=['POST'])
def flask_manual():

    # update mode if provided
    new_mode = request.args.get('m')
    if new_mode == '1':
        logging.warning("changing to manual control mode")
        manualControlEvent.set()

        # sync current state w/ target state to avoid leftovers of previous manual control targets
        if gateOpenEvent.is_set():
            manualTargetGateOpenEvent.set()
        else:
            manualTargetGateOpenEvent.clear()
        
        if pumpOnEvent.is_set():
            manualTargetPumpOnEvent.set()
        else:
            manualTargetPumpOnEvent.clear()

    elif new_mode == '0':
        logging.info("changing to automatic control mode")
        manualControlEvent.clear()

    if manualControlEvent.is_set():

        # update gate status if provided
        new_gate_state = request.args.get('g')
        if new_gate_state == '1':
            logging.info("received manual mode request to open gate")
            manualTargetGateOpenEvent.set()
        elif new_gate_state == '0':
            logging.info("received manual mode request to close gate")
            manualTargetGateOpenEvent.clear()

        # update pump status if provided
        new_pump_state = request.args.get('p')
        if new_pump_state == '1':
            logging.info("received manual mode request to start pump")
            manualTargetPumpOnEvent.set()
        elif new_pump_state == '0':
            logging.info("received manual mode request to stop pump")
            manualTargetPumpOnEvent.clear()

    return ('', 204)


@app.route("/")
@app.route("/<path:build_file>")
def flask_react_root(build_file="index.html"):
    return send_from_directory(HMI_ROOT, build_file)


@app.route("/static/js/<path:build_file>")
def flask_react_js(build_file="index.html"):
    return send_from_directory(Path(HMI_ROOT)/"static/js", build_file)


@app.route("/static/css/<path:build_file>")
def flask_react_css(build_file="index.html"):
    return send_from_directory(Path(HMI_ROOT)/"static/css", build_file)


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


def set_pump(state_on, clients):
    if state_on is True and not pumpOnEvent.is_set():
        clients[2].write_coil(0x00, 1)
        pumpOnEvent.set()
    elif state_on is False and pumpOnEvent.is_set():
        clients[2].write_coil(0x00, 0)
        pumpOnEvent.clear()


def set_gate(state_open, clients):
    if state_open is True and not gateOpenEvent.is_set():
        clients[1].write_coil(0x00, 1)
        gateOpenEvent.set()
    elif state_open is False and gateOpenEvent.is_set():
        clients[1].write_coil(0x00, 0)
        gateOpenEvent.clear()


def automatic_control_logic(is_day, water_level_high, previous_action, clients):
    if is_day:
        # open gate, stop pump
        if previous_action == 1:
            logging.debug("(DAY, ___) --> opening gate, stopping pump")
        else:
            logging.info("(DAY, ___) --> opening gate, stopping pump")

        # manipulate relays
        set_gate(True, clients)
        set_pump(False, clients)

        return 1

    elif not is_day and not water_level_high:
        # close gate, run pump
        if previous_action == 2:
            logging.debug("(NIGHT, LOW) --> closing gate, starting pump")
        else:
            logging.info("(NIGHT, LOW) --> closing gate, starting pump")

        # manipulate relays
        set_gate(False, clients)
        set_pump(True, clients)

        return 2

    else: #(not day and water level is high)
        # close gate, stop pump
        if previous_action == 3:
            logging.debug("(NIGHT, HIGH) --> closing gate, stopping pump")
        else:
            logging.info("(NIGHT, HIGH) --> closing gate, stopping pump")

        # manipulate relays
        set_gate(False, clients)
        set_pump(False, clients)

        return 3


def manual_control_logic(clients):
    if manualTargetGateOpenEvent.is_set():
        set_gate(True, clients)
    else:
        set_gate(False, clients)

    if manualTargetPumpOnEvent.is_set():
        set_pump(True, clients)
    else:
        set_pump(False, clients)


def update_thread_variables(clients):
    # for now make every even minute represent daytime and every odd minute represent nighttime
    if dt.datetime.now().minute % 2 == 0:
        isDayEvent.set()
    else:
        isDayEvent.clear()

    # update water level status
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

    if sr.bits[0] == 1:
        waterLevelHighEvent.set()
    else:
        waterLevelHighEvent.clear()

    # update gate status
    try:
        sr = clients[1].read_coils(0x00)
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

    if sr.bits[0] == 1:
        gateOpenEvent.set()
    else:
        gateOpenEvent.clear()

    # update pump status
    try:
        sr = clients[2].read_coils(0x00)
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

    if sr.bits[0] == 1:
        pumpOnEvent.set()
    else:
        pumpOnEvent.clear()


def run_control_loop(sensor_server, sensor_server_port, gate_server, gate_server_port, pump_server, pump_server_port):
    clients = setup(sensor_server, sensor_server_port, gate_server, gate_server_port, pump_server, pump_server_port)
    previous_action = 0

    try:

        # poll in loop and set values in loop (mindful of day.night cycles; this is PSH after all)
        while True:
            import time
            time.sleep(1)

            # update current state
            update_thread_variables(clients)

            # flip between manual and automatic control
            is_day = 1 if isDayEvent.is_set() else 0
            water_level_high = 1 if waterLevelHighEvent.is_set() else 0
            if manualControlEvent.is_set():
                previous_action = manual_control_logic(clients)
            else:
                previous_action = automatic_control_logic(is_day, water_level_high, previous_action, clients)

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
    hmi_webserver_thread = threading.Thread(target=app.run, kwargs={"host": args['hmi_host'], "port": args['hmi_port']})
    hmi_webserver_thread.start()
    control_loop_thread.join()
    hmi_webserver_thread.join()


if __name__ == "__main__":
    main()
