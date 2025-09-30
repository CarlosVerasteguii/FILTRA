"""Alias map loading and normalization helpers."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from filtra.errors import InputValidationError

DEFAULT_ALIAS_MAP_PATH = Path(__file__).resolve().parents[2] / "config" / "alias_map.yaml"


@dataclass(frozen=True)
class AliasMapDetails:
    """Summary details describing loaded alias maps."""

    sources: tuple[Path, ...]
    canonical_count: int
    alias_count: int
    locale_codes: tuple[str, ...]


@dataclass(frozen=True)
class AliasMap:
    """Provides canonicalization for extracted entities."""

    canonical_to_aliases: Mapping[str, tuple[str, ...]]
    alias_lookup: Mapping[str, str]
    locale_lookup: Mapping[str, Mapping[str, str]]
    sources: tuple[Path, ...]

    def canonicalize(
        self,
        text: str,
        *,
        language: str | None = None,
    ) -> tuple[str, tuple[str, ...]]:
        """Return the canonical representation for *text* and a transformation log."""

        log: list[str] = []
        trimmed = text.strip()
        if trimmed != text:
            log.append(f"Trimmed whitespace: '{text}' -> '{trimmed}'.")

        if not trimmed:
            log.append("Discarded empty entity after trimming.")
            return "", tuple(log)

        folded = trimmed.casefold()
        if folded != trimmed:
            log.append(f"Casefolded '{trimmed}' -> '{folded}'.")

        language_key = _normalize_language(language)
        for candidate in _language_candidates(language_key):
            overrides = self.locale_lookup.get(candidate)
            if overrides and folded in overrides:
                canonical = overrides[folded]
                log.append(
                    f"Applied locale override '{candidate}': '{trimmed}' -> '{canonical}'."
                )
                return canonical, tuple(log)

        canonical = self.alias_lookup.get(folded)
        if canonical:
            if canonical != trimmed:
                log.append(f"Mapped alias '{trimmed}' -> '{canonical}'.")
            else:
                log.append(f"Confirmed canonical form '{canonical}'.")
            return canonical, tuple(log)

        log.append(f"No alias mapping for '{trimmed}'; using canonical key '{trimmed}'.")
        return trimmed, tuple(log)

    def details(self) -> AliasMapDetails:
        """Summarise alias map coverage for diagnostics and logging."""

        locale_codes = tuple(sorted(self.locale_lookup.keys()))
        alias_total = sum(len(aliases) for aliases in self.canonical_to_aliases.values())
        return AliasMapDetails(
            sources=self.sources,
            canonical_count=len(self.canonical_to_aliases),
            alias_count=alias_total,
            locale_codes=locale_codes,
        )


def load_alias_map(extra_paths: Sequence[Path] | None = None) -> AliasMap:
    """Load and merge alias maps from *extra_paths* and the default location."""

    candidate_paths: list[Path] = [DEFAULT_ALIAS_MAP_PATH]
    if extra_paths:
        candidate_paths.extend(extra_paths)

    canonical_to_aliases: dict[str, set[str]] = {}
    alias_lookup: dict[str, str] = {}
    locale_lookup: dict[str, dict[str, str]] = {}
    resolved_sources: list[Path] = []
    canonical_registry: dict[str, tuple[str, Path]] = {}
    alias_registry: dict[str, tuple[str, Path]] = {}

    for path in candidate_paths:
        resolved = _resolve_path(path)
        payload = _load_yaml(resolved)
        _apply_aliases(
            payload.get("aliases"),
            canonical_to_aliases,
            alias_lookup,
            canonical_registry,
            alias_registry,
            resolved,
        )
        _apply_locale_overrides(
            payload.get("locale_overrides"),
            canonical_to_aliases,
            alias_lookup,
            locale_lookup,
            canonical_registry,
            alias_registry,
            resolved,
        )
        resolved_sources.append(resolved)

    snapshot = {key: tuple(sorted(values)) for key, values in canonical_to_aliases.items()}
    locale_snapshot = {code: dict(mapping) for code, mapping in locale_lookup.items()}

    return AliasMap(
        canonical_to_aliases=snapshot,
        alias_lookup=dict(alias_lookup),
        locale_lookup=locale_snapshot,
        sources=tuple(resolved_sources),
    )


def _resolve_path(path: Path) -> Path:
    candidate = path.expanduser()
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate

    if not resolved.exists() or not resolved.is_file():
        display = str(resolved)
        raise InputValidationError(
            message=f"Alias map file {display} does not exist or is not a file.",
            remediation="Verify the path or remove the --alias-map option.",
        )
    return resolved


def _load_yaml(path: Path) -> dict:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        display = str(path)
        raise InputValidationError(
            message=f"Unable to read alias map file {display}.",
            remediation="Check file permissions and retry.",
        ) from exc

    try:
        loaded = yaml.safe_load(raw_text) or {}
    except yaml.YAMLError as exc:
        display = str(path)
        raise InputValidationError(
            message=f"Alias map file {display} contains invalid YAML.",
            remediation="Ensure the file follows the documented schema.",
        ) from exc

    if not isinstance(loaded, dict):
        display = str(path)
        raise InputValidationError(
            message=f"Alias map file {display} must define a mapping at the root level.",
            remediation="Provide 'aliases' and optional 'locale_overrides' mappings.",
        )
    return loaded


def _apply_aliases(
    data: object,
    canonical_to_aliases: dict[str, set[str]],
    alias_lookup: dict[str, str],
    canonical_registry: dict[str, tuple[str, Path]],
    alias_registry: dict[str, tuple[str, Path]],
    source: Path,
) -> None:
    if data is None:
        return
    if not isinstance(data, Mapping):
        display = str(source)
        raise InputValidationError(
            message=f"Alias map file {display} must map canonical terms to alias lists.",
            remediation="Under 'aliases', provide {canonical: [alias, ...]} entries.",
        )

    for canonical_raw, aliases_raw in data.items():
        canonical = _normalize_canonical(canonical_raw, source)
        canonical_key = canonical.casefold()
        _register_canonical(canonical, canonical_registry, source)
        _register_alias(canonical_key, canonical, alias_registry, source, display=canonical)
        alias_lookup[canonical_key] = canonical
        bucket = canonical_to_aliases.setdefault(canonical, set())

        if aliases_raw is None:
            continue
        if not isinstance(aliases_raw, Sequence) or isinstance(aliases_raw, str | bytes):
            display = str(source)
            raise InputValidationError(
                message=f"Alias list for '{canonical}' in {display} must be a sequence.",
                remediation="Use a YAML list for aliases, e.g. ['foo', 'bar'].",
            )

        for alias_raw in aliases_raw:
            key, display_alias = _normalize_alias(alias_raw, source, canonical)
            _register_alias(key, canonical, alias_registry, source, display=display_alias)
            alias_lookup[key] = canonical
            bucket.add(display_alias)


def _apply_locale_overrides(
    data: object,
    canonical_to_aliases: dict[str, set[str]],
    alias_lookup: dict[str, str],
    locale_lookup: dict[str, dict[str, str]],
    canonical_registry: dict[str, tuple[str, Path]],
    alias_registry: dict[str, tuple[str, Path]],
    source: Path,
) -> None:
    if data is None:
        return
    if not isinstance(data, Mapping):
        display = str(source)
        raise InputValidationError(
            message=f"Locale overrides in {display} must map locale codes to alias maps.",
            remediation="Example: locale_overrides: { es: { alias: canonical } }.",
        )

    for locale_raw, mapping in data.items():
        locale = _normalize_locale(locale_raw, source)
        if not isinstance(mapping, Mapping):
            display = str(source)
            raise InputValidationError(
                message=f"Locale '{locale}' in {display} must map aliases to canonical terms.",
                remediation="Provide alias: canonical pairs under each locale.",
            )

        bucket = locale_lookup.setdefault(locale, {})
        for alias_raw, canonical_raw in mapping.items():
            canonical = _normalize_canonical(canonical_raw, source)
            canonical_key = canonical.casefold()
            _register_canonical(canonical, canonical_registry, source)
            _register_alias(canonical_key, canonical, alias_registry, source, display=canonical)
            key, display_alias = _normalize_alias(alias_raw, source, canonical)
            _register_alias(key, canonical, alias_registry, source, display=display_alias)
            bucket[key] = canonical
            canonical_lookup = canonical_to_aliases.setdefault(canonical, set())
            canonical_lookup.add(display_alias)
            alias_lookup[key] = canonical


def _register_canonical(
    canonical: str,
    registry: dict[str, tuple[str, Path]],
    source: Path,
) -> None:
    key = canonical.casefold()
    existing = registry.get(key)
    if existing and existing[0] != canonical:
        previous, previous_source = existing
        display_new = str(source)
        display_existing = str(previous_source)
        raise InputValidationError(
            message=(
                f"Canonical term '{canonical}' in {display_new} conflicts with '{previous}' "
                f"defined in {display_existing}."
            ),
            remediation=(
                "Align the canonical value with the existing entry or remove the duplicate."
            ),
        )
    registry[key] = (canonical, source)


def _register_alias(
    alias_key: str,
    canonical: str,
    registry: dict[str, tuple[str, Path]],
    source: Path,
    *,
    display: str | None = None,
) -> None:
    existing = registry.get(alias_key)
    if existing and existing[0] != canonical:
        previous, previous_source = existing
        display_new = str(source)
        display_existing = str(previous_source)
        label = display or alias_key
        raise InputValidationError(
            message=(
                f"Alias '{label}' in {display_new} maps to '{canonical}' but was previously "
                f"assigned to '{previous}' in {display_existing}."
            ),
            remediation=(
                "Update the alias to reference the same canonical term or remove the conflict."
            ),
        )
    registry[alias_key] = (canonical, source)


def _normalize_canonical(value: object, source: Path) -> str:
    if not isinstance(value, str):
        display = str(source)
        raise InputValidationError(
            message=f"Canonical names in {display} must be strings.",
            remediation="Ensure canonical keys and values are plain text strings.",
        )
    trimmed = value.strip()
    if not trimmed:
        display = str(source)
        raise InputValidationError(
            message=f"Canonical name in {display} cannot be empty.",
            remediation="Remove blank canonical entries.",
        )
    return trimmed


def _normalize_alias(value: object, source: Path, canonical: str) -> tuple[str, str]:
    if not isinstance(value, str):
        display = str(source)
        raise InputValidationError(
            message=f"Alias for '{canonical}' in {display} must be a string.",
            remediation="Ensure aliases are provided as strings.",
        )
    trimmed = value.strip()
    if not trimmed:
        display = str(source)
        raise InputValidationError(
            message=f"Alias for '{canonical}' in {display} cannot be empty.",
            remediation="Remove blank alias entries.",
        )
    return trimmed.casefold(), trimmed


def _normalize_locale(value: object, source: Path) -> str:
    if not isinstance(value, str):
        display = str(source)
        raise InputValidationError(
            message=f"Locale keys in {display} must be strings (e.g. 'es', 'en-US').",
            remediation="Update locale_overrides to use string locale keys.",
        )
    trimmed = value.strip().lower()
    if not trimmed:
        display = str(source)
        raise InputValidationError(
            message=f"Locale key in {display} cannot be empty.",
            remediation="Remove blank locale entries.",
        )
    return trimmed


def _normalize_language(language: str | None) -> str | None:
    if not language:
        return None
    return language.strip().lower() or None


def _language_candidates(language: str | None) -> tuple[str, ...]:
    if not language:
        return ()
    if "-" in language:
        base = language.split("-", 1)[0]
        return language, base
    return (language,)


__all__ = [
    "AliasMap",
    "AliasMapDetails",
    "DEFAULT_ALIAS_MAP_PATH",
    "load_alias_map",
]






