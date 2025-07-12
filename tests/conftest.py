"""Shared test fixtures for pytryfi tests."""
import json
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
import requests


@pytest.fixture
def mock_session():
    """Create a mock requests session."""
    session = Mock(spec=requests.Session)
    session.post = Mock()
    session.get = Mock()
    session.headers = {}
    return session


@pytest.fixture
def sample_login_response():
    """Sample successful login response."""
    return {
        "userId": "user123",
        "sessionId": "session123",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_error_response():
    """Sample error response."""
    return {
        "error": {
            "message": "Invalid credentials"
        }
    }


@pytest.fixture
def sample_pet_data():
    """Sample pet data from API."""
    return {
        "id": "pet123",
        "name": "Max",
        "breed": {"name": "Golden Retriever"},
        "gender": "MALE",
        "weight": 70,
        "yearOfBirth": 2020,
        "monthOfBirth": 3,
        "dayOfBirth": 15,
        "homeCityState": "New York, NY",
        "photos": {
            "first": {
                "image": {
                    "fullSize": "https://example.com/photo.jpg"
                }
            }
        },
        "device": {
            "id": "device123",
            "moduleId": "module123",
            "info": {
                "buildId": "1.0.0",
                "batteryPercent": 75,
                "isCharging": False,
                "temperature": 2500  # 25.00 C
            },
            "operationParams": {
                "ledEnabled": True,
                "ledOffAt": None,
                "mode": "NORMAL"
            },
            "ledColor": {
                "name": "BLUE",
                "hexCode": "#0000FF"
            },
            "lastConnectionState": {
                "date": "2024-01-01T12:00:00Z",
                "__typename": "ConnectedToCellular",
                "signalStrengthPercent": 85
            },
            "nextLocationUpdateExpectedBy": "2024-01-01T13:00:00Z",
            "availableLedColors": [
                {"ledColorCode": "1", "hexCode": "#FF00FF", "name": "MAGENTA"},
                {"ledColorCode": "2", "hexCode": "#0000FF", "name": "BLUE"},
                {"ledColorCode": "3", "hexCode": "#00FF00", "name": "GREEN"},
                {"ledColorCode": "4", "hexCode": "#FFFF00", "name": "YELLOW"},
                {"ledColorCode": "5", "hexCode": "#FFA500", "name": "ORANGE"},
                {"ledColorCode": "6", "hexCode": "#FF0000", "name": "RED"}
            ]
        }
    }


@pytest.fixture
def sample_pet_without_device():
    """Sample pet data without device/collar."""
    return {
        "id": "pet456",
        "name": "Luna",
        "breed": {"name": "Labrador"},
        "gender": "FEMALE",
        "weight": 65,
        "yearOfBirth": 2021,
        "monthOfBirth": 6,
        "dayOfBirth": 10,
        "device": "None"  # No collar
    }


@pytest.fixture
def sample_base_data():
    """Sample base station data."""
    return {
        "baseId": "base123",
        "name": "Living Room",
        "online": True,
        "onlineQuality": {"chargingBase": "GOOD"},
        "lastSeenAt": "2024-01-01T12:00:00Z",
        "position": {
            "latitude": 40.7128,
            "longitude": -74.0060
        }
    }


@pytest.fixture
def sample_household_response():
    """Sample household API response."""
    def _household(pets=None, bases=None):
        if pets is None:
            pets = [sample_pet_data()]
        if bases is None:
            bases = [sample_base_data()]
        return [{
            "household": {
                "pets": pets,
                "bases": bases
            }
        }]
    return _household


@pytest.fixture
def sample_user_details():
    """Sample user details response."""
    return {
        "id": "user123",
        "email": "test@example.com",
        "firstName": "Test",
        "lastName": "User",
        "phoneNumber": "+1234567890"
    }


@pytest.fixture
def sample_location_data():
    """Sample location/activity data."""
    return {
        "__typename": "Rest",
        "areaName": "Home",
        "lastReportTimestamp": "2024-01-01T12:00:00Z",
        "position": {
            "latitude": 40.7128,
            "longitude": -74.0060
        },
        "place": {
            "name": "Home",
            "address": "123 Main St"
        },
        "start": "2024-01-01T11:00:00Z"
    }


@pytest.fixture
def sample_ongoing_walk_data():
    """Sample ongoing walk activity data."""
    return {
        "__typename": "OngoingWalk",
        "areaName": "Park",
        "lastReportTimestamp": "2024-01-01T12:00:00Z",
        "positions": [
            {
                "position": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            },
            {
                "position": {
                    "latitude": 40.7130,
                    "longitude": -74.0062
                }
            }
        ],
        "start": "2024-01-01T11:30:00Z"
    }


@pytest.fixture
def sample_stats_data():
    """Sample pet statistics data."""
    return {
        "dailyStat": {
            "stepGoal": 5000,
            "totalSteps": 3000,
            "totalDistance": 2000.5
        },
        "weeklyStat": {
            "stepGoal": 35000,
            "totalSteps": 21000,
            "totalDistance": 14000.75
        },
        "monthlyStat": {
            "stepGoal": 150000,
            "totalSteps": 90000,
            "totalDistance": 60000.25
        }
    }


@pytest.fixture
def sample_rest_stats_data():
    """Sample rest/sleep statistics data."""
    return {
        "dailyStat": {
            "restSummaries": [{
                "data": {
                    "sleepAmounts": [
                        {"type": "SLEEP", "duration": 28800},  # 8 hours in seconds
                        {"type": "NAP", "duration": 3600}      # 1 hour in seconds
                    ]
                }
            }]
        },
        "weeklyStat": {
            "restSummaries": [{
                "data": {
                    "sleepAmounts": [
                        {"type": "SLEEP", "duration": 201600},  # 56 hours
                        {"type": "NAP", "duration": 25200}      # 7 hours
                    ]
                }
            }]
        },
        "monthlyStat": {
            "restSummaries": [{
                "data": {
                    "sleepAmounts": [
                        {"type": "SLEEP", "duration": 864000},  # 240 hours
                        {"type": "NAP", "duration": 108000}     # 30 hours
                    ]
                }
            }]
        }
    }


@pytest.fixture
def mock_successful_response():
    """Create a mock successful HTTP response."""
    response = Mock()
    response.status_code = 200
    response.ok = True
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def mock_error_response():
    """Create a mock error HTTP response."""
    response = Mock()
    response.status_code = 401
    response.ok = False
    response.raise_for_status = Mock(side_effect=requests.HTTPError("401 Unauthorized"))
    return response