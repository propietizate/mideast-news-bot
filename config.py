# ── Fuentes y palabras clave del Middle East News Bot ─────────────────────────
# Para sumar un medio: agregar una línea en FEEDS. "cl": True lo manda a la
# sección Chile. Las búsquedas de Google News (GN) sirven para medios sin RSS.

GN_ES = "&hl=es-419&gl=CL&ceid=CL:es-419"
GN_EN = "&hl=en-US&gl=US&ceid=US:en"
GN_TOPIC = "(israel+OR+palestina+OR+gaza+OR+jud%C3%ADo+OR+jud%C3%ADa+OR+hamas+OR+hezbol%C3%A1+OR+antisemitismo+OR+yihadista+OR+%22estado+isl%C3%A1mico%22)"


def gn(query: str, lang: str = GN_ES) -> str:
    return f"https://news.google.com/rss/search?q={query}{lang}"


FEEDS = [
    # Israel (inglés)
    {"name": "Times of Israel",   "url": "https://www.timesofisrael.com/feed/"},
    {"name": "Jerusalem Post",    "url": "https://www.jpost.com/rss/rssfeedsfrontpage.aspx"},
    {"name": "Haaretz",           "url": "https://www.haaretz.com/srv/haaretz-latest-headlines"},
    {"name": "Ynetnews",          "url": gn("site:ynetnews.com+when:1d", GN_EN)},
    {"name": "i24NEWS",           "url": gn("site:i24news.tv+when:1d", GN_EN)},
    # Mundo judío
    {"name": "JTA",               "url": "https://www.jta.org/feed"},
    {"name": "JNS",               "url": "https://www.jns.org/feed/"},
    {"name": "Algemeiner",        "url": "https://www.algemeiner.com/feed/"},
    {"name": "Jewish Insider",    "url": "https://jewishinsider.com/feed/"},
    {"name": "Enlace Judío",      "url": "https://www.enlacejudio.com/feed/"},
    {"name": "Itongadol",         "url": "https://www.itongadol.com/feed"},
    # Internacional / Medio Oriente
    {"name": "BBC Middle East",   "url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"},
    {"name": "BBC World",         "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "Al Jazeera",        "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "France24",          "url": "https://www.france24.com/en/middle-east/rss"},
    {"name": "Al-Monitor",        "url": "https://www.al-monitor.com/rss"},
    {"name": "Middle East Eye",   "url": "https://www.middleeasteye.net/rss"},
    {"name": "Electronic Intifada", "url": "https://electronicintifada.net/rss.xml"},
    {"name": "Long War Journal",  "url": gn("site:longwarjournal.org+when:2d", GN_EN)},
    # General en español
    {"name": "El País",           "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada"},
    {"name": "France24 ES",       "url": "https://www.france24.com/es/rss"},
    {"name": "DW Español",        "url": "https://rss.dw.com/rdf/rss-sp-all"},
    {"name": "Infobae",           "url": "https://www.infobae.com/arc/outboundfeeds/rss/"},
    # Chile
    {"name": "La Tercera",        "url": "https://www.latercera.com/arc/outboundfeeds/rss/?outputType=xml", "cl": True},
    {"name": "Cooperativa",       "url": "https://www.cooperativa.cl/noticias/site/tax/port/all/rss_3___1.xml", "cl": True},
    {"name": "CIPER",             "url": "https://www.ciperchile.cl/feed/", "cl": True},
    {"name": "Radio UChile",      "url": "https://radio.uchile.cl/feed/", "cl": True},
    {"name": "El Ciudadano",      "url": "https://www.elciudadano.com/feed/", "cl": True},
    {"name": "Interferencia",     "url": "https://interferencia.cl/rss.xml", "cl": True},
    {"name": "El Siglo",          "url": "https://elsiglo.cl/feed/", "cl": True},
    {"name": "Ex-Ante",           "url": "https://www.ex-ante.cl/feed/", "cl": True},
    {"name": "The Clinic",        "url": "https://www.theclinic.cl/feed/", "cl": True},
    {"name": "Emol",              "url": gn(f"site:emol.com+{GN_TOPIC}+when:1d"), "cl": True},
    {"name": "BioBioChile",       "url": gn(f"site:biobiochile.cl+{GN_TOPIC}+when:1d"), "cl": True},
    # Búsquedas Chile (cualquier medio)
    {"name": "Google News",       "url": gn("(marcha+OR+convocatoria+OR+manifestaci%C3%B3n+OR+protesta)+(palestina+OR+gaza+OR+israel)+chile+when:1d"), "cl": True},
    {"name": "Google News",       "url": gn("(%22comunidad+palestina%22+OR+%22federaci%C3%B3n+palestina%22)+chile+when:1d"), "cl": True},
    {"name": "Google News",       "url": gn("(%22comunidad+jud%C3%ADa%22+OR+antisemitismo+OR+sinagoga)+chile+when:1d"), "cl": True},
]

