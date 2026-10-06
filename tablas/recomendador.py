from .models import TipoAbono, Producto


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalizar_temporada(temporada):

    if not temporada:
        return "Cosecha"

    valor = str(temporada).strip().lower()

    equivalencias = {
        "cosecha": "Cosecha",
        "mitaca": "Mitaca",
        "floracion": "Florescencia",
        "floración": "Florescencia",
        "florecencia": "Florescencia",
        "florescencia": "Florescencia",
        "recuperacion": "Recuperacion",
        "recuperación": "Recuperacion",
    }

    return equivalencias.get(
        valor,
        str(temporada)
    )


def normalizar_variedad(variedad):

    if not variedad:
        return ""

    valor = str(variedad).strip().lower()

    equivalencias = {
        "bourbon": "Bourbon",
        "tabi": "Tabi",
        "typica": "Typica",
        "típica": "Typica",
        "maragogipe": "Maragogipe",
        "caturra": "Caturra",
        "castillo": "Castillo",
    }

    return equivalencias.get(
        valor,
        str(variedad)
    )


def normalizar_clima(clima):

    if not clima:
        return None

    valor = str(clima).strip().lower()

    equivalencias = {
        "seca": "seca",
        "seco": "seca",
        "normal": "normal",
        "lluviosa": "lluviosa",
        "lluvioso": "lluviosa",
    }

    return equivalencias.get(
        valor,
        valor
    )


# ============================================================
# REGLAS BASE DE ABONOS
# ============================================================

REGLAS_ABONOS = [

    # ========================================================
    # MITACA
    # ========================================================

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Mitaca"
            and 4.5 <= ph <= 5.2
            and 35 <= h <= 50
            and 12 <= t <= 18,

        "nombre": "Nutrimon produccion 17-6-18-2",

        "fallback":
            "Mitaca ácido-seco (N/K con Mg)",
    },

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Mitaca"
            and 5.3 <= ph <= 5.8
            and 51 <= h <= 65
            and 12 <= t <= 18,

        "nombre": "NUTRIMON 15-15-15",

        "fallback":
            "Mitaca balanceado en frío",
    },

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Mitaca"
            and 5.9 <= ph <= 6.5
            and 66 <= h <= 80
            and 18 <= t <= 24,

        "nombre": "ABOTEK",

        "fallback":
            "Mitaca con mayor demanda nutricional",
    },

    # ========================================================
    # COSECHA
    # ========================================================

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Cosecha"
            and 4.5 <= ph <= 5.2
            and 35 <= h <= 50
            and 18 <= t <= 24,

        "nombre": "ABOTEK",

        "fallback":
            "Cosecha ácida y seca con aporte de K y Mg",
    },

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Cosecha"
            and 5.3 <= ph <= 5.8
            and 51 <= h <= 65
            and 18 <= t <= 24,

        "nombre": "REMITAL",

        "fallback":
            "Cosecha balanceada",
    },

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Cosecha"
            and 5.9 <= ph <= 6.5
            and 66 <= h <= 80
            and 18 <= t <= 24,

        "nombre": "HYDROCOMPLEX",

        "fallback":
            "Cosecha con nutrición completa",
    },

    # ========================================================
    # FLORESCENCIA
    # ========================================================

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Florescencia"
            and 4.5 <= ph <= 5.2
            and 35 <= h <= 50
            and 18 <= t <= 24,

        "nombre": "Yara 10-30-10",

        "fallback":
            "Florescencia con mayor aporte de fósforo",
    },

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Florescencia"
            and 5.3 <= ph <= 5.8
            and 51 <= h <= 65
            and 18 <= t <= 24,

        "nombre": "Fosfato Diamónico",

        "fallback":
            "Florescencia con aporte de fósforo y nitrógeno",
    },

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Florescencia"
            and 5.9 <= ph <= 6.5
            and 66 <= h <= 80
            and 18 <= t <= 24,

        "nombre": "YaraVita CaBtrac",

        "fallback":
            "Florescencia con apoyo de Ca, B y Zn",
    },

    # ========================================================
    # RECUPERACIÓN
    # ========================================================

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Recuperacion"
            and 4.5 <= ph <= 5.2
            and 35 <= h <= 50
            and 18 <= t <= 24,

        "nombre": "NUTRICARGA",

        "fallback":
            "Recuperación nutricional con Mg, S, B y Zn",
    },

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Recuperacion"
            and 5.3 <= ph <= 5.8
            and 51 <= h <= 65
            and 18 <= t <= 24,

        "nombre": "HYDRAN",

        "fallback":
            "Recuperación y nutrición general",
    },

    {
        "condicion": lambda ph, h, t, temporada:
            temporada == "Recuperacion"
            and 5.9 <= ph <= 6.5
            and 66 <= h <= 80
            and 18 <= t <= 24,

        "nombre": "EMBAJADOR KS",

        "fallback":
            "Recuperación con nutrición completa",
    },
]


# ============================================================
# PRODUCTOS SEGÚN DEFICIENCIA
# ============================================================

PRODUCTOS_POR_DEFICIENCIA = {

    "def_azufre": [
        "YaraVera AMIDAS",
        "NUTRIMON Sulfato de Amonio",
        "NITRAX-S",
        "ABOTEK",
        "EMBAJADOR KS",
        "REMITAL",
        "HYDROCOMPLEX",
        "MicroEssentials",
    ],

    "def_boro": [
        "YaraVita CaBtrac",
        "ABOTEK",
        "EMBAJADOR KS",
        "REMITAL",
        "HYDROCOMPLEX",
        "HYDRAN",
    ],

    "def_calcio": [
        "YaraVita CaBtrac",
        "BONANZA",
    ],

    "def_cobre": [],

    "def_fosforo": [
        "Fosfato Diamónico",
        "MicroEssentials",
        "NUTRIMON 15-15-15",
        "BONANZA",
        "HYDROCOMPLEX",
        "REMITAL",
    ],

    "def_hierro": [
        "HYDROCOMPLEX",
    ],

    "def_magnesio": [
        "REMITAL",
        "ABOTEK",
        "HYDROCOMPLEX",
        "HYDRAN",
        "EMBAJADOR KS",
        "NUTRICARGA",
    ],

    "def_manganeso": [
        "HYDROCOMPLEX",
    ],

    "def_nitrogeno": [
        "Urea 46-0-0",
        "YaraVera AMIDAS",
        "NITRAX-S",
        "NUTRIMON Sulfato de Amonio",
        "NUTRICARGA",
        "HYDRAN",
        "EMBAJADOR KS",
        "REMITAL",
        "Agrocosecha",
    ],

    "def_potasio": [
        "Cloruro de Potasio",
        "ABOTEK",
        "EMBAJADOR KS",
        "HYDRAN",
        "REMITAL",
        "HYDROCOMPLEX",
        "Agrocosecha",
        "BONANZA",
    ],

    "def_zinc": [
        "YaraVita CaBtrac",
        "MicroEssentials",
        "REMITAL",
        "ABOTEK",
        "EMBAJADOR KS",
        "HYDROCOMPLEX",
        "HYDRAN",
    ],
}


# ============================================================
# PRODUCTOS DE APOYO PARA ENFERMEDADES
# ============================================================

