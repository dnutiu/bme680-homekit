import logging
import os
import signal
import sys

import bme680
from prometheus_client import Gauge, start_http_server
from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SENSOR


def fail(message: str):
    """
    Fail crashes the program and logs the message.
    """
    logging.critical(message)
    sys.exit(1)


class Bme680Sensor(Accessory):
    """Implementation of a mock temperature sensor accessory."""

    category = CATEGORY_SENSOR  # This is for the icon in the iOS Home app.

    def __init__(self, *args, **kwargs):
        """Here, we just store a reference to the current temperature characteristic and
        add a method that will be executed every time its value changes.
        """
        # If overriding this method, be sure to call the super's implementation first.
        super().__init__(*args, **kwargs)

        self.sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)

        if os.getenv("ENABLE_GAS_MEASUREMENT", "false") == "true":
            self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
            self.sensor.set_gas_heater_temperature(320)
            self.sensor.set_gas_heater_duration(150)
            self.sensor.select_gas_heater_profile(0)

        self._temperature_metric = Gauge(
            "bme680_temperature_celsius", "The temperature measurement in celsius."
        )
        self._humidity_metric = Gauge(
            "bme680_humidity_rh", "The humidity measurement in relative humidity."
        )
        self._pressure_metric = Gauge(
            "bme680_pressure_hpa", "The pressure measurement in hectopascals."
        )
        self._gas_resistance_metric = Gauge(
            "bme860_gas_resistance_ohm", "The gas resistance measurement in ohms."
        )

        # Add the services that this Accessory will support with add_preload_service here
        temp_service = self.add_preload_service("TemperatureSensor")
        humidity_service = self.add_preload_service("HumiditySensor")

        self.temp_value = temp_service.get_characteristic("CurrentTemperature")
        self.humidity_value = humidity_service.get_characteristic(
            "CurrentRelativeHumidity"
        )

    def _run(self):
        if self.sensor.get_sensor_data():
            self.temp_value.set_value(self.sensor.data.temperature)
            self.humidity_value.set_value(self.sensor.data.humidity)

            # Update prometheus metrics.
            self._temperature_metric.set(self.sensor.data.temperature)
            self._humidity_metric.set(self.sensor.data.humidity)
            self._pressure_metric.set(self.sensor.data.pressure)

            if self.sensor.data.heat_stable:
                self._gas_resistance_metric.set(self.sensor.data.gas_resistance)

    @Accessory.run_at_interval(30)
    def run(self):
        """We override this method to implement what the accessory will do when it is
        started.

        We set the current temperature to a random number. The decorator runs this method
        every 3 seconds.
        """
        try:
            self._run()
        except IOError as e:
            # This happens from time to time, best we stop and let systemd restart us.
            fail(f"Failed due to IOError: {e}")

    def stop(self):
        """We override this method to clean up any resources or perform final actions, as
        this is called by the AccessoryDriver when the Accessory is being stopped.
        """
        print("Stopping accessory.")


def get_bridge(accessory_driver):
    bridge = Bridge(accessory_driver, "Bridge")
    bridge.add_accessory(Bme680Sensor(accessory_driver, "Sensor"))
    return bridge


if __name__ == "__main__":
    # Prometheus' metrics server
    start_http_server(8000)
    # Python HAP
    driver = AccessoryDriver(
        port=51826, persist_file="/home/pi/bme680-homekit/sensors/accessory.state"
    )
    driver.add_accessory(accessory=get_bridge(driver))
    signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
