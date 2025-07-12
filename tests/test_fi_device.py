"""Tests for FiDevice class."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import sentry_sdk

from pytryfi.fiDevice import FiDevice
from pytryfi.ledColors import ledColors
from pytryfi.const import PET_MODE_NORMAL, PET_MODE_LOST


class TestFiDevice:
    """Test FiDevice class."""
    
    def test_init(self):
        """Test device initialization."""
        device = FiDevice("device123")
        assert device._deviceId == "device123"
        assert device.deviceId == "device123"
    
    def test_set_device_details_complete(self, sample_pet_data):
        """Test setting device details from complete JSON."""
        device = FiDevice("device123")
        device_data = sample_pet_data["device"]
        device.setDeviceDetailsJSON(device_data)
        
        assert device._moduleId == "module123"
        assert device._buildId == "1.0.0"
        assert device._batteryPercent == 75
        assert device._isCharging is False
        # When ledOffAt is None, it gets set to current time, so LED appears off
        # This is a quirk of the implementation
        assert device._ledOn is False
        assert device._mode == "NORMAL"
        assert device._ledColor == "BLUE"
        assert device._ledColorHex == "#0000FF"
        assert isinstance(device._connectionStateDate, datetime)
        assert device._connectionStateType == "ConnectedToCellular"
        assert len(device._availableLedColors) == 6
        assert isinstance(device._lastUpdated, datetime)
    
    def test_set_device_details_v1_collar_with_charging(self):
        """Test V1 collar with isCharging field."""
        device_data = {
            "moduleId": "module123",
            "info": {
                "buildId": "1.0.0",
                "batteryPercent": 75,
                "isCharging": True  # V1 collar has this
            },
            "operationParams": {
                "ledEnabled": True,
                "ledOffAt": None,
                "mode": "NORMAL"
            },
            "ledColor": {"name": "BLUE", "hexCode": "#0000FF"},
            "lastConnectionState": {
                "date": "2024-01-01T12:00:00Z",
                "__typename": "ConnectedToCellular"
            },
            "availableLedColors": []
        }
        
        device = FiDevice("device123")
        device.setDeviceDetailsJSON(device_data)
        
        assert device._isCharging is True
    
    def test_set_device_details_v2_collar_without_charging(self):
        """Test V2 collar without isCharging field."""
        device_data = {
            "moduleId": "module123",
            "info": {
                "buildId": "2.0.0",
                "batteryPercent": 75
                # V2 collar doesn't have isCharging
            },
            "operationParams": {
                "ledEnabled": True,
                "ledOffAt": None,
                "mode": "NORMAL"
            },
            "ledColor": {"name": "BLUE", "hexCode": "#0000FF"},
            "lastConnectionState": {
                "date": "2024-01-01T12:00:00Z",
                "__typename": "ConnectedToCellular"
            },
            "availableLedColors": []
        }
        
        device = FiDevice("device123")
        device.setDeviceDetailsJSON(device_data)
        
        assert device._isCharging is False  # Defaults to False
    
    def test_set_device_details_led_colors(self):
        """Test setting available LED colors."""
        device_data = {
            "moduleId": "module123",
            "info": {"buildId": "1.0.0", "batteryPercent": 75},
            "operationParams": {"ledEnabled": True, "ledOffAt": None, "mode": "NORMAL"},
            "ledColor": {"name": "BLUE", "hexCode": "#0000FF"},
            "lastConnectionState": {
                "date": "2024-01-01T12:00:00Z",
                "__typename": "ConnectedToCellular"
            },
            "availableLedColors": [
                {"ledColorCode": "1", "hexCode": "#FF00FF", "name": "MAGENTA"},
                {"ledColorCode": "2", "hexCode": "#0000FF", "name": "BLUE"},
                {"ledColorCode": "3", "hexCode": "#00FF00", "name": "GREEN"}
            ]
        }
        
        device = FiDevice("device123")
        device.setDeviceDetailsJSON(device_data)
        
        assert len(device._availableLedColors) == 3
        assert all(isinstance(color, ledColors) for color in device._availableLedColors)
        assert device._availableLedColors[0].name == "MAGENTA"
        assert device._availableLedColors[1].name == "BLUE"
        assert device._availableLedColors[2].name == "GREEN"
    
    @patch('pytryfi.fiDevice.capture_exception')
    def test_set_device_details_error(self, mock_capture):
        """Test error handling in set device details."""
        device = FiDevice("device123")
        
        # Invalid device data
        device.setDeviceDetailsJSON({"invalid": "data"})
        
        # Should capture exception
        mock_capture.assert_called_once()
    
    def test_str_representation(self):
        """Test string representation."""
        device = FiDevice("device123")
        device._lastUpdated = datetime.now()
        device._deviceId = "device123"
        device._mode = "NORMAL"
        device._batteryPercent = 75
        device._ledOn = True
        device._connectionStateDate = datetime.now()
        device._connectionStateType = "ConnectedToCellular"
        
        result = str(device)
        
        assert "Device ID: device123" in result
        assert "Device Mode: NORMAL" in result
        assert "Battery Left: 75%" in result
        assert "LED State: True" in result
        assert "ConnectedToCellular" in result
    
    def test_set_led_off_at_date_none(self):
        """Test setLedOffAtDate when ledOffAt is None."""
        device = FiDevice("device123")
        result = device.setLedOffAtDate(None)
        
        assert isinstance(result, datetime)
        assert result.tzinfo is not None  # Should have timezone
        # Should be close to current time
        assert abs((result - datetime.now(timezone.utc)).total_seconds()) < 5
    
    def test_set_led_off_at_date_with_value(self):
        """Test setLedOffAtDate with actual date."""
        device = FiDevice("device123")
        result = device.setLedOffAtDate("2024-01-01T15:00:00Z")
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 15
        assert result.minute == 0
        assert result.tzinfo is not None
    
    def test_get_accurate_led_status_false(self):
        """Test getAccurateLEDStatus when LED is off."""
        device = FiDevice("device123")
        device._ledOffAt = datetime.now(timezone.utc)
        
        result = device.getAccurateLEDStatus(False)
        assert result is False
    
    def test_get_accurate_led_status_expired(self):
        """Test getAccurateLEDStatus when LED timer has expired."""
        device = FiDevice("device123")
        # Set ledOffAt to past time
        device._ledOffAt = datetime.now(timezone.utc) - timedelta(hours=1)
        
        result = device.getAccurateLEDStatus(True)
        assert result is False  # Should be off because time expired
    
    def test_get_accurate_led_status_active(self):
        """Test getAccurateLEDStatus when LED timer is still active."""
        device = FiDevice("device123")
        # Set ledOffAt to future time
        device._ledOffAt = datetime.now(timezone.utc) + timedelta(hours=1)
        
        result = device.getAccurateLEDStatus(True)
        assert result is True  # Should be on because time not expired
    
    def test_is_lost_true(self):
        """Test isLost property when device is in lost mode."""
        device = FiDevice("device123")
        device._mode = PET_MODE_LOST
        
        assert device.isLost is True
    
    def test_is_lost_false(self):
        """Test isLost property when device is in normal mode."""
        device = FiDevice("device123")
        device._mode = PET_MODE_NORMAL
        
        assert device.isLost is False
    
    def test_all_properties(self):
        """Test all property getters."""
        device = FiDevice("device123")
        
        # Set all properties
        device._moduleId = "module123"
        device._mode = "NORMAL"
        device._buildId = "1.0.0"
        device._batteryPercent = 75
        device._isCharging = False
        device._ledOn = True
        device._ledOffAt = datetime.now(timezone.utc)
        device._ledColor = "BLUE"
        device._ledColorHex = "#0000FF"
        device._connectionStateDate = datetime.now()
        device._connectionStateType = "ConnectedToCellular"
        device._availableLedColors = []
        device._lastUpdated = datetime.now()
        
        # Test all property getters
        assert device.deviceId == "device123"
        assert device.moduleId == "module123"
        assert device.mode == "NORMAL"
        assert device.buildId == "1.0.0"
        assert device.batteryPercent == 75
        assert device.isCharging is False
        assert device.ledOn is True
        assert isinstance(device.ledOffAt, datetime)
        assert device.ledColor == "BLUE"
        assert device.ledColorHex == "#0000FF"
        assert isinstance(device.connectionStateDate, datetime)
        assert device.connectionStateType == "ConnectedToCellular"
        assert device.availableLedColors == []
        assert isinstance(device.lastUpdated, datetime)
    
    def test_led_off_at_integration(self):
        """Test LED off at date integration with accurate LED status."""
        device_data = {
            "moduleId": "module123",
            "info": {"buildId": "1.0.0", "batteryPercent": 75},
            "operationParams": {
                "ledEnabled": True,
                "ledOffAt": (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "mode": "NORMAL"
            },
            "ledColor": {"name": "BLUE", "hexCode": "#0000FF"},
            "lastConnectionState": {
                "date": "2024-01-01T12:00:00Z",
                "__typename": "ConnectedToCellular"
            },
            "availableLedColors": []
        }
        
        device = FiDevice("device123")
        device.setDeviceDetailsJSON(device_data)
        
        # LED should be on because ledOffAt is in the future
        assert device.ledOn is True
        
        # Now test with expired time
        device_data["operationParams"]["ledOffAt"] = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        device.setDeviceDetailsJSON(device_data)
        
        # LED should be off because time expired
        assert device.ledOn is False
    
    def test_connection_state_date_parsing(self):
        """Test various date formats for connection state."""
        device = FiDevice("device123")
        
        # Test ISO format with Z
        device_data = {
            "moduleId": "module123",
            "info": {"buildId": "1.0.0", "batteryPercent": 75},
            "operationParams": {"ledEnabled": False, "ledOffAt": None, "mode": "NORMAL"},
            "ledColor": {"name": "BLUE", "hexCode": "#0000FF"},
            "lastConnectionState": {
                "date": "2024-01-01T12:00:00Z",
                "__typename": "ConnectedToCellular"
            },
            "availableLedColors": []
        }
        
        device.setDeviceDetailsJSON(device_data)
        
        assert device.connectionStateDate.year == 2024
        assert device.connectionStateDate.month == 1
        assert device.connectionStateDate.day == 1
        assert device.connectionStateDate.hour == 12
    
    def test_temperature_conversion(self):
        """Test that temperature field is handled if present."""
        device_data = {
            "moduleId": "module123",
            "info": {
                "buildId": "1.0.0",
                "batteryPercent": 75,
                "temperature": 2500  # 25.00 C
            },
            "operationParams": {"ledEnabled": False, "ledOffAt": None, "mode": "NORMAL"},
            "ledColor": {"name": "BLUE", "hexCode": "#0000FF"},
            "lastConnectionState": {
                "date": "2024-01-01T12:00:00Z",
                "__typename": "ConnectedToCellular"
            },
            "availableLedColors": []
        }
        
        device = FiDevice("device123")
        device.setDeviceDetailsJSON(device_data)
        
        # Device doesn't expose temperature as property, but shouldn't crash
        assert device.batteryPercent == 75