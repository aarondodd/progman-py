# Lab 5: Testing with Files and Fixtures

This lab brings together fixtures, temporary files, and assertions to test
code that reads and writes files -- like a configuration system.

## The scenario

The `AppModel` class loads configuration from a JSON file, provides defaults
when no file exists, and migrates old config formats to new ones. This kind
of code has lots of edge cases worth testing:

- No config file exists (first run).
- Config file exists with valid data.
- Config file exists with old-format data (needs migration).
- Config file contains invalid JSON (corrupted).
- Save and reload preserves all data.

## Setting up test data with fixtures

Recall from Lab 3 that `conftest.py` defines these fixtures:

```python
@pytest.fixture
def tmp_config(tmp_path):
    return tmp_path / "test_progman.json"

@pytest.fixture
def sample_config(tmp_config):
    data = {
        "config_version": 1,
        "dark_mode": False,
        "groups": [{"title": "Main", "items": [...]}],
    }
    with open(tmp_config, "w") as f:
        json.dump(data, f)
    return tmp_config

@pytest.fixture
def old_format_config(tmp_config):
    data = {
        "theme": "classic",
        "groups": [{"title": "Main", "items": [...]}],
    }
    with open(tmp_config, "w") as f:
        json.dump(data, f)
    return tmp_config
```

Each fixture gives the test a different starting condition:

| Fixture | File state |
|---|---|
| `tmp_config` | Path exists, but file does not |
| `sample_config` | File exists with valid v1 data |
| `old_format_config` | File exists with old v0 data |

## Test: first run (no config file)

```python
def test_load_default_when_no_config(self, tmp_config):
    model = AppModel(config_path=tmp_config)
    assert model.config_version == 1
    assert model.dark_mode is False
    assert len(model.groups) >= 1
    assert model.groups[0].title == "Main"
    assert tmp_config.exists()
```

`tmp_config` is just a path -- the file does not exist yet. After `AppModel`
loads, it should create the file with default values. The last assertion
(`tmp_config.exists()`) verifies the file was actually written.

## Test: loading existing config

```python
def test_load_existing_config(self, sample_config):
    model = AppModel(config_path=sample_config)
    assert model.dark_mode is False
    assert len(model.groups) == 2
    assert model.groups[0].title == "Main"
    assert model.groups[1].title == "Development"
```

`sample_config` gives us a pre-written file. The test verifies that the data
was loaded correctly, not replaced with defaults.

## Test: save and reload (roundtrip)

```python
def test_save_and_reload(self, tmp_config):
    model = AppModel(config_path=tmp_config)
    model.dark_mode = True
    model.groups.append(ProgramGroup(title="New", items=[]))
    model.save()

    model2 = AppModel(config_path=tmp_config)
    assert model2.dark_mode is True
    assert len(model2.groups) == 2
    assert model2.groups[1].title == "New"
```

This is the file-based equivalent of the roundtrip test from Lab 2. It:

1. Creates a model (gets defaults).
2. Modifies it.
3. Saves to disk.
4. Loads a fresh model from the same file.
5. Verifies the modifications survived.

## Test: corrupted config

```python
def test_invalid_config_falls_back_to_default(self, tmp_config):
    with open(tmp_config, "w") as f:
        f.write("not json")
    model = AppModel(config_path=tmp_config)
    assert len(model.groups) >= 1
```

This writes garbage to the config file and verifies the app does not crash --
it falls back to defaults. Defensive tests like this are important for
user-facing applications where files can be hand-edited or corrupted.

## Testing config migration

The migration tests in `tests/test_config_migration.py` use the
`old_format_config` fixture:

```python
class TestConfigMigration:
    def test_v0_to_v1_theme_classic_becomes_dark(self, old_format_config):
        model = AppModel(config_path=old_format_config)
        assert model.dark_mode is True
        assert model.config_version == CONFIG_VERSION

    def test_v0_to_v1_preserves_groups(self, old_format_config):
        model = AppModel(config_path=old_format_config)
        assert len(model.groups) == 1
        assert model.groups[0].items[0].title == "Notepad"

    def test_v0_to_v1_saves_new_format(self, old_format_config):
        model = AppModel(config_path=old_format_config)
        with open(old_format_config) as f:
            saved = json.load(f)
        assert saved["config_version"] == CONFIG_VERSION
        assert "dark_mode" in saved
        assert "theme" not in saved
```

Each test checks one aspect of migration:

- **Theme conversion:** `"classic"` becomes `dark_mode: True`.
- **Data preservation:** Groups and items survive migration.
- **File update:** The migrated format is written back to disk (no `"theme"`
  key remains).

## Inline test data

Sometimes you need a fixture variation for just one test. Instead of creating a
new fixture, write the data directly in the test:

```python
def test_missing_config_version_triggers_migration(self, tmp_config):
    data = {
        "theme": "system",
        "groups": [{"title": "Test", "items": []}],
    }
    with open(tmp_config, "w") as f:
        json.dump(data, f)

    model = AppModel(config_path=tmp_config)
    assert model.config_version == CONFIG_VERSION
```

This test needed a slightly different config (no `config_version` field, with
`"theme": "system"`). Creating a fixture for a one-off case adds complexity
without benefit -- inline is clearer.

## Pattern: read back the file

After code writes a file, you can read it back to verify the contents:

```python
def test_v0_to_v1_saves_new_format(self, old_format_config):
    model = AppModel(config_path=old_format_config)

    with open(old_format_config) as f:
        saved = json.load(f)

    assert "dark_mode" in saved
    assert "theme" not in saved
```

This checks not just the in-memory model but the actual file on disk. It
catches bugs where the model is correct but the save logic is wrong.

## Exercise

Write a test that:

1. Creates a config with `dark_mode: False`.
2. Loads it into an `AppModel`.
3. Changes `dark_mode` to `True`.
4. Saves.
5. Reads the raw JSON from disk.
6. Asserts that `dark_mode` is `True` in the JSON.

This verifies the full cycle: load -> modify -> save -> verify on disk.

## Key takeaways

- Use `tmp_path` and fixture chaining to create isolated test files.
- Test the "no file" case, the "valid file" case, and the "broken file" case.
- Roundtrip tests (save then reload) catch serialization bugs.
- Migration tests verify both the in-memory state and the written file.
- Inline data is fine for one-off test scenarios.

## Next

[Lab 6: Testing GUI Code](06_testing_gui.md) -- test Qt widgets without
displaying any windows.
