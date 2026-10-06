import logging
from pathlib import Path

from ultralytics import YOLO

from tablas.recomendador import (
    construir_sugerencia_integrada,
)

logger = logging.getLogger(__name__)


# ============================================================
# RUTA DEL MODELO ENTRENADO
# ============================================================

RUTA_PESOS = (
    Path(__file__).resolve().parent
    / "modelos"
    / "best.pt"
)


# ============================================================
# CONFIGURACIÓN DEL MODELO
# ============================================================

MODELO_LISTO = True

# YOLO empieza buscando detecciones desde 5%.
CONF_MIN = 0.05

# Confianza mínima para aceptar un diagnóstico.
CONF_DIAGNOSTICO = 0.20

# Diferencia mínima entre diagnósticos posibles.
MARGEN_DIAGNOSTICO = 0.05


# ============================================================
# MODELO EN MEMORIA
# ============================================================

_modelo = None


# ============================================================
# CARGAR MODELO
# ============================================================

def cargar_modelo():
    """
    Carga el modelo YOLO entrenado una sola vez.
    """

    global _modelo

    if _modelo is None:

        if not RUTA_PESOS.exists():
            raise FileNotFoundError(
                f"No se encontró el modelo YOLO en: {RUTA_PESOS}"
            )

        _modelo = YOLO(str(RUTA_PESOS))

    return _modelo


# ============================================================
# INFORMACIÓN DE LAS CLASES
# ============================================================

INFO_CLASES = {

    # ========================================================
    # ENFERMEDADES
    # ========================================================

    "cercospora": {
        "tipo": "enfermedad",
        "diagnostico": "Cercospora",
        "scientificName": "Cercospora coffeicola",
        "recommendation": (
            "Se recomienda realizar monitoreo frecuente de las hojas, "
            "mejorar la ventilación del cultivo, retirar material vegetal "
            "muy afectado y aplicar un manejo fitosanitario adecuado."
        ),
    },

    "cercospora_1": {
        "tipo": "enfermedad",
        "diagnostico": "Cercospora",
        "scientificName": "Cercospora coffeicola",
        "recommendation": (
            "Se recomienda realizar monitoreo frecuente de las hojas, "
            "mejorar la ventilación del cultivo, retirar material vegetal "
            "muy afectado y aplicar un manejo fitosanitario adecuado."
        ),
    },

    "antracnosis": {
        "tipo": "enfermedad",
        "diagnostico": "Antracnosis",
        "scientificName": "Colletotrichum spp.",
        "recommendation": (
            "Se recomienda retirar material vegetal afectado, mejorar "
            "la ventilación del cultivo y realizar un manejo preventivo "
            "de la enfermedad."
        ),
    },

    "phoma": {
        "tipo": "enfermedad",
        "diagnostico": "Phoma",
        "scientificName": "Phoma spp.",
        "recommendation": (
            "Se recomienda monitorear las hojas afectadas, retirar "
            "material vegetal severamente afectado y mantener buenas "
            "condiciones de ventilación del cultivo."
        ),
    },

    "roya": {
        "tipo": "enfermedad",
        "diagnostico": "Roya del café",
        "scientificName": "Hemileia vastatrix",
        "recommendation": (
            "Se recomienda realizar monitoreo periódico del cultivo, "
            "retirar material severamente afectado y aplicar un programa "
            "de manejo fitosanitario de acuerdo con las recomendaciones "
            "técnicas para el cultivo."
        ),
    },

    "fumagina": {
        "tipo": "enfermedad",
        "diagnostico": "Fumagina",
        "scientificName": "Capnodium spp.",
        "recommendation": (
            "Se recomienda identificar y controlar los insectos que "
            "producen mielecilla, además de realizar monitoreo y manejo "
            "adecuado de la planta."
        ),
    },

    # ========================================================
    # HOJA SANA
    # ========================================================

    "hoja_sana": {
        "tipo": "sana",
        "diagnostico": "Hoja sana",
        "scientificName": "No aplica",
        "recommendation": (
            "La hoja no presenta una detección asociada a las clases "
            "de enfermedad o deficiencia evaluadas por el modelo. "
            "Se recomienda continuar con el monitoreo del cultivo."
        ),
    },

    # ========================================================
    # DEFICIENCIAS NUTRICIONALES
    # ========================================================

    "def_azufre": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de azufre",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda verificar las condiciones nutricionales "
            "del suelo y realizar un análisis antes de aplicar fertilizantes."
        ),
    },

    "def_boro": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de boro",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda realizar análisis de suelo y tejido vegetal "
            "antes de establecer una corrección nutricional."
        ),
    },

    "def_calcio": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de calcio",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda verificar el pH y realizar análisis de suelo "
            "para determinar la estrategia de corrección nutricional."
        ),
    },

    "def_cobre": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de cobre",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda confirmar la deficiencia mediante análisis "
            "de suelo o tejido vegetal antes de aplicar correctivos."
        ),
    },

    "def_fosforo": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de fósforo",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda realizar análisis de suelo y ajustar la "
            "fertilización de acuerdo con las necesidades del cultivo."
        ),
    },

    "def_hierro": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de hierro",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda verificar el pH del suelo y confirmar "
            "la deficiencia mediante análisis antes de realizar "
            "una corrección nutricional."
        ),
    },

    "def_magnesio": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de magnesio",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda realizar análisis de suelo y tejido vegetal "
            "para confirmar la deficiencia y determinar el manejo adecuado."
        ),
    },

    "def_manganeso": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de manganeso",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda confirmar la deficiencia mediante análisis "
            "de suelo o tejido vegetal antes de aplicar correctivos."
        ),
    },

    "def_nitrogeno": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de nitrógeno",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda realizar análisis de suelo y ajustar "
            "la fertilización nitrogenada según las necesidades del cultivo."
        ),
    },

    "def_potasio": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de potasio",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda realizar análisis de suelo y tejido vegetal "
            "para determinar la necesidad de corrección de potasio."
        ),
    },

    "def_zinc": {
        "tipo": "deficiencia",
        "diagnostico": "Posible deficiencia de zinc",
        "scientificName": "No aplica",
        "recommendation": (
            "Se recomienda confirmar la deficiencia mediante análisis "
            "antes de realizar una aplicación de zinc."
        ),
    },
}


