"""Tests for FiPet class."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sentry_sdk

from pytryfi.fiPet import FiPet
from pytryfi.fiDevice import FiDevice
from pytryfi.exceptions import TryFiError


class TestFiPet:
    """Test FiPet class."""
    
    def test_init(self):
        """Test pet initialization."""
        pet = FiPet("pet123")
        assert pet._petId == "pet123"
        # FiPet doesn't initialize other attributes in __init__
        # They are set by setPetDetailsJSON
    
    def test_set_pet_details_complete(self, sample_pet_data):
        """Test setting pet details from complete JSON."""
        pet = FiPet("pet123")
        pet.setPetDetailsJSON(sample_pet_data)
        
        assert pet._name == "Max"
        assert pet._breed == "Golden Retriever"
        assert pet._gender == "MALE"
        assert pet._weight == 70
        assert pet._yearOfBirth == 2020
        assert pet._monthOfBirth == 3
        assert pet._dayOfBirth == 15
        assert pet._photoLink == "https://example.com/photo.jpg"
        assert isinstance(pet._device, FiDevice)
        assert pet._device._deviceId == "device123"
    
    def test_set_pet_details_missing_fields(self):
        """Test setting pet details with missing fields."""
        incomplete_data = {
            "name": "Max",
            "device": {
                "id": "device123",
                "moduleId": "module123",
                "info": {"batteryPercent": 75},
                "operationParams": {"ledEnabled": True, "ledOffAt": None, "mode": "NORMAL"},
                "ledColor": {"name": "BLUE", "hexCode": "#0000FF"},
                "lastConnectionState": {"__typename": "ConnectedToCellular", "date": "2024-01-01T12:00:00Z", "signalStrengthPercent": 85},
                "availableLedColors": []
            }
        }
        
        pet = FiPet("pet123")
        pet.setPetDetailsJSON(incomplete_data)
        
        assert pet._name == "Max"
        assert pet._breed is None
        assert pet._weight is None
        assert pet._yearOfBirth == 1900  # Default when missing
        assert pet._monthOfBirth == 1
        assert pet._dayOfBirth is None
        assert pet._photoLink == ""  # Default when no photo
    
    def test_set_pet_details_no_photo(self):
        """Test setting pet details when photo is missing."""
        data = {
            "name": "Max",
            "photos": {},  # No photos
            "device": {
                "id": "device123",
                "moduleId": "module123",
                "info": {"batteryPercent": 75},
                "operationParams": {"ledEnabled": True, "ledOffAt": None, "mode": "NORMAL"},
                "ledColor": {"name": "BLUE", "hexCode": "#0000FF"},
                "lastConnectionState": {"__typename": "ConnectedToCellular", "date": "2024-01-01T12:00:00Z", "signalStrengthPercent": 85},
                "availableLedColors": []
            }
        }
        
        pet = FiPet("pet123")
        pet.setPetDetailsJSON(data)
        
        assert pet._photoLink == ""
    
    def test_str_representation(self, sample_pet_data):
        """Test string representation."""
        pet = FiPet("pet123")
        # Need to set up pet properly first
        pet.setPetDetailsJSON(sample_pet_data)
        pet._homeCityState = "New York, NY"
        pet._activityType = "Rest"
        pet._currLatitude = 40.7128
        pet._currLongitude = -74.0060
        pet._currStartTime = datetime.now()
        pet._lastUpdated = datetime.now()
        
        result = str(pet)
        
        assert "Max" in result
        assert "New York, NY" in result
        assert "Rest" in result
        assert "40.7128" in result
        assert "-74.006" in result  # Float string representation may vary
    
    def test_set_current_location_rest(self, sample_location_data):
        """Test setting current location for rest activity."""
        pet = FiPet("pet123")
        pet.setCurrentLocation(sample_location_data)
        
        assert pet._activityType == "Rest"
        assert pet._areaName == "Home"
        assert pet._currLatitude == 40.7128
        assert pet._currLongitude == -74.0060
        assert pet._currPlaceName == "Home"
        assert pet._currPlaceAddress == "123 Main St"
        assert isinstance(pet._currStartTime, datetime)
        assert isinstance(pet._lastUpdated, datetime)
    
    def test_set_current_location_ongoing_walk(self, sample_ongoing_walk_data):
        """Test setting current location for ongoing walk."""
        pet = FiPet("pet123")
        pet.setCurrentLocation(sample_ongoing_walk_data)
        
        assert pet._activityType == "OngoingWalk"
        assert pet._areaName == "Park"
        # Should use last position for ongoing walk
        assert pet._currLatitude == 40.7130
        assert pet._currLongitude == -74.0062
    
    def test_set_current_location_no_place(self):
        """Test setting location without place info."""
        location_data = {
            "__typename": "Rest",
            "areaName": "Unknown",
            "lastReportTimestamp": "2024-01-01T12:00:00Z",
            "position": {
                "latitude": 40.7128,
                "longitude": -74.0060
            },
            "start": "2024-01-01T11:00:00Z"
        }
        
        pet = FiPet("pet123")
        pet.setCurrentLocation(location_data)
        
        assert pet._currPlaceName is None
        assert pet._currPlaceAddress is None
    
    def test_set_current_location_error(self):
        """Test error handling in set current location."""
        pet = FiPet("pet123")
        pet._name = "Max"
        
        # Missing required fields should cause a KeyError
        with pytest.raises(KeyError):
            pet.setCurrentLocation({"invalid": "data"})
    
    @patch('pytryfi.fiPet.capture_exception')
    @patch('pytryfi.fiPet.datetime')
    def test_set_current_location_tryfi_error(self, mock_datetime, mock_capture):
        """Test TryFiError handling in set current location."""
        from pytryfi.exceptions import TryFiError
        
        # Mock datetime.fromisoformat to raise TryFiError
        mock_datetime.datetime.fromisoformat.side_effect = TryFiError("Invalid date format")
        
        pet = FiPet("pet123")
        pet._name = "Max"
        
        location_data = {
            "__typename": "Rest",
            "areaName": "Home",
            "position": {"latitude": 40.7128, "longitude": -74.0060},
            "start": "2024-01-01T11:00:00Z"
        }
        
        # Should raise TryFiError due to mocked datetime.fromisoformat failure
        with pytest.raises(TryFiError, match="Unable to set Pet Location Details"):
            pet.setCurrentLocation(location_data)
    
    @patch('pytryfi.fiPet.capture_exception')
    def test_set_current_location_generic_error(self, mock_capture):
        """Test generic Exception handling in set current location."""
        pet = FiPet("pet123")
        pet._name = "Max"
        
        # Create data that will trigger the try block but cause a generic Exception
        location_data = {
            "__typename": "Rest",
            "areaName": "Home",
            "position": {"latitude": "invalid_float", "longitude": -74.0060},  # Will cause ValueError
            "start": "2024-01-01T11:00:00Z"
        }
        
        # Should catch generic Exception and call capture_exception, but not re-raise
        pet.setCurrentLocation(location_data)
        mock_capture.assert_called_once()
    
    def test_set_connected_to_user(self):
        """Test setConnectedTo with ConnectedToUser type."""
        pet = FiPet("pet123")
        
        connection_data = {
            "__typename": "ConnectedToUser",
            "user": {"firstName": "John", "lastName": "Doe"}
        }
        
        result = pet.setConnectedTo(connection_data)
        assert result == "John Doe"
    
    def test_set_connected_to_base(self):
        """Test setConnectedTo with ConnectedToBase type."""
        pet = FiPet("pet123")
        
        connection_data = {
            "__typename": "ConnectedToBase",
            "chargingBase": {"id": "base123"}
        }
        
        result = pet.setConnectedTo(connection_data)
        assert result == "Base ID - base123"
    
    def test_set_connected_to_unknown(self):
        """Test setConnectedTo with unknown connection type."""
        pet = FiPet("pet123")
        
        connection_data = {
            "__typename": "UnknownType"
        }
        
        result = pet.setConnectedTo(connection_data)
        assert result is None
    
    def test_set_stats(self, sample_stats_data):
        """Test setting pet statistics."""
        pet = FiPet("pet123")
        pet.setStats(
            sample_stats_data["dailyStat"],
            sample_stats_data["weeklyStat"],
            sample_stats_data["monthlyStat"]
        )
        
        # Daily stats
        assert pet._dailyGoal == 5000
        assert pet._dailySteps == 3000
        assert pet._dailyTotalDistance == 2000.5
        
        # Weekly stats
        assert pet._weeklyGoal == 35000
        assert pet._weeklySteps == 21000
        assert pet._weeklyTotalDistance == 14000.75
        
        # Monthly stats
        assert pet._monthlyGoal == 150000
        assert pet._monthlySteps == 90000
        assert pet._monthlyTotalDistance == 60000.25
    
    def test_set_stats_missing_weekly_monthly(self):
        """Test setting stats when weekly/monthly are provided."""
        pet = FiPet("pet123")
        daily = {"stepGoal": 5000, "totalSteps": 3000, "totalDistance": 2000}
        weekly = {"stepGoal": 35000, "totalSteps": 21000, "totalDistance": 14000}
        monthly = {"stepGoal": 150000, "totalSteps": 90000, "totalDistance": 60000}
        
        pet.setStats(daily, weekly, monthly)
        
        assert pet._dailyGoal == 5000
        assert pet._dailySteps == 3000
        assert pet._weeklyGoal == 35000
        assert pet._monthlyGoal == 150000
    
    @patch('pytryfi.query.getCurrentPetStats')
    def test_update_stats_success(self, mock_get_stats, sample_stats_data):
        """Test updating pet statistics."""
        mock_get_stats.return_value = sample_stats_data
        
        pet = FiPet("pet123")
        result = pet.updateStats(Mock())
        
        assert result is True
        assert pet._dailySteps == 3000
        assert pet._weeklySteps == 21000
        assert pet._monthlySteps == 90000
    
    @patch('pytryfi.query.getCurrentPetStats')
    @patch('pytryfi.fiPet.capture_exception')
    def test_update_stats_failure(self, mock_capture, mock_get_stats):
        """Test update stats failure handling."""
        mock_get_stats.side_effect = Exception("API Error")
        
        pet = FiPet("pet123")
        pet._name = "Max"
        result = pet.updateStats(Mock())
        
        assert result is None  # Method doesn't return False, just None on error
        mock_capture.assert_called_once()
    
    def test_set_rest_stats_values(self, sample_rest_stats_data):
        """Test that rest stats are set correctly."""
        pet = FiPet("pet123")
        
        # Test setting rest stats
        pet.setRestStats(
            sample_rest_stats_data["dailyStat"],
            sample_rest_stats_data["weeklyStat"],
            sample_rest_stats_data["monthlyStat"]
        )
        assert pet._dailySleep == 28800  # 8 hours in seconds
        assert pet._dailyNap == 3600     # 1 hour in seconds
    
    @patch('pytryfi.query.getCurrentPetRestStats')
    def test_update_rest_stats_success(self, mock_get_rest_stats, sample_rest_stats_data):
        """Test updating rest statistics."""
        mock_get_rest_stats.return_value = sample_rest_stats_data
        
        pet = FiPet("pet123")
        result = pet.updateRestStats(Mock())
        
        assert result is True
        assert pet._dailySleep == 28800
        assert pet._dailyNap == 3600
        assert pet._weeklySleep == 201600
        assert pet._weeklyNap == 25200
        assert pet._monthlySleep == 864000
        assert pet._monthlyNap == 108000
    
    @patch('pytryfi.fiPet.capture_exception')
    def test_set_rest_stats_daily_tryfi_error(self, mock_capture):
        """Test TryFiError handling in setRestStats for daily stats."""
        from pytryfi.exceptions import TryFiError
        
        pet = FiPet("pet123")
        pet._name = "Max"
        
        # Mock the int() function to raise TryFiError on the first call during daily processing
        with patch('builtins.int') as mock_int:
            mock_int.side_effect = TryFiError("Invalid duration format")
            
            daily_data = {"restSummaries": [{"data": {"sleepAmounts": [{"type": "SLEEP", "duration": "invalid"}]}}]}
            weekly_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
            monthly_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
            
            with pytest.raises(TryFiError):
                pet.setRestStats(daily_data, weekly_data, monthly_data)
    
    def test_set_rest_stats_weekly_tryfi_error(self):
        """Test TryFiError handling in setRestStats for weekly stats."""
        from pytryfi.exceptions import TryFiError
        
        pet = FiPet("pet123")
        pet._name = "Max"
        
        # Create a custom class that raises TryFiError when iterated in the weekly section
        class FailOnIterWeekly:
            def __getitem__(self, key):
                if key == 'restSummaries':
                    return [{'data': {'sleepAmounts': self}}]
                raise TryFiError("Weekly processing error")
            
            def __iter__(self):
                raise TryFiError("Weekly processing error")
        
        daily_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        weekly_data = FailOnIterWeekly()
        monthly_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        
        with patch('pytryfi.fiPet.capture_exception'):
            with pytest.raises(TryFiError):
                pet.setRestStats(daily_data, weekly_data, monthly_data)
    
    def test_set_rest_stats_monthly_tryfi_error(self):
        """Test TryFiError handling in setRestStats for monthly stats."""
        from pytryfi.exceptions import TryFiError
        
        pet = FiPet("pet123")
        pet._name = "Max"
        
        # Create a custom class that raises TryFiError when iterated in the monthly section
        class FailOnIterMonthly:
            def __getitem__(self, key):
                if key == 'restSummaries':
                    return [{'data': {'sleepAmounts': self}}]
                raise TryFiError("Monthly processing error")
            
            def __iter__(self):
                raise TryFiError("Monthly processing error")
        
        daily_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        weekly_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        monthly_data = FailOnIterMonthly()
        
        with patch('pytryfi.fiPet.capture_exception'):
            with pytest.raises(TryFiError):
                pet.setRestStats(daily_data, weekly_data, monthly_data)
    
    @patch('pytryfi.fiPet.capture_exception')
    def test_set_rest_stats_daily_generic_error(self, mock_capture):
        """Test generic Exception handling in setRestStats for daily stats."""
        pet = FiPet("pet123")
        pet._name = "Max"
        
        # Create data that will cause ValueError (not TryFiError) in daily processing
        daily_data = {"restSummaries": [{"data": {"sleepAmounts": [{"type": "SLEEP", "duration": "invalid_int"}]}}]}
        weekly_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        monthly_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        
        # Should catch generic Exception and call capture_exception, but not re-raise
        pet.setRestStats(daily_data, weekly_data, monthly_data)
        mock_capture.assert_called_once()
    
    @patch('pytryfi.fiPet.capture_exception')
    def test_set_rest_stats_weekly_generic_error(self, mock_capture):
        """Test generic Exception handling in setRestStats for weekly stats."""
        pet = FiPet("pet123")
        pet._name = "Max"
        
        # Valid daily, invalid weekly that causes ValueError
        daily_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        weekly_data = {"restSummaries": [{"data": {"sleepAmounts": [{"type": "SLEEP", "duration": "invalid_int"}]}}]}
        monthly_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        
        # Should catch generic Exception and call capture_exception, but not re-raise
        pet.setRestStats(daily_data, weekly_data, monthly_data)
        mock_capture.assert_called_once()
    
    @patch('pytryfi.fiPet.capture_exception')
    def test_set_rest_stats_monthly_generic_error(self, mock_capture):
        """Test generic Exception handling in setRestStats for monthly stats."""
        pet = FiPet("pet123")
        pet._name = "Max"
        
        # Valid daily and weekly, invalid monthly that causes ValueError
        daily_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        weekly_data = {"restSummaries": [{"data": {"sleepAmounts": []}}]}
        monthly_data = {"restSummaries": [{"data": {"sleepAmounts": [{"type": "SLEEP", "duration": "invalid_int"}]}}]}
        
        # Should catch generic Exception and call capture_exception, but not re-raise
        pet.setRestStats(daily_data, weekly_data, monthly_data)
        mock_capture.assert_called_once()
    
    @patch('pytryfi.query.getCurrentPetRestStats')
    @patch('pytryfi.fiPet.capture_exception')
    def test_update_rest_stats_failure(self, mock_capture, mock_get_rest_stats):
        """Test update rest stats failure handling."""
        mock_get_rest_stats.side_effect = Exception("API Error")
        
        pet = FiPet("pet123")
        pet._name = "Max"
        result = pet.updateRestStats(Mock())
        
        assert result is None  # Method doesn't return False, just None on error
        mock_capture.assert_called_once()
    
    @patch('pytryfi.query.getCurrentPetLocation')
    def test_update_pet_location_success(self, mock_get_location, sample_location_data):
        """Test updating pet location."""
        mock_get_location.return_value = sample_location_data
        
        pet = FiPet("pet123")
        result = pet.updatePetLocation(Mock())
        
        assert result is True
        assert pet._currLatitude == 40.7128
        assert pet._currLongitude == -74.0060
    
    @patch('pytryfi.query.getCurrentPetLocation')
    @patch('pytryfi.fiPet.capture_exception')
    def test_update_pet_location_failure(self, mock_capture, mock_get_location):
        """Test update location failure handling."""
        mock_get_location.side_effect = Exception("API Error")
        
        pet = FiPet("pet123")
        pet._name = "Max"
        result = pet.updatePetLocation(Mock())
        
        assert result is False  # Method returns False on error
        mock_capture.assert_called_once()
    
    @patch('pytryfi.query.getDevicedetails')
    def test_update_device_details_success(self, mock_get_device, sample_pet_data):
        """Test updating device details."""
        mock_get_device.return_value = {"device": sample_pet_data["device"]}
        
        pet = FiPet("pet123")
        pet._device = FiDevice("device123")
        result = pet.updateDeviceDetails(Mock())
        
        assert result is True
    
    @patch('pytryfi.query.getDevicedetails')
    @patch('pytryfi.fiPet.capture_exception')
    def test_update_device_details_failure(self, mock_capture, mock_get_device):
        """Test update device failure handling."""
        mock_get_device.side_effect = Exception("API Error")
        
        pet = FiPet("pet123")
        pet._name = "Max"
        pet._device = Mock()  # Use _device not device
        result = pet.updateDeviceDetails(Mock())
        
        assert result is False  # Method returns False on error
        mock_capture.assert_called_once()
    
    def test_update_all_details(self):
        """Test updating all pet details."""
        pet = FiPet("pet123")
        pet._device = Mock()
        
        # Mock all the update methods
        pet.updateDeviceDetails = Mock()
        pet.updatePetLocation = Mock()
        pet.updateStats = Mock()
        pet.updateRestStats = Mock()
        
        # Call updateAllDetails
        session = Mock()
        pet.updateAllDetails(session)
        
        # Verify all methods were called
        pet.updateDeviceDetails.assert_called_once_with(session)
        pet.updatePetLocation.assert_called_once_with(session)
        pet.updateStats.assert_called_once_with(session)
        pet.updateRestStats.assert_called_once_with(session)
    
    @patch('pytryfi.query.turnOnOffLed')
    def test_turn_on_off_led_success(self, mock_turn_on_off):
        """Test turning on/off LED."""
        mock_turn_on_off.return_value = {
            "updateDeviceOperationParams": {
                "id": "device123",
                "operationParams": {"ledEnabled": True}
            }
        }
        
        pet = FiPet("pet123")
        pet._device = Mock(moduleId="module123")
        result = pet.turnOnOffLed(Mock(), True)
        
        assert result is True
        mock_turn_on_off.assert_called_once()
    
    @patch('pytryfi.query.turnOnOffLed')
    def test_turn_on_off_led_failure(self, mock_turn_on_off):
        """Test LED control failure."""
        mock_turn_on_off.side_effect = Exception("API Error")
        
        pet = FiPet("pet123")
        pet._device = Mock(moduleId="module123")
        pet._name = "Max"
        result = pet.turnOnOffLed(Mock(), True)
        
        assert result is False
    
    @patch('pytryfi.query.setLedColor')
    def test_set_led_color_success(self, mock_set_color):
        """Test setting LED color."""
        mock_set_color.return_value = {
            "setDeviceLed": {
                "id": "device123",
                "ledColor": {"name": "GREEN"}
            }
        }
        
        pet = FiPet("pet123")
        pet._device = Mock(moduleId="module123", setDeviceDetailsJSON=Mock())
        result = pet.setLedColorCode(Mock(), 3)
        
        assert result is True
        mock_set_color.assert_called_once()
        pet._device.setDeviceDetailsJSON.assert_called_once()
    
    @patch('pytryfi.query.setLedColor')
    def test_set_led_color_partial_success(self, mock_set_color):
        """Test LED color change with device update failure."""
        mock_set_color.return_value = {"setDeviceLed": {}}
        
        pet = FiPet("pet123")
        pet._device = Mock(moduleId="module123")
        pet._device.setDeviceDetailsJSON.side_effect = Exception("Parse error")
        pet._name = "Max"
        
        result = pet.setLedColorCode(Mock(), 3)
        
        # Should still return True even if device update fails
        assert result is True
    
    @patch('pytryfi.query.turnOnOffLed')
    @patch('pytryfi.fiPet.capture_exception')
    def test_turn_on_off_led_device_update_failure(self, mock_capture, mock_turn_on_off):
        """Test LED control with device update failure."""
        mock_turn_on_off.return_value = {
            "updateDeviceOperationParams": {
                "id": "device123",
                "operationParams": {"ledEnabled": True}
            }
        }
        
        pet = FiPet("pet123")
        pet._name = "Max"
        pet._device = Mock(moduleId="module123")
        pet._device.setDeviceDetailsJSON.side_effect = Exception("Device update failed")
        
        result = pet.turnOnOffLed(Mock(), True)
        
        # Should still return True even if device update fails, but capture exception
        assert result is True
        mock_capture.assert_called_once()
    
    @patch('pytryfi.query.setLedColor')
    def test_set_led_color_failure(self, mock_set_color):
        """Test LED color change failure."""
        mock_set_color.side_effect = Exception("API Error")
        
        pet = FiPet("pet123")
        pet._device = Mock(moduleId="module123")
        pet._name = "Max"
        result = pet.setLedColorCode(Mock(), 3)
        
        assert result is False
    
    @patch('pytryfi.query.setLostDogMode')
    def test_set_lost_dog_mode_enable(self, mock_set_lost):
        """Test enabling lost dog mode."""
        mock_set_lost.return_value = {"updateDeviceOperationParams": {"mode": "LOST"}}
        
        pet = FiPet("pet123")
        pet._device = Mock(moduleId="module123", setDeviceDetailsJSON=Mock())
        result = pet.setLostDogMode(Mock(), True)
        
        assert result is True
    
    @patch('pytryfi.query.setLostDogMode')
    def test_set_lost_dog_mode_disable(self, mock_set_lost):
        """Test disabling lost dog mode."""
        mock_set_lost.return_value = {"updateDeviceOperationParams": {"mode": "NORMAL"}}
        
        pet = FiPet("pet123")
        pet._device = Mock(moduleId="module123", setDeviceDetailsJSON=Mock())
        result = pet.setLostDogMode(Mock(), False)
        
        assert result is True
    
    @patch('pytryfi.query.setLostDogMode')
    def test_set_lost_dog_mode_failure(self, mock_set_lost):
        """Test lost mode failure."""
        mock_set_lost.side_effect = Exception("API Error")
        
        pet = FiPet("pet123")
        pet._name = "Max"
        result = pet.setLostDogMode(Mock(), "ENABLE")
        
        assert result is False
    
    @patch('pytryfi.query.setLostDogMode')
    @patch('pytryfi.fiPet.capture_exception')
    def test_set_lost_dog_mode_device_update_failure(self, mock_capture, mock_set_lost):
        """Test lost dog mode with device update failure."""
        mock_set_lost.return_value = {"updateDeviceOperationParams": {"mode": "LOST"}}
        
        pet = FiPet("pet123")
        pet._name = "Max"
        pet._device = Mock(moduleId="module123")
        pet._device.setDeviceDetailsJSON.side_effect = Exception("Device update failed")
        
        result = pet.setLostDogMode(Mock(), True)
        
        # Should still return True even if device update fails, but capture exception
        assert result is True
        mock_capture.assert_called_once()
    
    def test_properties(self):
        """Test all property getters."""
        pet = FiPet("pet123")
        # Set all properties
        pet._petId = "pet123"
        pet._name = "Max"
        pet._homeCityState = "New York, NY"
        pet._yearOfBirth = 2020
        pet._monthOfBirth = 3
        pet._dayOfBirth = 15
        pet._gender = "MALE"
        pet._breed = "Golden Retriever"
        pet._weight = 70
        pet._photoLink = "https://example.com/photo.jpg"
        pet._currLongitude = -74.0060
        pet._currLatitude = 40.7128
        pet._currStartTime = datetime.now()
        pet._currPlaceName = "Home"
        pet._currPlaceAddress = "123 Main St"
        pet._dailyGoal = 5000
        pet._dailySteps = 3000
        pet._dailyTotalDistance = 2000
        pet._weeklyGoal = 35000
        pet._weeklySteps = 21000
        pet._weeklyTotalDistance = 14000
        pet._monthlyGoal = 150000
        pet._monthlySteps = 90000
        pet._monthlyTotalDistance = 60000
        pet._dailySleep = 28800
        pet._dailyNap = 3600
        pet._weeklySleep = 201600
        pet._weeklyNap = 25200
        pet._monthlySleep = 864000
        pet._monthlyNap = 108000
        pet._locationLastUpdate = datetime.now()
        pet._device = Mock(_nextLocationUpdatedExpectedBy=datetime.now())
        pet._lastUpdated = datetime.now()
        pet._activityType = "Rest"
        pet._areaName = "Home"
        
        # Test all property getters
        assert pet.petId == "pet123"
        assert pet.name == "Max"
        assert pet.homeCityState == "New York, NY"
        assert pet.yearOfBirth == 2020
        assert pet.monthOfBirth == 3
        assert pet.dayOfBirth == 15
        assert pet.gender == "MALE"
        assert pet.breed == "Golden Retriever"
        assert pet.weight == 70
        assert pet.photoLink == "https://example.com/photo.jpg"
        assert pet.currLongitude == -74.0060
        assert pet.currLatitude == 40.7128
        assert isinstance(pet.currStartTime, datetime)
        assert pet.currPlaceName == "Home"
        assert pet.currPlaceAddress == "123 Main St"
        assert pet.dailyGoal == 5000
        assert pet.dailySteps == 3000
        assert pet.dailyTotalDistance == 2000
        assert pet.weeklyGoal == 35000
        assert pet.weeklySteps == 21000
        assert pet.weeklyTotalDistance == 14000
        assert pet.monthlyGoal == 150000
        assert pet.monthlySteps == 90000
        assert pet.monthlyTotalDistance == 60000
        assert pet.dailySleep == 28800
        assert pet.dailyNap == 3600
        assert pet.weeklySleep == 201600
        assert pet.weeklyNap == 25200
        assert pet.monthlySleep == 864000
        assert pet.monthlyNap == 108000
        # locationLastUpdate property doesn't exist in the current implementation
        assert isinstance(pet.lastUpdated, datetime)
        assert pet.activityType == "Rest"
        assert pet.areaName == "Home"
        # signalStrength property doesn't exist in the current implementation
        
        # Test device property
        assert pet.device == pet._device
        
        # Test isLost
        pet._device.isLost = True
        assert pet.isLost is True
        
        # Test methods that return properties
        assert pet.getCurrPlaceName() == "Home"
        assert pet.getCurrPlaceAddress() == "123 Main St"
        assert pet.getActivityType() == "Rest"
    
    def test_utility_getter_methods(self):
        """Test all utility getter methods."""
        pet = FiPet("pet123")
        # Set up the pet with all required attributes
        pet._yearOfBirth = 2020
        pet._monthOfBirth = 3
        pet._dayOfBirth = 15
        pet._dailySteps = 5000
        pet._dailyGoal = 7000
        pet._dailyTotalDistance = 2500.5
        pet._weeklySteps = 35000
        pet._weeklyGoal = 49000
        pet._weeklyTotalDistance = 17500.75
        pet._monthlySteps = 150000
        pet._monthlyGoal = 210000
        pet._monthlyTotalDistance = 75000.25
        
        # Test getBirthDate
        birth_date = pet.getBirthDate()
        assert birth_date.year == 2020
        assert birth_date.month == 3
        assert birth_date.day == 15
        
        # Test daily getter methods
        assert pet.getDailySteps() == 5000
        assert pet.getDailyGoal() == 7000
        assert pet.getDailyDistance() == 2500.5
        
        # Test weekly getter methods
        assert pet.getWeeklySteps() == 35000
        assert pet.getWeeklyGoal() == 49000
        assert pet.getWeeklyDistance() == 17500.75
        
        # Test monthly getter methods
        assert pet.getMonthlySteps() == 150000
        assert pet.getMonthlyGoal() == 210000
        assert pet.getMonthlyDistance() == 75000.25
    
    def test_connected_to_property(self):
        """Test connectedTo property access."""
        pet = FiPet("pet123")
        pet._connectedTo = "Cellular Signal Strength - 85"
        
        assert pet.connectedTo == "Cellular Signal Strength - 85"