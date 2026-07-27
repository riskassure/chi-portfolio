# backend/src/services/math/local_macro_helper.py

from __future__ import annotations

from dataclasses import dataclass, field
import re


DOCUMENT_BEGIN = r"\begin{document}"
DOCUMENT_END = r"\end{document}"

MACRO_NAME_RE = re.compile(
    r"\\[A-Za-z@]+$"
)

COMMAND_TOKEN_RE = re.compile(
    r"\\[A-Za-z@]+"
)

DEFINITION_COMMAND_RE = re.compile(
    r"\\(?:"
    r"newcommand|"
    r"renewcommand|"
    r"providecommand|"
    r"DeclareMathOperator|"
    r"def|"
    r"let"
    r")\*?"
)


@dataclass(frozen=True)
class LocalMacroDefinition:
    """
    One concept-local macro definition supported by the frontend parser.
    """

    name: str
    token: str
    argument_count: int
    replacement: str
    source_text: str
    start: int
    end: int


@dataclass(frozen=True)
class UnsupportedLocalMacro:
    """
    A definition-like construct that was deliberately not harvested.
    """

    command: str
    reason: str
    source_text: str
    start: int
    end: int


@dataclass
class LocalMacroHarvestResult:
    """
    Complete read-only result of inspecting one original PlanetMath source.
    """

    definitions: list[LocalMacroDefinition] = field(
        default_factory=list
    )

    unsupported: list[UnsupportedLocalMacro] = field(
        default_factory=list
    )

    document_body: str = ""
    prelude_tex: str = ""

    @property
    def cleaned_tex_preview(self) -> str:
        """
        Show cleaned_tex with every supported harvested definition.

        This is useful for diagnostics, but Step 1 should normally use
        used_cleaned_tex_preview instead.
        """

        parts = [
            part
            for part in (
                self.prelude_tex.strip(),
                self.document_body.strip(),
            )
            if part
        ]

        return "\n\n".join(parts)

    @property
    def used_definitions(
        self,
    ) -> list[LocalMacroDefinition]:
        """
        Return definitions actually referenced by the document body,
        including transitive dependencies between local definitions.
        """

        return select_used_local_definitions(
            self.definitions,
            self.document_body,
        )

    @property
    def used_prelude_tex(self) -> str:
        """
        Build a prelude containing only definitions needed by the body.
        """

        return "\n".join(
            definition.source_text
            for definition in self.used_definitions
        )

    @property
    def used_cleaned_tex_preview(self) -> str:
        """
        Show the cleaned_tex value Step 1 should produce.

        Only definitions referenced by the document body are prepended.
        """

        parts = [
            part
            for part in (
                self.used_prelude_tex.strip(),
                self.document_body.strip(),
            )
            if part
        ]

        return "\n\n".join(parts)


def extract_document_body(
    raw_content: str,
) -> str:
    """
    Extract the contents of the first LaTeX document body.

    This mirrors the current Step 1 intent without using a greedy regex.
    """

    text = raw_content or ""

    start = text.find(DOCUMENT_BEGIN)

    if start == -1:
        return ""

    start += len(DOCUMENT_BEGIN)

    end = text.rfind(DOCUMENT_END)

    if end == -1 or end < start:
        end = len(text)

    return text[start:end].strip()


