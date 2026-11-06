# Cricket Tournament Teams API

The API stores teams in PostgreSQL. You need PostgreSQL running locally or a
reachable PostgreSQL server before starting the API.

## 1. Create a PostgreSQL database

Install PostgreSQL if needed, and remember the password you set for the
`postgres` user. In pgAdmin:

1. Connect to your PostgreSQL server.
2. Right-click **Databases** and select **Create > Database**.
3. Enter `cricket_league` as the database name and save.

The application creates the `teams` table automatically the first time it
starts. You do not need to create the table manually.

## 2. Install and start the API

Open PowerShell and run these commands one at a time:

```powershell
cd C:\ai-cricket-league\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/cricket_league"
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Replace `YOUR_PASSWORD` with the password for your PostgreSQL user. If you use
a different PostgreSQL username, password, host, port, or database name, update
the URL accordingly. URL-encode special characters in the password (for
example, `@` as `%40`).

`DATABASE_URL` is set only for the current PowerShell window. Set it again in
any new window before starting the API. Keep the server window open while
using the application; press **Ctrl+C** to stop the server.

The API is available at `http://127.0.0.1:8000`, and interactive documentation
is at `http://127.0.0.1:8000/docs`.

## 3. Register, list, and delete teams

Use the interactive documentation at `/docs`, or send HTTP requests:

- `POST /api/teams/generate` with JSON `{"team_name": "Tigers"}` registers a
  team. PostgreSQL assigns its ID and creation timestamp.
- `GET /api/teams` reads saved teams, ordered by ID.
- `DELETE /api/teams/{team_id}` deletes that team. It returns 404 if the ID
  does not exist.

The POST endpoint inserts the team name into PostgreSQL and returns the
database-generated row. The GET endpoint selects saved rows, and DELETE removes
the row with the matching ID. Values remain in the database after the API
stops or restarts.

## Tests

Run `python -m unittest -v` from this folder. These tests mock PostgreSQL, so
they verify API behavior without requiring a running database.
