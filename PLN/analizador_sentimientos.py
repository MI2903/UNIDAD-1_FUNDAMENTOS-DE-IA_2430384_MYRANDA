"""
Analizador de sentimientos (PLN) basado en diccionarios y reglas
Fundamentos de Inteligencia Artificial

Qué hace:
  1. Normalización: convierte el texto a minúsculas y quita acentos.
  2. Tokenización: divide el texto en palabras individuales (tokens).
  3. Diccionarios: cada palabra clave tiene un puntaje (positivo o negativo).
  4. Reglas:
     - Negación: "no me gustó" invierte el puntaje de "gustó".
     - Intensificadores: "muy buena" pesa más que "buena".
     - Conectores de contraste:
         "pero", "sin embargo", "no obstante": lo que viene DESPUÉS pesa más.
         "aunque": lo que viene después del "aunque" pesa MENOS.
  5. Resultado: positivo, negativo o neutral, con porcentaje de confianza.

No usa librerías externas: solo Python.
"""

import re
import unicodedata

# ------------------------------------------------------------------
# DICCIONARIOS DE SENTIMIENTO (palabras sin acentos y en minúsculas)
# ------------------------------------------------------------------
POSITIVAS = {
    "excelente": 3, "increible": 3, "encanto": 3, "encanta": 3, "ame": 3,
    "amo": 3, "maravillosa": 3, "maravilloso": 3, "perfecta": 3, "perfecto": 3,
    "fantastica": 3, "fantastico": 3, "espectacular": 3,
    "genial": 2, "buena": 2, "bueno": 2, "buen": 2, "divertida": 2,
    "divertido": 2, "recomendable": 2, "recomiendo": 2, "gusto": 2,
    "gusta": 2, "feliz": 2, "emocionante": 2, "entretenida": 2,
    "entretenido": 2, "mejor": 2, "disfrute": 2, "hermosa": 2, "hermoso": 2,
    "interesante": 1, "bonita": 1, "bonito": 1, "agradable": 1, "facil": 1,
    "rapido": 1, "rapida": 1, "util": 1, "correcta": 1, "correcto": 1,
    "bien": 2, "chido": 2, "chida": 2, "padrisimo": 3, "padrisima": 3,
    "increiblemente": 2, "fascinante": 3, "fascino": 3, "encantadora": 2,
    "original": 1, "comico": 1, "comica": 1, "graciosa": 1, "gracioso": 1,
    "linda": 1, "lindo": 1, "satisfecho": 2, "satisfecha": 2, "adoro": 3,
}

NEGATIVAS = {
    "pesimo": -3, "pesima": -3, "horrible": -3, "odie": -3, "odio": -3,
    "terrible": -3, "decepcionante": -3, "malisima": -3, "malisimo": -3,
    "mala": -2, "malo": -2, "mal": -2, "aburrida": -2, "aburrido": -2,
    "evitaria": -2, "peor": -2, "molesta": -2, "molesto": -2, "fea": -2,
    "feo": -2, "decepciono": -2, "odioso": -2, "odiosa": -2,
    "triste": -1, "lenta": -1, "lento": -1, "larga": -1, "largo": -1,
    "dificil": -1, "confusa": -1, "confuso": -1, "predecible": -1,
    "floja": -1, "flojo": -1, "regular": -1,
    "basura": -3, "nefasto": -3, "nefasta": -3, "fatal": -3, "desastre": -3,
    "decepcion": -2, "insoportable": -3, "tedioso": -2, "tediosa": -2,
    "absurdo": -1, "absurda": -1, "cansado": -1, "cansada": -1,
    "perdida": -2, "mediocre": -2, "lamentable": -2, "odiar": -2,
}

# ------------------------------------------------------------------
# PALABRAS QUE ACTIVAN REGLAS
# ------------------------------------------------------------------
NEGADORES = {"no", "nunca", "jamas", "tampoco", "nada"}
INTENSIFICADORES = {"muy": 1.5, "super": 1.5, "bastante": 1.3, "demasiado": 1.5,
                    "tan": 1.3, "realmente": 1.5, "totalmente": 1.5, "sumamente": 1.5}
ATENUADORES = {"poco": 0.5, "algo": 0.7}
CONTRASTE_FUERTE = {"pero", "sin_embargo", "no_obstante", "sino"}  # lo de después pesa más
CONTRASTE_CONCESIVO = {"aunque"}                                     # lo de después pesa menos
SEPARADORES = {",", ";", ".", "!", "?"}

STOPWORDS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
             "y", "e", "o", "a", "al", "en", "que", "me", "te", "se", "lo", "le",
             "es", "son", "fue", "era", "con", "por", "para", "su", "sus", "mi",
             "mis", "este", "esta", "eso", "esa", "muy", "mas"}


