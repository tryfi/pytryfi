"""Tests for FiUser class."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import sentry_sdk

from pytryfi.fiUser import FiUser


class TestFiUser:
    """Test FiUser class."""
    
    def test_init(self):
        """Test user initialization."""
        user = FiUser("user123")
        assert user._userId == "user123"
        assert user.userId == "user123"
    
    @patch('pytryfi.fiUser.query.getUserDetail')
    def test_set_user_details_success(self, mock_get_user_detail, sample_user_details):
        """Test setting user details from API response."""
        mock_get_user_detail.return_value = sample_user_details
        
        user = FiUser("user123")
        session = Mock()
        user.setUserDetails(session)
        
        assert user._email == "test@example.com"
        assert user._firstName == "Test"
        assert user._lastName == "User"
        assert user._phoneNumber == "+1234567890"
        assert isinstance(user._lastUpdated, datetime)
        
        mock_get_user_detail.assert_called_once_with(session)
    
    @patch('pytryfi.fiUser.query.getUserDetail')
    @patch('pytryfi.fiUser.capture_exception')
    def test_set_user_details_failure(self, mock_capture, mock_get_user_detail):
        """Test error handling when setting user details fails."""
        mock_get_user_detail.side_effect = Exception("API Error")
        
        user = FiUser("user123")
        session = Mock()
        user.setUserDetails(session)
        
        # Should capture exception
        mock_capture.assert_called_once()
        
        # User details should not be set
        assert not hasattr(user, '_email')
        assert not hasattr(user, '_firstName')
    
    def test_str_representation(self):
        """Test string representation."""
        user = FiUser("user123")
        user._email = "test@example.com"
        user._firstName = "Test"
        user._lastName = "User"
        
        result = str(user)
        
        assert "User ID: user123" in result
        assert "Name: Test User" in result
        assert "Email: test@example.com" in result
    
    def test_full_name_property(self):
        """Test fullName property."""
        user = FiUser("user123")
        user._firstName = "John"
        user._lastName = "Doe"
        
        assert user.fullName == "John Doe"
    
    def test_all_properties(self):
        """Test all property getters."""
        user = FiUser("user123")
        
        # Set all properties
        user._userId = "user123"
        user._email = "test@example.com"
        user._firstName = "Test"
        user._lastName = "User"
        user._phoneNumber = "+1234567890"
        user._lastUpdated = datetime.now()
        
        # Test all property getters
        assert user.userId == "user123"
        assert user.email == "test@example.com"
        assert user.firstName == "Test"
        assert user.lastName == "User"
        assert user.phoneNumber == "+1234567890"
        assert user.fullName == "Test User"
        assert isinstance(user.lastUpdated, datetime)
    
    @patch('pytryfi.fiUser.query.getUserDetail')
    def test_set_user_details_missing_fields(self, mock_get_user_detail):
        """Test setting user details with missing fields."""
        incomplete_data = {
            "email": "test@example.com",
            "firstName": "Test",
            # Missing lastName and phoneNumber
        }
        mock_get_user_detail.return_value = incomplete_data
        
        user = FiUser("user123")
        session = Mock()
        
        # Should raise KeyError which gets captured
        user.setUserDetails(session)
        
        # Should have set what was available
        assert user._email == "test@example.com"
        assert user._firstName == "Test"
    
    @patch('pytryfi.fiUser.query.getUserDetail')
    def test_set_user_details_empty_response(self, mock_get_user_detail):
        """Test setting user details with empty response."""
        mock_get_user_detail.return_value = {}
        
        user = FiUser("user123")
        session = Mock()
        
        # Should handle gracefully
        user.setUserDetails(session)
        
        # No details should be set
        assert not hasattr(user, '_email')
    
    def test_full_name_with_extra_spaces(self):
        """Test fullName property with various name formats."""
        user = FiUser("user123")
        
        # Normal case
        user._firstName = "John"
        user._lastName = "Doe"
        assert user.fullName == "John Doe"
        
        # Empty first name
        user._firstName = ""
        user._lastName = "Doe"
        assert user.fullName == " Doe"
        
        # Empty last name
        user._firstName = "John"
        user._lastName = ""
        assert user.fullName == "John "
        
        # Both empty
        user._firstName = ""
        user._lastName = ""
        assert user.fullName == " "
        
        # Unicode names
        user._firstName = "José"
        user._lastName = "García"
        assert user.fullName == "José García"
    
    @patch('pytryfi.fiUser.query.getUserDetail')
    def test_set_user_details_unicode(self, mock_get_user_detail):
        """Test setting user details with unicode characters."""
        unicode_data = {
            "email": "josé@example.com",
            "firstName": "José",
            "lastName": "García",
            "phoneNumber": "+34123456789"
        }
        mock_get_user_detail.return_value = unicode_data
        
        user = FiUser("user123")
        session = Mock()
        user.setUserDetails(session)
        
        assert user._email == "josé@example.com"
        assert user._firstName == "José"
        assert user._lastName == "García"
        assert user.fullName == "José García"
    
    def test_user_without_details_set(self):
        """Test accessing properties before setUserDetails is called."""
        user = FiUser("user123")
        
        # userId should work
        assert user.userId == "user123"
        
        # Other properties will raise AttributeError
        with pytest.raises(AttributeError):
            _ = user.email
        
        with pytest.raises(AttributeError):
            _ = user.firstName
        
        with pytest.raises(AttributeError):
            _ = user.fullName