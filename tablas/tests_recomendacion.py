from django.test import TestCase

from .catalogo_fertilizantes import CATALOGO, aporta
from .motor_recomendacion import recomendar
from .recomendador import construir_sugerencia_integrada, recomendar_abono


def deficiencia(clase, confianza, **extra):
    return {"estado": "deficiency", "clase": clase, "etiqueta": clase,
            "confianza": confianza, **extra}


FOLIAR_K_BAJO = {"K": 1.2, "N": 2.5, "P": 0.17, "Mg": 0.3, "S": 0.17}
SUELO_BASICO = {"ph": 5.3, "materia_organica": 8, "K": 0.2}


class CatalogoTests(TestCase):

    def test_ids_e_imagenes_unicos(self):
        ids = [p["id"] for p in CATALOGO]
        self.assertEqual(len(ids), len(set(ids)))
        imagenes = [p["imagen"] for p in CATALOGO]
        self.assertEqual(len(imagenes), len(set(imagenes)))

    def test_no_confirmados_sin_nutrientes(self):
        for p in CATALOGO:
            if not p["composicion_confirmada"]:
                self.assertFalse(any(aporta(p, n) for n in ("N", "P", "K")), p["nombre"])


class DecisionTests(TestCase):

    def productos(self, r):
        return [i["producto"]["nombre"] for i in r["productos_recomendados"] + r["recomendaciones_foliares"]]

    def test_solo_visual_no_recomienda(self):
        r = recomendar(deficiencia("def_potasio", 0.87), {"temporada": "cosecha"})
        self.assertEqual(r["nivel_confianza"], "BAJA")
        self.assertEqual(r["decision"], "no_recomendar")
        self.assertEqual(self.productos(r), [])
        self.assertEqual(r["diagnostico_visual"]["descripcion"], "Posible deficiencia de potasio")

    def test_visual_mas_ph_es_media_pero_insuficiente(self):
        r = recomendar(deficiencia("def_potasio", 0.87),
                       {"temporada": "cosecha", "ph": 5.4, "humedad": 60, "temperatura": 21})
        self.assertEqual(r["nivel_confianza"], "MEDIA")
        self.assertEqual(r["decision"], "no_recomendar")
        self.assertTrue(any("insuficiente" in m for m in r["motivos_no_recomendacion"]))

    def test_confirmado_por_foliar_recomienda_con_k(self):
        r = recomendar(deficiencia("def_potasio", 0.87),
                       {"temporada": "cosecha", "analisis_foliar": FOLIAR_K_BAJO})
        self.assertEqual(r["nivel_confianza"], "ALTA")
        self.assertEqual(r["decision"], "recomendar")
        for item in r["productos_recomendados"]:
            self.assertIn("K", item["nutrientes_aportados"])
            self.assertTrue(item["razones"])
            self.assertTrue(item["producto"]["imagen"])
        nombres = self.productos(r)
        self.assertNotIn("DAP 18-46-0", nombres)
        self.assertNotIn("YaraVita CaBtrac", nombres)
        puntos = [i["puntuacion"] for i in r["productos_recomendados"]]
        self.assertEqual(puntos, sorted(puntos, reverse=True))

    def test_nk_supera_producto_alto_en_p_sin_k(self):
        # Necesidad de K (N adecuado): un producto con P muy alto y K = 0
        # queda fuera; uno N-K con P bajo queda entre los recomendados.
        r = recomendar(deficiencia("def_potasio", 0.9),
                       {"temporada": "cosecha", "analisis_foliar": FOLIAR_K_BAJO})
        excluidos = {e["producto"]["nombre"]: e["motivo"] for e in r["productos_excluidos"]}
        self.assertIn("DAP 18-46-0", excluidos)
        self.assertIn("MicroEssentials SZ 12-40-0", excluidos)
        self.assertIn("ABOTEK", self.productos(r))

    def test_p_muy_alto_innecesario_penalizado(self):
        r = recomendar(deficiencia("def_potasio", 0.9),
                       {"temporada": "cosecha", "analisis_foliar": {"K": 1.2, "N": 2.0}})
        todos = {i["producto"]["nombre"]: i for i in r["productos_recomendados"]}
        self.assertNotIn("Yara 10-30-10", todos)
        self.assertNotIn("DAP 18-46-0", todos)

    def test_foliar_contradice_descarta(self):
        r = recomendar(deficiencia("def_potasio", 0.9),
                       {"temporada": "cosecha", "analisis_foliar": {"K": 1.9}})
        self.assertEqual(r["hipotesis_nutricional"][0]["estado"], "descartado")
        self.assertEqual(r["decision"], "no_recomendar")

    def test_confianza_baja_no_concluyente(self):
        r = recomendar(deficiencia("def_potasio", 0.12),
                       {"temporada": "cosecha", "analisis_foliar": FOLIAR_K_BAJO})
        self.assertEqual(r["nivel_confianza"], "NO CONCLUYENTE")
        self.assertEqual(r["decision"], "no_recomendar")

    def test_ambiguo_no_concluyente(self):
        r = recomendar(deficiencia("def_potasio", 0.62, detecciones_secundarias=[
            {"clase": "def_magnesio", "confianza": 0.60}]),
            {"temporada": "cosecha", "analisis_foliar": FOLIAR_K_BAJO})
        self.assertEqual(r["nivel_confianza"], "NO CONCLUYENTE")

    def test_enfermedad_no_recomienda(self):
        r = recomendar({"estado": "alert", "clase": "roya", "etiqueta": "Roya del café",
                        "confianza": 0.95},
                       {"temporada": "cosecha", "analisis_suelo": SUELO_BASICO})
        self.assertEqual(r["decision"], "no_recomendar")
        self.assertTrue(any("enfermedad" in m for m in r["motivos_no_recomendacion"]))

    def test_hoja_sana_sin_necesidad(self):
        r = recomendar({"estado": "healthy", "clase": "hoja_sana", "confianza": 0.9},
                       {"temporada": "cosecha", "ph": 5.4})
        self.assertEqual(r["decision"], "no_recomendar")

    def test_cobre_sin_producto_confirmado(self):
        r = recomendar(deficiencia("def_cobre", 0.9),
                       {"temporada": "cosecha", "analisis_foliar": {"Cu": 4}})
        self.assertEqual(r["decision"], "no_recomendar")
        self.assertTrue(any("cobre" in m for m in r["motivos_no_recomendacion"]))

    def test_calcio_usa_foliar_separado(self):
        r = recomendar(deficiencia("def_calcio", 0.85),
                       {"temporada": "florescencia", "analisis_foliar": {"Ca": 0.5}})
        self.assertEqual(r["decision"], "recomendar")
        foliares = [i["producto"]["nombre"] for i in r["recomendaciones_foliares"]]
        self.assertIn("YaraVita CaBtrac", foliares)
        for i in r["productos_recomendados"]:
            self.assertEqual(i["producto"]["tipo"], "edafico")

    def test_no_confirmados_nunca_se_recomiendan(self):
        r = recomendar(deficiencia("def_potasio", 0.9),
                       {"temporada": "cosecha", "analisis_foliar": FOLIAR_K_BAJO})
        self.assertNotIn("Café Café", self.productos(r))
        self.assertNotIn("YaraVita", self.productos(r))

    def test_acidificante_penalizado_con_ph_acido(self):
        r = recomendar(deficiencia("def_nitrogeno", 0.9),
                       {"temporada": "recuperacion", "ph": 4.6,
                        "analisis_foliar": {"N": 1.8}})
        sulfato = next((i for i in r["productos_recomendados"]
                        if i["producto"]["nombre"].startswith("Sulfato")), None)
        if sulfato:
            self.assertTrue(any("ácida" in a for a in sulfato["advertencias"]))

    def test_sin_dosis_inventadas(self):
        r = recomendar(deficiencia("def_potasio", 0.9),
                       {"temporada": "cosecha", "analisis_foliar": FOLIAR_K_BAJO})
        self.assertIn("requiere recomendación técnica", r["dosis"])


