"""Check pinned dependencies of a requirements.txt against the PyPI JSON API."""
import sys
from typing import NamedTuple

import requests

PYPI = "https://pypi.org/pypi"


class Result(NamedTuple):
    name: str
    version: str
    status: str  # "ok" | "missing_package" | "missing_version"
    upload_time: str | None = None


def parse_requirements(text):
    """Return ([(name, version)], [warnings]). Only `name==version` lines count."""
    pins, warnings = [], []
    for line in text.splitlines():
        if not line or line.startswith("-"):
            continue
        name, sep, version = line.partition("==")
        version = version.strip()
        pins.append((name, version))
    return pins, warnings


def _get_json(session, url):
    """GET url; None on 404, raises on any other error."""
    response = session.get(url, timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def check_package(session, name, version):
    if _get_json(session, f"{PYPI}/{name}/json") is None:
        return Result(name, version, "missing_package")
    release = _get_json(session, f"{PYPI}/{name}/{version}/json")
    if release is None:
        return Result(name, version, "missing_version")
    urls = release["urls"]
    return Result(name, version, "ok", urls[0]["upload_time"] if urls else None)


def summarize(results):
    dated = [r for r in results if r.status == "ok" and r.upload_time]
    return {
        "checked": len(results),
        "missing_packages": sum(r.status == "missing_package" for r in results),
        "missing_versions": sum(r.status == "missing_version" for r in results),
        "oldest": min(dated, key=lambda r: r.upload_time, default=None),
    }


def format_report(summary):
    oldest = summary["oldest"]
    return "\n".join([
        f"Dependencies checked: {summary['checked']}",
        f"Packages not on PyPI: {summary['missing_packages']}",
        f"Version not on PyPI: {summary['missing_versions']}",
        "Oldest pinned release: "
        + (f"{oldest.name}=={oldest.version} ({oldest.upload_time[:4]})" if oldest else "none"),
    ])


def main(path):
    with open(path, encoding="utf-8") as f:
        pins, warnings = parse_requirements(f.read())
    for warning in warnings:
        print(warning, file=sys.stderr)
    try:
        with requests.Session() as session:
            results = [check_package(session, name, version) for name, version in pins]
    except requests.RequestException as e:
        sys.exit(f"ERROR: PyPI request failed: {e}")
    print(format_report(summarize(results)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python pypi_check.py <requirements.txt>")
    main(sys.argv[1])
