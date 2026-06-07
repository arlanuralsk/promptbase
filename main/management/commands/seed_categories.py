from django.core.management.base import BaseCommand
from django.db import models
from django.utils.text import slugify

from main.models import Category


CATEGORY_TREE = [
    {
        "name": "Маркетинг и PR",
        "icon": "📣",
        "description": "Контент, креативы, SEO и продвижение.",
        "children": [
            "Генерация контент-планов и постов для соцсетей (SMM)",
            "Создание рекламных креативов и копирайтинг",
            "SEO-оптимизация и написание статей",
        ],
    },
    {
        "name": "Продажи и Клиентский сервис",
        "icon": "💼",
        "description": "Скрипты продаж, лиды и поддержка клиентов.",
        "children": [
            "Скрипты отработки возражений для менеджеров",
            "AI-ассистенты для поддержки клиентов (чат-боты)",
            "Квалификация лидов и холодные рассылки",
        ],
    },
    {
        "name": "Управление и HR",
        "icon": "👥",
        "description": "Найм, онбординг и база знаний компании.",
        "children": [
            "Онбординг сотрудников и составление должностных инструкций",
            "Скрининг резюме и генерация вопросов для собеседований",
            "Автоматизация внутренней базы знаний компании",
        ],
    },
    {
        "name": "Аналитика и Финансы",
        "icon": "📊",
        "description": "Отчеты, анализ данных и оценка рисков.",
        "children": [
            "Промпты для анализа Excel/CSV отчетов",
            "Оценка рисков и базовый финансовый аудит",
        ],
    },
    {
        "name": "Разработка и IT",
        "icon": "💻",
        "description": "Код, техдокументация и инженерные процессы.",
        "children": [
            "Генерация и аудит кода, написание технической документации",
        ],
    },
    {
        "name": "Дизайн и Видео",
        "icon": "🎨",
        "description": "Визуалы, видео, презентации и креативы для бренда.",
        "children": [
            "Генерация изображений и бренд-креативов",
            "Создание видео и аватаров",
            "Дизайн презентаций и макетов",
        ],
    },
    {
        "name": "Автоматизация",
        "icon": "⚙️",
        "description": "Связки сервисов, AI-агенты и автоматизация процессов.",
        "children": [
            "Автоматизация бизнес-процессов и workflow",
            "AI-агенты для интеграций",
        ],
    },
    {
        "name": "Юристы и Документы",
        "icon": "⚖️",
        "description": "Договоры, правовой ресерч и документооборот.",
        "children": [
            "Анализ договоров и юридических рисков",
            "Подготовка и редактура документов",
        ],
    },
]


class Command(BaseCommand):
    help = "Creates business categories and subcategories for PromptBase catalog."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="Delete broken self-parent categories that have no tools.",
        )

    def _build_unique_slug(self, base_text):
        base_slug = slugify(base_text, allow_unicode=True)[:40] or "category"
        candidate = base_slug
        idx = 2
        while Category.objects.filter(slug=candidate).exists():
            suffix = f"-{idx}"
            candidate = f"{base_slug[:40-len(suffix)]}{suffix}"
            idx += 1
        return candidate

    def handle(self, *args, **options):
        created = 0
        updated = 0
        deleted = 0

        if options.get("cleanup"):
            broken_qs = Category.objects.filter(parent_id=models.F("id"), tools__isnull=True).distinct()
            deleted = broken_qs.count()
            broken_qs.delete()

        for parent_item in CATEGORY_TREE:
            parent = Category.objects.filter(name=parent_item["name"], parent__isnull=True).first()
            if not parent:
                parent = Category.objects.create(
                    name=parent_item["name"],
                    slug=self._build_unique_slug(parent_item["name"]),
                    icon_emoji=parent_item["icon"],
                    description=parent_item["description"],
                )
                created += 1
            else:
                parent.icon_emoji = parent_item["icon"]
                parent.description = parent_item["description"]
                parent.parent = None
                parent.save(update_fields=["icon_emoji", "description", "parent"])
                updated += 1

            for child_name in parent_item["children"]:
                child = Category.objects.filter(name=child_name, parent=parent).first()
                if not child:
                    child = Category.objects.create(
                        name=child_name,
                        slug=self._build_unique_slug(f"{parent_item['name']}-{child_name}"),
                        parent=parent,
                        icon_emoji="",
                        description="",
                    )
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}, Deleted: {deleted}"))
