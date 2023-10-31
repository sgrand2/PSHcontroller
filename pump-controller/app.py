"""
modbus server designed to provide a read-write interface for a water pump
"""

import click
import RPi.GPIO as gpio
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
        if address == 0x00:
            if values == [0]:
                gpio.output(self._pump_gpio, gpio.LOW)
                super().setValues(0x00, [0])
            elif values == [1]:
                gpio.output(self._pump_gpio, gpio.HIGH)
                super().setValues(0x00, [1])


def setup_gpio(pump_gpio, **args):
    # use BCM mode (as opposed to BOARD mode)
    gpio.setmode(gpio.BCM)

    # set up pump GPIO pin as output signal
    gpio.setup(pump_gpio, gpio.OUT, initial=gpio.LOW)


def run_server(pump_gpio, host, port, **args):
    # initialize data block with exactly 1 coil, value 0, at address 0x00
    block = CallbackDataBlock(pump_gpio, 0x00, [0] * 1)

    # pass the data block in as a coil initializer (read-write 1-bit cells);
    # ignore discrete inputs, holding registers, and input registers
    store = ModbusSlaveContext(co=block)

    # create the server context and tell it that it has exactly one slave
    # context to worry about
    context = ModbusServerContext(slaves=store, single=True)

    # start the modbus/TCP server with the provided information from cmdline
    return await StartTcpServer(
        context=context,
        address=(host, port),
    )


def cleanup(pump_gpio, **args):
    gpio.output(pump_gpio, gpio.LOW)
    gpio.cleanup()


@click.command()
@click.option("--pump-gpio", "-pg", default=16, help="The GPIO to use for controlling the pump (default: 16)")
@click.option("--host", "-h", default="0.0.0.0", help="The address to use when creating a socket for the Modbus server (default: 0.0.0.0)")
@click.option("--port", "-p", default=502, help="The address to use when creating a socket for the Modbus server (default: 502)")
def main(**args):
    try:
        setup_gpio(**args)
        run_server(**args)
    finally:
        cleanup(**args)


if __name__ == "__main__":
    main()
