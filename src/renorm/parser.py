"""
Renorm pattern Parser
"""

import re
import itertools

from .specs import NormSpec


class _Parser:  # pylint: disable=too-few-public-methods
    """Parse renorm raw pattern, build regex pattern and map capturing groups to specs"""

    def __init__(self, raw: str, /, *specs: NormSpec, **named_specs: NormSpec) -> None:
        self._raw_pattern = self._validate_raw_pattern(raw)
        self.specs = self._validate_specs(specs)
        self.named_specs = self._validate_named_specs(named_specs).copy()

        self.pattern, self.groupname_to_spec = self._parse()

    @staticmethod
    def _validate_raw_pattern(raw: str) -> str:

        if "(?P<" in raw:
            raise ValueError("Named groups '(?P<...>)' are not allowed in the input regex pattern")

        if "{}" in raw or "{@}" in raw:
            raise ValueError(
                f"Empty placeholders '{{}}' or '{{@}}' are not allowed: {raw}\n"
                "\tUse numbered placeholders '{@0}, {@1}, ...' for positional specs\n"
                "\tor named placeholders '{@a}, {@b}, ...' for named specs\n"
            )
        return raw

    @staticmethod
    def _validate_specs(specs: tuple[NormSpec, ...]) -> tuple[NormSpec, ...]:
        for i, s in enumerate(specs):
            if not isinstance(s, NormSpec):
                raise TypeError(f"positional spec @{i} must be a NormSpec, got {type(s)!r}")
        return specs

    @staticmethod
    def _validate_named_specs(named_specs: dict[str, NormSpec]) -> dict[str, NormSpec]:
        for k, s in named_specs.items():
            if not isinstance(s, NormSpec):
                raise TypeError(f"keyword spec @{k} must be a NormSpec, got {type(s)!r}")
        return named_specs

    def _map_specs_to_capture_groups(self, pattern: str) -> tuple[str, dict[str, NormSpec]]:
        """Tag regex pattern numbered placeholders with named groups (only capturing groups)."""

        counter = itertools.count()
        groupname_to_spec: dict[str, NormSpec] = {}

        def repl(m: re.Match[str]) -> str:
            group = m.group(1)
            key = group[1:]  # example: '@1'->1, '@name'->'name'
            if key.isdigit():
                idx = int(key)
                try:
                    spec = self.specs[int(key)]
                except IndexError as err:
                    raise IndexError(
                        f"Replacement index @{idx} out of range for positional specs tuple"
                    ) from err
            else:
                try:
                    spec = self.named_specs[key]
                except KeyError as err:
                    raise KeyError(f"@{key}") from err

            groupname = f"_spec_{next(counter)}"  # _spec_0, _spec_1
            groupname_to_spec[groupname] = spec
            return f"(?P<{groupname}>{{{group}}})"

        new_pattern = re.sub(r"\(\{(@[A-Za-z_]\w*|@\d+)\}\)", repl, pattern)
        return new_pattern, groupname_to_spec

    def _replace_index_placeholder(self, pattern: str) -> str:

        def repl(m: re.Match[str]) -> str:
            idx = int(m.group(1))
            try:
                spec = self.specs[idx]
            except IndexError as err:
                raise IndexError(
                    f"Replacement index @{idx} out of range for positional specs tuple"
                ) from err
            return f"{spec}"

        return re.sub(r"\{@(\d+)\}", repl, pattern)

    def _replace_named_placeholder(self, pattern: str) -> str:

        def repl(m: re.Match[str]) -> str:
            key = m.group(1)
            try:
                spec = self.named_specs[key]
            except KeyError as err:
                raise KeyError(f"@{key}") from err
            return f"{spec}"

        return re.sub(r"\{@([A-Za-z_]\w*)\}", repl, pattern)

    def _parse(self) -> tuple[str, dict[str, NormSpec]]:
        """
        Build a regex pattern fully tagged with named capture groups that map
        one-to-one to specs and named_specs
        """
        pattern, groupname_to_spec = self._map_specs_to_capture_groups(self._raw_pattern)
        pattern = self._replace_index_placeholder(pattern)
        pattern = self._replace_named_placeholder(pattern)
        return pattern, groupname_to_spec
