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
        
        # Add tariff sensors for the account
        if account.tariff_data:
            entities.append(TariffNameSensor(account))
            entities.append(StandingChargeSensor(account))
            entities.append(UnitRateSensor(account))
        
        # Add saving session sensors
        if account.saving_sessions:
            entities.append(SavingSessionsSensor(account))

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


class TariffNameSensor(SensorEntity):
    """Active tariff name for the account"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Tariff Name"
        self._attr_icon = "mdi:file-document-outline"
        self._attr_unique_id = f"{self.account.account_number}__tariff_name"
    

    async def async_update(self) -> None:
        await self.account._load_tariff_data()
        if self.account.tariff_data and len(self.account.tariff_data) > 0:
            # Get the most recent active agreement
            active = [a for a in self.account.tariff_data if not a.get('validTo') or dt_util.parse_datetime(a['validTo']) > dt_util.now()]
            if active:
                tariff = active[0].get('tariff', {})
                self._attr_native_value = tariff.get('displayName') or tariff.get('fullName')
                self._attr_extra_state_attributes = {
                    "tariff_code": tariff.get('tariffCode'),
                    "tariff_type": tariff.get('tariffType'),
                    "is_variable": tariff.get('isVariable'),
                    "valid_from": active[0].get('validFrom'),
                    "valid_to": active[0].get('validTo')
                }
            else:
                self._attr_native_value = None
        else:
            self._attr_native_value = None


class StandingChargeSensor(SensorEntity):
    """Daily standing charge for the account"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Standing Charge"
        self._attr_icon = "mdi:currency-gbp"
        self._attr_unit_of_measurement = "GBP/day"
        self._attr_unique_id = f"{self.account.account_number}__standing_charge"
    

    async def async_update(self) -> None:
        await self.account._load_tariff_data()
        if self.account.tariff_data and len(self.account.tariff_data) > 0:
            active = [a for a in self.account.tariff_data if not a.get('validTo') or dt_util.parse_datetime(a['validTo']) > dt_util.now()]
            if active:
                tariff = active[0].get('tariff', {})
                standing_charge = tariff.get('standingCharge')
                if standing_charge is not None:
                    # Convert pence to pounds
                    self._attr_native_value = round(standing_charge / 100, 4)
                else:
                    self._attr_native_value = None
            else:
                self._attr_native_value = None
        else:
            self._attr_native_value = None


class UnitRateSensor(SensorEntity):
    """Unit rate for the account"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Unit Rate"
        self._attr_icon = "mdi:currency-gbp"
        self._attr_unit_of_measurement = "GBP/kWh"
        self._attr_unique_id = f"{self.account.account_number}__unit_rate"
    

    async def async_update(self) -> None:
        await self.account._load_tariff_data()
        if self.account.tariff_data and len(self.account.tariff_data) > 0:
            active = [a for a in self.account.tariff_data if not a.get('validTo') or dt_util.parse_datetime(a['validTo']) > dt_util.now()]
            if active:
                tariff = active[0].get('tariff', {})
                unit_rate = tariff.get('unitRate')
                
                # Handle HalfHourlyTariff with multiple rates
                if unit_rate is None and tariff.get('unitRates'):
                    rates = tariff.get('unitRates')
                    if len(rates) > 0:
                        # Extract unique rates
                        unique_rates = sorted(list(set([r['value'] for r in rates])))
                        
                        # Default to the first rate (usually low/night rate if sorted, but we want current)
                        # Logic for Next Drive: 00:00 - 07:00 is Off-Peak (Low)
                        is_next_drive = "Next Drive" in (tariff.get('displayName') or "")
                        
                        if is_next_drive and len(unique_rates) >= 2:
                            low_rate = unique_rates[0]
                            high_rate = unique_rates[1] # Assuming 2 rates for now
                            
                            now = dt_util.now()
                            # Next Drive Off-Peak is 00:00 to 07:00
                            if 0 <= now.hour < 7:
                                unit_rate = low_rate
                                current_period = "Off-Peak"
                            else:
                                unit_rate = high_rate
                                current_period = "Peak"
                                
                            self._attr_extra_state_attributes = {
                                "meter_point": active[0].get('meterPoint', {}).get('mpan') or active[0].get('meterPoint', {}).get('mprn'),
                                "rates": unique_rates,
                                "current_period": current_period,
                                "low_rate": round(low_rate / 100, 4),
                                "high_rate": round(high_rate / 100, 4)
                            }
                        else:
                            # Fallback for unknown multi-rate tariffs
                            unit_rate = rates[0].get('value')
                            self._attr_extra_state_attributes = {
                                "meter_point": active[0].get('meterPoint', {}).get('mpan') or active[0].get('meterPoint', {}).get('mprn'),
                                "rates": unique_rates
                            }

                if unit_rate is not None:
                    # Convert pence to pounds
                    self._attr_native_value = round(unit_rate / 100, 4)
                    if not hasattr(self, '_attr_extra_state_attributes'):
                         self._attr_extra_state_attributes = {
                            "meter_point": active[0].get('meterPoint', {}).get('mpan') or active[0].get('meterPoint', {}).get('mprn')
                        }
                else:
                    self._attr_native_value = None
            else:
                self._attr_native_value = None
        else:
            self._attr_native_value = None


class SavingSessionsSensor(SensorEntity):
    """Upcoming and active saving sessions"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Saving Sessions"
        self._attr_icon = "mdi:piggy-bank-outline"
        self._attr_unique_id = f"{self.account.account_number}__saving_sessions"
    

    async def async_update(self) -> None:
        await self.account._load_saving_sessions()
        if self.account.saving_sessions:
            # Count active/upcoming sessions
            now = dt_util.now()
            upcoming = []
            active = []
            
            for s in self.account.saving_sessions:
                start_str = s.get('startedAt') or s.get('startAt')
                end_str = s.get('endedAt') or s.get('endAt')
                
                if start_str:
                    start_dt = dt_util.parse_datetime(start_str)
                    if start_dt > now:
                        upcoming.append(s)
                    elif end_str:
                        end_dt = dt_util.parse_datetime(end_str)
                        if start_dt <= now <= end_dt:
                            active.append(s)

            self._attr_native_value = len(upcoming) + len(active)
            self._attr_extra_state_attributes = {
                "active_count": len(active),
                "upcoming_count": len(upcoming),
                "sessions": [
                    {
                        "id": s.get('id'),
                        "start": s.get('startedAt') or s.get('startAt'),
                        "type": s.get('type')
                    }
                    for s in self.account.saving_sessions
                ]
            }
        else:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "active_count": 0,
                "upcoming_count": 0,
                "sessions": []
            }
