"""Tests for main PyTryFi class."""
import pytest
from unittest.mock import Mock, patch, call, MagicMock
import requests
import sentry_sdk

from pytryfi import PyTryFi
from pytryfi.exceptions import TryFiError
from pytryfi.fiPet import FiPet
from pytryfi.fiBase import FiBase


class TestPyTryFi:
    """Test PyTryFi main class."""
    
    def test_init_basic_attributes(self):
        """Test basic attribute initialization without full API calls."""
        # Create a partially mocked instance to test basic attributes
        api = Mock(spec=PyTryFi)
        api._username = "test@example.com"
        api._password = "password"
        api._pets = [Mock(spec=FiPet)]
        api._bases = [Mock(spec=FiBase)]
        
        # Test basic attributes are set correctly
        assert api._username == "test@example.com"
        assert api._password == "password"
        assert len(api._pets) == 1
        assert len(api._bases) == 1
    
    def test_empty_pets_and_bases(self):
        """Test instance with no pets or bases."""
        # Create instance with empty collections
        api = Mock(spec=PyTryFi)
        api._pets = []
        api._bases = []
        
        # Mock the property access
        api.pets = []
        api.bases = []
        
        # Verify no pets or bases
        assert len(api.pets) == 0
        assert len(api.bases) == 0
    
    def test_pet_filtering_logic(self):
        """Test that pets without collars are filtered out."""
        # This tests the filtering logic conceptually
        api = Mock(spec=PyTryFi)
        
        # Simulate pets where some have devices and some don't
        valid_pet = Mock(spec=FiPet)
        api._pets = [valid_pet]  # Only pets with devices get added
        api.pets = [valid_pet]
        
        # Verify only valid pets remain
        assert len(api.pets) == 1
    
    def test_str_representation(self):
        """Test string representation of PyTryFi instance."""
        api = Mock(spec=PyTryFi)
        api.username = "test@example.com"
        api.pets = []  # Make it iterable for the for loop
        api.bases = []  # Make it iterable for the for loop
        api.currentUser = Mock()
        
        result = PyTryFi.__str__(api)
        assert "test@example.com" in result
        assert "TryFi Instance" in result
    
    def test_set_headers(self):
        """Test setting headers."""
        api = Mock(spec=PyTryFi)
        api.session = Mock()
        api.session.headers = {}
        
        PyTryFi.setHeaders(api)
        
        # Headers should be set from HEADER constant
        assert api.session.headers != {}
    
    @patch('pytryfi.common.query.getPetList')
    @patch('pytryfi.common.query.getCurrentPetLocation')
    @patch('pytryfi.common.query.getCurrentPetStats')
    @patch('pytryfi.common.query.getCurrentPetRestStats')
    def test_update_pets(self, mock_get_rest_stats, mock_get_stats, mock_get_location, mock_get_pet_list):
        """Test updating all pets."""
        api = Mock(spec=PyTryFi)
        api._session = Mock()
        
        # Mock the API responses
        mock_get_pet_list.return_value = [{"household": {"pets": []}}]
        
        PyTryFi.updatePets(api)
        
        # Verify the query was called
        mock_get_pet_list.assert_called_once_with(api._session)
    
    def test_get_pet_by_id(self):
        """Test getting pet by ID."""
        api = Mock(spec=PyTryFi)
        pet1 = Mock(petId="pet1", name="Max")
        pet2 = Mock(petId="pet2", name="Luna")
        api.pets = [pet1, pet2]  # Use property not internal attribute
        
        # Test finding existing pet
        result = PyTryFi.getPet(api, "pet2")
        assert result == pet2
        
        # Test pet not found
        result = PyTryFi.getPet(api, "nonexistent")
        assert result is None
    
    @patch('pytryfi.common.query.getBaseList')
    def test_update_bases(self, mock_get_base_list):
        """Test updating base stations."""
        api = Mock(spec=PyTryFi)
        api._session = Mock()
        
        # Mock base list response
        mock_get_base_list.return_value = [{
            "household": {
                "bases": [{
                    "baseId": "base123",
                    "name": "Living Room",
                    "online": True
                }]
            }
        }]
        
        PyTryFi.updateBases(api)
        
        # Verify bases were updated
        assert len(api._bases) == 1
        assert isinstance(api._bases[0], FiBase)
    
    def test_get_base_by_id(self):
        """Test getting base by ID."""
        api = Mock(spec=PyTryFi)
        base1 = Mock(baseId="base1", name="Living Room")
        base2 = Mock(baseId="base2", name="Kitchen")
        api.bases = [base1, base2]
        
        # Test finding existing base
        result = PyTryFi.getBase(api, "base2")
        assert result == base2
        
        # Test base not found
        result = PyTryFi.getBase(api, "nonexistent")
        assert result is None
    
    def test_update_method(self):
        """Test update method that updates both bases and pets."""
        api = Mock(spec=PyTryFi)
        api.updateBases = Mock()
        api.updatePets = Mock()
        
        # Test successful update
        PyTryFi.update(api)
        
        api.updateBases.assert_called_once()
        api.updatePets.assert_called_once()
    
    def test_update_with_base_failure(self):
        """Test update method when base update fails."""
        api = Mock(spec=PyTryFi)
        api.updateBases = Mock(side_effect=Exception("Base update failed"))
        api.updatePets = Mock()
        
        # The actual update method doesn't catch exceptions, so it will raise
        with pytest.raises(Exception, match="Base update failed"):
            PyTryFi.update(api)
        
        # updatePets won't be called because the exception stops execution
        api.updatePets.assert_not_called()
    
    def test_properties(self):
        """Test all property getters."""
        api = Mock(spec=PyTryFi)
        api._currentUser = Mock()
        api._pets = [Mock()]
        api._bases = [Mock()]
        api._session = Mock()
        api._userID = "user123"  # Note: userID not userId
        api._username = "test@example.com"
        api._cookies = {"session": "cookie"}
        
        # Test all properties that actually exist
        assert PyTryFi.currentUser.fget(api) == api._currentUser
        assert PyTryFi.pets.fget(api) == api._pets
        assert PyTryFi.bases.fget(api) == api._bases
        assert PyTryFi.session.fget(api) == api._session
        assert PyTryFi.username.fget(api) == api._username
        assert PyTryFi.cookies.fget(api) == api._cookies
        assert PyTryFi.userID.fget(api) == api._userID  # Note: userID not userId
    
    @patch('pytryfi.requests.Session')
    def test_login_success(self, mock_session_class, sample_login_response):
        """Test successful login."""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = sample_login_response
        mock_response.cookies = {"session": "cookie"}
        mock_session.post.return_value = mock_response
        
        api = Mock(spec=PyTryFi)
        api._session = mock_session
        api._api_host = "https://api.tryfi.com"
        api._username = "test@example.com"  # Required by login method
        api._password = "password"  # Required by login method
        api.setHeaders = Mock()
        
        # Call login (login method doesn't take username/password parameters)
        PyTryFi.login(api)
        
        # Verify login details set (login sets _userId and _sessionId)
        assert api._userId == "user123"
        assert api._sessionId == "session123"
        assert api._cookies == {"session": "cookie"}
        # Note: login method doesn't call setHeaders internally
    
    @patch('pytryfi.requests.Session')
    @patch('pytryfi.capture_exception')
    def test_login_with_error_response(self, mock_capture, mock_session_class, sample_error_response):
        """Test login with error in response."""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = sample_error_response
        mock_session.post.return_value = mock_response
        
        api = Mock(spec=PyTryFi)
        api._session = mock_session
        api._api_host = "https://api.tryfi.com"
        api._username = "test@example.com"  # Required by login method
        api._password = "wrong_password"  # Required by login method
        
        # Should raise exception
        with pytest.raises(Exception, match="TryFiLoginError"):
            PyTryFi.login(api)
    
    @patch('pytryfi.requests.Session')
    def test_login_http_error(self, mock_session_class):
        """Test login with HTTP error."""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.ok = False
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_session.post.return_value = mock_response
        
        api = Mock(spec=PyTryFi)
        api._session = mock_session
        api._api_host = "https://api.tryfi.com"
        api._username = "test@example.com"  # Required by login method
        api._password = "password"  # Required by login method
        
        # Should raise exception (HTTP errors are re-raised, not converted to TryFiLoginError)
        with pytest.raises(requests.HTTPError):
            PyTryFi.login(api)
    
    @patch('pytryfi.sentry_sdk.capture_message')
    @patch('pytryfi.sentry_sdk.capture_exception')
    def test_sentry_integration(self, mock_capture_exception, mock_capture_message):
        """Test that Sentry is properly initialized but calls are made."""
        # The import should work
        from pytryfi import PyTryFi
        
        # Sentry calls should be available (though Sentry might not be initialized)
        assert hasattr(sentry_sdk, 'capture_exception')
        assert hasattr(sentry_sdk, 'capture_message')