"""Checks that personal OAuth tokens are sent as Bearer tokens.

From 2026-11-01 WakaTime API keys only work for plugins, so the stats request
must authenticate with a personal OAuth token instead.
"""

import importlib.util
import pathlib

SCRIPT = (
    pathlib.Path(__file__).resolve().parent.parent
    / "scripts"
    / "generate-wakatime-svg.py"
)

spec = importlib.util.spec_from_file_location("wakatime_svg", SCRIPT)
wakatime_svg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wakatime_svg)


def test_oauth_token_uses_bearer() -> None:
    headers = wakatime_svg.auth_headers(" waka_tok_example\n")
    assert headers == {"Authorization": "Bearer waka_tok_example"}, headers


def test_legacy_api_key_keeps_basic() -> None:
    headers = wakatime_svg.auth_headers("waka_00000000-0000-0000-0000-000000000000")
    assert headers == {
        "Authorization": "Basic waka_00000000-0000-0000-0000-000000000000"
    }, headers


if __name__ == "__main__":
    for name, case in sorted(globals().items()):
        if name.startswith("test_"):
            case()
            print(f"ok {name}")
