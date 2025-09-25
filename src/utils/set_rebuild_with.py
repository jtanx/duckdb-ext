import argparse

from utils.descriptor import load_descriptors, save_descriptors


def set_rebuild_with(
    descriptor_path: str, platform: str, duckdb_version: str, rebuild_with: str
) -> None:
    descriptors = load_descriptors(descriptor_path)
    changed = False
    for desc in descriptors:
        for build in desc.builds:
            if build.platform == platform and build.duckdb_version == duckdb_version:
                build.rebuild_with = rebuild_with
                changed = True
                print(
                    f"Set rebuild_with for {desc.repo.name}/{desc.extension.name} {platform} {duckdb_version} to {rebuild_with}"
                )
    if changed:
        save_descriptors(descriptors, descriptor_path)
        print("Descriptor updated.")
    else:
        print("No matching builds found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Set rebuild_with for builds matching platform and duckdb_version."
    )
    parser.add_argument(
        "--descriptor",
        default="descriptors",
        help="Path to the descriptor directory",
    )
    parser.add_argument("--platform", required=True, help="Platform to match")
    parser.add_argument(
        "--duckdb-version", required=True, help="DuckDB version to match"
    )
    parser.add_argument(
        "--rebuild-with", required=True, help="Value to set for rebuild_with"
    )

    args = parser.parse_args()
    set_rebuild_with(
        args.descriptor, args.platform, args.duckdb_version, args.rebuild_with
    )
