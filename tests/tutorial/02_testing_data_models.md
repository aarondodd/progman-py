# Lab 2: Testing Data Models

In this lab you will learn how to test Python dataclasses by examining the
tests for `ProgramItem` and `ProgramGroup` in this project.

## The code under test

Open `progman/models/program_item.py`:

```python
from dataclasses import asdict, dataclass

@dataclass
class ProgramItem:
    title: str
    command: str
    working_dir: str = ""
    icon_path: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ProgramItem":
        return cls(
            title=data.get("title", ""),
            command=data.get("command", ""),
            working_dir=data.get("working_dir", ""),
            icon_path=data.get("icon_path", ""),
        )

    def to_dict(self) -> dict:
        return asdict(self)
```

A `@dataclass` automatically generates `__init__`, `__eq__`, and `__repr__`
from the field definitions. The `from_dict` / `to_dict` methods handle JSON
serialization.

> **Official docs:** [dataclasses module](https://docs.python.org/3/library/dataclasses.html)

## What to test in a data model

When testing a data model, think about these questions:

1. **Construction** -- Can I create an instance with required and optional fields?
2. **Default values** -- Do optional fields get the right defaults?
3. **Serialization** -- Does `to_dict()` produce the expected dictionary?
4. **Deserialization** -- Does `from_dict()` reconstruct the object correctly?
5. **Missing/extra data** -- What happens with incomplete dictionaries?
6. **Roundtrip** -- Does `from_dict(obj.to_dict())` produce an equal object?

## Writing the tests

Here is the full test class from `tests/test_models.py`, annotated:

### Test 1: Basic construction

```python
def test_create_basic(self):
    item = ProgramItem(title="Test", command="echo hello")
    assert item.title == "Test"
    assert item.command == "echo hello"
    assert item.working_dir == ""   # default
    assert item.icon_path == ""     # default
```

This verifies that required fields are stored and optional fields get their
defaults. Simple but important -- if someone changes the default value, this
test catches it.

### Test 2: Full construction

```python
def test_create_full(self):
    item = ProgramItem(
        title="Editor",
        command="vim",
        working_dir="/tmp",
        icon_path="/usr/share/icons/vim.png",
    )
    assert item.working_dir == "/tmp"
    assert item.icon_path == "/usr/share/icons/vim.png"
```

Tests that optional fields work when provided.

### Test 3: Serialization

```python
def test_to_dict(self):
    item = ProgramItem(title="Test", command="echo")
    d = item.to_dict()
    assert d == {
        "title": "Test",
        "command": "echo",
        "working_dir": "",
        "icon_path": "",
    }
```

Checks the exact dictionary output. This matters because the dictionary is
what gets written to the JSON config file. If the keys or values change, saved
configs would break.

### Test 4: Deserialization

```python
def test_from_dict(self):
    d = {"title": "App", "command": "run", "working_dir": "/home", "icon_path": "icon.png"}
    item = ProgramItem.from_dict(d)
    assert item.title == "App"
    assert item.command == "run"
```

The reverse of `to_dict` -- given a dictionary (as loaded from JSON), can we
reconstruct the object?

### Test 5: Missing fields

```python
def test_from_dict_missing_fields(self):
    d = {"title": "Minimal"}
    item = ProgramItem.from_dict(d)
    assert item.title == "Minimal"
    assert item.command == ""
    assert item.working_dir == ""
```

This is a **defensive test**. Real-world config files may be hand-edited or
come from older versions that did not have all fields. The test verifies that
missing keys do not cause a crash -- they fall back to sensible defaults.

### Test 6: Roundtrip

```python
def test_roundtrip(self):
    original = ProgramItem(title="X", command="y", working_dir="z", icon_path="w")
    restored = ProgramItem.from_dict(original.to_dict())
    assert original == restored
```

This is the most important serialization test. It proves that no data is lost
when converting to a dictionary and back. The `==` comparison works because
`@dataclass` generates `__eq__` automatically.

## Testing nested models

`ProgramGroup` contains a list of `ProgramItem` objects. The same patterns
apply, but you also test the nesting:

```python
def test_from_dict(self):
    d = {
        "title": "Games",
        "items": [
            {"title": "Solitaire", "command": "sol.exe"},
            {"title": "Minesweeper", "command": "mine.exe"},
        ],
    }
    group = ProgramGroup.from_dict(d)
    assert group.title == "Games"
    assert len(group.items) == 2
```

The test verifies that the nested `items` list is deserialized into actual
`ProgramItem` objects, not left as raw dictionaries.

## Exercise

Try writing a test for this scenario: what happens if `from_dict` receives an
empty dictionary `{}`? What should `title` and `command` be? Write the test,
run it, and see if the behavior matches your expectation.

## Key takeaways

- Test construction with both required and optional fields.
- Test serialization by comparing against an expected dictionary.
- Test deserialization from both complete and incomplete data.
- Always write a roundtrip test for serializable models.
- `@dataclass` gives you `__eq__` for free, making assertions easy.

## Next

[Lab 3: Fixtures and Temporary Files](03_fixtures.md) -- learn how pytest
fixtures help you set up test data without repeating yourself.
