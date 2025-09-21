import argparse

from utils.descriptor import load_descriptor, save_descriptor


def set_rebuild_with(
    descriptor_path: str, platform: str, duckdb_version: str, rebuild_with: str
) -> None:
    descriptor = load_descriptor(descriptor_path)
    changed = False
    for repo in descriptor.repos:
        for ext in repo.extensions:
            for build in ext.builds:
                if (
                    build.platform == platform
                    and build.duckdb_version == duckdb_version
                ):
                    build.rebuild_with = rebuild_with
                    changed = True
                    print(
                        f"Set rebuild_with for {repo.name}/{ext.name} {platform} {duckdb_version} to {rebuild_with}"
                    )
    if changed:
        save_descriptor(descriptor, descriptor_path)
        print("Descriptor updated.")
    else:
        print("No matching builds found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Set rebuild_with for builds matching platform and duckdb_version."
    )
    parser.add_argument(
        "--descriptor", required=True, help="Path to the descriptor.yml file"
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