class DatosFaltantesTests(TestCase):

    def test_none_no_se_convierte_en_cero(self):
        r = recomendar(deficiencia("def_potasio", 0.9), {"temporada": "cosecha",
                       "ph": None, "humedad": "", "temperatura": None})
        self.assertIsNone(r["validacion"]["ph"])
        self.assertIsNone(r["validacion"]["humedad_suelo"])
        self.assertIn("pH", r["datos_faltantes"])

    def test_cero_real_se_respeta(self):
        r = recomendar(deficiencia("def_potasio", 0.9), {"temporada": "cosecha", "humedad": 0})
        self.assertEqual(r["validacion"]["humedad_suelo"], 0)

    def test_reglas_legacy_no_inventan_valores(self):
        self.assertEqual(recomendar_abono(None, None, None, "cosecha",
                                          usar_sensores=False, condicion_climatica="seca"), [])
        self.assertTrue(recomendar_abono(5.5, 60, 21, "cosecha"))

    def test_sugerencia_integrada_compatible(self):
        s = construir_sugerencia_integrada(
            None, None, None, "cosecha", [],
            {"estado": "deficiency", "etiqueta": "Deficiencia de potasio", "clase": "def_potasio",
             "confianza": 0.9},
            variedad="castillo", usar_sensores=False, condicion_climatica="seca",
            analisis_foliar=FOLIAR_K_BAJO,
        )
        for clave in ("abono", "abonos", "productos_recomendados", "texto", "tratamiento", "recomendacion"):
            self.assertIn(clave, s)
        self.assertTrue(s["productos_recomendados"][0]["imagenes"][0]["url"])


