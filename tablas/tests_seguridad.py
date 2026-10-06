"""Pruebas de las protecciones de seguridad de la API."""
import io
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from cuentas.models import Perfil
from tablas.correos import enviar_correo_contacto
from tablas.models import Arduino, DatoSuelo, Finca


class BaseSeguridad(TestCase):
    def setUp(self):
        cache.clear()  # reinicia los contadores de límite de peticiones
        self.client = APIClient()


class IngestaArduinoTests(BaseSeguridad):
    def setUp(self):
        super().setUp()
        dueno = User.objects.create_user('dueno@x.com', 'dueno@x.com', 'ClaveSegura123!')
        self.arduino = Arduino.objects.create(finca=Finca.objects.create(nombre='F', usuario=dueno))
        self.lectura = {'arduino_id': self.arduino.id, 'ph': 6.1, 'humedad_suelo': 40, 'temperatura': 21}

    def test_sin_clave_se_rechaza(self):
        r = self.client.post('/api/ingesta/', self.lectura, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertFalse(DatoSuelo.objects.exists())

    def test_clave_incorrecta_se_rechaza(self):
        r = self.client.post('/api/ingesta/', self.lectura, format='json', HTTP_X_ARDUINO_KEY='falsa')
        self.assertEqual(r.status_code, 403)

    def test_arduino_inexistente_responde_igual(self):
        r = self.client.post('/api/ingesta/', {**self.lectura, 'arduino_id': 9999}, format='json',
                             HTTP_X_ARDUINO_KEY=self.arduino.clave)
        self.assertEqual(r.status_code, 403)

    def test_clave_correcta_guarda(self):
        r = self.client.post('/api/ingesta/', self.lectura, format='json', HTTP_X_ARDUINO_KEY=self.arduino.clave)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(DatoSuelo.objects.count(), 1)

    def test_valores_imposibles_se_rechazan(self):
        r = self.client.post('/api/ingesta/', {**self.lectura, 'ph': 99}, format='json',
                             HTTP_X_ARDUINO_KEY=self.arduino.clave)
        self.assertEqual(r.status_code, 400)


class CuentasTests(BaseSeguridad):
    def test_registro_no_duplica_correo_con_mayusculas(self):
        User.objects.create_user('ana@x.com', 'ana@x.com', 'ClaveSegura123!')
        r = self.client.post('/api/auth/register/', {
            'email': 'ANA@x.com', 'nombre': 'Ana', 'apellido': 'P', 'password': 'OtraClave987!'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_login_tiene_limite_de_intentos(self):
        codigos = [self.client.post('/api/auth/login/', {'email': 'x@x.com', 'password': 'mala'},
                                    format='json').status_code for _ in range(12)]
        self.assertIn(429, codigos)

    def test_restablecer_cierra_sesiones_y_verifica_correo(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = User.objects.create_user('b@x.com', 'b@x.com', 'ClaveSegura123!')
        Token.objects.create(user=user)
        r = self.client.post('/api/auth/password-reset-confirm/', {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'password': 'NuevaClave456!'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Token.objects.filter(user=user).exists())
        self.assertTrue(Perfil.objects.get(usuario=user).email_verificado)

    @override_settings(GOOGLE_CLIENT_ID='cliente-prueba')
    def test_google_anula_cuenta_registrada_por_otro(self):
        # Alguien registra el correo de la víctima antes que ella (sin verificarlo).
        r = self.client.post('/api/auth/register/', {
            'email': 'victima@gmail.com', 'nombre': 'X', 'apellido': 'Y', 'password': 'ClaveAtacante1!'},
            format='json')
        token_atacante = r.data['token']
        info = {'email': 'victima@gmail.com', 'email_verified': True}
        with mock.patch('google.oauth2.id_token.verify_oauth2_token', return_value=info):
            r = self.client.post('/api/auth/google/', {'credential': 'x'}, format='json')
        self.assertEqual(r.status_code, 200)
        user = User.objects.get(email='victima@gmail.com')
        self.assertFalse(user.has_usable_password())
        self.assertFalse(Token.objects.filter(key=token_atacante).exists())


class AdminUsuariosTests(BaseSeguridad):
    def test_staff_no_puede_cambiar_clave_de_superusuario(self):
        sup = User.objects.create_superuser('root', 'root@x.com', 'ClaveSegura123!')
        staff = User.objects.create_user('staff', 'staff@x.com', 'ClaveSegura123!', is_staff=True)
        self.client.force_authenticate(staff)
        r = self.client.patch(f'/api/admin/usuarios/{sup.id}/', {'password': 'Tomada12345!'}, format='json')
        self.assertEqual(r.status_code, 403)
        sup.refresh_from_db()
        self.assertTrue(sup.check_password('ClaveSegura123!'))

    def test_crear_usuario_exige_contrasena_segura(self):
        admin = User.objects.create_superuser('root', 'root@x.com', 'ClaveSegura123!')
        self.client.force_authenticate(admin)
        r = self.client.post('/api/admin/usuarios/', {'username': 'n', 'email': 'n@x.com'}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.client.post('/api/admin/usuarios/', {'username': 'n', 'email': 'n@x.com', 'password': '123'},
                             format='json')
        self.assertEqual(r.status_code, 400)


class DiagnosticoImagenTests(BaseSeguridad):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(User.objects.create_user('c@x.com', 'c@x.com', 'ClaveSegura123!'))

    def test_archivo_que_no_es_imagen_se_rechaza(self):
        falso = SimpleUploadedFile('hoja.png', b'<?php echo 1; ?>', content_type='image/png')
        r = self.client.post('/api/diagnostico/analizar/', {'imagen': falso}, format='multipart')
        self.assertEqual(r.status_code, 400)

    @override_settings(MAX_IMAGEN_BYTES=100)
    def test_imagen_muy_grande_se_rechaza(self):
        buf = io.BytesIO()
        Image.new('RGB', (64, 64), 'green').save(buf, 'PNG')
        grande = SimpleUploadedFile('hoja.png', buf.getvalue(), content_type='image/png')
        r = self.client.post('/api/diagnostico/analizar/', {'imagen': grande}, format='multipart')
        self.assertEqual(r.status_code, 400)


class CorreoContactoTests(TestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                       CONTACTO_EMAIL='admin@x.com')
    def test_html_del_visitante_se_escapa(self):
        enviar_correo_contacto('<b>Ana</b>', 'P', 'a@x.com', '<a href="http://malo">clic</a>', True)
        html = mail.outbox[0].alternatives[0][0]
        self.assertNotIn('<a href="http://malo">', html)
        self.assertIn('&lt;a href=', html)


class DispositivosUsuarioTests(BaseSeguridad):
    def setUp(self):
        super().setUp()
        self.yo = User.objects.create_user('yo@x.com', 'yo@x.com', 'ClaveSegura123!')
        self.otro = User.objects.create_user('otro@x.com', 'otro@x.com', 'ClaveSegura123!')
        self.mi_finca = Finca.objects.create(nombre='Mia', usuario=self.yo)
        self.finca_ajena = Finca.objects.create(nombre='Ajena', usuario=self.otro)
        self.ajeno = Arduino.objects.create(finca=self.finca_ajena, nombre='ajeno')
        self.client.force_authenticate(self.yo)

    def test_crear_y_listar_solo_los_propios(self):
        r = self.client.post('/api/dispositivos/', {'nombre': 'Sensor 1', 'finca': self.mi_finca.id}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data['clave'])
        self.assertFalse(r.data['en_linea'])
        ids = [d['id'] for d in self.client.get('/api/dispositivos/').data]
        self.assertEqual(ids, [r.data['id']])

    def test_no_puede_usar_finca_ajena(self):
        r = self.client.post('/api/dispositivos/', {'nombre': 'x', 'finca': self.finca_ajena.id}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_no_ve_ni_borra_dispositivos_ajenos(self):
        self.assertEqual(self.client.get(f'/api/dispositivos/{self.ajeno.id}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/dispositivos/{self.ajeno.id}/').status_code, 404)
        self.assertEqual(
            self.client.post(f'/api/dispositivos/{self.ajeno.id}/regenerar-clave/').status_code, 404)

    def test_regenerar_clave_invalida_la_anterior(self):
        arduino = Arduino.objects.create(finca=self.mi_finca, nombre='s')
        vieja = arduino.clave
        nueva = self.client.post(f'/api/dispositivos/{arduino.id}/regenerar-clave/').data['clave']
        self.assertNotEqual(vieja, nueva)
        anon = APIClient()
        lectura = {'arduino_id': arduino.id, 'ph': 6, 'humedad_suelo': 50, 'temperatura': 20, 'humedad_aire': 70}
        self.assertEqual(anon.post('/api/ingesta/', lectura, format='json', HTTP_X_ARDUINO_KEY=vieja).status_code, 403)
        self.assertEqual(anon.post('/api/ingesta/', lectura, format='json', HTTP_X_ARDUINO_KEY=nueva).status_code, 201)
        self.assertEqual(DatoSuelo.objects.get(arduino=arduino).humedad_aire, 70)
        d = self.client.get(f'/api/dispositivos/{arduino.id}/').data
        self.assertTrue(d['en_linea'])
        self.assertEqual(d['total_lecturas'], 1)

    def test_conexion_devuelve_ruta_de_ingesta(self):
        r = self.client.get('/api/dispositivos/conexion/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['ruta'], '/api/ingesta/')
