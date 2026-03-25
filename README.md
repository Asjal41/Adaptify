# CogniLearn AI

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

## Running the Application

### Backend

Run the FastAPI server:
```bash
uvicorn backend.main:app --reload
```
The API will be available at http://localhost:8000.

### Frontend

Open `frontend/login.html` in your browser or use Live Server extension in VS Code.

## API Testing

Use the `api_tests.http` file with the REST Client extension to test the API endpoints directly.
Required steps:
1. Register a teacher.
2. Login as teacher (token is set automatically).
3. Register a student.
4. Login as student.
5. Upload materials.
6. Submit student IQ.
7. Generate assignment (as teacher).
