"""Tests for theme management."""

from PyQt6.QtWidgets import QApplication

from progman.utils.theme import ThemeManager


class TestThemeManager:
    def test_apply_light_mode(self, qapp):
        ThemeManager.apply(qapp, dark_mode=False)
        stylesheet = qapp.styleSheet()
        assert f"background-color: {ThemeManager.LIGHT_BG_PRIMARY}" in stylesheet
        assert f"background-color: {ThemeManager.DARK_BG_PRIMARY}" not in stylesheet

    def test_apply_dark_mode(self, qapp):
        ThemeManager.apply(qapp, dark_mode=True)
        stylesheet = qapp.styleSheet()
        assert f"background-color: {ThemeManager.DARK_BG_PRIMARY}" in stylesheet

    def test_switch_themes(self, qapp):
        ThemeManager.apply(qapp, dark_mode=True)
        assert f"background-color: {ThemeManager.DARK_BG_PRIMARY}" in qapp.styleSheet()

        ThemeManager.apply(qapp, dark_mode=False)
        assert f"background-color: {ThemeManager.LIGHT_BG_PRIMARY}" in qapp.styleSheet()
        assert f"background-color: {ThemeManager.DARK_BG_PRIMARY}" not in qapp.styleSheet()

    def test_dark_stylesheet_has_required_widgets(self):
        for widget in ["QMainWindow", "QMenuBar", "QMenu", "QMdiArea",
                       "QListWidget", "QLineEdit", "QPushButton", "QStatusBar"]:
            assert widget in ThemeManager.DARK_STYLESHEET

    def test_light_stylesheet_has_required_widgets(self):
        for widget in ["QMainWindow", "QMenuBar", "QMenu", "QMdiArea",
                       "QListWidget", "QLineEdit", "QPushButton", "QStatusBar"]:
            assert widget in ThemeManager.LIGHT_STYLESHEET

    def test_color_constants_defined(self):
        # Verify key color constants exist
        assert ThemeManager.DARK_BG_PRIMARY == "#1e1e1e"
        assert ThemeManager.LIGHT_BG_PRIMARY == "#ffffff"
        assert ThemeManager.DARK_ACCENT == "#0078d4"
        assert ThemeManager.LIGHT_ACCENT == "#0078d4"
