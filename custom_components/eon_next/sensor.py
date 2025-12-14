#!/usr/bin/env python3

import logging
from homeassistant.util import dt as dt_util

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)

from homeassistant.const import (
    UnitOfEnergy,
    UnitOfVolume
)

from . import DOMAIN
from .eonnext import METER_TYPE_GAS, METER_TYPE_ELECTRIC, METER_TYPE_EV

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup sensors from a config entry created in the integrations UI."""

    api = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for account in api.accounts:
        for meter in account.meters:
            if await meter.has_reading() == True:

                entities.append(LatestReadingDateSensor(meter))

                if meter.get_type() == METER_TYPE_ELECTRIC:
                    entities.append(LatestElectricKwhSensor(meter))
                
                if meter.get_type() == METER_TYPE_GAS:
                    entities.append(LatestGasCubicMetersSensor(meter))
                    entities.append(LatestGasKwhSensor(meter))
        
        for charger in account.ev_chargers:
            entities.append(SmartChargingScheduleSensor(charger))
            entities.append(NextChargeStartSensor(charger))
            entities.append(NextChargeEndSensor(charger))
            entities.append(NextChargeStartSensor2(charger))
            entities.append(NextChargeEndSensor2(charger))

    async_add_entities(entities, update_before_add=True)



class LatestReadingDateSensor(SensorEntity):
    """Date of latest meter reading"""

    def __init__(self, meter):
        self.meter = meter

        self._attr_name = self.meter.get_serial() + " Reading Date"
        self._attr_device_class = SensorDeviceClass.DATE
        self._attr_icon = "mdi:calendar"
        self._attr_unique_id = self.meter.get_serial() + "__" + "reading_date"
    

    async def async_update(self) -> None:
        self._attr_native_value = await self.meter.get_latest_reading_date()



class LatestElectricKwhSensor(SensorEntity):
    """Latest electricity meter reading"""

    def __init__(self, meter):
        self.meter = meter

        self._attr_name = self.meter.get_serial() + " Electricity"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = "total"
        self._attr_icon = "mdi:meter-electric-outline"
        self._attr_unique_id = self.meter.get_serial() + "__" + "electricity_kwh"
    

    async def async_update(self) -> None:
        self._attr_native_value = await self.meter.get_latest_reading()



class LatestGasKwhSensor(SensorEntity):
    """Latest gas meter reading in kWh"""

    def __init__(self, meter):
        self.meter = meter

        self._attr_name = self.meter.get_serial() + " Gas kWh"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = "total"
        self._attr_icon = "mdi:meter-gas-outline"
        self._attr_unique_id = self.meter.get_serial() + "__" + "gas_kwh"
    

    async def async_update(self) -> None:
        self._attr_native_value = await self.meter.get_latest_reading_kwh()



class LatestGasCubicMetersSensor(SensorEntity):
    """Latest gas meter reading in kWh"""

    def __init__(self, meter):
        self.meter = meter

        self._attr_name = self.meter.get_serial() + " Gas"
        self._attr_device_class = SensorDeviceClass.GAS
        self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        self._attr_state_class = "total"
        self._attr_icon = "mdi:meter-gas-outline"
        self._attr_unique_id = self.meter.get_serial() + "__" + "gas_m3"
    

    async def async_update(self) -> None:
        self._attr_native_value = await self.meter.get_latest_reading()


class SmartChargingScheduleSensor(SensorEntity):
    """Smart Charging Schedule"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Smart Charging Schedule"
        self._attr_icon = "mdi:ev-station"
        self._attr_unique_id = self.charger.get_serial() + "__" + "smart_charging_schedule"
        self._attr_extra_state_attributes = {}
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule is not None:
            if len(schedule) > 0:
                self._attr_native_value = "Active"
                self._attr_extra_state_attributes["schedule"] = schedule
            else:
                self._attr_native_value = "No Schedule"
                self._attr_extra_state_attributes["schedule"] = []
        else:
            self._attr_native_value = "Unknown"


class NextChargeStartSensor(SensorEntity):
    """Start time of next charge"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Next Charge Start"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-start"
        self._attr_unique_id = self.charger.get_serial() + "__" + "next_charge_start"
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule and len(schedule) > 0:
            self._attr_native_value = dt_util.parse_datetime(schedule[0]['start'])
        else:
            self._attr_native_value = None


class NextChargeEndSensor(SensorEntity):
    """End time of next charge"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Next Charge End"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-end"
        self._attr_unique_id = self.charger.get_serial() + "__" + "next_charge_end"
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule and len(schedule) > 0:
            self._attr_native_value = dt_util.parse_datetime(schedule[0]['end'])
        else:
            self._attr_native_value = None


class NextChargeStartSensor2(SensorEntity):
    """Start time of next charge slot 2"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Next Charge Start 2"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-start"
        self._attr_unique_id = self.charger.get_serial() + "__" + "next_charge_start_2"
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule and len(schedule) > 1:
            self._attr_native_value = dt_util.parse_datetime(schedule[1]['start'])
        else:
            self._attr_native_value = None


class NextChargeEndSensor2(SensorEntity):
    """End time of next charge slot 2"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Next Charge End 2"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-end"
        self._attr_unique_id = self.charger.get_serial() + "__" + "next_charge_end_2"
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule and len(schedule) > 1:
            self._attr_native_value = dt_util.parse_datetime(schedule[1]['end'])
        else:
            self._attr_native_value = None


