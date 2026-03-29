---
description: "Use when cutting or pushing a Faceless release tag. Enforces script-based pre-clean and rebuild so GitHub release artifacts are always freshly generated."
applyTo: "**"
---

# Faceless Release Cut Instructions

Use this workflow whenever asked to create a release for Faceless.

## Required checks before release

1. Confirm `pyproject.toml` has the intended `[project].version`.
2. Confirm `CHANGELOG.md` has relevant entries under `## [Unreleased]`.
3. Always pre-clean and rebuild using release scripts before creating/pushing the tag:
   - `pwsh -NoProfile -File scripts/Invoke-Clean-Faceless-Build.ps1`
   - `pwsh -NoProfile -File scripts/Invoke-Build-Faceless-Wheels.ps1`
4. Do not cut a release tag from stale artifacts already present in `dist/` or `build/`.
5. Hard gate: if either script fails or is skipped, stop and do not create/push a release tag.

## Release process

1. Commit release-related changes to `main`.
2. Create and push a semantic version tag in `vX.Y.Z` form:
   - `git tag v0.1.0`
   - `git push origin v0.1.0`
3. The GitHub Actions `Release` workflow will:
   - build `dist/*.whl` and `dist/*.tar.gz`
   - create/update the GitHub Release for that tag
   - attach built artifacts to the release

## Manual release trigger

Use Actions -> `Release` -> `Run workflow` and provide:
- `tag` (required, must look like `v1.2.3`)
- `title` (optional)
- `prerelease` (optional)

## Version/tag consistency rule

Tag version and `pyproject.toml` version must match:
- tag `v1.2.3` -> version `1.2.3`
