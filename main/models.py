from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=32, unique=True, blank=True, null=True, verbose_name="Phone number")

    def __str__(self):
        return self.phone or self.user.get_username()


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(unique=True, verbose_name="URL-префикс")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    icon_emoji = models.CharField(max_length=8, blank=True, verbose_name="Иконка (emoji)")
    description = models.CharField(max_length=255, blank=True, verbose_name="Краткое описание")

    def __str__(self):
        if self.parent_id == self.id:
            return self.name
        return f"{self.parent.name} -> {self.name}" if self.parent else self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class AITool(models.Model):
    class PublicationStatus(models.TextChoices):
        DRAFT = "draft", "Черновик"
        PENDING = "pending", "На модерации"
        PUBLISHED = "published", "Опубликован"
        REJECTED = "rejected", "Отклонен"
        HIDDEN = "hidden", "Скрыт"

    class Audience(models.TextChoices):
        SMM = "smm", "SMM"
        HR = "hr", "HR"
        SALES = "sales", "Sales"
        OPERATIONS = "ops", "Operations"
        FOUNDERS = "founders", "Founders"

    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        MIDDLE = "middle", "Middle"
        ADVANCED = "advanced", "Advanced"

    class ProductType(models.TextChoices):
        PROMPT = "prompt", "Готовые промпты"
        AGENT = "agent", "AI-агенты"
        MINI_SERVICE = "mini_service", "Мини-сервисы / Инструменты"
        INTEGRATION = "integration", "Интеграции и автоматизация"

    title = models.CharField(max_length=200, verbose_name="Название ИИ-инструмента")
    seo_slug = models.SlugField(unique=True, verbose_name="SEO slug")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="authored_tools")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tools', verbose_name="Категория")
    audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.FOUNDERS, verbose_name="Для кого")
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER, verbose_name="Уровень сложности")
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.PROMPT,
        verbose_name="Тип AI-продукта",
    )
    short_description = models.CharField(max_length=255, verbose_name="Краткое описание")
    full_description = models.TextField(verbose_name="Полное описание / Инструкция")
    problem_solved = models.CharField(max_length=255, blank=True, verbose_name="Какую проблему решает")
    time_saving_hours = models.PositiveIntegerField(default=1, verbose_name="Экономия часов в неделю")
    setup_minutes = models.PositiveIntegerField(default=15, verbose_name="Время запуска (мин)")
    demo_input = models.TextField(blank=True, verbose_name="Demo: входные данные")
    demo_output = models.TextField(blank=True, verbose_name="Demo: результат")
    prompt_text = models.TextField(blank=True, null=True, verbose_name="Готовый промпт (если есть)")
    external_link = models.URLField(blank=True, null=True, verbose_name="Ссылка на сервис")
    price_usd = models.DecimalField(max_digits=8, decimal_places=2, default=19.00, verbose_name="Цена, USD")
    publication_status = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHED,
        verbose_name="Статус публикации",
    )
    is_featured = models.BooleanField(default=False, verbose_name="Показывать в топе")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "ИИ Инструмент"
        verbose_name_plural = "ИИ Инструменты"


class Plan(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название тарифа")
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255)
    price_usd = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Purchase(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELED = "canceled", "Canceled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    tool = models.ForeignKey(AITool, on_delete=models.SET_NULL, null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    amount_usd = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase #{self.pk}"


class UserAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tool_accesses")
    tool = models.ForeignKey(AITool, on_delete=models.CASCADE, related_name="granted_users")
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "tool")


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    tool = models.ForeignKey(AITool, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "tool")


class Review(models.Model):
    tool = models.ForeignKey(AITool, on_delete=models.CASCADE, related_name="reviews")
    author_name = models.CharField(max_length=80, verbose_name="Имя")
    company = models.CharField(max_length=120, blank=True, verbose_name="Компания")
    rating = models.PositiveSmallIntegerField(default=5)
    text = models.TextField(verbose_name="Отзыв")
    result_metric = models.CharField(max_length=200, blank=True, verbose_name="Результат в цифрах")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author_name}: {self.tool.title}"


class AuthorApplication(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        REVIEWING = "reviewing", "На рассмотрении"
        APPROVED = "approved", "Принята"
        REJECTED = "rejected", "Отклонена"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="author_applications")
    name = models.CharField(max_length=120)
    email = models.EmailField()
    tool_title = models.CharField(max_length=160)
    tool_description = models.TextField()
    revenue_share_expectation = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    admin_comment = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_author_applications")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Author application: {self.tool_title}"


class AuthorProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        PAUSED = "paused", "Приостановлен"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="author_profile")
    display_name = models.CharField(max_length=120)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    revenue_share_percent = models.PositiveSmallIntegerField(default=70)
    approved_application = models.ForeignKey(
        AuthorApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_author_profiles",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name


class CustomBotRequest(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    company = models.CharField(max_length=120, blank=True)
    challenge = models.TextField(verbose_name="Какая задача у бизнеса")
    budget = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Custom bot request: {self.name}"


class PromptGeneration(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="prompt_generations")
    category = models.CharField(max_length=80)
    role = models.CharField(max_length=80)
    task = models.TextField()
    tone = models.CharField(max_length=80)
    language = models.CharField(max_length=40)
    output_format = models.CharField(max_length=80)
    generated_prompt = models.TextField()
    provider = models.CharField(max_length=40, default="template")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prompt: {self.task[:60]}"


class FunnelEvent(models.Model):
    event_type = models.CharField(max_length=40)
    tool = models.ForeignKey(AITool, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=64, blank=True)
    metadata = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_type
