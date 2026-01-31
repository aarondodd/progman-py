# Lab 4: Mocking with unittest.mock

Some code interacts with the outside world: launching processes, making network
requests, showing dialog boxes. You do not want your tests to actually launch
programs or hit the internet. **Mocking** lets you replace those external calls
with controlled fakes so you can test the logic around them.

## What is mocking?

A mock is a substitute object that records how it was called and returns
whatever you tell it to. Instead of calling the real `subprocess.Popen`, your
test provides a mock that pretends to be `Popen`, and then you check that it
was called with the right arguments.

Python's standard library includes everything you need in `unittest.mock`.

> **Official docs:** [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## patch: replacing objects temporarily

The most common tool is `patch`. It temporarily replaces an object with a
`MagicMock` for the duration of a test. Here is a real example from
`tests/test_launcher.py`:

```python
from unittest.mock import patch
from progman.models.program_item import ProgramItem
from progman.utils.launcher import Launcher


class TestLauncher:
    def test_launch_calls_popen(self, qapp):
        item = ProgramItem(title="Test", command="echo hello")
        with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
            Launcher.launch(item)
            mock_popen.assert_called_once_with(
                "echo hello", shell=True, cwd=None
            )
```

### What is happening here?

1. `patch("progman.utils.launcher.subprocess.Popen")` replaces `subprocess.Popen`
   inside the `launcher` module with a `MagicMock`.
2. The `as mock_popen` gives you a reference to the mock.
3. `Launcher.launch(item)` runs the real code, but when it calls
   `subprocess.Popen(...)`, it actually calls the mock instead.
4. `mock_popen.assert_called_once_with(...)` verifies the mock was called
   exactly once with the expected arguments.

When the `with` block exits, the real `subprocess.Popen` is restored.

### Where to patch

The string you pass to `patch` is the **location where the object is used**,
not where it is defined. The `Launcher` class imports `subprocess` inside
`progman.utils.launcher`, so you patch `progman.utils.launcher.subprocess.Popen`.

This is a common mistake:

```python
# WRONG: patches subprocess in the subprocess module itself
with patch("subprocess.Popen"):

# RIGHT: patches subprocess where launcher.py looks it up
with patch("progman.utils.launcher.subprocess.Popen"):
```

> **Official docs:** [Where to patch](https://docs.python.org/3/library/unittest.mock.html#where-to-patch)

## Asserting calls

Mocks track every call made to them. Common assertions:

```python
mock.assert_called_once()               # called exactly once
mock.assert_called_once_with(arg1, kw=val)  # once, with specific args
mock.assert_not_called()                # never called
mock.assert_called()                    # called at least once
```

From the project -- verifying that an empty command does nothing:

```python
def test_launch_empty_command_does_nothing(self, qapp):
    item = ProgramItem(title="Empty", command="")
    with patch("progman.utils.launcher.subprocess.Popen") as mock_popen:
        Launcher.launch(item)
        mock_popen.assert_not_called()
```

## Simulating errors with side_effect

`side_effect` makes the mock raise an exception when called. This lets you
test error handling without causing real errors:

```python
def test_launch_error_shows_messagebox(self, qapp):
    item = ProgramItem(title="Bad", command="nonexistent")
    with patch("progman.utils.launcher.subprocess.Popen", side_effect=OSError("fail")):
        with patch("progman.utils.launcher.QMessageBox.critical") as mock_msg:
            Launcher.launch(item)
            mock_msg.assert_called_once()
            args = mock_msg.call_args
            assert "Launch Error" in args[0][1]
```

This test does two things:

1. Makes `Popen` raise an `OSError` when called.
2. Mocks `QMessageBox.critical` to prevent a real dialog from appearing.
3. Verifies that the error dialog was shown with the right title.

Notice you can nest `with patch(...)` blocks to mock multiple things at once.

## Mocking return values

You can control what a mock returns with `return_value`:

```python
mock_response = MagicMock()
mock_response.read.return_value = b'{"tag_name": "v2.0.0"}'
```

From `tests/test_updater.py`, here is how the project mocks an HTTP response
from the GitHub API:

```python
def test_successful_fetch(self):
    config = {"owner": "test", "repo": "test"}
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "tag_name": "v2.0.0",
        "zipball_url": "https://example.com/download.zip",
    }).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("progman.utils.updater.urllib.request.urlopen",
               return_value=mock_response):
        result = get_latest_release(config)
        assert result is not None
        assert result["tag_name"] == "2.0.0"
```

The `__enter__` and `__exit__` methods make the mock work with `with`
statements (context managers). This is a common pattern when mocking file-like
or network objects.

## Mocking with patch as a function argument

Instead of `with` blocks, you can also pass `return_value` directly to
`patch`:

```python
with patch("progman.utils.updater.get_last_version_check", return_value=None):
    assert should_check_for_updates(config) is True
```

This replaces `get_last_version_check` with a mock that returns `None` when
called.

## Stacking patches

When you need multiple mocks, the `with` blocks nest:

```python
def test_returns_versions_when_update_available(self):
    config = {"owner": "test", "repo": "test"}
    with patch("progman.utils.updater.should_check_for_updates", return_value=True):
        with patch("progman.utils.updater.record_version_check"):
            with patch("progman.utils.updater.get_latest_release", return_value={
                "tag_name": "99.0.0",
                "zipball_url": "https://example.com/dl.zip",
            }):
                result = check_for_updates(config)
                assert result is not None
                local, remote = result
                assert remote == "99.0.0"
```

This test isolates `check_for_updates` from all its dependencies:
- `should_check_for_updates` is forced to return `True` (skip the throttle).
- `record_version_check` is silenced (do not write to disk).
- `get_latest_release` returns a fake API response.

## MagicMock vs Mock

`MagicMock` is a `Mock` with all magic methods pre-configured (`__enter__`,
`__exit__`, `__len__`, etc.). Use `MagicMock` unless you have a reason not to
-- it handles more cases automatically.

```python
from unittest.mock import MagicMock, Mock

mock = MagicMock()
mock.some_method(42)
mock.some_method.assert_called_with(42)
```

> **Official docs:** [MagicMock](https://docs.python.org/3/library/unittest.mock.html#magicmock-and-magic-method-support)

## When to mock and when not to

**Do mock:**

- External processes (`subprocess.Popen`)
- Network calls (`urllib`, `requests`)
- GUI dialogs (`QMessageBox`)
- File system operations when testing logic, not I/O
- Time-dependent functions (`datetime.now()`)

**Do not mock:**

- The code you are testing (that defeats the purpose).
- Simple data structures (just create real ones).
- Everything -- if you mock too much, the test proves nothing about real
  behavior.

A good rule: mock at the boundary between your code and the outside world.

## Exercise

Write a test for a function that reads a URL and returns the status code.
Mock `urllib.request.urlopen` to return a mock response with `.status = 200`.
Then write a second test where the mock raises `urllib.error.URLError` and
verify the function handles it.

## Key takeaways

- `patch` temporarily replaces an object with a mock.
- Always patch where the object is **used**, not where it is **defined**.
- `assert_called_once_with` verifies exact call arguments.
- `side_effect` simulates exceptions.
- `return_value` controls what the mock returns.
- Mock external boundaries; use real objects for internal code.

## Next

[Lab 5: Testing with Files and Fixtures](05_testing_with_files.md) -- combine
fixtures, temporary files, and assertions to test config loading and migration.
