import logging
import datetime
import json
from .ledColors import ledColors
from .const import PET_MODE_NORMAL, PET_MODE_LOST
from sentry_sdk import capture_exception

LOGGER = logging.getLogger(__name__)

class FiDevice(object):
    def __init__(self, deviceId):
        self._deviceId = deviceId
    
    def setDeviceDetailsJSON(self, deviceJSON):
        try:
            # Log the raw device JSON to see what fields are available
            LOGGER.info(f"TryFi Device {deviceJSON.get('moduleId', 'unknown')} info field contains: {list(deviceJSON.get('info', {}).keys())}")
            LOGGER.info(f"TryFi Device {deviceJSON.get('moduleId', 'unknown')} root fields: {list(deviceJSON.keys())}")
            
            self._moduleId = deviceJSON['moduleId']
            self._buildId = deviceJSON['info']['buildId']
            self._batteryPercent = int(deviceJSON['info']['batteryPercent'])
            
            #V1 of the collar has this parameter but V2 it is missing
            try:
                self._isCharging = bool(deviceJSON['info']['isCharging'])
            except Exception as e1:
                self._isCharging = False
            
            #self._batteryHealth = deviceJSON['info']['batteryHealth']  
            self._ledOffAt = self.setLedOffAtDate(deviceJSON['operationParams']['ledOffAt'])
            self._ledOn = self.getAccurateLEDStatus( bool(deviceJSON['operationParams']['ledEnabled']))
            self._mode = deviceJSON['operationParams']['mode']
            self._ledColor = deviceJSON['ledColor']['name']
            self._ledColorHex = deviceJSON['ledColor']['hexCode']
            self._connectionStateDate = datetime.datetime.fromisoformat(str(deviceJSON['lastConnectionState']['date']).replace('Z', '+00:00'))
            self._connectionStateType = deviceJSON['lastConnectionState']['__typename']
            self._availableLedColors = []
            self._lastUpdated = datetime.datetime.now()
            for cString in deviceJSON['availableLedColors']:
                c = ledColors(int(cString['ledColorCode']),cString['hexCode'], cString['name'] )
                self._availableLedColors.append(c)
            
            # Enhanced device fields (may not be available on older collars)
            self._hardwareRevision = deviceJSON.get('hardwareRevision', 'Unknown')
            
            # Extract additional info fields if available
            info = deviceJSON.get('info', {})
            self._batteryVoltage = info.get('batteryVoltage', None)
            self._temperature = info.get('temperature', None)
            self._uptime = info.get('uptime', None)
            
            # Log other available fields for investigation
            LOGGER.info(f"TryFi Device - wifiNetworkNames: {info.get('wifiNetworkNames', 'N/A')}")
            LOGGER.info(f"TryFi Device - capabilityFlags: {info.get('capabilityFlags', 'N/A')}")
            LOGGER.info(f"TryFi Device - deviceStats: {info.get('deviceStats', 'N/A')}")
            LOGGER.info(f"TryFi Device - selfTestResults: {info.get('selfTestResults', 'N/A')}")
            LOGGER.info(f"TryFi Device - wallClockSec: {info.get('wallClockSec', 'N/A')}")
            LOGGER.info(f"TryFi Device - batteryResistanceProfile: {info.get('batteryResistanceProfile', 'N/A')}")
            
            # Extract more useful fields
            self._wifiNetworkNames = info.get('wifiNetworkNames', [])
            self._capabilityFlags = info.get('capabilityFlags', {})
            self._deviceStats = info.get('deviceStats', {})
            self._selfTestResults = info.get('selfTestResults', {})
            self._wallClockSec = info.get('wallClockSec', None)
            
            # Try to get signal strength from connection state if available
            if 'lastConnectionState' in deviceJSON and deviceJSON['lastConnectionState'].get('__typename') == 'ConnectedToCellular':
                self._signalStrength = deviceJSON['lastConnectionState'].get('signalStrengthPercent', None)
            else:
                self._signalStrength = None
        except Exception as e:
            LOGGER.debug(f"tryfi Error: {e}")
            capture_exception(e)

    def __str__(self):
        return f"Last Updated - {self.lastUpdated} - Device ID: {self.deviceId} Device Mode: {self.mode} Battery Left: {self.batteryPercent}% LED State: {self.ledOn} Last Connected: {self.connectionStateDate} by: {self.connectionStateType}"

    @property
    def deviceId(self):
        return self._deviceId
    @property
    def moduleId(self):
        return self._moduleId
    @property
    def mode(self):
        return self._mode
    @property
    def buildId(self):
        return self._buildId
    @property
    def batteryPercent(self):
        return self._batteryPercent
    #This was deprecated in the newer collars
    #@property
    #def batteryHealth(self):
    #    return self._batteryHealth
    @property
    def isCharging(self):
        return self._isCharging
    @property
    def ledOn(self):
        return self._ledOn
    @property
    def ledOffAt(self):
        return self._ledOffAt
    @property
    def ledColor(self):
        return self._ledColor
    @property
    def ledColorHex(self):
        return self._ledColorHex
    @property
    def connectionStateDate(self):
        return self._connectionStateDate
    @property
    def connectionStateType(self):
        return self._connectionStateType
    @property
    def availableLedColors(self):
        return self._availableLedColors
    @property
    def lastUpdated(self):
        return self._lastUpdated
    @property
    def isLost(self):
        if self._mode == PET_MODE_LOST:
            return True
        else:
            return False
    @property
    def hardwareRevision(self):
        return self._hardwareRevision
    @property
    def signalStrength(self):
        return self._signalStrength
    
    @property
    def batteryVoltage(self):
        return self._batteryVoltage
    
    @property
    def temperature(self):
        return self._temperature
    
    @property
    def uptime(self):
        return self._uptime
    
    @property
    def wifiNetworkNames(self):
        return self._wifiNetworkNames
    
    @property
    def capabilityFlags(self):
        return self._capabilityFlags
    
    @property
    def deviceStats(self):
        return self._deviceStats
    
    @property
    def selfTestResults(self):
        return self._selfTestResults
    
    @property
    def wallClockSec(self):
        return self._wallClockSec

#This is created because if TryFi automatically turns off the LED, the status is still set to true in the api.
#This will compare the dates to see if the current date/time is greater than the turnoffat time in the api.
    def getAccurateLEDStatus(self, ledStatus):
        if ledStatus is False:
            LOGGER.debug("getAccurateLedStatus: LED Status is False")
            return False
        else:
            LOGGER.debug("getAccurateLedStatus: LED Status is True... comparing date/times")
            currentDateTime = datetime.datetime.now(datetime.timezone.utc)
            if currentDateTime > self.ledOffAt:
                LOGGER.debug(f"Current datetime: {currentDateTime} is greater than ledOffAt: {self.ledOffAt}, Returning False")
                return False
            else:
                LOGGER.debug(f"Current datetime: {currentDateTime} is less than ledOffAt: {self.ledOffAt}, Returning False")
                return True
#Created function to return a date/time regardless.
    def setLedOffAtDate(self, ledOffAt):
        if ledOffAt == None:
            ## if object is null, return current date/time in UTC
            LOGGER.debug("LedOffAt is None, returning current datetime in UTC")
            return datetime.datetime.now(datetime.timezone.utc)
        else:
            LOGGER.debug(f"LedOffAt has date/time of {ledOffAt}. Returning this in ISO Format.")
            return datetime.datetime.fromisoformat(str(ledOffAt).replace('Z', '+00:00'))