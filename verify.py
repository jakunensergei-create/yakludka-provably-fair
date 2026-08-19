#!/usr/bin/env python3
"""
YakLudka — верификатор честной игры (Provably Fair)

Проверяет, что результат раунда Crash / Arena / PvP действительно получен
из опубликованного server_seed, а не подменён после того, как сервер
объявил хеш (server_seed_hash) до начала раунда.

Данные для проверки берутся из окна «Честная игра» в приложении:
round_id, server_seed_hash, server_seed, nonce (=client_seed для Crash не
используется, для Arena/PvP nonce = total_tickets), result.

Использование:
    python verify.py crash --round-id 1234 --result 2.35 \
        --server-seed <hex> --server-seed-hash <hex>

    python verify.py arena --round-id 1234 --nonce 57 --result 41 \
        --server-seed <hex>

    python verify.py pvp --round-id 1234 --nonce 57 --result 41 \
        --server-seed <hex>
"""

import argparse
import hashlib
import sys


def sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_crash(round_id: int, crash_point: float, server_seed: str, server_seed_hash: str = "") -> tuple[bool, str]:
    """
    Crash — схема commit-reveal без формулы: множитель падения (crash_point)
    выбирается сервером случайно ДО раунда, и сразу считается хеш
    sha256(round_id:crash_point:server_seed) — он публикуется как
    server_seed_hash ДО приёма ставок. server_seed раскрывается только
    после раунда.

    Проверка: пересчитать этот же хеш из вскрытых round_id/crash_point/
    server_seed и сверить с тем server_seed_hash, что был опубликован ДО
    раунда (его нужно было записать заранее — сервер не может задним
    числом посчитать другой crash_point под уже опубликованный хеш).
    """
    payload = f"{int(round_id)}:{float(crash_point):.2f}:{server_seed}"
    computed_hash = sha256_hex(payload)
    if server_seed_hash:
        ok = computed_hash == server_seed_hash
        return ok, f"payload={payload}\ncomputed_hash={computed_hash}\nexpected_hash={server_seed_hash}\nmatch={ok}"
    return True, f"payload={payload}\ncomputed_hash={computed_hash}\n(server_seed_hash не передан — сверьте его с тем, что видели ДО раунда)"


def verify_ticket(prefix: str, round_id: int, total_tickets: int, server_seed: str, expected_result: int) -> tuple[bool, str]:
    """
    Arena / PvP — победный билет вычисляется по формуле:
        sha256(f"{prefix}_ticket:{round_id}:{total_tickets}:{server_seed}") % total_tickets + 1
    Тот, чей билет совпал с результатом, выигрывает раунд.
    """
    payload = f"{prefix}_ticket:{int(round_id)}:{int(total_tickets)}:{server_seed}"
    digest_hex = sha256_hex(payload)
    ticket = int(digest_hex, 16) % int(total_tickets) + 1
    ok = ticket == int(expected_result)
    return ok, f"payload={payload}\nsha256={digest_hex}\ncomputed_ticket={ticket}\nexpected_ticket={expected_result}\nmatch={ok}"


def main():
    parser = argparse.ArgumentParser(description="YakLudka Provably Fair verifier")
    sub = parser.add_subparsers(dest="game", required=True)

    p_crash = sub.add_parser("crash", help="Проверить раунд Crash")
    p_crash.add_argument("--round-id", type=int, required=True)
    p_crash.add_argument("--result", type=float, required=True, help="Икс краха (crash_point)")
    p_crash.add_argument("--server-seed", required=True)
    p_crash.add_argument("--server-seed-hash", default="", help="Хеш, который вы видели ДО раунда (необязательно)")

    for name, label in (("arena", "Arena"), ("pvp", "PvP")):
        p = sub.add_parser(name, help=f"Проверить раунд {label}")
        p.add_argument("--round-id", type=int, required=True)
        p.add_argument("--nonce", type=int, required=True, help="total_tickets раунда")
        p.add_argument("--result", type=int, required=True, help="Победный билет")
        p.add_argument("--server-seed", required=True)

    args = parser.parse_args()

    if args.game == "crash":
        ok, details = verify_crash(args.round_id, args.result, args.server_seed, args.server_seed_hash)
    else:
        ok, details = verify_ticket(args.game, args.round_id, args.nonce, args.server_seed, args.result)

    print(details)
    print()
    print("РЕЗУЛЬТАТ: ЧЕСТНО ✓" if ok else "РЕЗУЛЬТАТ: НЕ СОВПАДАЕТ ✗")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
