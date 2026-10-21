# Embedded category-theory definitions audit

Reviewed 2026-09-24 using category-classified defined terms, existing titles,
and the full source of the selected parent entries.

| Standalone entry | Previous location |
| --- | --- |
| Natural isomorphism | Natural transformation |
| Contravariant functor | Functor |
| Forgetful functor | Functor |
| Zero object | Initial and terminal objects |
| Small category | Category |
| Locally small category | Category |

The parent entries link to the new definitions and retain their surrounding
examples and explanations. The componentwise criterion for natural
isomorphisms and its proof moved to the new page; the natural-transformation
entry's document types were updated accordingly. Definition metadata now
resolves the six terms to their standalone titles. New entries use owner CWoo,
MSC classifications, semantic document types, examples, related entries, and
references to Emily Riehl's *Category Theory in Context*.

Autolinking was checked through the public rendering service, including
existing occurrences outside the parent entries. Unrelated meanings of
object, terminal, path, and monoid were suppressed locally in the new pages.
Validation also covers math preservation, semantic blocks, search discovery,
parent links, and database integrity; no browser-based visual review was run.

This is a selected extraction pass. Other possible candidates include
coequalizers, pushouts, injective objects, and full subcategories. Their
existing contexts need separate review before extraction; not every dual
notion or short supporting definition necessarily needs a separate page.

Migration: `backend/src/database/math/migrations/extract_category_foundations.py`.
