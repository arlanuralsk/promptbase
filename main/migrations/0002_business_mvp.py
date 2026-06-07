from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="aitool",
            name="audience",
            field=models.CharField(
                choices=[
                    ("smm", "SMM"),
                    ("hr", "HR"),
                    ("sales", "Sales"),
                    ("ops", "Operations"),
                    ("founders", "Founders"),
                ],
                default="founders",
                max_length=20,
                verbose_name="Для кого",
            ),
        ),
        migrations.AddField(
            model_name="aitool",
            name="demo_input",
            field=models.TextField(blank=True, verbose_name="Demo: входные данные"),
        ),
        migrations.AddField(
            model_name="aitool",
            name="demo_output",
            field=models.TextField(blank=True, verbose_name="Demo: результат"),
        ),
        migrations.AddField(
            model_name="aitool",
            name="difficulty",
            field=models.CharField(
                choices=[("beginner", "Beginner"), ("middle", "Middle"), ("advanced", "Advanced")],
                default="beginner",
                max_length=20,
                verbose_name="Уровень сложности",
            ),
        ),
        migrations.AddField(
            model_name="aitool",
            name="is_featured",
            field=models.BooleanField(default=False, verbose_name="Показывать в топе"),
        ),
        migrations.AddField(
            model_name="aitool",
            name="price_usd",
            field=models.DecimalField(decimal_places=2, default=19.0, max_digits=8, verbose_name="Цена, USD"),
        ),
        migrations.AddField(
            model_name="aitool",
            name="problem_solved",
            field=models.CharField(blank=True, max_length=255, verbose_name="Какую проблему решает"),
        ),
        migrations.AddField(
            model_name="aitool",
            name="seo_slug",
            field=models.SlugField(default="temp-seo-slug", unique=True, verbose_name="SEO slug"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="aitool",
            name="setup_minutes",
            field=models.PositiveIntegerField(default=15, verbose_name="Время запуска (мин)"),
        ),
        migrations.AddField(
            model_name="aitool",
            name="time_saving_hours",
            field=models.PositiveIntegerField(default=1, verbose_name="Экономия часов в неделю"),
        ),
        migrations.CreateModel(
            name="AuthorApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("tool_title", models.CharField(max_length=160)),
                ("tool_description", models.TextField()),
                ("revenue_share_expectation", models.CharField(blank=True, max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="CustomBotRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("company", models.CharField(blank=True, max_length=120)),
                ("challenge", models.TextField(verbose_name="Какая задача у бизнеса")),
                ("budget", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Plan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Название тарифа")),
                ("slug", models.SlugField(unique=True)),
                ("description", models.CharField(max_length=255)),
                ("price_usd", models.DecimalField(decimal_places=2, max_digits=8)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="FunnelEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=40)),
                ("session_key", models.CharField(blank=True, max_length=64)),
                ("metadata", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tool",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="main.aitool"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Purchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount_usd", models.DecimalField(decimal_places=2, max_digits=8)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid")], default="paid", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("plan", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="main.plan")),
                ("tool", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="main.aitool")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="purchases", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("author_name", models.CharField(max_length=80, verbose_name="Имя")),
                ("company", models.CharField(blank=True, max_length=120, verbose_name="Компания")),
                ("rating", models.PositiveSmallIntegerField(default=5)),
                ("text", models.TextField(verbose_name="Отзыв")),
                ("result_metric", models.CharField(blank=True, max_length=200, verbose_name="Результат в цифрах")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tool", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="main.aitool")),
            ],
        ),
        migrations.CreateModel(
            name="Favorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tool", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorited_by", to="main.aitool")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorites", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "unique_together": {("user", "tool")},
            },
        ),
        migrations.CreateModel(
            name="UserAccess",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("granted_at", models.DateTimeField(auto_now_add=True)),
                ("tool", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="granted_users", to="main.aitool")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tool_accesses", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "unique_together": {("user", "tool")},
            },
        ),
    ]
