"""Effects management for iHomma SmartLight."""
from dataclasses import dataclass
from typing import Dict
from homeassistant.core import HomeAssistant
from homeassistant.helpers.translation import async_get_translations

from .const import (
    DOMAIN,
)

@dataclass
class LightEffect:
    """Class representing a light effect."""
    id: str  # Identifiant unique (ex: "strong_white")
    instruction: int

    @property
    def description_key(self) -> str:
        """Construit la clé de traduction à partir de l'id."""
        return f"component.{DOMAIN}.entity.light.effect.state.{self.id}"
    
AVAILABLE_EFFECTS: Dict[str, LightEffect] = {
    "strong_white": LightEffect(
        id = "strong_white",
        instruction = 0x0,
    ),
    "candlelight": LightEffect(
        id="candlelight",
        instruction=0x1,
    ),
    "morning_light": LightEffect(
        id="morning_light",
        instruction=0x2,
    ),
    "nature_light": LightEffect(
        id="nature_light",
        instruction=0x3,
    ),
    "snow_light": LightEffect(
        id="snow_light",
        instruction=0x4,
    ),
    "squirrel_light": LightEffect(
        id="squirrel_light",
        instruction=0x5,
    ),
    "coffee_light": LightEffect(
        id="coffee_light",
        instruction=0x6,
    ),
    "desk_light": LightEffect(
        id="desk_light",
        instruction=0x7,
    ),
    "hipster": LightEffect(
        id="hipster",
        instruction=0x8,
    ),
    "yellow_light": LightEffect(
        id="yellow_light",
        instruction=0x9,
    ),
    "slow_colors": LightEffect(
        id="slow_colors",
        instruction=0xB,
    ),
    "slow_morning": LightEffect(
        id="slow_morning",
        instruction=0xC,
    ),
    "circle": LightEffect(
        id="circle",
        instruction=0xD,
    ),
    "party": LightEffect(
        id="party",
        instruction=0xE,
    ),
    "romantic": LightEffect(
        id="romantic",
        instruction=0xF,
    ),
    "smooth_yellow": LightEffect(
        id="smooth_yellow",
        instruction=0x10,
    ),
    "blue_wave": LightEffect(
        id="blue_wave",
        instruction=0x11,
    ),
    "strong_green": LightEffect(
        id="strong_green",
        instruction=0x12,
    ),
    "white_yellow": LightEffect(
        id="white_yellow",
        instruction=0x13,
    ),
}