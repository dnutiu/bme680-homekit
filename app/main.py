import logging
import pprint
import signal

from prometheus_client import start_http_server
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver

from app.config import Settings
from app.sensors.bme import Bme680Sensor


def get_bridge(accessory_driver: AccessoryDriver, settings: Settings):
    """
    Returns a Homekit Bridge.

    Parameters
    ----------
    accessory_driver: AccessoryDriver
        The accessory driver.
    """
    bridge = Bridge(accessory_driver, settings.hap.bridge.display_name)
    if settings.hap.bridge.bme680.enabled:
        bridge.add_accessory(
            Bme680Sensor(
                accessory_driver, settings.hap.bridge.bme680.name, settings=settings
            )
        )
    return bridge


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    settings = Settings()
    logging.info("Running with settings:")
    logging.info(pprint.pformat(settings.model_dump()))
    # Start prometheus metrics server. Any metrics will be registered automatically.
    if settings.prometheus.enabled:
        start_http_server(settings.prometheus.port)
    # Python HAP
    driver = AccessoryDriver(
        port=settings.hap.port, persist_file=settings.hap.persist_file
    )
    driver.add_accessory(accessory=get_bridge(driver, settings))
    signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
