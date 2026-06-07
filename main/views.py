import json
import urllib.error
import urllib.request

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import (
    AuthorApplicationForm,
    AuthorToolForm,
    CustomBotRequestForm,
    EmailOrPhoneAuthenticationForm,
    PromptGeneratorForm,
    SignUpForm,
)
from .models import AITool, AuthorProfile, Category, Favorite, FunnelEvent, Plan, PromptGeneration, Purchase, Review, UserAccess

try:
    import stripe
except ImportError:  # pragma: no cover
    stripe = None

def _build_template_prompt(data):
    language_names = {"ru": "русском", "en": "English", "kk": "қазақ тілінде"}
    format_instructions = {
        "prompt": "Верни готовый результат без лишних пояснений.",
        "instruction": "После результата добавь короткую инструкцию, как использовать этот промпт.",
        "checklist": "После результата добавь чеклист проверки качества ответа.",
        "table": "Попроси AI вернуть результат в таблице с понятными колонками.",
    }
    return (
        f"Ты опытный AI-ассистент для направления: {data['category']}.\n"
        f"Роль пользователя: {data['role']}.\n"
        f"Задача: {data['task']}\n\n"
        f"Сформируй лучший промпт на {language_names.get(data['language'], 'русском')} языке.\n"
        f"Стиль ответа: {data['tone']}.\n"
        f"{format_instructions.get(data['output_format'], '')}\n\n"
        "Промпт должен быть конкретным и сразу готовым к копированию. "
        "Добавь контекст, роль модели, входные данные, критерии качества и ожидаемый формат ответа."
    )


