"""
Motor de recomendación de fertilizantes en dos etapas.

    IMAGEN → YOLO → DIAGNÓSTICO VISUAL → CONFIANZA
      → HIPÓTESIS NUTRICIONAL
      → VALIDACIÓN AGRONÓMICA (análisis foliar / análisis de suelo / pH)
      → NECESIDAD NUTRICIONAL
      → COMPATIBILIDAD CON LA COMPOSICIÓN DE CADA PRODUCTO
      → PENALIZACIONES / EXCLUSIONES
      → DECISIÓN (puede ser NO recomendar)
      → PRODUCTO + IMAGEN + RAZONES

Principios:

- Una detección visual es una HIPÓTESIS ("posible deficiencia"), nunca
  una deficiencia confirmada.
- None significa "dato no disponible" y no participa en ninguna regla.
  Nunca se sustituye por 0 ni por un valor "típico".
- Temperatura, humedad y variedad son contexto: generan advertencias,
  no eligen productos.
- No se generan dosis.
- Todas las razones se construyen a partir de los datos reales usados.
"""

from django.conf import settings

from .catalogo_fertilizantes import (
    CATALOGO,
    MACRONUTRIENTES,
    MICRONUTRIENTES,
    NOMBRES_NUTRIENTES,
    NUTRIENTES,
    aporta,
    nutrientes_aportados,
    producto_por_clave_legacy,
    texto_composicion,
)


# ============================================================
# PARÁMETROS
# ============================================================

# Umbrales de confianza del MODELO (no son valores agronómicos).
# Coinciden con CONF_DIAGNOSTICO / MARGEN_DIAGNOSTICO de motor_yolo.py.
CONF_VISUAL_ALTA = 0.70
CONF_VISUAL_MEDIA = 0.50
CONF_VISUAL_MINIMA = 0.20
MARGEN_AMBIGUEDAD = 0.05

# Rangos críticos foliares del café (referencia diagnóstica, NO dosis).
# Fuente: especificación técnica del proyecto.
FUENTE_RANGOS_FOLIARES = "Rangos críticos foliares del café suministrados en la especificación del proyecto."
RANGOS_FOLIARES = {
    "N": (2.36, 2.78, "%"),
    "P": (0.14, 0.20, "%"),
    "K": (1.58, 2.15, "%"),
    "Ca": (0.75, 1.29, "%"),
    "Mg": (0.18, 0.45, "%"),
    "S": (0.15, 0.19, "%"),
    "Mn": (106, 278, "mg/kg"),
    "Fe": (54, 121, "mg/kg"),
    "B": (29, 55, "mg/kg"),
    "Cu": (8, 17, "mg/kg"),
    "Zn": (6, 12, "mg/kg"),
}

# pH: se conservan los umbrales que ya usaba el proyecto
# (recomendacion_general). El efecto cualitativo de la acidez
# (menor CICE, más Al intercambiable, menos bases) está descrito por
# Cenicafé, Avance Técnico "La acidez del suelo, una limitante común
# para la producción de café".
PH_ACIDO = 5.0
PH_ALTO = 6.5
FUENTE_PH = (
    "Umbrales de pH existentes en el proyecto (< 5.0 y > 6.5). Efecto de la "
    "acidez según Cenicafé, Avance Técnico 'La acidez del suelo, una limitante "
    "común para la producción de café'."
)

# Humedad del suelo y temperatura: umbrales que ya usaba el proyecto.
# Solo producen advertencias sobre la aplicación, nunca eligen producto.
HUMEDAD_SUELO_BAJA = 35
HUMEDAD_SUELO_ALTA = 80
TEMPERATURA_FRIA = 11

# Demanda asociada a la etapa: en producción el café extrae N y K en
# mayor cantidad (Cenicafé, Sadeghian: "Fertilidad del suelo y nutrición
# del café en Colombia"). Se usa solo como CONTEXTO de bajo peso.
DEMANDA_POR_ETAPA = {
    "Cosecha": ["N", "K"],
    "Mitaca": ["N", "K"],
}

ETAPAS_POR_TEMPORADA = {
    "Cosecha": ["llenado de fruto", "maduración"],
    "Mitaca": ["llenado de fruto", "maduración"],
    "Florescencia": ["prefloración", "floración", "cuajado"],
    "Recuperacion": ["postcosecha/recuperación", "desarrollo vegetativo"],
}

OBJETIVO_POR_TEMPORADA = {
    "Cosecha": "produccion",
    "Mitaca": "produccion",
    "Florescencia": "floracion",
    "Recuperacion": "recuperacion",
}

# Pesos de la necesidad y puntos de compatibilidad (explicables).
PESO_NECESIDAD = {"alta": 3.0, "media": 1.5, "contexto": 0.5}
PUNTOS_APORTE = 10
PUNTOS_CONCENTRACION = 4
PUNTOS_ETAPA = 10
PENALIZACION_ETAPA = 8
PUNTOS_OBJETIVO = 5
PUNTOS_FOLIAR = 5
PUNTOS_REGLA_LEGACY = 3
PUNTOS_LISTA_LEGACY = 2
PENALIZACION_EXCESO = 15
PENALIZACION_INNECESARIO = 10
PENALIZACION_ACIDIFICANTE = 8
PUNTOS_VIA_FOLIAR_PH_ALTO = 8

# Concentración a partir de la cual un macronutriente NO requerido se
# considera un aporte innecesario en exceso (% del grado).
CONCENTRACION_ALTA = 30

NOMBRES_OBJETIVO = {
    "produccion": "producción",
    "floracion": "floración",
    "recuperacion": "recuperación",
}

COMPATIBILIDAD_ALTA = 70
COMPATIBILIDAD_MEDIA = 45

MAX_EDAFICOS = 5
MAX_FOLIARES = 2

DOSIS_TEXTO = "Dosis: requiere recomendación técnica y/o análisis de suelo."

MENSAJE_SIN_EVIDENCIA = "No hay un fertilizante recomendado con suficiente evidencia."
MENSAJE_VALIDACION = (
    "Se recomienda realizar análisis de suelo y/o análisis foliar antes de "
    "seleccionar un fertilizante."
)

ENFERMEDADES = {"cercospora", "antracnosis", "phoma", "roya", "fumagina"}