PRODUCTOS_APOYO_ENFERMEDAD = {

    "roya": [
        "HYDROCOMPLEX",
        "REMITAL",
        "ABOTEK",
    ],

    "ojo de gallo": [
        "HYDROCOMPLEX",
        "REMITAL",
        "ABOTEK",
    ],

    "mancha de hierro": [
        "REMITAL",
        "NUTRIMON 15-15-15",
        "ABOTEK",
    ],

    "cercospora": [
        "REMITAL",
        "NUTRIMON 15-15-15",
        "ABOTEK",
    ],

    "antracnosis": [
        "HYDROCOMPLEX",
        "REMITAL",
        "ABOTEK",
    ],

    "mal rosado": [
        "HYDROCOMPLEX",
        "REMITAL",
        "ABOTEK",
    ],

    "llaga macana": [
        "HYDROCOMPLEX",
        "REMITAL",
    ],

    "nematodos": [
        "NUTRICARGA",
        "HYDROCOMPLEX",
    ],

    "broca": [
        "REMITAL",
        "ABOTEK",
    ],
}


# ============================================================
# INFORMACIÓN DE LOS ABONOS
# ============================================================

INFO_ABONOS = {

    "ABOTEK": {
        "formula": "15-4-23 + MgO + S + B + Zn",
        "nutrientes": "N, P, K, Mg, S, B y Zn",
        "aplicacion": "Principalmente al suelo",
        "uso": (
            "Producción, llenado del fruto y apoyo nutricional."
        ),
    },

    "EMBAJADOR KS": {
        "formula": "20-3-18 + MgO + S + B + Zn",
        "nutrientes": "N, P, K, Mg, S, B y Zn",
        "aplicacion": "Principalmente al suelo",
        "uso": "Nutrición y producción.",
    },

    "NUTRIMON 15-15-15": {
        "formula": "15-15-15",
        "nutrientes": "N, P y K",
        "aplicacion": "Suelo",
        "uso": "Nutrición general balanceada.",
    },

    "KATIUSKA": {
        "formula": "18-6-18 + MgO + S",
        "nutrientes": "N, P, K, Mg y S",
        "aplicacion": "Suelo",
        "uso": "Nutrición general y producción.",
    },

    "BONANZA": {
        "formula": "19-9-19 + Ca",
        "nutrientes": "N, P, K y Ca",
        "aplicacion": "Suelo",
        "uso": "Nutrición general con aporte de calcio.",
    },

    "Urea 46-0-0": {
        "formula": "46-0-0",
        "nutrientes": "N",
        "aplicacion": "Suelo",
        "uso": "Corrección de necesidades de nitrógeno.",
    },

    "MicroEssentials": {
        "formula": "12-40-0 + 10S + Zn",
        "nutrientes": "N, P, S y Zn",
        "aplicacion": "Suelo",
        "uso": "Aporte de fósforo, azufre y zinc.",
    },

    "HYDRAN": {
        "formula": "19-4-19 + Mg + S + B + Zn",
        "nutrientes": "N, P, K, Mg, S, B y Zn",
        "aplicacion": "Suelo",
        "uso": "Nutrición y producción.",
    },

    "NUTRICARGA": {
        "formula": "19-4-18 + Mg + S + B + Zn",
        "nutrientes": "N, P, K, Mg, S, B y Zn",
        "aplicacion": "Suelo",
        "uso": "Recuperación y nutrición.",
    },

    "NUTRIMON Sulfato de Amonio": {
        "formula": "21-0-0 + 24S",
        "nutrientes": "N y S",
        "aplicacion": "Suelo",
        "uso": "Aporte de nitrógeno y azufre.",
    },

    "REMITAL": {
        "formula": "17-6-18 + MgO + S + B + Zn",
        "nutrientes": "N, P, K, Mg, S, B y Zn",
        "aplicacion": "Suelo",
        "uso": "Nutrición completa y producción.",
    },

    "YaraVera AMIDAS": {
        "formula": "40-0-0 + S",
        "nutrientes": "N y S",
        "aplicacion": "Suelo",
        "uso": "Aporte de nitrógeno y azufre.",
    },

    "Cloruro de Potasio": {
        "formula": "0-0-60",
        "nutrientes": "K",
        "aplicacion": "Suelo",
        "uso": "Fuente concentrada de potasio.",
    },

    "Fosfato Diamónico": {
        "formula": "18-46-0",
        "nutrientes": "N y P",
        "aplicacion": "Suelo",
        "uso": "Fuente de fósforo y nitrógeno.",
    },

    "NITRAX-S": {
        "formula": "28-4-0 + 6S",
        "nutrientes": "N, P y S",
        "aplicacion": "Suelo",
        "uso": "Aporte de nitrógeno, fósforo y azufre.",
    },

    "HYDROCOMPLEX": {
        "formula": "12-11-18 + Mg + S + micronutrientes",
        "nutrientes": "N, P, K, Mg, S, B, Fe, Mn y Zn",
        "aplicacion": "Suelo",
        "uso": "Nutrición completa.",
    },

    "YaraVita CaBtrac": {
        "formula": "Ca + B + Zn + N",
        "nutrientes": "Ca, B, Zn y N",
        "aplicacion": "Foliar",
        "uso": "Aporte de calcio, boro y zinc.",
    },

    "Agrocosecha": {
        "formula": "26-4-22",
        "nutrientes": "N, P y K",
        "aplicacion": "Suelo",
        "uso": "Nutrición y producción.",
    },

    "Ecofertil": {
        "formula": "25-4-24",
        "nutrientes": "N, P y K",
        "aplicacion": "Suelo",
        "uso": "Producción.",
    },

    "Yara 18-18-18": {
        "formula": "18-18-18",
        "nutrientes": "N, P y K",
        "aplicacion": "Suelo",
        "uso": "Nutrición balanceada.",
    },

    "Nutrimon 10-20-20": {
        "formula": "10-20-20",
        "nutrientes": "N, P y K",
        "aplicacion": "Suelo",
        "uso": "Aporte de fósforo y potasio.",
    },

    "Yara 10-30-10": {
        "formula": "10-30-10",
        "nutrientes": "N, P y K",
        "aplicacion": "Suelo",
        "uso": "Aporte de fósforo.",
    },

    "Nutrimon produccion 17-6-18-2": {
        "formula": "17-6-18 + MgO",
        "nutrientes": "N, P, K y Mg",
        "aplicacion": "Suelo",
        "uso": "Nutrición y producción durante la mitaca.",
    },
}


# ============================================================
# TRATAMIENTOS FITOSANITARIOS
# ============================================================

NOTAS_FITOSANITARIAS = {

    "roya": {
        "titulo": "Roya del café (Hemileia vastatrix)",
        "tratamiento": (
            "Realiza monitoreo frecuente, retira hojas severamente "
            "afectadas y mejora la aireación del cultivo. En condiciones "
            "favorables para la enfermedad, utiliza el manejo fungicida "
            "recomendado para roya según la orientación técnica local."
        ),
    },

    "ojo de gallo": {
        "titulo": "Ojo de gallo (Mycena citricolor)",
        "tratamiento": (
            "Mejora la aireación mediante podas, regula la sombra y evita "
            "condiciones de humedad excesiva. En zonas con alta presión "
            "de la enfermedad se debe realizar manejo preventivo y "
            "seguimiento."
        ),
    },

    "mancha de hierro": {
        "titulo": "Mancha de hierro (Cercospora coffeicola)",
        "tratamiento": (
            "Refuerza la nutrición del cultivo, especialmente cuando "
            "exista estrés nutricional, controla el exceso de exposición "
            "solar y realiza manejo preventivo de la enfermedad."
        ),
    },

    "antracnosis": {
        "titulo": "Antracnosis del café",
        "tratamiento": (
            "Realiza podas sanitarias, retira material vegetal afectado, "
            "mejora la aireación del cultivo y realiza manejo preventivo "
            "cuando existan condiciones de alta humedad."
        ),
    },

    "mal rosado": {
        "titulo": "Mal rosado",
        "tratamiento": (
            "Realiza podas sanitarias de las ramas afectadas, mejora la "
            "aireación y reduce el exceso de humedad y sombra dentro del cultivo."
        ),
    },

    "mal_rosado": {
        "titulo": "Mal rosado",
        "tratamiento": (
            "Realiza podas sanitarias de las ramas afectadas, mejora la "
            "aireación y reduce el exceso de humedad y sombra dentro del cultivo."
        ),
    },

    "llaga macana": {
        "titulo": "Llaga macana",
        "tratamiento": (
            "Retira las plantas o partes severamente afectadas, evita "
            "heridas innecesarias durante las labores y realiza "
            "desinfección de herramientas."
        ),
    },

    "llaga_macana": {
        "titulo": "Llaga macana",
        "tratamiento": (
            "Retira las plantas o partes severamente afectadas, evita "
            "heridas innecesarias durante las labores y realiza "
            "desinfección de herramientas."
        ),
    },

    "nematodos": {
        "titulo": "Nematodos del café",
        "tratamiento": (
            "Realiza monitoreo de raíces y suelo, utiliza material vegetal "
            "sano y aplica medidas de manejo integrado para reducir la "
            "población del organismo en el suelo."
        ),
    },

    "broca": {
        "titulo": "Broca del café",
        "tratamiento": (
            "Realiza recolección oportuna de frutos maduros y remanentes, "
            "mantén una cosecha sanitaria y realiza manejo integrado de "
            "la broca según el nivel de infestación."
        ),
    },
}


