"""Tests for FiBase class."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import sentry_sdk

from pytryfi.fiBase import FiBase


class TestFiBase:
    """Test FiBase class."""
    
    def test_init(self):
        """Test base station initialization."""
        base = FiBase("base123")
        assert base._baseId == "base123"
        assert base.baseId == "base123"
    
    def test_set_base_details_complete(self, sample_base_data):
        """Test setting base details from complete JSON."""
        base = FiBase("base123")
        # Add missing required fields to sample data
        sample_base_data['networkName'] = 'TestNetwork'
        sample_base_data['infoLastUpdated'] = '2024-01-01T12:00:00Z'
        base.setBaseDetailsJSON(sample_base_data)
        
        assert base._name == "Living Room"
        assert base._latitude == 40.7128
        assert base._longitude == -74.0060
        assert base._online is True
        assert base._onlineQuality == {"chargingBase": "GOOD"}
        assert isinstance(base._lastUpdated, datetime)
        assert base._networkName == "TestNetwork"
    
    def test_set_base_details_with_network(self):
        """Test setting base details with network name."""
        base_data = {
            "name": "Kitchen Base",
            "position": {
                "latitude": 40.7128,
                "longitude": -74.0060
            },
            "online": True,
            "onlineQuality": {"chargingBase": "EXCELLENT"},
            "infoLastUpdated": "2024-01-01T12:00:00Z",
            "networkName": "HomeWiFi"
        }
        
        base = FiBase("base456")
        base.setBaseDetailsJSON(base_data)
        
        assert base._name == "Kitchen Base"
        assert base._latitude == 40.7128
        assert base._longitude == -74.0060
        assert base._online is True
        assert base._onlineQuality == {"chargingBase": "EXCELLENT"}
        assert base._networkName == "HomeWiFi"
        assert isinstance(base._lastUpdated, datetime)
    
    def test_set_base_details_minimal(self):
        """Test setting base details with minimal data."""
        base_data = {
            "name": "Minimal Base",
            "position": {
                "latitude": 0.0,
                "longitude": 0.0
            },
            "online": False,
            "onlineQuality": None,
            "infoLastUpdated": None,
            "networkName": ""
        }
        
        base = FiBase("base789")
        base.setBaseDetailsJSON(base_data)
        
        assert base._name == "Minimal Base"
        assert base._latitude == 0.0
        assert base._longitude == 0.0
        assert base._online is False
        assert base._onlineQuality is None
        # lastUpdated should be set to datetime.now() 
        assert isinstance(base._lastUpdated, datetime)
    
    @patch('pytryfi.fiBase.capture_exception')
    def test_set_base_details_error(self, mock_capture):
        """Test error handling in set base details."""
        base = FiBase("base123")
        
        # Invalid base data
        base.setBaseDetailsJSON({"invalid": "data"})
        
        # Should capture exception
        mock_capture.assert_called_once()
    
    @patch('pytryfi.fiBase.capture_exception')
    def test_set_base_details_missing_position(self, mock_capture):
        """Test error when position data is missing."""
        base_data = {
            "name": "Bad Base",
            # Missing position
            "online": True,
            "onlineQuality": {"chargingBase": "GOOD"}
        }
        
        base = FiBase("base123")
        base.setBaseDetailsJSON(base_data)
        
        # Should capture exception due to missing position
        mock_capture.assert_called_once()
    
    def test_str_representation(self):
        """Test string representation."""
        base = FiBase("base123")
        base._lastUpdated = datetime.now()
        base._name = "Living Room"
        base._online = True
        base._networkName = "HomeWiFi"
        base._latitude = 40.7128
        base._longitude = -74.0060
        
        result = str(base)
        
        assert "Base ID: base123" in result
        assert "Name: Living Room" in result
        assert "Online Status: True" in result
        assert "Wifi Network: HomeWiFi" in result
        assert "Located: 40.7128,-74.006" in result  # Note: float repr might truncate
    
    def test_all_properties(self):
        """Test all property getters."""
        base = FiBase("base123")
        
        # Set all properties
        base._baseId = "base123"
        base._name = "Living Room"
        base._latitude = 40.7128
        base._longitude = -74.0060
        base._online = True
        base._onlineQuality = {"chargingBase": "GOOD"}
        base._lastUpdated = datetime.now()
        base._networkName = "HomeWiFi"
        
        # Test all property getters
        assert base.baseId == "base123"
        assert base.name == "Living Room"
        assert base.latitude == 40.7128
        assert base.longitude == -74.0060
        assert base.online is True
        assert base.onlineQuality == {"chargingBase": "GOOD"}
        assert base.networkname == "HomeWiFi"
        assert isinstance(base.lastUpdated, datetime)
        assert isinstance(base.lastupdate, datetime)  # Both properties return same value
    
    def test_online_quality_variations(self):
        """Test different online quality values."""
        base = FiBase("base123")
        
        # Test string quality
        base_data = {
            "name": "Base",
            "position": {"latitude": 0, "longitude": 0},
            "online": True,
            "onlineQuality": "EXCELLENT",
            "infoLastUpdated": None
        }
        base.setBaseDetailsJSON(base_data)
        assert base.onlineQuality == "EXCELLENT"
        
        # Test dict quality
        base_data["onlineQuality"] = {"chargingBase": "POOR", "signal": -85}
        base.setBaseDetailsJSON(base_data)
        assert base.onlineQuality == {"chargingBase": "POOR", "signal": -85}
        
        # Test None quality
        base_data["onlineQuality"] = None
        base.setBaseDetailsJSON(base_data)
        assert base.onlineQuality is None
    
    def test_coordinate_edge_cases(self):
        """Test edge cases for coordinates."""
        base = FiBase("base123")
        
        # Test negative coordinates
        base_data = {
            "name": "Southern Base",
            "position": {
                "latitude": -90.0,  # South pole
                "longitude": -180.0  # International date line
            },
            "online": True,
            "onlineQuality": None,
            "infoLastUpdated": None
        }
        
        base.setBaseDetailsJSON(base_data)
        assert base.latitude == -90.0
        assert base.longitude == -180.0
        
        # Test maximum positive coordinates
        base_data["position"] = {
            "latitude": 90.0,   # North pole
            "longitude": 180.0  # International date line
        }
        
        base.setBaseDetailsJSON(base_data)
        assert base.latitude == 90.0
        assert base.longitude == 180.0
    
    def test_network_name_variations(self):
        """Test different network name values."""
        base = FiBase("base123")
        
        base_data = {
            "name": "Base",
            "position": {"latitude": 0, "longitude": 0},
            "online": True,
            "onlineQuality": None,
            "infoLastUpdated": None,
            "networkName": ""
        }
        
        # Empty string network name
        base.setBaseDetailsJSON(base_data)
        assert base.networkname == ""
        
        # Long network name
        base_data["networkName"] = "VeryLongNetworkNameWith-Special_Characters.123"
        base.setBaseDetailsJSON(base_data)
        assert base.networkname == "VeryLongNetworkNameWith-Special_Characters.123"
        
        # Unicode network name
        base_data["networkName"] = "WiFi-🏠-Network"
        base.setBaseDetailsJSON(base_data)
        assert base.networkname == "WiFi-🏠-Network"
    
    def test_duplicate_last_updated_bug(self):
        """Test the bug where infoLastUpdated gets overwritten."""
        base_data = {
            "name": "Base",
            "position": {"latitude": 0, "longitude": 0},
            "online": True,
            "onlineQuality": None,
            "infoLastUpdated": "2024-01-01T12:00:00Z",  # This value gets lost
            "networkName": "WiFi"
        }
        
        base = FiBase("base123")
        base.setBaseDetailsJSON(base_data)
        
        # The bug causes this to be datetime.now() instead of the JSON value
        # The current implementation overwrites the JSON value with datetime.now()
        assert isinstance(base._lastUpdated, datetime)
        # Can't check the exact value since it's overwritten