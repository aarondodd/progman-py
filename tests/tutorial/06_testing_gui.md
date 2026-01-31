# Lab 6: Testing GUI Code

Testing graphical user interfaces can seem intimidating, but the same
principles apply: create the object, interact with it, assert on its state.
The trick is running without a visible display.

## Headless testing with offscreen rendering

Qt applications normally need a display server (X11, Wayland, or the Windows
desktop). For automated tests, you run Qt in "offscreen" mode -- it processes
everything in memory without opening any windows.

In this project, `tests/conftest.py` sets this up before any Qt imports:

```python
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
```

This single line is what makes the entire test suite work in CI environments
and terminals without a display.

## The qapp fixture

Qt requires exactly one `QApplication` instance to exist before you can create
any widgets. The `conftest.py` fixture creates it once for the whole session:

```python
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
```

Any test that creates Qt widgets must request `qapp`:

```python
def test_create_with_empty_group(self, qapp):
    group = ProgramGroup(title="Empty")
    launcher = Launcher()
    window = GroupWindow(group, launcher)
    assert window.list_widget.count() == 0
```

The `qapp` parameter is required even if the test does not reference it
directly -- its presence ensures the `QApplication` exists.

> **Note:** The `pytest-qt` plugin provides its own `qapp` fixture. This
> project defines a custom one for full control, but either approach works.
> See [pytest-qt docs](https://pytest-qt.readthedocs.io/).

## Testing widget creation and state

Most GUI tests follow this pattern:

1. Create the widget.
2. Query its properties.
3. Assert they match expectations.

From `tests/test_widgets.py`:

```python
class TestGroupWindow:
    def test_create_with_items(self, qapp):
        group = ProgramGroup(
            title="Test",
            items=[
                ProgramItem(title="App1", command="app1"),
                ProgramItem(title="App2", command="app2"),
            ],
        )
        launcher = Launcher()
        window = GroupWindow(group, launcher)
        assert window.list_widget.count() == 2
```

No windows appear. The widget is created in memory, populated with items, and
the test checks that the list widget has the right number of entries.

## Testing state changes

You can modify the model and call methods, then check that the UI updated:

```python
def test_refresh_items(self, qapp):
    group = ProgramGroup(title="Test", items=[])
    launcher = Launcher()
    window = GroupWindow(group, launcher)
    assert window.list_widget.count() == 0

    group.items.append(ProgramItem(title="New", command="new"))
    window.refresh_items()
    assert window.list_widget.count() == 1
```

This test verifies the `refresh_items()` method: after adding an item to the
model and refreshing, the list widget should show one item.

## Testing data stored in widgets

Qt widgets can store arbitrary Python objects using "roles." This project
stores `ProgramItem` references in each list widget item's `UserRole`:

```python
def test_items_stored_in_user_role(self, qapp):
    item = ProgramItem(title="Stored", command="stored")
    group = ProgramGroup(title="Test", items=[item])
    launcher = Launcher()
    window = GroupWindow(group, launcher)

    from PyQt6.QtCore import Qt
    lw_item = window.list_widget.item(0)
    stored = lw_item.data(Qt.ItemDataRole.UserRole)
    assert stored is item
    assert stored.title == "Stored"
```

`stored is item` checks identity (same Python object), not just equality.
This matters because the app modifies items in-place.

## Testing widget configuration

You can verify that a widget was set up correctly:

```python
def test_drag_enabled(self, qapp):
    group = ProgramGroup(title="Test", items=[])
    launcher = Launcher()
    window = GroupWindow(group, launcher)
    assert window.list_widget.dragEnabled() is True
    assert window.list_widget.acceptDrops() is True
```

These tests act as guards: if someone accidentally disables drag-and-drop
during a refactor, this test catches it.

## Testing boolean flags and mode switching

```python
def test_dark_mode_flag(self, qapp):
    group = ProgramGroup(title="Test", items=[
        ProgramItem(title="App", command="app"),
    ])
    launcher = Launcher()
    window = GroupWindow(group, launcher, dark_mode=True)
    assert window._dark_mode is True

def test_set_dark_mode(self, qapp):
    group = ProgramGroup(title="Test", items=[])
    launcher = Launcher()
    window = GroupWindow(group, launcher, dark_mode=False)
    window.set_dark_mode(True)
    assert window._dark_mode is True
```

The first test checks the constructor parameter. The second tests runtime
state changes.

## Testing stylesheets (theme)

From `tests/test_theme.py`:

```python
def test_apply_dark_mode(self, qapp):
    ThemeManager.apply(qapp, dark_mode=True)
    stylesheet = qapp.styleSheet()
    assert "background-color: #1e1e1e" in stylesheet

def test_apply_light_mode(self, qapp):
    ThemeManager.apply(qapp, dark_mode=False)
    stylesheet = qapp.styleSheet()
    assert "background-color: #1e1e1e" not in stylesheet
```

After applying a theme, the test reads the stylesheet string and checks for
expected CSS properties. This is a lightweight way to verify theming without
rendering anything.

## What about clicking buttons and typing text?

For interactive testing (simulating clicks, keyboard input, dialog
interactions), `pytest-qt` provides tools like `qtbot`:

```python
def test_button_click(qtbot):
    button = QPushButton("Click me")
    qtbot.addWidget(button)
    with qtbot.waitSignal(button.clicked, timeout=1000):
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
```

This project focuses on state-based testing rather than interaction simulation,
but `pytest-qt` is there when you need it.

> **Official docs:** [pytest-qt](https://pytest-qt.readthedocs.io/en/latest/)

## Guidelines for GUI testing

1. **Test state, not appearance.** Check `widget.count()` or `widget.text()`,
   not pixel colors.
2. **Test the model, not just the view.** Verify the underlying data, not just
   what the widget displays.
3. **Keep tests fast.** Creating widgets in offscreen mode is quick. Avoid
   timers or sleeps.
4. **Mock dialogs.** If code shows a `QMessageBox`, mock it (see Lab 4) rather
   than trying to interact with it.
5. **One `QApplication` per session.** Qt enforces this -- use a session-scoped
   fixture.

## Exercise

Write a test that creates a `GroupWindow` with three items, then removes the
middle item from `group.items`, calls `refresh_items()`, and asserts that:
- The list widget count is 2.
- The remaining items have the correct titles.

## Key takeaways

- `QT_QPA_PLATFORM=offscreen` enables headless widget testing.
- A session-scoped `qapp` fixture ensures one `QApplication` exists.
- Test widget state (counts, text, data) rather than visual output.
- Mock dialogs and external interactions.
- GUI tests follow the same create-act-assert pattern as any other test.

## Next

[Lab 7: Putting It All Together](07_putting_it_together.md) -- test
organization, running your suite, and next steps.
