"""
modbus server designed to provide a read-write interface for a water flow gate
"""

import RPi.GPIO as gpio
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)


class CallbackDataBlock(ModbusSequentialDataBlock):
    def __init__(self, gate_gpio, address, values):
        super().__init__(address, values)
        self._gate_gpio = gate_gpio

    def setValues(self, address, values):
        if address == 0x00:
            if values == [0]:
                gpio.output(self._gate_gpio, gpio.LOW)
                super().setValues(0x00, [0])
            elif values == [1]:
                gpio.output(self._gate_gpio, gpio.HIGH)
                super().setValues(0x00, [1])


def get_args():
    # TODO could pull these values from command-line arguments instead
    return {
        "host": "0.0.0.0",
        "port": 502,
        "gate_gpio": 22
    }


def setup_gpio(gate_gpio=22, **args):
    # use BCM mode (as opposed to BOARD mode)
    gpio.setmode(gpio.BCM)

    # set up gate GPIO pin as output signal
    gpio.setup(gate_gpio, gpio.OUT, initial=gpio.LOW)


def run_server(gate_gpio=22, host=None, port=502, **args):
    # initialize data block with exactly 1 coil, value 0, at address 0x00
    block = CallbackDataBlock(gate_gpio, 0x00, [0] * 1)

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


def cleanup(gate_gpio=22, **args):
    gpio.output(gate_gpio, gpio.LOW)
    gpio.cleanup()


if __name__ == "__main__":
    args = get_args()
    try:
        setup_gpio(**args)
        run_server(**args)
    finally:
        cleanup(**args)
