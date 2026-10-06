import secrets

from django.db import migrations, models

import tablas.models


def asignar_claves(apps, schema_editor):
    Arduino = apps.get_model('tablas', 'Arduino')
    for arduino in Arduino.objects.all():
        arduino.clave = secrets.token_urlsafe(32)
        arduino.save(update_fields=['clave'])


class Migration(migrations.Migration):

    dependencies = [
        ('tablas', '0008_eliminar_recoleccion_y_cobros'),
    ]

    operations = [
        migrations.AddField(
            model_name='arduino',
            name='clave',
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.RunPython(asignar_claves, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='arduino',
            name='clave',
            field=models.CharField(default=tablas.models.generar_clave_arduino, editable=False,
                                   max_length=64, unique=True),
        ),
    ]