NUTRIENTE_POR_PALABRA = {
    "azufre": "S", "boro": "B", "calcio": "Ca", "cobre": "Cu",
    "fosforo": "P", "fósforo": "P", "hierro": "Fe", "magnesio": "Mg",
    "manganeso": "Mn", "nitrogeno": "N", "nitrógeno": "N",
    "potasio": "K", "zinc": "Zn",
}


# ============================================================
# UTILIDADES
# ============================================================

def a_numero(valor):
    """Convierte a float. Vacío, texto inválido o None → None (nunca 0)."""

    if valor is None or isinstance(valor, bool):
        return None
    try:
        texto = str(valor).strip().replace(",", ".")
        if not texto:
            return None
        return float(texto)
    except (TypeError, ValueError):
        return None


def nutriente_desde_texto(texto):
    """'def_potasio' / 'Deficiencia de potasio' → 'K'."""

    texto = str(texto or "").lower().replace("_", " ").replace("-", " ")
    for palabra, nutriente in NUTRIENTE_POR_PALABRA.items():
        if palabra in texto:
            return nutriente
    return None


def nivel_visual(confianza):
    if confianza is None:
        return "desconocida"
    if confianza >= CONF_VISUAL_ALTA:
        return "alta"
    if confianza >= CONF_VISUAL_MEDIA:
        return "media"
    if confianza >= CONF_VISUAL_MINIMA:
        return "baja"
    return "no_concluyente"


def normalizar_confianza(valor):
    """Acepta 0–1 o 0–100 y devuelve 0–1 (o None)."""

    numero = a_numero(valor)
    if numero is None:
        return None
    return numero / 100 if numero > 1 else numero


def url_media(ruta):
    if not ruta:
        return None
    return f"{settings.MEDIA_URL.rstrip('/')}/{ruta.lstrip('/')}"


def resolver_imagen(producto):
    """
    Imagen del producto:
    1. Imagen principal del TipoAbono enlazado en la BD (si el archivo existe),
       para que el administrador pueda cambiarla desde el panel.
    2. Imagen registrada en el catálogo.
    """

    nombre_bd = producto.get("nombre_bd")
    if nombre_bd:
        try:
            from .models import TipoAbono

            tipo = TipoAbono.objects.filter(nombre=nombre_bd).first()
            if tipo:
                img = (
                    tipo.imagenes.filter(es_principal=True).first()
                    or tipo.imagenes.first()
                )
                if img and img.imagen and img.imagen.storage.exists(img.imagen.name):
                    return img.imagen.url
        except Exception:
            pass

    return url_media(producto.get("imagen"))


def absolutizar_imagenes(datos, request):
    """Convierte las rutas /media/... de la respuesta en URLs absolutas."""

    if request is None or datos is None:
        return datos

    def convertir(valor):
        if isinstance(valor, str) and valor.startswith(settings.MEDIA_URL):
            return request.build_absolute_uri(valor)
        return valor

    def recorrer(obj):
        if isinstance(obj, dict):
            for clave, valor in obj.items():
                if clave in ("imagen", "url", "imagen_principal"):
                    obj[clave] = convertir(valor)
                else:
                    recorrer(valor)
        elif isinstance(obj, list):
            for item in obj:
                recorrer(item)

    recorrer(datos)
    return datos


# ============================================================
# 1. DIAGNÓSTICO VISUAL
# ============================================================

def interpretar_diagnostico(diagnostico):
    diagnostico = diagnostico or {}

    clase = str(diagnostico.get("clase") or "").strip().lower()
    etiqueta = str(
        diagnostico.get("etiqueta") or diagnostico.get("diagnostico") or ""
    ).strip()
    estado = diagnostico.get("estado") or diagnostico.get("status")
    confianza = normalizar_confianza(diagnostico.get("confianza"))

    texto = f"{clase} {etiqueta}".lower()

    if not clase and not etiqueta:
        tipo = "sin_diagnostico"
    elif "no concluyente" in texto:
        tipo = "no_concluyente"
    elif estado == "deficiency" or clase.startswith("def_"):
        tipo = "deficiencia"
    elif estado == "healthy" or "sana" in texto:
        tipo = "sana"
    elif any(e in texto for e in ENFERMEDADES) or estado == "alert":
        tipo = "enfermedad"
    else:
        tipo = "no_concluyente"

    secundarias = []
    for d in diagnostico.get("detecciones_secundarias") or []:
        conf = normalizar_confianza(d.get("confianza"))
        clase_sec = str(d.get("clase") or "").lower()
        if conf is None or conf < CONF_VISUAL_MINIMA:
            continue
        secundarias.append({
            "clase": clase_sec,
            "nutriente": nutriente_desde_texto(clase_sec) if clase_sec.startswith("def_") else None,
            "enfermedad": any(e in clase_sec for e in ENFERMEDADES),
            "sana": "sana" in clase_sec,
            "confianza": conf,
        })

    return {
        "tipo": tipo,
        "clase": clase or None,
        "etiqueta": etiqueta,
        "confianza": confianza,
        "confianza_porcentaje": round(confianza * 100) if confianza is not None else None,
        "nivel_visual": nivel_visual(confianza) if tipo != "no_concluyente" else "no_concluyente",
        "ambiguo": bool(diagnostico.get("ambiguo")),
        "nutriente": nutriente_desde_texto(clase or etiqueta) if tipo == "deficiencia" else None,
        "secundarias": secundarias,
    }


# ============================================================
# 2. DATOS AGRONÓMICOS
# ============================================================

def leer_analisis_foliar(analisis):
    """{'K': 1.2, ...} → {'K': {'valor', 'minimo', 'maximo', 'unidad', 'estado'}}"""

    resultado = {}
    for nutriente, (minimo, maximo, unidad) in RANGOS_FOLIARES.items():
        valor = a_numero((analisis or {}).get(nutriente))
        if valor is None:
            continue
        if valor < minimo:
            estado = "bajo"
        elif valor > maximo:
            estado = "alto"
        else:
            estado = "adecuado"
        resultado[nutriente] = {
            "valor": valor, "minimo": minimo, "maximo": maximo,
            "unidad": unidad, "estado": estado,
        }
    return resultado


CAMPOS_SUELO = ["ph", "materia_organica", "P", "K", "Ca", "Mg", "Al",
                "saturacion_al", "cice", "humedad"]


