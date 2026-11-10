from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    original_activities = deepcopy(app_module.activities)
    try:
        with TestClient(app_module.app) as test_client:
            yield test_client
    finally:
        app_module.activities.clear()
        app_module.activities.update(original_activities)


def test_get_activities_returns_activity_details(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[activity_name]["max_participants"] == 12
    assert "michael@mergington.edu" in response.json()[activity_name]["participants"]


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Team"
    email = "new.student@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert app_module.activities[activity_name]["participants"].count(email) == 1


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404


def test_signup_rejects_invalid_email(client):
    # Arrange
    activity_name = "Basketball Team"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup", params={"email": "not-an-email"}
    )

    # Assert
    assert response.status_code == 422
    assert app_module.activities[activity_name]["participants"] == []


def test_signup_requires_email(client):
    # Arrange
    activity_name = "Basketball Team"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup")

    # Assert
    assert response.status_code == 422


def test_signup_allows_last_available_spot(client):
    # Arrange
    activity_name = "Basketball Team"
    activity = app_module.activities[activity_name]
    activity["participants"] = [
        f"student{index}@example.com"
        for index in range(activity["max_participants"] - 1)
    ]
    email = "last.student@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert len(activity["participants"]) == activity["max_participants"]
    assert email in activity["participants"]


def test_signup_rejects_full_activity(client):
    # Arrange
    activity_name = "Basketball Team"
    activity = app_module.activities[activity_name]
    activity["participants"] = [
        f"student{index}@example.com" for index in range(activity["max_participants"])
    ]

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": "new.student@example.com"},
    )

    # Assert
    assert response.status_code == 400
    assert len(activity["participants"]) == activity["max_participants"]


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404


def test_unregister_returns_404_for_unregistered_participant(client):
    # Arrange
    activity_name = "Basketball Team"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404