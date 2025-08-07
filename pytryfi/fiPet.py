import datetime
import logging
from pytryfi.common import query
from pytryfi.const import PET_ACTIVITY_ONGOINGWALK
from pytryfi.exceptions import *
from pytryfi.fiDevice import FiDevice
from sentry_sdk import capture_exception

LOGGER = logging.getLogger(__name__)

class FiPet(object):
    def __init__(self, petId):
        self._petId = petId
        self._name = None  # Initialize to None, will be set by setPetDetailsJSON

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
        self._device = FiDevice(petJSON['device']['id'])
        self._device.setDeviceDetailsJSON(petJSON['device'])
        self._connectedTo = self.setConnectedTo(petJSON['device']['lastConnectionState'])

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
            LOGGER.info(f"Updating behavior stats for pet {self.name or 'unknown'} (ID: {self.petId})")
            # Get health trends which include behavior data
            healthTrendsJSON = query.getPetHealthTrends(sessionId, self.petId, 'DAY')
            LOGGER.info(f"Got health trends response for {self.name or 'unknown'}: {healthTrendsJSON}")
            behavior_trends = healthTrendsJSON.get('behaviorTrends', [])
            LOGGER.info(f"Found {len(behavior_trends)} behavior trends for {self.name or 'unknown'}")
            self.setBehaviorStatsFromTrends(behavior_trends)
            return True
        except Exception as e:
            LOGGER.warning(f"Could not update behavior stats for Pet {self.name or 'unknown'}. This may be an older collar model.\n{e}")
            # Don't capture exception for behavior stats as they may not be available on older collars
            return False

    # Parse behavior timeline data from health trends API
    def setBehaviorStatsFromTrends(self, behaviorTrends):
        """Parse behavior data from health trends API including timeline"""
        LOGGER.info(f"setBehaviorStatsFromTrends called for {self.name or 'unknown pet'} with {len(behaviorTrends)} trends")
        
        # Initialize all behavior metrics to 0 as default
        self._dailyBarkingCount = 0
        self._dailyBarkingDuration = 0
        self._dailyLickingCount = 0
        self._dailyLickingDuration = 0
        self._dailyScratchingCount = 0
        self._dailyScratchingDuration = 0
        self._dailyEatingCount = 0
        self._dailyEatingDuration = 0
        self._dailyDrinkingCount = 0
        self._dailyDrinkingDuration = 0
        
        # Initialize timeline
        self._behaviorTimeline = []
        
        try:
            # Parse the new health trends API format
            for trend in behaviorTrends:
                if not isinstance(trend, dict):
                    continue
                    
                trend_id = trend.get('id', '')
                summary = trend.get('summaryComponents', {})
                
                # Extract events count from eventsSummary (e.g., "10 events")
                events_summary = summary.get('eventsSummary')
                events_count = 0
                if events_summary and 'event' in events_summary:
                    try:
                        events_count = int(events_summary.split()[0])
                    except:
                        pass
                
                # Extract duration from durationSummary (e.g., "7m" or "1h 5m")
                duration_summary = summary.get('durationSummary')
                duration_seconds = 0
                if duration_summary:
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
                
                # Parse timeline data if available
                chart = trend.get('chart', {})
                if chart.get('__typename') == 'PetHealthTrendSegmentedTimeline':
                    timeline_events = self._parseTimelineSegments(trend_id, trend.get('title', ''), chart)
                    self._behaviorTimeline.extend(timeline_events)
                
                # Map trend IDs to our attributes (daily stats only for now)
                if trend_id == 'barking:DAY':
                    self._dailyBarkingCount = events_count
                    self._dailyBarkingDuration = duration_seconds
                elif trend_id == 'cleaning_self:DAY':  # This is licking
                    self._dailyLickingCount = events_count
                    self._dailyLickingDuration = duration_seconds
                    LOGGER.info(f"Set {self.name or 'unknown pet'} licking: {events_count} events, {duration_seconds} seconds")
                elif trend_id == 'scratching:DAY':
                    self._dailyScratchingCount = events_count
                    self._dailyScratchingDuration = duration_seconds
                    LOGGER.info(f"Set {self.name or 'unknown pet'} scratching: {events_count} events, {duration_seconds} seconds")
                elif trend_id == 'eating:DAY':
                    self._dailyEatingCount = events_count
                    self._dailyEatingDuration = duration_seconds
                elif trend_id == 'drinking:DAY':
                    self._dailyDrinkingCount = events_count
                    self._dailyDrinkingDuration = duration_seconds
                    
        except Exception as e:
            LOGGER.warning(f"Unable to parse behavior metrics for Pet {self.name or 'unknown'}. This may be an older collar model.\nException: {e}")
            capture_exception(e)
    
    def _parseTimelineSegments(self, trend_id, title, chart):
        """Parse timeline segments to extract individual behavior events"""
        events = []
        
        try:
            segments = chart.get('segments', [])
            if not segments:
                return events
            
            # Identify background color (most common duration)
            color_durations = {}
            for seg in segments:
                color = seg.get('color', '')
                duration = seg.get('length', 0)
                if color not in color_durations:
                    color_durations[color] = 0
                color_durations[color] += duration
            
            # Background color has the most total duration
            if color_durations:
                background_color = max(color_durations.items(), key=lambda x: x[1])[0]
                
                # Extract events (non-background segments)
                for seg in segments:
                    if seg.get('color') != background_color and seg.get('length', 0) > 0:
                        # Get midnight of current day
                        from datetime import datetime, timedelta
                        now = datetime.now()
                        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        # Calculate event time
                        start_time = midnight + timedelta(seconds=seg.get('offset', 0))
                        end_time = midnight + timedelta(seconds=seg.get('offset', 0) + seg.get('length', 0))
                        
                        # Determine behavior type from trend_id
                        behavior_type = 'unknown'
                        if 'barking' in trend_id:
                            behavior_type = 'barking'
                        elif 'cleaning_self' in trend_id:
                            behavior_type = 'licking'
                        elif 'scratching' in trend_id:
                            behavior_type = 'scratching'
                        elif 'eating' in trend_id:
                            behavior_type = 'eating'
                        elif 'drinking' in trend_id:
                            behavior_type = 'drinking'
                        
                        events.append({
                            'type': behavior_type,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration_seconds': seg.get('length', 0)
                        })
                        
        except Exception as e:
            LOGGER.debug(f"Error parsing timeline segments: {e}")
            
        return events

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
        self.updateBehaviorStats(sessionId)  # Update behavior stats for Series 3+ collars

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
    
    # Behavior properties
    @property
    def dailyBarkingCount(self):
        return getattr(self, '_dailyBarkingCount', 0)
    
    @property
    def dailyBarkingDuration(self):
        return getattr(self, '_dailyBarkingDuration', 0)
    
    @property
    def weeklyBarkingCount(self):
        return getattr(self, '_weeklyBarkingCount', 0)
    
    @property
    def weeklyBarkingDuration(self):
        return getattr(self, '_weeklyBarkingDuration', 0)
    
    @property
    def monthlyBarkingCount(self):
        return getattr(self, '_monthlyBarkingCount', 0)
    
    @property
    def monthlyBarkingDuration(self):
        return getattr(self, '_monthlyBarkingDuration', 0)
    
    @property
    def dailyLickingCount(self):
        return getattr(self, '_dailyLickingCount', 0)
    
    @property
    def dailyLickingDuration(self):
        return getattr(self, '_dailyLickingDuration', 0)
    
    @property
    def weeklyLickingCount(self):
        return getattr(self, '_weeklyLickingCount', 0)
    
    @property
    def weeklyLickingDuration(self):
        return getattr(self, '_weeklyLickingDuration', 0)
    
    @property
    def monthlyLickingCount(self):
        return getattr(self, '_monthlyLickingCount', 0)
    
    @property
    def monthlyLickingDuration(self):
        return getattr(self, '_monthlyLickingDuration', 0)
    
    @property
    def dailyScratchingCount(self):
        return getattr(self, '_dailyScratchingCount', 0)
    
    @property
    def dailyScratchingDuration(self):
        return getattr(self, '_dailyScratchingDuration', 0)
    
    @property
    def weeklyScratchingCount(self):
        return getattr(self, '_weeklyScratchingCount', 0)
    
    @property
    def weeklyScratchingDuration(self):
        return getattr(self, '_weeklyScratchingDuration', 0)
    
    @property
    def monthlyScratchingCount(self):
        return getattr(self, '_monthlyScratchingCount', 0)
    
    @property
    def monthlyScratchingDuration(self):
        return getattr(self, '_monthlyScratchingDuration', 0)
    
    @property
    def dailyEatingCount(self):
        return getattr(self, '_dailyEatingCount', 0)
    
    @property
    def dailyEatingDuration(self):
        return getattr(self, '_dailyEatingDuration', 0)
    
    @property
    def weeklyEatingCount(self):
        return getattr(self, '_weeklyEatingCount', 0)
    
    @property
    def weeklyEatingDuration(self):
        return getattr(self, '_weeklyEatingDuration', 0)
    
    @property
    def monthlyEatingCount(self):
        return getattr(self, '_monthlyEatingCount', 0)
    
    @property
    def monthlyEatingDuration(self):
        return getattr(self, '_monthlyEatingDuration', 0)
    
    @property
    def dailyDrinkingCount(self):
        return getattr(self, '_dailyDrinkingCount', 0)
    
    @property
    def dailyDrinkingDuration(self):
        return getattr(self, '_dailyDrinkingDuration', 0)
    
    @property
    def weeklyDrinkingCount(self):
        return getattr(self, '_weeklyDrinkingCount', 0)
    
    @property
    def weeklyDrinkingDuration(self):
        return getattr(self, '_weeklyDrinkingDuration', 0)
    
    @property
    def monthlyDrinkingCount(self):
        return getattr(self, '_monthlyDrinkingCount', 0)
    
    @property
    def monthlyDrinkingDuration(self):
        return getattr(self, '_monthlyDrinkingDuration', 0)
    
    @property
    def behaviorTimeline(self):
        """Get the behavior timeline events"""
        return getattr(self, '_behaviorTimeline', [])
        