def leer_analisis_suelo(analisis):
    analisis = analisis or {}
    datos = {}
    for campo in CAMPOS_SUELO:
        valor = a_numero(analisis.get(campo))
        if valor is not None:
            datos[campo] = valor
    textura = str(analisis.get("textura") or "").strip()
    if textura:
        datos["textura"] = textura
    return datos


# ============================================================
# 3. MOTOR
# ============================================================

def recomendar(diagnostico=None, contexto=None):
    from .recomendador import (
        PRODUCTOS_POR_DEFICIENCIA,
        REGLAS_ABONOS,
        normalizar_clima,
        normalizar_nombre_abono,
        normalizar_temporada,
        normalizar_variedad,
    )

    contexto = contexto or {}
    visual = interpretar_diagnostico(diagnostico)

    temporada = normalizar_temporada(contexto.get("temporada"))
    variedad = normalizar_variedad(contexto.get("variedad"))
    clima = normalizar_clima(contexto.get("condicion_climatica"))

    foliar = leer_analisis_foliar(contexto.get("analisis_foliar"))
    suelo = leer_analisis_suelo(contexto.get("analisis_suelo"))

    ph_sensor = a_numero(contexto.get("ph"))
    ph = suelo.get("ph", ph_sensor)
    ph_origen = (
        "análisis de suelo" if "ph" in suelo
        else (contexto.get("fuente_datos") or "sensores") if ph_sensor is not None
        else None
    )
    humedad_suelo = suelo.get("humedad", a_numero(contexto.get("humedad")))
    temperatura = a_numero(contexto.get("temperatura"))

    etapas = ETAPAS_POR_TEMPORADA.get(temporada, [])
    objetivo = OBJETIVO_POR_TEMPORADA.get(temporada)

    advertencias = []
    datos_faltantes = []

    if ph is None:
        datos_faltantes.append("pH")
    if humedad_suelo is None:
        datos_faltantes.append("humedad del suelo")
    if temperatura is None:
        datos_faltantes.append("temperatura")
    if not suelo:
        datos_faltantes.append("análisis de suelo")
    if not foliar:
        datos_faltantes.append("análisis foliar")

    # --------------------------------------------------------
    # pH (mayor peso que temperatura y humedad)
    # --------------------------------------------------------

    evaluacion_ph = None
    if ph is not None:
        if ph < PH_ACIDO:
            evaluacion_ph = "acido"
            advertencias.append(
                f"pH {ph:g} ({ph_origen}): suelo ácido. La acidez reduce la retención "
                "de nutrientes y aumenta el aluminio intercambiable; evalúe la "
                "corrección de acidez con un análisis de suelo antes de fertilizar."
            )
        elif ph > PH_ALTO:
            evaluacion_ph = "alto"
            advertencias.append(
                f"pH {ph:g} ({ph_origen}): elevado para café. La disponibilidad de "
                "micronutrientes (Fe, Mn, Zn, B, Cu) puede disminuir."
            )
        else:
            evaluacion_ph = "dentro_de_rango"

    # Humedad del suelo y temperatura: solo advertencias de aplicación.
    if humedad_suelo is not None and humedad_suelo < HUMEDAD_SUELO_BAJA:
        advertencias.append(
            f"Humedad del suelo {humedad_suelo:g} %: baja. Evite aplicar fertilizantes "
            "al suelo hasta que haya humedad suficiente."
        )
    elif humedad_suelo is not None and humedad_suelo > HUMEDAD_SUELO_ALTA:
        advertencias.append(
            f"Humedad del suelo {humedad_suelo:g} %: elevada. Verifique drenaje; "
            "hay riesgo de pérdidas por lavado."
        )
    if temperatura is not None and temperatura <= TEMPERATURA_FRIA:
        advertencias.append(
            f"Temperatura {temperatura:g} °C: la absorción de nutrientes puede ser más lenta."
        )
    if clima == "lluviosa":
        advertencias.append("Condición lluviosa: fraccione las aplicaciones edáficas para reducir pérdidas.")
    elif clima == "seca":
        advertencias.append("Condición seca: aplique al suelo solo cuando exista humedad suficiente.")

    # --------------------------------------------------------
    # HIPÓTESIS NUTRICIONAL
    # --------------------------------------------------------

    hipotesis = []
    motivos_no = []

    if visual["tipo"] == "deficiencia" and visual["nutriente"]:
        hipotesis.append({
            "nutriente": visual["nutriente"],
            "nombre": NOMBRES_NUTRIENTES[visual["nutriente"]],
            "rol": "primaria",
            "origen": "visual",
            "confianza_visual": visual["confianza_porcentaje"],
        })
        for sec in visual["secundarias"]:
            if sec["nutriente"] and sec["nutriente"] != visual["nutriente"]:
                if any(h["nutriente"] == sec["nutriente"] for h in hipotesis):
                    continue
                hipotesis.append({
                    "nutriente": sec["nutriente"],
                    "nombre": NOMBRES_NUTRIENTES[sec["nutriente"]],
                    "rol": "secundaria",
                    "origen": "visual",
                    "confianza_visual": round(sec["confianza"] * 100),
                })

    # Validación con análisis foliar
    for h in hipotesis:
        dato = foliar.get(h["nutriente"])
        if dato is None:
            h["estado"] = "probable" if (
                h["rol"] == "primaria" and visual["nivel_visual"] in ("alta", "media")
            ) else "posible"
            h["validacion"] = "Sin análisis foliar para este nutriente: solo evidencia visual."
        elif dato["estado"] == "bajo":
            h["estado"] = "confirmado"
            h["validacion"] = (
                f"Análisis foliar {dato['valor']:g} {dato['unidad']} por debajo del rango "
                f"crítico {dato['minimo']:g}–{dato['maximo']:g} {dato['unidad']}."
            )
        else:
            h["estado"] = "descartado"
            h["validacion"] = (
                f"Análisis foliar {dato['valor']:g} {dato['unidad']} "
                f"({'dentro' if dato['estado'] == 'adecuado' else 'por encima'} del rango "
                f"crítico {dato['minimo']:g}–{dato['maximo']:g} {dato['unidad']}): "
                "no respalda la deficiencia visual."
            )

    # Nutrientes deficientes por laboratorio sin síntoma visual asociado
    for nutriente, dato in foliar.items():
        if dato["estado"] == "bajo" and not any(h["nutriente"] == nutriente for h in hipotesis):
            hipotesis.append({
                "nutriente": nutriente,
                "nombre": NOMBRES_NUTRIENTES[nutriente],
                "rol": "laboratorio",
                "origen": "análisis foliar",
                "confianza_visual": None,
                "estado": "confirmado",
                "validacion": (
                    f"Análisis foliar {dato['valor']:g} {dato['unidad']} por debajo del rango "
                    f"crítico {dato['minimo']:g}–{dato['maximo']:g} {dato['unidad']}."
                ),
            })

    # --------------------------------------------------------
    # NIVEL DE CONFIANZA (ALTA / MEDIA / BAJA / NO CONCLUYENTE)
    # --------------------------------------------------------

    primaria = next((h for h in hipotesis if h["rol"] == "primaria"), None)
    hay_dato_agronomico = bool(foliar or suelo or ph is not None)
    info_suficiente = bool(foliar or suelo)

    # Otra deficiencia con confianza casi igual, o una detección de hoja
    # sana igual o más confiable que la deficiencia: evidencia ambigua.
    secundaria_cercana = visual["confianza"] is not None and any(
        (
            s["nutriente"] and s["nutriente"] != visual["nutriente"]
            and abs(visual["confianza"] - s["confianza"]) < MARGEN_AMBIGUEDAD
        )
        or (
            s["sana"] and visual["tipo"] == "deficiencia"
            and s["confianza"] >= visual["confianza"] - MARGEN_AMBIGUEDAD
        )
        for s in visual["secundarias"]
    )

    if visual["tipo"] in ("no_concluyente",) or visual["nivel_visual"] == "no_concluyente":
        nivel = "NO CONCLUYENTE"
        motivos_no.append("La confianza del modelo es insuficiente o el diagnóstico no es concluyente.")
    elif visual["ambiguo"] or secundaria_cercana:
        nivel = "NO CONCLUYENTE"
        motivos_no.append("Hay varios diagnósticos posibles con confianza similar (síntomas ambiguos).")
    elif primaria and primaria["estado"] == "confirmado":
        nivel = "ALTA" if visual["nivel_visual"] in ("alta", "media") else "MEDIA"
    elif primaria and primaria["estado"] == "descartado":
        nivel = "BAJA"
        motivos_no.append("El análisis foliar no respalda la deficiencia observada en la imagen.")
    elif primaria:
        if hay_dato_agronomico and visual["nivel_visual"] in ("alta", "media"):
            nivel = "MEDIA"
        else:
            nivel = "BAJA"
    elif any(h["rol"] == "laboratorio" for h in hipotesis):
        nivel = "MEDIA"
    else:
        nivel = "BAJA" if visual["tipo"] != "sin_diagnostico" else "NO CONCLUYENTE"

    # --------------------------------------------------------
    # NECESIDAD NUTRICIONAL
    # --------------------------------------------------------

    necesidad = {n: {"nivel": "sin_evidencia", "motivo": "Sin evidencia."} for n in NUTRIENTES}

    for nutriente, dato in foliar.items():
        if dato["estado"] == "adecuado":
            necesidad[nutriente] = {"nivel": "normal", "motivo": "Análisis foliar dentro del rango crítico."}
        elif dato["estado"] == "alto":
            necesidad[nutriente] = {"nivel": "exceso", "motivo": "Análisis foliar por encima del rango crítico."}

    for h in hipotesis:
        if h["estado"] == "descartado":
            continue
        if h["estado"] == "confirmado" or (h["rol"] == "primaria" and h["estado"] == "probable"):
            nivel_n = "alta"
        else:
            nivel_n = "media"
        necesidad[h["nutriente"]] = {
            "nivel": nivel_n,
            "motivo": f"{h['estado'].capitalize()} ({h['origen']}).",
        }

    for nutriente in DEMANDA_POR_ETAPA.get(temporada, []):
        if necesidad[nutriente]["nivel"] == "sin_evidencia":
            necesidad[nutriente] = {
                "nivel": "contexto",
                "motivo": f"Demanda asociada a la etapa ({', '.join(etapas)}); no es una deficiencia.",
            }

    requeridos = {n: v["nivel"] for n, v in necesidad.items() if v["nivel"] in PESO_NECESIDAD}
    principales = [n for n, nv in requeridos.items() if nv in ("alta", "media")]

    # --------------------------------------------------------
    # DECISIÓN: ¿HAY EVIDENCIA PARA RECOMENDAR?
    # --------------------------------------------------------

    puede_recomendar = True

    if visual["tipo"] == "enfermedad":
        puede_recomendar = False
        motivos_no.append(
            "Se detectó una posible enfermedad: la fertilización no sustituye el "
            "manejo fitosanitario y no se recomienda un fertilizante específico."
        )
    if visual["tipo"] == "deficiencia" and any(s["enfermedad"] for s in visual["secundarias"]):
        puede_recomendar = False
        motivos_no.append("Existe también posibilidad de enfermedad en la imagen.")
    if nivel in ("NO CONCLUYENTE", "BAJA"):
        puede_recomendar = False
        if nivel == "BAJA" and not motivos_no:
            motivos_no.append("Solo existe evidencia visual; no hay datos agronómicos que la validen.")
    if nivel == "MEDIA" and not info_suficiente:
        puede_recomendar = False
        motivos_no.append(
            "Información agronómica insuficiente: el pH o los sensores no confirman "
            "una deficiencia nutricional."
        )
    if not principales:
        puede_recomendar = False
        if visual["tipo"] in ("sana", "sin_diagnostico"):
            motivos_no.append(
                "No se identificó una necesidad nutricional específica. Mantenga el plan "
                "de fertilización basado en el análisis de suelo."
            )
        elif not motivos_no:
            motivos_no.append("No se pudo establecer una necesidad nutricional.")

    # --------------------------------------------------------
    # COMPATIBILIDAD DE CADA PRODUCTO
    # --------------------------------------------------------

    reglas_coincidentes = set()
    if None not in (ph, humedad_suelo, temperatura):
        for regla in REGLAS_ABONOS:
            try:
                if regla["condicion"](ph, humedad_suelo, temperatura, temporada):
                    reglas_coincidentes.add(normalizar_nombre_abono(regla["nombre"]).lower())
            except Exception:
                continue

    listados_legacy = set()
    if visual["clase"] and visual["clase"].startswith("def_"):
        listados_legacy = {
            normalizar_nombre_abono(n).lower()
            for n in PRODUCTOS_POR_DEFICIENCIA.get(visual["clase"], [])
        }

    maximos = {
        n: max((p[n] or 0) for p in CATALOGO if p["composicion_confirmada"]) or 1
        for n in NUTRIENTES
    }

    evaluados = []
    excluidos = []

    for producto in CATALOGO:
        evaluacion = evaluar_producto(
            producto, requeridos, principales, foliar, etapas, objetivo,
            evaluacion_ph, maximos, reglas_coincidentes, listados_legacy,
        )
        if evaluacion.get("excluido"):
            excluidos.append({
                "producto": ficha_producto(producto),
                "motivo": evaluacion["motivo"],
            })
        else:
            evaluados.append(evaluacion)

    evaluados.sort(key=lambda e: (-e["puntuacion"], e["producto"]["nombre"]))

    edaficos = [e for e in evaluados if e["producto"]["tipo"] == "edafico"
                and e["puntuacion"] >= COMPATIBILIDAD_MEDIA][:MAX_EDAFICOS]
    foliares = [e for e in evaluados if e["producto"]["tipo"] == "foliar"
                and e["puntuacion"] >= COMPATIBILIDAD_MEDIA][:MAX_FOLIARES]

    if puede_recomendar and not (edaficos or foliares):
        puede_recomendar = False
        sin_producto = [
            NOMBRES_NUTRIENTES[n] for n in principales
            if not any(aporta(p, n) for p in CATALOGO if p["composicion_confirmada"])
        ]
        if sin_producto:
            motivos_no.append(
                "Ningún producto del catálogo con composición confirmada aporta: "
                + ", ".join(sin_producto) + "."
            )
        else:
            motivos_no.append("Ningún producto alcanzó una compatibilidad suficiente con la necesidad detectada.")

    if not puede_recomendar:
        edaficos, foliares = [], []

    for posicion, item in enumerate(edaficos + foliares, start=1):
        item["orden"] = posicion

    # Capa adicional: si la recomendación agronómica no alcanza, pero hay
    # una deficiencia visual válida, se ofrece una recomendación preliminar.
    visual_preliminar = (
        None if puede_recomendar
        else recomendar_visual(visual, hipotesis, etapas, objetivo, maximos)
    )

    return {
        "version": 2,
        "diagnostico_visual": {
            "tipo": visual["tipo"],
            "clase": visual["clase"],
            "etiqueta": visual["etiqueta"],
            "descripcion": describir_diagnostico(visual),
            "confianza_visual": visual["confianza_porcentaje"],
            "nivel_visual": visual["nivel_visual"],
            "ambiguo": visual["ambiguo"] or secundaria_cercana,
        },
        "nivel_confianza": nivel,
        "hipotesis_nutricional": hipotesis,
        "validacion": {
            "analisis_foliar": foliar or None,
            "analisis_suelo": suelo or None,
            "ph": ph,
            "ph_origen": ph_origen,
            "evaluacion_ph": evaluacion_ph,
            "humedad_suelo": humedad_suelo,
            "temperatura": temperatura,
            "condicion_climatica": clima,
            "informacion_suficiente": info_suficiente,
            "resumen": resumir_validacion(foliar, suelo, ph, ph_origen),
            "fuentes": {
                "rangos_foliares": FUENTE_RANGOS_FOLIARES,
                "ph": FUENTE_PH,
            },
        },
        "necesidad_nutricional": [
            {"nutriente": n, "nombre": NOMBRES_NUTRIENTES[n], **necesidad[n]}
            for n in NUTRIENTES if necesidad[n]["nivel"] != "sin_evidencia"
        ],
        "contexto": {
            "temporada": temporada,
            "etapas_fisiologicas": etapas,
            "variedad": variedad or None,
            "variedad_nota": (
                f"La variedad {variedad} se registra como contexto; no modifica la "
                "puntuación porque no hay un efecto nutricional documentado en el sistema."
            ) if variedad else None,
        },
        "decision": "recomendar" if puede_recomendar else "no_recomendar",
        "mensaje": (
            "Mayor compatibilidad con las necesidades detectadas."
            if puede_recomendar
            else MENSAJE_SIN_EVIDENCIA
        ),
        "motivos_no_recomendacion": [] if puede_recomendar else motivos_no,
        "recomendacion_validacion": None if puede_recomendar and nivel == "ALTA" else MENSAJE_VALIDACION,
        "productos_recomendados": edaficos,
        "recomendaciones_foliares": foliares,
        "productos_excluidos": excluidos,
        "recomendacion_visual": visual_preliminar,
        "advertencias": advertencias,
        "datos_faltantes": datos_faltantes,
        "dosis": DOSIS_TEXTO,
    }


