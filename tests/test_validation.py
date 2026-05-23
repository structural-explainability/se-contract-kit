"""Tests for se_contract_kit.validation."""

from pathlib import Path

import pytest

from se_contract_kit.base.errors import ContractKitError
from se_contract_kit.declarations.config import RepoConfig
from se_contract_kit.declarations.contracts import (
    ContractConfigDeclaration,
    ContractConsumesDeclaration,
    ContractProvidesDeclaration,
)
from se_contract_kit.declarations.manifests import (
    DependencyDeclaration,
    LayerDeclaration,
    ManifestDeclaration,
    ProvidesDeclaration,
    RepoDeclaration,
)
from se_contract_kit.resolution.artifacts import ArtifactResolutionSet, ResolvedArtifact
from se_contract_kit.resolution.context import ResolutionContext
from se_contract_kit.resolution.dependencies import DependencySet
from se_contract_kit.validation.registry import Check, CheckRegistry
from se_contract_kit.validation.results import (
    CheckSeverity,
    CheckStatus,
    cannot_verify,
    failure,
    ok,
    partial,
    warning,
    worst_status,
)
from se_contract_kit.validation.runner import run_checks


def _context(tmp_path: Path) -> ResolutionContext:
    manifest = ManifestDeclaration(
        path=tmp_path / "MANIFEST.toml",
        schema="se-manifest-schema",
        schema_url="https://example.com/manifest-schema.toml",
        repo=RepoDeclaration(
            name="se-contract-kit",
            org="structural-explainability",
            repo_class="engine",
            kind="contract-kit",
            status="active",
            since="2026",
            summary="Generic contract machinery.",
        ),
        layer=LayerDeclaration(
            space="application",
            role="contract-engine",
        ),
        depends=DependencyDeclaration(
            required=(),
            optional=(),
        ),
        provides=ProvidesDeclaration(
            artifacts=("contract-loading-engine",),
        ),
        contract=None,
    )

    config = RepoConfig(
        repo_root=tmp_path,
        manifest=manifest,
        contract_config=ContractConfigDeclaration(
            path=tmp_path / "contract.toml",
            provides=ContractProvidesDeclaration(artifacts=()),
            consumes=ContractConsumesDeclaration(contracts=()),
        ),
    )

    return ResolutionContext(
        repo_root=tmp_path,
        config=config,
        dependencies=DependencySet(required=(), optional=()),
        artifacts=ArtifactResolutionSet(
            provided=(
                ResolvedArtifact(
                    artifact_id="contract-loading-engine",
                    kind="source",
                    path=tmp_path / "src" / "file.py",
                    source_repo="se-contract-kit",
                    authority_repo="se-contract-kit",
                    is_local=True,
                ),
            ),
            consumed=(),
        ),
    )


def _pass_check(context: ResolutionContext):
    _ = context
    return (ok("pass-check", "passed"),)


def _fail_check(context: ResolutionContext):
    _ = context
    return (failure("fail-check", "failed"),)


def _warn_check(context: ResolutionContext):
    _ = context
    return (warning("warn-check", "warned"),)


def _partial_check(context: ResolutionContext):
    _ = context
    return (partial("partial-check", "partial"),)


def _strict_check(context: ResolutionContext):
    _ = context
    return (warning("strict-check", "strict warning"),)


def _cannot_verify_check(context: ResolutionContext):
    _ = context
    return (cannot_verify("cannot-verify-check", "cannot verify"),)


def _crash_check(context: ResolutionContext):
    _ = context
    raise ContractKitError("boom")


PASS_CHECK = Check(
    check_id="pass-check",
    title="Pass check",
    run=_pass_check,
)

FAIL_CHECK = Check(
    check_id="fail-check",
    title="Fail check",
    run=_fail_check,
)

WARN_CHECK = Check(
    check_id="warn-check",
    title="Warn check",
    run=_warn_check,
)

PARTIAL_CHECK = Check(
    check_id="partial-check",
    title="Partial check",
    run=_partial_check,
)

CANNOT_VERIFY_CHECK = Check(
    check_id="cannot-verify-check",
    title="Cannot verify check",
    run=_cannot_verify_check,
)

CRASH_CHECK = Check(
    check_id="crash-check",
    title="Crash check",
    run=_crash_check,
)

STRICT_CHECK = Check(
    check_id="strict-check",
    title="Strict check",
    run=_strict_check,
    strict_only=True,
)


def test_check_result_helpers() -> None:
    assert ok("x").status is CheckStatus.PASS
    assert failure("x", "bad").status is CheckStatus.FAIL
    assert warning("x", "warn").severity is CheckSeverity.WARNING
    assert partial("x", "partial").status is CheckStatus.PARTIAL
    assert cannot_verify("x", "nope").status is CheckStatus.CANNOT_VERIFY


