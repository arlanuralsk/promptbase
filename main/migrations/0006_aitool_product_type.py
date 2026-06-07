from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0005_category_parent"),
    ]

    operations = [
        migrations.AddField(
            model_name="aitool",
            name="product_type",
            field=models.CharField(
                choices=[
                    ("prompt", "Готовые промпты"),
                    ("agent", "AI-агенты"),
                    ("mini_service", "Мини-сервисы / Инструменты"),
                    ("integration", "Интеграции и автоматизация"),
                ],
                default="prompt",
                max_length=20,
                verbose_name="Тип AI-продукта",
            ),
        ),
    ]
