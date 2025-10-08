import datetime as dt
from dataclasses import asdict
from pathlib import Path

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
    skip: bool = False
    rebuild_with: str | None = None


@dataclass
class Extension:
    name: str
    alias: str | None
    author: str
    license: str


@dataclass
class Repo:
    name: str
    url: str
    prefix: str


@dataclass
class Descriptor:
    repo: Repo
    extension: Extension
    builds: list[BuildInfo]


def get_extension_url(repo: Repo, ext: Extension, build: BuildInfo) -> str:
    return f"{repo.url}/v{build.duckdb_version}/{build.platform}/{ext.alias or ext.name}.duckdb_extension.gz"


def package_version(info: BuildInfo) -> str:
    base = info.duckdb_version
    suffix = (
        info.rebuild_with
        if info.rebuild_with is not None
        else dt.datetime.now(tz=dt.timezone.utc).strftime("%Y%m%d")
    )
    return f"{base}.{suffix}"


def load_descriptor(path: Path) -> Descriptor:
    with open(path) as fp:
        data = yaml.load(fp, Loader=yaml.CSafeLoader)
    return Descriptor(**data)  # type: ignore[missing-argument]


def save_descriptor(descriptor: Descriptor, path: str | Path) -> None:
    descriptor_path = (
        Path(path) / descriptor.repo.name / f"{descriptor.extension.name}.yml"
    )
    descriptor_path.parent.mkdir(parents=True, exist_ok=True)

    with open(descriptor_path, "w") as fp:
        yaml.dump(asdict(descriptor), fp, Dumper=yaml.CSafeDumper, sort_keys=False)


def load_descriptors(path: str | Path) -> list[Descriptor]:
    return [
        load_descriptor(ext_file) for ext_file in sorted(Path(path).glob("**/*.yml"))
    ]


def save_descriptors(descriptors: list[Descriptor], path: str | Path) -> None:
    for descriptor in descriptors:
        save_descriptor(descriptor, path)