# ============================================================
# NORMALIZACIÓN DE NOMBRES DE ABONOS
# ============================================================

def normalizar_nombre_abono(nombre):

    if not nombre:
        return ""

    valor = str(nombre).strip().lower()

    equivalencias = {

        "nutrimon produccion 17-6-18-2":
            "Nutrimon produccion 17-6-18-2",

        "nutrimon producción 17-6-18-2":
            "Nutrimon produccion 17-6-18-2",

        "yara18-18-18":
            "Yara 18-18-18",

        "yaramilahydrocomplex 12-11-18":
            "HYDROCOMPLEX",

        "yaramilahydrocomplex":
            "HYDROCOMPLEX",

        "yaravita zintrac mgb":
            "YaraVita CaBtrac",

        "nutrimon microessentials 12-40-0-10(s)":
            "MicroEssentials",

        "yaramilahydran 19-4-19":
            "HYDRAN",

        "nutrimon sulfato de amonio 21-0-0-24(s)":
            "NUTRIMON Sulfato de Amonio",

        "nitrimon sulfato de amonio 21-0-0-24(s)":
            "NUTRIMON Sulfato de Amonio",

        "cloruro de potasio kcl gr 0-0-60":
            "Cloruro de Potasio",

        "fosfato diamonico 18-46-0":
            "Fosfato Diamónico",

        "fosfato diamónico 18-46-0":
            "Fosfato Diamónico",

        "yara 10-30-10":
            "Yara 10-30-10",

        "nutrimon 10-20-20":
            "Nutrimon 10-20-20",

        "ecofertil 25-4-24":
            "Ecofertil",

        "agrocosecha 26-4-22":
            "Agrocosecha",

        "urea 46-0-0":
            "Urea 46-0-0",

        "yaravera amidas 40-5-35-5.6(s)":
            "YaraVera AMIDAS",

        "yaravera amidas":
            "YaraVera AMIDAS",

        "nitrax-s 28-4-0-6s":
            "NITRAX-S",

        "katiuska 18 – 6 – 18 – 2 (mgo) – 2 (s)":
            "KATIUSKA",

        "katiuska 18-6-18":
            "KATIUSKA",

        "bonanza 19 9 19-1(cao)":
            "BONANZA",

        "bonanza 19-9-19":
            "BONANZA",

        "nutricarga 19 – 4 – 18 – 3 (mgo) – 2 (s) – 0.1 (b) – 0.1 (zn)":
            "NUTRICARGA",

        "nutricarga 19-4-18":
            "NUTRICARGA",

        "embajador ks 20-3-18-3mgo-2s-0.1zn-0.1b":
            "EMBAJADOR KS",

        "embajador ks 20-3-18":
            "EMBAJADOR KS",

        "abotek 15 – 4 – 23 + 4% mgo + 2% s + 0.1% b + 0.1% zn":
            "ABOTEK",

        "abotek 15-4-23":
            "ABOTEK",

        "remital 17 – 6 – 18 + 2 (mgo)":
            "REMITAL",

        "remital 17-6-18":
            "REMITAL",
    }

    return equivalencias.get(
        valor,
        nombre
    )


# ============================================================
# OBTENER INFORMACIÓN DEL ABONO
# ============================================================

def informacion_abono(nombre):

    nombre_normalizado = normalizar_nombre_abono(
        nombre
    )

    info = INFO_ABONOS.get(
        nombre_normalizado
    )

    if not info:

        return {
            "nombre": nombre,
            "formula": None,
            "nutrientes": None,
            "aplicacion": None,
            "uso": None,
        }

    return {
        "nombre":
            nombre_normalizado,

        "formula":
            info.get("formula"),

        "nutrientes":
            info.get("nutrientes"),

        "aplicacion":
            info.get("aplicacion"),

        "uso":
            info.get("uso"),
    }


# ============================================================
# OBTENER ABONOS SEGÚN DEFICIENCIA
# ============================================================

def obtener_abonos_deficiencia(etiqueta):

    if not etiqueta:
        return []

    texto = (
        str(etiqueta)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )

    equivalencias = {

        "azufre":
            "def_azufre",

        "boro":
            "def_boro",

        "calcio":
            "def_calcio",

        "cobre":
            "def_cobre",

        "fosforo":
            "def_fosforo",

        "fósforo":
            "def_fosforo",

        "hierro":
            "def_hierro",

        "magnesio":
            "def_magnesio",

        "manganeso":
            "def_manganeso",

        "nitrogeno":
            "def_nitrogeno",

        "nitrógeno":
            "def_nitrogeno",

        "potasio":
            "def_potasio",

        "zinc":
            "def_zinc",
    }

    clave = None

    for palabra, deficiencia in equivalencias.items():

        if palabra in texto:

            clave = deficiencia
            break

    if not clave:
        return []

    return [
        informacion_abono(nombre)
        for nombre in PRODUCTOS_POR_DEFICIENCIA.get(
            clave,
            []
        )
    ]


# ============================================================
# OBTENER PRODUCTOS DE APOYO PARA ENFERMEDAD
# ============================================================

def obtener_abonos_enfermedad(etiqueta):

    if not etiqueta:
        return []

    texto = (
        str(etiqueta)
        .strip()
        .lower()
        .replace("_", " ")
    )

    for enfermedad, productos in PRODUCTOS_APOYO_ENFERMEDAD.items():

        if enfermedad in texto:

            return [
                informacion_abono(nombre)
                for nombre in productos
            ]

    return []


# ============================================================
# OBTENER TRATAMIENTO FITOSANITARIO
# ============================================================

def obtener_tratamiento_fitosanitario(
    etiqueta,
    estado=None
):

    texto = (
        str(etiqueta or "")
        .strip()
        .lower()
        .replace("_", " ")
    )

    for clave, nota in NOTAS_FITOSANITARIAS.items():

        clave_normalizada = (
            str(clave)
            .replace("_", " ")
            .lower()
        )

        if clave_normalizada in texto:

            return nota

    if estado == "healthy":

        return {
            "titulo":
                "Planta sana",

            "tratamiento": (
                "No se detectaron enfermedades. Mantén el plan "
                "de fertilización y realiza monitoreo preventivo "
                "del cultivo."
            ),
        }

    if estado == "deficiency":

        return {
            "titulo":
                "Deficiencia nutricional",

            "tratamiento": (
                "Corrige la deficiencia con un producto que aporte "
                "el nutriente requerido. Se recomienda confirmar "
                "la necesidad mediante análisis de suelo o tejido "
                "vegetal antes de realizar aplicaciones correctivas."
            ),
        }

    return {
        "titulo":
            etiqueta or "Diagnóstico",

        "tratamiento": (
            "Realiza seguimiento al cultivo y aplica el manejo "
            "recomendado de acuerdo con el diagnóstico obtenido."
        ),
    }