def _generate_prompt_with_openai(data):
    if not settings.OPENAI_API_KEY:
        return _build_template_prompt(data), "template"

    payload = {
        "model": settings.OPENAI_PROMPT_MODEL,
        "input": [
            {
                "role": "system",
                "content": (
                    "Ты продуктовый эксперт по промптам для бизнеса. "
                    "Создавай практичные, конкретные промпты, которые можно сразу копировать в AI-сервис."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Категория: {data['category']}\n"
                    f"Роль пользователя: {data['role']}\n"
                    f"Задача: {data['task']}\n"
                    f"Стиль: {data['tone']}\n"
                    f"Язык: {data['language']}\n"
                    f"Формат: {data['output_format']}\n\n"
                    "Сгенерируй сильный готовый промпт. Добавь структуру, переменные, критерии качества и формат ответа."
                ),
            },
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return _build_template_prompt(data), "template"

    if result.get("output_text"):
        return result["output_text"].strip(), "openai"

    chunks = []
    for item in result.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    generated = "\n".join(chunks).strip()
    return generated or _build_template_prompt(data), "openai" if generated else "template"


def _track_event(request, event_type, tool=None, metadata=""):
    if not request.session.session_key:
        request.session.create()
    FunnelEvent.objects.create(
        event_type=event_type,
        tool=tool,
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or "",
        metadata=metadata,
    )


class WelcomeLoginView(LoginView):
    authentication_form = EmailOrPhoneAuthenticationForm
    redirect_authenticated_user = True

    def get(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            return redirect(self.get_success_url())
        params = request.GET.copy()
        params.setdefault("tab", "login")
        return redirect(f"{reverse('main:home')}?{params.urlencode()}")

    def form_invalid(self, form):
        return render(
            self.request,
            "registration/auth_welcome.html",
            {
                "tab": "login",
                "login_form": form,
                "signup_form": SignUpForm(),
                "next": self.request.POST.get("next", ""),
            },
        )


def home(request):
    if not request.user.is_authenticated:
        tab = request.GET.get("tab", "login")
        if tab not in {"login", "signup"}:
            tab = "login"
        return render(
            request,
            "registration/auth_welcome.html",
            {
                "tab": tab,
                "login_form": EmailOrPhoneAuthenticationForm(),
                "signup_form": SignUpForm(),
                "next": request.GET.get("next", ""),
            },
        )

    featured_tools = AITool.objects.filter(
        is_featured=True,
        publication_status=AITool.PublicationStatus.PUBLISHED,
    ).select_related("category")[:3]
    categories = Category.objects.filter(parent__isnull=True).order_by("name")[:8]
    _track_event(request, "home_view")
    return render(
        request,
        "main/home.html",
        {"featured_tools": featured_tools, "categories": categories},
    )


def signup(request):
    if request.user.is_authenticated:
        return redirect("main:home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт создан. Добро пожаловать в PromptBase!")
            return redirect("main:home")
        return render(
            request,
            "registration/auth_welcome.html",
            {
                "tab": "signup",
                "login_form": EmailOrPhoneAuthenticationForm(),
                "signup_form": form,
                "next": request.GET.get("next", ""),
            },
        )

    return redirect(f"{reverse('main:home')}?tab=signup")


def feature_detail(request, slug):
    features = {
        "quick-start": {
            "title": "Быстрый старт",
            "lead": "Запуск AI-инструментов без долгой настройки и сложной интеграции.",
            "full_description": (
                "В PromptBase сценарии подготовлены так, чтобы команда могла начать работу в день подключения. "
                "Вы выбираете нужный инструмент, получаете готовую структуру промпта, пример входных данных и "
                "ожидаемый формат результата. Это снижает время внедрения и избавляет от этапа ручного R&D."
            ),
        },
        "result-focus": {
            "title": "Фокус на результат",
            "lead": "Мы показываем не только функциональность, но и ценность в цифрах.",
            "full_description": (
                "Каждая карточка инструмента содержит блок ценности: какую задачу решает, сколько часов экономит, "
                "за сколько минут запускается и какой тип результата получает пользователь. За счет этого проще "
                "сравнивать решения и выбирать те, которые быстрее окупаются для бизнеса."
            ),
        },
        "roles": {
            "title": "Для разных ролей",
            "lead": "Каталог адаптирован под реальные задачи команд.",
            "full_description": (
                "В сервисе есть фильтры и категории для SMM, HR, Sales, Operations и команд роста. "
                "Это помогает каждому специалисту быстро найти релевантный инструмент без просмотра лишних разделов. "
                "В будущем можно добавить персональные рекомендации по роли и отрасли."
            ),
        },
    }
    feature = features.get(slug)
    if not feature:
        return redirect("main:home")
    return render(request, "main/feature_detail.html", {"feature": feature})


def tool_list(request):
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    audience = request.GET.get("audience", "").strip()
    difficulty = request.GET.get("difficulty", "").strip()
    product_type = request.GET.get("product_type", "").strip()
    sort = request.GET.get("sort", "new").strip()

    tools = AITool.objects.filter(publication_status=AITool.PublicationStatus.PUBLISHED).select_related("category")
    categories = Category.objects.select_related("parent").annotate(tools_count=Count("tools")).order_by("parent__name", "name")
    parent_categories = [cat for cat in categories if cat.parent_id is None]
    selected_category = None

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        child_ids = list(selected_category.children.values_list("id", flat=True))
        category_ids = [selected_category.id] + child_ids
        tools = tools.filter(category_id__in=category_ids)

    if query:
        tools = tools.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(full_description__icontains=query)
        )

    if audience:
        tools = tools.filter(audience=audience)

    if difficulty:
        tools = tools.filter(difficulty=difficulty)

    if product_type:
        tools = tools.filter(product_type=product_type)

    sort_map = {
        "new": "-created_at",
        "price_low": "price_usd",
        "price_high": "-price_usd",
        "featured": "-is_featured",
    }
    tools = tools.order_by(sort_map.get(sort, "-created_at"), "-created_at")

    _track_event(request, "catalog_view", metadata=f"q={query};cat={category_slug}")

    context = {
        "tools": tools,
        "featured_tools": AITool.objects.filter(
            is_featured=True,
            publication_status=AITool.PublicationStatus.PUBLISHED,
        )[:3],
        "categories": categories,
        "parent_categories": parent_categories,
        "selected_category": selected_category,
        "query": query,
        "selected_audience": audience,
        "selected_difficulty": difficulty,
        "selected_product_type": product_type,
        "audience_choices": AITool.Audience.choices,
        "difficulty_choices": AITool.Difficulty.choices,
        "product_type_choices": AITool.ProductType.choices,
        "selected_sort": sort,
    }
    return render(request, "main/tool_list.html", context)


def tool_detail(request, pk):
    tools = AITool.objects.select_related("category", "author")
    if not request.user.is_staff:
        visible_filter = Q(publication_status=AITool.PublicationStatus.PUBLISHED)
        if request.user.is_authenticated:
            visible_filter |= Q(author=request.user)
        tools = tools.filter(visible_filter)
    tool = get_object_or_404(tools, pk=pk)
    reviews = Review.objects.filter(tool=tool).order_by("-created_at")
    is_favorite = request.user.is_authenticated and Favorite.objects.filter(user=request.user, tool=tool).exists()
    has_access = request.user.is_authenticated and UserAccess.objects.filter(user=request.user, tool=tool).exists()
    _track_event(request, "tool_open", tool=tool)
    return render(
        request,
        "main/tool_detail.html",
        {"tool": tool, "reviews": reviews, "is_favorite": is_favorite, "has_access": has_access},
    )


@login_required
def create_tool_purchase(request, pk):
    tool = get_object_or_404(AITool, pk=pk, publication_status=AITool.PublicationStatus.PUBLISHED)
    if not stripe or not settings.STRIPE_SECRET_KEY:
        messages.error(request, "Stripe не настроен. Добавьте ключи в .env.")
        return redirect("main:tool_detail", pk=pk)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    purchase = Purchase.objects.create(
        user=request.user,
        tool=tool,
        amount_usd=tool.price_usd,
        status=Purchase.Status.PENDING,
    )
    checkout_session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=request.user.email or None,
        metadata={
            "purchase_id": str(purchase.id),
            "kind": "tool",
        },
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(tool.price_usd * 100),
                    "product_data": {
                        "name": tool.title,
                        "description": tool.short_description,
                    },
                },
            }
        ],
        success_url=request.build_absolute_uri(reverse("main:payment_success")) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri(reverse("main:payment_cancel")) + f"?purchase_id={purchase.id}",
    )
    purchase.stripe_checkout_session_id = checkout_session.id
    purchase.save(update_fields=["stripe_checkout_session_id"])
    _track_event(request, "tool_buy_click", tool=tool, metadata=f"purchase={purchase.id}")
    return redirect(checkout_session.url)


