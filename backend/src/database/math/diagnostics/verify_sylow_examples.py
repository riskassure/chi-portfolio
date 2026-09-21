"""Independent finite checks for the Sylow content (no database mutations).

These are numerical sanity checks, not a substitute for reviewing the proofs.
Enumerates subgroups directly, without using Sylow or orbit-stabilizer to
produce the expected counts. Only standard-library modules are needed.
"""
from itertools import combinations, permutations
from math import comb


def mul(a, b):
    return tuple(a[b[i]] for i in range(len(a)))


def inverse(a):
    return tuple(a.index(i) for i in range(len(a)))


def closure(generators, identity):
    result = {identity, *generators}
    while True:
        enlarged = result | {mul(a, b) for a in result for b in result}
        if enlarged == result:
            return result
        result = enlarged


def valuation(n, p):
    result = 0
    while n % p == 0:
        result += 1
        n //= p
    return result


def subgroups(group):
    identity = tuple(range(len(next(iter(group)))))
    others = sorted(group - {identity})
    result = []
    for count in range(len(others) + 1):
        for subset in combinations(others, count):
            h = frozenset((identity, *subset))
            if all(inverse(a) in h for a in h) and all(mul(a, b) in h for a in h for b in h):
                result.append(h)
    return result


def verify():
    cases = 0
    for p in (2, 3, 5, 7):
        for a in range(4):
            for m in range(1, 10):
                if m % p == 0:
                    continue
                for r in range(a + 1):
                    assert valuation(comb(p**a * m, p**r), p) == a - r
                    cases += 1
    print("Counting lemma verified for", cases, "integer cases (including r=0).")

    s3 = set(permutations(range(3)))
    a4 = {g for g in permutations(range(4)) if sum(g[i] > g[j] for i in range(4) for j in range(i+1, 4)) % 2 == 0}
    d8 = closure([(1, 2, 3, 0), (0, 3, 2, 1)], tuple(range(4)))
    for name, group, expected in [("S3", s3, {2: 3, 3: 1}), ("A4", a4, {2: 1, 3: 4}), ("D8", d8, {2: 1})]:
        subs = subgroups(group)
        for p, expected_count in expected.items():
            a = valuation(len(group), p)
            sylows = [h for h in subs if len(h) == p**a]
            assert len(sylows) == expected_count
            assert len(sylows) % p == 1 and (len(group) // p**a) % len(sylows) == 0
            for r in range(a + 1):
                assert any(len(h) == p**r for h in subs)
            base = sylows[0]
            conjugates = {frozenset(mul(mul(g, h), inverse(g)) for h in base) for g in group}
            assert conjugates == set(sylows)
            for q in subs:
                if len(q) in {p**r for r in range(a+1)}:
                    assert any(q <= h for h in sylows)
            fixed = [q for q in sylows if all(frozenset(mul(mul(g,h),inverse(g)) for h in q) == q for g in base)]
            assert fixed == [base]
        print(name, "verified: existence, containment, conjugacy, counts, and unique conjugation fixed point", expected)


if __name__ == "__main__":
    verify()
