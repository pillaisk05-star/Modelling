# NumAdd

A web application that specialises in adding numbers. Provides a browser UI and a REST API.

## Architecture

The full C4 model diagrams are in the parent directory:

| Level | File | Description |
|-------|------|-------------|
| Level 1 | [numadd-c4-level1-context.md](../numadd-c4-level1-context.md) | System Context — users and external systems |
| Level 2 | [numadd-c4-level2-container.md](../numadd-c4-level2-container.md) | Containers — web app, API, cache |
| Level 3 | [numadd-c4-level3-component.md](../numadd-c4-level3-component.md) | Components inside the REST API |
| Level 4 | [numadd-c4-level4-code.md](../numadd-c4-level4-code.md) | Class diagram for the Addition Service |

## Project Structure

```
numadd/
├── app.py               # Flask API entry point
├── addition_service.py  # Core addition logic
├── input_validator.py   # Input validation
├── cache_service.py     # In-memory cache
├── log_service.py       # Logging
└── test_numadd.py       # Pytest tests
```

## Run the API

```bash
pip3 install flask
python3 app.py
```

Then call:
```
GET http://localhost:5000/add?a=3&b=4
```

Response:
```json
{"a": 3.0, "b": 4.0, "result": 7.0, "cached": false}
```

## Run Tests

```bash
cd numadd
python3 -m pytest test_numadd.py -v
```
