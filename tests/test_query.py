"""Tests for query module."""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests

from pytryfi.common import query
from pytryfi.const import (
    API_HOST_URL_BASE, API_GRAPHQL, PET_MODE_NORMAL, PET_MODE_LOST,
    QUERY_CURRENT_USER, FRAGMENT_USER_DETAILS
)
from pytryfi.exceptions import TryFiError


class TestQuery:
    """Test query module functions."""
    
    @patch('pytryfi.common.query.execute')
    def test_get_user_detail(self, mock_execute):
        """Test getUserDetail function."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "currentUser": {
                    "id": "user123",
                    "email": "test@example.com",
                    "firstName": "Test",
                    "lastName": "User"
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.getUserDetail(session)
        
        assert result["id"] == "user123"
        assert result["email"] == "test@example.com"
        mock_execute.assert_called_once()
    
    @patch('pytryfi.common.query.execute')
    def test_get_pet_list(self, mock_execute):
        """Test getPetList function."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "currentUser": {
                    "userHouseholds": [{
                        "household": {
                            "pets": [{"id": "pet123", "name": "Max"}],
                            "bases": [{"baseId": "base123"}]
                        }
                    }]
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.getPetList(session)
        
        assert len(result) == 1
        assert result[0]["household"]["pets"][0]["id"] == "pet123"
        mock_execute.assert_called_once()
    
    @patch('pytryfi.common.query.execute')
    def test_get_base_list(self, mock_execute):
        """Test getBaseList function."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "currentUser": {
                    "userHouseholds": [{
                        "household": {
                            "pets": [],
                            "bases": [{"baseId": "base123", "name": "Living Room"}]
                        }
                    }]
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.getBaseList(session)
        
        assert len(result) == 1
        assert result[0]["household"]["bases"][0]["baseId"] == "base123"
        mock_execute.assert_called_once()
    
    @patch('pytryfi.common.query.execute')
    def test_get_current_pet_location(self, mock_execute, sample_location_data):
        """Test getCurrentPetLocation function."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "pet": {
                    "ongoingActivity": sample_location_data
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.getCurrentPetLocation(session, "pet123")
        
        assert result["__typename"] == "Rest"
        assert result["position"]["latitude"] == 40.7128
        mock_execute.assert_called_once()
    
    @patch('pytryfi.common.query.execute')
    def test_get_current_pet_stats(self, mock_execute, sample_stats_data):
        """Test getCurrentPetStats function."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "pet": sample_stats_data
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.getCurrentPetStats(session, "pet123")
        
        assert "dailyStat" in result
        assert result["dailyStat"]["totalSteps"] == 3000
        mock_execute.assert_called_once()
    
    @patch('pytryfi.common.query.execute')
    def test_get_current_pet_rest_stats(self, mock_execute, sample_rest_stats_data):
        """Test getCurrentPetRestStats function."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "pet": sample_rest_stats_data
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.getCurrentPetRestStats(session, "pet123")
        
        assert "dailyStat" in result
        assert result["dailyStat"]["restSummaries"][0]["data"]["sleepAmounts"][0]["duration"] == 28800
        mock_execute.assert_called_once()
    
    @patch('pytryfi.common.query.execute')
    def test_get_device_details(self, mock_execute, sample_pet_data):
        """Test getDevicedetails function."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "pet": {"device": sample_pet_data["device"]}
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.getDevicedetails(session, "pet123")
        
        assert result["device"]["id"] == "device123"
        assert result["device"]["moduleId"] == "module123"
        mock_execute.assert_called_once()
    
    @patch('pytryfi.common.query.execute')
    def test_set_led_color(self, mock_execute):
        """Test setLedColor function."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "setDeviceLed": {
                    "id": "device123",
                    "ledColor": {"name": "GREEN", "hexCode": "#00FF00"}
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.setLedColor(session, "device123", 3)
        
        assert "setDeviceLed" in result
        assert result["setDeviceLed"]["ledColor"]["name"] == "GREEN"
        
        # Verify the mutation was called with correct variables
        call_args = mock_execute.call_args
        assert call_args[1]["method"] == "POST"
        params = call_args[1]["params"]
        assert params["variables"]["moduleId"] == "device123"
        assert params["variables"]["ledColorCode"] == 3
    
    @patch('pytryfi.common.query.execute')
    def test_turn_on_led(self, mock_execute):
        """Test turnOnOffLed function for turning on LED."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "updateDeviceOperationParams": {
                    "id": "device123",
                    "operationParams": {"ledEnabled": True}
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.turnOnOffLed(session, "module123", True)
        
        assert "updateDeviceOperationParams" in result
        
        # Verify the mutation variables
        call_args = mock_execute.call_args
        params = call_args[1]["params"]
        assert params["variables"]["input"]["moduleId"] == "module123"
        assert params["variables"]["input"]["ledEnabled"] is True
    
    @patch('pytryfi.common.query.execute')
    def test_turn_off_led(self, mock_execute):
        """Test turnOnOffLed function for turning off LED."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "updateDeviceOperationParams": {
                    "id": "device123",
                    "operationParams": {"ledEnabled": False}
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.turnOnOffLed(session, "module123", False)
        
        assert "updateDeviceOperationParams" in result
        
        # Verify the mutation variables
        call_args = mock_execute.call_args
        params = call_args[1]["params"]
        assert params["variables"]["input"]["ledEnabled"] is False
    
    @patch('pytryfi.common.query.execute')
    def test_set_lost_dog_mode_enable(self, mock_execute):
        """Test setLostDogMode function for enabling lost mode."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "updateDeviceOperationParams": {
                    "id": "device123",
                    "operationParams": {"mode": PET_MODE_LOST}
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.setLostDogMode(session, "module123", True)
        
        # Verify the mutation variables
        call_args = mock_execute.call_args
        params = call_args[1]["params"]
        assert params["variables"]["input"]["mode"] == PET_MODE_LOST
    
    @patch('pytryfi.common.query.execute')
    def test_set_lost_dog_mode_disable(self, mock_execute):
        """Test setLostDogMode function for disabling lost mode."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "updateDeviceOperationParams": {
                    "id": "device123",
                    "operationParams": {"mode": PET_MODE_NORMAL}
                }
            }
        }
        mock_execute.return_value = mock_response
        
        session = Mock()
        result = query.setLostDogMode(session, "module123", False)
        
        # Verify the mutation variables
        call_args = mock_execute.call_args
        params = call_args[1]["params"]
        assert params["variables"]["input"]["mode"] == PET_MODE_NORMAL
    
    def test_get_graphql_url(self):
        """Test getGraphqlURL function."""
        url = query.getGraphqlURL()
        assert url == API_HOST_URL_BASE + API_GRAPHQL
    
    @patch('pytryfi.common.query.execute')
    def test_mutation(self, mock_execute):
        """Test mutation function."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"result": "success"}}
        mock_execute.return_value = mock_response
        
        session = Mock()
        qString = "mutation { test }"
        qVariables = '{"var1": "value1"}'
        
        result = query.mutation(session, qString, qVariables)
        
        assert result["data"]["result"] == "success"
        
        # Verify execute was called correctly
        call_args = mock_execute.call_args
        assert call_args[0][1] == session  # sessionId
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["params"]["query"] == qString
        assert call_args[1]["params"]["variables"] == {"var1": "value1"}
    
    @patch('pytryfi.common.query.execute')
    def test_query_function(self, mock_execute):
        """Test query function."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"result": "success"}}
        mock_execute.return_value = mock_response
        
        session = Mock()
        qString = "query { test }"
        
        result = query.query(session, qString)
        
        assert result["data"]["result"] == "success"
        
        # Verify execute was called correctly
        call_args = mock_execute.call_args
        assert call_args[0][1] == session
        assert call_args[1]["params"]["query"] == qString
        # Default method should be GET
        assert "method" not in call_args[1] or call_args[1].get("method") == "GET"
    
    def test_execute_get(self):
        """Test execute function with GET method."""
        session = Mock()
        session.get = Mock(return_value=Mock())
        
        url = "https://api.tryfi.com/graphql"
        params = {"query": "test"}
        
        result = query.execute(url, session, method="GET", params=params)
        
        session.get.assert_called_once_with(url, params=params)
        session.post.assert_not_called()
    
    def test_execute_post(self):
        """Test execute function with POST method."""
        session = Mock()
        session.post = Mock(return_value=Mock())
        
        url = "https://api.tryfi.com/graphql"
        params = {"query": "test"}
        
        result = query.execute(url, session, method="POST", params=params)
        
        session.post.assert_called_once_with(url, json=params)
        session.get.assert_not_called()
    
    def test_execute_invalid_method(self):
        """Test execute function with invalid method."""
        session = Mock()
        url = "https://api.tryfi.com/graphql"
        params = {"query": "test"}
        
        with pytest.raises(TryFiError, match="Method Passed was invalid: PUT"):
            query.execute(url, session, method="PUT", params=params)
    
    def test_execute_default_method(self):
        """Test execute function with default method."""
        session = Mock()
        session.get = Mock(return_value=Mock())
        
        url = "https://api.tryfi.com/graphql"
        params = {"query": "test"}
        
        # Should default to GET when method not specified
        result = query.execute(url, session, params=params)
        
        session.get.assert_called_once_with(url, params=params)
    
    @patch('pytryfi.common.query.execute')
    def test_query_string_construction(self, mock_execute):
        """Test that query strings are properly constructed."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"currentUser": {"id": "user123"}}}
        mock_execute.return_value = mock_response
        
        session = Mock()
        
        # Test getUserDetail query construction
        result = query.getUserDetail(session)
        call_args = mock_execute.call_args
        query_string = call_args[1]["params"]["query"]
        assert "currentUser" in query_string
        assert "UserDetails" in query_string
        assert result["id"] == "user123"
    
    def test_mutation_json_parsing(self):
        """Test that mutation properly parses JSON variables."""
        session = Mock()
        session.post = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"data": {}}
        session.post.return_value = mock_response
        
        # Test with complex JSON variables
        qVariables = '{"input": {"moduleId": "123", "nested": {"value": true}}}'
        query.mutation(session, "mutation test", qVariables)
        
        call_args = session.post.call_args
        variables = call_args[1]["json"]["variables"]
        assert variables["input"]["moduleId"] == "123"
        assert variables["input"]["nested"]["value"] is True
    
    @patch('pytryfi.common.query.execute')
    def test_error_response_handling(self, mock_execute):
        """Test handling of error responses."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_execute.return_value = mock_response
        
        session = Mock()
        
        # Should raise when JSON parsing fails
        with pytest.raises(ValueError, match="Invalid JSON"):
            query.getUserDetail(session)