# ============================================================
# NORMALIZAR NOMBRE DE CLASE
# ============================================================

def normalizar_clase(nombre):
    """
    Convierte el nombre de la clase a un formato uniforme.
    """

    return (
        str(nombre)
        .strip()
        .lower()
    )


# ============================================================
# OBTENER INFORMACIÓN DE UNA CLASE
# ============================================================

def obtener_info_clase(
    clase,
    nombre_original=None
):
    """
    Obtiene la información asociada a una clase YOLO.
    """

    clase = normalizar_clase(clase)

    info = INFO_CLASES.get(clase)

    if info is not None:
        return info

    return {
        "tipo": "enfermedad",
        "diagnostico": (
            nombre_original
            or clase
        ),
        "scientificName": "No disponible",
        "recommendation": (
            "Se recomienda realizar una revisión visual y "
            "confirmar el diagnóstico con un técnico agrícola."
        ),
    }


# ============================================================
# NORMALIZAR CONTEXTO
# ============================================================

def normalizar_contexto(contexto=None):
    """
    Normaliza el contexto enviado desde Angular.

    IMPORTANTE:
    No contiene finca.

    El diagnóstico funciona únicamente con:

    - variedad
    - temporada
    - sensores
    - fechas
    - condición climática
    - valores de sensores
    """

    if contexto is None:
        contexto = {}

    usar_sensores = contexto.get(
        "usar_sensores"
    )

    if usar_sensores is None:
        usar_sensores = True

    contexto_normalizado = {

        "variedad":
            contexto.get("variedad"),

        "temporada":
            contexto.get(
                "temporada",
                "cosecha"
            ),

        "usar_sensores":
            bool(usar_sensores),

        "desde":
            contexto.get("desde"),

        "hasta":
            contexto.get("hasta"),

        "condicion_climatica":
            contexto.get(
                "condicion_climatica"
            ),

        # ---------------------------------------------
        # DATOS DE SENSORES
        # ---------------------------------------------

        "ph":
            contexto.get("ph"),

        "humedad":
            contexto.get("humedad"),

        "temperatura":
            contexto.get("temperatura"),

        # ---------------------------------------------
        # ORIGEN DE LOS DATOS Y ANÁLISIS DE LABORATORIO
        # ---------------------------------------------

        "fuente_datos":
            contexto.get("fuente_datos"),

        "analisis_suelo":
            contexto.get("analisis_suelo"),

        "analisis_foliar":
            contexto.get("analisis_foliar"),
    }

    return contexto_normalizado


