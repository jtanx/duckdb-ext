import argparse

from utils.descriptor import load_descriptors, save_descriptors


def delete_builds(descriptor_path: str, platform: str, duckdb_version: str) -> None:
    descriptors = load_descriptors(descriptor_path)
    changed = False
    for desc in descriptors:
        original_count = len(desc.builds)
        desc.builds = [
            build
            for build in desc.builds
            if not (
                build.platform == platform and build.duckdb_version == duckdb_version
            )
        ]
        removed = original_count - len(desc.builds)
        if removed > 0:
            changed = True
            print(
                f"Removed {removed} build(s) for {desc.repo.name}/{desc.extension.name} {platform} {duckdb_version}"
            )
    if changed:
        save_descriptors(descriptors, descriptor_path)
        print("Descriptor updated.")
    else:
        print("No matching builds found to delete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete builds matching specific platform and duckdb_version."
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

    args = parser.parse_args()
    delete_builds(args.descriptor, args.platform, args.duckdb_version)
