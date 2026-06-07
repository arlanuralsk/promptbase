from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    AITool,
    AuthorApplication,
    AuthorProfile,
    Category,
    CustomBotRequest,
    Favorite,
    FunnelEvent,
    Plan,
    PromptGeneration,
    Purchase,
    Review,
    UserAccess,
    UserProfile,
)

User = get_user_model()


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "user__email", "phone")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}  # Автоматически генерирует slug из названия
    list_display = ("name", "parent", "slug", "icon_emoji")
    list_filter = ("parent",)
    search_fields = ("name", "description")

@admin.register(AITool)
class AIToolAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "publication_status",
        "product_type",
        "audience",
        "difficulty",
        "price_usd",
        "is_featured",
        "created_at",
    )
    list_filter = ("publication_status", "category", "product_type", "audience", "difficulty", "is_featured")
    search_fields = ("title", "short_description", "problem_solved", "author__username", "author__email")
    prepopulated_fields = {"seo_slug": ("title",)}
    actions = ("publish_tools", "reject_tools", "hide_tools")

    @admin.action(description="Опубликовать выбранные инструменты")
    def publish_tools(self, request, queryset):
        updated = queryset.update(publication_status=AITool.PublicationStatus.PUBLISHED)
        self.message_user(request, f"Опубликовано инструментов: {updated}")

    @admin.action(description="Отклонить выбранные инструменты")
    def reject_tools(self, request, queryset):
        updated = queryset.update(publication_status=AITool.PublicationStatus.REJECTED)
        self.message_user(request, f"Отклонено инструментов: {updated}")

    @admin.action(description="Скрыть выбранные инструменты")
    def hide_tools(self, request, queryset):
        updated = queryset.update(publication_status=AITool.PublicationStatus.HIDDEN)
        self.message_user(request, f"Скрыто инструментов: {updated}")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_usd", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "tool",
        "plan",
        "amount_usd",
        "status",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
        "created_at",
    )
    list_filter = ("status", "created_at")


@admin.register(UserAccess)
class UserAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "tool", "granted_at")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "tool", "created_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("tool", "author_name", "rating", "result_metric", "created_at")
    list_filter = ("rating",)


@admin.register(AuthorApplication)
class AuthorApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "tool_title", "status", "user", "reviewed_by", "reviewed_at", "created_at")
    list_filter = ("status", "created_at", "reviewed_at")
    search_fields = ("name", "email", "tool_title", "tool_description")
    readonly_fields = ("created_at", "reviewed_at", "reviewed_by")
    actions = ("mark_reviewing", "approve_applications", "reject_applications")

    @admin.action(description="Взять на рассмотрение")
    def mark_reviewing(self, request, queryset):
        updated = queryset.update(
            status=AuthorApplication.Status.REVIEWING,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"Заявок на рассмотрении: {updated}")

    @admin.action(description="Принять заявки и создать профиль автора")
    def approve_applications(self, request, queryset):
        approved = 0
        without_user = 0
        for application in queryset:
            user = application.user or User.objects.filter(email__iexact=application.email).first()
            application.status = AuthorApplication.Status.APPROVED
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            if user:
                application.user = user
                AuthorProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        "display_name": application.name,
                        "email": application.email,
                        "status": AuthorProfile.Status.ACTIVE,
                        "approved_application": application,
                    },
                )
                approved += 1
            else:
                without_user += 1
            application.save(update_fields=["status", "reviewed_by", "reviewed_at", "user"])

        message = f"Принято заявок: {approved}"
        if without_user:
            message += f". Без аккаунта пользователя: {without_user}"
        self.message_user(request, message)

    @admin.action(description="Отклонить заявки")
    def reject_applications(self, request, queryset):
        updated = queryset.update(
            status=AuthorApplication.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"Отклонено заявок: {updated}")


@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "email", "status", "revenue_share_percent", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("display_name", "email", "user__username", "user__email")


@admin.register(CustomBotRequest)
class CustomBotRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "company", "created_at")


@admin.register(PromptGeneration)
class PromptGenerationAdmin(admin.ModelAdmin):
    list_display = ("task", "category", "role", "language", "provider", "user", "created_at")
    list_filter = ("category", "language", "provider", "created_at")
    search_fields = ("task", "generated_prompt", "user__username", "user__email")


@admin.register(FunnelEvent)
class FunnelEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "tool", "user", "session_key", "created_at")
    list_filter = ("event_type", "created_at")
