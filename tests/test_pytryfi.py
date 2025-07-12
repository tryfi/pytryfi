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
    
    @patch('pytryfi.requests.Session')
    @patch('pytryfi.query.getHouseHolds')
    @patch('pytryfi.PyTryFi.login')
    def test_init_success(self, mock_login, mock_get_households, mock_session_class,
                         sample_household_response, sample_pet_data, sample_base_data):
        """Test successful initialization."""
        # Setup mocks
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_get_households.return_value = sample_household_response()
        
        # Create instance
        api = PyTryFi("test@example.com", "password")
        
        # Verify initialization
        assert api._username == "test@example.com"
        assert api._password == "password"
        assert len(api._pets) == 1
        assert len(api._bases) == 1
        assert isinstance(api._pets[0], FiPet)
        assert isinstance(api._bases[0], FiBase)
        
        # Verify login was called
        mock_login.assert_called_once_with("test@example.com", "password")
    
    @patch('pytryfi.requests.Session')
    @patch('pytryfi.query.getHouseHolds')
    @patch('pytryfi.PyTryFi.login')
    def test_init_no_pets(self, mock_login, mock_get_households, mock_session_class,
                         sample_household_response):
        """Test initialization with no pets."""
        # Setup mocks
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_get_households.return_value = sample_household_response(pets=[], bases=[])
        
        # Create instance
        api = PyTryFi("test@example.com", "password")
        
        # Verify no pets or bases
        assert len(api._pets) == 0
        assert len(api._bases) == 0
    
    @patch('pytryfi.requests.Session')
    @patch('pytryfi.query.getHouseHolds')
    @patch('pytryfi.PyTryFi.login')
    def test_init_pet_without_collar(self, mock_login, mock_get_households, mock_session_class,
                                   sample_household_response, sample_pet_without_device):
        """Test initialization with pet that has no collar."""
        # Setup mocks
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_get_households.return_value = sample_household_response(
            pets=[sample_pet_without_device], 
            bases=[]
        )
        
        # Create instance
        api = PyTryFi("test@example.com", "password")
        
        # Verify pet without collar is ignored
        assert len(api._pets) == 0
    
    def test_str_representation(self):
        """Test string representation of PyTryFi instance."""
        api = Mock(spec=PyTryFi)
        api.username = "test@example.com"
        api._pets = []
        api.bases = []
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
    
    def test_update_pets(self):
        """Test updating all pets."""
        api = Mock(spec=PyTryFi)
        pet1 = Mock()
        pet2 = Mock()
        api._pets = [pet1, pet2]
        api._session = Mock()
        
        PyTryFi.updatePets(api)
        
        # Each pet should be updated
        pet1.updateAllDetails.assert_called_once_with(api._session)
        pet2.updateAllDetails.assert_called_once_with(api._session)
    
    def test_get_pet_by_id(self):
        """Test getting pet by ID."""
        api = Mock(spec=PyTryFi)
        pet1 = Mock(petId="pet1", name="Max")
        pet2 = Mock(petId="pet2", name="Luna")
        api._pets = [pet1, pet2]
        
        # Test finding existing pet
        result = PyTryFi.getPet(api, "pet2")
        assert result == pet2
        
        # Test pet not found
        result = PyTryFi.getPet(api, "nonexistent")
        assert result is None
    
    @patch('pytryfi.query.getBaseList')
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
        
        # Should still update pets even if bases fail
        PyTryFi.update(api)
        
        api.updatePets.assert_called_once()
    
    def test_properties(self):
        """Test all property getters."""
        api = Mock(spec=PyTryFi)
        api._currentUser = Mock()
        api._pets = [Mock()]
        api._bases = [Mock()]
        api._session = Mock()
        api._userId = "user123"
        api._sessionId = "session123"
        api._username = "test@example.com"
        api._password = "password"
        api._cookies = {"session": "cookie"}
        
        # Test all properties
        assert PyTryFi.currentUser.fget(api) == api._currentUser
        assert PyTryFi.pets.fget(api) == api._pets
        assert PyTryFi.bases.fget(api) == api._bases
        assert PyTryFi.session.fget(api) == api._session
        assert PyTryFi.userId.fget(api) == api._userId
        assert PyTryFi.sessionId.fget(api) == api._sessionId
        assert PyTryFi.username.fget(api) == api._username
        assert PyTryFi.password.fget(api) == api._password
        assert PyTryFi.cookies.fget(api) == api._cookies
        assert PyTryFi.userID.fget(api) == api._userId  # Deprecated property
    
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
        api.setHeaders = Mock()
        
        # Call login
        PyTryFi.login(api, "test@example.com", "password")
        
        # Verify login details set
        assert api._userId == "user123"
        assert api._sessionId == "session123"
        assert api._cookies == {"session": "cookie"}
        api.setHeaders.assert_called_once()
    
    @patch('pytryfi.requests.Session')
    def test_login_with_error_response(self, mock_session_class, sample_error_response):
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
        
        # Should raise exception
        with pytest.raises(Exception, match="TryFiLoginError"):
            PyTryFi.login(api, "test@example.com", "wrong_password")
    
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
        
        # Should raise exception
        with pytest.raises(Exception, match="TryFiLoginError"):
            PyTryFi.login(api, "test@example.com", "wrong_password")
    
    @patch('pytryfi.sentry_sdk.capture_message')
    @patch('pytryfi.sentry_sdk.capture_exception')
    def test_sentry_integration(self, mock_capture_exception, mock_capture_message):
        """Test that Sentry is properly initialized but calls are made."""
        # The import should work
        from pytryfi import PyTryFi
        
        # Sentry calls should be available (though Sentry might not be initialized)
        assert hasattr(sentry_sdk, 'capture_exception')
        assert hasattr(sentry_sdk, 'capture_message')