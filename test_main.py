from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import create_app


class FakeCursor:
    def __init__(self, rows: list[tuple] | None = None, rowcount: int = -1) -> None:
        self.rows = rows or []
        self.rowcount = rowcount

    def fetchone(self) -> tuple | None:
        return self.rows[0] if self.rows else None

    def fetchall(self) -> list[tuple]:
        return self.rows


class FakeConnection:
    def __init__(self, teams: list[tuple]) -> None:
        self.teams = teams

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str, params: tuple = ()) -> FakeCursor:
        query = " ".join(query.split()).upper()
        if query.startswith("CREATE TABLE"):
            return FakeCursor()
        if query.startswith("INSERT INTO TEAMS"):
            team_id = max((team[0] for team in self.teams), default=0) + 1
            row = (team_id, params[0], datetime.now(timezone.utc))
            self.teams.append(row)
            return FakeCursor([row])
        if query.startswith("SELECT"):
            return FakeCursor(sorted(self.teams, key=lambda team: team[0]))
        if query.startswith("DELETE"):
            original_length = len(self.teams)
            self.teams[:] = [team for team in self.teams if team[0] != params[0]]
            return FakeCursor(rowcount=original_length - len(self.teams))
        raise AssertionError(f"Unexpected SQL query: {query}")


class TeamApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.teams: list[tuple] = []
        self.connect_patch = patch(
            "main.psycopg.connect",
            side_effect=lambda _: FakeConnection(self.teams),
        )
        self.connect_patch.start()
        self.client_context = TestClient(create_app("postgresql://test"))
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        self.connect_patch.stop()

    def test_register_list_and_delete_team(self) -> None:
        created = self.client.post(
            "/api/teams/generate",
            json={"team_name": "  Tigers  "},
        )
        self.assertEqual(created.status_code, 201)
        team = created.json()
        self.assertEqual(team["team_name"], "Tigers")
        self.assertIsInstance(team["id"], int)

        listed = self.client.get("/api/teams")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json(), [team])

        deleted = self.client.delete(f"/api/teams/{team['id']}")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get("/api/teams").json(), [])

    def test_register_rejects_empty_team_name(self) -> None:
        response = self.client.post(
            "/api/teams/generate",
            json={"team_name": "   "},
        )
        self.assertEqual(response.status_code, 422)

    def test_delete_returns_not_found_for_unknown_team(self) -> None:
        response = self.client.delete("/api/teams/999")
        self.assertEqual(response.status_code, 404)

    def test_frontend_origin_can_call_api(self) -> None:
        response = self.client.options(
            "/api/teams/generate",
            headers={
                "Origin": "http://127.0.0.1:5500",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://127.0.0.1:5500",
        )


if __name__ == "__main__":
    unittest.main()
