"""Tests for exceptions module."""
import pytest
from pytryfi.exceptions import Error, TryFiError


class TestExceptions:
    """Test exception classes."""
    
    def test_error_base_class(self):
        """Test Error base exception class."""
        # Test instantiation with no message
        error = Error()
        assert isinstance(error, Exception)
        assert isinstance(error, Error)
        assert str(error) == ""
        
        # Test instantiation with message
        error = Error("Test error message")
        assert str(error) == "Test error message"
    
    def test_tryfi_error_class(self):
        """Test TryFiError exception class."""
        # Test instantiation with no message
        error = TryFiError()
        assert isinstance(error, Exception)
        assert isinstance(error, Error)
        assert isinstance(error, TryFiError)
        assert str(error) == ""
        
        # Test instantiation with message
        error = TryFiError("TryFi API error")
        assert str(error) == "TryFi API error"
    
    def test_inheritance(self):
        """Test exception inheritance hierarchy."""
        tryfi_error = TryFiError("Test")
        
        # TryFiError should be instance of all parent classes
        assert isinstance(tryfi_error, TryFiError)
        assert isinstance(tryfi_error, Error)
        assert isinstance(tryfi_error, Exception)
        
        # But not the other way around
        base_error = Error("Test")
        assert isinstance(base_error, Error)
        assert isinstance(base_error, Exception)
        assert not isinstance(base_error, TryFiError)
    
    def test_raising_exceptions(self):
        """Test raising custom exceptions."""
        # Test raising Error
        with pytest.raises(Error) as exc_info:
            raise Error("Base error occurred")
        assert str(exc_info.value) == "Base error occurred"
        
        # Test raising TryFiError
        with pytest.raises(TryFiError) as exc_info:
            raise TryFiError("TryFi specific error")
        assert str(exc_info.value) == "TryFi specific error"
    
    def test_catching_exceptions(self):
        """Test catching exceptions with different handlers."""
        # TryFiError can be caught as Error
        try:
            raise TryFiError("Test error")
        except Error as e:
            assert isinstance(e, TryFiError)
            assert str(e) == "Test error"
        else:
            pytest.fail("Exception was not caught")
        
        # TryFiError can be caught as Exception
        try:
            raise TryFiError("Test error")
        except Exception as e:
            assert isinstance(e, TryFiError)
            assert str(e) == "Test error"
        else:
            pytest.fail("Exception was not caught")
    
    def test_exception_with_multiple_args(self):
        """Test exceptions with multiple arguments."""
        # Python exceptions can take multiple args
        error = Error("Error", "Additional", "Info")
        assert error.args == ("Error", "Additional", "Info")
        
        tryfi_error = TryFiError("API Error", 404, {"detail": "Not found"})
        assert tryfi_error.args == ("API Error", 404, {"detail": "Not found"})
    
    def test_exception_attributes(self):
        """Test that exceptions have standard attributes."""
        error = TryFiError("Test error")
        
        # Should have standard exception attributes
        assert hasattr(error, 'args')
        assert hasattr(error, '__str__')
        assert hasattr(error, '__repr__')
        assert hasattr(error, '__class__')
    
    def test_exception_repr(self):
        """Test exception representation."""
        error = Error("Test error")
        assert repr(error) == "Error('Test error')"
        
        tryfi_error = TryFiError("API failed")
        assert repr(tryfi_error) == "TryFiError('API failed')"
        
        # Empty message
        empty_error = TryFiError()
        assert repr(empty_error) == "TryFiError()"
    
    def test_exception_equality(self):
        """Test exception equality."""
        error1 = TryFiError("Same message")
        error2 = TryFiError("Same message")
        error3 = TryFiError("Different message")
        
        # Exceptions are compared by identity, not value
        assert error1 != error2
        assert error1 != error3
        
        # But messages are equal
        assert str(error1) == str(error2)
        assert str(error1) != str(error3)
    
    def test_exception_in_context(self):
        """Test using exceptions in realistic contexts."""
        def api_call():
            """Simulate an API call that can fail."""
            raise TryFiError("API request failed: 401 Unauthorized")
        
        def process_data():
            """Simulate data processing that catches API errors."""
            try:
                api_call()
            except TryFiError as e:
                # Re-raise with additional context
                raise TryFiError(f"Failed to process data: {e}") from e
        
        # Test the exception chain
        with pytest.raises(TryFiError) as exc_info:
            process_data()
        
        assert "Failed to process data" in str(exc_info.value)
        assert "API request failed" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None