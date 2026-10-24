"""Dependencies between new math entries in one batch: related concepts and \\PMlinkname targets.

Shared by the laptop planner and the live batch check sent over SSH, so it
imports nothing beyond the standard library. Explicit links are resolved the
way the site resolves them: the entry is rendered with the site's own
renderer, and each explicit link target is matched, ignoring case, against
canonical names (services.math.autolink_service). A target that matches no
canonical name, or more than one, is reported and blocks publication.
"""
import re
from urllib.parse import unquote

# The anchor render_pmlinkname_to_html produces, as autolink_service matches it.
EXPLICIT_LINK = re.compile(r'<a\b[^>]*\bclass="[^"]*\bmath-explicit-link\b[^"]*"'
                           r'[^>]*\bhref="concept\.html\?slug=([^"]+)"[^>]*>([\s\S]*?)</a>', re.I)


def explicit_targets(tex, render):
    """Return [(visible text, target)] for each explicit link in tex, in order, using the site's renderer."""
    if r'\PMlinkname' not in tex:
        return []
    return [(re.sub(r'<[^>]+>', '', text).strip(), unquote(target).strip())
            for target, text in EXPLICIT_LINK.findall(render(tex))]


def name_index(canonical_names):
    """Return {casefolded canonical name: [canonical names]} for resolving explicit links."""
    index = {}
    for name in canonical_names:
        if name and name.strip():
            index.setdefault(name.strip().casefold(), []).append(name)
    return index


def resolve(target, index):
    """Return (status, canonical): status is 'resolved', 'unresolved' or 'ambiguous'."""
    matches = index.get(target.casefold(), [])
    if len(matches) == 1:
        return 'resolved', matches[0]
    return ('ambiguous' if matches else 'unresolved'), None


def entry_links(canonical, tex, render, index):
    """Return one record per explicit link: visible text, target, status and resolved canonical name."""
    links = []
    for text, target in explicit_targets(tex, render):
        status, resolved = resolve(target, index)
        links.append(dict(text=text, target=target, status=status, canonical=resolved,
                          self_link=resolved == canonical))
    return links


def cycles(graph):
    """Return each dependency loop in graph ({name: set of names it needs first}) as a sorted list.

    A loop is a strongly connected group of two or more entries, or one entry that needs itself.
    """
    index, low, stack, on_stack, found = {}, {}, [], set(), []

    def visit(node):
        index[node] = low[node] = len(index)
        stack.append(node)
        on_stack.add(node)
        for target in sorted(graph.get(node, ())):
            if target not in graph:
                continue
            if target not in index:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], index[target])
        if low[node] == index[node]:
            group = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                group.append(member)
                if member == node:
                    break
            if len(group) > 1 or node in graph.get(node, ()):
                found.append(sorted(group))

    for node in sorted(graph):
        if node not in index:
            visit(node)
    return sorted(found)


def dependants(graph, names):
    """Return every entry that needs one of names first, directly or through others (names excluded)."""
    result, changed = set(), True
    while changed:
        changed = False
        for node, needs in graph.items():
            if node not in result and node not in names and needs & (set(names) | result):
                result.add(node)
                changed = True
    return sorted(result)


def publish_order(graph, preferred):
    """Return the names of graph with every entry after the entries it needs; ties follow preferred order.

    Raise ValueError if graph has a loop.
    """
    rank = {name: position for position, name in enumerate(preferred)}
    remaining = {node: set(needs) & set(graph) for node, needs in graph.items()}
    order = []
    while remaining:
        ready = sorted((node for node, needs in remaining.items() if not needs),
                       key=lambda node: (rank.get(node, len(rank)), node))
        if not ready:
            raise ValueError('These entries depend on each other in a loop: ' + ', '.join(sorted(remaining)))
        node = ready[0]
        order.append(node)
        del remaining[node]
        for needs in remaining.values():
            needs.discard(node)
    return order
