from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)

# keep an immutable snapshot of the original activities dict
ORIGINAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: restore the in-memory store before each test."""
    app_module.activities = deepcopy(ORIGINAL_ACTIVITIES)
    yield


def test_get_activities_returns_all_entries():
    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # at least one known key is present
    assert "Chess Club" in data


def test_signup_happy_path():
    # Arrange
    activity = "Chess Club"
    email = "test@example.com"

    # Act
    resp = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert resp.status_code == 200
    assert "Signed up" in resp.json()["message"]
    # the participant should now appear in the data
    assert email in app_module.activities[activity]["participants"]


def test_signup_duplicate_fails():
    activity = "Chess Club"
    email = ORIGINAL_ACTIVITIES[activity]["participants"][0]

    resp = client.post(f"/activities/{activity}/signup?email={email}")

    assert resp.status_code == 400
    assert "already" in resp.json()["detail"]


def test_signup_nonexistent_activity():
    resp = client.post("/activities/NoSuchThing/signup?email=foo@bar.com")
    assert resp.status_code == 404


def test_remove_participant_happy_path():
    activity = "Chess Club"
    email = ORIGINAL_ACTIVITIES[activity]["participants"][0]

    resp = client.delete(f"/activities/{activity}/participants?email={email}")

    assert resp.status_code == 200
    assert email not in app_module.activities[activity]["participants"]


def test_remove_nonexistent_participant():
    activity = "Chess Club"
    resp = client.delete(f"/activities/{activity}/participants?email=nosuch@bar.com")
    assert resp.status_code == 404


def test_remove_from_nonexistent_activity():
    resp = client.delete("/activities/FakeActivity/participants?email=foo@bar.com")
    assert resp.status_code == 404