# ------------------------------------------------------------------
# FASE 1: PREPARAR EL TEXTO
# ------------------------------------------------------------------
def normalizar(texto):
    """Minúsculas, sin acentos y une conectores de dos palabras."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("sin embargo", "sin_embargo")
    texto = texto.replace("no obstante", "no_obstante")
    return texto


def tokenizar(texto):
    """Divide el texto en palabras individuales (y conserva comas/puntos)."""
    return re.findall(r"[a-z_]+|[,;.!?]", texto)


def polaridad(palabra):
    """Busca la palabra en los diccionarios (también en plural)."""
    for candidata in (palabra, palabra[:-1], palabra[:-2]):
        if candidata in POSITIVAS:
            return POSITIVAS[candidata]
        if candidata in NEGATIVAS:
            return NEGATIVAS[candidata]
    return 0


# ------------------------------------------------------------------
# FASE 2: ANALIZAR
# ------------------------------------------------------------------
def dividir_en_segmentos(tokens):
    """Corta la oración en partes usando comas y conectores de contraste."""
    segmentos = []
    actual = {"conector": None, "tokens": []}
    for t in tokens:
        es_conector = t in CONTRASTE_FUERTE or t in CONTRASTE_CONCESIVO
        if t in SEPARADORES or es_conector:
            if actual["tokens"] or actual["conector"]:
                segmentos.append(actual)
            actual = {"conector": t if es_conector else None, "tokens": []}
        else:
            actual["tokens"].append(t)
    if actual["tokens"] or actual["conector"]:
        segmentos.append(actual)
    return segmentos


def calcular_pesos(segmentos):
    """Regla de los conectores de contraste."""
    pesos = [1.0] * len(segmentos)
    for i, seg in enumerate(segmentos):
        if seg["conector"] in CONTRASTE_FUERTE:
            for j in range(i):
                pesos[j] *= 0.5      # lo de antes del "pero" importa menos
            pesos[i] *= 1.5          # lo de después del "pero" importa más
        elif seg["conector"] in CONTRASTE_CONCESIVO:
            pesos[i] *= 0.5          # lo que dice el "aunque" importa menos
    return pesos


def analizar(texto):
    tokens = tokenizar(normalizar(texto))
    segmentos = dividir_en_segmentos(tokens)
    pesos = calcular_pesos(segmentos)

    detalle = []
    total = 0.0
    suma_pos = 0.0
    suma_neg = 0.0

    for seg, peso in zip(segmentos, pesos):
        toks = seg["tokens"]
        for k, t in enumerate(toks):
            base = polaridad(t)
            if base == 0:
                continue
            valor = float(base)
            notas = []

            # Regla de negación: busca "no", "nunca"... hasta 3 palabras antes
            if any(v in NEGADORES for v in toks[max(0, k - 3):k]):
                valor = -valor
                notas.append("negada")

            # Regla de intensidad: "muy", "un poco"... hasta 2 palabras antes
            for v in toks[max(0, k - 2):k]:
                if v in INTENSIFICADORES:
                    valor *= INTENSIFICADORES[v]
                    notas.append(f"intensificada por '{v}'")
                elif v in ATENUADORES:
                    valor *= ATENUADORES[v]
                    notas.append(f"atenuada por '{v}'")

            # Regla del conector de contraste
            if peso != 1.0:
                valor *= peso
                notas.append(f"peso x{peso:g} por conector '{seg['conector'] or 'previo'}'")

            total += valor
            if valor > 0:
                suma_pos += valor
            else:
                suma_neg += abs(valor)
            detalle.append((t, base, round(valor, 2), ", ".join(notas)))

    if total > 0.5:
        resultado = "POSITIVO"
    elif total < -0.5:
        resultado = "NEGATIVO"
    else:
        resultado = "NEUTRAL"

    if suma_pos + suma_neg > 0 and resultado != "NEUTRAL":
        confianza = max(suma_pos, suma_neg) / (suma_pos + suma_neg) * 100
    else:
        confianza = 0.0

    conectores = [s["conector"].replace("_", " ") for s in segmentos if s["conector"]]
    return {
        "tokens": [t for t in tokens if t not in SEPARADORES],
        "sin_stopwords": [t for t in tokens if t not in SEPARADORES and t not in STOPWORDS],
        "conectores": conectores,
        "detalle": detalle,
        "total": round(total, 2),
        "resultado": resultado,
        "confianza": round(confianza, 1),
    }


# ------------------------------------------------------------------
# PRESENTACIÓN DE RESULTADOS
# ------------------------------------------------------------------
def mostrar(r):
    print("\n1) Tokenización:")
    print("   ", r["tokens"])
    print("   Sin stopwords:", r["sin_stopwords"])

    print("\n2) Palabras clave encontradas (diccionario):")
    if not r["detalle"]:
        print("    Ninguna palabra con carga emocional.")
    for palabra, base, final, notas in r["detalle"]:
        tipo = "positiva" if base > 0 else "negativa"
        extra = f"  -> {notas}" if notas else ""
        print(f"    {palabra:<15} {tipo:<9} base {base:+}  final {final:+}{extra}")

    print("\n3) Conectores de contraste:",
          ", ".join(r["conectores"]) if r["conectores"] else "ninguno")

    print(f"\n4) Puntaje total: {r['total']:+}")
    emoji = {"POSITIVO": ":)", "NEGATIVO": ":(", "NEUTRAL": ":|"}[r["resultado"]]
    if r["resultado"] == "NEUTRAL":
        print(f"   RESULTADO: {r['resultado']} {emoji}")
    else:
        print(f"   RESULTADO: {r['resultado']} {emoji}  (confianza {r['confianza']}%)")
    print("-" * 60)


def main():
    print("=" * 60)
    print("   ANALIZADOR DE SENTIMIENTOS (PLN) - Diccionarios y reglas")
    print("=" * 60)
    print("Escribe una opinión y presiona Enter.")
    print("Escribe 'ejemplos' para ver frases de prueba o 'salir' para terminar.\n")

    ejemplos = [
        "La serie es excelente, me encantó",
        "La película fue aburrida y pésima",
        "La serie es buena pero muy aburrida",
        "Aunque es un poco larga, la recomiendo",
        "No me gustó para nada",
        "El episodio salió ayer",
    ]

    while True:
        texto = input("Opinión > ").strip()
        if not texto:
            continue
        if texto.lower() == "salir":
            print("¡Gracias!")
            break
        if texto.lower() == "ejemplos":
            for e in ejemplos:
                print(f'\nFrase: "{e}"')
                mostrar(analizar(e))
            continue
        mostrar(analizar(texto))


if __name__ == "__main__":
    main()
