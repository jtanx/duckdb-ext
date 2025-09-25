from pathlib import Path

import tomli
import tomli_w

from utils.descriptor import load_descriptors

DESCRIPTORS_ROOT = Path("descriptors")


def update_extras() -> None:
    descriptors = load_descriptors(DESCRIPTORS_ROOT)
    with open("pyproject.toml", "rb") as fp:
        pyproject = tomli.load(fp)

    changed = False
    extras = pyproject["project"].setdefault("optional-dependencies", {})
    for desc in descriptors:
        print(f"Processing descriptor {desc.repo.name}/{desc.extension.name}")
        ext_name = f"{desc.repo.prefix}{desc.extension.name}"
        pkg_name = f"duckdb-ext-{ext_name}"

        print(f"  Extension: {ext_name} -> {pkg_name}")
        changed = changed or (ext_name not in extras)
        extras[ext_name] = [pkg_name]

    if not changed:
        print("No changes to extras detected")
        return

    dev_extra = extras.pop("duckdb-ext-dev")
    extras = {"duckdb-ext-dev": dev_extra, **{k: v for k, v in sorted(extras.items())}}
    pyproject["project"]["optional-dependencies"] = extras

    print("Updating pyproject.toml with new extras")
    with open("pyproject.toml", "wb") as fp:
        tomli_w.dump(pyproject, fp)


if __name__ == "__main__":
    update_extras()
