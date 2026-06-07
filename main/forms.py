from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.text import slugify

from .auth_utils import looks_like_email, normalize_phone
from .models import AITool, AuthorApplication, CustomBotRequest, UserProfile


User = get_user_model()


class EmailOrPhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email или номер телефона",
        widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "name@example.com или +77001234567"}),
    )


class SignUpForm(UserCreationForm):
    identifier = forms.CharField(
        label="Email или номер телефона",
        widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "name@example.com или +77001234567"}),
    )

    class Meta:
        model = User
        fields = ("identifier", "password1", "password2")

    def clean_identifier(self):
        identifier = self.cleaned_data["identifier"].strip()
        if looks_like_email(identifier):
            email = identifier.lower()
            if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
                raise forms.ValidationError("Пользователь с такой почтой уже есть.")
            return email

        phone = normalize_phone(identifier)
        if len(phone.lstrip("+")) < 7:
            raise forms.ValidationError("Введите корректный номер телефона или email.")
        if UserProfile.objects.filter(phone=phone).exists() or User.objects.filter(username__iexact=phone).exists():
            raise forms.ValidationError("Пользователь с таким номером уже есть.")
        return phone

    def save(self, commit=True):
        identifier = self.cleaned_data["identifier"]
        user = super().save(commit=False)
        user.username = identifier
        if looks_like_email(identifier):
            user.email = identifier
        if commit:
            user.save()
            if not looks_like_email(identifier):
                UserProfile.objects.create(user=user, phone=identifier)
        return user


class AuthorApplicationForm(forms.ModelForm):
    class Meta:
        model = AuthorApplication
        fields = [
            "name",
            "email",
            "tool_title",
            "tool_description",
            "revenue_share_expectation",
        ]


class AuthorToolForm(forms.ModelForm):
    class Meta:
        model = AITool
        fields = [
            "title",
            "category",
            "audience",
            "difficulty",
            "product_type",
            "short_description",
            "full_description",
            "problem_solved",
            "time_saving_hours",
            "setup_minutes",
            "demo_input",
            "demo_output",
            "prompt_text",
            "external_link",
            "price_usd",
        ]

    def save(self, commit=True):
        tool = super().save(commit=False)
        if not tool.seo_slug:
            base_slug = slugify(tool.title, allow_unicode=True)[:45] or "ai-tool"
            candidate = base_slug
            index = 2
            while AITool.objects.filter(seo_slug=candidate).exclude(pk=tool.pk).exists():
                suffix = f"-{index}"
                candidate = f"{base_slug[:45-len(suffix)]}{suffix}"
                index += 1
            tool.seo_slug = candidate
        if commit:
            tool.save()
            self.save_m2m()
        return tool


class PromptGeneratorForm(forms.Form):
    CATEGORY_CHOICES = [
        ("Маркетинг и PR", "Маркетинг и PR"),
        ("Продажи и клиентский сервис", "Продажи и клиентский сервис"),
        ("HR и управление", "HR и управление"),
        ("Аналитика и финансы", "Аналитика и финансы"),
        ("Разработка и IT", "Разработка и IT"),
        ("Дизайн и видео", "Дизайн и видео"),
        ("Юристы и документы", "Юристы и документы"),
    ]
    ROLE_CHOICES = [
        ("founder", "Founder / владелец бизнеса"),
        ("marketer", "Маркетолог / SMM"),
        ("sales", "Менеджер по продажам"),
        ("support", "Поддержка клиентов"),
        ("hr", "HR"),
        ("analyst", "Аналитик"),
        ("developer", "Разработчик"),
    ]
    TONE_CHOICES = [
        ("expert", "Экспертно"),
        ("simple", "Просто и понятно"),
        ("friendly", "Дружелюбно"),
        ("strict", "Строго и структурно"),
        ("creative", "Креативно"),
    ]
    LANGUAGE_CHOICES = [
        ("ru", "Русский"),
        ("en", "English"),
        ("kk", "Қазақша"),
    ]
    FORMAT_CHOICES = [
        ("prompt", "Готовый промпт"),
        ("instruction", "Промпт + инструкция"),
        ("checklist", "Промпт + чеклист"),
        ("table", "Промпт для ответа таблицей"),
    ]

    task = forms.CharField(
        label="Какая задача?",
        widget=forms.Textarea(attrs={"placeholder": "Например: сделать контент-план для Instagram на 7 дней"}),
    )
    category = forms.ChoiceField(label="Категория", choices=CATEGORY_CHOICES)
    role = forms.ChoiceField(label="Для кого", choices=ROLE_CHOICES)
    tone = forms.ChoiceField(label="Стиль", choices=TONE_CHOICES)
    language = forms.ChoiceField(label="Язык", choices=LANGUAGE_CHOICES)
    output_format = forms.ChoiceField(label="Формат результата", choices=FORMAT_CHOICES)


class CustomBotRequestForm(forms.ModelForm):
    class Meta:
        model = CustomBotRequest
        fields = ["name", "email", "company", "challenge", "budget"]