def payment_success(request):
    session_id = request.GET.get("session_id", "")
    purchase = Purchase.objects.filter(stripe_checkout_session_id=session_id).first()
    if purchase and purchase.status == Purchase.Status.PAID:
        messages.success(request, "Оплата подтверждена. Доступ открыт.")
        if purchase.tool:
            return redirect("main:tool_detail", pk=purchase.tool_id)
        return redirect("main:dashboard")

    messages.info(request, "Платеж в обработке. Обновите страницу через несколько секунд.")
    return redirect("main:dashboard")


def payment_cancel(request):
    purchase_id = request.GET.get("purchase_id", "")
    purchase = Purchase.objects.filter(id=purchase_id).first()
    if purchase and purchase.status == Purchase.Status.PENDING:
        purchase.status = Purchase.Status.CANCELED
        purchase.save(update_fields=["status"])
    messages.warning(request, "Оплата отменена.")
    if purchase and purchase.tool_id:
        return redirect("main:tool_detail", pk=purchase.tool_id)
    return redirect("main:pricing")


@login_required
def toggle_favorite(request, pk):
    tool = get_object_or_404(AITool, pk=pk, publication_status=AITool.PublicationStatus.PUBLISHED)
    favorite = Favorite.objects.filter(user=request.user, tool=tool).first()
    if favorite:
        favorite.delete()
    else:
        Favorite.objects.create(user=request.user, tool=tool)
    _track_event(request, "favorite_toggle", tool=tool)
    return redirect("main:tool_detail", pk=pk)


