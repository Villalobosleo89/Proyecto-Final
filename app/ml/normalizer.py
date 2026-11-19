import unicodedata
import re

def normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto clínico:
    - Unicode NFC
    - Eliminación de diacríticos (acentos)
    - Reemplazo de espacios y tabulaciones múltiples por un solo espacio
    - Reducción de saltos de línea consecutivos
    """
    if not texto:
        return ""
    # Normalización NFC
    texto_nfc = unicodedata.normalize('NFC', texto)
    # Eliminar diacríticos (acentos)
    texto_nfd = unicodedata.normalize('NFD', texto_nfc)
    texto_sin_acentos = ''.join(c for c in texto_nfd if not unicodedata.combining(c))
    # Reemplazo de espacios/tabulaciones múltiples
    texto_limpio = re.sub(r'[ \t]+', ' ', texto_sin_acentos)
    # Reducir saltos de línea repetidos
    texto_limpio = re.sub(r'\n+', '\n', texto_limpio)
    return texto_limpio.strip()

def validar_rango_longitud(texto: str, min_len: int = 30, max_len: int = 10000) -> bool:
    longitud = len(texto.strip()) if texto else 0
    return min_len <= longitud <= max_len