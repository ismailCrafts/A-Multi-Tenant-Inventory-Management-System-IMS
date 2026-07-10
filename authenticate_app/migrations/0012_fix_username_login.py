"""
Migration 0012 — Switch login field from email to username.

What this fixes:
  - Migration 0011 wrongly set email as globally unique=True.
    This breaks multi-tenant: two users in different orgs can share
    the same email address. We remove that global constraint.
  - USERNAME_FIELD is now "username" in the model, so Django's auth
    system will use username as the identity field.
  - username stays as plain CharField (no global unique) because
    uniqueness is enforced per-org via unique_together.
  - email stays as plain EmailField (no global unique) — same reason.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authenticate_app', '0011_auto_20260305_0600'),
    ]

    operations = [
        # Remove global unique=True from email (was wrongly added in 0011).
        # Per-org uniqueness is already handled by unique_together.
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        # Confirm username stays as plain CharField — no global unique.
        # Per-org uniqueness is handled by unique_together.
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150),
        ),
    ]