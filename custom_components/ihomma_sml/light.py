"""Platform for iHomma SmartLight integration."""

import logging
from typing import Dict, Any
from datetime import timedelta
import voluptuous as vol

from homeassistant.const import CONF_NAME
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.restore_state import RestoreEntity

import homeassistant.helpers.config_validation as cv

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
    PLATFORM_SCHEMA,
)

from .ihomma_effects import AVAILABLE_EFFECTS
from .device import iHommaSML_Device
from .state_manager import StateManager
from .const import (
    DOMAIN,
    CONF_DEVICE_IP,
    CONF_DEVICES_IP,
    CONF_IS_GROUP,
    BASE_BRIGHTNESS,
    BASE_COLOR_K,
    BASE_COLOR_RGB,
    TEMP_COLOR_MAX_K,
    TEMP_COLOR_MIN_K,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Exclusive(CONF_DEVICE_IP, 'ip'): cv.string,
        vol.Exclusive(CONF_DEVICES_IP, 'ip'): vol.All(
            cv.ensure_list,
            [cv.string],
            vol.Length(min=1, msg="At least one IP is required for a group")
        ),
        vol.Optional(CONF_IS_GROUP, default=False): cv.boolean,
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info = None,
) -> None:
    """Configuration of the platform."""
    name = config[CONF_NAME]
    is_group = config.get(CONF_IS_GROUP, False)

    if is_group:
        devices_ip = config.get(CONF_DEVICES_IP)
        if not devices_ip:
            _LOGGER.error("A group must have at least one bulb IP")
            return

        entity = iHommaSML_GroupEntity(
            hass,
            {
                "name": name,
                "devices_ip": devices_ip,
            }
        )
    else:
        device_ip = config.get(CONF_DEVICE_IP)
        _LOGGER.debug(
            "Async Setting up light platform with name: %s, ip: %s, is_group: %s",
            name,
            device_ip,
            is_group)
        if not device_ip:
            _LOGGER.error("A unique bulb must have an IP")
            return

        entity = iHommaSML_Entity(
            hass,
            {
                "name": name,
                "device_ip": device_ip,
            }
        )

    async_add_entities([entity])