# ============================================================
# RECOMENDACIÓN GENERAL
# ============================================================

def recomendacion_general(
    ph,
    humedad,
    temperatura,
    temporada,
    **_contexto
):

    sugerencias = []

    temporada_normalizada = normalizar_temporada(
        temporada
    )

    if ph is not None and ph < 5.0:

        sugerencias.append({
            "nombre":
                "Corrección de acidez",

            "descripcion": (
                "El pH registrado es bajo. Se recomienda evaluar "
                "la acidez del suelo y realizar análisis antes "
                "de aplicar correctivos."
            ),

            "tipo_abono":
                None,

            "formula":
                "Corrección según análisis de suelo",

            "situacion":
                "extraordinaria",

            "es_general":
                True,
        })

    elif ph is not None and ph > 6.5:

        sugerencias.append({
            "nombre":
                "Manejo de pH elevado",

            "descripcion": (
                "El pH registrado es elevado para el cultivo de café. "
                "Se recomienda confirmar mediante análisis de suelo "
                "y ajustar la fertilización."
            ),

            "tipo_abono":
                None,

            "formula":
                "Corrección según análisis de suelo",

            "situacion":
                "extraordinaria",

            "es_general":
                True,
        })

    if humedad is not None and humedad < 35:

        sugerencias.append({
            "nombre":
                "Condición de baja humedad",

            "descripcion": (
                "La humedad registrada es baja. Evita realizar "
                "aplicaciones de fertilizantes al suelo cuando "
                "exista riesgo de pérdida por falta de humedad "
                "y espera condiciones adecuadas."
            ),

            "tipo_abono":
                None,

            "formula":
                None,

            "situacion":
                "extraordinaria",

            "es_general":
                True,
        })

    elif humedad is not None and humedad > 80:

        sugerencias.append({
            "nombre":
                "Condición de humedad elevada",

            "descripcion": (
                "La humedad registrada es elevada. Evita aplicaciones "
                "innecesarias y verifica drenaje y aireación del cultivo."
            ),

            "tipo_abono":
                None,

            "formula":
                None,

            "situacion":
                "extraordinaria",

            "es_general":
                True,
        })

    if temperatura is not None and temperatura <= 11:

        sugerencias.append({
            "nombre":
                "HYDROCOMPLEX",

            "descripcion": (
                "Condición de frío extremo: la absorción puede ser "
                "más lenta. Se recomienda una fórmula balanceada "
                "y realizar la aplicación en condiciones adecuadas."
            ),

            "tipo_abono":
                None,

            "formula":
                "12-11-18 + Mg + S + micronutrientes",

            "situacion":
                "extraordinaria",

            "es_general":
                True,
        })

    if not sugerencias:

        sugerencias.append({
            "nombre":
                "Fórmula balanceada",

            "descripcion": (
                f"No existe una coincidencia exacta para "
                f"{temporada_normalizada}. Se recomienda ajustar "
                "la fertilización con base en el análisis del suelo, "
                "tejido vegetal y las condiciones del cultivo."
            ),

            "tipo_abono":
                None,

            "formula":
                None,

            "situacion":
                "general",

            "es_general":
                True,
        })

    return sugerencias


# ============================================================
# OBTENER ABONO DESDE BASE DE DATOS
# ============================================================

def obtener_producto_bd(nombre):

    if not nombre:
        return None

    try:

        return (
            Producto.objects
            .filter(
                nombre__icontains=nombre
            )
            .select_related(
                "tipo_abono"
            )
            .first()
        )

    except Exception:

        return None


def obtener_tipo_abono_bd(nombre):

    if not nombre:
        return None

    try:

        return (
            TipoAbono.objects
            .filter(
                nombre__icontains=nombre
            )
            .first()
        )

    except Exception:

        return None


# ============================================================
# RECOMENDAR ABONO SEGÚN SENSORES / CLIMA
# ============================================================

def recomendar_abono(
    ph,
    humedad,
    temperatura,
    temporada,
    variedad=None,
    usar_sensores=True,
    condicion_climatica=None,
):

    temporada = normalizar_temporada(
        temporada
    )

    variedad = normalizar_variedad(
        variedad
    )

    condicion_climatica = normalizar_clima(
        condicion_climatica
    )

    recomendados = []

    # ========================================================
    # DATOS REALES ÚNICAMENTE
    # ========================================================
    # Antes se usaban valores de referencia (pH 5.5, humedad 55 %,
    # 21 °C o una humedad deducida del clima) cuando faltaba un dato.
    # Eso producía recomendaciones sin medición real. Ahora las reglas
    # solo se evalúan con pH, humedad y temperatura medidos.

    ph_referencia = ph
    humedad_referencia = humedad
    temperatura_referencia = temperatura

    if None in (ph_referencia, humedad_referencia, temperatura_referencia):
        return recomendados

    # ========================================================
    # EVALUAR REGLAS
    # ========================================================

    for regla in REGLAS_ABONOS:

        try:

            coincide = regla["condicion"](
                ph_referencia,
                humedad_referencia,
                temperatura_referencia,
                temporada,
            )

        except Exception:

            coincide = False

        if not coincide:
            continue

        nombre_regla = regla["nombre"]

        producto = obtener_producto_bd(
            nombre_regla
        )

        if producto:

            info = informacion_abono(
                producto.nombre
            )

            recomendados.append({

                "nombre":
                    producto.nombre,

                "descripcion": (
                    producto.descripcion
                    or info.get("uso")
                ),

                "tipo_abono":
                    producto.tipo_abono,

                "formula":
                    info.get("formula"),

                "nutrientes":
                    info.get("nutrientes"),

                "aplicacion":
                    info.get("aplicacion"),

                "uso":
                    info.get("uso"),

                "situacion":
                    "normal",

                "es_general":
                    False,

                "variedad":
                    variedad,

                "temporada":
                    temporada,

                "condicion_climatica":
                    condicion_climatica,

            })

            continue

        abono = obtener_tipo_abono_bd(
            nombre_regla
        )

        if abono:

            info = informacion_abono(
                abono.nombre
            )

            recomendados.append({

                "nombre":
                    abono.nombre,

                "descripcion":
                    info.get("uso"),

                "tipo_abono":
                    abono,

                "formula":
                    info.get("formula"),

                "nutrientes":
                    info.get("nutrientes"),

                "aplicacion":
                    info.get("aplicacion"),

                "uso":
                    info.get("uso"),

                "situacion":
                    "normal",

                "es_general":
                    False,

                "variedad":
                    variedad,

                "temporada":
                    temporada,

                "condicion_climatica":
                    condicion_climatica,

            })

            continue

        info = informacion_abono(
            nombre_regla
        )

        recomendados.append({

            "nombre":
                info.get("nombre")
                or regla["fallback"],

            "descripcion":
                info.get("uso")
                or regla["fallback"],

            "tipo_abono":
                None,

            "formula":
                info.get("formula"),

            "nutrientes":
                info.get("nutrientes"),

            "aplicacion":
                info.get("aplicacion"),

            "uso":
                info.get("uso"),

            "situacion":
                "normal",

            "es_general":
                False,

            "variedad":
                variedad,

            "temporada":
                temporada,

            "condicion_climatica":
                condicion_climatica,

        })

    return recomendados


