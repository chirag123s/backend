# Carreb - API

Carreb API is designed to provide API endpoint and bakend processing related to Carreb service.

This setup is Dockerized provide the necessary framework and services that includes Django REST Framework, MariaDB, and NGiNX.

## Installation

### Prerequisites

- **Docker**
- **Python 3**

### Setup Instructions

1. Clone the repository
   
    Go to the local or deployment path. Clone the repository:
    &nbsp;&nbsp;&nbsp;&nbsp;`git clone git@bitbucket.org:carreb/backend.git`<br>

    Change directory to the backend:
    &nbsp;&nbsp;&nbsp;&nbsp;`cd backend`

    Build and run the docker container as daemon:
    &nbsp;&nbsp;&nbsp;&nbsp;`docker-compose up --build -d`

    Open and connect to the MariaDB hosted on a container, the connection details can be found in *docker-compose.yml*

    Create an empty database *carreb_db* and assign a user using details from *docker-compose.yml*

2. Setup local environment

    Change directory to the Django app:
    &nbsp;&nbsp;&nbsp;&nbsp;`cd django_app`

    Build local environment:
    &nbsp;&nbsp;&nbsp;&nbsp;`python3 -m venv .venv`

    Activate environment:
    (Mac/linux)
    &nbsp;&nbsp;&nbsp;&nbsp;`source .venv/bin/activate`

    Install dependencies:    
    &nbsp;&nbsp;&nbsp;&nbsp;`pip3 install -r requirements.txt`
    
3. Initialise database
   
    Run initial migrations:
    &nbsp;&nbsp;&nbsp;&nbsp;`python3 manage.py makemigrations`
    &nbsp;&nbsp;&nbsp;&nbsp;`python3 manage.py migrate`

    Update .env with the database details from *docker-compose.yml*

    Create local super user:
    &nbsp;&nbsp;&nbsp;&nbsp;`python3 manage.py createsuperuser`

3. Run local server

    &nbsp;&nbsp;&nbsp;&nbsp;`python3 manage.py runserver 8001`

    Open browser and open http;//localhost:8001 .   This should open the Django landing page.