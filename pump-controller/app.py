"""
modbus server designed to provide a read-write interface for a water pump
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
    def __init__(self, pump_gpio, address, values):
        super().__init__(address, values)
        self._pump_gpio = pump_gpio

    def setValues(self, address, values):
        logging.debug(f"write request received for address {address}, values {values}")
        if self._pump_gpio is not None:
            import RPi.GPIO as gpio
            if address == 0x00:
                if values == [0]:
                    logging.info("toggling pump OFF in response to request")
                    gpio.output(self._pump_gpio, gpio.LOW)
                    super().setValues(0x00, [0])
                elif values == [1]:
                    logging.info("toggling pump ON in response to request")
                    gpio.output(self._pump_gpio, gpio.HIGH)
                    super().setValues(0x00, [1])


def setup_gpio(pump_gpio, **args):
    logging.debug("setting up GPIO")
    import RPi.GPIO as gpio

    # use BCM mode (as opposed to BOARD mode)
    gpio.setmode(gpio.BCM)

    # set up pump GPIO pin as output signal
    gpio.setup(pump_gpio, gpio.OUT, initial=gpio.LOW)


def run_server(pump_gpio, host, port, **args):
    logging.debug("setting up Modbus/TCP server")

    # initialize data block with exactly 1 coil, value 0, at address 0x00
    block = CallbackDataBlock(pump_gpio, 0x00, [0] * 1)

    # pass the data block in as a coil initializer (read-write 1-bit cells);
    # ignore discrete inputs, holding registers, and input registers
    store = ModbusSlaveContext(co=block)

    # create the server context and tell it that it has exactly one slave
    # context to worry about
    context = ModbusServerContext(slaves=store, single=True)

    # start the modbus/TCP server with the provided information from cmdline
    logging.info(f"running Modbus/TCP server at {host}:{port}")
    return StartTcpServer(
        context=context,
        address=(host, port),
    )


def cleanup(pump_gpio, **args):
    logging.debug("cleaning up GPIO")
    import RPi.GPIO as gpio
    gpio.output(pump_gpio, gpio.LOW)
    gpio.cleanup()


@click.group()
@click.option("--log", "-l", default="info", help="The log level to use when sending logs to stdout (default: INFO; options: DEBUG, INFO, WARNING, ERROR, CRITICAL)")
def cli(log):
    log_level = getattr(logging, log.upper())
    logging.basicConfig(level=log_level)
    logging.info(f"logging level set to {log.upper()}")

@click.command()
@click.option("--pump-gpio", "-pg", default=16, help="The GPIO to use for controlling the pump (default: 16)")
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
    args['pump_gpio'] = None
    run_server(**args)

@click.command("gpio")
@click.option("--pump-gpio", "-pg", default=16, help="The GPIO to use for controlling the pump (default: 16)")
def gpio_debug(**args):
    logging.info(f"starting GPIO debugging mode (pump_gpio={args['pump_gpio']})")
    import RPi.GPIO as gpio
    import time
    try:
        setup_gpio(**args)
        while True:
            logging.info("toggling pump ON")
            gpio.output(args['pump_gpio'], gpio.HIGH)
            time.sleep(1)
            logging.info("toggling pump OFF")
            gpio.output(args['pump_gpio'], gpio.LOW)
            time.sleep(1)
    finally:
        cleanup(**args)

if __name__ == "__main__":
    cli.add_command(run)
    cli.add_command(debug)
    debug.add_command(modbus_debug)
    debug.add_command(gpio_debug)
    cli()
