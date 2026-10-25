"""List pairs of math entries that might be merged, cross-linked or renamed. Read-only.

    python backend/find_merge_candidates.py --db PATH-TO-WORKING-DB [--output FOLDER]

Opens the database read-only and writes candidates.md and candidates.csv into a new
folder (default dist/merge-candidates/<UTC time>/). Nothing else is changed.

Every suggested action is a heuristic. Shared MSC codes, document types and word
overlap cannot establish that two entries state the same mathematics, so each row
is a prompt for a human decision, never a verdict. Shared terminology on its own
(a synonym or defined term used by two entries) never produces a merge suggestion.
See /mnt/project-files/entry-merging/ (design v3, section 9) for the rules.
"""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
import csv
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]

# Word shingles shared by many entries are boilerplate ("let be a ...") and say
# nothing about two particular entries being alike.
SHINGLE_SIZE = 4
MAX_SHINGLE_ENTRIES = 15
# Below these, word overlap is ignored as a signal.
MIN_SHARED_SHINGLES = 5
MIN_CONTAINMENT = 0.3
# Overlap strong enough, together with subject and role, to suggest a merge.
MERGE_CONTAINMENT = 0.6
MERGE_JACCARD = 0.4
# Sibling definitions ("full functor", "faithful functor") share templated wording.
# Without a title link between them, only a near-subset counts as a possible duplicate.
NEAR_SUBSET = 0.85

STATEMENT_TYPES = {'Theorem', 'Result', 'Corollary', 'Conjecture', 'Axiom'}
TITLE_ROLES = [
    (re.compile(r'^(proof|proofs|another proof|alternative proof)\b'), 'proof'),
    (re.compile(r'^(example|examples)\b'), 'examples'),
    (re.compile(r'characteri[sz]ation|equivalent (definitions|conditions|formulations)|criteri(on|a)\b'),
     'characterization'),
    (re.compile(r'^(properties|basic properties|facts)\b'), 'properties'),
]
HEURISTIC = ('Heuristic: MSC overlap, document types and text similarity cannot establish '
             'mathematical equivalence. Chi decides every row.')
ACTIONS = ('merge', 'rename', 'cross-link', 'leave')


def normalize_title(title):
    """Lowercase, drop leading articles and simple plurals, so "The groups" matches "group"."""
    words = re.sub(r'[^a-z0-9$ ]+', ' ', (title or '').lower()).split()
    if words and words[0] in ('the', 'a', 'an'):
        words = words[1:]
    return ' '.join(w[:-1] if len(w) > 3 and w.endswith('s') and not w.endswith('ss') else w for w in words)


def words_of(tex):
    """Prose and symbol words of an entry's TeX, without commands, for overlap comparison."""
    text = re.sub(r'\\[A-Za-z@]+\*?', ' ', tex or '')
    return [w for w in re.findall(r'[a-z0-9]+', text.lower()) if len(w) > 1]


def shingles(tex):
    words = words_of(tex)
    return {tuple(words[i:i + SHINGLE_SIZE]) for i in range(len(words) - SHINGLE_SIZE + 1)}


def pmlink_targets(tex):
    return re.findall(r'\\PMlinkname\s*\{[^{}]*\}\s*\{([^{}]+)\}', tex or '')


def role_of(title, types):
    """The entry's main kind of content, from its title first and its document types second."""
    lowered = (title or '').lower()
    for pattern, role in TITLE_ROLES:
        if pattern.search(lowered):
            return role
    statement, definition = bool(types & STATEMENT_TYPES), 'Definition' in types
    if statement and not definition:
        return 'statement'
    if definition and not statement:
        return 'definition'
    return 'mixed'


def comparable_roles(a, b):
    """Whether two roles could be the same page: equal, or one is mixed with a definition/statement."""
    if a == b:
        return True
    return {a, b} <= {'mixed', 'definition', 'statement'} and 'mixed' in (a, b)


