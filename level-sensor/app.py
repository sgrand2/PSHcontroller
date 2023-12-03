"""
modbus server designed to provide a readout for a water level sensor in a
discrete input cell
"""

import logging

import click
from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)

class CallbackDataBlock(ModbusSequentialDataBlock):
    def __init__(self, sensor_gpio, address, values):
        super().__init__(address, values)
        self._sensor_gpio = sensor_gpio

    def _included_in_range(addr, rng, target_addr):
        if addr + rng > target_addr:
            return target_addr - addr
        return None

    def _read_sensor_gpio(self):
        import RPi.GPIO as gpio
        if gpio.input(self._sensor_gpio) == gpio.LOW:
            logging.info("read level sensor state as FULL in response to request")
            return 1
        logging.info("read level sensor state as EMPTY in response to request")
        return 0

    def _fake_sensor_gpio(self):
        import random
        if random.randint(0, 100) < 50:
            return 0
        return 1

    def getValues(self, address, count=1):
        """Return the requested values from the datastore."""
        logging.debug(f"read request received for address {address}, count {count}")
        idx = CallbackDataBlock._included_in_range(address, count, 0x01)
        if idx is not None:
            results = [0] * count
            if self._sensor_gpio is not None:
                results[idx] = self._read_sensor_gpio()
            else:
                results[idx] = self._fake_sensor_gpio()
            return results
        return [self._fake_sensor_gpio()] * count

def setup_gpio(sensor_gpio, **args):
    logging.debug("setting up GPIO")
    import RPi.GPIO as gpio

    # use BCM mode (as opposed to BOARD mode)
    gpio.setmode(gpio.BCM)

    # set up read pin as input signal
    gpio.setup(sensor_gpio, gpio.IN)


def run_server(sensor_gpio, host, port, **args):
    logging.debug("setting up Modbus/TCP server")

    # initialize data block with exactly 1 coil, value 0, at address 0x01
    block = CallbackDataBlock(sensor_gpio, 0x01, [0] * 1)

    # pass the data block in as a discrete input initializer (read-only 1-bit
    # cells); ignore coils, holding registers, and input registers
    store = ModbusSlaveContext(di=block)

    # create the server context and tell it that it has exactly one slave
    # context to worry about
    context = ModbusServerContext(slaves=store, single=True)

    # start the modbus/TCP server with the provided information from cmdline
    logging.info(f"running Modbus/TCP server at {host}:{port}")
    return StartTcpServer(
        context=context,
        address=(host, port),
    )


def cleanup(sensor_gpio, **args):
    logging.debug("cleaning up GPIO")
    import RPi.GPIO as gpio
    gpio.cleanup()


@click.group()
@click.option("--log", "-l", default="info", help="The log level to use when sending logs to stdout (default: INFO; options: DEBUG, INFO, WARNING, ERROR, CRITICAL)")
def cli(log):
    log_level = getattr(logging, log.upper())
    logging.basicConfig(level=log_level)
    logging.info(f"logging level set to {log.upper()}")

@click.command()
@click.option("--sensor-gpio", "-sg", default=11, help="The GPIO to use for reading water level sensor signal (default: 11)")
@click.option("--host", "-h", default="0.0.0.0", help="The address to use when creating a socket for the Modbus server (default: 0.0.0.0)")
@click.option("--port", "-p", default=502, help="The address to use when creating a socket for the Modbus server (default: 502)")
def run(**args):
    try:
        setup_gpio(**args)
        run_server(**args)
    finally:
        cleanup(**args)

@click.group()
def debug():
    pass

@click.command("modbus")
@click.option("--host", "-h", default="0.0.0.0", help="The address to use when creating a socket for the Modbus server (default: 0.0.0.0)")
@click.option("--port", "-p", default=502, help="The address to use when creating a socket for the Modbus server (default: 502)")
def modbus_debug(**args):
    logging.info(f"starting Modbus debugging mode (host={args['host']}, port={args['port']})")
    args['sensor_gpio'] = None
    run_server(**args)

@click.command("gpio")
@click.option("--sensor-gpio", "-sg", default=11, help="The GPIO to use for reading water level sensor signal (default: 11)")
def gpio_debug(**args):
    logging.info(f"starting GPIO debugging mode (sensor_gpio={args['sensor_gpio']})")
    import RPi.GPIO as gpio
    import time
    try:
        setup_gpio(**args)
        while True:
            if gpio.input(args['sensor_gpio']) == gpio.HIGH:
                logging.info("water level sensor HIGH")
            else:
                logging.info("water level sensor LOW")
            time.sleep(1)
    finally:
        cleanup(**args)

if __name__ == "__main__":
    cli.add_command(run)
    cli.add_command(debug)
    debug.add_command(modbus_debug)
    debug.add_command(gpio_debug)
    cli()
