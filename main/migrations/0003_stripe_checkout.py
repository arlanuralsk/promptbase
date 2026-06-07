from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_business_mvp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="purchase",
            name="status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("paid", "Paid"), ("canceled", "Canceled")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="purchase",
            name="stripe_checkout_session_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="purchase",
            name="stripe_payment_intent_id",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