# ============================================================
# OBTENER CLAVE DE DEFICIENCIA
# ============================================================

def obtener_clave_deficiencia(etiqueta):

    if not etiqueta:
        return None

    texto = (
        str(etiqueta)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )

    equivalencias = {

        "azufre":
            "def_azufre",

        "boro":
            "def_boro",

        "calcio":
            "def_calcio",

        "cobre":
            "def_cobre",

        "fosforo":
            "def_fosforo",

        "fósforo":
            "def_fosforo",

        "hierro":
            "def_hierro",

        "magnesio":
            "def_magnesio",

        "manganeso":
            "def_manganeso",

        "nitrogeno":
            "def_nitrogeno",

        "nitrógeno":
            "def_nitrogeno",

        "potasio":
            "def_potasio",

        "zinc":
            "def_zinc",
    }

    for palabra, clave in equivalencias.items():

        if palabra in texto:
            return clave

    return None


# ============================================================
# OBTENER NUTRIENTE PRINCIPAL DE DEFICIENCIA
# ============================================================

def obtener_nombre_nutriente(clave):

    equivalencias = {

        "def_azufre":
            "azufre",

        "def_boro":
            "boro",

        "def_calcio":
            "calcio",

        "def_cobre":
            "cobre",

        "def_fosforo":
            "fósforo",

        "def_hierro":
            "hierro",

        "def_magnesio":
            "magnesio",

        "def_manganeso":
            "manganeso",

        "def_nitrogeno":
            "nitrógeno",

        "def_potasio":
            "potasio",

        "def_zinc":
            "zinc",
    }

    return equivalencias.get(
        clave,
        "nutrientes requeridos"
    )


# ============================================================
# CALCULAR COINCIDENCIA DEL NUTRIENTE
# ============================================================

def puntaje_nutriente(
    producto,
    deficiencia_key
):

    if not deficiencia_key:
        return 0, ""

    nutriente = obtener_nombre_nutriente(
        deficiencia_key
    )

    nutrientes = str(
        producto.get("nutrientes")
        or ""
    ).lower()

    if nutriente == "fósforo":

        if (
            "fósforo" in nutrientes
            or "fosforo" in nutrientes
            or "p" in nutrientes
        ):

            return (
                45,
                "aporta fósforo"
            )

    elif nutriente in nutrientes:

        return (
            45,
            f"aporta {nutriente}"
        )

    return (
        0,
        ""
    )


# ============================================================
# PUNTAJE SEGÚN TEMPORADA
# ============================================================

def puntaje_temporada(
    nombre,
    temporada
):

    nombre = str(
        nombre or ""
    ).lower()

    reglas = {

        "Cosecha": [
            "abotek",
            "remital",
            "hydrocomplex",
            "embajador",
            "agrocosecha",
        ],

        "Mitaca": [
            "nutrimon",
            "abotek",
            "remital",
            "hydran",
        ],

        "Florescencia": [
            "10-30-10",
            "fosfato",
            "cabtrac",
            "microessentials",
        ],

        "Recuperacion": [
            "nutricarga",
            "hydran",
            "embajador",
            "hydrocomplex",
            "remital",
        ],
    }

    for palabra in reglas.get(
        temporada,
        []
    ):

        if palabra.lower() in nombre:

            return (
                20,
                f"es compatible con la etapa de {temporada.lower()}"
            )

    return (
        0,
        ""
    )


# ============================================================
# PUNTAJE SEGÚN CLIMA
# ============================================================

def puntaje_clima(
    producto,
    clima
):

    if not clima:
        return 0, ""

    nombre = str(
        producto.get("nombre")
        or ""
    ).lower()

    nutrientes = str(
        producto.get("nutrientes")
        or ""
    ).lower()

    if clima == "seca":

        if (
            "potasio" in nutrientes
            or " k" in nutrientes
            or "n, p, k" in nutrientes
        ):

            return (
                8,
                "se considera favorable como apoyo nutricional en condición seca"
            )

        if (
            "abotek" in nombre
            or "remital" in nombre
            or "hydrocomplex" in nombre
        ):

            return (
                6,
                "puede utilizarse como apoyo nutricional en condición seca"
            )

    elif clima == "lluviosa":

        if (
            "hydrocomplex" in nombre
            or "remital" in nombre
            or "embajador" in nombre
        ):

            return (
                8,
                "aporta una nutrición amplia como apoyo en condición lluviosa"
            )

    elif clima == "normal":

        if (
            "nutrimon 15-15-15" in nombre
            or "hydrocomplex" in nombre
            or "remital" in nombre
        ):

            return (
                8,
                "es una alternativa de nutrición equilibrada"
            )

    return (
        0,
        ""
    )


# ============================================================
# PUNTAJE SEGÚN SENSORES
# ============================================================

def puntaje_sensores(
    producto,
    ph,
    humedad,
    temperatura
):

    puntos = 0
    razones = []

    if ph is not None:

        if 5.0 <= ph <= 6.5:

            puntos += 5

            razones.append(
                "compatible con el rango de pH registrado"
            )

        elif ph < 5.0:

            if (
                "Ca" in str(
                    producto.get("nutrientes")
                    or ""
                )
            ):

                puntos += 3

                razones.append(
                    "aporta nutrientes útiles dentro del contexto de pH bajo"
                )

    if humedad is not None:

        if 40 <= humedad <= 75:

            puntos += 4

            razones.append(
                "el nivel de humedad permite considerar la aplicación"
            )

        elif humedad < 35:

            razones.append(
                "la baja humedad requiere esperar condiciones adecuadas para aplicar"
            )

        elif humedad > 80:

            razones.append(
                "la humedad elevada requiere verificar las condiciones del suelo"
            )

    if temperatura is not None:

        if 18 <= temperatura <= 24:

            puntos += 3

            razones.append(
                "la temperatura está dentro del contexto utilizado por las reglas"
            )

    return (
        puntos,
        razones
    )


# ============================================================
# PUNTAJE SEGÚN VARIEDAD
# ============================================================

def puntaje_variedad(
    producto,
    variedad
):

    if not variedad:
        return 0, ""

    # No se inventa una necesidad nutricional específica
    # por variedad. La variedad solamente se conserva como
    # contexto para la recomendación.

    return (
        2,
        f"la recomendación considera la variedad {variedad}"
    )


# ============================================================
# CONSTRUIR RAZÓN DE RECOMENDACIÓN
# ============================================================

def construir_razon_producto(
    producto,
    deficiencia_key,
    temporada,
    clima,
    usar_sensores,
    ph,
    humedad,
    temperatura,
    variedad
):

    razones = []

    puntos, razon = puntaje_nutriente(
        producto,
        deficiencia_key
    )

    if razon:
        razones.append(razon)

    puntos, razon = puntaje_temporada(
        producto.get("nombre"),
        temporada
    )

    if razon:
        razones.append(razon)

    puntos, razon = puntaje_clima(
        producto,
        clima
    )

    if razon:
        razones.append(razon)

    if usar_sensores:

        puntos, razones_sensores = puntaje_sensores(
            producto,
            ph,
            humedad,
            temperatura
        )

        razones.extend(
            razones_sensores
        )

    puntos, razon = puntaje_variedad(
        producto,
        variedad
    )

    if razon:
        razones.append(razon)

    if not razones:

        razones.append(
            "se selecciona como alternativa de apoyo nutricional "
            "dentro de las condiciones disponibles"
        )

    return razones