class RecomendacionVisualTests(TestCase):
    """Capa adicional: abonos preliminares a partir de la deficiencia visual."""

    def visual(self, diagnostico, contexto=None):
        return recomendar(diagnostico, contexto or {"temporada": "cosecha"})["recomendacion_visual"]

    def test_deficiencia_sin_datos_produce_abonos(self):
        v = self.visual(deficiencia("def_potasio", 0.87))
        self.assertEqual(v["tipo_recomendacion"], "visual_preliminar")
        self.assertTrue(v["productos"])
        self.assertIn("preliminar", v["advertencia"])

    def test_productos_reales_confirmados_con_el_nutriente_e_imagen_propia(self):
        v = self.visual(deficiencia("def_nitrogeno", 0.8))
        por_id = {p["id"]: p for p in CATALOGO}
        for item in v["productos"] + v["foliares"]:
            original = por_id[item["id"]]
            self.assertTrue(original["composicion_confirmada"])
            self.assertTrue(aporta(original, "N"))
            self.assertTrue(item["imagen"].endswith(original["imagen"]))
        puntos = [i["score"] for i in v["productos"]]
        self.assertEqual(puntos, sorted(puntos, reverse=True))

    def test_varias_deficiencias_priorizan_cobertura(self):
        v = self.visual(deficiencia("def_nitrogeno", 0.8, detecciones_secundarias=[
            {"clase": "def_potasio", "confianza": 0.6},
            {"clase": "def_magnesio", "confianza": 0.5}]))
        self.assertEqual([d["nutriente"] for d in v["nutrientes_detectados"]], ["N", "K", "Mg"])
        primero = v["productos"][0]
        self.assertEqual(set(primero["nutrientes_detectados"]), {"N", "K", "Mg"})
        urea = next((i for i in v["productos"] if i["nombre"] == "Urea 46"), None)
        self.assertIsNone(urea)

    def test_enfermedad_con_deficiencia_es_apoyo_no_tratamiento(self):
        v = self.visual({"estado": "alert", "clase": "roya", "etiqueta": "Roya del café",
                         "confianza": 0.9,
                         "detecciones_secundarias": [{"clase": "def_nitrogeno", "confianza": 0.4}]})
        self.assertEqual(v["tipo_recomendacion"], "apoyo_nutricional_preliminar")
        self.assertIn("no tratan", v["nota_enfermedad"])
        for item in v["productos"]:
            texto = " ".join(item["razones"] + [item["motivo"]]).lower()
            self.assertNotIn("roya", texto)

    def test_enfermedad_sola_no_genera_abonos(self):
        self.assertIsNone(self.visual({"estado": "alert", "clase": "roya", "confianza": 0.9}))

    def test_nutriente_sin_producto_no_inventa(self):
        v = self.visual(deficiencia("def_cobre", 0.8))
        self.assertEqual(v["productos"] + v["foliares"], [])
        self.assertIn("No se encontraron abonos", v["mensaje_sin_producto"])

    def test_agronomica_intacta_cuando_hay_evidencia(self):
        r = recomendar(deficiencia("def_potasio", 0.87),
                       {"temporada": "cosecha", "analisis_foliar": FOLIAR_K_BAJO})
        self.assertEqual(r["decision"], "recomendar")
        self.assertIsNone(r["recomendacion_visual"])

    def test_no_se_usa_si_el_foliar_descarta_o_la_confianza_es_baja(self):
        self.assertIsNone(self.visual(deficiencia("def_potasio", 0.9),
                                      {"temporada": "cosecha", "analisis_foliar": {"K": 1.9}}))
        self.assertIsNone(self.visual(deficiencia("def_potasio", 0.12)))

    def test_decision_agronomica_no_cambia(self):
        r = recomendar(deficiencia("def_potasio", 0.87), {"temporada": "cosecha"})
        self.assertEqual(r["decision"], "no_recomendar")
        self.assertEqual(r["productos_recomendados"], [])