# ============================================================
# RECOMENDACIÓN VISUAL PRELIMINAR (FALLBACK)
# ============================================================
#
# IMAGEN → YOLO → DEFICIENCIA → NUTRIENTE → CATÁLOGO → PRODUCTOS QUE
# APORTAN EL NUTRIENTE → COMPATIBILIDAD → ORDEN → PRODUCTO + IMAGEN
#
# Solo se usa cuando la recomendación agronómica decidió no recomendar
# (faltan datos de suelo/foliares) y YOLO detectó al menos una deficiencia
# válida. No reemplaza a la agronómica: se devuelve en una clave aparte y
# siempre marcada como preliminar. Nunca asocia un fertilizante con una
# enfermedad: solo con las deficiencias detectadas.

TIPO_VISUAL = "visual_preliminar"
TIPO_APOYO = "apoyo_nutricional_preliminar"

TITULO_VISUAL = "Recomendación nutricional preliminar basada en diagnóstico visual."
TITULO_APOYO = "Apoyo nutricional preliminar"

ADVERTENCIA_VISUAL = (
    "Recomendación preliminar basada únicamente en diagnóstico visual. Se "
    "recomienda validar mediante análisis de suelo o análisis foliar."
)
MENSAJE_SIN_PRODUCTO_VISUAL = (
    "No se encontraron abonos del catálogo que aporten directamente el "
    "nutriente detectado."
)
MENSAJE_VALIDAR_DEFICIENCIA = (
    "Se recomienda validar la deficiencia mediante análisis de suelo o análisis foliar."
)