# ============================================================
# CALCULAR PUNTAJE COMPLETO DE PRODUCTO
# ============================================================

def calcular_puntaje_producto(
    producto,
    deficiencia_key,
    temporada,
    clima,
    usar_sensores,
    ph,
    humedad,
    temperatura,
    variedad
):

    puntaje = 0
    razones = []

    # ========================================================
    # DEFICIENCIA
    # ========================================================

    puntos, razon = puntaje_nutriente(
        producto,
        deficiencia_key
    )

    puntaje += puntos

    if razon:
        razones.append(
            razon
        )

    # ========================================================
    # TEMPORADA
    # ========================================================

    puntos, razon = puntaje_temporada(
        producto.get("nombre"),
        temporada
    )

    puntaje += puntos

    if razon:
        razones.append(
            razon
        )

    # ========================================================
    # CLIMA
    # ========================================================

    puntos, razon = puntaje_clima(
        producto,
        clima
    )

    puntaje += puntos

    if razon:
        razones.append(
            razon
        )

    # ========================================================
    # SENSORES
    # ========================================================

    if usar_sensores:

        puntos, razones_sensores = puntaje_sensores(
            producto,
            ph,
            humedad,
            temperatura
        )

        puntaje += puntos

        razones.extend(
            razones_sensores
        )

    # ========================================================
    # VARIEDAD
    # ========================================================

    puntos, razon = puntaje_variedad(
        producto,
        variedad
    )

    puntaje += puntos

    if razon:
        razones.append(
            razon
        )

    # ========================================================
    # EVITAR RAZONES REPETIDAS
    # ========================================================

    razones_finales = []

    for razon in razones:

        if razon in razones_finales:
            continue

        razones_finales.append(
            razon
        )

    return (
        puntaje,
        razones_finales
    )


# ============================================================
# SELECCIONAR LOS 3 MEJORES ABONOS
# ============================================================

def seleccionar_tres_abonos(
    productos,
    deficiencia_key,
    temporada,
    clima,
    usar_sensores,
    ph,
    humedad,
    temperatura,
    variedad
):

    candidatos = []

    nombres_vistos = set()

    for producto in productos:

        if not producto:
            continue

        nombre = producto.get(
            "nombre"
        )

        if not nombre:
            continue

        nombre_normalizado = (
            normalizar_nombre_abono(
                nombre
            )
        )

        clave = (
            nombre_normalizado
            .strip()
            .lower()
        )

        if clave in nombres_vistos:
            continue

        nombres_vistos.add(
            clave
        )

        producto = {
            **producto,
            **informacion_abono(
                nombre_normalizado
            )
        }

        producto["nombre"] = (
            nombre_normalizado
        )

        puntaje, razones = (
            calcular_puntaje_producto(
                producto,
                deficiencia_key,
                temporada,
                clima,
                usar_sensores,
                ph,
                humedad,
                temperatura,
                variedad,
            )
        )

        producto["puntaje"] = (
            puntaje
        )

        producto["razones"] = (
            razones
        )

        candidatos.append(
            producto
        )

    candidatos.sort(
        key=lambda x: (
            x.get("puntaje", 0)
        ),
        reverse=True
    )

    seleccionados = (
        candidatos[:3]
    )

    for posicion, producto in enumerate(
        seleccionados,
        start=1
    ):

        producto["prioridad"] = (
            posicion
        )

        if posicion == 1:
            producto["nivel_recomendacion"] = (
                "Principal"
            )

        elif posicion == 2:
            producto["nivel_recomendacion"] = (
                "Alternativa"
            )

        else:
            producto["nivel_recomendacion"] = (
                "Alternativa"
            )

        razones = producto.get(
            "razones",
            []
        )

        if razones:

            producto["razon"] = (
                "Se recomienda porque "
                + ", ".join(razones)
                + "."
            )

        else:

            producto["razon"] = (
                "Se recomienda como alternativa "
                "de apoyo nutricional."
            )

    return seleccionados


# ============================================================
# CONSTRUIR SUGERENCIA INTEGRADA
# ============================================================

