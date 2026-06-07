from django.urls import path

from .views import (
    author_apply,
    author_tool_create,
    buy_plan,
    create_tool_purchase,
    custom_bot_request,
    dashboard,
    feature_detail,
    home,
    payment_cancel,
    payment_success,
    pricing,
    prompt_generator,
    signup,
    solutions_landing,
    stripe_webhook,
    toggle_favorite,
    tool_detail,
    tool_list,
)

app_name = "main"

urlpatterns = [
    path("", home, name="home"),
    path("features/<slug:slug>/", feature_detail, name="feature_detail"),
    path("catalog/", tool_list, name="tool_list"),
    path("tools/<int:pk>/", tool_detail, name="tool_detail"),
    path("tools/<int:pk>/buy/", create_tool_purchase, name="create_tool_purchase"),
    path("tools/<int:pk>/favorite/", toggle_favorite, name="toggle_favorite"),
    path("dashboard/", dashboard, name="dashboard"),
    path("pricing/", pricing, name="pricing"),
    path("prompt-generator/", prompt_generator, name="prompt_generator"),
    path("accounts/signup/", signup, name="signup"),
    path("pricing/<slug:slug>/buy/", buy_plan, name="buy_plan"),
    path("payments/success/", payment_success, name="payment_success"),
    path("payments/cancel/", payment_cancel, name="payment_cancel"),
    path("payments/webhook/stripe/", stripe_webhook, name="stripe_webhook"),
    path("solutions/<str:slug>/", solutions_landing, name="solutions_landing"),
    path("authors/apply/", author_apply, name="author_apply"),
    path("authors/tools/new/", author_tool_create, name="author_tool_create"),
    path("custom-bot-request/", custom_bot_request, name="custom_bot_request"),
]
