"""
Endpoints del módulo de Diagnóstico IA.

El frontend envía la imagen junto con el contexto seleccionado:

- variedad
- temporada
- usar_sensores
- desde
- hasta
- condicion_climatica

La finca NO se solicita al frontend.

Cuando usar_sensores=True:

1. Se obtiene automáticamente la finca del usuario autenticado.
2. Se consultan sus lecturas.
3. Se calculan los promedios de pH, humedad y temperatura.
4. Se envían esos valores al motor YOLO.
5. El motor utiliza el diagnóstico + temporada + variedad +
   condiciones de sensores para construir la recomendación.

Cuando usar_sensores=False:

1. No se consultan sensores.
2. Se utiliza la condición climática seleccionada.
"""

import json
import os
import tempfile
from datetime import datetime

from django.conf import settings
from PIL import Image, UnidentifiedImageError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .ia_yolo import motor_yolo
from .models import Diagnostico
from .serializers import DiagnosticoSerializer

from tablas.models import DatoSuelo, Finca
from tablas.motor_recomendacion import absolutizar_imagenes
from tablas.serializers import DatoSueloSerializer


# Formatos de imagen que acepta el análisis (Pillow -> extensión del archivo temporal).
FORMATOS_IMAGEN = {
    'JPEG': '.jpg',
    'PNG': '.png',
    'WEBP': '.webp',
    'BMP': '.bmp',
}


def validar_imagen(imagen):
    """
    Comprueba que el archivo subido sea de verdad una imagen y no pese demasiado.

    Devuelve (extension, None) si es válida o (None, mensaje_error).
    No se confía en el nombre ni en el tipo que manda el navegador: se abre
    el archivo con Pillow.
    """

    if imagen.size > settings.MAX_IMAGEN_BYTES:
        limite = settings.MAX_IMAGEN_BYTES // (1024 * 1024)
        return None, f'La imagen supera el tamaño máximo de {limite} MB.'

    try:
        with Image.open(imagen) as img:
            formato = img.format
            img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        return None, 'El archivo enviado no es una imagen válida.'
    finally:
        imagen.seek(0)

    if formato not in FORMATOS_IMAGEN:
        return None, 'Formato no permitido. Usa JPG, PNG, WEBP o BMP.'

    return FORMATOS_IMAGEN[formato], None


# ============================================================
# CALCULAR PROMEDIO
# ============================================================

def leer_json(valor):
    """
    Los análisis de laboratorio llegan como texto JSON dentro del
    multipart (o como dict si la petición es JSON). Vacío → None.
    """

    if not valor:
        return None

    if isinstance(valor, dict):
        return valor

    try:
        datos = json.loads(valor)
    except (TypeError, ValueError):
        return None

    return datos if isinstance(datos, dict) else None


def calcular_promedio(valores):
    """
    Calcula el promedio ignorando valores None.

    Sin lecturas válidas devuelve None ("dato no disponible"),
    nunca 0: un 0 se confundiría con una medición real.
    """

    valores_validos = [
        valor
        for valor in valores
        if valor is not None
    ]

    if not valores_validos:
        return None

    return round(
        sum(valores_validos) /
        len(valores_validos),
        2
    )


# ============================================================
# DIAGNÓSTICO VIEWSET
# ============================================================