def load(db):
    """Read the active entries and their metadata as {id: entry}."""
    columns = {row[1] for row in db.execute('PRAGMA table_info(math_concepts)')}
    # Forward compatible: once retirement exists, retired entries are not candidates.
    active = ' WHERE retired_at IS NULL' if 'retired_at' in columns else ''
    entries = {}
    for ident, canonical, slug, title, tex in db.execute(
            'SELECT id, canonical_name, slug, title, cleaned_tex FROM math_concepts' + active):
        entries[ident] = dict(id=ident, canonical=canonical, slug=slug, title=title, tex=tex or '',
                              msc=set(), types=set(), aliases=set(), related=set(), links=set())
    queries = [
        ('msc', 'SELECT m.concept_id, c.code FROM math_concept_classifications m '
                'JOIN math_classifications c ON c.id = m.classification_id'),
        ('types', 'SELECT m.concept_id, t.type_name FROM math_concept_types m JOIN math_types t ON t.id = m.type_id'),
        ('aliases', 'SELECT concept_id, synonym_text FROM math_synonyms'),
        ('aliases', 'SELECT concept_id, defined_term FROM math_definitions'),
    ]
    for key, query in queries:
        for ident, value in db.execute(query):
            if ident in entries and value:
                entries[ident][key].add(value.strip() if key != 'aliases' else value.strip().lower())
    by_canonical = {e['canonical'].casefold(): e['id'] for e in entries.values() if e['canonical']}
    for ident, name, target in db.execute(
            'SELECT concept_id, related_canonical_name, related_concept_id FROM math_related_concepts'):
        target = target if target in entries else by_canonical.get((name or '').casefold())
        if ident in entries and target and target != ident:
            entries[ident]['related'].add(target)
    for entry in entries.values():
        for name in pmlink_targets(entry['tex']):
            target = by_canonical.get(name.strip().casefold())
            if target and target != entry['id']:
                entry['links'].add(target)
        entry['role'] = role_of(entry['title'], entry['types'])
        entry['length'] = len(entry['tex'])
    incoming = Counter()
    for entry in entries.values():
        for target in entry['related'] | entry['links']:
            incoming[target] += 1
    for ident, entry in entries.items():
        entry['incoming'] = incoming[ident]
    return entries


def text_overlaps(entries):
    """Return {(a, b): (shared, jaccard, containment)} for pairs with meaningful word overlap."""
    sets = {ident: shingles(entry['tex']) for ident, entry in entries.items()}
    index = defaultdict(list)
    for ident, found in sets.items():
        for shingle in found:
            index[shingle].append(ident)
    shared = Counter()
    for owners in index.values():
        if 1 < len(owners) <= MAX_SHINGLE_ENTRIES:
            for pair in combinations(sorted(owners), 2):
                shared[pair] += 1
    result = {}
    for (a, b), count in shared.items():
        if count < MIN_SHARED_SHINGLES:
            continue
        union = len(sets[a] | sets[b])
        containment = count / min(len(sets[a]), len(sets[b]))
        if containment >= MIN_CONTAINMENT:
            result[(a, b)] = (count, count / union, containment)
    return result


def msc_relation(a, b):
    """'same area' when codes share a 3-character prefix (e.g. 03B), 'same field' for 2 digits, else 'different'."""
    if {c[:3] for c in a} & {c[:3] for c in b}:
        return 'same area'
    if {c[:2] for c in a} & {c[:2] for c in b}:
        return 'same field'
    return 'different' if a and b else 'unknown'


def suggest(a, b, signals, overlap):
    """Return (action, reason) for one pair; see the module docstring for what this is not."""
    area = msc_relation(a['msc'], b['msc'])
    roles = comparable_roles(a['role'], b['role'])
    linked = b['id'] in a['related'] | a['links'] or a['id'] in b['related'] | b['links']
    _, jaccard, containment = overlap or (0, 0.0, 0.0)
    strong_text = containment >= MERGE_CONTAINMENT or jaccard >= MERGE_JACCARD
    if 'same title' in signals:
        if area in ('different', 'same field') and not strong_text:
            return 'rename', 'same title in different subjects; disambiguate the titles'
        if area == 'same area' and roles:
            return 'merge', 'same title, same subject area and comparable content roles'
        return 'rename', 'same title but different content roles or unclassified; disambiguate'
    if strong_text and area == 'same area' and roles and (containment >= NEAR_SUBSET or 'title is alias' in signals):
        return 'merge', 'strong text overlap, same subject area and comparable content roles'
    if strong_text and area == 'same area' and roles and not linked:
        return 'cross-link', 'similar wording but different titles; likely sibling concepts, link them'
    if strong_text or ('title is alias' in signals and area == 'same area'):
        if linked:
            return 'leave', 'related, and already linked to each other'
        if not roles:
            return 'cross-link', f"same object, different roles ({a['role']} / {b['role']}); link them"
        return 'cross-link', 'related content that does not link to the other entry'
    if 'text overlap' in signals and not linked and area == 'same area':
        return 'cross-link', 'some shared wording in the same subject area; check whether a link helps'
    return 'leave', 'shared terminology or weak overlap only; not evidence of a duplicate'


def survivor(a, b):
    """Suggest the entry more pages point to, then the longer text, then the older id."""
    return min((a, b), key=lambda e: (-e['incoming'], -e['length'], e['id']))


