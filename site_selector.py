import re
from datetime import datetime
import os

SITE_KEYWORDS = {
    "mindat.org": ["mineral", "cristal", "roca", "piedra", "meteorito", "geoda", "geología"],
    "imdb.com": ["película", "serie", "temporada", "actor", "actriz", "cine", "director", "episodio"],
    "justwatch.com": ["dónde ver", "streaming", "ver online", "ver serie", "ver película"],
    "youtube.com": ["video", "youtube", "canal", "youtuber", "último video"],
    "goodreads.com": ["libro", "novela", "autor", "lectura", "escritor"],
    "genius.com": ["letra", "canción", "artista", "álbum", "música"],
    "wolframalpha.com": ["resolver", "fórmula", "ecuación", "matemática", "cálculo", "operación"],
    "symbolab.com": ["derivada", "integral", "logaritmo", "ecuación", "simplificar"],
    "wikipedia.org": ["qué es", "definición", "significado", "historia de", "explicación"],
    "amazon.com": ["comprar", "precio", "oferta", "producto", "tienda", "dólares"],
    "mercadolibre.com": ["mercadolibre", "comprar en argentina", "envío gratis", "cuotas"]
}

def smart_site_selector(query: str) -> str | None:
    query_lower = query.lower()

    for site, keywords in SITE_KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", query_lower):
                full_url = f"https://{site}"
                return full_url
    return None
