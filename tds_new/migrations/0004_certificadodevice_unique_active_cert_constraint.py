# Generated manually — replace unique_together with conditional UniqueConstraint
# Fixes: ValidationError when generating a new cert for a device that already has
# a revoked cert (unique_together blocked creation even for revoked records).

from django.db import migrations, models
import django.db.models.functions


class Migration(migrations.Migration):

    dependencies = [
        ('tds_new', '0003_gateway_and_cert_provisioning_fields'),
    ]

    operations = [
        # Remove the old blanket unique_together constraint
        migrations.AlterUniqueTogether(
            name='certificadodevice',
            unique_together=set(),
        ),
        # Add partial unique constraint — only active (non-revoked) certs
        migrations.AddConstraint(
            model_name='certificadodevice',
            constraint=models.UniqueConstraint(
                fields=['conta', 'mac_address'],
                condition=models.Q(is_revoked=False),
                name='unique_active_cert_per_device',
            ),
        ),
    ]