def extract_local_newcommands(
    raw_content: str,
) -> LocalMacroHarvestResult:
    """
    Harvest the concept-local ``\\newcommand`` subset currently supported
    by frontend/math/math_local_macros.js.

    Supported forms:

        \\newcommand{\\name}{replacement}
        \\newcommand{\\name}[1]{replacement}
        \\newcommand{\\name}[2]{replacement}
        \\newcommand\\name{replacement}
        \\newcommand*{\\name}{replacement}

    Argument counts from 0 through 9 are accepted.

    Deliberately unsupported:

        \\newcommand{\\name}[2][default]{replacement}
        \\renewcommand
        \\providecommand
        \\DeclareMathOperator
        \\def
        \\let

    Unsupported or malformed definitions are reported instead of guessed.
    Only the preamble before ``\\begin{document}`` is inspected.
    """

    text = raw_content or ""

    document_start = text.find(DOCUMENT_BEGIN)

    preamble = (
        text[:document_start]
        if document_start != -1
        else text
    )

    result = LocalMacroHarvestResult(
        document_body=extract_document_body(text)
    )

    definitions_by_name: dict[
        str,
        LocalMacroDefinition,
    ] = {}

    cursor = 0

    while True:
        match = DEFINITION_COMMAND_RE.search(
            preamble,
            cursor,
        )

        if not match:
            break

        start = match.start()
        command = match.group(0)
        cursor = match.end()

        # Ignore definitions that appear inside TeX comments.
        if _is_inside_tex_comment(
            preamble,
            start,
        ):
            continue

        base_command = (
            command[:-1]
            if command.endswith("*")
            else command
        )

        if base_command != r"\newcommand":
            result.unsupported.append(
                UnsupportedLocalMacro(
                    command=command,
                    reason=(
                        "Definition command is not supported "
                        "by local-macro V1."
                    ),
                    source_text=_make_preview(
                        preamble,
                        start,
                    ),
                    start=start,
                    end=cursor,
                )
            )

            continue

        parsed_name = _read_macro_name(
            preamble,
            cursor,
        )

        if parsed_name is None:
            result.unsupported.append(
                UnsupportedLocalMacro(
                    command=command,
                    reason=(
                        "Malformed or unsupported macro name."
                    ),
                    source_text=_make_preview(
                        preamble,
                        start,
                    ),
                    start=start,
                    end=cursor,
                )
            )

            continue

        token, definition_cursor = parsed_name

        (
            argument_count_text,
            after_argument_count,
            optional_error,
        ) = _read_optional_group(
            preamble,
            definition_cursor,
        )

        if optional_error:
            result.unsupported.append(
                UnsupportedLocalMacro(
                    command=command,
                    reason=optional_error,
                    source_text=_make_preview(
                        preamble,
                        start,
                    ),
                    start=start,
                    end=after_argument_count,
                )
            )

            cursor = after_argument_count
            continue

        argument_count = 0

        if argument_count_text is not None:
            clean_count = argument_count_text.strip()

            if not re.fullmatch(
                r"[0-9]",
                clean_count,
            ):
                result.unsupported.append(
                    UnsupportedLocalMacro(
                        command=command,
                        reason=(
                            "Argument count must be one digit "
                            "from 0 through 9."
                        ),
                        source_text=_make_preview(
                            preamble,
                            start,
                        ),
                        start=start,
                        end=after_argument_count,
                    )
                )

                cursor = after_argument_count
                continue

            argument_count = int(clean_count)
            definition_cursor = after_argument_count

            (
                default_argument,
                after_default_argument,
                default_error,
            ) = _read_optional_group(
                preamble,
                definition_cursor,
            )

            if default_error:
                result.unsupported.append(
                    UnsupportedLocalMacro(
                        command=command,
                        reason=default_error,
                        source_text=_make_preview(
                            preamble,
                            start,
                        ),
                        start=start,
                        end=after_default_argument,
                    )
                )

                cursor = after_default_argument
                continue

            if default_argument is not None:
                unsupported_end = (
                    _find_definition_end_after_default(
                        preamble,
                        after_default_argument,
                    )
                )

                result.unsupported.append(
                    UnsupportedLocalMacro(
                        command=command,
                        reason=(
                            "Optional default arguments are "
                            "not supported."
                        ),
                        source_text=_make_preview(
                            preamble,
                            start,
                            unsupported_end,
                        ),
                        start=start,
                        end=unsupported_end,
                    )
                )

                cursor = unsupported_end
                continue

        definition_cursor = (
            _skip_whitespace_and_comments(
                preamble,
                definition_cursor,
            )
        )

        if (
            definition_cursor >= len(preamble)
            or preamble[definition_cursor] != "{"
        ):
            result.unsupported.append(
                UnsupportedLocalMacro(
                    command=command,
                    reason="Missing replacement group.",
                    source_text=_make_preview(
                        preamble,
                        start,
                    ),
                    start=start,
                    end=definition_cursor,
                )
            )

            continue

        replacement_close = (
            _find_matching_delimiter(
                preamble,
                definition_cursor,
                "{",
                "}",
            )
        )

        if replacement_close == -1:
            result.unsupported.append(
                UnsupportedLocalMacro(
                    command=command,
                    reason="Unterminated replacement group.",
                    source_text=_make_preview(
                        preamble,
                        start,
                        len(preamble),
                    ),
                    start=start,
                    end=len(preamble),
                )
            )

            break

        replacement = preamble[
            definition_cursor + 1:
            replacement_close
        ]

        source_text = preamble[
            start:
            replacement_close + 1
        ].strip()

        parameter_error = (
            _validate_parameter_markers(
                replacement,
                argument_count,
            )
        )

        if parameter_error:
            result.unsupported.append(
                UnsupportedLocalMacro(
                    command=command,
                    reason=parameter_error,
                    source_text=source_text,
                    start=start,
                    end=replacement_close + 1,
                )
            )

            cursor = replacement_close + 1
            continue

        name = token[1:]

        existing = definitions_by_name.get(name)

        if existing is not None:
            same_definition = (
                existing.argument_count
                == argument_count
                and existing.replacement
                == replacement
            )

            reason = (
                "Duplicate local macro definition."
                if same_definition
                else "Conflicting local macro definition."
            )

            result.unsupported.append(
                UnsupportedLocalMacro(
                    command=command,
                    reason=reason,
                    source_text=source_text,
                    start=start,
                    end=replacement_close + 1,
                )
            )

            cursor = replacement_close + 1
            continue

        definition = LocalMacroDefinition(
            name=name,
            token=token,
            argument_count=argument_count,
            replacement=replacement,
            source_text=source_text,
            start=start,
            end=replacement_close + 1,
        )

        result.definitions.append(definition)
        definitions_by_name[name] = definition

        cursor = replacement_close + 1

    result.prelude_tex = "\n".join(
        definition.source_text
        for definition in result.definitions
    )

    return result