class iHommaSML_Entity(LightEntity, RestoreEntity):
    """Representation of an iHommaSML Light."""

    def __init__(self, hass: HomeAssistant, entry_infos: dict) -> None:
        """Initialize the entity."""
        self._hass = hass
        self._attr_name = entry_infos.get("name")

        """Creation of the underlying device for communication"""
        self._device = iHommaSML_Device(entry_infos.get("device_ip"))

        """Home Assistant attributes"""
        self._attr_has_entity_name = True
        self._translations = {}
        self._attr_unique_id = f"ihomma_sml_{self._attr_name.replace(' ', '_').lower()}"

        """Capacities"""
        self._attr_supported_color_modes = {ColorMode.RGB, ColorMode.COLOR_TEMP}
        self._attr_supported_features = LightEntityFeature.EFFECT

        """Initial states"""
        self._attr_available = False
        self._attr_state = STATE_UNAVAILABLE
        self._was_unavailable = True

        """Default values"""
        self._brightness = BASE_BRIGHTNESS
        self._attr_color_temp_kelvin = BASE_COLOR_K
        self._attr_rgb_color = BASE_COLOR_RGB
        self._attr_color_mode = ColorMode.RGB
        self._attr_effect = None

        """Backup States"""
        self._saved_states = {
            "state": self._attr_state,
            "brightness": self._brightness,
            "effect": self._attr_effect,
            "color_temp_kelvin": self._attr_color_temp_kelvin,
            "rgb_color": self._attr_rgb_color
        }

        """Entity information"""
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._attr_name,
            "manufacturer": "iHomma",
            "model": "SmartLight",
            "via_device": (DOMAIN, self._device.device_ip),
        }

        _LOGGER.info("Initializing iHommaSML Light entity %s with unique_id %s",
                    self._attr_name,
                    self._attr_unique_id)

        self._update_interval = timedelta(seconds=10)  # Default interval
        self._timer_cancel = None  # To store the cancellation function

        self._state_manager = StateManager()

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._attr_name

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        return self._brightness

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the CT color value in kelvin."""
        return self._attr_color_temp_kelvin if self._attr_color_mode == ColorMode.COLOR_TEMP else None

    @property
    def min_color_temp_kelvin(self) -> int:
        """Returns the minimum color temperature in Kelvin."""
        return TEMP_COLOR_MIN_K

    @property
    def max_color_temp_kelvin(self) -> int:
        """Returns the maximum color temperature in Kelvin."""
        return TEMP_COLOR_MAX_K

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color value."""
        return self._attr_rgb_color if self._attr_color_mode == ColorMode.RGB else None

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return [
            self._translations.get(effect.description_key, effect.id)
            for effect in AVAILABLE_EFFECTS.values()
        ]

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self._attr_effect

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:lightbulb"

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""

        return self._attr_state == STATE_ON if self._attr_state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) else False

    def update_state(self):
        """Synchronous state update
        Force Home Assistant to be executed async_write_ha_state
        In the event loop"""
        _LOGGER.debug("Updating state for light %s", self._attr_name)

        self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    @callback
    async def async_added_to_hass(self) -> None:
        """Called when entity is added to HA."""
        _LOGGER.info("Adding light %s to Home Assistant", self._attr_name)

        await super().async_added_to_hass()

        """Restoration of the last known state"""
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_state = last_state.state
            self._brightness = last_state.attributes.get("brightness", 255)
            self._attr_effect = last_state.attributes.get("effect", None)
            self._attr_color_temp_kelvin = last_state.attributes.get("color_temp_kelvin", None)
            self._attr_rgb_color = last_state.attributes.get("rgb_color", None)
        self.__backup_online_states()

        """Configuration of the update timer"""
        self._timer_cancel = async_track_time_interval(
            self._hass,
            self.async_get_light_states,
            interval=self._update_interval,
        )
        """Disarm the timer when the entity is destroyed"""
        self.async_on_remove(self._timer_cancel)

        """Loading of translations"""
        _LOGGER.debug("Get translations for light %s", self._translations)
        self._translations = await async_get_translations(
            self.hass,
            self.hass.config.language,
            integrations=[DOMAIN],
            category="entity"
        )

        self._state_manager.register_light(
            self._device.device_ip,
            self._handle_state_update
        )

        """Update state after entity loading"""
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up when entity is removed."""
        self._state_manager.unregister_light(
            self._device.device_ip,
            self._handle_state_update
        )

    def _handle_state_update(self, state: Dict[str, Any]) -> None:
        """Handle state updates from other entities."""
        self._attr_state = state["state"]
        self._brightness = state["brightness"]
        self._attr_color_temp_kelvin = state["color_temp"]
        self._attr_rgb_color = state["rgb_color"]
        self._attr_effect = state["effect"]
        self.update_state()

    async def async_get_light_states(self, *_) -> None:
        """Periodic state update."""
        _LOGGER.debug("Updating states for light %s", self._attr_name)
        device_state = self._device.get_state()
        _LOGGER.debug("Retrieving states for light %s: %s", self._attr_name, device_state)
        if device_state["available"]:
            self._attr_available = True
            if device_state["state"] == STATE_ON:
                self._attr_state = STATE_ON

        """Update the state of the entity and manage unavailability."""
        _LOGGER.info("Updating light %s status", self._attr_name)
        _LOGGER.debug("Light %s was Last %s and now is %s",
                   self.name,
                   ("unavailable" if self._was_unavailable else "available"),
                   ("available" if self._attr_available else "unavailable"))

        if self._was_unavailable and self._attr_available:
            """The entity becomes available after being unavailable"""
            _LOGGER.debug("Light %s is now available", self.name)
            self.__restore_online_states()
            _LOGGER.info("Light %s is Restoring Last State", self.name)
            _LOGGER.debug("Light %s Restoring Last State with State: %s", self.name, self._attr_state)
            _LOGGER.debug("Light %s Restoring Last State with Brightness: %s", self.name, self._brightness)
            _LOGGER.debug("Light %s Restoring Last State with Effect: %s", self.name, self._attr_effect)
            _LOGGER.debug("Light %s Restoring Last State with Temp: %s", self.name, self._attr_color_temp_kelvin)
            _LOGGER.debug("Light %s Restoring Last State with RGB: %s", self.name, self._attr_rgb_color)

            if (self._attr_state == STATE_ON if self._attr_state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) else False):
                kwargs = {}
                if self._brightness is not None:
                    kwargs[ATTR_BRIGHTNESS] = self._brightness
                if self._attr_color_temp_kelvin is not None:
                    kwargs[ATTR_COLOR_TEMP_KELVIN] = self._attr_color_temp_kelvin
                if self._attr_rgb_color is not None:
                    kwargs[ATTR_RGB_COLOR] = self._attr_rgb_color
                if self._attr_effect is not None:
                    kwargs[ATTR_EFFECT] = self._attr_effect
                self.turn_on(**kwargs)
            else:
                _LOGGER.debug("Light %s need to be off (state_off/unavailable/unknown", self.name)
                self.turn_off()

        """Store if the entity is unavailable to detect when it comes back online"""
        self._was_unavailable = not self._attr_available
        self.update_state()

    def turn_on(self, **kwargs) -> None:
        """Turn the light on."""
        _LOGGER.debug("Turn on light %s with params: %s", self._attr_name, kwargs)

        self._attr_color_mode = ColorMode.RGB
        if not (self._attr_state in [STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN]):
            if self._device.turn_on():
                self._attr_state = STATE_ON

                """Light parameters management"""
                if ATTR_BRIGHTNESS in kwargs:
                    brightness = kwargs[ATTR_BRIGHTNESS]
                    if self._device.set_brightness(brightness):
                        self._brightness = brightness

                """Check if a color temperature is passed"""
                if ATTR_COLOR_TEMP_KELVIN in kwargs:
                    temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
                    if TEMP_COLOR_MIN_K <= temp <= TEMP_COLOR_MAX_K:
                        if self._device.set_temperature(temp):
                            self._attr_color_temp_kelvin = temp
                            self._attr_color_mode = ColorMode.COLOR_TEMP

                """Check if an RGB color is passed"""
                if ATTR_RGB_COLOR in kwargs:
                    rgb = kwargs[ATTR_RGB_COLOR]
                    if self._device.set_color(rgb):
                        self._attr_rgb_color = rgb
                        self._attr_color_mode = ColorMode.RGB

                """Effects management"""
                if ATTR_EFFECT in kwargs:
                    effect_str = kwargs[ATTR_EFFECT]
                    effect = next(
                        (effect for effect in AVAILABLE_EFFECTS.values()
                        if self._translations.get(effect.description_key, effect.id) == effect_str),
                        None
                    )
                    _LOGGER.debug("Selected Effect: %s of %s", effect_str, self.effect_list)
                    if effect and self._device.set_effect(effect.instruction, effect_str):
                        self._attr_effect = effect_str
                        self._attr_color_mode = ColorMode.RGB

        self.update_state()

    def turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        _LOGGER.info("Turning off light %s", self._attr_name)
        if self._device.turn_off():
            self._attr_state = STATE_OFF
            self.update_state()

    def __backup_online_states(self) -> None:
        """Save the light's online states."""
        self._saved_states.update({
            'state': self._attr_state,
            'brightness': self._brightness,
            'effect': self._attr_effect,
            'color_temp_kelvin': self._attr_color_temp_kelvin,
            'rgb_color': self._attr_rgb_color
        })

    def __restore_online_states(self) -> None:
        """Restore the light's online states."""
        self._attr_state = self._saved_states["state"]
        self._brightness = self._saved_states["brightness"]
        self._attr_effect = self._saved_states["effect"]
        self._attr_color_temp_kelvin = self._saved_states["color_temp_kelvin"]
        self._attr_rgb_color = self._saved_states["rgb_color"]

    def __update_timer_interval(self, new_interval: int) -> None:
        """Updates the timer interval."""
        if self._timer_cancel:
            self._timer_cancel()  # Cancels the existing timer

        self._update_interval = timedelta(new_interval)
        self._timer_cancel = async_track_time_interval(
            self._hass,
            self.async_get_light_states,
            interval=self._update_interval,
        )
        _LOGGER.debug(
            "Light %s: Update interval changed to %d seconds",
            self.name,
            new_interval
        )

