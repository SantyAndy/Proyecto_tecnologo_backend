"""
Catálogo técnico de fertilizantes.

Cada producto es un registro con su composición, su imagen y sus
metadatos. El recomendador y el frontend trabajan SOLO con estos
registros: no hay if/else por nombre de producto para elegir imágenes
ni composiciones.

Convenciones de la composición (tal como aparece en la etiqueta):

    N  = % nitrógeno total
    P  = % P2O5
    K  = % K2O
    Ca = % CaO
    Mg = % MgO
    S  = % S
    B, Zn, Fe, Mn, Cu = % del elemento

    None  → dato NO confirmado (no se inventa).
    0     → el producto no contiene el nutriente (confirmado por el grado).

`presentes_sin_cantidad` lista nutrientes que el producto contiene según
su ficha, pero cuya cantidad no está registrada: cuentan como aporte,
pero no reciben puntos por concentración.

`imagen` es la ruta relativa a MEDIA_ROOT. Si el TipoAbono enlazado
(`nombre_bd`) tiene una imagen principal válida en la base de datos,
esa tiene prioridad (ver motor_recomendacion.resolver_imagen).

`clave_legacy` enlaza el producto con las reglas y listas antiguas de
recomendador.py (REGLAS_ABONOS, PRODUCTOS_POR_DEFICIENCIA, INFO_ABONOS).
"""


NUTRIENTES = ["N", "P", "K", "Ca", "Mg", "S", "B", "Zn", "Fe", "Mn", "Cu"]

NOMBRES_NUTRIENTES = {
    "N": "nitrógeno",
    "P": "fósforo",
    "K": "potasio",
    "Ca": "calcio",
    "Mg": "magnesio",
    "S": "azufre",
    "B": "boro",
    "Zn": "zinc",
    "Fe": "hierro",
    "Mn": "manganeso",
    "Cu": "cobre",
}

MACRONUTRIENTES = {"N", "P", "K", "Ca", "Mg", "S"}
MICRONUTRIENTES = {"B", "Zn", "Fe", "Mn", "Cu"}

FUENTE_ESPECIFICACION = "Composición suministrada en la especificación técnica del proyecto."


def _producto(**datos):
    """Completa los campos que falten con None / listas vacías."""

    base = {n: None for n in NUTRIENTES}
    base.update({
        "presentes_sin_cantidad": [],
        "imagenes_alternativas": [],
        "categorias": [],
        "etapas": [],
        "objetivos": [],
        "observaciones": "",
        "fuente": "",
        "composicion_confirmada": True,
        "efecto_acidificante": None,
        "clave_legacy": None,
        "nombre_bd": None,
        "alias": [],
    })
    base.update(datos)
    return base


# Etapas fisiológicas (ver motor_recomendacion.ETAPAS_POR_TEMPORADA)
LLENADO = "llenado de fruto"
MADURACION = "maduración"
PREFLORACION = "prefloración"
FLORACION = "floración"
CUAJADO = "cuajado"
POSTCOSECHA = "postcosecha/recuperación"
VEGETATIVO = "desarrollo vegetativo"

FUENTE_ETAPAS = (
    "Etapas según el uso descrito en el código existente "
    "(INFO_ABONOS y puntaje_temporada) y la ficha comercial."
)