def select_used_local_definitions(
    definitions: list[LocalMacroDefinition],
    document_body: str,
) -> list[LocalMacroDefinition]:
    r"""
    Select definitions referenced by the document body.

    Dependencies between local definitions are included transitively.

    Example:

        \newcommand{\foo}{\bar}
        \newcommand{\bar}{...}

    When the body uses \foo, both \foo and \bar are retained.

    The original preamble order is preserved.
    """

    definitions_by_token = {
        definition.token: definition
        for definition in definitions
    }

    required_tokens = {
        token
        for token in COMMAND_TOKEN_RE.findall(
            document_body or ""
        )
        if token in definitions_by_token
    }

    changed = True

    while changed:
        changed = False

        for token in tuple(required_tokens):
            definition = definitions_by_token[token]

            dependencies = {
                dependency
                for dependency
                in COMMAND_TOKEN_RE.findall(
                    definition.replacement
                )
                if dependency in definitions_by_token
            }

            new_dependencies = (
                dependencies - required_tokens
            )

            if new_dependencies:
                required_tokens.update(
                    new_dependencies
                )

                changed = True

    return [
        definition
        for definition in definitions
        if definition.token in required_tokens
    ]


def _read_macro_name(
    text: str,
    index: int,
) -> tuple[str, int] | None:
    """
    Read either ``{\\foo}`` or the unbraced ``\\foo`` form.
    """

    index = _skip_whitespace_and_comments(
        text,
        index,
    )

    if index >= len(text):
        return None

    if text[index] == "{":
        close_index = _find_matching_delimiter(
            text,
            index,
            "{",
            "}",
        )

        if close_index == -1:
            return None

        token = text[
            index + 1:
            close_index
        ].strip()

        if not MACRO_NAME_RE.fullmatch(token):
            return None

        return token, close_index + 1

    match = re.match(
        r"\\[A-Za-z@]+",
        text[index:],
    )

    if not match:
        return None

    token = match.group(0)

    return token, index + len(token)