# ============================================================
# AGREGAR CONTEXTO AL RESULTADO
# ============================================================

def agregar_contexto(
    resultado,
    contexto=None
):
    """
    Agrega al resultado de YOLO el contexto seleccionado
    por el usuario en Angular.

    NO se solicita finca aquí.
    """

    contexto = normalizar_contexto(
        contexto
    )

    resultado["contexto"] = {

        "variedad":
            contexto.get("variedad"),

        "temporada":
            contexto.get("temporada"),

        "usar_sensores":
            contexto.get("usar_sensores"),

        "desde":
            contexto.get("desde"),

        "hasta":
            contexto.get("hasta"),

        "condicion_climatica":
            contexto.get(
                "condicion_climatica"
            ),

        "ph":
            contexto.get("ph"),

        "humedad":
            contexto.get("humedad"),

        "temperatura":
            contexto.get("temperatura"),
    }

    return resultado


# ============================================================
# RESULTADO NO CONCLUYENTE
# ============================================================

def resultado_no_concluyente(
    bounding_boxes,
    mensaje=None,
    contexto=None
):
    """
    Respuesta utilizada cuando no existe suficiente evidencia
    para establecer un diagnóstico.
    """

    if mensaje is None:

        mensaje = (
            "El modelo encontró posibles características en la hoja, "
            "pero ninguna detección alcanzó el nivel de confianza "
            "necesario para establecer un diagnóstico principal. "
            "Se recomienda realizar otra captura con buena iluminación "
            "y enfocando claramente la hoja."
        )

    resultado = {

        "status":
            "alert",

        "diagnosis":
            "Resultado no concluyente",

        "scientificName":
            "No aplica",

        "recommendation":
            mensaje,

        "source":
            "Modelo YOLO entrenado",

        "boundingBoxes":
            [],

        "sugerencia_integrada":
            None,

        "abono":
            None,

        "abonos":
            [],

        "productos_recomendados":
            [],

        "texto_sugerencia":
            mensaje,

        "tratamiento":
            mensaje,
    }

    sugerencia = construir_sugerencia_diagnostico(
        {
            "estado": "alert",
            "etiqueta": "Resultado no concluyente",
            "clase": None,
            "confianza": None,
        },
        contexto,
    )

    if sugerencia and not sugerencia.get("error"):

        resultado["sugerencia_integrada"] = sugerencia

        resultado["recomendacion_fertilizacion"] = (
            sugerencia.get("recomendacion")
        )

    return agregar_contexto(
        resultado,
        contexto
    )


# ============================================================
# CONSTRUIR SUGERENCIA INTEGRADA
# ============================================================

