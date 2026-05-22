from __future__ import annotations

from .normalizer import normalize_component_token

VERY_HIGH = {"MN3005", "MN3007", "SAD1024", "TDA1022", "CA3080", "LM308", "2SK170", "AC128", "OC44"}
HIGH = {"2SK30", "2SK117", "MN3207", "MN3205", "NE570", "NE571", "SA571", "J201", "MPF102", "2N5457"}
MEDIUM = {"PT2399", "CD4049", "CD4053", "CD4066", "LF356", "CA3130", "CA3140", "RC4558"}

AUDIO_USE = {
    "jfet": "buffers, phasers, chaveamento, pré-amplificadores de alta impedância",
    "germanio": "fuzzes, clipping vintage, diodos/transistores de baixa queda",
    "opamps_vintage": "distorções, filtros ativos, compressores e circuitos clássicos",
    "bbd_delay": "chorus, flanger, vibrato e delay analógico",
    "audio_geral": "utilidades gerais para pedais, modulação, delay, chaveamento ou controle",
}


def classify_priority(component: str) -> str:
    c = normalize_component_token(component)
    if c in VERY_HIGH:
        return "muito alta"
    if c in HIGH:
        return "alta"
    if c in MEDIUM:
        return "média"
    return "baixa"


def audio_use_for_category(category: str) -> str:
    return AUDIO_USE.get(category, "")
