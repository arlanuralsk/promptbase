from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0003_stripe_checkout"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="description",
            field=models.CharField(blank=True, max_length=255, verbose_name="Краткое описание"),
        ),
        migrations.AddField(
            model_name="category",
            name="icon_emoji",
            field=models.CharField(blank=True, max_length=8, verbose_name="Иконка (emoji)"),
        ),
    ]
