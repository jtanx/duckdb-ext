import csv
import gzip
import hashlib
import io
import multiprocessing
import shutil
import subprocess
import urllib.error
import urllib.request
from functools import partial
from pathlib import Path

import tomli
import tomli_w

from utils.descriptor import (
    BuildInfo,
    BuildKey,
    Extension,
    Repo,
    get_extension_url,
    load_descriptor,
    package_version,
    save_descriptor,
)

PLATFORM_MAP = {
    "linux_amd64": "manylinux_2_17_x86_64",
    "linux_arm64": "manylinux_2_17_aarch64",
    "osx_amd64": "macosx_10_9_x86_64",
    "osx_arm64": "macosx_11_0_arm64",
    "windows_amd64": "win_amd64",
}


def fetch_duckdb_releases(min_version: str = "1.4.0") -> list[str]:
    releases = "https://duckdb.org/data/duckdb-releases.csv"
    with urllib.request.urlopen(releases) as response:
        data = response.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(data))
    versions = sorted(
        row["version_number"] for row in reader if row["version_number"] >= min_version
    )
    return versions


def check_needs_rebuild(repo: Repo, ext: Extension, build: BuildInfo) -> bool:
    if build.skip:
        print(f"    Skipping {ext.name} as marked")
        return False
    if build.etag is None:
        print(f"    No ETag for {ext.name}, needs rebuild")
        return True

    url = get_extension_url(repo, ext, build)
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("If-None-Match", build.etag)

    print(f"    Checking {ext.name} with {url} and ETag {build.etag}")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                new_etag = response.getheader("ETag")
                print(f"      ETag changed from {build.etag} to {new_etag}")
                return True
    except urllib.error.HTTPError as e:
        if e.code == 304:
            print("      Not modified (304)")
        else:
            print(f"      HTTP error: {e.code}")
    except Exception as e:
        print(f"      Error checking extension: {e}")
    return False


def rebuild(repo: Repo, ext: Extension, build: BuildInfo) -> Path | None:
    print(
        f"    Rebuilding {ext.name} for {build.platform} and DuckDB {build.duckdb_version}"
    )

    build_suffix = Path(f"v{build.duckdb_version}") / build.platform
    build_root = Path("build/ext_packages") / Path(repo.name) / ext.name / build_suffix
    extension_path = (
        build_root
        / "duckdb_ext"
        / "extensions"
        / build_suffix
        / f"{ext.name}.duckdb_extension"
    )
    extension_path.parent.mkdir(parents=True, exist_ok=True)
    url = get_extension_url(repo, ext, build)
    version = package_version(build)

    with urllib.request.urlopen(url) as response:
        if response.status != 200:
            raise RuntimeError(f"Failed to download extension: HTTP {response.status}")

        new_etag = response.getheader("ETag")
        reader = io.BufferedReader(response)
        sha256 = hashlib.sha256()
        with (
            gzip.GzipFile(fileobj=reader) as gz,
            open(extension_path, "wb") as out_file,
        ):
            chunk_size = 8192
            while True:
                chunk = gz.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                sha256.update(chunk)
        new_sha256 = sha256.hexdigest()

    print(f"      Downloaded and extracted to {extension_path}")
    print(f"      New ETag: {new_etag}, SHA256: {new_sha256}")
    build.etag = new_etag

    if build.sha256 == new_sha256:
        print("      SHA256 unchanged, not rebuilding")
        return None

    print(f"      Rebuilding package into {build_root}")
    shutil.copy("extension_template/MANIFEST.in", build_root / "MANIFEST.in")
    with open("extension_template/pyproject.toml", "rb") as fp:
        pyproject = tomli.load(fp)
    pyproject["project"]["name"] = f"duckdb-ext-{repo.prefix}{ext.name}"
    pyproject["project"]["version"] = version
    pyproject["project"]["dependencies"] = [f"duckdb=={build.duckdb_version}"]
    pyproject["project"]["description"] = (
        f"DuckDB extension package for {repo.name}/{ext.name}"
    )
    pyproject["project"]["authors"] = [
        {"name": ext.author},
        {"name": "Jeremy Tan", "email": "jtanx@outlook.com"},
    ]
    pyproject["project"]["license"] = ext.license

    with open(build_root / "pyproject.toml", "wb") as fp:
        tomli_w.dump(pyproject, fp)

    with (
        open("extension_template/README.md") as fpi,
        open(build_root / "README.md", "w") as fpo,
    ):
        readme = fpi.read().format(ext_name=f"{repo.prefix}{ext.name}")
        fpo.write(readme)

    print("      Building wheel")
    subprocess.run(["uv", "build", "--wheel", "."], cwd=build_root, check=True)

    platform_tag = PLATFORM_MAP[build.platform]
    wheel = (
        build_root
        / "dist"
        / f"duckdb_ext_{repo.prefix}{ext.name}-{version}-py3-none-any.whl"
    )
    fixed_wheel = (
        wheel.parent
        / f"duckdb_ext_{repo.prefix}{ext.name}-{version}-py3-none-{platform_tag}.whl"
    )
    print(f"      Fixing wheel platform tag to {platform_tag}")
    subprocess.run(["wheel", "tags", "--platform-tag", platform_tag, wheel], check=True)

    print(f"      Moving wheel to dist/ - {fixed_wheel.name}")
    dest_wheel = Path("dist") / fixed_wheel.name
    dest_wheel.parent.mkdir(parents=True, exist_ok=True)
    fixed_wheel.rename(dest_wheel)

    build.sha256 = new_sha256
    return fixed_wheel