CATALOGO = [

    _producto(
        id=1, nombre="ABOTEK", marca="Yara", clave_legacy="ABOTEK",
        nombre_bd="ABOTEK 15 – 4 – 23 + 4% MgO + 2% S + 0.1% B + 0.1% Zn",
        imagen="abonos/1.png", tipo="edafico", categorias=["compuesto NPK"],
        N=15, P=4, K=23, Mg=4, S=2, B=0.1, Zn=0.1,
        etapas=[LLENADO, MADURACION], objetivos=["produccion"],
        fuente=FUENTE_ESPECIFICACION + " Coincide con el registro de la base de datos.",
    ),

    _producto(
        id=2, nombre="EMBAJADOR KS", marca="Yara", clave_legacy="EMBAJADOR KS",
        nombre_bd="EMBAJADOR KS 20-3-18-3MgO-2S-0.1Zn-0.1B",
        imagen="abonos/2.png", tipo="edafico", categorias=["compuesto NPK"],
        N=20, P=4, K=18, Mg=3, S=3, B=0.1, Zn=0.1,
        etapas=[LLENADO, MADURACION], objetivos=["produccion"],
        fuente="Ficha Yara Colombia (Embajador KS 20-4-18) y especificación del proyecto.",
        observaciones=(
            "El código anterior y la base de datos registraban la formulación "
            "anterior 20-3-18-3MgO-2S; se usa la ficha vigente 20-4-18 + 3 MgO + 3 S."
        ),
    ),

    _producto(
        id=3, nombre="Nutrimon 15-15-15", marca="Nutrimon", clave_legacy="NUTRIMON 15-15-15",
        nombre_bd="NUTRIMON 15-15-15",
        imagen="abonos/3.png", tipo="edafico", categorias=["compuesto NPK"],
        N=15, P=15, K=15,
        objetivos=["nutricion_general"],
        fuente="Grado garantizado en la etiqueta (15-15-15).",
        observaciones="Nutrientes secundarios y menores no registrados.",
    ),

    _producto(
        id=4, nombre="Katiuska 18-6-18", marca="Ferticolombia", clave_legacy="KATIUSKA",
        nombre_bd="KATIUSKA 18 – 6 – 18 – 2 (MgO) – 2 (S)",
        imagen="abonos/4.png", tipo="edafico", categorias=["compuesto NPK"],
        N=18, P=6, K=18, Mg=2, S=2,
        etapas=[LLENADO], objetivos=["produccion"],
        fuente=FUENTE_ESPECIFICACION,
    ),

    _producto(
        id=5, nombre="Bonanza 19-9-19 + 1 CaO", marca="Ferticolombia", clave_legacy="BONANZA",
        nombre_bd="BONANZA 19 9 19-1(CAO)",
        imagen="abonos/5.png", imagenes_alternativas=["abonos/27.png"],
        tipo="edafico", categorias=["compuesto NPK", "fuente de Ca"],
        N=19, P=9, K=19, Ca=1,
        objetivos=["nutricion_general"],
        fuente=FUENTE_ESPECIFICACION,
        observaciones="Las imágenes 5 y 27 del catálogo corresponden al mismo producto.",
    ),

    _producto(
        id=6, nombre="Urea 46", marca="AgroCafé", clave_legacy="Urea 46-0-0",
        nombre_bd="Urea 46-0-0",
        imagen="abonos/6.png", tipo="edafico", categorias=["simple", "fuente de N"],
        N=46, P=0, K=0, Ca=0, Mg=0, S=0,
        objetivos=["aporte_N"],
        fuente=FUENTE_ESPECIFICACION,
    ),

    _producto(
        id=7, nombre="MicroEssentials SZ 12-40-0", marca="Nutrimon", clave_legacy="MicroEssentials",
        nombre_bd="NUTRIMON MicroEssentials 12-40-0-10(s)",
        imagen="abonos/7.png", tipo="edafico",
        categorias=["compuesto", "fuente de P", "fuente de S"],
        N=12, P=40, K=0, S=10, presentes_sin_cantidad=["Zn"],
        etapas=[PREFLORACION, FLORACION], objetivos=["aporte_P"],
        fuente=FUENTE_ESPECIFICACION,
        observaciones=(
            "La referencia SZ indica aporte de zinc (el código anterior lo "
            "registraba); la cantidad de Zn no está confirmada."
        ),
    ),

    _producto(
        id=8, nombre="YaraMila HYDRAN", marca="Yara", clave_legacy="HYDRAN",
        nombre_bd="YaraMila HYDRAN 19-4-19",
        imagen="abonos/8.png", tipo="edafico", categorias=["compuesto NPK"],
        N=18.7, P=4, K=18.8, Mg=3, S=1.8, presentes_sin_cantidad=["B", "Zn"],
        etapas=[LLENADO, POSTCOSECHA], objetivos=["produccion"],
        fuente=FUENTE_ESPECIFICACION,
    ),

    _producto(
        id=9, nombre="Nutricarga 19-4-18", marca="Nutrimon", clave_legacy="NUTRICARGA",
        nombre_bd="NUTRICARGA 19 – 4 – 18 – 3 (MgO) – 2 (S) – 0.1 (B) – 0.1 (Zn)",
        imagen="abonos/9.png", tipo="edafico", categorias=["compuesto NPK"],
        N=19, P=4, K=18, Mg=3, S=2, B=0.1, Zn=0.1,
        etapas=[POSTCOSECHA], objetivos=["recuperacion"],
        fuente=FUENTE_ESPECIFICACION + " Cantidades de B y Zn según el registro de la base de datos.",
    ),

    _producto(
        id=10, nombre="Sulfato de Amonio 21-0-0-24(S)", marca="Nutrimon",
        clave_legacy="NUTRIMON Sulfato de Amonio",
        nombre_bd="NUTRIMON Sulfato de Amonio 21-0-0-24(s)",
        imagen="abonos/10.png", tipo="edafico",
        categorias=["simple", "fuente de N", "fuente de S"],
        N=21, P=0, K=0, S=24,
        objetivos=["aporte_N", "aporte_S"],
        efecto_acidificante="alto",
        fuente=FUENTE_ESPECIFICACION,
        observaciones="Fuente amoniacal de reacción ácida en el suelo.",
    ),

    _producto(
        id=11, nombre="REMITAL-M", marca="Yara", clave_legacy="REMITAL",
        nombre_bd="REMITAL 17 – 6 – 18 + 2 (MgO)",
        imagen="abonos/11.png", tipo="edafico", categorias=["compuesto NPK"],
        N=17, P=6, K=18, Mg=2, S=1.6, presentes_sin_cantidad=["B", "Zn"],
        etapas=[LLENADO, MADURACION], objetivos=["produccion"],
        fuente=FUENTE_ESPECIFICACION,
    ),

    _producto(
        id=12, nombre="YaraVera AMIDAS", marca="Yara", clave_legacy="YaraVera AMIDAS",
        nombre_bd="YaraVera AMIDAS 40-5-35-5.6(s)",
        imagen="abonos/12.png", tipo="edafico", categorias=["simple", "fuente de N", "fuente de S"],
        N=40, P=0, K=0, S=5.6,
        objetivos=["aporte_N"],
        fuente=FUENTE_ESPECIFICACION,
        observaciones=(
            "El nombre registrado en la base de datos (40-5-35-5.6) no "
            "corresponde al grado del producto; se usa 40-0-0 + 5.6 S."
        ),
    ),

    _producto(
        id=13, nombre="KCl 0-0-60", marca="Nutrimon", clave_legacy="Cloruro de Potasio",
        nombre_bd="Cloruro de Potasio KCL Gr 0-0-60",
        imagen="abonos/13.png", tipo="edafico", categorias=["simple", "fuente de K"],
        N=0, P=0, K=60, Ca=0, Mg=0, S=0,
        objetivos=["aporte_K"],
        fuente=FUENTE_ESPECIFICACION,
    ),

    _producto(
        id=14, nombre="DAP 18-46-0", marca="Nutrimon", clave_legacy="Fosfato Diamónico",
        nombre_bd="Fosfato Diamónico 18-46-0",
        imagen="abonos/14.png", tipo="edafico", categorias=["compuesto", "fuente de P", "fuente de N"],
        N=18, P=46, K=0,
        etapas=[PREFLORACION, FLORACION], objetivos=["aporte_P"],
        fuente=FUENTE_ESPECIFICACION,
    ),

    _producto(
        id=15, nombre="NITRAX-S", marca="Yara", clave_legacy="NITRAX-S",
        nombre_bd="NITRAX-S 28-4-0-6S",
        imagen="abonos/15.png", tipo="edafico", categorias=["compuesto", "fuente de N", "fuente de S"],
        N=28, P=4, K=0, S=6,
        objetivos=["aporte_N"],
        fuente=FUENTE_ESPECIFICACION,
    ),

    _producto(
        id=16, nombre="YaraMila HYDROCOMPLEX", marca="Yara", clave_legacy="HYDROCOMPLEX",
        nombre_bd="YaraMila HYDROCOMPLEX 12-11-18",
        imagen="abonos/16.png", tipo="edafico", categorias=["compuesto NPK", "micronutrientes"],
        N=12.4, P=11.4, K=17.7, Mg=2.65, S=8,
        presentes_sin_cantidad=["B", "Fe", "Mn", "Zn"],
        etapas=[LLENADO, POSTCOSECHA], objetivos=["nutricion_completa"],
        fuente=FUENTE_ESPECIFICACION,
        observaciones="Micronutrientes según el registro del código anterior; cantidades no confirmadas.",
    ),

    _producto(
        id=17, nombre="YaraVita", marca="Yara", clave_legacy=None,
        nombre_bd="YaraVita Zintrac MgB",
        imagen="abonos/17.png", tipo="foliar", categorias=["foliar"],
        composicion_confirmada=False,
        fuente="",
        observaciones=(
            "La imagen no permite identificar la referencia YaraVita. En la base "
            "de datos figura como 'YaraVita Zintrac MgB' sin composición verificada."
        ),
    ),

    _producto(
        id=18, nombre="YaraVita CaBtrac", marca="Yara", clave_legacy="YaraVita CaBtrac",
        nombre_bd="YaraVita CaBtrac",
        imagen="abonos/18.png", tipo="foliar", categorias=["foliar", "fuente de Ca", "micronutrientes"],
        presentes_sin_cantidad=["Ca", "B", "Zn"],
        etapas=[FLORACION, CUAJADO], objetivos=["aporte_Ca", "aporte_B", "aporte_Zn"],
        fuente=FUENTE_ESPECIFICACION + " Producto foliar de Ca + B + Zn.",
        observaciones="Cantidades de Ca, B y Zn no registradas. Uso exclusivamente foliar.",
    ),

    _producto(
        id=19, nombre="Agrocosecha 26-4-22", marca="AgroCafé", clave_legacy="Agrocosecha",
        nombre_bd="Agrocosecha 26-4-22",
        imagen="abonos/19.png", imagenes_alternativas=["abonos/28.png"],
        tipo="edafico", categorias=["compuesto NPK"],
        N=26, P=4, K=22,
        etapas=[LLENADO, MADURACION], objetivos=["produccion"],
        fuente=FUENTE_ESPECIFICACION,
        observaciones="Las imágenes 19 y 28 del catálogo corresponden al mismo producto.",
    ),

    _producto(
        id=20, nombre="Nitrosoil 23-4-20-3", marca="Nitrosoil",
        nombre_bd="Nitrosoil 23-4-20-3",
        imagen="abonos/20.png", tipo="edafico", categorias=["compuesto NPK"],
        N=23, P=4, K=20, Mg=3, presentes_sin_cantidad=["S"],
        etapas=[LLENADO], objetivos=["produccion"],
        fuente="Ficha Nitrosoil / vademécum PLM: 23-4-20-3 (MgO).",
        observaciones="Contiene azufre según la ficha; cantidad no registrada.",
    ),

    _producto(
        id=21, nombre="Ecofertil 25-4-24", marca="Ecofértil", clave_legacy="Ecofertil",
        nombre_bd="Ecofertil 25-4-24",
        imagen="abonos/21.png", tipo="edafico", categorias=["compuesto NPK"],
        N=25, P=4, K=24,
        etapas=[LLENADO], objetivos=["produccion"],
        fuente="Composición garantizada de la ficha comercial (25-4-24).",
        observaciones="Nutrientes secundarios y menores no registrados.",
    ),

    _producto(
        id=22, nombre="Nutrimon 10-20-20", marca="Nutrimon", clave_legacy="Nutrimon 10-20-20",
        nombre_bd="Nutrimon 10-20-20",
        imagen="abonos/22.png", tipo="edafico", categorias=["compuesto NPK"],
        N=10, P=20, K=20,
        objetivos=["aporte_P", "aporte_K"],
        fuente="Grado garantizado en la etiqueta (10-20-20).",
        observaciones="Nutrientes secundarios y menores no registrados.",
    ),

    _producto(
        id=23, nombre="Yara 10-30-10", marca="Yara", clave_legacy="Yara 10-30-10",
        nombre_bd="Yara 10-30-10",
        imagen="abonos/23.png", tipo="edafico", categorias=["compuesto NPK", "fuente de P"],
        N=10, P=30, K=10,
        etapas=[PREFLORACION, FLORACION], objetivos=["aporte_P"],
        fuente="Grado garantizado en la etiqueta (10-30-10).",
        observaciones="Nutrientes secundarios y menores no registrados.",
    ),

    _producto(
        id=24, nombre="YaraMila INTEGRADOR", marca="Yara",
        nombre_bd="YaraMila integrador 15-9-20-4",
        imagen="abonos/24.png", tipo="edafico", categorias=["compuesto NPK", "micronutrientes"],
        N=15, P=9, K=20, Mg=1.8, S=3.8, B=0.015, Mn=0.02, Zn=0.02,
        etapas=[LLENADO], objetivos=["produccion"],
        fuente="Ficha técnica Yara CO-FT916 (YaraMila INTEGRADOR 15-9-20).",
    ),

    _producto(
        id=25, nombre="Café Café", marca="",
        nombre_bd="Café Café",
        imagen="abonos/25.png", tipo="edafico",
        composicion_confirmada=False,
        observaciones="Composición no confirmada: no se encontró la ficha del producto.",
    ),

    _producto(
        id=26, nombre="Yara 18-18-18", marca="Yara", clave_legacy="Yara 18-18-18",
        nombre_bd="Yara18-18-18",
        imagen="abonos/26.png", tipo="edafico", categorias=["compuesto NPK"],
        N=18, P=18, K=18,
        objetivos=["nutricion_general"],
        fuente="Grado garantizado en la etiqueta (18-18-18).",
        observaciones="Nutrientes secundarios y menores no registrados.",
    ),

    _producto(
        id=29, nombre="Nutrimon Producción 17-6-18-2", marca="Nutrimon",
        clave_legacy="Nutrimon produccion 17-6-18-2",
        nombre_bd="Nutrimon produccion 17-6-18-2",
        imagen="abonos/29.png", tipo="edafico", categorias=["compuesto NPK"],
        N=17, P=6, K=18, Mg=2,
        etapas=[FLORACION, CUAJADO, LLENADO], objetivos=["produccion"],
        fuente="Composición garantizada Monómeros: 17-6-18-2 (MgO).",
    ),
]


