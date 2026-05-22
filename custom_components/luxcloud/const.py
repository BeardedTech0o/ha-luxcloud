DOMAIN = "luxcloud"
DEFAULT_SCAN_INTERVAL = 30

CONF_SERIAL = "serial_number"
CONF_REGION = "region"

REGION_GLOBAL = "global"
REGION_EU = "eu"

API_URLS = {
    REGION_GLOBAL: "https://openapi.luxpowertek.com",
    REGION_EU: "https://eu.luxpowertek.com",
}

WORK_MODES = {
    0: "Self Use",
    1: "Feed-in Priority",
    2: "Backup",
    3: "Manual",
}

INVERTER_STATUS = {
    0: "Standby",
    1: "Normal",
    2: "Warning",
    3: "Fault",
    4: "Flash",
    5: "Grid charging",
    6: "Off-grid charging",
    7: "Off-grid discharging",
}
