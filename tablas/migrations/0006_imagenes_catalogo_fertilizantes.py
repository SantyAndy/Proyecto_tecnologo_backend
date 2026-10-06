"""
Asocia cada tipo de abono con su imagen real de media/abonos/.

Situación encontrada: 22 de 26 imágenes registradas apuntaban a archivos
que no existen en este proyecto (p. ej. abonos/10_wIaKjVZ.png) y otras
estaban cruzadas (Yara 18-18-18 mostraba ABOTEK, Nitrosoil mostraba
EMBAJADOR, KATIUSKA la del DAP...).

- Registro con archivo inexistente → se corrige la ruta.
- Registro con archivo existente pero de otro producto → deja de ser
  principal (no se borra).
- Tipos de abono del catálogo que no existían → se crean.
"""

import os

from django.conf import settings
from django.db import migrations


# nombre del TipoAbono → (imagen principal, imágenes alternativas)
IMAGENES = {
    "ABOTEK 15 – 4 – 23 + 4% MgO + 2% S + 0.1% B + 0.1% Zn": ("abonos/1.png", []),
    "EMBAJADOR KS 20-3-18-3MgO-2S-0.1Zn-0.1B": ("abonos/2.png", []),
    "NUTRIMON 15-15-15": ("abonos/3.png", []),
    "KATIUSKA 18 – 6 – 18 – 2 (MgO) – 2 (S)": ("abonos/4.png", []),
    "BONANZA 19 9 19-1(CAO)": ("abonos/5.png", ["abonos/27.png"]),
    "Urea 46-0-0": ("abonos/6.png", []),
    "NUTRIMON MicroEssentials 12-40-0-10(s)": ("abonos/7.png", []),
    "YaraMila HYDRAN 19-4-19": ("abonos/8.png", []),
    "NUTRICARGA 19 – 4 – 18 – 3 (MgO) – 2 (S) – 0.1 (B) – 0.1 (Zn)": ("abonos/9.png", []),
    "NUTRIMON Sulfato de Amonio 21-0-0-24(s)": ("abonos/10.png", []),
    "REMITAL 17 – 6 – 18 + 2 (MgO)": ("abonos/11.png", []),
    "YaraVera AMIDAS 40-5-35-5.6(s)": ("abonos/12.png", []),
    "Cloruro de Potasio KCL Gr 0-0-60": ("abonos/13.png", []),
    "Fosfato Diamónico 18-46-0": ("abonos/14.png", []),
    "NITRAX-S 28-4-0-6S": ("abonos/15.png", []),
    "YaraMila HYDROCOMPLEX 12-11-18": ("abonos/16.png", []),
    "YaraVita Zintrac MgB": ("abonos/17.png", []),
    "YaraVita CaBtrac": ("abonos/18.png", []),
    "Agrocosecha 26-4-22": ("abonos/19.png", ["abonos/28.png"]),
    "Nitrosoil 23-4-20-3": ("abonos/20.png", []),
    "Ecofertil 25-4-24": ("abonos/21.png", []),
    "Nutrimon 10-20-20": ("abonos/22.png", []),
    "Yara 10-30-10": ("abonos/23.png", []),
    "YaraMila integrador 15-9-20-4": ("abonos/24.png", []),
    "Café Café": ("abonos/25.png", []),
    "Yara18-18-18": ("abonos/26.png", []),
    "Nutrimon produccion 17-6-18-2": ("abonos/29.png", []),
}


def existe(ruta):
    return bool(ruta) and os.path.exists(os.path.join(settings.MEDIA_ROOT, ruta))


def asociar(apps, schema_editor):
    TipoAbono = apps.get_model("tablas", "TipoAbono")
    TipoAbonoImagen = apps.get_model("tablas", "TipoAbonoImagen")

    for nombre, (principal, alternativas) in IMAGENES.items():
        if not existe(principal):
            continue

        tipo = TipoAbono.objects.filter(nombre=nombre).first()
        if tipo is None:
            tipo = TipoAbono.objects.create(nombre=nombre)

        imagenes = list(TipoAbonoImagen.objects.filter(tipo_abono=tipo))
        correcta = next((i for i in imagenes if i.imagen.name == principal), None)

        for img in imagenes:
            if img is correcta:
                continue
            if not existe(img.imagen.name) and correcta is None:
                img.imagen.name = principal
                correcta = img
            elif img.es_principal:
                img.es_principal = False
            img.save()

        if correcta is None:
            correcta = TipoAbonoImagen.objects.create(
                tipo_abono=tipo, imagen=principal, titulo=nombre, orden=0,
            )

        correcta.es_principal = True
        correcta.orden = 0
        correcta.save()

        for orden, alternativa in enumerate(alternativas, start=1):
            if existe(alternativa) and not TipoAbonoImagen.objects.filter(
                tipo_abono=tipo, imagen=alternativa
            ).exists():
                TipoAbonoImagen.objects.create(
                    tipo_abono=tipo, imagen=alternativa, titulo=nombre,
                    orden=orden, es_principal=False,
                )


class Migration(migrations.Migration):

    dependencies = [
        ("tablas", "0005_finca_hectareas_tarifa_cobro"),
    ]

    operations = [
        migrations.RunPython(asociar, migrations.RunPython.noop),
    ]