def find_candidates(entries):
    pairs = defaultdict(set)
    by_title = defaultdict(list)
    for entry in entries.values():
        by_title[normalize_title(entry['title'])].append(entry['id'])
    for owners in by_title.values():
        for pair in combinations(sorted(owners), 2):
            pairs[pair].add('same title')
    titles = {entry['title'].strip().lower(): entry['id'] for entry in entries.values() if entry['title']}
    by_alias = defaultdict(set)
    for entry in entries.values():
        for alias in entry['aliases']:
            by_alias[alias].add(entry['id'])
            other = titles.get(alias)
            if other and other != entry['id']:
                pairs[tuple(sorted((entry['id'], other)))].add('title is alias')
    for owners in by_alias.values():
        for pair in combinations(sorted(owners), 2):
            pairs[pair].add('shared alias')
    overlaps = text_overlaps(entries)
    for pair in overlaps:
        pairs[pair].add('text overlap')
    rows = []
    for (x, y), signals in pairs.items():
        a, b = entries[x], entries[y]
        overlap = overlaps.get((x, y))
        action, reason = suggest(a, b, signals, overlap)
        keep = survivor(a, b) if action == 'merge' else None
        rows.append(dict(action=action, reason=reason, signals=sorted(signals), a=a, b=b,
                         shared_shingles=overlap[0] if overlap else 0,
                         jaccard=round(overlap[1], 3) if overlap else 0.0,
                         containment=round(overlap[2], 3) if overlap else 0.0,
                         msc=msc_relation(a['msc'], b['msc']),
                         survivor=keep['title'] + f" ({keep['id']})" if keep else ''))
    rows.sort(key=lambda r: (ACTIONS.index(r['action']), -r['containment'], r['a']['id'], r['b']['id']))
    return rows


def _describe(entry):
    return (f"{entry['title']} ({entry['id']}, {entry['slug']}; {','.join(sorted(entry['msc'])) or 'no MSC'}; "
            f"{entry['role']}; {entry['length']} chars; {entry['incoming']} in)")


def write_report(rows, folder, database, entry_count):
    counts = Counter(r['action'] for r in rows)
    with (folder / 'candidates.csv').open('x', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['suggested_action (heuristic)', 'reason', 'signals', 'id_a', 'title_a', 'slug_a', 'msc_a',
                         'role_a', 'length_a', 'incoming_a', 'id_b', 'title_b', 'slug_b', 'msc_b', 'role_b',
                         'length_b', 'incoming_b', 'msc_relation', 'shared_shingles', 'jaccard', 'containment',
                         'suggested_survivor', 'chi_decision'])
        for r in rows:
            a, b = r['a'], r['b']
            writer.writerow([r['action'], r['reason'], '; '.join(r['signals']),
                             a['id'], a['title'], a['slug'], ' '.join(sorted(a['msc'])), a['role'], a['length'],
                             a['incoming'], b['id'], b['title'], b['slug'], ' '.join(sorted(b['msc'])), b['role'],
                             b['length'], b['incoming'], r['msc'], r['shared_shingles'], r['jaccard'],
                             r['containment'], r['survivor'], ''])
    lines = ['# Merge candidates (heuristic)', '',
             f'Database: `{database}` (read-only), {entry_count} active entries. '
             f'Generated {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}.', '',
             f'**{HEURISTIC}** Shared terminology alone never produces a merge suggestion.', '',
             'Each entry: title (id, slug; MSC codes; content role; text length; entries linking to it by '
             'related concept or \\PMlinkname).', '',
             '| Suggested action | Pairs |', '|---|---|']
    lines += [f'| {action} | {counts[action]} |' for action in ACTIONS]
    for action in ACTIONS:
        lines += ['', f'## {action.capitalize()} (heuristic)', '']
        selected = [r for r in rows if r['action'] == action]
        if action == 'leave':
            lines += [f'{len(selected)} pairs share only terminology or weak wording, or are already linked. '
                      'They are listed in candidates.csv, not here.']
            continue
        if not selected:
            lines.append('None.')
        for number, r in enumerate(selected, 1):
            lines.append(f"{number}. {_describe(r['a'])}  \n   {_describe(r['b'])}  \n"
                         f"   Why: {r['reason']}. Signals: {', '.join(r['signals'])}"
                         + (f"; overlap {r['containment']:.0%} of the shorter entry" if r['shared_shingles'] else '')
                         + (f".  \n   Suggested survivor: {r['survivor']}." if r['survivor'] else '.'))
    (folder / 'candidates.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return counts


def run(database, output=None):
    """Write the report for database into output (a new folder); return (folder, counts)."""
    database = Path(database).resolve()
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        entries = load(db)
    rows = find_candidates(entries)
    folder = Path(output) if output else ROOT / 'dist' / 'merge-candidates' / datetime.now(timezone.utc).strftime(
        '%Y%m%dT%H%M%SZ')
    folder.mkdir(parents=True, exist_ok=False)
    return folder, write_report(rows, folder, database, len(entries))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--db', type=Path, required=True, help='Database to read (opened read-only).')
    parser.add_argument('--output', type=Path, help='New folder for the report (must not exist).')
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f'no database file at {args.db}')
    folder, counts = run(args.db, args.output)
    print('Read-only; no database was changed.')
    print(', '.join(f'{action}: {counts[action]}' for action in ACTIONS))
    print('Report:', folder / 'candidates.md')


if __name__ == '__main__':
    main()