# Una nota entra al resumen si calza con alguna palabra de CORE.
# Se compara sin tildes y por palabra completa; "*" al final = prefijo.
CORE = [
    # Israel y mundo judío
    "israel", "israeli*", "israelita*", "judio*", "judia*", "judaismo", "jewish", "jews", "judaism",
    "sinagoga*", "synagogue*", "antisemit*", "sionis*", "zionis*", "knesset", "netanyahu",
    "idf", "tsahal", "mossad", "shin bet", "jerusalem", "jerusalen", "tel aviv",
    "holocaust*", "holocausto", "shoa", "shoah", "kibutz*", "kibbutz*", "rabino*", "rabbi*",
    # Conflicto
    "palestin*", "gaza", "cisjordania", "west bank", "hamas", "hezbollah", "hezbola", "hizbola",
    "hizbulah", "hutie*", "huties", "houthi*", "yihad islamica", "islamic jihad", "intifada",
    "unrwa", "rafah", "ramallah", "jenin", "nablus", "golan", "cupula de hierro", "iron dome",
    # Terrorismo yihadista
    "isis", "estado islamico", "islamic state", "daesh", "al qaeda", "al-qaeda", "alqaeda",
    "boko haram", "al shabaab", "al-shabaab", "yihadis*", "jihadis*", "islamista*", "islamist*",
    "taliban*", "talibanes",
]

# Notas que calzan por error (personas, apellidos, etc.)
EXCLUDE = [
    "mauricio israel",
    "sponsored content", "contenido patrocinado",
]

# Sección del resumen: primera categoría que calce, en este orden.
CATEGORIES = [
    ("🇨🇱 Chile", ["chile", "chileno*", "chilena*", "la moneda", "valparaiso", "vina del mar"]),
    ("📢 Marchas y protestas", [
        "marcha*", "manifestacion*", "manifestante*", "protesta*", "convocatoria*", "acampada*",
        "boicot", "bds", "protest*", "rally", "rallies", "encampment*",
        "boycott*", "demonstration*", "demonstrator*", "protesters",
    ]),
    ("💣 Terrorismo y yihadismo", [
        "terror*", "atentado*", "yihad*", "jihad*", "isis", "daesh", "estado islamico",
        "islamic state", "al qaeda", "al-qaeda", "boko haram", "al shabaab", "al-shabaab",
        "islamist*", "islamista*", "taliban*",
    ]),
    ("✡️ Comunidades judías y antisemitismo", [
        "antisemit*", "sinagoga*", "synagogue*", "comunidad judia", "jewish community",
        "judaismo", "judaism", "rabino*", "rabbi*", "holocaust*", "holocausto", "shoa", "shoah",
        "jewish", "jews", "judio*", "judia*",
    ]),
    ("⚔️ Conflicto en Medio Oriente", [
        "gaza", "palestin*", "cisjordania", "west bank", "hamas", "hezbol*", "hizbol*",
        "hezbollah", "huti*", "houthi*", "libano", "lebanon", "iran*", "yemen", "siria", "syria",
        "rafah", "intifada", "unrwa", "idf", "tsahal", "rehen*", "hostage*",
    ]),
    ("🇮🇱 Israel", []),  # todo lo demás
]