# Pesos y puntos de la priorización visual (suman 100).
PESO_VISUAL_PRIMARIA = 2.0
PESO_VISUAL_SECUNDARIA = 1.0
PUNTOS_VISUAL_COBERTURA = 60
PUNTOS_VISUAL_CONCENTRACION = 20
PUNTOS_VISUAL_ETAPA = 15
PUNTOS_VISUAL_ETAPA_SIN_DATO = 7
PUNTOS_VISUAL_AMPLITUD = 5


def nutrientes_deficiencia_visual(visual, hipotesis):
    """
    Nutrientes de las deficiencias detectadas por YOLO (principal y
    secundarias), en orden. Se omiten los que un análisis foliar descartó.
    """

    descartados = {h["nutriente"] for h in hipotesis if h.get("estado") == "descartado"}
    detectados = []

    confianza = visual["confianza"]
    if (
        visual["tipo"] == "deficiencia" and visual["nutriente"]
        and (confianza is None or confianza >= CONF_VISUAL_MINIMA)
    ):
        detectados.append({
            "nutriente": visual["nutriente"],
            "nombre": NOMBRES_NUTRIENTES[visual["nutriente"]],
            "rol": "principal",
            "confianza_visual": visual["confianza_porcentaje"],
        })

    for sec in visual["secundarias"]:
        n = sec["nutriente"]
        if n and not any(d["nutriente"] == n for d in detectados):
            detectados.append({
                "nutriente": n,
                "nombre": NOMBRES_NUTRIENTES[n],
                "rol": "secundaria",
                "confianza_visual": round(sec["confianza"] * 100),
            })

    return [d for d in detectados if d["nutriente"] not in descartados]