def construir_sugerencia_diagnostico(
    diagnostico,
    contexto=None,
    abonos=None,
):
    """
    Conecta el diagnóstico de YOLO con el recomendador.

    El recomendador determina hasta 3 productos teniendo
    en cuenta:

    1. Enfermedad o deficiencia detectada.
    2. Temporada.
    3. Variedad.
    4. Condición climática.
    5. Sensores cuando están disponibles.
    6. Condición con sensores o sin sensores.

    NO utiliza finca.
    """

    contexto = normalizar_contexto(
        contexto
    )

    if abonos is None:
        abonos = []

    if not diagnostico:
        return None

    estado = (
        diagnostico.get("estado")
        or diagnostico.get("status")
        or "alert"
    )

    etiqueta = (
        diagnostico.get("etiqueta")
        or diagnostico.get("diagnostico")
        or diagnostico.get("diagnosis")
        or ""
    )

    temporada = contexto.get(
        "temporada"
    )

    variedad = contexto.get(
        "variedad"
    )

    usar_sensores = contexto.get(
        "usar_sensores"
    )

    condicion_climatica = contexto.get(
        "condicion_climatica"
    )

    ph = contexto.get(
        "ph"
    )

    humedad = contexto.get(
        "humedad"
    )

    temperatura = contexto.get(
        "temperatura"
    )

    try:

        return construir_sugerencia_integrada(

            ph=ph,

            humedad=humedad,

            temperatura=temperatura,

            temporada=temporada,

            abonos=abonos,

            diagnostico={

                "estado":
                    estado,

                "etiqueta":
                    etiqueta,

                "diagnostico":
                    etiqueta,

                # Evidencia visual para el motor en dos etapas
                "clase":
                    diagnostico.get("clase"),

                "confianza":
                    diagnostico.get("confianza"),

                "ambiguo":
                    diagnostico.get("ambiguo", False),

                "detecciones_secundarias":
                    diagnostico.get("detecciones_secundarias", []),
            },

            variedad=variedad,

            usar_sensores=usar_sensores,

            condicion_climatica=condicion_climatica,

            analisis_suelo=contexto.get("analisis_suelo"),

            analisis_foliar=contexto.get("analisis_foliar"),

            fuente_datos=contexto.get("fuente_datos"),
        )

    except Exception:

        # El detalle técnico queda en el registro del servidor, no en la
        # respuesta (podría revelar rutas o estructura interna).
        logger.exception("No se pudo construir la recomendación integrada")

        return {

            "error":
                True,

            "mensaje": (
                "El diagnóstico de la IA fue obtenido correctamente, "
                "pero no fue posible construir la recomendación integrada."
            ),
        }


# ============================================================
# CREAR RESPUESTA DE DIAGNÓSTICO
# ============================================================