@login_required
def dashboard(request):
    purchases = Purchase.objects.filter(user=request.user).select_related("tool", "plan").order_by("-created_at")
    favorites = Favorite.objects.filter(user=request.user).select_related("tool").order_by("-created_at")
    accesses = UserAccess.objects.filter(user=request.user).select_related("tool")
    author_profile = AuthorProfile.objects.filter(user=request.user).first()
    author_applications = request.user.author_applications.order_by("-created_at")
    authored_tools = request.user.authored_tools.select_related("category").order_by("-created_at")
    author_sales_count = Purchase.objects.filter(tool__author=request.user, status=Purchase.Status.PAID).count()
    return render(
        request,
        "main/dashboard.html",
        {
            "purchases": purchases,
            "favorites": favorites,
            "accesses": accesses,
            "author_profile": author_profile,
            "author_applications": author_applications,
            "authored_tools": authored_tools,
            "author_sales_count": author_sales_count,
        },
    )


def pricing(request):
    plans = Plan.objects.filter(is_active=True).order_by("price_usd")
    currency_prices = {
        "starter": "$5 / 2 500 ₸ / 450 ₽ / €5",
        "pro": "$15 / 7 500 ₸ / 1 350 ₽ / €14",
        "business": "$49 / 24 500 ₸ / 4 400 ₽ / €45",
    }
    for plan in plans:
        plan.display_price = currency_prices.get(plan.slug, f"${plan.price_usd}")
    return render(request, "main/pricing.html", {"plans": plans})


def prompt_generator(request):
    generated_prompt = ""
    provider = ""

    if request.method == "POST":
        form = PromptGeneratorForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            generated_prompt, provider = _generate_prompt_with_openai(data)
            PromptGeneration.objects.create(
                user=request.user if request.user.is_authenticated else None,
                category=data["category"],
                role=data["role"],
                task=data["task"],
                tone=data["tone"],
                language=data["language"],
                output_format=data["output_format"],
                generated_prompt=generated_prompt,
                provider=provider,
            )
            _track_event(request, "prompt_generated", metadata=f"provider={provider};category={data['category']}")
            if provider == "template":
                messages.info(request, "Промпт создан в шаблонном режиме. Для AI-генерации добавьте OPENAI_API_KEY.")
    else:
        form = PromptGeneratorForm()

    history = PromptGeneration.objects.order_by("-created_at")
    if request.user.is_authenticated:
        history = history.filter(Q(user=request.user) | Q(user__isnull=True))
    else:
        history = history.filter(user__isnull=True)

    return render(
        request,
        "main/prompt_generator.html",
        {
            "form": form,
            "generated_prompt": generated_prompt,
            "provider": provider,
            "history": history[:5],
        },
    )


@login_required
def buy_plan(request, slug):
    plan = get_object_or_404(Plan, slug=slug, is_active=True)
    if not stripe or not settings.STRIPE_SECRET_KEY:
        messages.error(request, "Stripe не настроен. Добавьте ключи в .env.")
        return redirect("main:pricing")
    stripe.api_key = settings.STRIPE_SECRET_KEY

    purchase = Purchase.objects.create(
        user=request.user,
        plan=plan,
        amount_usd=plan.price_usd,
        status=Purchase.Status.PENDING,
    )
    checkout_session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=request.user.email or None,
        metadata={"purchase_id": str(purchase.id), "kind": "plan"},
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(plan.price_usd * 100),
                    "product_data": {
                        "name": f"Plan: {plan.name}",
                        "description": plan.description,
                    },
                },
            }
        ],
        success_url=request.build_absolute_uri(reverse("main:payment_success")) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri(reverse("main:payment_cancel")) + f"?purchase_id={purchase.id}",
    )
    purchase.stripe_checkout_session_id = checkout_session.id
    purchase.save(update_fields=["stripe_checkout_session_id"])
    _track_event(request, "plan_buy_click", metadata=f"{plan.slug};purchase={purchase.id}")
    return redirect(checkout_session.url)