def recomendar_visual(visual, hipotesis, etapas, objetivo, maximos):
    detectados = nutrientes_deficiencia_visual(visual, hipotesis)
    if not detectados:
        return None

    hay_enfermedad = visual["tipo"] == "enfermedad" or any(
        s["enfermedad"] for s in visual["secundarias"]
    )
    pesos = {
        d["nutriente"]: PESO_VISUAL_PRIMARIA if d["rol"] == "principal" else PESO_VISUAL_SECUNDARIA
        for d in detectados
    }

    evaluados = [
        e for e in (
            evaluar_producto_visual(p, pesos, etapas, objetivo, maximos, hay_enfermedad)
            for p in CATALOGO
        ) if e
    ]
    evaluados.sort(key=lambda e: (-e["puntuacion"], e["producto"]["nombre"]))

    edaficos = [e for e in evaluados if e["producto"]["tipo"] == "edafico"][:MAX_EDAFICOS]
    foliares = [e for e in evaluados if e["producto"]["tipo"] == "foliar"][:MAX_FOLIARES]
    for posicion, item in enumerate(edaficos + foliares, start=1):
        item["orden"] = posicion

    con_producto = {n for e in edaficos + foliares for n in e["nutrientes_detectados"]}
    sin_producto = [d for d in detectados if d["nutriente"] not in con_producto]

    nota_enfermedad = None
    if hay_enfermedad:
        enfermedad = visual["etiqueta"] if visual["tipo"] == "enfermedad" else next(
            (s["clase"] for s in visual["secundarias"] if s["enfermedad"]), "la enfermedad"
        )
        nota_enfermedad = (
            f"Estos abonos no tratan ni controlan {enfermedad}. Son apoyo nutricional "
            "para la deficiencia detectada; la enfermedad requiere manejo fitosanitario."
        )

    return {
        "tipo_recomendacion": TIPO_APOYO if hay_enfermedad else TIPO_VISUAL,
        "titulo": TITULO_APOYO if hay_enfermedad else TITULO_VISUAL,
        "diagnostico_principal": describir_diagnostico(visual),
        "nutrientes_detectados": detectados,
        "productos": edaficos,
        "foliares": foliares,
        "nutrientes_sin_producto": sin_producto,
        "mensaje_sin_producto": (
            MENSAJE_SIN_PRODUCTO_VISUAL
            + " (" + ", ".join(d["nombre"] for d in sin_producto) + ")."
        ) if sin_producto else None,
        "advertencia": ADVERTENCIA_VISUAL,
        "recomendacion_validacion": MENSAJE_VALIDAR_DEFICIENCIA,
        "nota_enfermedad": nota_enfermedad,
        "dosis": DOSIS_TEXTO,
    }


