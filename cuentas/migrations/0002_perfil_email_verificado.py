from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cuentas', '0001_initial'),
    ]

    operations = [
        # Las cuentas que ya existían se marcan como verificadas para no
        # afectarlas; las nuevas empiezan sin verificar.
        migrations.AddField(
            model_name='perfil',
            name='email_verificado',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='perfil',
            name='email_verificado',
            field=models.BooleanField(default=False),
        ),
    ]
