# YakLudka — Provably Fair

Скрипт для независимой проверки честности раундов Crash, Arena и PvP в
[YakLudka](https://t.me/yakludkabot) (Telegram Mini App).

## Как это работает

Перед началом раунда сервер публикует хеш секрета (`server_seed_hash`) —
результат раунда уже определён на этот момент, но скрыт. После окончания
раунда сервер раскрывает сам секрет (`server_seed`). Вы можете сами
пересчитать результат по формуле ниже и убедиться, что он совпадает с тем,
что видели в игре — то есть сервер не мог задним числом подменить исход.

- **Crash** — commit-reveal: `server_seed_hash = sha256(round_id:crash_point:server_seed)`.
  Раскрытый `server_seed` должен давать ровно тот хеш, что был опубликован
  до раунда.
- **Arena / PvP** — победный билет вычисляется по формуле:
  `sha256(f"{game}_ticket:{round_id}:{total_tickets}:{server_seed}") % total_tickets + 1`.

Все нужные значения (`round_id`, `server_seed_hash`, `server_seed`, `nonce`,
результат) показаны в окне «Честная игра» (кнопка-щит) в самом приложении —
после розыгрыша раунда.

## Использование

```bash
python verify.py crash --round-id 1234 --result 2.35 \
    --server-seed <hex> --server-seed-hash <hex>

python verify.py arena --round-id 1234 --nonce 57 --result 41 \
    --server-seed <hex>

python verify.py pvp --round-id 1234 --nonce 57 --result 41 \
    --server-seed <hex>
```

Скрипт выводит промежуточные вычисления и итог: **ЧЕСТНО** или
**НЕ СОВПАДАЕТ**.

Требуется только Python 3.9+, без сторонних зависимостей.