class DiagnosticoViewSet(viewsets.ModelViewSet):
    """
    Historial de diagnósticos del usuario
    + análisis con IA
    + contexto del cultivo
    + datos de sensores.
    """

    serializer_class = DiagnosticoSerializer

    permission_classes = [
        IsAuthenticated
    ]

    parser_classes = [
        JSONParser,
        FormParser,
        MultiPartParser,
    ]

    def get_throttles(self):
        # El análisis con YOLO es costoso: se limita para que nadie sature el servidor.
        if self.action == 'analizar':
            self.throttle_scope = 'diagnostico'
        return super().get_throttles()


    # ========================================================
    # HISTORIAL
    # ========================================================

    def get_queryset(self):

        return (
            Diagnostico.objects
            .filter(
                usuario=self.request.user
            )
            .prefetch_related(
                'detecciones'
            )
        )


    # ========================================================
    # GUARDAR EN EL HISTORIAL
    # ========================================================

    def create(self, request, *args, **kwargs):
        """
        Acepta JSON (flujo anterior) o multipart con la imagen
        analizada. En multipart las listas y objetos llegan como
        texto JSON.
        """

        if hasattr(request.data, 'getlist'):

            datos = {
                clave: request.data.get(clave)
                for clave in request.data.keys()
                if clave != 'imagen'
            }

            for clave in ('detecciones', 'recomendacion_detalle'):
                if isinstance(datos.get(clave), str):
                    try:
                        datos[clave] = json.loads(datos[clave])
                    except ValueError:
                        datos.pop(clave)

            if request.FILES.get('imagen'):
                datos['imagen'] = request.FILES['imagen']

        else:

            datos = request.data

        serializer = self.get_serializer(data=datos)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


    # ========================================================
    # ANALIZAR IMAGEN
    # ========================================================

    @action(
        detail=False,
        methods=['post']
    )
    def analizar(self, request):
        """
        Analiza una imagen mediante YOLO.

        IMPORTANTE:

        La finca NO viene desde Angular.

        Si se utilizan sensores, la finca se obtiene
        automáticamente desde el usuario autenticado.

        Campos recibidos:

            imagen
            variedad
            temporada
            usar_sensores
            desde
            hasta
            condicion_climatica
        """

        # ====================================================
        # IMAGEN
        # ====================================================

        imagen = request.FILES.get(
            'imagen'
        )

        if not imagen:

            return Response(
                {
                    'detail':
                        'Debes enviar una imagen.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        sufijo, error_imagen = validar_imagen(imagen)

        if error_imagen:

            return Response(
                {
                    'detail':
                        error_imagen
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        # ====================================================
        # CONTEXTO DEL CULTIVO
        # ====================================================

        variedad = (
            request.data.get(
                'variedad'
            )
            or ''
        )

        temporada = (
            request.data.get(
                'temporada'
            )
            or 'cosecha'
        )

        usar_sensores_raw = (
            request.data.get(
                'usar_sensores'
            )
        )

        desde = (
            request.data.get(
                'desde'
            )
            or None
        )

        hasta = (
            request.data.get(
                'hasta'
            )
            or None
        )

        condicion_climatica = (
            request.data.get(
                'condicion_climatica'
            )
            or None
        )


        # ====================================================
        # CONVERTIR usar_sensores A BOOLEAN
        # ====================================================

        if isinstance(
            usar_sensores_raw,
            bool
        ):

            usar_sensores = (
                usar_sensores_raw
            )

        else:

            usar_sensores = str(
                usar_sensores_raw
            ).strip().lower() in [
                'true',
                '1',
                'si',
                'sí',
                'yes',
            ]


        # ====================================================
        # ORIGEN DE LOS DATOS DEL SUELO
        #   arduino → promedio de las lecturas de los sensores
        #   manual  → pH, humedad y temperatura escritos por el
        #             usuario (medidos sin Arduino)
        #   ninguno → solo la condición climática
        # ====================================================

        fuente_sensores = str(
            request.data.get('fuente_sensores') or ''
        ).strip().lower()

        if fuente_sensores not in ('arduino', 'manual', 'ninguno'):
            fuente_sensores = 'arduino' if usar_sensores else 'ninguno'

        usar_sensores = fuente_sensores == 'arduino'


        # ====================================================
        # VARIABLES DE SENSORES
        # ====================================================

        # None = dato no disponible (no se usa en las reglas).
        ph_promedio = None

        humedad_promedio = None

        temperatura_promedio = None

        cantidad_lecturas = 0

        lecturas = []

        finca = None

        finca_id = None


        # ====================================================
        # ANÁLISIS DE LABORATORIO (OPCIONALES)
        # ====================================================

        analisis_suelo = leer_json(
            request.data.get('analisis_suelo')
        )

        analisis_foliar = leer_json(
            request.data.get('analisis_foliar')
        )


        # ====================================================
        # MODALIDAD CON SENSORES
        # ====================================================

        if usar_sensores:

            # ------------------------------------------------
            # OBTENER AUTOMÁTICAMENTE LA FINCA DEL USUARIO
            # ------------------------------------------------

            fincas_usuario = Finca.objects.filter(
                usuario=request.user
            )

            finca_pedida = request.data.get('finca_id')

            finca = (
                fincas_usuario.filter(id=finca_pedida).first()
                if str(finca_pedida or '').isdigit()
                else None
            ) or fincas_usuario.first()


            # ------------------------------------------------
            # VALIDAR FINCA
            # ------------------------------------------------

            if not finca:

                return Response(
                    {
                        'detail':
                            'El usuario autenticado no tiene '
                            'una finca registrada.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


            finca_id = finca.id


            # ------------------------------------------------
            # VALIDAR FECHAS
            # ------------------------------------------------

            if not desde or not hasta:

                return Response(
                    {
                        'detail':
                            'Para utilizar los sensores '
                            'debes seleccionar la fecha '
                            'inicial y final.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


            # ------------------------------------------------
            # CONVERTIR FECHAS
            # ------------------------------------------------

            try:

                fecha_desde = datetime.strptime(
                    desde,
                    '%Y-%m-%d'
                ).date()

                fecha_hasta = datetime.strptime(
                    hasta,
                    '%Y-%m-%d'
                ).date()

            except ValueError:

                return Response(
                    {
                        'detail':
                            'Formato de fecha inválido. '
                            'Utiliza YYYY-MM-DD.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


            # ------------------------------------------------
            # VALIDAR RANGO
            # ------------------------------------------------

            if fecha_desde > fecha_hasta:

                return Response(
                    {
                        'detail':
                            'La fecha inicial no puede '
                            'ser mayor que la fecha final.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )


            # ------------------------------------------------
            # CONSULTAR DATOS DE SENSORES
            # ------------------------------------------------

            datos = (
                DatoSuelo.objects
                .filter(
                    arduino__finca=finca,
                    fecha__date__gte=fecha_desde,
                    fecha__date__lte=fecha_hasta,
                )
                .order_by(
                    'fecha'
                )
            )


            datos_lista = list(
                datos
            )


            cantidad_lecturas = len(
                datos_lista
            )


            # ------------------------------------------------
            # PROMEDIO DE pH
            # ------------------------------------------------

            ph_promedio = calcular_promedio(
                [
                    dato.ph
                    for dato in datos_lista
                ]
            )


            # ------------------------------------------------
            # PROMEDIO DE HUMEDAD
            # ------------------------------------------------

            humedad_promedio = calcular_promedio(
                [
                    dato.humedad
                    for dato in datos_lista
                ]
            )


            # ------------------------------------------------
            # PROMEDIO DE TEMPERATURA
            # ------------------------------------------------

            temperatura_promedio = calcular_promedio(
                [
                    dato.temperatura
                    for dato in datos_lista
                ]
            )


            # ------------------------------------------------
            # SERIALIZAR LECTURAS
            # ------------------------------------------------

            lecturas = DatoSueloSerializer(
                datos_lista,
                many=True,
                context={
                    'request': request
                }
            ).data


        # ====================================================
        # MODALIDAD SIN SENSORES
        # ====================================================

        else:

            # No necesitamos finca ni fechas para
            # realizar el análisis sin sensores.

            finca = None

            finca_id = None

            ph_promedio = None

            humedad_promedio = None

            temperatura_promedio = None

            cantidad_lecturas = 0

            lecturas = []


            # ------------------------------------------------
            # DATOS ESCRITOS POR EL USUARIO
            # ------------------------------------------------

            if fuente_sensores == 'manual':

                limites = {
                    'ph': (0, 14, 'El pH'),
                    'humedad': (0, 100, 'La humedad'),
                    'temperatura': (-10, 60, 'La temperatura'),
                }

                valores = {}

                for campo, (minimo, maximo, nombre) in limites.items():
                    try:
                        valor = float(
                            str(request.data.get(campo)).replace(',', '.')
                        )
                    except (TypeError, ValueError):
                        return Response(
                            {'detail': f'{nombre} es obligatorio y debe ser un número.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    if not minimo <= valor <= maximo:
                        return Response(
                            {'detail': f'{nombre} debe estar entre {minimo} y {maximo}.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    valores[campo] = round(valor, 2)

                ph_promedio = valores['ph']
                humedad_promedio = valores['humedad']
                temperatura_promedio = valores['temperatura']


        # ====================================================
        # GUARDAR IMAGEN TEMPORALMENTE
        # ====================================================

        ruta = None


        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=sufijo
            ) as tmp:

                for chunk in imagen.chunks():

                    tmp.write(
                        chunk
                    )

                ruta = tmp.name


            # =================================================
            # CONTEXTO PARA EL MOTOR YOLO
            # =================================================

            contexto = {

                'finca_id':
                    finca_id,

                'variedad':
                    variedad,

                'temporada':
                    temporada,

                # Con datos manuales el recomendador también
                # debe tener en cuenta pH, humedad y temperatura.
                'usar_sensores':
                    fuente_sensores in ('arduino', 'manual'),

                'desde':
                    desde,

                'hasta':
                    hasta,

                'condicion_climatica':
                    condicion_climatica,

                'ph':
                    ph_promedio,

                'humedad':
                    humedad_promedio,

                'temperatura':
                    temperatura_promedio,

                'cantidad_lecturas':
                    cantidad_lecturas,

                'fuente_datos':
                    {
                        'arduino': 'sensores Arduino',
                        'manual': 'medición manual',
                    }.get(fuente_sensores),

                'analisis_suelo':
                    analisis_suelo,

                'analisis_foliar':
                    analisis_foliar,
            }


            # =================================================
            # EJECUTAR YOLO
            # =================================================

            try:

                resultado = (
                    motor_yolo.analizar_imagen(
                        ruta,
                        contexto=contexto
                    )
                )

            except TypeError:

                # Compatibilidad con versiones antiguas
                # del motor YOLO.

                resultado = (
                    motor_yolo.analizar_imagen(
                        ruta
                    )
                )

            except NotImplementedError as e:

                return Response(
                    {
                        'detail':
                            str(e)
                    },
                    status=status.HTTP_501_NOT_IMPLEMENTED
                )


            # =================================================
            # ASEGURAR RESPUESTA COMO DICCIONARIO
            # =================================================

            if not isinstance(
                resultado,
                dict
            ):

                resultado = {

                    'status':
                        'alert',

                    'diagnosis':
                        'Resultado no disponible',

                    'recommendation':
                        'No fue posible obtener '
                        'el diagnóstico.',

                    'boundingBoxes':
                        [],
                }


            # =================================================
            # AGREGAR CONTEXTO
            # =================================================

            resultado['contexto'] = {

                'fuente_sensores':
                    fuente_sensores,

                'finca_id':
                    finca_id,

                'variedad':
                    variedad,

                'temporada':
                    temporada,

                'usar_sensores':
                    usar_sensores,

                'desde':
                    desde,

                'hasta':
                    hasta,

                'condicion_climatica':
                    condicion_climatica,
            }


            # =================================================
            # DATOS DE SENSORES
            # =================================================

            resultado['sensores'] = {

                'usados':
                    fuente_sensores in ('arduino', 'manual'),

                'fuente':
                    fuente_sensores,

                'cantidad_lecturas':
                    cantidad_lecturas,

                'ph_promedio':
                    ph_promedio,

                'humedad_promedio':
                    humedad_promedio,

                'temperatura_promedio':
                    temperatura_promedio,

                'desde':
                    desde,

                'hasta':
                    hasta,

                'lecturas':
                    lecturas,
            }


            # =================================================
            # CONTEXTO PARA RECOMENDACIONES
            # =================================================

            resultado['recomendacion_contexto'] = {

                'finca_id':
                    finca_id,

                'variedad':
                    variedad,

                'temporada':
                    temporada,

                'condicion_climatica':
                    condicion_climatica,

                'fuente_sensores':
                    fuente_sensores,

                'usar_sensores':
                    fuente_sensores in ('arduino', 'manual'),

                'ph':
                    ph_promedio,

                'humedad':
                    humedad_promedio,

                'temperatura':
                    temperatura_promedio,

            }


            # =================================================
            # INFORMACIÓN DE LA FINCA
            # =================================================

            if finca:

                resultado['finca'] = {

                    'id':
                        finca.id,

                    'nombre':
                        finca.nombre,

                    'ubicacion':
                        finca.ubicacion,

                }


            resultado['analisis'] = {

                'suelo':
                    analisis_suelo,

                'foliar':
                    analisis_foliar,
            }


            # =================================================
            # RESPUESTA FINAL
            # =================================================

            # Las imágenes de los productos salen como /media/...;
            # el frontend corre en otro origen, así que se envían
            # como URL absoluta.
            return Response(
                absolutizar_imagenes(
                    resultado,
                    request
                )
            )


        finally:

            # =================================================
            # ELIMINAR ARCHIVO TEMPORAL
            # =================================================

            if ruta:

                try:

                    os.remove(
                        ruta
                    )

                except OSError:

                    pass