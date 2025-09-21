import argparse

from utils.descriptor import load_descriptor, save_descriptor


def delete_builds(descriptor_path: str, platform: str, duckdb_version: str) -> None:
    descriptor = load_descriptor(descriptor_path)
    changed = False
    for repo in descriptor.repos:
        for ext in repo.extensions:
            original_count = len(ext.builds)
            ext.builds = [
                build
                for build in ext.builds
                if not (
                    build.platform == platform
                    and build.duckdb_version == duckdb_version
                )
            ]
            removed = original_count - len(ext.builds)
            if removed > 0:
                changed = True
                print(
                    f"Removed {removed} build(s) for {repo.name}/{ext.name} {platform} {duckdb_version}"
                )
    if changed:
        save_descriptor(descriptor, descriptor_path)
        print("Descriptor updated.")
    else:
        print("No matching builds found to delete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete builds matching specific platform and duckdb_version."
    )
    parser.add_argument(
        "--descriptor", required=True, help="Path to the descriptor.yml file"
    )
    parser.add_argument("--platform", required=True, help="Platform to match")
    parser.add_argument(
        "--duckdb-version", required=True, help="DuckDB version to match"
    )

    args = parser.parse_args()
    delete_builds(args.descriptor, args.platform, args.duckdb_version)