def crear_diagnostico(
    deteccion,
    bounding_boxes,
    contexto=None,
    ambiguo=False,
    otras_detecciones=None,
):
    """
    Construye la respuesta final para el frontend.

    El diagnóstico final es uno solo.

    Después del diagnóstico se generan hasta 3 recomendaciones
    de abonos dependiendo del contexto.
    """

    contexto = normalizar_contexto(
        contexto
    )

    info = deteccion["info"]

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    if info["tipo"] == "deficiencia":

        estado = "deficiency"

    elif info["tipo"] == "sana":

        estado = "healthy"

    else:

        estado = "alert"

    # --------------------------------------------------------
    # CLASE GANADORA
    # --------------------------------------------------------

    clase_ganadora = normalizar_clase(
        deteccion["clase"]
    )

    # --------------------------------------------------------
    # CONSERVAR SOLO LA CAJA DEL DIAGNÓSTICO GANADOR
    # --------------------------------------------------------

    cajas_ganadoras = [

        box

        for box in bounding_boxes

        if normalizar_clase(
            box["label"]
        ) == clase_ganadora
    ]

    if cajas_ganadoras:

        caja_principal = max(

            cajas_ganadoras,

            key=lambda box:
                box.get(
                    "confidence",
                    0
                )
        )

        bounding_boxes_finales = [
            caja_principal
        ]

    else:

        bounding_boxes_finales = []

    # --------------------------------------------------------
    # DIAGNÓSTICO BASE
    # --------------------------------------------------------

    resultado = {

        "status":
            estado,

        "diagnosis":
            info["diagnostico"],

        "scientificName":
            info["scientificName"],

        "recommendation":
            info["recommendation"],

        "source":
            "Modelo YOLO entrenado",

        "boundingBoxes":
            bounding_boxes_finales,

        "sugerencia_integrada":
            None,

        "abono":
            None,

        "abonos":
            [],

        "productos_recomendados":
            [],

        "texto_sugerencia":
            None,

        "tratamiento":
            info["recommendation"],
    }

    # --------------------------------------------------------
    # AGREGAR CONTEXTO
    # --------------------------------------------------------

    resultado = agregar_contexto(
        resultado,
        contexto
    )

    # --------------------------------------------------------
    # DIAGNÓSTICO PARA EL RECOMENDADOR
    # --------------------------------------------------------

    diagnostico_contexto = {

        "estado":
            estado,

        "etiqueta":
            info["diagnostico"],

        "diagnostico":
            info["diagnostico"],

        # La confianza de YOLO y las demás clases detectadas
        # permiten al recomendador distinguir entre evidencia
        # fuerte, débil o ambigua.
        "clase":
            clase_ganadora,

        "confianza":
            deteccion.get("confianza"),

        "ambiguo":
            ambiguo,

        "detecciones_secundarias": [
            {
                "clase": d["clase"],
                "confianza": d["confianza"],
            }
            for d in (otras_detecciones or [])
            if d["clase"] != clase_ganadora
        ],
    }

    resultado["confianza"] = round(
        deteccion.get("confianza", 0) * 100
    )

    # --------------------------------------------------------
    # GENERAR RECOMENDACIÓN
    # --------------------------------------------------------

    sugerencia = (
        construir_sugerencia_diagnostico(

            diagnostico_contexto,

            contexto,

            [],
        )
    )

    resultado[
        "sugerencia_integrada"
    ] = sugerencia

    # --------------------------------------------------------
    # COPIAR INFORMACIÓN AL NIVEL PRINCIPAL
    # --------------------------------------------------------

    if (
        sugerencia
        and not sugerencia.get("error")
    ):

        resultado["abono"] = (
            sugerencia.get(
                "abono"
            )
        )

        resultado["abonos"] = (
            sugerencia.get(
                "abonos",
                []
            )
        )

        resultado[
            "productos_recomendados"
        ] = (
            sugerencia.get(
                "productos_recomendados",
                sugerencia.get(
                    "abonos",
                    []
                )
            )
        )

        resultado[
            "texto_sugerencia"
        ] = (
            sugerencia.get(
                "texto"
            )
        )

        resultado[
            "tratamiento"
        ] = (
            sugerencia.get(
                "tratamiento"
            )
            or info["recommendation"]
        )

        # ----------------------------------------------------
        # INFORMACIÓN DE LOS 3 ABONOS
        # ----------------------------------------------------

        productos = resultado[
            "productos_recomendados"
        ]

        if len(productos) > 0:

            resultado[
                "abono_principal"
            ] = productos[0]

        if len(productos) > 1:

            resultado[
                "segundo_abono"
            ] = productos[1]

        if len(productos) > 2:

            resultado[
                "tercer_abono"
            ] = productos[2]

        resultado[
            "cantidad_recomendados"
        ] = len(productos)

        resultado[
            "recomendacion_fertilizacion"
        ] = sugerencia.get(
            "recomendacion"
        )

    else:

        resultado[
            "abono"
        ] = None

        resultado[
            "abonos"
        ] = []

        resultado[
            "productos_recomendados"
        ] = []

        resultado[
            "cantidad_recomendados"
        ] = 0

        resultado[
            "texto_sugerencia"
        ] = info[
            "recommendation"
        ]

        resultado[
            "tratamiento"
        ] = info[
            "recommendation"
        ]

    return resultado


# ============================================================
# ANALIZAR IMAGEN
# ============================================================

