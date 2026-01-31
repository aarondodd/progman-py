# Lab 1: Getting Started with Python Testing

This tutorial series teaches you how to write unit tests in Python using
[pytest](https://docs.pytest.org/). Every example comes from the progman-py
project so you can read the real code alongside these labs.

## Prerequisites

- Python 3.10 or later installed
- A terminal / command prompt
- A text editor

No prior Python testing experience is assumed. If you are new to Python itself,
the official [Python Tutorial](https://docs.python.org/3/tutorial/index.html)
is a good starting point.

## What is a unit test?

A unit test is a small piece of code that checks whether another piece of code
behaves correctly. "Unit" means you are testing one thing in isolation -- a
single function, a single class method, or a single behavior. If the code
works, the test passes. If it does not, the test fails and tells you what went
wrong.

## Why bother?

- **Catch bugs early.** A test that runs in a second can find a problem that
  would take minutes to reproduce manually.
- **Prevent regressions.** When you change code later, existing tests tell you
  immediately if you broke something.
- **Document behavior.** A test is an executable specification. Reading
  `test_empty_command_does_nothing` tells you exactly what happens when a
  command is empty.

## Installing pytest

pytest is the most popular Python testing framework. Install it with pip:

```bash
pip install pytest
```

For this project, you can install all development dependencies at once:

```bash
pip install -r requirements-dev.txt
```

This installs `pytest` along with `pytest-qt` (a plugin for testing Qt
applications).

> **Official docs:** [Installing pytest](https://docs.pytest.org/en/stable/getting-started.html#install-pytest)

## Your first test

Create a file called `test_hello.py` (the `test_` prefix is important --
pytest uses it to find test files):

```python
def test_addition():
    assert 1 + 1 == 2
```

Run it:

```bash
pytest test_hello.py -v
```

Output:

```
test_hello.py::test_addition PASSED
```

That is all there is to a minimal test:

1. A function whose name starts with `test_`.
2. An `assert` statement that checks a condition.

If the condition is `True`, the test passes. If `False`, pytest reports a
failure with a helpful message showing what the values actually were.

## The assert statement

Python's built-in `assert` is the only tool you need. pytest enhances it to
show detailed failure information automatically. You do not need special
assertion methods like `assertEqual` or `assertTrue`.

```python
def test_string_methods():
    name = "Program Manager"
    assert name.lower() == "program manager"
    assert name.startswith("Program")
    assert len(name) == 15
```

When an assertion fails, pytest shows both the expected and actual values:

```
    assert len(name) == 999
AssertionError: assert 15 == 999
```

> **Official docs:** [The assert statement](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement)

## Test file and function naming conventions

pytest discovers tests automatically using these rules:

| Convention | Example |
|---|---|
| Test files start with `test_` | `test_models.py` |
| Test functions start with `test_` | `def test_create_basic():` |
| Test classes start with `Test` | `class TestProgramItem:` |
| Test methods start with `test_` | `def test_roundtrip(self):` |

In this project, every test file in the `tests/` directory follows this
pattern. For example, `test_models.py` tests the code in `progman/models/`.

## Organizing tests into classes

You can group related tests inside a class. This is optional but keeps things
tidy when you have many tests for the same subject. From our project's
`tests/test_models.py`:

```python
class TestProgramItem:
    def test_create_basic(self):
        item = ProgramItem(title="Test", command="echo hello")
        assert item.title == "Test"
        assert item.command == "echo hello"

    def test_create_full(self):
        item = ProgramItem(
            title="Editor",
            command="vim",
            working_dir="/tmp",
            icon_path="/usr/share/icons/vim.png",
        )
        assert item.working_dir == "/tmp"
```

Notice:

- The class name starts with `Test`.
- Each method takes `self` as its first parameter (standard Python class
  method), but you do not need `__init__` or any setup.
- Each method is an independent test. If one fails, the others still run.

## Running tests

Run all tests in a directory:

```bash
pytest tests/ -v
```

Run a single file:

```bash
pytest tests/test_models.py -v
```

Run a single test class:

```bash
pytest tests/test_models.py::TestProgramItem -v
```

Run a single test function:

```bash
pytest tests/test_models.py::TestProgramItem::test_create_basic -v
```

The `-v` flag means "verbose" -- it shows each test name and its result.

> **Official docs:** [How to invoke pytest](https://docs.pytest.org/en/stable/how-to/usage.html)

## What you have learned

- A test is a function that uses `assert` to check that code behaves correctly.
- pytest discovers test files and functions by their `test_` prefix.
- You can group tests into classes starting with `Test`.
- `pytest tests/ -v` runs your test suite.

## Next

[Lab 2: Testing Data Models](02_testing_data_models.md) -- write tests for
Python dataclasses using examples from this project.
