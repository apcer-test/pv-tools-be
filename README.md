# Apcer Fastapi Starter

Apcer Fastapi Starter is a comprehensive boilerplate for building FastAPI applications. It uses Poetry for dependency management and Docker for containerization. Pre-commit hooks and deployment configurations are also included to streamline development.

## Features

FastAPI: Modern, fast (high-performance) web framework for building APIs with Python 3.7+.
- Poetry: Dependency management and packaging tool.
- Pre-commit Hooks: Pre-configured hooks for code quality and consistency.
- Mega Linter: An advanced tool to ensure code quality across various languages and formats.

## Getting Started

### 1.Clone the repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2.Checkout to the Development Branch

```bash
git checkout development
```

## Setup

### 1. Activate the Poetry virtual environment

```bash
poetry shell
```

### 2. Install dependencies using Poetry

```bash
poetry install
```

## Folder Structure

```bash
your-repo-name/
├── src/
│   ├── apps/
│   │   ├── module_file/
│   │   │   ├── controller/
│   │   │   ├── schemas/
│   │   │   ├── models/
│   │   │   ├── services/
│   ├── migrations/
│   ├── main.py
│   ├── ... (other directories and files)
├── docker-compose-local.yml
├── Dockerfile
├── pyproject.toml
├── env.example
└── README.md

```

## configurations

Configuration settings for the application should be defined in the `.env` file. Copy the `env.example` to `.env` and adjust the settings as needed.
there will be a variable named DECRYPT_REQUEST_TIME_CHECK in env make it to 'True' if it's in production else keep it to 'False' in local or devlopment enviornoment

There will be a variable named `DECRYPT_REQUEST_TIME_CHECK` in the `.env`. Set it to `'True'` if it's in production, else keep it `'False'` in local or development environment.

This variable is used in the decrypt function.

- If set to `True`, it will **seek a timestamp** from the encrypted payload and compare it with the current time. If the time difference is **within the limit defined by the `PAYLOAD_TIMEOUT`** variable in the `constants.py` file, it will return the token. Otherwise, it will raise an `InvalidPayload` error.

```bash
{
  "email": "admin@gmail.com",
  "password": "Admin@123",
  "timestamp": "2025-07-09T12:12:08.913Z" #timestamp of the time when payload was created
}
```

- If set to `False`, the function will **only extract email and password** from the encrypted payload, and if they are correct, it will return the access token without checking the timestamp.

```bash
{
  "email": "admin@gmail.com",
  "password": "Admin@123"
}
```

## Local Development

The Docker-compose.yml file can be used to run the postgresql and Pgadmin Service when needed

```bash
docker compose -f docker-compose-local.yml up
```

## To run the project

1. Navigate to the `src` directory:

```bash
cd src/
```

2. Make-migrations for database:

```bash
python main.py make-migrations
```

3. Execute the seeder File in the migration version file

```bash
 op.create_index(op.f('****'), '****', ['*****'], unique=False)
    op.create_index(op.f('****'), '****', ['****'], unique=False)
    # ### end Alembic commands ###
    op.execute(sql_for_create_admin)
    #This command is used to create a default admin entry.
```

4. Migrate the database

```bash
python main.py migrate
```

4. Run the Project

```bash
python main.py run --host=0.0.0.0 --port=8080 --debug
```

## API Usage Examples

### User Sign-In

**Endpoint:** `/user/sign-in`  
**Method:** `POST`

**Request Body:**

```json
{
  "encrypted_data": "...",
  "encrypted_key": "...",
  "iv": "..."
}
```

**Response:**

```json
{
  "status": "SUCCESS",
  "code": 200,
  "data": {
    "access_token": "...",
    "refresh_token": "..."
  }
}
```

### User Creation

**Endpoint:** `/user/sign-up`  
**Method:** `POST`

**Request Body:**

```json
{
  "encrypted_data": "...",
  "encrypted_key": "...",
  "iv": "..."
}
```

**Response:**

```json
{
  "status": "SUCCESS",
  "code": 201,
  "data": {
    "id": "...",
    "email": "...",
    "first_name": "...",
    "last_name": "...",
    "phone": "..."
  }
}
```

> **Note:** All sensitive data (email, password, etc.) must be encrypted as per the encryption scheme described in the project.

````

## Code Quality Check

### Pre-commit hooks

This boilerplate includes several pre-commit hooks configured to ensure code quality and consistency. These hooks are defined in the pyproject.toml file under the [tool.pre-commit] section. The most commonly used hooks include:

- black : Code formatter
- ruff : Linter for Python code
- interrogate : Static analysis tool

### To install pre-commit hooks, run

```bash
pre-commit install
````

### To run the hooks manually on all files, use

```bash
pre-commit run --all-files
```

### Mega-linter

#### Mega-Linter is a tool for linting and formatting code. It supports many languages and formats. This boilerplate includes a basic configuration for Mega-Linter

### To run the Mega-Linters locally, use

```bash
npx mega-linter-runner
```

## Notes

- Ensure that your Docker services are running if your application depends on PostgreSQL or any other services defined in your docker-compose-local.yml.
- Adjust the python main.py run --host=0.0.0.0 --port=8080 --debug command to fit your project's entry point and configuration if needed.
- This should provide a clear, step-by-step guide to setting up and running your FastAPI project using Apcer Fastapi Starter.
