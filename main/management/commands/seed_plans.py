from django.core.management.base import BaseCommand

from main.models import Plan


PLANS = [
    {
        "name": "Starter",
        "slug": "starter",
        "description": "8 доступов к AI-инструментам в месяц, готовые промпты и базовые обновления.",
        "price_usd": "5.00",
    },
    {
        "name": "Pro",
        "slug": "pro",
        "description": "25 доступов в месяц, premium-категории, приоритетные обновления и расширенные сценарии.",
        "price_usd": "15.00",
    },
    {
        "name": "Business",
        "slug": "business",
        "description": "Командный доступ, помощь с внедрением, кастомные AI-боты и приоритетная поддержка.",
        "price_usd": "49.00",
    },
]


class Command(BaseCommand):
    help = "Creates default subscription plans."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for item in PLANS:
            _, was_created = Plan.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                    "price_usd": item["price_usd"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}"))