for _p in CATALOGO:
    _p.setdefault("fuente_etapas", FUENTE_ETAPAS if _p["etapas"] else "")


def producto_por_id(producto_id):
    return next((p for p in CATALOGO if p["id"] == producto_id), None)


def producto_por_clave_legacy(clave):
    if not clave:
        return None
    clave = str(clave).strip().lower()
    return next(
        (p for p in CATALOGO if (p["clave_legacy"] or "").lower() == clave),
        None,
    )


def aporta(producto, nutriente):
    """True si el producto aporta el nutriente (cantidad > 0 o presente sin cantidad)."""

    valor = producto.get(nutriente)
    if valor is not None and valor > 0:
        return True
    return nutriente in producto.get("presentes_sin_cantidad", [])


def nutrientes_aportados(producto):
    return [n for n in NUTRIENTES if aporta(producto, n)]


def texto_composicion(producto):
    """Ej.: '15-4-23 + 4 MgO + 2 S + 0.1 B + 0.1 Zn'."""

    if not producto.get("composicion_confirmada"):
        return "Composición no confirmada"

    def num(v):
        return f"{v:g}"

    partes = []
    if all(producto.get(n) is not None for n in ("N", "P", "K")):
        partes.append(f"{num(producto['N'])}-{num(producto['P'])}-{num(producto['K'])}")

    extras = [("Ca", "CaO"), ("Mg", "MgO"), ("S", "S"), ("B", "B"),
              ("Zn", "Zn"), ("Fe", "Fe"), ("Mn", "Mn"), ("Cu", "Cu")]
    for clave, etiqueta in extras:
        valor = producto.get(clave)
        if valor:
            partes.append(f"{num(valor)} {etiqueta}")
        elif clave in producto.get("presentes_sin_cantidad", []):
            partes.append(etiqueta)

    return " + ".join(partes) if partes else "Composición no registrada"
