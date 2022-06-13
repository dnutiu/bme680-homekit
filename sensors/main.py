import signal
from pyhap.accessory import Accessory, Bridge
import bme680
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SENSOR


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

        # Add the services that this Accessory will support with add_preload_service here
        temp_service = self.add_preload_service('TemperatureSensor')
        humidity_service = self.add_preload_service('HumiditySensor')

        self.temp_value = temp_service.get_characteristic('CurrentTemperature')
        self.humidity_value = humidity_service.get_characteristic("CurrentRelativeHumidity")

    @Accessory.run_at_interval(3)
    def run(self):
        """We override this method to implement what the accessory will do when it is
        started.

        We set the current temperature to a random number. The decorator runs this method
        every 3 seconds.
        """
        if self.sensor.get_sensor_data():
            self.temp_value.set_value(self.sensor.data.temperature)
            self.humidity_value.set_value(self.sensor.data.humidity)

    def stop(self):
        """We override this method to clean up any resources or perform final actions, as
        this is called by the AccessoryDriver when the Accessory is being stopped.
        """
        print('Stopping accessory.')


def get_bridge(accessory_driver):
    bridge = Bridge(accessory_driver, 'Bridge')
    bridge.add_accessory(Bme680Sensor(accessory_driver, 'Sensor'))
    return bridge


if __name__ == '__main__':
    driver = AccessoryDriver(port=51826, persist_file="/home/pi/bme680-homekit/accessory.state")
    driver.add_accessory(accessory=get_bridge(driver))
    signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
