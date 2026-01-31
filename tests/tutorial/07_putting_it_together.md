# Lab 7: Putting It All Together

This final lab covers how to organize a test suite, run it effectively, and
where to go next.

## Project test structure

Here is how this project organizes its tests:

```
tests/
├── __init__.py               # Makes tests/ a package (can be empty)
├── conftest.py               # Shared fixtures (qapp, tmp_config, etc.)
├── tutorial/                 # This tutorial (not test code)
├── test_models.py            # Tests for ProgramItem, ProgramGroup, AppModel
├── test_config_migration.py  # Tests for v0 -> v1 config migration
├── test_launcher.py          # Tests for Launcher (mocked subprocess)
├── test_scanner.py           # Tests for program scanner (.desktop, .lnk)
├── test_theme.py             # Tests for ThemeManager stylesheets
├── test_updater.py           # Tests for GitHub updater (mocked network)
├── test_widgets.py           # Tests for GroupWindow (offscreen Qt)
└── test_drag_drop.py         # Tests for drag-and-drop setup and behavior
```

### Naming convention

Each test file corresponds to a module or feature:

| Source file | Test file |
|---|---|
| `progman/models/program_item.py` | `tests/test_models.py` |
| `progman/utils/launcher.py` | `tests/test_launcher.py` |
| `progman/utils/scanner.py` | `tests/test_scanner.py` |
| `progman/utils/theme.py` | `tests/test_theme.py` |
| `progman/utils/updater.py` | `tests/test_updater.py` |
| `progman/widgets/group_window.py` | `tests/test_widgets.py`, `tests/test_drag_drop.py` |
| `progman/models/app_model.py` | `tests/test_models.py`, `tests/test_config_migration.py` |

Some modules have multiple test files when the functionality is complex enough
to warrant separate concerns (e.g., `app_model` has basic model tests and
dedicated migration tests).

### What goes in conftest.py

Put fixtures in `conftest.py` when they are used by **multiple test files**.
Fixtures used by only one file can live in that file instead. In this project:

- `qapp` -- used by widget, theme, launcher, and drag-drop tests
- `tmp_config` -- used by model and migration tests
- `sample_config`, `old_format_config` -- used by model and migration tests

## Running the full suite

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run all tests with verbose output
QT_QPA_PLATFORM=offscreen pytest tests/ -v
```

Note: `QT_QPA_PLATFORM=offscreen` is set in `conftest.py` so you do not
strictly need it on the command line, but it is harmless to include.

Example output:

```
tests/test_models.py::TestProgramItem::test_create_basic PASSED
tests/test_models.py::TestProgramItem::test_roundtrip PASSED
tests/test_launcher.py::TestLauncher::test_launch_calls_popen PASSED
...
========================= 95 passed in 1.50s ==========================
```

## Useful pytest options

| Option | What it does |
|---|---|
| `-v` | Verbose -- show each test name and result |
| `-x` | Stop on first failure |
| `-k "pattern"` | Run only tests matching a name pattern |
| `--tb=short` | Shorter tracebacks on failure |
| `--tb=long` | Full tracebacks |
| `-s` | Show print() output (normally captured) |
| `--lf` | Re-run only tests that failed last time |

Examples:

```bash
# Run only migration tests
pytest tests/ -v -k "migration"

# Run only tests with "roundtrip" in the name
pytest tests/ -v -k "roundtrip"

# Stop at first failure and show full traceback
pytest tests/ -x --tb=long
```

> **Official docs:** [Command-line flags](https://docs.pytest.org/en/stable/reference/reference.html#command-line-flags)

## Anatomy of a good test

Looking back at every test in this project, they follow a consistent pattern:

```
1. ARRANGE  -- set up the objects and data you need
2. ACT      -- call the function or method being tested
3. ASSERT   -- check the result
```

Example:

```python
def test_launch_with_working_dir(self, qapp):
    # Arrange
    item = ProgramItem(title="Test", command="echo hello", working_dir="/tmp")

    # Act
    with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
        Launcher.launch(item)

    # Assert
    mock_popen.assert_called_once_with("echo hello", shell=True, cwd="/tmp")
```

Keep each test focused on **one behavior**. If a test needs a comment to
explain what it checks, consider splitting it or improving the test name.

## What makes a good test name?

Test names should describe the scenario and expected outcome:

```python
# Good -- describes what happens
def test_empty_command_does_nothing(self):
def test_v0_to_v1_preserves_groups(self):
def test_parse_with_relative_path_fallback(self):

# Less good -- too vague
def test_launch(self):
def test_migration(self):
def test_parse(self):
```

A person reading the test name alone should understand what is being verified.

## Quick reference: techniques by lab

| Technique | Lab | Example file |
|---|---|---|
| Basic assertions | Lab 1 | `test_models.py` |
| Testing dataclasses | Lab 2 | `test_models.py` |
| Fixtures and tmp_path | Lab 3 | `conftest.py`, `test_config_migration.py` |
| Mocking with patch | Lab 4 | `test_launcher.py`, `test_updater.py` |
| File-based testing | Lab 5 | `test_config_migration.py` |
| GUI testing (offscreen) | Lab 6 | `test_widgets.py`, `test_theme.py` |

## Checklist for writing tests

When adding a new feature or fixing a bug, ask yourself:

- [ ] Did I test the normal/happy path?
- [ ] Did I test edge cases (empty input, missing data, invalid values)?
- [ ] Did I test error handling (what happens when things go wrong)?
- [ ] If the code reads/writes files, did I use `tmp_path`?
- [ ] If the code calls external systems, did I mock them?
- [ ] If the code uses Qt widgets, did I request the `qapp` fixture?
- [ ] Does each test check one specific behavior?
- [ ] Do my test names describe what they verify?

## Further reading

- [pytest documentation](https://docs.pytest.org/en/stable/) -- the full
  reference for everything pytest can do.
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html) --
  comprehensive guide to Python's mocking library.
- [pytest-qt documentation](https://pytest-qt.readthedocs.io/) -- testing Qt
  applications with pytest.
- [Python Testing with pytest (book)](https://pragprog.com/titles/bopytest2/python-testing-with-pytest-second-edition/) --
  a thorough book-length treatment.
- [dataclasses documentation](https://docs.python.org/3/library/dataclasses.html) --
  understanding the model classes used throughout.
- [Real Python: Testing in Python](https://realpython.com/python-testing/) --
  a broad introduction covering multiple frameworks.

## Summary of the series

| Lab | Topic |
|---|---|
| [Lab 1](01_getting_started.md) | Installing pytest, writing your first test, assert, running tests |
| [Lab 2](02_testing_data_models.md) | Testing dataclasses: construction, serialization, roundtrips |
| [Lab 3](03_fixtures.md) | Fixtures, tmp_path, conftest.py, scope, yield |
| [Lab 4](04_mocking.md) | Mocking with patch, side_effect, return_value |
| [Lab 5](05_testing_with_files.md) | File-based tests, config loading, migration testing |
| [Lab 6](06_testing_gui.md) | Offscreen Qt testing, widget state, theme verification |
| [Lab 7](07_putting_it_together.md) | Organization, running the suite, best practices |

You now have all the tools used to build and maintain the 95 tests in this
project. Start with the exercises in each lab, then try adding a test for a
feature you care about. The best way to learn testing is to write tests.