def _read_optional_group(
    text: str,
    index: int,
) -> tuple[str | None, int, str | None]:
    """
    Read an optional balanced square-bracket group.
    """

    index = _skip_whitespace_and_comments(
        text,
        index,
    )

    if (
        index >= len(text)
        or text[index] != "["
    ):
        return None, index, None

    close_index = _find_matching_delimiter(
        text,
        index,
        "[",
        "]",
    )

    if close_index == -1:
        return (
            None,
            len(text),
            "Unterminated optional group.",
        )

    return (
        text[index + 1:close_index],
        close_index + 1,
        None,
    )


def _find_definition_end_after_default(
    text: str,
    index: int,
) -> int:
    """
    Consume the replacement group of an unsupported default-argument
    definition so scanning can continue after the complete definition.
    """

    index = _skip_whitespace_and_comments(
        text,
        index,
    )

    if (
        index >= len(text)
        or text[index] != "{"
    ):
        return index

    close_index = _find_matching_delimiter(
        text,
        index,
        "{",
        "}",
    )

    if close_index == -1:
        return len(text)

    return close_index + 1


def _validate_parameter_markers(
    replacement: str,
    argument_count: int,
) -> str | None:
    """
    Ensure the replacement agrees with the frontend V1 parameter model.
    """

    if "##" in replacement:
        return (
            "Doubled parameter markers are not supported."
        )

    parameter_numbers = [
        int(value)
        for value in re.findall(
            r"(?<!#)#([1-9])",
            replacement,
        )
    ]

    if any(
        number > argument_count
        for number in parameter_numbers
    ):
        return (
            "Replacement references a parameter greater "
            "than the declared argument count."
        )

    return None


def _skip_whitespace_and_comments(
    text: str,
    index: int,
) -> int:
    """
    Skip ordinary whitespace and complete unescaped TeX comment lines.
    """

    while index < len(text):
        if text[index].isspace():
            index += 1
            continue

        if (
            text[index] == "%"
            and not _is_escaped(text, index)
        ):
            newline_index = text.find(
                "\n",
                index + 1,
            )

            if newline_index == -1:
                return len(text)

            index = newline_index + 1
            continue

        break

    return index


def _find_matching_delimiter(
    text: str,
    open_index: int,
    opening: str,
    closing: str,
) -> int:
    """
    Find a balanced closing brace or bracket.

    Escaped delimiters and delimiters inside TeX comments are ignored.
    """

    if (
        open_index < 0
        or open_index >= len(text)
        or text[open_index] != opening
    ):
        return -1

    depth = 0
    inside_comment = False

    for index in range(
        open_index,
        len(text),
    ):
        character = text[index]

        if inside_comment:
            if character == "\n":
                inside_comment = False

            continue

        if (
            character == "%"
            and not _is_escaped(text, index)
        ):
            inside_comment = True
            continue

        if character not in {
            opening,
            closing,
        }:
            continue

        if _is_escaped(text, index):
            continue

        if character == opening:
            depth += 1
        else:
            depth -= 1

            if depth == 0:
                return index

    return -1


def _is_inside_tex_comment(
    text: str,
    index: int,
) -> bool:
    """
    Determine whether an index occurs after an unescaped percent sign
    on its current line.
    """

    line_start = text.rfind(
        "\n",
        0,
        index,
    ) + 1

    cursor = line_start

    while cursor < index:
        if (
            text[cursor] == "%"
            and not _is_escaped(text, cursor)
        ):
            return True

        cursor += 1

    return False


def _is_escaped(
    text: str,
    index: int,
) -> bool:
    """
    Return True when the character at index has an odd number of
    immediately preceding backslashes.
    """

    backslash_count = 0
    previous = index - 1

    while (
        previous >= 0
        and text[previous] == "\\"
    ):
        backslash_count += 1
        previous -= 1

    return backslash_count % 2 == 1


def _make_preview(
    text: str,
    start: int,
    end: int | None = None,
    limit: int = 260,
) -> str:
    """
    Produce a compact diagnostic excerpt.
    """

    if end is None:
        newline_index = text.find(
            "\n",
            start,
        )

        end = (
            len(text)
            if newline_index == -1
            else newline_index
        )

        end = max(
            end,
            min(
                len(text),
                start + 80,
            ),
        )

    value = text[start:end].strip()

    if len(value) > limit:
        return value[:limit - 1] + "…"

    return value