def construir_sugerencia_integrada_anterior(
    ph,
    humedad,
    temperatura,
    temporada,
    abonos,
    diagnostico=None,
    variedad=None,
    usar_sensores=True,
    condicion_climatica=None,
):

    # ========================================================
    # NORMALIZAR CONTEXTO
    # ========================================================

    temporada = normalizar_temporada(
        temporada
    )

    variedad = normalizar_variedad(
        variedad
    )

    condicion_climatica = normalizar_clima(
        condicion_climatica
    )

    # ========================================================
    # CONTEXTO CON SENSORES
    # ========================================================

    if usar_sensores:

        contexto = (
            f"pH {ph}, humedad {humedad}% "
            f"y temperatura {temperatura}°C"
        )

    # ========================================================
    # CONTEXTO SIN SENSORES
    # ========================================================

    else:

        contexto = (
            f"condición climática "
            f"{condicion_climatica or 'normal'}"
        )

    # ========================================================
    # SI NO EXISTE DIAGNÓSTICO
    # ========================================================

    if not diagnostico:

        if not abonos:

            return None

        productos_base = []

        for abono in abonos:

            if not isinstance(
                abono,
                dict
            ):
                continue

            nombre = abono.get(
                "nombre"
            )

            if not nombre:
                continue

            productos_base.append(
                informacion_abono(
                    nombre
                )
            )

        productos_finales = (
            seleccionar_tres_abonos(
                productos_base,
                None,
                temporada,
                condicion_climatica,
                usar_sensores,
                ph,
                humedad,
                temperatura,
                variedad,
            )
        )

        principal = (
            productos_finales[0]
            if productos_finales
            else None
        )

        return {

            "estado":
                "healthy",

            "etiqueta":
                "",

            "titulo_fito":
                "Recomendación nutricional",

            "abono":
                (
                    principal.get("nombre")
                    if principal
                    else None
                ),

            "texto": (
                f"Para la temporada de {temporada}, "
                f"considerando {contexto}, "
                f"se seleccionaron hasta tres alternativas "
                f"de apoyo nutricional."
            ),

            "tratamiento": (
                "La selección debe complementarse con "
                "las indicaciones técnicas del producto "
                "y las condiciones reales del cultivo."
            ),

            "productos_deficiencia":
                productos_finales,

            "abonos":
                productos_finales,

            "ph":
                ph,

            "humedad":
                humedad,

            "temperatura":
                temperatura,

            "temporada":
                temporada,

            "variedad":
                variedad,

            "usar_sensores":
                usar_sensores,

            "condicion_climatica":
                condicion_climatica,

            "enfermedad":
                None,

        }

    # ========================================================
    # DATOS DEL DIAGNÓSTICO
    # ========================================================

    estado = (
        diagnostico.get("estado")
        or "alert"
    )

    etiqueta = (
        diagnostico.get("etiqueta")
        or diagnostico.get("diagnostico")
        or ""
    )

    etiqueta_texto = str(
        etiqueta
    ).strip()

    etiqueta_normalizada = (
        etiqueta_texto
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )

    # ========================================================
    # TRATAMIENTO FITOSANITARIO
    # ========================================================

    tratamiento = obtener_tratamiento_fitosanitario(
        etiqueta_texto,
        estado
    )

    # ========================================================
    # DETECTAR DEFICIENCIA
    # ========================================================

    deficiencia_key = None

    productos_deficiencia = []

    if estado == "deficiency":

        deficiencia_key = (
            obtener_clave_deficiencia(
                etiqueta_texto
            )
        )

        productos_deficiencia = (
            obtener_abonos_deficiencia(
                etiqueta_texto
            )
        )

    # ========================================================
    # DETECTAR ENFERMEDAD
    # ========================================================

    enfermedad_detectada = None

    for clave in NOTAS_FITOSANITARIAS.keys():

        clave_normalizada = (
            str(clave)
            .lower()
            .replace("_", " ")
        )

        if clave_normalizada in etiqueta_normalizada:

            enfermedad_detectada = (
                clave
            )

            break

    # ========================================================
    # PRODUCTOS DE APOYO PARA ENFERMEDAD
    # ========================================================

    productos_enfermedad = []

    if enfermedad_detectada:

        productos_enfermedad = (
            obtener_abonos_enfermedad(
                etiqueta_texto
            )
        )

    # ========================================================
    # CONSTRUIR CANDIDATOS
    # ========================================================

    candidatos = []

    # ========================================================
    # DEFICIENCIA
    # ========================================================

    if productos_deficiencia:

        candidatos.extend(
            productos_deficiencia
        )

    # ========================================================
    # ENFERMEDAD
    # ========================================================

    elif enfermedad_detectada:

        candidatos.extend(
            productos_enfermedad
        )

        # Si no existen productos de apoyo
        # se pueden utilizar los obtenidos
        # por las reglas de sensores/clima.

        if not candidatos and abonos:

            candidatos.extend(
                [
                    informacion_abono(
                        a.get("nombre")
                    )
                    for a in abonos
                    if a.get("nombre")
                ]
            )

    # ========================================================
    # PLANTA SANA
    # ========================================================

    elif estado == "healthy":

        if abonos:

            candidatos.extend(
                [
                    informacion_abono(
                        a.get("nombre")
                    )
                    for a in abonos
                    if a.get("nombre")
                ]
            )

    # ========================================================
    # OTRO DIAGNÓSTICO
    # ========================================================

    elif abonos:

        candidatos.extend(
            [
                informacion_abono(
                    a.get("nombre")
                )
                for a in abonos
                if a.get("nombre")
            ]
        )

    # ========================================================
    # SI NO HAY CANDIDATOS
    # BUSCAR RECOMENDACIONES DE SENSORES/CLIMA
    # ========================================================

    if not candidatos:

        candidatos.extend(
            recomendar_abono(
                ph=ph,
                humedad=humedad,
                temperatura=temperatura,
                temporada=temporada,
                variedad=variedad,
                usar_sensores=usar_sensores,
                condicion_climatica=condicion_climatica,
            )
        )

    # ========================================================
    # SELECCIONAR LOS 3 MEJORES
    # ========================================================

    productos_finales = (
        seleccionar_tres_abonos(
            candidatos,
            deficiencia_key,
            temporada,
            condicion_climatica,
            usar_sensores,
            ph,
            humedad,
            temperatura,
            variedad,
        )
    )

    # ========================================================
    # PRODUCTO PRINCIPAL
    # ========================================================

    abono_principal = (
        productos_finales[0]
        if productos_finales
        else None
    )

    # ========================================================
    # NOMBRES PARA EL TEXTO
    # ========================================================

    nombres_productos = [
        producto.get("nombre")
        for producto in productos_finales
        if producto.get("nombre")
    ]

    # ========================================================
    # PLANTA SANA
    # ========================================================

    if estado == "healthy":

        titulo = (
            "Planta sana"
        )

        texto = (
            "La IA no identificó una enfermedad o "
            "deficiencia nutricional en la muestra. "
            f"Para la temporada de {temporada}, "
            f"considerando {contexto}, se recomienda "
            "mantener el monitoreo y el programa "
            "nutricional del cultivo."
        )

        if nombres_productos:

            texto += (
                " Como alternativas de apoyo nutricional "
                "se seleccionaron: "
                + ", ".join(
                    nombres_productos
                )
                + "."
            )

        tratamiento_texto = (
            "No se detectaron enfermedades o deficiencias "
            "en la muestra. Mantén el monitoreo preventivo "
            "del cultivo y continúa con un programa de "
            "fertilización equilibrado."
        )

    # ========================================================
    # DEFICIENCIA NUTRICIONAL
    # ========================================================

    elif productos_deficiencia:

        titulo = (
            f"Deficiencia nutricional: "
            f"{etiqueta_texto}"
        )

        texto = (
            f"La IA identificó {etiqueta_texto}. "
            "La selección de los abonos considera el "
            "nutriente relacionado con la deficiencia, "
            f"la temporada de {temporada} y "
            f"{contexto}."
        )

        if nombres_productos:

            texto += (
                " Las tres alternativas priorizadas son: "
                + ", ".join(
                    nombres_productos
                )
                + "."
            )

        texto += (
            " La selección del producto debe complementarse "
            "con un análisis de suelo o tejido vegetal antes "
            "de establecer la dosis."
        )

        tratamiento_texto = tratamiento.get(
            "tratamiento",
            (
                "Se recomienda confirmar la deficiencia "
                "mediante análisis de suelo o tejido vegetal."
            )
        )

    # ========================================================
    # ENFERMEDAD
    # ========================================================

    elif enfermedad_detectada:

        titulo = tratamiento.get(
            "titulo",
            etiqueta_texto
            or "Enfermedad detectada"
        )

        texto = (
            f"La IA identificó {etiqueta_texto}. "
            "La fertilización se considera únicamente "
            "como apoyo al estado nutricional de la planta "
            "y no sustituye el manejo fitosanitario."
        )

        if nombres_productos:

            texto += (
                f" Considerando la temporada de {temporada} "
                f"y {contexto}, se seleccionaron como apoyo "
                "nutricional: "
                + ", ".join(
                    nombres_productos
                )
                + "."
            )

        tratamiento_texto = tratamiento.get(
            "tratamiento",
            (
                "Realiza el manejo fitosanitario "
                "correspondiente y mantén el monitoreo "
                "del cultivo."
            )
        )

    # ========================================================
    # ALERTA / OTRO DIAGNÓSTICO
    # ========================================================

    else:

        titulo = (
            etiqueta_texto
            or "Diagnóstico del cultivo"
        )

        texto = (
            f"La IA identificó "
            f"{etiqueta_texto or 'una condición de alerta'}. "
            f"Para la temporada de {temporada}, "
            f"considerando {contexto}, se recomienda "
            "mantener el monitoreo del cultivo y validar "
            "el diagnóstico antes de realizar aplicaciones "
            "correctivas."
        )

        if nombres_productos:

            texto += (
                " Como apoyo nutricional se seleccionaron: "
                + ", ".join(
                    nombres_productos
                )
                + "."
            )

        tratamiento_texto = tratamiento.get(
            "tratamiento",
            (
                "Realiza seguimiento al cultivo y aplica "
                "el manejo recomendado de acuerdo con "
                "el diagnóstico."
            )
        )

    # ========================================================
    # DETALLES DE LOS 3 PRODUCTOS
    # ========================================================

    productos_detallados = []

    for producto in productos_finales:

        productos_detallados.append({

            "nombre":
                producto.get("nombre"),

            "formula":
                producto.get("formula"),

            "nutrientes":
                producto.get("nutrientes"),

            "aplicacion":
                producto.get("aplicacion"),

            "uso":
                producto.get("uso"),

            "descripcion":
                producto.get("descripcion")
                or producto.get("uso"),

            "prioridad":
                producto.get("prioridad"),

            "nivel_recomendacion":
                producto.get(
                    "nivel_recomendacion"
                ),

            "puntaje":
                producto.get("puntaje", 0),

            "razon":
                producto.get("razon"),

            "variedad":
                variedad,

            "temporada":
                temporada,

            "condicion_climatica":
                condicion_climatica,

            "usar_sensores":
                usar_sensores,
        })

    # ========================================================
    # INFORMACIÓN TÉCNICA DEL PRINCIPAL
    # ========================================================

    if abono_principal:

        nombre_abono = (
            abono_principal.get(
                "nombre"
            )
        )

        formula = (
            abono_principal.get(
                "formula"
            )
        )

        nutrientes = (
            abono_principal.get(
                "nutrientes"
            )
        )

        aplicacion = (
            abono_principal.get(
                "aplicacion"
            )
        )

        uso = (
            abono_principal.get(
                "uso"
            )
        )

        razon = (
            abono_principal.get(
                "razon"
            )
        )

        informacion_tecnica = (
            f"Producto principal: {nombre_abono}."
        )

        if formula:

            informacion_tecnica += (
                f" Fórmula: {formula}."
            )

        if nutrientes:

            informacion_tecnica += (
                f" Nutrientes: {nutrientes}."
            )

        if aplicacion:

            informacion_tecnica += (
                f" Aplicación: {aplicacion}."
            )

        if uso:

            informacion_tecnica += (
                f" Uso: {uso}."
            )

        if razon:

            informacion_tecnica += (
                f" Motivo de selección: {razon}"
            )

        tratamiento_texto = (
            informacion_tecnica
            + " "
            + tratamiento_texto
        )

    # ========================================================
    # RESPUESTA FINAL
    # ========================================================

    return {

        "estado":
            estado or "alert",

        "etiqueta":
            etiqueta_texto,

        "titulo_fito":
            titulo,

        "abono":
            (
                abono_principal.get(
                    "nombre"
                )
                if abono_principal
                else None
            ),

        "texto":
            texto,

        "tratamiento":
            tratamiento_texto,

        "productos_deficiencia":
            productos_detallados,

        "abonos":
            productos_detallados,

        "productos_recomendados":
            productos_detallados,

        "cantidad_recomendados":
            len(productos_detallados),

        "abono_principal":
            (
                productos_detallados[0]
                if productos_detallados
                else None
            ),

        "segundo_abono":
            (
                productos_detallados[1]
                if len(productos_detallados) > 1
                else None
            ),

        "tercer_abono":
            (
                productos_detallados[2]
                if len(productos_detallados) > 2
                else None
            ),

        "ph":
            ph,

        "humedad":
            humedad,

        "temperatura":
            temperatura,

        "temporada":
            temporada,

        "variedad":
            variedad,

        "usar_sensores":
            usar_sensores,

        "condicion_climatica":
            condicion_climatica,

        "enfermedad":
            enfermedad_detectada,

    }

