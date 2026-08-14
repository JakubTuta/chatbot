from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE django_app_chathistory DROP COLUMN IF EXISTS user_id;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
