import os
import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from cuentas.models import Perfil
from tablas.models import Arduino, DatoSuelo, Finca, Producto, TipoAbono, TipoAbonoImagen
from tablas.recomendador import REGLAS_ABONOS


def _abonos_del_recomendador():
    """Todos los abonos únicos que el motor de reglas puede recomendar."""
    nombres = []
    for regla in REGLAS_ABONOS:
        n = regla.get('nombre')
        if n and n not in nombres:
            nombres.append(n)
    return nombres

# Fincas de ejemplo (sector cafetero del Huila) con sus dispositivos.
FINCAS = [
    ('Finca El Progreso', 'Acevedo - Huila', ['Sensor Lote Alto', 'Sensor Lote Bajo']),
    ('Hacienda La Esperanza', 'Pitalito - Huila', ['Sensor Norte']),
    ('Finca La Primavera', 'Garzón - Huila', ['Sensor Cafetal', 'Sensor Beneficiadero']),
    ('Finca Buenavista', 'Gigante - Huila', ['Sensor Principal']),
]

# Todos los abonos que puede recomendar el sistema (extraídos del recomendador).
ABONOS = _abonos_del_recomendador()

DESCRIPCIONES = {
    'default': 'Fertilizante recomendado según el análisis de pH, humedad y temperatura del suelo. Mejora la nutrición del cafeto y la calidad del grano.',
}


def _imagenes_disponibles():
    carpeta = os.path.join(settings.MEDIA_ROOT, 'abonos')
    if not os.path.isdir(carpeta):
        return []
    return sorted(f for f in os.listdir(carpeta) if f.lower().endswith('.png'))


class Command(BaseCommand):
    help = 'Carga datos de demostración realistas (fincas, sensores, lecturas y abonos).'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Borra fincas/lecturas/abonos antes de cargar.')

    def handle(self, *args, **options):
        rng = random.Random(42)  # reproducible

        if options['reset']:
            DatoSuelo.objects.all().delete()
            Arduino.objects.all().delete()
            Producto.objects.all().delete()
            TipoAbonoImagen.objects.all().delete()
            Finca.objects.all().delete()
            self.stdout.write(self.style.WARNING('Datos previos borrados (--reset).'))

        # ---- Usuario demo ----
        email = 'demo@cafe.com'
        user, creado = User.objects.get_or_create(
            username=email, defaults={'email': email, 'first_name': 'Daniel', 'last_name': 'Rojas'},
        )
        if creado:
            user.set_password('demo12345')
            user.save()
        Perfil.objects.get_or_create(usuario=user, defaults={'ubicacion': 'Neiva - Huila'})

        # ---- Fincas, arduinos y lecturas ----
        ahora = timezone.now()
        total_lecturas = 0
        for nombre, ubic, sensores in FINCAS:
            finca, _ = Finca.objects.get_or_create(nombre=nombre, usuario=user, defaults={'ubicacion': ubic})
            for sensor in sensores:
                arduino, _ = Arduino.objects.get_or_create(finca=finca, nombre=sensor)
                if DatoSuelo.objects.filter(arduino=arduino).exists():
                    continue
                # ~45 lecturas por sensor, una cada ~16 h durante el último mes
                ph = rng.uniform(4.6, 6.4)
                hum = rng.uniform(35, 75)
                temp = rng.uniform(15, 30)
                lote = []
                for i in range(45):
                    # paseo aleatorio suave para que parezca medición real
                    ph = min(6.6, max(4.2, ph + rng.uniform(-0.15, 0.15)))
                    hum = min(85, max(25, hum + rng.uniform(-4, 4)))
                    temp = min(33, max(12, temp + rng.uniform(-1.2, 1.2)))
                    lote.append(DatoSuelo(
                        arduino=arduino,
                        ph=round(ph, 2),
                        humedad=round(hum, 1),
                        temperatura=round(temp, 1),
                        fecha=ahora - timedelta(hours=i * 16, minutes=rng.randint(0, 59)),
                    ))
                DatoSuelo.objects.bulk_create(lote)
                total_lecturas += len(lote)

        finca_principal = Finca.objects.filter(usuario=user).first()

        # ---- Tipos de abono + productos + imágenes ----
        imagenes = _imagenes_disponibles()
        for idx, nombre in enumerate(ABONOS):
            tipo, _ = TipoAbono.objects.get_or_create(nombre=nombre)
            Producto.objects.get_or_create(
                nombre=nombre, tipo_abono=tipo, finca=finca_principal,
                defaults={'descripcion': DESCRIPCIONES['default']},
            )
            if imagenes and not tipo.imagenes.exists():
                archivo = imagenes[idx % len(imagenes)]
                TipoAbonoImagen.objects.create(
                    tipo_abono=tipo, imagen=f'abonos/{archivo}',
                    titulo=nombre, orden=0, es_principal=True,
                )

        self.stdout.write(self.style.SUCCESS(
            f'Seed completado: {Finca.objects.filter(usuario=user).count()} fincas, '
            f'{Arduino.objects.count()} sensores, {DatoSuelo.objects.count()} lecturas, '
            f'{TipoAbono.objects.count()} abonos.'
        ))
        self.stdout.write(self.style.SUCCESS('Usuario demo: demo@cafe.com / demo12345'))