# ============================================================
# SUGERENCIA INTEGRADA (MOTOR EN DOS ETAPAS)
# ============================================================
#
# Diagnóstico visual y recomendación son etapas separadas:
# ver tablas/motor_recomendacion.py. Las reglas anteriores
# (REGLAS_ABONOS, PRODUCTOS_POR_DEFICIENCIA, puntajes por etapa)
# se conservan en este módulo y el motor las usa como factores
# secundarios. La versión anterior de esta función se conserva
# como construir_sugerencia_integrada_anterior.

def construir_sugerencia_integrada(
    ph,
    humedad,
    temperatura,
    temporada,
    abonos=None,
    diagnostico=None,
    variedad=None,
    usar_sensores=True,
    condicion_climatica=None,
    analisis_suelo=None,
    analisis_foliar=None,
    fuente_datos=None,
):

    from .motor_recomendacion import (
        productos_formato_legacy,
        recomendar,
    )

    diagnostico = diagnostico or {}

    recomendacion = recomendar(
        diagnostico=diagnostico,
        contexto={
            "temporada": temporada,
            "variedad": variedad,
            "condicion_climatica": condicion_climatica,
            # Sin sensores los valores no existen: no se inventan.
            "ph": ph if usar_sensores else None,
            "humedad": humedad if usar_sensores else None,
            "temperatura": temperatura if usar_sensores else None,
            "fuente_datos": fuente_datos,
            "analisis_suelo": analisis_suelo,
            "analisis_foliar": analisis_foliar,
        },
    )

    visual = recomendacion["diagnostico_visual"]
    productos = productos_formato_legacy(recomendacion)
    etiqueta = str(diagnostico.get("etiqueta") or diagnostico.get("diagnostico") or "").strip()
    tratamiento = obtener_tratamiento_fitosanitario(etiqueta, diagnostico.get("estado"))

    # --------------------------------------------------------
    # TEXTO EXPLICATIVO (generado con los datos reales)
    # --------------------------------------------------------

    partes = [
        f"{visual['descripcion']}"
        + (f" (confianza visual {visual['confianza_visual']} %)." if visual["confianza_visual"] is not None else "."),
        f"Confianza de la recomendación: {recomendacion['nivel_confianza']}.",
        recomendacion["validacion"]["resumen"],
    ]

    if recomendacion["decision"] == "recomendar":
        partes.append(
            "Productos ordenados por mayor compatibilidad con las necesidades detectadas: "
            + ", ".join(p["nombre"] for p in productos) + "."
        )
    else:
        partes.append(recomendacion["mensaje"])
        partes.extend(recomendacion["motivos_no_recomendacion"])

    visual_preliminar = recomendacion.get("recomendacion_visual")
    if visual_preliminar:
        productos_visuales = visual_preliminar["productos"] + visual_preliminar["foliares"]
        if productos_visuales:
            partes.append(
                f"{visual_preliminar['titulo']} Productos que aportan "
                + ", ".join(d["nombre"] for d in visual_preliminar["nutrientes_detectados"])
                + ": " + ", ".join(p["nombre"] for p in productos_visuales) + "."
            )
        if visual_preliminar["mensaje_sin_producto"]:
            partes.append(visual_preliminar["mensaje_sin_producto"])
        if visual_preliminar["nota_enfermedad"]:
            partes.append(visual_preliminar["nota_enfermedad"])
        partes.append(visual_preliminar["advertencia"])
    elif recomendacion["recomendacion_validacion"]:
        partes.append(recomendacion["recomendacion_validacion"])

    partes.append(recomendacion["dosis"])

    texto = " ".join(p for p in partes if p)

    return {
        # Claves que ya consumían el frontend y motor_yolo
        "estado": diagnostico.get("estado") or "alert",
        "etiqueta": etiqueta,
        "titulo_fito": tratamiento.get("titulo") or visual["descripcion"],
        "abono": productos[0]["nombre"] if productos else None,
        "texto": texto,
        "tratamiento": tratamiento.get("tratamiento"),
        "productos_deficiencia": productos,
        "abonos": productos,
        "productos_recomendados": productos,
        "cantidad_recomendados": len(productos),
        "abono_principal": productos[0] if productos else None,
        "segundo_abono": productos[1] if len(productos) > 1 else None,
        "tercer_abono": productos[2] if len(productos) > 2 else None,
        "ph": recomendacion["validacion"]["ph"],
        "humedad": recomendacion["validacion"]["humedad_suelo"],
        "temperatura": recomendacion["validacion"]["temperatura"],
        "temporada": recomendacion["contexto"]["temporada"],
        "variedad": recomendacion["contexto"]["variedad"],
        "usar_sensores": usar_sensores,
        "condicion_climatica": recomendacion["validacion"]["condicion_climatica"],
        "enfermedad": visual["etiqueta"] if visual["tipo"] == "enfermedad" else None,

        # Resultado completo del motor en dos etapas
        "recomendacion": recomendacion,
        "decision": recomendacion["decision"],
        "nivel_confianza": recomendacion["nivel_confianza"],

        # Recomendación visual preliminar (solo cuando la agronómica no alcanza)
        "recomendacion_visual": visual_preliminar,
    }