class iHommaSML_GroupEntity(LightEntity, RestoreEntity):
    """Representation of a group of iHomma bulbs."""

    def __init__(self, hass: HomeAssistant, entry_infos: dict) -> None:
        """Initialize the group."""
        self._hass = hass
        self._attr_name = entry_infos.get("name")
        self._devices_ip = entry_infos.get("devices_ip", [])

        """Creation of devices"""
        self._devices = {
            ip: iHommaSML_Device(ip) for ip in self._devices_ip
        }

        """Home Assistant attributes"""
        self._attr_has_entity_name = True
        self._translations = {}
        self._attr_unique_id = f"ihomma_sml_group_{self._attr_name.replace(' ', '_').lower()}"

        """Capacities"""
        self._attr_supported_color_modes = {ColorMode.RGB, ColorMode.COLOR_TEMP}
        self._attr_supported_features = LightEntityFeature.EFFECT

        """Initial states"""
        self._attr_available = False
        self._attr_state = STATE_UNAVAILABLE
        self._was_unavailable = True

        """Default values"""
        self._brightness = BASE_BRIGHTNESS
        self._attr_color_temp_kelvin = BASE_COLOR_K
        self._attr_rgb_color = BASE_COLOR_RGB
        self._attr_color_mode = ColorMode.RGB
        self._attr_effect = None

        """"Backup States"""
        self._saved_states = {
            "state": self._attr_state,
            "brightness": self._brightness,
            "effect": self._attr_effect,
            "color_temp_kelvin": self._attr_color_temp_kelvin,
            "rgb_color": self._attr_rgb_color
        }

        """Entity information"""
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._attr_name,
            "manufacturer": "iHomma",
            "model": "SmartLight Group",
            "via_device": (DOMAIN, "group"),
        }

        _LOGGER.info(
            "Initializing iHommaSML Group %s with %d devices: %s",
            self._attr_name,
            len(self._devices),
            self._devices_ip
        )

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._attr_name

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the group."""
        return self._brightness

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the CT color value in kelvin."""
        return self._attr_color_temp_kelvin if self._attr_color_mode == ColorMode.COLOR_TEMP else None

    @property
    def min_color_temp_kelvin(self) -> int:
        """Returns the minimum color temperature in Kelvin."""
        return TEMP_COLOR_MIN_K

    @property
    def max_color_temp_kelvin(self) -> int:
        """Returns the maximum color temperature in Kelvin."""
        return TEMP_COLOR_MAX_K

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color value."""
        return self._attr_rgb_color if self._attr_color_mode == ColorMode.RGB else None

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return [
            self._translations.get(effect.description_key, effect.id)
            for effect in AVAILABLE_EFFECTS.values()
        ]

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self._attr_effect

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:lightbulb-group"

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""

        return self._attr_state == STATE_ON if self._attr_state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) else False

    @callback
    async def async_added_to_hass(self) -> None:
        """Called when entity is added to HA."""
        _LOGGER.info("Adding group %s to Home Assistant", self._attr_name)

        await super().async_added_to_hass()

        """Restoration of the last known state"""
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_state = last_state.state
            self._brightness = last_state.attributes.get("brightness", 255)
            self._attr_effect = last_state.attributes.get("effect", None)
            self._attr_color_temp_kelvin = last_state.attributes.get("color_temp_kelvin", None)
            self._attr_rgb_color = last_state.attributes.get("rgb_color", None)
        self.__backup_online_states()

        """Configuration of the update timer"""
        timer_cancel = async_track_time_interval(
            self._hass,
            self.async_get_light_states,
            interval=timedelta(seconds=10),
        )
        """Disarm the timer when the entity is destroyed"""
        self.async_on_remove(timer_cancel)

        """Loading of translations"""
        self._translations = await async_get_translations(
            self.hass,
            self.hass.config.language,
            integrations=[DOMAIN],
            category="entity"
        )
        _LOGGER.debug("Get translations for light %s", self._translations)

        """Update state after entity loading"""
        self.async_write_ha_state()

    async def async_get_light_states(self, *_) -> None:
        """Periodic update of states."""
        _LOGGER.debug("Updating states for group %s", self._attr_name)

        available_devices = []
        on_devices = []

        for ip, device in self._devices.items():
            device_state = device.get_state()
            _LOGGER.debug("Retrieving states for group %s: %s", self._attr_name, device_state)
            if device_state["available"]:
                available_devices.append(ip)
                if device_state["state"] == STATE_ON:
                    on_devices.append(ip)
            self._attr_available = len(available_devices) > 0
        if not self._attr_available:
            self._attr_state = STATE_UNAVAILABLE
            self._was_unavailable = True
            _LOGGER.warning("Group %s is unavailable - No devices responding", self._attr_name)
        else:
            if self._was_unavailable:
                _LOGGER.info("Group %s is now available - Restoring states", self._attr_name)
                self.__restore_online_states()
                """Apply restored states"""
                if self.is_on:
                    kwargs = {}
                    if self._brightness is not None:
                        kwargs[ATTR_BRIGHTNESS] = self._brightness
                    if self._attr_color_temp_kelvin is not None:
                        kwargs[ATTR_COLOR_TEMP_KELVIN] = self._attr_color_temp_kelvin
                    if self._attr_rgb_color is not None:
                        kwargs[ATTR_RGB_COLOR] = self._attr_rgb_color
                    if self._attr_effect is not None:
                        kwargs[ATTR_EFFECT] = self._attr_effect
                    await self.async_turn_on(**kwargs)
            else:
                self._attr_state = STATE_ON if on_devices else STATE_OFF
                self.__backup_online_states()

            _LOGGER.debug(
                "Group %s: %d/%d devices available, %d devices on",
                self._attr_name,
                len(available_devices),
                len(self._devices),
                len(on_devices)
            )

        self._was_unavailable = not self._attr_available
        self.update_state()

    def update_state(self):
        """Synchronous state update
        Force Home Assistant to be executed async_write_ha_state
        In the event loop"""
        _LOGGER.debug("Updating state for light %s", self._attr_name)

        self._hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    def turn_on(self, **kwargs) -> None:
        """Turn on all lights in group."""
        _LOGGER.info("Turning on group %s with parameters: %s", self._attr_name, kwargs)

        success = True
        for ip, device in self._devices.items():
            _LOGGER.debug("Verify Device is_on : %s", device.is_on)
            if not device.is_on == STATE_ON:
                _LOGGER.debug("Device Turning On")
                if not device.turn_on():
                    success = False
                    _LOGGER.warning("Failed to turn on device %s in group %s", ip, self._attr_name)
                    continue

            """Light parameters management"""
            if ATTR_BRIGHTNESS in kwargs:
                brightness = kwargs[ATTR_BRIGHTNESS]
                if device.set_brightness(brightness):
                    self._brightness = brightness
                else:
                    _LOGGER.warning("Failed to set brightness for device %s", ip)

            """Check if a color temperature is passed"""
            if ATTR_COLOR_TEMP_KELVIN in kwargs:
                temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
                if TEMP_COLOR_MIN_K <= temp <= TEMP_COLOR_MAX_K:
                    if device.set_temperature(temp):
                        self._attr_color_temp_kelvin = temp
                        self._attr_color_mode = ColorMode.COLOR_TEMP
                    else:
                        _LOGGER.warning("Failed to set temperature for device %s", ip)

            """Check if an RGB color is passed"""
            if ATTR_RGB_COLOR in kwargs:
                rgb = kwargs[ATTR_RGB_COLOR]
                if device.set_color(rgb):
                    self._attr_rgb_color = rgb
                    self._attr_color_mode = ColorMode.RGB
                else:
                    _LOGGER.warning("Failed to set color for device %s", ip)

            """Effects management"""
            if ATTR_EFFECT in kwargs:
                effect_str = kwargs[ATTR_EFFECT]
                effect = next(
                    (effect for effect in AVAILABLE_EFFECTS.values()
                     if self._translations.get(effect.description_key, effect.id) == effect_str),
                    None
                )
                if effect and device.set_effect(effect.instruction, effect_str):
                    self._attr_effect = effect_str
                    self._attr_color_mode = ColorMode.RGB
                else:
                    _LOGGER.warning("Failed to set effect for device %s", ip)

        if success:
            self._attr_state = STATE_ON
            self.update_state()

    def turn_off(self, **kwargs) -> None:
        """Turn off all lights in group."""
        _LOGGER.info("Turning off group %s", self._attr_name)

        success = True
        for ip, device in self._devices.items():
            if not device.turn_off():
                success = False
                _LOGGER.warning("Failed to turn off device %s in group %s", ip, self._attr_name)

        if success:
            self._attr_state = STATE_OFF
            self.update_state()

    def __backup_online_states(self) -> None:
        """Backup of online states."""
        self._saved_states.update({
            'state': self._attr_state,
            'brightness': self._brightness,
            'effect': self._attr_effect,
            'color_temp_kelvin': self._attr_color_temp_kelvin,
            'rgb_color': self._attr_rgb_color
        })

    def __restore_online_states(self) -> None:
        """Restoration of online states."""
        self._attr_state = self._saved_states["state"]
        self._brightness = self._saved_states["brightness"]
        self._attr_effect = self._saved_states["effect"]
        self._attr_color_temp_kelvin = self._saved_states["color_temp_kelvin"]
        self._attr_rgb_color = self._saved_states["rgb_color"]