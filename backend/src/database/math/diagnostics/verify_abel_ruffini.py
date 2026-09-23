"""Independent finite checks for the permutation identities in Abel--Ruffini.

These corroborate examples and catch composition-order errors; the proofs of
the general statements are in the entries, not replaced by these checks.
"""
from itertools import permutations, combinations
from math import factorial


def compose(a, b):
    return tuple(a[b[i]] for i in range(len(a)))


def inverse(a):
    return tuple(a.index(i) for i in range(len(a)))


def cycle(n, *letters):
    a = list(range(n))
    for i, x in enumerate(letters):
        a[x] = letters[(i + 1) % len(letters)]
    return tuple(a)


def generated(n, generators):
    identity = tuple(range(n))
    seen, pending = {identity}, [identity]
    while pending:
        a = pending.pop()
        for b in generators:
            c = compose(a, b)
            if c not in seen:
                seen.add(c)
                pending.append(c)
    return seen


def sign(a):
    return (-1) ** sum(a[i] > a[j] for i in range(len(a)) for j in range(i + 1, len(a)))


def verify():
    n = 5
    a, b = cycle(n, 0, 1, 2), compose(cycle(n, 0, 1), cycle(n, 3, 4))
    assert compose(compose(b, a), inverse(b)) == inverse(a)
    commutator = compose(compose(compose(a, b), inverse(a)), inverse(b))
    assert commutator == compose(a, a)
    alternating = {p for p in permutations(range(n)) if sign(p) == 1}
    conjugates = {compose(compose(g, commutator), inverse(g)) for g in alternating}
    assert len(conjugates) == 20
    assert generated(n, conjugates) == alternating
    assert len(alternating) == 60
    for x, y, z, w in permutations(range(n), 4):
        assert compose(cycle(n, x, y), cycle(n, z, w)) == compose(cycle(n, x, z, y), cycle(n, x, z, w))

    # Every transposition together with a fixed p-cycle generates S_p.
    for p in (2, 3, 5, 7):
        rotation = cycle(p, *range(p))
        for x, y in combinations(range(p), 2):
            assert len(generated(p, (rotation, cycle(p, x, y)))) == factorial(p)
        # Verify the path-conjugation construction with right-to-left products.
        path_product = tuple(range(p))
        for i in range(p - 2):
            path_product = compose(path_product, cycle(p, i, i + 1))
        assert compose(compose(path_product, cycle(p, p - 2, p - 1)), inverse(path_product)) == cycle(p, 0, p - 1)

    coefficients = (5, -10, 0, 0, 0, 1)
    assert coefficients[-1] % 5 and all(x % 5 == 0 for x in coefficients[:-1])
    assert coefficients[0] % 25
    f = lambda x: x**5 - 10*x + 5
    assert f(-2) < 0 < f(-1) and f(0) > 0 > f(1) and f(2) > 0
    print('Passed: A5 commutators, permutation identities, prime-cycle generation, path conjugation, and quintic arithmetic.')


if __name__ == '__main__':
    verify()
