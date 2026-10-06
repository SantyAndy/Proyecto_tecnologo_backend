"""Plantillas de correo HTML con la estética de Agroindustria Cafetera.

Todos los correos comparten el mismo marco (cabecera verde degradada, tarjeta
crema, tipografía y colores de la página) para que lleguen de forma agradable y
coherente con la marca. Se envían como multipart (texto + HTML) para que también
se vean bien en clientes que no renderizan HTML.
"""
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

# Paleta de la página
VERDE = '#2E7D32'
VERDE_OSCURO = '#1B5E20'
CREMA = '#f6f8f3'
TEXTO = '#2b2b2b'
SUAVE = '#5b6b61'
BORDE = '#e6ece6'


def _plantilla(titulo, intro, contenido_html='', boton=None, nota=''):
    """Arma el HTML completo del correo (compatible con clientes de correo)."""
    boton_html = ''
    if boton:
        boton_html = f'''
          <table role="presentation" cellpadding="0" cellspacing="0" style="margin:6px 0 4px;"><tr><td>
            <a href="{boton['url']}" style="display:inline-block;background:{VERDE};color:#ffffff;
               text-decoration:none;font-weight:700;font-family:Arial,Helvetica,sans-serif;font-size:15px;
               padding:14px 30px;border-radius:999px;">{boton['texto']}</a>
          </td></tr></table>'''
    nota_html = (f'<p style="margin:20px 0 0;color:{SUAVE};font-size:13px;line-height:1.6;">{nota}</p>'
                 if nota else '')
    return f'''<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{CREMA};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CREMA};padding:28px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;width:100%;background:#ffffff;border-radius:18px;overflow:hidden;
                    box-shadow:0 10px 30px -12px rgba(0,0,0,.18);">
        <!-- Encabezado -->
        <tr><td style="background:linear-gradient(120deg,{VERDE},{VERDE_OSCURO});padding:26px 30px;
                       font-family:Arial,Helvetica,sans-serif;">
          <div style="color:#ffffff;font-size:20px;font-weight:800;">&#127793; Agroindustria Cafetera</div>
          <div style="font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;
                      color:rgba(255,255,255,.75);margin-top:4px;">Monitoreo del caf&eacute;</div>
        </td></tr>
        <!-- Cuerpo -->
        <tr><td style="padding:32px 30px;font-family:Arial,Helvetica,sans-serif;color:{TEXTO};">
          <h1 style="margin:0 0 12px;font-size:22px;color:{VERDE_OSCURO};">{titulo}</h1>
          <p style="margin:0 0 18px;font-size:15px;line-height:1.7;color:{TEXTO};">{intro}</p>
          {contenido_html}
          {boton_html}
          {nota_html}
        </td></tr>
        <!-- Pie -->
        <tr><td style="background:{CREMA};padding:18px 30px;font-family:Arial,Helvetica,sans-serif;
                       color:{SUAVE};font-size:12px;line-height:1.6;border-top:1px solid {BORDE};">
          Este mensaje fue enviado autom&aacute;ticamente por la plataforma <b>Agroindustria Cafetera</b>.<br>
          Cuidando el suelo y la cosecha del caf&eacute; colombiano. &#9749;
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>'''


def _fila_dato(etiqueta, valor):
    return f'''<tr>
      <td style="padding:10px 14px;background:#eef4ee;border-radius:10px 0 0 10px;
                 font-family:Arial,Helvetica,sans-serif;font-size:13px;color:{SUAVE};font-weight:700;
                 white-space:nowrap;vertical-align:top;">{etiqueta}</td>
      <td style="padding:10px 14px;background:#f7faf7;border-radius:0 10px 10px 0;
                 font-family:Arial,Helvetica,sans-serif;font-size:14px;color:{TEXTO};">{valor}</td>
    </tr>
    <tr><td colspan="2" style="height:8px;line-height:8px;">&nbsp;</td></tr>'''


def enviar_correo_contacto(nombre, apellido, email, mensaje, autoriza):
    """Correo que le llega al administrador cuando alguien usa el formulario."""
    # Los datos los escribe cualquier visitante: se escapan para que no puedan
    # meter HTML (enlaces falsos, imágenes de rastreo...) en el correo del administrador.
    nombre_h, apellido_h, email_h, mensaje_h = (escape(v) for v in (nombre, apellido, email, mensaje))
    filas = (
        _fila_dato('Nombre', f'{nombre_h} {apellido_h}')
        + _fila_dato('Correo', f'<a href="mailto:{email_h}" style="color:{VERDE};">{email_h}</a>')
        + _fila_dato('Autoriza datos', 'S&iacute;' if autoriza else 'No')
    )
    contenido = f'''
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 18px;">{filas}</table>
      <div style="background:{CREMA};border-left:4px solid {VERDE};border-radius:12px;padding:16px 18px;">
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:{SUAVE};font-weight:700;
                    text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Mensaje</div>
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.7;color:{TEXTO};
                    white-space:pre-wrap;">{mensaje_h}</div>
      </div>'''
    html = _plantilla(
        titulo='Nuevo mensaje de contacto',
        intro='Recibiste un nuevo mensaje desde el formulario de contacto de la p&aacute;gina.',
        contenido_html=contenido,
        nota='Puedes responder directamente a este correo para contactar a la persona.',
    )
    texto = (
        f'Nuevo mensaje de contacto\n\n'
        f'Nombre: {nombre} {apellido}\n'
        f'Correo: {email}\n'
        f'Autoriza datos: {"Sí" if autoriza else "No"}\n\n'
        f'Mensaje:\n{mensaje}\n'
    )
    msg = EmailMultiAlternatives(
        subject=f'\U0001F4E9 Nuevo contacto: {nombre} {apellido}',
        body=texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACTO_EMAIL],
        reply_to=[email],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=True)


def enviar_correo_recuperacion(user, link):
    """Correo con el enlace para restablecer la contraseña."""
    nombre = user.first_name or user.username
    contenido = (
        f'<p style="margin:0 0 22px;font-size:15px;line-height:1.7;color:{TEXTO};">'
        f'Pulsa el bot&oacute;n para crear una nueva contrase&ntilde;a. Por seguridad, el enlace caduca pronto.</p>'
    )
    html = _plantilla(
        titulo=f'Hola, {escape(nombre)}',
        intro='Recibimos una solicitud para restablecer tu contrase&ntilde;a en Agroindustria Cafetera.',
        contenido_html=contenido,
        boton={'texto': 'Crear nueva contraseña', 'url': link},
        nota=(f'Si el bot&oacute;n no funciona, copia y pega este enlace en tu navegador:<br>'
              f'<a href="{link}" style="color:{VERDE};word-break:break-all;">{link}</a><br><br>'
              f'Si no fuiste t&uacute;, ignora este correo: tu contrase&ntilde;a seguir&aacute; igual.'),
    )
    texto = (
        f'Hola {nombre},\n\n'
        f'Recibimos una solicitud para restablecer tu contraseña en Agroindustria Cafetera.\n'
        f'Abre este enlace para crear una nueva contraseña:\n\n{link}\n\n'
        f'Si no fuiste tú, ignora este correo.'
    )
    msg = EmailMultiAlternatives(
        subject='Restablecer tu contraseña — Agroindustria Cafetera',
        body=texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently=False)