def evaluar_producto_visual(producto, pesos, etapas, objetivo, maximos, hay_enfermedad):
    # Solo productos del catálogo con composición confirmada.
    if not producto["composicion_confirmada"]:
        return None

    es_foliar = producto["tipo"] == "foliar"
    considerados = {
        n: p for n, p in pesos.items()
        if not es_foliar or n in MICRONUTRIENTES or n == "Ca"
    }
    cubiertos = [n for n in considerados if aporta(producto, n)]
    if not cubiertos:
        return None

    razones = []
    advertencias = []

    # 1-2. Aporte directo y cobertura de varias deficiencias
    cobertura = sum(considerados[n] for n in cubiertos) / sum(considerados.values())
    puntos = PUNTOS_VISUAL_COBERTURA * cobertura
    nombres = ", ".join(NOMBRES_NUTRIENTES[n] for n in cubiertos)
    razones.append(f"Aporta directamente {nombres}, asociado a la deficiencia detectada visualmente.")
    if len(pesos) > 1:
        razones.append(f"Cubre {len(cubiertos)} de {len(pesos)} nutrientes detectados.")

    # Concentración de los nutrientes cubiertos
    concentraciones = []
    for n in cubiertos:
        valor = producto.get(n)
        if valor:
            concentraciones.append(min(1.0, valor / maximos[n]))
        else:
            concentraciones.append(0.0)
            advertencias.append(f"Contiene {NOMBRES_NUTRIENTES[n]}, pero la cantidad no está registrada.")
    puntos += PUNTOS_VISUAL_CONCENTRACION * (sum(concentraciones) / len(concentraciones))

    # 4. Etapa del cultivo (si está disponible)
    if producto["etapas"] and etapas:
        comunes = [e for e in producto["etapas"] if e in etapas]
        if comunes:
            puntos += PUNTOS_VISUAL_ETAPA
            razones.append(f"Compatible con la etapa ({', '.join(comunes)}).")
        else:
            advertencias.append(
                f"Su uso descrito es para {', '.join(producto['etapas'])}, no para la etapa actual."
            )
    else:
        puntos += PUNTOS_VISUAL_ETAPA_SIN_DATO

    # 5. Cobertura nutricional general
    aportados = nutrientes_aportados(producto)
    puntos += PUNTOS_VISUAL_AMPLITUD * len(aportados) / len(NUTRIENTES)

    # Macronutriente muy concentrado que no corresponde a ninguna deficiencia
    for n in aportados:
        if n in MACRONUTRIENTES and n not in pesos and (producto.get(n) or 0) >= CONCENTRACION_ALTA:
            puntos -= PENALIZACION_INNECESARIO
            advertencias.append(
                f"Aporta {NOMBRES_NUTRIENTES[n]} en alta concentración ({producto[n]:g}) "
                "sin deficiencia detectada."
            )

    if es_foliar:
        advertencias.append("Producto de aplicación foliar.")

    puntuacion = max(0, min(100, round(puntos)))
    compatibilidad = (
        "alta" if puntuacion >= COMPATIBILIDAD_ALTA
        else "media" if puntuacion >= COMPATIBILIDAD_MEDIA
        else "baja"
    )
    tipo_recomendacion = TIPO_APOYO if hay_enfermedad else TIPO_VISUAL
    ficha = ficha_producto(producto)
    motivo = (
        f"Aporta {', '.join(cubiertos)}: nutrientes asociados a las deficiencias "
        "detectadas visualmente."
    )

    return {
        # Estructura común con las tarjetas agronómicas
        "producto": ficha,
        "compatibilidad": compatibilidad,
        "puntuacion": puntuacion,
        "nutrientes_requeridos": list(considerados),
        "nutrientes_aportados": aportados,
        "nutrientes_cubiertos": cubiertos,
        "razones": razones,
        "advertencias": advertencias,
        "dosis": DOSIS_TEXTO,

        # Campos de la recomendación visual preliminar
        "id": ficha["id"],
        "nombre": ficha["nombre"],
        "marca": ficha["marca"],
        "imagen": ficha["imagen"],
        "tipo": ficha["tipo"],
        "composicion": ficha["composicion"],
        "nutrientes_objetivo": aportados,
        "nutrientes_detectados": cubiertos,
        "score": puntuacion,
        "tipo_recomendacion": tipo_recomendacion,
        "motivo": motivo,
        "advertencia": ADVERTENCIA_VISUAL,
    }


# ============================================================
# EVALUACIÓN DE UN PRODUCTO
# ============================================================

def ficha_producto(producto):
    return {
        "id": producto["id"],
        "nombre": producto["nombre"],
        "marca": producto["marca"],
        "imagen": resolver_imagen(producto),
        "imagenes_alternativas": [url_media(i) for i in producto["imagenes_alternativas"]],
        "composicion": texto_composicion(producto),
        "tipo": producto["tipo"],
        "categorias": producto["categorias"],
        "composicion_confirmada": producto["composicion_confirmada"],
        "nutrientes": {n: producto[n] for n in NUTRIENTES},
        "presentes_sin_cantidad": producto["presentes_sin_cantidad"],
        "etapas": producto["etapas"],
        "objetivos": producto["objetivos"],
        "observaciones": producto["observaciones"],
        "fuente": producto["fuente"],
    }


