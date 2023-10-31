"""
modbus server designed to provide a read-write interface for a water pump
"""

import RPi.GPIO as gpio
from pymodbus.server import StartAsyncTcpServer
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


def get_args():
    # TODO could pull these values from command-line arguments instead
    return {
        "host": "0.0.0.0",
        "port": 502,
        "pump_gpio": 16
    }


def setup_gpio(pump_gpio=16, **args):
    # use BCM mode (as opposed to BOARD mode)
    gpio.setmode(gpio.BCM)

    # set up pump GPIO pin as output signal
    gpio.setup(pump_gpio, gpio.OUT, initial=gpio.LOW)


def run_server(pump_gpio=16, host=None, port=502, **args):
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


def cleanup(pump_gpio=16, **args):
    gpio.output(pump_gpio, gpio.LOW)
    gpio.cleanup()


if __name__ == "__main__":
    args = get_args()
    try:
        setup_gpio(**args)
        run_server(**args)
    finally:
        cleanup(**args)
