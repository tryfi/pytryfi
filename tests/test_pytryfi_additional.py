"""Additional tests for PyTryFi class to improve coverage."""
import pytest
from unittest.mock import Mock, patch, PropertyMock
import requests

from pytryfi import PyTryFi
from pytryfi.exceptions import TryFiError
from pytryfi.fiPet import FiPet
from pytryfi.fiBase import FiBase


class TestPyTryFiAdditional:
    """Additional tests for PyTryFi to achieve 100% coverage."""
    
    def test_duplicate_session_property(self):
        """Test that duplicate session property is defined."""
        # This tests line 191-192 where session property is defined twice
        # The second definition should override the first
        api = Mock(spec=PyTryFi)
        api._session = Mock()
        
        # Test that session property exists and can be called
        result = PyTryFi.session.fget(api)
        assert result == api._session
    
    @patch('pytryfi.capture_exception')
    def test_update_pets_with_exception(self, mock_capture):
        """Test updatePets method when exception occurs."""
        api = Mock(spec=PyTryFi)
        api._session = Mock()
        
        # Mock getPetList to raise exception
        with patch('pytryfi.common.query.getPetList', side_effect=Exception("API Error")):
            PyTryFi.updatePets(api)
            
            # Should catch exception and call capture_exception
            mock_capture.assert_called_once()
    
    def test_update_pet_object_successful_update(self):
        """Test updatePetObject method successful case."""
        api = Mock(spec=PyTryFi)
        
        # Create existing pet
        existing_pet = Mock()
        existing_pet.petId = "pet123"
        api.pets = [existing_pet]
        api._pets = [existing_pet]
        
        # Create new pet object to replace the existing one
        new_pet = Mock()
        new_pet.petId = "pet123"
        
        PyTryFi.updatePetObject(api, new_pet)
        
        # Verify the pet was updated (lines 120-123)
        api._pets.pop.assert_called_once_with(0)
        api._pets.append.assert_called_once_with(new_pet)
    
    def test_get_pet_with_exception(self):
        """Test getPet method when exception occurs."""
        api = Mock(spec=PyTryFi)
        
        # Mock pets property to raise exception
        with patch.object(PyTryFi, 'pets', new_callable=PropertyMock) as mock_pets:
            mock_pets.side_effect = Exception("Pet access error")
            
            with patch('pytryfi.capture_exception') as mock_capture:
                result = PyTryFi.getPet(api, "pet123")
                
                # Should catch exception, call capture_exception, and return None
                assert result is None
                mock_capture.assert_called_once()
    
    @patch('pytryfi.capture_exception')
    def test_update_bases_with_exception(self, mock_capture):
        """Test updateBases method when exception occurs."""
        api = Mock(spec=PyTryFi)
        api._session = Mock()
        
        # Mock getBaseList to raise exception
        with patch('pytryfi.common.query.getBaseList', side_effect=Exception("API Error")):
            PyTryFi.updateBases(api)
            
            # Should catch exception and call capture_exception
            mock_capture.assert_called_once()
    
    def test_get_base_with_exception(self):
        """Test getBase method when exception occurs."""
        api = Mock(spec=PyTryFi)
        
        # Mock bases property to raise exception
        with patch.object(PyTryFi, 'bases', new_callable=PropertyMock) as mock_bases:
            mock_bases.side_effect = Exception("Base access error")
            
            with patch('pytryfi.capture_exception') as mock_capture:
                result = PyTryFi.getBase(api, "base123")
                
                # Should catch exception, call capture_exception, and return None
                assert result is None
                mock_capture.assert_called_once()
    
    def test_str_with_iterations(self):
        """Test __str__ method with iterations over pets and bases."""
        api = Mock(spec=PyTryFi)
        api.username = "test@example.com"
        api.currentUser = Mock(__str__=Mock(return_value="User: John Doe"))
        
        # Mock pets and bases with __str__ methods
        pet1 = Mock(__str__=Mock(return_value="Pet: Max"))
        pet2 = Mock(__str__=Mock(return_value="Pet: Luna"))
        base1 = Mock(__str__=Mock(return_value="Base: Living Room"))
        
        api.pets = [pet1, pet2]
        api.bases = [base1]
        
        result = PyTryFi.__str__(api)
        
        assert "test@example.com" in result
        assert "TryFi Instance" in result
        assert "Pet: Max" in result
        assert "Pet: Luna" in result
        assert "Base: Living Room" in result
    
    @patch('pytryfi.sentry_sdk.init')
    @patch('pytryfi.requests.Session')  
    @patch('pytryfi.PyTryFi.login')
    @patch('pytryfi.PyTryFi.setHeaders')
    @patch('pytryfi.fiUser.FiUser.__init__', return_value=None)
    @patch('pytryfi.fiUser.FiUser.setUserDetails')
    @patch('pytryfi.common.query.getPetList')
    @patch('pytryfi.common.query.getBaseList')
    def test_initialization_flow_basic(self, mock_get_base_list, mock_get_pet_list, 
                                       mock_set_user, mock_user_init, mock_set_headers, 
                                       mock_login, mock_session_class, mock_sentry):
        """Test the initialization flow up to pets and bases setup."""
        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock empty pet and base lists to avoid complex initialization
        mock_get_pet_list.return_value = [{"household": {"pets": []}}]
        mock_get_base_list.return_value = [{"household": {"bases": []}}]
        
        # Mock login to set userId
        def mock_login_side_effect(self):
            self._userId = "user123"
        mock_login.side_effect = mock_login_side_effect
        
        # Create instance - this should cover lines 36-71
        api = PyTryFi("test@example.com", "password")
        
        # Verify initialization steps were called
        mock_sentry.assert_called_once()
        mock_session_class.assert_called_once()
        mock_login.assert_called_once()
        mock_set_headers.assert_called_once()
        mock_user_init.assert_called_once_with("user123")
        mock_set_user.assert_called_once()
        mock_get_pet_list.assert_called_once()
        mock_get_base_list.assert_called_once()
        
        # Verify basic attributes are set
        assert api._username == "test@example.com"
        assert api._password == "password"
        assert hasattr(api, '_pets')
        assert hasattr(api, '_bases')
    
    def test_update_pets_successful_flow(self):
        """Test updatePets method successful execution."""
        api = Mock(spec=PyTryFi)
        api._session = Mock()
        
        # Mock pet list with one pet that has no device (to test filtering)
        mock_pet_list = [{
            "household": {
                "pets": [{
                    "id": "pet123",
                    "name": "Max",
                    "device": "None"  # This should be filtered out
                }]
            }
        }]
        
        with patch('pytryfi.common.query.getPetList', return_value=mock_pet_list):
            # This should test lines 97-109
            PyTryFi.updatePets(api)
            
            # Verify that _pets was set to empty list (pet filtered out)
            assert api._pets == []
    
    def test_update_pets_with_valid_pet(self):
        """Test updatePets with a pet that has a device.""" 
        api = Mock(spec=PyTryFi)
        api._session = Mock()
        
        # Mock pet list with valid pet
        mock_pet_list = [{
            "household": {
                "pets": [{
                    "id": "pet123", 
                    "name": "Max",
                    "device": {
                        "id": "device123",
                        "moduleId": "module123",
                        "info": {"batteryPercent": 75},
                        "operationParams": {"ledEnabled": True},
                        "ledColor": {"name": "BLUE"},
                        "lastConnectionState": {"__typename": "ConnectedToCellular", "date": "2024-01-01T12:00:00Z", "signalStrengthPercent": 85},
                        "availableLedColors": []
                    }
                }]
            }
        }]
        
        with patch('pytryfi.common.query.getPetList', return_value=mock_pet_list), \
             patch('pytryfi.common.query.getCurrentPetLocation'), \
             patch('pytryfi.common.query.getCurrentPetStats'), \
             patch('pytryfi.common.query.getCurrentPetRestStats'):
            
            PyTryFi.updatePets(api)
            
            # Verify a pet was added
            assert len(api._pets) == 1
            assert isinstance(api._pets[0], FiPet)