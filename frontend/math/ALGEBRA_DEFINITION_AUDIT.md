# Embedded algebra definitions audit

Reviewed 2026-09-24. Searched titles, synonyms, registered defined terms, and
the source text of the candidate parent entries. This is a focused extraction
pass, not an assertion that every embedded definition should become a page.

| New standalone entry | Previous definition location |
| --- | --- |
| Subgroup | Lagrange's theorem for finite groups |
| Normal subgroup | Normalizer of a subgroup |
| Quotient group | Solvable group |
| Quotient ring | Ideal of a ring |
| Principal ideal of a commutative ring | Principal ideal domain |
| Maximal ideal of a commutative ring | Local ring |
| Finite field | Every finite integral domain is a field |
| Minimal polynomial of an algebraic element | Separable field extension |
| Galois extension | Galois group |

The original entries now reference the standalone definitions. Their remaining
arguments and definitions are retained. The minimal-polynomial existence and
irreducibility proof moved to its new entry, with a divisibility argument added.
Its former parent no longer carries Proof or Result document types for that
removed argument. Extracted terms no longer register their former parents as
their definition locations. Each new entry has owner CWoo, classifications,
document types, examples, references, and related entries.

Principal and maximal ideals retain ring-qualified titles to avoid conflating
them with order-theoretic ideals. The minimal-polynomial title specifies
algebraic elements rather than linear operators. Existing explicit links to
theorems remain intact; changing every historical link would require reviewing
what each particular passage means to cite.

Other possible extractions found in the metadata include group actions (from
orbit-stabilizer), alternating groups (from nonsolvability of symmetric groups),
roots of unity (from cyclotomic extensions), and algebraic closure (from
algebraically closed fields). These have not been extracted in this pass and
would need the same full-source and collision review before changing them.

Reproducible migration:
`backend/src/database/math/migrations/extract_algebra_foundations.py`.
Validation covers source-to-rendered formula preservation, semantic blocks,
document types, classifications, search discovery, parent links, and database
integrity. These checks do not replace a browser-based visual review.
