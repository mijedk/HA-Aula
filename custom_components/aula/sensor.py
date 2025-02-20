from .const import DOMAIN
import logging

from datetime import datetime, timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup sensor platform"""

    async def async_update_data():
        #try:
        client = hass.data[DOMAIN]["client"]
        await hass.async_add_executor_job(client.update_data)
        #except Exception as e:
        #    raise UpdateFailed(f"Error communicating with server: {e}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5)
    )

    # Immediate refresh
    await coordinator.async_request_refresh()
    
    entities = []
    client = hass.data[DOMAIN]["client"]
    for i, child in enumerate(client._children):     
        if str(child["id"]) in client._daily_overview:
            entities.append(AulaSensor(hass, coordinator, child))
    async_add_entities(entities)

class AulaSensor(Entity):
    def __init__(self, hass, coordinator, child) -> None:
        self._hass = hass
        self._coordinator = coordinator
        self._child = child
        self._client = hass.data[DOMAIN]["client"]

    @property
    def name(self):
        try:
            group_name = self._client._daily_overview[str(self._child["id"])]["mainGroup"]["name"]
        except:
            group_name = "Aula"
        _LOGGER.debug("Sensor name: " + group_name + " " + self._child["name"].split()[0])
        return group_name + " " + self._child["name"].split()[0]

    @property
    def state(self):
        """
            0 = IKKE KOMMET
            1 = SYG
            2 = FERIE/FRI
            3 = KOMMET/TIL STEDE
            5 = SOVER
            8 = HENTET/GÅET
        """

        states = ["Ikke kommet", "Syg", "Ferie/Fri", "Kommet/Til stede", "4", "Sover", "6", "7", "Gået", "9", "10", "11", "12", "13", "14", "15"]
        daily_info = self._client._daily_overview[str(self._child["id"])]

        return states[daily_info["status"]]

    @property
    def extra_state_attributes(self):
        daily_info = self._client._daily_overview[str(self._child["id"])]
        
        fields = ['location', 'sleepIntervals', 'checkInTime', 'checkOutTime', 'activityType', 'entryTime', 'exitTime', 'exitWith', 'comment', 'spareTimeActivity', 'selfDeciderStartTime', 'selfDeciderEndTime']
        attributes = {}
        for attribute in fields:
            attributes[attribute] = daily_info[attribute]
        return attributes
        

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self._coordinator.last_update_success

    async def async_update(self):
        """Update the entity. Only used by the generic entity update service."""
        await self._coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )
