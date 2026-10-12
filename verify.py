#!/usr/bin/env python3
"""
YakLudka — верификатор честной игры (Provably Fair)

Проверяет, что результат раунда Crash / PvP / Arena / Gravity получен из сида,
хеш которого сервер опубликовал заранее, а не подменён после ставок.

Данные берутся из окна «Честная игра» в приложении (кнопка-щит):
блок «Прошлые раунды» → раскрыть раунд → Server Seed, хеш, строка для билета.

Использование:
    python verify.py crash --round-id 1234 --result 2.35 \
        --server-seed <hex> --server-seed-hash <hex>

    python verify.py pvp --round-id 1234 --total-tickets 57 --result 41 \
        --server-seed <hex> --server-seed-hash <hex>

    (arena и gravity — так же, как pvp)
"""

import argparse
import hashlib
import sys

TICKET_GAMES = ("pvp", "arena", "gravity")


def sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_crash(round_id: int, crash_point: float, server_seed: str, server_seed_hash: str):
    """
    Crash — commit-reveal: при старте раунда публикуется
        sha256(f"{round_id}:{crash_point:.2f}:{server_seed}")
    После краха раскрывается server_seed. Пересчитанный хеш должен совпасть
    с опубликованным — значит, крах был зафиксирован до полёта.
    """
    payload = f"{int(round_id)}:{float(crash_point):.2f}:{server_seed}"
    computed = sha256_hex(payload)
    ok = computed == server_seed_hash.lower()
    return ok, [f"payload       = {payload}", f"computed_hash = {computed}", f"expected_hash = {server_seed_hash}", f"хеш совпал    = {ok}"]


def verify_ticket(game: str, round_id: int, total_tickets: int, server_seed: str, server_seed_hash: str, expected_ticket: int):
    """
    PvP / Arena / Gravity — две проверки, обе обязательны:
      1) сид не подменён: sha256(f"{game}_seed:{server_seed}") == опубликованный хеш
      2) билет из сида:   sha256(f"{game}_ticket:{round_id}:{total_tickets}:{server_seed}") % total_tickets + 1
    Без первой проверки вторая ничего не доказывает: под уже известные ставки
    можно было бы подобрать любой сид.
    """
    commit = sha256_hex(f"{game}_seed:{server_seed}")
    commit_ok = commit == server_seed_hash.lower()
    payload = f"{game}_ticket:{int(round_id)}:{int(total_tickets)}:{server_seed}"
    digest = sha256_hex(payload)
    ticket = int(digest, 16) % int(total_tickets) + 1
    ticket_ok = ticket == int(expected_ticket)
    lines = [
        f"1) commit      = sha256({game}_seed:{server_seed})",
        f"   computed    = {commit}",
        f"   expected    = {server_seed_hash}",
        f"   хеш совпал  = {commit_ok}",
        f"2) payload     = {payload}",
        f"   sha256      = {digest}",
        f"   билет       = {ticket} (ожидался {expected_ticket})",
        f"   билет совпал = {ticket_ok}",
    ]
    return commit_ok and ticket_ok, lines


def main():
    parser = argparse.ArgumentParser(description="YakLudka Provably Fair verifier")
    sub = parser.add_subparsers(dest="game", required=True)

    p_crash = sub.add_parser("crash", help="Проверить раунд Crash")
    p_crash.add_argument("--round-id", type=int, required=True)
    p_crash.add_argument("--result", type=float, required=True, help="Икс краха")
    p_crash.add_argument("--server-seed", required=True)
    p_crash.add_argument("--server-seed-hash", required=True, help="Хеш, опубликованный при старте раунда")

    for name in TICKET_GAMES:
        p = sub.add_parser(name, help=f"Проверить раунд {name}")
        p.add_argument("--round-id", type=int, required=True)
        p.add_argument("--total-tickets", "--nonce", dest="total_tickets", type=int, required=True, help="Всего билетов в раунде")
        p.add_argument("--result", type=int, required=True, help="Победный билет")
        p.add_argument("--server-seed", required=True)
        p.add_argument("--server-seed-hash", required=True, help="Хеш (коммит), опубликованный до розыгрыша")

    args = parser.parse_args()
    if args.game == "crash":
        ok, lines = verify_crash(args.round_id, args.result, args.server_seed, args.server_seed_hash)
    else:
        ok, lines = verify_ticket(args.game, args.round_id, args.total_tickets, args.server_seed, args.server_seed_hash, args.result)

    print("\n".join(lines))
    print()
    print("РЕЗУЛЬТАТ: ЧЕСТНО" if ok else "РЕЗУЛЬТАТ: НЕ СОВПАДАЕТ")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