def test_check_result_failure_detection() -> None:
    assert ok("x").is_failure is False
    assert partial("x", "partial").is_failure is False
    assert failure("x", "bad").is_failure is True
    assert cannot_verify("x", "nope").is_failure is True


def test_worst_status() -> None:
    assert worst_status(()) is CheckStatus.PASS
    assert worst_status((ok("a"), partial("b", "partial"))) is CheckStatus.PARTIAL
    assert worst_status((ok("a"), failure("b", "bad"))) is CheckStatus.FAIL
    assert (
        worst_status((failure("a", "bad"), cannot_verify("b", "nope")))
        is CheckStatus.CANNOT_VERIFY
    )


def test_registry_preserves_order() -> None:
    registry = CheckRegistry().extend(PASS_CHECK, FAIL_CHECK)

    assert registry.ids() == ("pass-check", "fail-check")


def test_registry_rejects_duplicate_check_ids() -> None:
    with pytest.raises(ValueError, match="duplicate check ids"):
        CheckRegistry(checks=(PASS_CHECK, PASS_CHECK))


def test_registry_extend_returns_new_registry() -> None:
    original = CheckRegistry(checks=(PASS_CHECK,))
    extended = original.extend(FAIL_CHECK)

    assert original.ids() == ("pass-check",)
    assert extended.ids() == ("pass-check", "fail-check")


def test_registry_extended_with_multiple_checks() -> None:
    registry = CheckRegistry().extended_with((PASS_CHECK, WARN_CHECK, PARTIAL_CHECK))

    assert registry.ids() == ("pass-check", "warn-check", "partial-check")


def test_registry_select_skips_strict_only_when_not_strict() -> None:
    registry = CheckRegistry(checks=(PASS_CHECK, STRICT_CHECK))

    assert tuple(check.check_id for check in registry.select(strict=False)) == (
        "pass-check",
    )
    assert tuple(check.check_id for check in registry.select(strict=True)) == (
        "pass-check",
        "strict-check",
    )


def test_runner_runs_checks_in_order(tmp_path: Path) -> None:
    registry = CheckRegistry().extend(PASS_CHECK, WARN_CHECK, PARTIAL_CHECK)

    report = run_checks(
        context=_context(tmp_path),
        registry=registry,
        strict=True,
    )

    assert tuple(result.check_id for result in report.results) == (
        "pass-check",
        "warn-check",
        "partial-check",
    )


def test_runner_reports_failed_check(tmp_path: Path) -> None:
    registry = CheckRegistry().extend(PASS_CHECK, FAIL_CHECK)

    report = run_checks(
        context=_context(tmp_path),
        registry=registry,
        strict=True,
    )

    assert tuple(result.check_id for result in report.results) == (
        "pass-check",
        "fail-check",
    )
    assert any(result.is_failure for result in report.results)


def test_runner_reports_cannot_verify_check(tmp_path: Path) -> None:
    registry = CheckRegistry().extend(PASS_CHECK, CANNOT_VERIFY_CHECK)

    report = run_checks(
        context=_context(tmp_path),
        registry=registry,
        strict=True,
    )

    assert tuple(result.check_id for result in report.results) == (
        "pass-check",
        "cannot-verify-check",
    )
    assert report.results[1].status is CheckStatus.CANNOT_VERIFY


def test_runner_converts_exception_to_cannot_verify_result(tmp_path: Path) -> None:
    registry = CheckRegistry().extend(PASS_CHECK, CRASH_CHECK)

    report = run_checks(
        context=_context(tmp_path),
        registry=registry,
        strict=True,
    )

    assert len(report.results) == 2

    crashed = report.results[1]
    assert crashed.check_id == "crash-check"
    assert crashed.status is CheckStatus.CANNOT_VERIFY
    assert crashed.severity is CheckSeverity.ERROR
    assert "boom" in crashed.message


def test_runner_skips_strict_only_check_when_not_strict(tmp_path: Path) -> None:
    registry = CheckRegistry().extend(PASS_CHECK, STRICT_CHECK)

    report = run_checks(
        context=_context(tmp_path),
        registry=registry,
        strict=False,
    )

    assert tuple(result.check_id for result in report.results) == ("pass-check",)


def test_runner_runs_strict_only_check_when_strict(tmp_path: Path) -> None:
    registry = CheckRegistry().extend(PASS_CHECK, STRICT_CHECK)

    report = run_checks(
        context=_context(tmp_path),
        registry=registry,
        strict=True,
    )

    assert tuple(result.check_id for result in report.results) == (
        "pass-check",
        "strict-check",
    )
