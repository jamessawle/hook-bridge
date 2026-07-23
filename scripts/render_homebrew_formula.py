#!/usr/bin/env python3
"""Renders Formula/hook-bridge-runner.rb pushed to jamessawle/homebrew-tap on release.

Reads the version hook-bridge-runner was just published at (from
packages/hook-bridge/pyproject.toml) and looks up its sdist url + sha256 from
PyPI's JSON API. The whole formula file is regenerated each release rather
than patched in place, so a change to this template (e.g. a python pin bump)
takes effect on the next release without hand-editing the tap.
"""

from __future__ import annotations

import json
import pathlib
import time
import tomllib
import urllib.error
import urllib.request

PACKAGE = "hook-bridge-runner"
PYPROJECT = pathlib.Path(__file__).parent.parent / "packages" / "hook-bridge" / "pyproject.toml"

FORMULA_TEMPLATE = """class HookBridgeRunner < Formula
  include Language::Python::Virtualenv

  desc "Runner that bridges a Harness's native hook events to hook-bridge Hooks"
  homepage "https://github.com/jamessawle/hook-bridge"
  url "{url}"
  sha256 "{sha256}"
  license "MIT"

  depends_on "python@3.14"
  depends_on "uv"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{{bin}}/hook-bridge-runner", "--help"
  end
end
"""


def current_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text())
    return data["project"]["version"]


def pypi_sdist(version: str, *, retries: int = 5, delay_seconds: float = 5.0) -> tuple[str, str]:
    url = f"https://pypi.org/pypi/{PACKAGE}/{version}/json"
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as exc:
            if exc.code != 404 or attempt == retries - 1:
                raise
            time.sleep(delay_seconds)  # PyPI indexing can lag just after publish
    for entry in data["urls"]:
        if entry["packagetype"] == "sdist":
            return entry["url"], entry["digests"]["sha256"]
    raise RuntimeError(f"no sdist found for {PACKAGE} {version}")


def main() -> None:
    version = current_version()
    url, sha256 = pypi_sdist(version)
    print(FORMULA_TEMPLATE.format(url=url, sha256=sha256), end="")


if __name__ == "__main__":
    main()
