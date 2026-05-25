# Run Guide

Commands to run the project locally on Windows PowerShell.

## 1. Activate the virtual environment

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
```

## 2. Run tests

### Normal tests

```powershell
python -m pytest -q
```

### Integration tests

Run integration tests directly; the test schema is created and dropped
automatically by the test fixtures.

PowerShell:

```powershell
python -m pytest tests\integration -q
```

Linux / macOS:

```bash
python -m pytest tests/integration -q
```

### Tests for a specific folder

```powershell
python -m pytest tests\unit -q
python -m pytest tests\integration -q
```

### Coverage

```powershell
python -m pytest --cov=backend.app --cov-report=html
```

## 3. Start the backend

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend available at:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

## 4. Start the frontend

```powershell
Set-Location frontend
npm run dev
```

Frontend available at:

```text
http://localhost:3000
```

## 5. Run migrations

```powershell
alembic upgrade head
```

## 6. Common support commands

```powershell
pre-commit run --all-files
python -m pytest tests\unit\test_user_use_cases.py -q
python -m pytest tests\integration\test_user_api.py -q
```
