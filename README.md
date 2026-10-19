# 🗞️ Middle East News Bot

Bot de Telegram que junta noticias sobre Israel, mundo judío, conflicto árabe-israelí, marchas pro-Palestina y terrorismo yihadista, y las manda como **resumen** a las 08:00, 14:00 y 20:00 (hora de Chile).

- Fuentes y palabras clave: `config.py` (medios sin RSS se leen vía búsquedas de Google News).
- Estado (notas vistas, pendientes, último resumen): `/data/state.json` en un volumen de Railway.

## Variables de entorno

| Variable | Valor |
|----------|-------|
| `TELEGRAM_TOKEN` | Token de @BotFather |
| `TELEGRAM_CHAT_ID` | Chat ID numérico |
| `DIGEST_HOURS` | `8,14,20` (opcional) |
| `POLL_INTERVAL_MINUTES` | `30` (opcional) |
| `STATE_FILE` | `/data/state.json` (opcional) |

## Prueba local (sin enviar a Telegram)

```bash
DRY_RUN=1 RUN_ONCE=1 STATE_FILE=state.json python bot.py
```
