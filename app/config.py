import functools
import os
from pathlib import Path
from typing import Type, Tuple, Any, Dict

import yaml
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

config_file_default_location = "config.yaml"


class PrometheusSettings(BaseModel):
    enabled: bool = Field(True, description="Enable prometheus metrics server.")
    port: int = Field(8000, description="The prometheus metrics server port.")


class Bme680Settings(BaseModel):
    enabled: bool = Field(True, description="If the sensor should be enabled on not.")
    address: int = Field(
        0x76, description="The I2C address of the sensor. Defaults to primary"
    )
    name: str = Field("Climate Sensor", description="The name of the sensor.")


class Pms5003ModuleSettings(BaseModel):
    enabled: bool = Field(True, description="If sensor should be enabled or not.")
    device: str = Field("/dev/ttyUSB0", description="The TTY path of the sensor.")
    baudrate: int = Field(9600, description="The baudrate of the serial port.")
    pin_enable: str = Field("GPIO22", description="The pin enable.")
    pin_reset: str = Field("GPIO27", description="The pin reset.")


class BridgeSettings(BaseModel):
    display_name: str = Field(
        "Bridge", description="The display name of the HAP bridge."
    )
    bme680: Bme680Settings = Field(
        Bme680Settings(), description="Settings for the BME680 module."
    )
    pms5003: Pms5003ModuleSettings = Field(Pms5003ModuleSettings(), description="Settings for the PMS5003 sensor.")


class HomekitAccessoryProtocolSettings(BaseModel):
    port: int = Field(
        51826, description="The port of the homekit accessory protocol server."
    )
    persist_file: str = Field(
        ...,
        description="The persistence file which holds the homekit accessory protocol server's state.",
    )
    bridge: BridgeSettings = Field(
        BridgeSettings(), description="The HAP's default bridge settings."
    )


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A simple settings source class that loads variables from a YAML file
    at the project's root.

    Here we happen to choose to use the `env_file_encoding` from Config
    when reading `config.yaml`
    """

    @functools.lru_cache
    def read_file_content(self):
        encoding = self.config.get("env_file_encoding")
        return yaml.safe_load(
            Path(
                os.getenv("HOMEKIT_CONFIG", default=config_file_default_location)
            ).read_text(encoding)
        )

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> Tuple[Any, str, bool]:
        file_content_json = self.read_file_content()
        field_value = file_content_json.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex
            )
            if field_value is not None:
                d[field_key] = field_value

        return d


class Settings(BaseSettings):
    prometheus: PrometheusSettings = Field(
        PrometheusSettings(), description="Settings for prometheus."
    )
    hap: HomekitAccessoryProtocolSettings = Field(
        ..., description="Homekit Accessory Protocol server settings."
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls),
            env_settings,
            file_secret_settings,
        )
