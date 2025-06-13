# Elifoot Online

A web-based, multiplayer football management game inspired by the classic Elifoot 98, built with Python and Flask.

## Features

-   **Authentic League**: Based on the 12 teams of the 2023-2024 Liga BPI (Portuguese Women's League).
-   **Dynamic Squads**: Each team is populated with a unique roster of 22 players, each with distinct skills and attributes.
-   **Full Season Simulation**: A complete round-robin fixture calendar for the entire 22-round season.
-   **Live Match Day**: Simulate an entire fixture's games with a minute-by-minute clock, live score updates, and a goal-by-goal event log.
-   **Player Progression**: Goals scored during simulations are tracked and updated in each player's profile.
-   **League Standings**: A "Competitions" page features a real-time classification table and a list of the league's top 10 goalscorers.

## Tech Stack

-   **Backend**: Python, Flask, Flask-SocketIO, Flask-SQLAlchemy
-   **Frontend**: HTML, CSS, JavaScript
-   **Database**: SQLite

## How to Run the Project

1.  **Clone the Repository**
    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd <repository_folder>
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```

5.  **Initialize the Game Database**
    -   Open your web browser and navigate to `http://127.0.0.1:5000/populate-db`.
    -   This is a one-time step that will create the database, teams, players, and fixtures. You will be redirected to the "Competitions" page.

6.  **Start Playing!**
    -   Navigate to the "Match Day" tab (`http://127.0.0.1:5000`) to start simulating fixtures.