def solutions_landing(request, slug):
    category = get_object_or_404(Category.objects.prefetch_related("children"), slug=slug)
    sort = request.GET.get("sort", "featured").strip()
    category_ids = [category.id] + list(category.children.values_list("id", flat=True))
    tools = AITool.objects.filter(
        category_id__in=category_ids,
        publication_status=AITool.PublicationStatus.PUBLISHED,
    ).order_by("-is_featured", "-created_at")
    sort_map = {
        "featured": ("-is_featured", "-created_at"),
        "new": ("-created_at",),
        "price_low": ("price_usd", "-created_at"),
        "price_high": ("-price_usd", "-created_at"),
    }
    tools = tools.order_by(*sort_map.get(sort, ("-is_featured", "-created_at")))
    return render(
        request,
        "main/solution_landing.html",
        {"category": category, "tools": tools, "selected_sort": sort, "subcategories": category.children.all()},
    )


def author_apply(request):
    if request.method == "POST":
        form = AuthorApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            if request.user.is_authenticated:
                application.user = request.user
            application.save()
            messages.success(request, "Заявка отправлена. Мы свяжемся по партнерству.")
            return redirect("main:author_apply")
    else:
        form = AuthorApplicationForm()
    return render(request, "main/author_apply.html", {"form": form})


@login_required
def author_tool_create(request):
    author_profile = AuthorProfile.objects.filter(user=request.user, status=AuthorProfile.Status.ACTIVE).first()
    if not author_profile:
        messages.warning(request, "Сначала дождитесь принятия заявки автора.")
        return redirect("main:dashboard")

    if request.method == "POST":
        form = AuthorToolForm(request.POST)
        if form.is_valid():
            tool = form.save(commit=False)
            tool.author = request.user
            tool.publication_status = AITool.PublicationStatus.PENDING
            tool.is_featured = False
            tool.save()
            messages.success(request, "Инструмент отправлен на модерацию.")
            return redirect("main:dashboard")
    else:
        form = AuthorToolForm()

    return render(request, "main/author_tool_form.html", {"form": form})


def custom_bot_request(request):
    if request.method == "POST":
        form = CustomBotRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Заявка принята. Подготовим предложение по кастом-боту.")
            return redirect("main:custom_bot_request")
    else:
        form = CustomBotRequestForm()
    return render(request, "main/custom_bot_request.html", {"form": form})


@csrf_exempt
def stripe_webhook(request):
    if not stripe or not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse(status=503)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = request.body
    signature = request.META.get("HTTP_STRIPE_SIGNATURE")
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        purchase_id = session.get("metadata", {}).get("purchase_id")
        purchase = Purchase.objects.filter(id=purchase_id).first()
        if purchase and purchase.status != Purchase.Status.PAID:
            purchase.status = Purchase.Status.PAID
            purchase.stripe_payment_intent_id = session.get("payment_intent", "") or ""
            if not purchase.stripe_checkout_session_id:
                purchase.stripe_checkout_session_id = session.get("id", "") or ""
            purchase.save(
                update_fields=["status", "stripe_payment_intent_id", "stripe_checkout_session_id"]
            )
            if purchase.tool_id:
                UserAccess.objects.get_or_create(user=purchase.user, tool=purchase.tool)

    return HttpResponse(status=200)
