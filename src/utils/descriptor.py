import datetime as dt
from dataclasses import asdict

import yaml
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class BuildKey:
    platform: str
    duckdb_version: str


@dataclass
class BuildInfo:
    platform: str
    duckdb_version: str
    etag: str | None
    sha256: str | None


@dataclass
class Extension:
    name: str
    author: str
    license: str
    builds: list[BuildInfo]


@dataclass
class Repo:
    name: str
    url: str
    prefix: str
    extensions: list[Extension]


@dataclass
class Descriptor:
    repos: list[Repo]


def get_extension_url(repo: Repo, ext: Extension, build: BuildInfo) -> str:
    return f"{repo.url}/v{build.duckdb_version}/{build.platform}/{ext.name}.duckdb_extension.gz"


def package_version(info: BuildInfo) -> str:
    base = info.duckdb_version
    today = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%d")
    return f"{base}.{today}"


def load_descriptor(path: str) -> Descriptor:
    with open(path) as f:
        data = yaml.safe_load(f)
    return Descriptor(**data)  # type: ignore[missing-argument]


def save_descriptor(descriptor: Descriptor, path: str) -> None:
    with open(path, "w") as fp:
        yaml.safe_dump(asdict(descriptor), fp, sort_keys=False)
