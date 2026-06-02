from django.db import migrations, models


def create_default_categories(apps, schema_editor):
    TipoInstrumento = apps.get_model("store", "TipoInstrumento")

    guitarras, _ = TipoInstrumento.objects.get_or_create(
        name="Guitarras",
        defaults={
            "description": "Instrumentos de seis o doce cuerdas.",
        },
    )

    TipoInstrumento.objects.get_or_create(
        name="Guitarra de 6 cuerdas",
        defaults={
            "description": "Guitarra acústica o eléctrica de 6 cuerdas.",
            "parent_id": guitarras.id,
        },
    )
    TipoInstrumento.objects.get_or_create(
        name="Guitarra de 12 cuerdas",
        defaults={
            "description": "Guitarra de 12 cuerdas para un sonido más amplio.",
            "parent_id": guitarras.id,
        },
    )

    TipoInstrumento.objects.get_or_create(
        name="Grabación",
        defaults={
            "description": "Equipos y servicios para grabación de audio.",
        },
    )
    TipoInstrumento.objects.get_or_create(
        name="Video",
        defaults={
            "description": "Equipos y servicios para producción de video.",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tipoinstrumento",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="subtypes",
                to="store.tipoinstrumento",
            ),
        ),
        migrations.RunPython(create_default_categories),
    ]