def analizar_imagen(
    ruta_imagen: str,
    contexto=None
) -> dict:
    """
    Ejecuta YOLO sobre una imagen y devuelve el diagnóstico.

    contexto puede contener:

        {
            "variedad": "caturra",
            "temporada": "cosecha",

            "usar_sensores": True,

            "desde": "2026-08-01",
            "hasta": "2026-08-14",

            "ph": 5.4,
            "humedad": 60,
            "temperatura": 21,

            "condicion_climatica": "lluviosa"
        }

    CON SENSORES:

        usar_sensores = True

        Se utilizan:

        - pH
        - humedad
        - temperatura
        - temporada
        - variedad

    SIN SENSORES:

        usar_sensores = False

        Se utiliza:

        - condición climática
        - temporada
        - variedad

    NO se solicita finca.
    """

    # ========================================================
    # NORMALIZAR CONTEXTO
    # ========================================================

    contexto = normalizar_contexto(
        contexto
    )

    # ========================================================
    # VERIFICAR MODELO
    # ========================================================

    if not MODELO_LISTO:

        raise RuntimeError(
            "El modelo YOLO no está habilitado."
        )

    modelo = cargar_modelo()

    # ========================================================
    # VERIFICAR IMAGEN
    # ========================================================

    ruta = Path(
        ruta_imagen
    )

    if not ruta.exists():

        raise FileNotFoundError(
            f"No se encontró la imagen para analizar: "
            f"{ruta_imagen}"
        )

    # ========================================================
    # EJECUTAR YOLO
    # ========================================================

    resultados = modelo.predict(

        source=str(ruta),

        conf=CONF_MIN,

        save=False,

        verbose=False,
    )

    if not resultados:

        return resultado_no_concluyente(
            [],
            contexto=contexto
        )

    resultado = resultados[0]

    # ========================================================
    # VARIABLES
    # ========================================================

    bounding_boxes = []

    detecciones = []

    # ========================================================
    # PROCESAR DETECCIONES
    # ========================================================

    if resultado.boxes is not None:

        imagen_ancho = (
            resultado.orig_shape[1]
        )

        imagen_alto = (
            resultado.orig_shape[0]
        )

        for box in resultado.boxes:

            clase_id = int(
                box.cls[0]
            )

            confianza = float(
                box.conf[0]
            )

            nombre_clase = (
                modelo.names[
                    clase_id
                ]
            )

            clase_normalizada = (
                normalizar_clase(
                    nombre_clase
                )
            )

            # ------------------------------------------------
            # COORDENADAS
            # ------------------------------------------------

            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )

            x = (
                x1 / imagen_ancho
            ) * 100

            y = (
                y1 / imagen_alto
            ) * 100

            width = (
                (x2 - x1)
                / imagen_ancho
            ) * 100

            height = (
                (y2 - y1)
                / imagen_alto
            ) * 100

            # ------------------------------------------------
            # BOUNDING BOX
            # ------------------------------------------------

            bounding_boxes.append({

                "label":
                    nombre_clase,

                "confidence":
                    round(
                        confianza * 100
                    ),

                "x":
                    round(
                        x,
                        2
                    ),

                "y":
                    round(
                        y,
                        2
                    ),

                "width":
                    round(
                        width,
                        2
                    ),

                "height":
                    round(
                        height,
                        2
                    ),
            })

            # ------------------------------------------------
            # DETECCIÓN
            # ------------------------------------------------

            detecciones.append({

                "clase":
                    clase_normalizada,

                "nombre":
                    nombre_clase,

                "confianza":
                    confianza,

                "box": {

                    "x":
                        x,

                    "y":
                        y,

                    "width":
                        width,

                    "height":
                        height,
                },
            })

    # ========================================================
    # NO HAY DETECCIONES
    # ========================================================

    if not detecciones:

        return resultado_no_concluyente(

            bounding_boxes,

            (
                "El modelo no encontró detecciones suficientes "
                "para establecer un diagnóstico. Se recomienda "
                "realizar otra captura con buena iluminación y "
                "enfocando claramente la hoja."
            ),

            contexto
        )

    # ========================================================
    # AGRUPAR POR CLASE
    # ========================================================

    mejores_por_clase = {}

    for deteccion in detecciones:

        clase = deteccion[
            "clase"
        ]

        if (

            clase not in
            mejores_por_clase

            or

            deteccion[
                "confianza"
            ]

            >

            mejores_por_clase[
                clase
            ][
                "confianza"
            ]

        ):

            mejores_por_clase[
                clase
            ] = deteccion

    detecciones_unicas = list(
        mejores_por_clase.values()
    )

    # ========================================================
    # INFORMACIÓN DE CADA CLASE
    # ========================================================

    for deteccion in detecciones_unicas:

        deteccion[
            "info"
        ] = obtener_info_clase(

            deteccion[
                "clase"
            ],

            deteccion[
                "nombre"
            ]
        )

    # ========================================================
    # SEPARAR SANAS Y PROBLEMAS
    # ========================================================

    detecciones_sanas = [

        d

        for d in detecciones_unicas

        if d[
            "info"
        ][
            "tipo"
        ] == "sana"
    ]

    detecciones_problema = [

        d

        for d in detecciones_unicas

        if d[
            "info"
        ][
            "tipo"
        ] != "sana"
    ]

    # ========================================================
    # ORDENAR POR CONFIANZA
    # ========================================================

    detecciones_sanas.sort(

        key=lambda x:
            x[
                "confianza"
            ],

        reverse=True
    )

    detecciones_problema.sort(

        key=lambda x:
            x[
                "confianza"
            ],

        reverse=True
    )

    # ========================================================
    # MEJORES DETECCIONES
    # ========================================================

    mejor_sana = (

        detecciones_sanas[0]

        if detecciones_sanas

        else None
    )

    mejor_problema = (

        detecciones_problema[0]

        if detecciones_problema

        else None
    )

    # ========================================================
    # CASO 1
    # HOJA SANA VS PROBLEMA
    # ========================================================

    if (
        mejor_sana
        and mejor_problema
    ):

        confianza_sana = (
            mejor_sana[
                "confianza"
            ]
        )

        confianza_problema = (
            mejor_problema[
                "confianza"
            ]
        )

        # ----------------------------------------------------
        # PRIORIDAD AL PROBLEMA
        # ----------------------------------------------------

        if (
            confianza_problema
            >= CONF_DIAGNOSTICO
        ):

            return crear_diagnostico(

                mejor_problema,

                bounding_boxes,

                contexto,

                otras_detecciones=detecciones_unicas,
            )

        # ----------------------------------------------------
        # HOJA SANA
        # ----------------------------------------------------

        if (
            confianza_sana
            >= CONF_DIAGNOSTICO
        ):

            return crear_diagnostico(

                mejor_sana,

                bounding_boxes,

                contexto,

                otras_detecciones=detecciones_problema,
            )

        # ----------------------------------------------------
        # NO CONCLUYENTE
        # ----------------------------------------------------

        return resultado_no_concluyente(

            bounding_boxes,

            contexto=contexto
        )

    # ========================================================
    # CASO 2
    # SOLO HAY PROBLEMAS
    # ========================================================

    if mejor_problema:

        confianza = (
            mejor_problema[
                "confianza"
            ]
        )

        if (
            confianza
            >= CONF_DIAGNOSTICO
        ):

            # -----------------------------------------------
            # SEGUNDA CLASE DIFERENTE
            # -----------------------------------------------

            otras = [

                d

                for d in detecciones_problema

                if d[
                    "clase"
                ]
                !=
                mejor_problema[
                    "clase"
                ]
            ]

            segunda = (

                otras[0]

                if otras

                else None
            )

            # -----------------------------------------------
            # MARGEN
            # -----------------------------------------------

            if segunda:

                diferencia = (
                    confianza
                    - segunda[
                        "confianza"
                    ]
                )

                # -------------------------------------------
                # Si ambas están demasiado cerca, seguimos
                # usando la principal pero dejamos constancia.
                # -------------------------------------------

                if (
                    diferencia
                    < MARGEN_DIAGNOSTICO
                ):

                    resultado = (
                        crear_diagnostico(

                            mejor_problema,

                            bounding_boxes,

                            contexto,

                            ambiguo=True,

                            otras_detecciones=detecciones_unicas,
                        )
                    )

                    resultado[
                        "diagnostico_ambiguo"
                    ] = True

                    resultado[
                        "advertencia_modelo"
                    ] = (
                        "Se encontraron dos posibles diagnósticos "
                        "con niveles de confianza cercanos. "
                        "Se muestra como principal el diagnóstico "
                        "con mayor confianza."
                    )

                    return resultado

            return crear_diagnostico(

                mejor_problema,

                bounding_boxes,

                contexto,

                otras_detecciones=detecciones_unicas,
            )

    # ========================================================
    # CASO 3
    # SOLO HOJA SANA
    # ========================================================

    if mejor_sana:

        if (
            mejor_sana[
                "confianza"
            ]
            >= CONF_DIAGNOSTICO
        ):

            return crear_diagnostico(

                mejor_sana,

                bounding_boxes,

                contexto,

                otras_detecciones=detecciones_problema,
            )

    # ========================================================
    # RESULTADO FINAL NO CONCLUYENTE
    # ========================================================

    return resultado_no_concluyente(

        bounding_boxes,

        (
            "El modelo encontró posibles características "
            "asociadas a una enfermedad, deficiencia o estado "
            "saludable, pero ninguna detección alcanzó un nivel "
            "de confianza suficiente para establecer un "
            "diagnóstico definitivo. Se recomienda realizar "
            "otra captura con buena iluminación, enfocando "
            "claramente la hoja."
        ),

        contexto
    )