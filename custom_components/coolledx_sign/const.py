"""Constants for the CoolLEDX LED sign integration."""
DOMAIN = "coolledx_sign"

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

CONF_PASSWORD = "password"
CONF_MIRROR = "mirror"
CONF_SCROLL_SPEED = "scroll_speed"
CONF_LARGE_TEXT = "large_text"
CONF_IDLE_MODE = "idle_mode"

DEFAULT_PASSWORD = "000000"
DEFAULT_SCROLL_SPEED = 200
IDLE_MODES = ["auto", "reading", "optics", "holidays", "halloween", "any"]

ATTR_MESSAGE = "message"
ATTR_COLOR = "color"
ATTR_ICON = "icon"
ATTR_LABEL = "label"
ATTR_MODE = "mode"
ATTR_SPEED = "speed"
ATTR_LARGE = "large"
ATTR_NAME = "name"
ATTR_FRAME_MS = "frame_ms"
ATTR_ENABLED = "enabled"
ATTR_DEVICE_ID = "device_id"
