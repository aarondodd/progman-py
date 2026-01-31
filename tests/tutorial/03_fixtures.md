# Lab 3: Fixtures and Temporary Files

Many tests need setup work before they can run: creating files, initializing
objects, or preparing test data. pytest **fixtures** let you define that setup
once and reuse it across many tests.

## The problem: repeated setup

Imagine writing several tests that all need a config file on disk. Without
fixtures, every test would have to create the file itself:

```python
def test_load_config():
    path = "/tmp/test_config.json"
    with open(path, "w") as f:
        json.dump({"dark_mode": False, "groups": []}, f)
    model = AppModel(config_path=path)
    assert model.dark_mode is False

def test_save_config():
    path = "/tmp/test_config.json"
    with open(path, "w") as f:
        json.dump({"dark_mode": False, "groups": []}, f)
    # ... more test logic
```

This has problems:

- The setup code is duplicated.
- Tests write to `/tmp`, which may conflict with other tests or persist after
  failure.
- Cleanup is your responsibility.

## What is a fixture?

A fixture is a function decorated with `@pytest.fixture` that provides
something a test needs. Tests request it by adding the fixture name as a
parameter:

```python
import pytest

@pytest.fixture
def greeting():
    return "hello"

def test_greeting_length(greeting):
    assert len(greeting) == 5
```

When pytest sees `greeting` in the test's parameter list, it calls the
`greeting()` function and passes the result to the test.

> **Official docs:** [About fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)

## Built-in fixture: tmp_path

pytest provides `tmp_path` out of the box. It gives each test a unique
temporary directory that is automatically cleaned up:

```python
def test_write_file(tmp_path):
    my_file = tmp_path / "data.txt"
    my_file.write_text("hello")
    assert my_file.read_text() == "hello"
```

`tmp_path` is a `pathlib.Path` object. Each test gets its own directory, so
tests never interfere with each other.

> **Official docs:** [tmp_path fixture](https://docs.pytest.org/en/stable/how-to/tmp_path.html)

## Real example: conftest.py

Fixtures defined in a file called `conftest.py` are available to all tests in
that directory (and subdirectories) without needing an import. This is where
project-wide fixtures live.

Here is this project's `tests/conftest.py`:

```python
import json
import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def tmp_config(tmp_path):
    """Provide a temporary config file path."""
    return tmp_path / "test_progman.json"


@pytest.fixture
def sample_config(tmp_config):
    """Provide a temporary config file with sample data."""
    data = {
        "config_version": 1,
        "dark_mode": False,
        "groups": [
            {"title": "Main", "items": [
                {"title": "Test App", "command": "echo hello"}
            ]},
        ],
    }
    with open(tmp_config, "w") as f:
        json.dump(data, f)
    return tmp_config
```

Let's break this down.

### tmp_config: building on built-in fixtures

```python
@pytest.fixture
def tmp_config(tmp_path):
    return tmp_path / "test_progman.json"
```

This fixture **takes another fixture as a parameter**. `tmp_path` is provided
by pytest; `tmp_config` builds on it to return a path where a test config can
be written. The file does not exist yet -- it just provides the path.

### sample_config: building on your own fixtures

```python
@pytest.fixture
def sample_config(tmp_config):
    data = { ... }
    with open(tmp_config, "w") as f:
        json.dump(data, f)
    return tmp_config
```

This fixture depends on `tmp_config`. It writes JSON data to the file and
returns the path. Tests that need a pre-populated config file request
`sample_config`:

```python
def test_load_existing_config(self, sample_config):
    model = AppModel(config_path=sample_config)
    assert model.dark_mode is False
    assert len(model.groups) == 2
```

### Fixture chaining

The chain works like this:

```
pytest provides tmp_path (unique temp directory)
        |
  tmp_config uses tmp_path (creates a file path)
        |
  sample_config uses tmp_config (writes data to the file)
        |
  test_load_existing_config uses sample_config (loads and tests)
```

Each link does one job. You can mix and match -- some tests use `tmp_config`
(empty), others use `sample_config` (pre-populated).

## Fixture scope

By default, a fixture runs once **per test function**. You can change this
with the `scope` parameter:

| Scope | Fixture runs... |
|---|---|
| `"function"` (default) | Once per test function |
| `"class"` | Once per test class |
| `"module"` | Once per test file |
| `"session"` | Once for the entire test run |

The `qapp` fixture uses `scope="session"` because creating a `QApplication` is
expensive and only one can exist at a time:

```python
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
```

> **Official docs:** [Fixture scope](https://docs.pytest.org/en/stable/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session)

## yield fixtures: setup and teardown

When a fixture uses `yield` instead of `return`, the code after `yield` runs
as teardown when the test finishes:

```python
@pytest.fixture
def database_connection():
    conn = create_connection()
    yield conn
    conn.close()  # runs after the test, even if it fails
```

The `qapp` fixture above uses `yield` so the application object stays alive
for the duration of the session.

## Using fixtures in test classes

Class-based tests request fixtures through method parameters (after `self`):

```python
class TestAppModel:
    def test_load_default_when_no_config(self, tmp_config):
        model = AppModel(config_path=tmp_config)
        assert model.config_version == 1

    def test_load_existing_config(self, sample_config):
        model = AppModel(config_path=sample_config)
        assert len(model.groups) == 2
```

Different tests in the same class can use different fixtures. Each test gets a
fresh instance of its fixtures.

## Why this matters: test isolation

Every test in this project uses temporary paths for config files. No test ever
touches `~/.progman.json`. This is critical:

- Tests can run in parallel without conflicts.
- A failing test cannot corrupt your real config.
- Tests work on any machine, not just yours.

## Exercise

Write a fixture called `old_format_config` that creates a config file in the
pre-v1 format (with `"theme": "classic"` instead of `"dark_mode": true`). Use
it in a test that loads the config and verifies migration happened. Then check
`tests/conftest.py` to see how the project does it.

## Key takeaways

- Fixtures provide reusable test setup via `@pytest.fixture`.
- `tmp_path` gives each test a unique temporary directory.
- Fixtures can depend on other fixtures, forming a chain.
- `conftest.py` makes fixtures available to all tests without imports.
- Use `scope="session"` for expensive, shared resources.
- `yield` enables cleanup code that runs after the test.

## Next

[Lab 4: Mocking with unittest.mock](04_mocking.md) -- learn how to test code
that calls external systems without actually calling them.
