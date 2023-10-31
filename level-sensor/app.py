"""
modbus server designed to provide a readout for a water level sensor in a
discrete input cell
"""

import RPi.GPIO as gpio
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)


def read_water_level_sensor(gpio_pin):
    if gpio.input(gpio_pin) == gpio.HIGH:
        return 1
    return 0


class CallbackDataBlock(ModbusSequentialDataBlock):
    def __init__(self, sensor_gpio, address, values):
        super().__init__(address, values)
        self._sensor_gpio = sensor_gpio

    def getValues(self, address, count=1):
        """Return the requested values from the datastore."""
        if address == 0x00:
            return read_water_level_sensor(self.sensor_gpio)
        else:
            return 0


def get_args():
    # TODO could pull these values from command-line arguments instead
    return {
        "host": "0.0.0.0",
        "port": 502,
        "sensor_read_gpio": 11,
        "sensor_pwr_gpio": 17
    }


def setup_gpio(sensor_read_gpio=11, sensor_pwr_gpio=17, **args):
    # use BCM mode (as opposed to BOARD mode)
    gpio.setmode(gpio.BCM)

    # set up read pin as input signal
    gpio.setup(sensor_read_gpio, gpio.IN)

    # send power signal through selected power pin
    gpio.setup(sensor_pwr_gpio, gpio.OUT, initial=gpio.HIGH)


def run_server(sensor_read_gpio=11, host=None, port=502, **args):
    # initialize data block with exactly 1 coil, value 0, at address 0x00
    block = CallbackDataBlock(sensor_read_gpio, 0x00, [0] * 1)

    # pass the data block in as a discrete input initializer (read-only 1-bit
    # cells); ignore coils, holding registers, and input registers
    store = ModbusSlaveContext(di=block)

    # create the server context and tell it that it has exactly one slave
    # context to worry about
    context = ModbusServerContext(slaves=store, single=True)

    # start the modbus/TCP server with the provided information from cmdline
    return await StartTcpServer(
        context=context,
        address=(host, port),
    )


def cleanup(sensor_read_gpio=11, sensor_pwr_gpio=17, **args):
    gpio.output(sensor_pwr_gpio, gpio.LOW)
    gpio.cleanup()


if __name__ == "__main__":
    args = get_args()
    try:
        setup_gpio(**args)
        run_server(**args)
    finally:
        cleanup(**args)