def evaluar_producto(producto, requeridos, principales, foliar, etapas, objetivo,
                     evaluacion_ph, maximos, reglas_coincidentes, listados_legacy):

    if not producto["composicion_confirmada"]:
        return {"excluido": True, "motivo": "Composición no confirmada."}

    if not principales:
        return {"excluido": True, "motivo": "No hay una necesidad nutricional que cubrir."}

    es_foliar = producto["tipo"] == "foliar"

    # Los foliares solo se evalúan para Ca y micronutrientes; los edáficos
    # para todo. Así CaBtrac no compite con los granulados.
    nutrientes_objetivo = (
        [n for n in principales if n in MICRONUTRIENTES or n == "Ca"]
        if es_foliar else principales
    )
    if es_foliar and not nutrientes_objetivo:
        return {"excluido": True, "motivo": "Producto foliar: la necesidad detectada es de macronutrientes edáficos."}

    cubiertos = [n for n in nutrientes_objetivo if aporta(producto, n)]
    if not cubiertos:
        faltan = ", ".join(NOMBRES_NUTRIENTES[n] for n in nutrientes_objetivo)
        return {"excluido": True, "motivo": f"No aporta el nutriente requerido ({faltan})."}

    razones = []
    advertencias = []
    puntos = 0.0
    maximo = 0.0

    considerados = {n: v for n, v in requeridos.items() if not es_foliar or n in nutrientes_objetivo}

    for nutriente, nivel in considerados.items():
        peso = PESO_NECESIDAD[nivel]
        maximo += peso * (PUNTOS_APORTE + PUNTOS_CONCENTRACION)
        nombre = NOMBRES_NUTRIENTES[nutriente]

        if not aporta(producto, nutriente):
            if nivel in ("alta", "media"):
                advertencias.append(f"No aporta {nombre}.")
            continue

        puntos += peso * PUNTOS_APORTE
        valor = producto.get(nutriente)
        if valor:
            puntos += peso * PUNTOS_CONCENTRACION * min(1.0, valor / maximos[nutriente])

        if nivel == "contexto":
            razones.append(f"Aporta {nombre}, demandado en esta etapa.")
        else:
            razones.append(f"Existe necesidad de {nombre} ({nivel}) y el producto lo aporta.")
            if valor is None:
                advertencias.append(f"Contiene {nombre}, pero la cantidad no está registrada.")

    # Confirmación por análisis foliar
    for nutriente in cubiertos:
        if foliar.get(nutriente, {}).get("estado") == "bajo":
            puntos += PUNTOS_FOLIAR
            razones.append(f"El análisis foliar confirma la necesidad de {NOMBRES_NUTRIENTES[nutriente]}.")
    maximo += PUNTOS_FOLIAR * sum(1 for n in nutrientes_objetivo if foliar.get(n, {}).get("estado") == "bajo")

    # Etapa fisiológica
    maximo += PUNTOS_ETAPA
    if producto["etapas"] and etapas:
        comunes = [e for e in producto["etapas"] if e in etapas]
        if comunes:
            puntos += PUNTOS_ETAPA
            razones.append(f"Compatible con la etapa ({', '.join(comunes)}).")
        else:
            puntos -= PENALIZACION_ETAPA
            advertencias.append(
                f"Su uso descrito es para {', '.join(producto['etapas'])}, no para la etapa actual."
            )

    # Objetivo
    maximo += PUNTOS_OBJETIVO
    if objetivo and objetivo in producto["objetivos"]:
        puntos += PUNTOS_OBJETIVO
        razones.append(f"Su objetivo de {NOMBRES_OBJETIVO.get(objetivo, objetivo)} coincide con la etapa.")

    # Excesos y nutrientes innecesarios
    for nutriente in nutrientes_aportados(producto):
        if foliar.get(nutriente, {}).get("estado") == "alto":
            puntos -= PENALIZACION_EXCESO
            advertencias.append(
                f"Aporta {NOMBRES_NUTRIENTES[nutriente]}, que el análisis foliar muestra por encima del rango."
            )
        elif (
            nutriente in MACRONUTRIENTES
            and nutriente not in requeridos
            and (producto.get(nutriente) or 0) >= CONCENTRACION_ALTA
        ):
            puntos -= PENALIZACION_INNECESARIO
            advertencias.append(
                f"Aporta {NOMBRES_NUTRIENTES[nutriente]} en alta concentración "
                f"({producto[nutriente]:g}) sin necesidad detectada."
            )

    # pH
    if evaluacion_ph == "acido" and producto["efecto_acidificante"] == "alto" and not es_foliar:
        puntos -= PENALIZACION_ACIDIFICANTE
        advertencias.append("Fuente de reacción ácida en un suelo que ya presenta pH ácido.")
    if evaluacion_ph == "alto" and any(n in MICRONUTRIENTES for n in cubiertos):
        if es_foliar:
            puntos += PUNTOS_VIA_FOLIAR_PH_ALTO
            maximo += PUNTOS_VIA_FOLIAR_PH_ALTO
            razones.append("La vía foliar evita la baja disponibilidad de micronutrientes en suelos de pH alto.")
        else:
            advertencias.append("Con pH alto los micronutrientes aplicados al suelo pueden quedar poco disponibles.")

    # Reglas anteriores del proyecto como factores secundarios
    clave = (producto["clave_legacy"] or "").lower()
    if clave and clave in reglas_coincidentes:
        puntos += PUNTOS_REGLA_LEGACY
        razones.append("Coincide con la regla de referencia del proyecto para la etapa, pH, humedad y temperatura (factor secundario).")
    if clave and clave in listados_legacy:
        puntos += PUNTOS_LISTA_LEGACY
        razones.append("Figura en la lista de referencia del proyecto para esta deficiencia (factor secundario).")
    maximo += PUNTOS_REGLA_LEGACY + PUNTOS_LISTA_LEGACY

    puntuacion = max(0, min(100, round(100 * puntos / maximo))) if maximo else 0

    if puntuacion >= COMPATIBILIDAD_ALTA:
        compatibilidad = "alta"
    elif puntuacion >= COMPATIBILIDAD_MEDIA:
        compatibilidad = "media"
    else:
        compatibilidad = "baja"

    return {
        "producto": ficha_producto(producto),
        "compatibilidad": compatibilidad,
        "puntuacion": puntuacion,
        "nutrientes_requeridos": [n for n in nutrientes_objetivo],
        "nutrientes_aportados": nutrientes_aportados(producto),
        "nutrientes_cubiertos": cubiertos,
        "razones": razones,
        "advertencias": advertencias,
        "dosis": DOSIS_TEXTO,
    }


# ============================================================
# TEXTOS
# ============================================================

def describir_diagnostico(visual):
    tipo = visual["tipo"]
    if tipo == "deficiencia" and visual["nutriente"]:
        return f"Posible deficiencia de {NOMBRES_NUTRIENTES[visual['nutriente']]}"
    if tipo == "enfermedad":
        return f"Posible enfermedad: {visual['etiqueta'] or visual['clase']}"
    if tipo == "sana":
        return "Hoja sin síntomas detectados"
    if tipo == "sin_diagnostico":
        return "Sin diagnóstico visual"
    return "Resultado no concluyente"


def resumir_validacion(foliar, suelo, ph, ph_origen):
    partes = []
    if foliar:
        partes.append(f"análisis foliar ({len(foliar)} nutrientes)")
    if suelo:
        partes.append(f"análisis de suelo ({len(suelo)} variables)")
    if ph is not None and "ph" not in suelo:
        partes.append(f"pH {ph:g} ({ph_origen})")
    if not partes:
        return "Sin datos agronómicos: solo evidencia visual."
    return "Datos agronómicos disponibles: " + ", ".join(partes) + "."


def productos_formato_legacy(recomendacion):
    """
    Adapta los productos al formato que ya consumían el frontend y el PDF
    (nombre, formula, nutrientes, razon...), conservando la estructura nueva.
    """

    salida = []
    for item in (recomendacion.get("productos_recomendados") or []) + (
        recomendacion.get("recomendaciones_foliares") or []
    ):
        p = item["producto"]
        salida.append({
            **item,
            "nombre": p["nombre"],
            "formula": p["composicion"],
            "nutrientes": ", ".join(item["nutrientes_aportados"]),
            "aplicacion": "Foliar" if p["tipo"] == "foliar" else "Al suelo",
            "descripcion": p["observaciones"] or None,
            "uso": ", ".join(p["etapas"]) or None,
            "imagen": p["imagen"],
            "imagenes": [{"url": p["imagen"], "es_principal": True}] if p["imagen"] else [],
            "prioridad": item.get("orden"),
            "nivel_recomendacion": f"Compatibilidad {item['compatibilidad']}",
            "puntaje": item["puntuacion"],
            "razon": " ".join(item["razones"]),
            "porQueSeRecomienda": " ".join(item["razones"]),
        })
    return salida
