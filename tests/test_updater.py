"""Tests for the GitHub-based updater."""

import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from progman.utils.updater import (
    parse_version,
    is_newer_version,
    should_check_for_updates,
    get_latest_release,
    check_for_updates,
)
from progman.utils.config import get_default_github_config


class TestVersionParsing:
    def test_parse_simple(self):
        assert parse_version("1.0.0") == (1, 0, 0)

    def test_parse_with_v_prefix(self):
        assert parse_version("v2.1.3") == (2, 1, 3)

    def test_parse_two_parts(self):
        assert parse_version("1.0") == (1, 0)

    def test_parse_empty(self):
        assert parse_version("") is None

    def test_parse_none(self):
        assert parse_version(None) is None

    def test_parse_invalid(self):
        assert parse_version("abc") is None

    def test_parse_partial_invalid(self):
        assert parse_version("1.x.0") is None


class TestVersionComparison:
    def test_newer(self):
        assert is_newer_version("2.0.0", "1.0.0") is True

    def test_same(self):
        assert is_newer_version("1.0.0", "1.0.0") is False

    def test_older(self):
        assert is_newer_version("0.9.0", "1.0.0") is False

    def test_minor_newer(self):
        assert is_newer_version("1.1.0", "1.0.0") is True

    def test_patch_newer(self):
        assert is_newer_version("1.0.1", "1.0.0") is True

    def test_with_v_prefix(self):
        assert is_newer_version("v2.0.0", "v1.0.0") is True

    def test_invalid_remote(self):
        assert is_newer_version("invalid", "1.0.0") is False

    def test_invalid_local(self):
        assert is_newer_version("2.0.0", "invalid") is False


class TestShouldCheckForUpdates:
    def test_check_when_no_config(self):
        config = {}
        assert should_check_for_updates(config) is False

    def test_check_with_valid_config_no_previous_check(self):
        config = {"owner": "test", "repo": "test"}
        with patch("progman.utils.updater.get_last_version_check", return_value=None):
            assert should_check_for_updates(config) is True

    def test_skip_when_recent_check(self):
        config = {"owner": "test", "repo": "test"}
        recent = datetime.now() - timedelta(days=1)
        with patch("progman.utils.updater.get_last_version_check", return_value=recent):
            assert should_check_for_updates(config) is False

    def test_check_when_old_check(self):
        config = {"owner": "test", "repo": "test"}
        old = datetime.now() - timedelta(days=8)
        with patch("progman.utils.updater.get_last_version_check", return_value=old):
            assert should_check_for_updates(config) is True


class TestGetLatestRelease:
    def test_successful_fetch(self):
        config = {"owner": "test", "repo": "test"}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "tag_name": "v2.0.0",
            "zipball_url": "https://example.com/download.zip",
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("progman.utils.updater.urllib.request.urlopen", return_value=mock_response):
            result = get_latest_release(config)
            assert result is not None
            assert result["tag_name"] == "2.0.0"
            assert result["zipball_url"] == "https://example.com/download.zip"

    def test_empty_config(self):
        assert get_latest_release({}) is None

    def test_network_error(self):
        config = {"owner": "test", "repo": "test"}
        with patch("progman.utils.updater.urllib.request.urlopen", side_effect=Exception("timeout")):
            assert get_latest_release(config) is None


class TestCheckForUpdates:
    def test_no_update_when_throttled(self):
        config = {"owner": "test", "repo": "test"}
        recent = datetime.now() - timedelta(days=1)
        with patch("progman.utils.updater.get_last_version_check", return_value=recent):
            assert check_for_updates(config) is None

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
