import json
import paho.mqtt.client as mqtt
from homeassistant.components.light import LightEntity, LightEntityFeature, ATTR_BRIGHTNESS, COLOR_MODE_BRIGHTNESS
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import logging

DOMAIN = "lytviya"

# Set up logging
_LOGGER = logging.getLogger(__name__)
_LOGGER.info("Loading Lytviya integration version 2.1")  # Updated version marker

# Configuration schema for the platform
PLATFORM_SCHEMA = vol.Schema({
    vol.Required("host"): cv.string,
    # vol.Required("username"): cv.string,
    # vol.Required("password"): cv.string,
}, extra=vol.ALLOW_EXTRA)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Lytviya light platform."""
    host = config["host"]
    # username = config["username"]
    # password = config["password"]

    # Set up MQTT client
    mqtt_client = mqtt.Client()
    # mqtt_client.username_pw_set(username, password)
    try:
        mqtt_client.connect(host, 1883, 60)
        mqtt_client.loop_start()
        _LOGGER.info("Successfully connected to MQTT broker at %s", host)
    except Exception as e:
        _LOGGER.error("Failed to connect to MQTT broker at %s: %s", host, str(e))

    # Store MQTT client in hass.data
    hass.data[DOMAIN] = {"mqtt_client": mqtt_client}

    # Add the light entity
    add_entities([LytviyaLight(hass)])
    _LOGGER.info("LytviyaLight entity added to Home Assistant")

class LytviyaLight(LightEntity):
    """Representation of a Lytviya dimmable light."""

    _attr_supported_features = LightEntityFeature(0)
    _attr_name = "Lytviya Light"
    _attr_unique_id = "lytviya_light_001"
    _attr_supported_color_modes = {COLOR_MODE_BRIGHTNESS}
    _attr_color_mode = COLOR_MODE_BRIGHTNESS

    def __init__(self, hass):
        """Initialize the light."""
        self._hass = hass
        self._is_on = False
        self._brightness = 0
        _LOGGER.debug("LytviyaLight initialized")

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def brightness(self) -> int:
        return self._brightness

    @property
    def supported_color_modes(self):
        return self._attr_supported_color_modes

    @property
    def color_mode(self):
        return self._attr_color_mode

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug("async_turn_on called with kwargs: %s", kwargs)
        self._is_on = True
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
        else:
            self._brightness = 255
        
        # Publish state to MQTT with result checking
        state = {"state": "ON", "brightness": self._brightness}
        message = json.dumps(state)
        try:
            mqtt_client = self._hass.data[DOMAIN]["mqtt_client"]
            result = mqtt_client.publish("/Lytviya/serial", message)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                _LOGGER.info("Successfully published to MQTT: topic=/Lytviya/serial, message=%s", message)
            else:
                _LOGGER.error("Failed to publish to MQTT: rc=%d", result.rc)
        except Exception as e:
            _LOGGER.error("Exception while publishing to MQTT: %s", str(e))
        
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug("async_turn_off called with kwargs: %s", kwargs)
        self._is_on = False
        self._brightness = 0
        
        # Publish state to MQTT with result checking
        state = {"state": "OFF", "brightness": self._brightness}
        message = json.dumps(state)
        try:
            mqtt_client = self._hass.data[DOMAIN]["mqtt_client"]
            result = mqtt_client.publish("/Lytviya/serial", message)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                _LOGGER.info("Successfully published to MQTT: topic=/Lytviya/serial, message=%s", message)
            else:
                _LOGGER.error("Failed to publish to MQTT: rc=%d", result.rc)
        except Exception as e:
            _LOGGER.error("Exception while publishing to MQTT: %s", str(e))
        
        self.async_write_ha_state()