def try_rebuild(
    repo: Repo, ext: Extension, build: BuildInfo
) -> tuple[Path | None, BuildInfo]:
    try:
        path = rebuild(repo, ext, build)
        return path, build
    except Exception as e:
        print(f"      Error rebuilding extension: {e}")
        build.skip = True
        return None, build


def process_repo(repo: Repo, duckdb_releases: list[str]) -> bool:
    print(f"Processing repo: {repo.name}")

    new_wheels: list[Path] = []
    for ext in repo.extensions:
        print(f"  Extension: {ext.name}")

        new_ext_wheels: list[Path] = []
        to_rebuild: list[BuildInfo] = []
        existing_builds = {
            BuildKey(b.platform, b.duckdb_version): b for b in ext.builds
        }

        for version in duckdb_releases:
            for platform in PLATFORM_MAP.keys():
                key = BuildKey(platform, version)
                entry = existing_builds.get(key)
                if entry is not None:
                    if check_needs_rebuild(repo, ext, entry):
                        print(f"    Needs rebuild for {platform} and DuckDB {version}")
                        to_rebuild.append(entry)
                    else:
                        print(f"    Up to date for {platform} and DuckDB {version}")
                else:
                    print(f"    Missing build for {platform} and DuckDB {version}")
                    entry = BuildInfo(
                        platform=platform,
                        duckdb_version=version,
                        etag=None,
                        sha256=None,
                    )
                    check_needs_rebuild(repo, ext, entry)  # always true for new
                    existing_builds[key] = entry
                    to_rebuild.append(entry)

        with multiprocessing.Pool(8) as pool:
            results = pool.map(partial(try_rebuild, repo, ext), to_rebuild)

        for wheel, build in results:
            if wheel:
                new_ext_wheels.append(wheel)
            key = BuildKey(build.platform, build.duckdb_version)
            existing_builds[key] = build

        if new_ext_wheels:
            ext.builds = sorted(
                existing_builds.values(), key=lambda b: (b.duckdb_version, b.platform)
            )
            new_wheels.extend(new_ext_wheels)

    if new_wheels:
        return True
    return False


def main():
    print("Fetching DuckDB releases and loading descriptor...")
    descriptor = load_descriptor("descriptor.yml")
    duckdb_releases = fetch_duckdb_releases()
    changed = False

    for repo in descriptor.repos:
        repo_changed = process_repo(repo, duckdb_releases)
        changed = changed or repo_changed

    if changed:
        print("Updating descriptor.yml with new build info")
        save_descriptor(descriptor, "descriptor.yml")


if __name__ == "__main__":
    main()
