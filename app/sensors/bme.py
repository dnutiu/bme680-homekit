import logging
import os
import sys

from prometheus_client import Gauge
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR
import bme680

from app.config import Settings


class Bme680Sensor(Accessory):
    """Implementation of a mock temperature sensor accessory."""

    category = CATEGORY_SENSOR  # This is for the icon in the iOS Home app.

    def __init__(self, driver, *, aid=None, settings: Settings):
        """Here, we just store a reference to the current temperature characteristic and
        add a method that will be executed every time its value changes.
        """
        # If overriding this method, be sure to call the super's implementation first.
        super().__init__(driver, settings.hap.bridge.bme680.name, aid=aid)

        self.settings = settings
        self.sensor = bme680.BME680(
            settings.hap.bridge.bme680.address or bme680.I2C_ADDR_PRIMARY
        )

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

    @Accessory.run_at_interval(120)
    def run(self):
        """
        This function runs the accessory. It polls for data and publishes it at the given interval.
        """
        try:
            logging.info("Reading data from BME680 sensor.")
            self._run()
        except IOError as e:
            # This happens from time to time, best we stop and let systemd restart us.
            logging.critical("Failed to run BME680.")
            sys.exit(1)

    def stop(self):
        """We override this method to clean up any resources or perform final actions, as
        this is called by the AccessoryDriver when the Accessory is being stopped.
        """
        print("Stopping accessory.")
