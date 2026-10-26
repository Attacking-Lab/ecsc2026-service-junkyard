import random
import string
import time
from ctypes import c_int32

from z3 import Solver, unsat, BitVec, BitVecVal, Or, And


CHARSET = [ord(c) for c in string.digits + string.ascii_uppercase + string.ascii_lowercase]
CHARSET_SET = set(CHARSET)


def random_string(l: int) -> str:
    return "".join(random.choice(string.ascii_letters) for i in range(l))


def hashcode(s: str) -> int:
    h = 0
    for c in s:
        h = (h * 31) + ord(c)
    return c_int32(h).value


def get_input_with_z3(h: int, l: int) -> str:
    chars = [BitVec(f'c{_}', 32) for _ in range(l)]
    solver = Solver()
    for c in chars:
        # solver.add(ord('A') <= c)
        # solver.add(c <= ord('z'))
        solver.add(Or(
            And(ord('0') <= c, c <= ord('9')),
            And(ord('A') <= c, c <= ord('Z')),
            And(ord('a') <= c, c <= ord('z')),
        ))

    formula = BitVecVal(0, 32)
    for i, c in enumerate(chars):
        formula += pow(31, i) * c
    formula = (formula == BitVecVal(h, 32))
    solver.add(formula)

    check = solver.check()
    if check == unsat:
        raise Exception("Formula is unsat")

    model = solver.model()
    return "".join(chr(model[c].as_long()) for c in chars[::-1])


def get_input_with_proper_math(h: int, l: int) -> str:
    # Find chars c_0..c_{l-1} with sum(c_i * 31^(l-1-i)) == h (mod 2^32).
    # Since 31^(l-1) * len(range) >> 2^32, we lift to an exact integer equation
    # sum(...) == h + k * 2^32 and solve it digit by digit (most significant first),
    # pruning with the min/max value the remaining positions can still reach.
    weights = [pow(31, l - 1 - i) for i in range(l)]
    lo = [CHARSET[0] * sum(weights[i:]) for i in range(l + 1)]
    hi = [CHARSET[-1] * sum(weights[i:]) for i in range(l + 1)]

    def solve(i: int, rest: int) -> list[int] | None:
        if i == l - 1:
            return [rest] if rest in CHARSET_SET else None
        w = weights[i]
        for c in random.sample(CHARSET, len(CHARSET)):
            r = rest - c * w
            if lo[i + 1] <= r <= hi[i + 1]:
                tail = solve(i + 1, r)
                if tail is not None:
                    return [c] + tail
        return None

    h &= 0xffffffff
    ks = list(range(max(0, -(-(lo[0] - h) // 2**32)), (hi[0] - h) // 2**32 + 1))
    random.shuffle(ks)
    for k in ks:
        res = solve(0, h + k * 2**32)
        if res is not None:
            return "".join(map(chr, res))
    raise Exception("Formula is unsat")


def get_suffix(h: int, l: int, prefix: str) -> str:
    # hash(prefix) * 31^l + h' == h
    h2 = (h - hashcode(prefix) * pow(31, l)) & 0xffffffff
    # return get_input_with_z3(h2, l)
    return get_input_with_proper_math(h2, l)


def get_hashcode_collision(target: int | str, l1: int = 7, l2: int = 7) -> str:
    target = target if isinstance(target, int) else hashcode(target)
    prefix = random_string(l1)
    return prefix + get_suffix(target, l2, prefix)


def main() -> None:
    count = 100
    tg = time.monotonic()
    for _ in range(count):
        username = random_string(random.randint(8, 16))
        t = time.monotonic()
        result = get_hashcode_collision(username)
        dt = time.monotonic() - t
        print(f'{username!r} -> {result!r}: 0x{hashcode(username):x} == 0x{hashcode(result):x}  (in {dt:.3f}s)')
    print(f'{(time.monotonic() - tg) / count:.3f}s / collision')


if __name__ =="__main__":
    main()
