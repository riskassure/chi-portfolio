"""Create the centralizer entry and autolink its two motivating occurrences.

Run after the math catalog has been loaded. The migration is safe to rerun.
"""

from datetime import datetime
from pathlib import Path
import sqlite3
import sys


BACKEND_SRC = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_SRC))

from services.math.concept_create_service import create_math_concept
from services.math.concept_render_service import render_tex_reusing_existing_diagrams


DB_PATH = BACKEND_SRC.parent / "portfolio.db"
TITLE = "centralizer in a ring"
CANONICAL_NAME = "CentralizerinaRing"
SLUG = "centralizer-in-a-ring"
SOURCE = r"""Let $R$ be an associative ring with identity and let $S\subseteq R$.

\begin{definition}
The \emph{centralizer of $S$ in $R$} is the set
\[
C_R(S)=\{r\in R\mid rs=sr\text{ for every }s\in S\}.
\]
For a single element $s\in R$, write $C_R(s)$ for $C_R(\{s\})$.
\end{definition}

The centralizer is a unital subring of $R$: if $x$ and $y$ commute with every
element of $S$, so do $x-y$ and $xy$, and $1_R$ commutes with every element.
If $S\subseteq T\subseteq R$, then $C_R(T)\subseteq C_R(S)$.  In particular,
$C_R(R)$ is the center of $R$.

\begin{example}
Let $R=M_n(A)$, where $A$ is an associative ring with identity, and let
$E_{ij}$ be the standard matrix units. A matrix commutes with every $E_{ij}$
if and only if it is of the form $aI_n$ for some $a\in A$. Thus
\[
C_{M_n(A)}(\{E_{ij}:1\leq i,j\leq n\})=\{aI_n:a\in A\}.
\]
The displayed subring is isomorphic to $A$, even when $A$ is not commutative.
\end{example}

\begin{thebibliography}{9}
\bibitem{Brosnan} P. Brosnan, \PMlinkexternal{Centralizers and Center}{https://www.math.umd.edu/~pbrosnan/notes/ugalg/sect0017.html}, undergraduate algebra notes, University of Maryland.
\end{thebibliography}
"""


def apply(db_path: Path = DB_PATH) -> dict:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        existing = cursor.execute(
            "SELECT id FROM math_concepts WHERE slug = ?", (SLUG,)
        ).fetchone()

        if existing:
            concept_id = existing[0]
            created = False
        else:
            result = create_math_concept(
                cursor=cursor,
                canonical_name=CANONICAL_NAME,
                slug=SLUG,
                title=TITLE,
                timestamp=timestamp,
                owner="CWoo",
                cleaned_tex=SOURCE,
                is_cleaned_flag=1,
                classifications=["16U70", "16S50"],
                types=["Definition", "Example"],
                synonyms=[
                    "centralizer",
                    "ring centralizer",
                    "centralizer of a subset of a ring",
                ],
                definitions=["centralizer in a ring"],
                related_concepts=["MatrixRing", "MatrixUnit"],
            )
            concept_id = result["concept_id"]
            created = True

        # Existing local installations may have run the first version of this
        # migration, which used explicit links before the synonym was verified.
        synonym_exists = cursor.execute(
            """
            SELECT 1 FROM math_synonyms
            WHERE concept_id = ? AND lower(trim(synonym_text)) = 'centralizer'
            """,
            (concept_id,),
        ).fetchone()
        if not synonym_exists:
            cursor.execute(
                "INSERT INTO math_synonyms (concept_id, synonym_text) VALUES (?, ?)",
                (concept_id, "centralizer"),
            )

        linked_entries = []
        for parent_slug in ("matrix-ring", "matrix-unit"):
            parent = cursor.execute(
                "SELECT id, cleaned_tex FROM math_concepts WHERE slug = ?",
                (parent_slug,),
            ).fetchone()
            if parent is None:
                raise RuntimeError(f"Missing source entry: {parent_slug}")

            parent_id, cleaned_tex = parent
            explicit_link = rf"\PMlinkname{{centralizer}}{{{CANONICAL_NAME}}}"
            if explicit_link in cleaned_tex:
                updated_tex = cleaned_tex.replace(explicit_link, "centralizer")
            elif "centralizer" in cleaned_tex:
                continue
            else:
                raise RuntimeError(f"No centralizer occurrence in {parent_slug}")

            rendered_tex = render_tex_reusing_existing_diagrams(
                parent_id, updated_tex, cursor
            )
            cursor.execute(
                """
                UPDATE math_concepts
                SET cleaned_tex = ?, rendered_tex = ?, updated_at = ?
                WHERE id = ?
                """,
                (updated_tex, rendered_tex, timestamp, parent_id),
            )
            linked_entries.append(parent_slug)

    return {"concept_id": concept_id, "created": created, "linked": linked_entries}


if __name__ == "__main__":
    print(apply())
