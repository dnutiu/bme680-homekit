import logging
import sys

from prometheus_client import Gauge
from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_SENSOR

from app.config import Settings
from pms5003 import PMS5003


class Pms5003Sensor(Accessory):
    category = CATEGORY_SENSOR

    def __init__(self, driver, *, aid=None, settings: Settings):
        super().__init__(driver, settings.hap.bridge.bme680.name, aid=aid)

        self.settings = settings
        self.sensor = PMS5003(
            device=settings.hap.bridge.pms5003.device,
            baudrate=settings.hap.bridge.pms5003.baudrate,
            pin_enable=settings.hap.bridge.pms5003.pin_enable,
            pin_reset=settings.hap.bridge.pms5003.pin_reset
        )

        self._pms5003_pm_ug_per_m3_1 = Gauge(
            "pms5003_pm_ug_per_m3_1", "The PM1.0 ug/m3 (ultrafine particles)."
        )
        self._pms5003_pm_ug_per_m3_2 = Gauge(
            "pms5003_pm_ug_per_m3_2", "PM2.5 ug/m3 (combustion particles, organic compounds, metals)."
        )
        self._pms5003_pm_ug_per_m3_10 = Gauge(
            "pms5003_pm_ug_per_m3_10", "PM10 ug/m3  (dust, pollen, mould spores)"
        )

    @Accessory.run_at_interval(120)
    def run(self):
        """
        This function runs the accessory. It polls for data and updates prometheus metrics.
        """
        try:
            logging.info("Reading data from PMS5003 sensor.")
            data = self.sensor.read()

            self._pms5003_pm_ug_per_m3_1.set(data.pm_ug_per_m3(1.0))
            self._pms5003_pm_ug_per_m3_2.set(data.pm_ug_per_m3(2.5))
            self._pms5003_pm_ug_per_m3_10.set(data.pm_ug_per_m3(10))

            logging.info(f"PM1.0 {data.pm_ug_per_m3(1.0)} PM2.5 {data.pm_ug_per_m3(2.5)} PM10 {data.pm_ug_per_m3(10)}")
        except IOError as e:
            # This happens from time to time, best we stop and let systemd restart us.
            logging.critical("Failed to read data from serial.")
            sys.exit(1)

    def stop(self):
        """We override this method to clean up any resources or perform final actions, as
        this is called by the AccessoryDriver when the Accessory is being stopped.
        """
        print("Stopping accessory.")
