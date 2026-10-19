# ── Paso con Claude: agrupa notas repetidas y resume en español ──────────────
# Si no hay ANTHROPIC_API_KEY o la llamada falla, curate() devuelve None y el
# bot manda la lista normal.
import os
import logging
from typing import List, Literal

from pydantic import BaseModel

log = logging.getLogger(__name__)

MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
ENABLED = bool(os.getenv("ANTHROPIC_API_KEY"))

# Clave interna → título de sección (mismo orden que CATEGORIES en config.py)
SECTIONS = {
    "chile": "🇨🇱 Chile",
    "marchas": "📢 Marchas y protestas",
    "terrorismo": "💣 Terrorismo y yihadismo",
    "comunidades": "✡️ Comunidades judías y antisemitismo",
    "conflicto": "⚔️ Conflicto en Medio Oriente",
    "israel": "🇮🇱 Israel",
}

SYSTEM = """Eres el editor de un resumen de noticias en español para un lector chileno.
Recibes una lista numerada de notas (id | medio | titular | resumen) en inglés y español.

Tu trabajo:
1. Agrupa en una sola noticia las notas que cuentan el mismo hecho (aunque vengan de medios o idiomas distintos).
2. Descarta las notas que no traten de: Israel, judaísmo o comunidades judías, antisemitismo, el conflicto árabe-israelí y sus actores (Gaza, Cisjordania, Hamás, Hezbolá, hutíes, Irán en ese contexto), marchas o protestas pro-palestinas o pro-israelíes, o terrorismo yihadista (ISIS, al-Qaeda, Boko Haram, al-Shabaab, etc.). Descarta también avisos, publicidad y columnas sin hecho noticioso.
3. Para cada noticia escribe un titular breve en español y un resumen de una oración en español (máximo 200 caracteres), neutral y factual: atribuye las afirmaciones a su fuente ("según las FDI", "según el Ministerio de Salud de Gaza") y no agregues opinión ni datos que no estén en las notas.
4. Asigna una sección: chile (hechos ocurridos en Chile o que involucran a Chile), marchas, terrorismo, comunidades, conflicto o israel (política y sociedad israelí).
5. En item_ids pon los ids de todas las notas agrupadas en esa noticia. Cada id aparece como máximo una vez.

Ordena las noticias dentro de cada sección de más a menos relevante."""


class Story(BaseModel):
    section: Literal["chile", "marchas", "terrorismo", "comunidades", "conflicto", "israel"]
    title: str
    summary: str
    item_ids: List[int]


class Digest(BaseModel):
    stories: List[Story]


_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(timeout=120.0)
    return _client


def curate(items: list):
    """Devuelve [(sección, titular, resumen, [items])] o None si no se pudo."""
    if not ENABLED or not items:
        return None
    lines = []
    for i, it in enumerate(items):
        summary = it["summary"].replace("\n", " ")
        lines.append(f"{i} | {it['source']} | {it['title']} | {summary}")
    try:
        response = _get_client().messages.parse(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": "low"},
            system=SYSTEM,
            messages=[{"role": "user", "content": "\n".join(lines)}],
            output_format=Digest,
        )
    except Exception as e:
        log.error(f"Claude error, se manda lista normal: {e}")
        return None

    u = response.usage
    log.info(f"Claude ({MODEL}): {u.input_tokens} tokens entrada, {u.output_tokens} salida, stop={response.stop_reason}")
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        log.error(f"Claude no terminó bien (stop_reason={response.stop_reason}), se manda lista normal")
        return None

    used = set()
    stories = []
    for s in response.parsed_output.stories:
        ids = [i for i in s.item_ids if 0 <= i < len(items) and i not in used]
        if not ids:
            continue
        used.update(ids)
        stories.append((SECTIONS[s.section], s.title.strip(), s.summary.strip(), [items[i] for i in ids]))
    if not stories:
        return None
    log.info(f"Claude: {len(items)} notas → {len(stories)} noticias ({len(items) - len(used)} descartadas)")
    return stories
