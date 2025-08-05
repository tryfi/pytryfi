import datetime
import logging
from .common import query
from .const import PET_ACTIVITY_ONGOINGWALK
from .exceptions import *
from .fiDevice import FiDevice
from sentry_sdk import capture_exception

LOGGER = logging.getLogger(__name__)

class FiPet(object):
    def __init__(self, petId):
        self._petId = petId

    def setPetDetailsJSON(self, petJSON: dict):
        self._name = petJSON.get('name')
        self._homeCityState = petJSON.get('homeCityState')
        try:
            self._yearOfBirth = int(petJSON['yearOfBirth'])
        except:
            LOGGER.warning(f"Unknown Year of Birth")
            self._yearOfBirth = 1900
        try:
            self._monthOfBirth = int(petJSON['monthOfBirth'])
        except:
            LOGGER.warning(f"Unknown Month of Birth")
            self._monthOfBirth = 1
        try:
            self._dayOfBirth = int(petJSON['dayOfBirth'])
        except:
            LOGGER.warning(f"Unknown day of birth")
            self._dayOfBirth = None
        self._gender = petJSON.get('gender')
        self._weight = float(petJSON['weight']) if 'weight' in petJSON else None
        try:
            self._breed = petJSON['breed']['name']
        except:
            LOGGER.warning(f"Unknown Breed of Dog")
            self._breed = None
            #track last updated
        self._lastUpdated = datetime.datetime.now()
        try:
            self._photoLink = petJSON['photos']['first']['image']['fullSize']
        except Exception as e:
            #capture_exception(e)
            LOGGER.warning(f"Cannot find photo of your pet. Defaulting to empty string.")
            self._photoLink = ""
        # Check if pet has a device
        if petJSON.get('device'):
            self._device = FiDevice(petJSON['device']['id'])
            self._device.setDeviceDetailsJSON(petJSON['device'])
            self._connectedTo = self.setConnectedTo(petJSON['device']['lastConnectionState'])
        else:
            self._device = None
            self._connectedTo = None
            LOGGER.info(f"Pet {self._name} has no device assigned")
        
        # Initialize behavior metrics to 0 (will be updated later if available)
        self._dailyBarkingCount = 0
        self._dailyBarkingDuration = 0
        self._weeklyBarkingCount = 0
        self._weeklyBarkingDuration = 0
        self._monthlyBarkingCount = 0
        self._monthlyBarkingDuration = 0
        
        self._dailyLickingCount = 0
        self._dailyLickingDuration = 0
        self._weeklyLickingCount = 0
        self._weeklyLickingDuration = 0
        self._monthlyLickingCount = 0
        self._monthlyLickingDuration = 0
        
        self._dailyScratchingCount = 0
        self._dailyScratchingDuration = 0
        self._weeklyScratchingCount = 0
        self._weeklyScratchingDuration = 0
        self._monthlyScratchingCount = 0
        self._monthlyScratchingDuration = 0
        
        self._dailyEatingCount = 0
        self._dailyEatingDuration = 0
        self._weeklyEatingCount = 0
        self._weeklyEatingDuration = 0
        self._monthlyEatingCount = 0
        self._monthlyEatingDuration = 0
        
        self._dailyDrinkingCount = 0
        self._dailyDrinkingDuration = 0
        self._weeklyDrinkingCount = 0
        self._weeklyDrinkingDuration = 0
        self._monthlyDrinkingCount = 0
        self._monthlyDrinkingDuration = 0

    def __str__(self):
        return f"Last Updated - {self.lastUpdated} - Pet ID: {self.petId} Name: {self.name} Is Lost: {self.isLost} From: {self.homeCityState} ActivityType: {self.activityType} Located: {self.currLatitude},{self.currLongitude} Last Updated: {self.currStartTime}\n \
            using Device/Collar: {self._device}"
    
    # set the Pet's current location details
    def setCurrentLocation(self, activityJSON):
        activityType = activityJSON['__typename']
        self._activityType = activityType
        self._areaName = activityJSON['areaName']
        try:
            if activityType == PET_ACTIVITY_ONGOINGWALK:
                positionSize = len(activityJSON['positions'])
                currentPosition = activityJSON['positions'][positionSize-1]['position']
                self._currLongitude = float(currentPosition['longitude'])
                self._currLatitude = float(currentPosition['latitude'])          
            else:
                self._currLongitude = float(activityJSON['position']['longitude'])
                self._currLatitude = float(activityJSON['position']['latitude'])
            self._currStartTime = datetime.datetime.fromisoformat(activityJSON['start'].replace('Z', '+00:00'))

            if 'place' in activityJSON:
                self._currPlaceName = activityJSON['place']['name']
                self._currPlaceAddress = activityJSON['place']['address']
            else:
                self._currPlaceName = None
                self._currPlaceAddress = None
            self._lastUpdated = datetime.datetime.now()
        except TryFiError as e:
            capture_exception(e)
            LOGGER.error(f"Unable to set values Current Location for Pet {self.name}.\nException: {e}\nwhile parsing {activityJSON}")
            raise TryFiError("Unable to set Pet Location Details")
        except Exception as e:
            capture_exception(e)

    def setConnectedTo(self, connectedToJSON):
        connectedToString = ""
        typename = connectedToJSON['__typename']
        if typename == 'ConnectedToUser':
            connectedToString = connectedToJSON['user']['firstName'] + " " + connectedToJSON['user']['lastName']
        elif typename == 'ConnectedToCellular':
            connectedToString = "Cellular Signal Strength - " + str(connectedToJSON['signalStrengthPercent'])
        elif typename == 'ConnectedToBase':
            connectedToString = "Base ID - " + connectedToJSON['chargingBase']['id']
        else:
            connectedToString = None
        return connectedToString

    # set the Pet's current steps, goals and distance details for daily, weekly and monthly
    def setStats(self, activityJSONDaily, activityJSONWeekly, activityJSONMonthly):
            #distance is in metres
        self._dailyGoal = int(activityJSONDaily['stepGoal'])
        self._dailySteps = int(activityJSONDaily['totalSteps'])
        self._dailyTotalDistance = float(activityJSONDaily['totalDistance'])
        self._weeklyGoal = int(activityJSONWeekly['stepGoal'])
        self._weeklySteps = int(activityJSONWeekly['totalSteps'])
        self._weeklyTotalDistance = float(activityJSONWeekly['totalDistance'])
        self._monthlyGoal = int(activityJSONMonthly['stepGoal'])
        self._monthlySteps = int(activityJSONMonthly['totalSteps'])
        self._monthlyTotalDistance = float(activityJSONMonthly['totalDistance'])

        self._lastUpdated = datetime.datetime.now()

    # set the Pet's behavior stats for daily, weekly and monthly
    def setBehaviorStats(self, behaviorTrends):
        # Initialize all behavior metrics to 0 as default
        self._dailyBarkingCount = 0
        self._dailyBarkingDuration = 0
        self._weeklyBarkingCount = 0
        self._weeklyBarkingDuration = 0
        self._monthlyBarkingCount = 0
        self._monthlyBarkingDuration = 0
        
        self._dailyLickingCount = 0
        self._dailyLickingDuration = 0
        self._weeklyLickingCount = 0
        self._weeklyLickingDuration = 0
        self._monthlyLickingCount = 0
        self._monthlyLickingDuration = 0
        
        self._dailyScratchingCount = 0
        self._dailyScratchingDuration = 0
        self._weeklyScratchingCount = 0
        self._weeklyScratchingDuration = 0
        self._monthlyScratchingCount = 0
        self._monthlyScratchingDuration = 0
        
        self._dailyEatingCount = 0
        self._dailyEatingDuration = 0
        self._weeklyEatingCount = 0
        self._weeklyEatingDuration = 0
        self._monthlyEatingCount = 0
        self._monthlyEatingDuration = 0
        
        self._dailyDrinkingCount = 0
        self._dailyDrinkingDuration = 0
        self._weeklyDrinkingCount = 0
        self._weeklyDrinkingDuration = 0
        self._monthlyDrinkingCount = 0
        self._monthlyDrinkingDuration = 0
        
        try:
            # Parse the new health trends API format
            for trend in behaviorTrends:
                if not isinstance(trend, dict):
                    continue
                    
                trend_id = trend.get('id', '')
                summary = trend.get('summaryComponents', {})
                
                # Extract events count from eventsSummary (e.g., "10 events")
                events_summary = summary.get('eventsSummary', '0 events')
                events_count = 0
                if 'event' in events_summary:
                    try:
                        events_count = int(events_summary.split()[0])
                    except:
                        pass
                
                # Extract duration from durationSummary (e.g., "7m" or "1h 5m")
                duration_summary = summary.get('durationSummary', '0m')
                duration_seconds = 0
                try:
                    # Handle "<1m" case
                    if duration_summary.startswith('<'):
                        duration_seconds = 30  # Assume 30 seconds for <1m
                    else:
                        # Parse hours and minutes
                        parts = duration_summary.replace('h', '').replace('m', '').split()
                        if len(parts) == 2:  # "1h 5m" format
                            duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
                        elif 'h' in duration_summary:  # "1h" format
                            duration_seconds = int(parts[0]) * 3600
                        else:  # "5m" format
                            duration_seconds = int(parts[0]) * 60
                except:
                    pass
                
                # Map trend IDs to our attributes (daily stats only for now)
                if trend_id == 'barking:DAY':
                    self._dailyBarkingCount = events_count
                    self._dailyBarkingDuration = duration_seconds
                elif trend_id == 'cleaning_self:DAY':  # This is licking
                    self._dailyLickingCount = events_count
                    self._dailyLickingDuration = duration_seconds
                elif trend_id == 'scratching:DAY':
                    self._dailyScratchingCount = events_count
                    self._dailyScratchingDuration = duration_seconds
                elif trend_id == 'eating:DAY':
                    self._dailyEatingCount = events_count
                    self._dailyEatingDuration = duration_seconds
                elif trend_id == 'drinking:DAY':
                    self._dailyDrinkingCount = events_count
                    self._dailyDrinkingDuration = duration_seconds
                    
        except Exception as e:
            LOGGER.warning(f"Unable to parse behavior metrics for Pet {self.name}. This may be an older collar model.\nException: {e}")
            capture_exception(e)

    # set the Pet's current rest details for daily, weekly and monthly
    def setRestStats(self, restJSONDaily, restJSONWeekly, restJSONMonthly):
        #setting default values to zero in case this feature is not supported by older collars
        self._dailyNap = 0
        self._dailySleep = 0
        self._weeklyNap = 0
        self._weeklySleep = 0
        self._monthlyNap = 0
        self._monthlySleep = 0
        try:
            for sleepAmount in restJSONDaily['restSummaries'][0]['data']['sleepAmounts']:
                if sleepAmount['type'] == 'SLEEP':
                    self._dailySleep = int(sleepAmount['duration'])
                if sleepAmount['type'] == "NAP":
                    self._dailyNap = int(sleepAmount['duration'])
        except TryFiError as e:
            LOGGER.error(f"Unable to set values Daily Rest Stats for Pet {self.name}.\nException: {e}\nwhile parsing {restJSONDaily}")
            capture_exception(e)
            raise TryFiError("Unable to set Pet Daily Rest Stats")
        except Exception as e:
            capture_exception(e)
        try:
            for sleepAmount in restJSONWeekly['restSummaries'][0]['data']['sleepAmounts']:
                if sleepAmount['type'] == 'SLEEP':
                    self._weeklySleep = int(sleepAmount['duration'])
                if sleepAmount['type'] == 'NAP':
                    self._weeklyNap = int(sleepAmount['duration'])
        except TryFiError as e:
            LOGGER.error(f"Unable to set values Weekly Rest Stats for Pet {self.name}.\nException: {e}\nwhile parsing {restJSONWeekly}")
            capture_exception(e)
            raise TryFiError("Unable to set Pet Weekly Rest Stats")
        except Exception as e:
            capture_exception(e)
        try:
            for sleepAmount in restJSONMonthly['restSummaries'][0]['data']['sleepAmounts']:
                if sleepAmount['type'] == 'SLEEP':
                    self._monthlySleep = int(sleepAmount['duration'])
                if sleepAmount['type'] == 'NAP':
                    self._monthlyNap = int(sleepAmount['duration'])
        except TryFiError as e:
            LOGGER.error(f"Unable to set values Monthly Rest Stats for Pet {self.name}.\nException: {e}\nwhile parsing {restJSONMonthly}")
            capture_exception(e)
            raise TryFiError("Unable to set Pet Monthly Rest Stats")
        except Exception as e:
            capture_exception(e)

    # Update the Stats of the pet
    def updateStats(self, sessionId):
        try:
            pStatsJSON = query.getCurrentPetStats(sessionId,self.petId)
            self.setStats(pStatsJSON['dailyStat'],pStatsJSON['weeklyStat'],pStatsJSON['monthlyStat'])
            return True
        except Exception as e:
            LOGGER.error(f"Could not update stats for Pet {self.name}.\n{e}")
            capture_exception(e)

    # Update the Stats of the pet
    def updateRestStats(self, sessionId):
        try:
            pRestStatsJSON = query.getCurrentPetRestStats(sessionId,self.petId)
            self.setRestStats(pRestStatsJSON['dailyStat'],pRestStatsJSON['weeklyStat'],pRestStatsJSON['monthlyStat'])
            return True
        except Exception as e:
            LOGGER.error(f"Could not update rest stats for Pet {self.name}.\n{e}")
            capture_exception(e)

    # Update the behavior stats of the pet
    def updateBehaviorStats(self, sessionId):
        try:
            # Get health trends which include behavior data
            healthTrendsJSON = query.getPetHealthTrends(sessionId, self.petId, 'DAY')
            behavior_trends = healthTrendsJSON.get('behaviorTrends', [])
            self.setBehaviorStats(behavior_trends)
            return True
        except Exception as e:
            LOGGER.warning(f"Could not update behavior stats for Pet {self.name}. This may be an older collar model.\n{e}")
            # Don't capture exception for behavior stats as they may not be available on older collars
            return False

    # Update the Pet's GPS location
    def updatePetLocation(self, sessionId):
        try:
            pLocJSON = query.getCurrentPetLocation(sessionId,self.petId)
            self.setCurrentLocation(pLocJSON)
            return True
        except Exception as e:
            LOGGER.error(f"Could not update Pet: {self.name}'s location.\n{e}")
            capture_exception(e)
            return False
    
    # Update the device/collar details for this pet
    def updateDeviceDetails(self, sessionId):
        try:
            deviceJSON = query.getDevicedetails(sessionId, self.petId)
            self.device.setDeviceDetailsJSON(deviceJSON['device'])
            return True
        except Exception as e:
            LOGGER.error(f"Could not update Device/Collar information for Pet: {self.name}\n{e}")
            capture_exception(e)
            return False

    # Update all details regarding this pet
    def updateAllDetails(self, sessionId):
        self.updateDeviceDetails(sessionId)
        self.updatePetLocation(sessionId)
        self.updateStats(sessionId)
        self.updateRestStats(sessionId)
        self.updateBehaviorStats(sessionId)  # Now supported via health trends API

    # set the color code of the led light on the pet collar
    def setLedColorCode(self, sessionId, colorCode):
        try:
            moduleId = self.device.moduleId
            ledColorCode = int(colorCode)
            setColorJSON = query.setLedColor(sessionId, moduleId, ledColorCode)
            try:  
                self.device.setDeviceDetailsJSON(setColorJSON['setDeviceLed'])
            except Exception as e:
                LOGGER.warning(f"Updated LED Color but could not get current status for Pet: {self.name}\nException: {e}")
                capture_exception(e)
            return True
        except Exception as e:
            LOGGER.error(f"Could not complete Led Color request:\n{e}")
            capture_exception(e)
            return False
    
    # turn on or off the led light. action = True will enable the light, false turns off the light
    def turnOnOffLed(self, sessionId, action):
        try:
            moduleId = self.device.moduleId
            onOffResponse = query.turnOnOffLed(sessionId, moduleId, action)
            try:
                self.device.setDeviceDetailsJSON(onOffResponse['updateDeviceOperationParams'])
            except Exception as e:
                LOGGER.warning(f"Action: {action} was successful however unable to get current status for Pet: {self.name}")
                capture_exception(e)
            return True
        except Exception as e:
            LOGGER.error(f"Could not complete LED request:\n{e}")
            capture_exception(e)
            return False

    # set the lost dog mode to Normal or Lost Dog. Action is true for lost dog and false for normal (not lost)
    def setLostDogMode(self, sessionId, action):
        try:
            moduleId = self.device.moduleId
            petModeResponse = query.setLostDogMode(sessionId, moduleId, action)
            try:
                self.device.setDeviceDetailsJSON(petModeResponse['updateDeviceOperationParams'])
            except Exception as e:
                LOGGER.warning(f"Action: {action} was successful however unable to get current status for Pet: {self.name}")
                capture_exception(e)
            return True
        except Exception as e:
            LOGGER.error(f"Could not complete turn on/off light where ledEnable is {action}.\nException: {e}")
            capture_exception(e)
            return False

    @property
    def device(self):
        return self._device
    @property
    def petId(self):
        return self._petId
    @property
    def name(self):
        return self._name
    @property
    def homeCityState(self):
        return self._homeCityState
    @property
    def yearOfBirth(self):
        return self._yearOfBirth
    @property
    def monthOfBirth(self):
        return self._monthOfBirth
    @property
    def dayOfBirth(self):
        return self._dayOfBirth
    @property
    def gender(self):
        return self._gender
    @property
    def weight(self):
        return self._weight
    @property
    def breed(self):
        return self._breed
    @property
    def photoLink(self):
        return self._photoLink
    @property
    def currLongitude(self):
        return self._currLongitude
    @property
    def currLatitude(self):
        return self._currLatitude
    @property
    def currStartTime(self):
        return self._currStartTime
    @property
    def currPlaceName(self):
        return self._currPlaceName
    @property
    def currPlaceAddress(self):
        return self._currPlaceAddress
    @property
    def dailyGoal(self):
        return self._dailyGoal
    @property
    def dailySteps(self):
        return self._dailySteps
    @property
    def dailyTotalDistance(self):
        return self._dailyTotalDistance
    @property
    def weeklyGoal(self):
        return self._weeklyGoal
    @property
    def weeklySteps(self):
        return self._weeklySteps
    @property
    def weeklyTotalDistance(self):
        return self._weeklyTotalDistance
    @property
    def monthlyGoal(self):
        return self._monthlyGoal
    @property
    def monthlySteps(self):
        return self._monthlySteps
    @property
    def monthlyTotalDistance(self):
        return self._monthlyTotalDistance

    @property
    def dailySleep(self):
        return self._dailySleep
    @property
    def weeklySleep(self):
        return self._weeklySleep
    @property
    def monthlySleep(self):
        return self._monthlySleep
    @property
    def dailyNap(self):
        return self._dailyNap
    @property
    def weeklyNap(self):
        return self._weeklyNap
    @property
    def monthlyNap(self):
        return self._monthlyNap
    
    # Barking properties
    @property
    def dailyBarkingCount(self):
        return self._dailyBarkingCount
    @property
    def dailyBarkingDuration(self):
        return self._dailyBarkingDuration
    @property
    def weeklyBarkingCount(self):
        return self._weeklyBarkingCount
    @property
    def weeklyBarkingDuration(self):
        return self._weeklyBarkingDuration
    @property
    def monthlyBarkingCount(self):
        return self._monthlyBarkingCount
    @property
    def monthlyBarkingDuration(self):
        return self._monthlyBarkingDuration
    
    # Licking properties
    @property
    def dailyLickingCount(self):
        return self._dailyLickingCount
    @property
    def dailyLickingDuration(self):
        return self._dailyLickingDuration
    @property
    def weeklyLickingCount(self):
        return self._weeklyLickingCount
    @property
    def weeklyLickingDuration(self):
        return self._weeklyLickingDuration
    @property
    def monthlyLickingCount(self):
        return self._monthlyLickingCount
    @property
    def monthlyLickingDuration(self):
        return self._monthlyLickingDuration
    
    # Scratching properties
    @property
    def dailyScratchingCount(self):
        return self._dailyScratchingCount
    @property
    def dailyScratchingDuration(self):
        return self._dailyScratchingDuration
    @property
    def weeklyScratchingCount(self):
        return self._weeklyScratchingCount
    @property
    def weeklyScratchingDuration(self):
        return self._weeklyScratchingDuration
    @property
    def monthlyScratchingCount(self):
        return self._monthlyScratchingCount
    @property
    def monthlyScratchingDuration(self):
        return self._monthlyScratchingDuration
    
    # Eating properties
    @property
    def dailyEatingCount(self):
        return self._dailyEatingCount
    @property
    def dailyEatingDuration(self):
        return self._dailyEatingDuration
    @property
    def weeklyEatingCount(self):
        return self._weeklyEatingCount
    @property
    def weeklyEatingDuration(self):
        return self._weeklyEatingDuration
    @property
    def monthlyEatingCount(self):
        return self._monthlyEatingCount
    @property
    def monthlyEatingDuration(self):
        return self._monthlyEatingDuration
    
    # Drinking properties
    @property
    def dailyDrinkingCount(self):
        return self._dailyDrinkingCount
    @property
    def dailyDrinkingDuration(self):
        return self._dailyDrinkingDuration
    @property
    def weeklyDrinkingCount(self):
        return self._weeklyDrinkingCount
    @property
    def weeklyDrinkingDuration(self):
        return self._weeklyDrinkingDuration
    @property
    def monthlyDrinkingCount(self):
        return self._monthlyDrinkingCount
    @property
    def monthlyDrinkingDuration(self):
        return self._monthlyDrinkingDuration

    @property
    def lastUpdated(self):
        return self._lastUpdated
    @property
    def isLost(self):
        return self.device.isLost
    @property
    def activityType(self):
        return self._activityType
    @property
    def areaName(self):
        return self._areaName
    
    @property
    def connectedTo(self):
        return self._connectedTo
    
    def getCurrPlaceName(self):
        return self.currPlaceName
    
    def getCurrPlaceAddress(self):
        return self.currPlaceAddress

    def getActivityType(self):
        return self.activityType

    def getBirthDate(self):
        return datetime.datetime(self.yearOfBirth, self.monthOfBirth, self.dayOfBirth)
    
    def getDailySteps(self):
        return self.dailySteps
    
    def getDailyGoal(self):
        return self.dailyGoal

    def getDailyDistance(self):
        return self.dailyTotalDistance

    def getWeeklySteps(self):
        return self.weeklySteps
    
    def getWeeklyGoal(self):
        return self.weeklyGoal

    def getWeeklyDistance(self):
        return self.weeklyTotalDistance

    def getMonthlySteps(self):
        return self.monthlySteps
    
    def getMonthlyGoal(self):
        return self.monthlyGoal

    def getMonthlyDistance(self):
        return self.monthlyTotalDistance
        
