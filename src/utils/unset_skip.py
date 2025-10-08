import argparse

from utils.descriptor import load_descriptors, save_descriptors


def unset_skip(descriptor_path: str, platform: str | None, duckdb_version: str) -> None:
    descriptors = load_descriptors(descriptor_path)
    changed = False
    for desc in descriptors:
        for build in desc.builds:
            if (
                (not platform or build.platform == platform)
                and build.duckdb_version == duckdb_version
                and build.skip
            ):
                build.skip = False
                changed = True
                print(
                    f"Unset skip for {desc.repo.name}/{desc.extension.name} {platform} {duckdb_version}"
                )
    if changed:
        save_descriptors(descriptors, descriptor_path)
        print("Descriptor updated.")
    else:
        print("No matching builds found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Unset skip for builds matching platform and duckdb_version."
    )
    parser.add_argument(
        "--descriptor",
        default="descriptors",
        help="Path to the descriptor directory",
    )
    parser.add_argument("--platform", required=False, help="Platform to match")
    parser.add_argument(
        "--duckdb-version", required=True, help="DuckDB version to match"
    )

    args = parser.parse_args()
    unset_skip(args.descriptor, args.platform, args.duckdb_version)
