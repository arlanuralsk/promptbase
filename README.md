# PromptBase (MVP)

Быстрый сайт-каталог AI-ассистентов на Django.

## Что уже есть

- Главная страница с каталогом инструментов
- Поиск по ключевым словам
- Фильтры по категории, роли, сложности и типу AI-продукта
- Детальная страница инструмента
- Демо-блок "до/после" и карточка ценности (экономия времени)
- Кнопки покупки и добавления в избранное
- Тарифы и подписка Pro
- Генератор промптов (`/prompt-generator/`)
- Личный кабинет (доступы, история, избранное)
- Отзывы/кейсы (через админку)
- SEO-страницы категорий (`/solutions/<slug>/`)
- Форма партнерки для авторов
- Форма заявки на кастомного AI-бота
- Базовая аналитика воронки (события в `FunnelEvent`)
- Админка для наполнения контента

## Быстрый запуск

1. Активируй виртуальное окружение (если еще не активно).
2. Выполни миграции:

```bash
python manage.py migrate
```

3. Создай администратора:

```bash
python manage.py createsuperuser
```

4. Запусти проект:

```bash
python manage.py runserver
```

5. Открой:
- Сайт: `http://127.0.0.1:8000/`
- Админка: `http://127.0.0.1:8000/admin/`
- Тарифы: `http://127.0.0.1:8000/pricing/`
- Кабинет: `http://127.0.0.1:8000/dashboard/`

## Реальные платежи Stripe

1. Установи зависимости:

```bash
pip install -r requirements.txt
```

2. Добавь переменные окружения:

```bash
set STRIPE_SECRET_KEY=sk_test_xxx
set STRIPE_PUBLISHABLE_KEY=pk_test_xxx
set STRIPE_WEBHOOK_SECRET=whsec_xxx
```

3. Прогони миграции после обновления модели покупок:

```bash
python manage.py migrate
```

4. Подключи webhook в Stripe:
- endpoint: `https://your-domain.com/payments/webhook/stripe/`
- event: `checkout.session.completed`

Локально можно прокинуть через Stripe CLI и слушать вебхуки на `http://127.0.0.1:8000/payments/webhook/stripe/`.

### Как теперь работает покупка

- Клик по покупке создает `Purchase` со статусом `pending`.
- Пользователь уходит в Stripe Checkout.
- После успешной оплаты Stripe шлет webhook.
- Webhook переводит `Purchase` в `paid` и выдает `UserAccess` для инструмента.

## Как наполнить каталог

В админке:
1. Добавь несколько категорий (например: Маркетинг, HR, Продажи).
2. Добавь AI-инструменты в эти категории:
   - Название и `seo_slug`
   - Для кого, сложность, цена
   - Тип AI-продукта (`Prompt`, `Agent`, `Mini Service`, `Integration`)
   - Краткое описание
   - Полное описание
   - Проблема/ценность, экономия часов, время запуска
   - Demo input / Demo output
   - Готовый промпт (опционально)
   - Ссылку на внешний сервис (опционально)
3. Добавь тарифы в `Plan` (например: Starter, Pro, Team).
4. Добавь отзывы в `Review`.

После сохранения инструменты сразу отобразятся на главной странице.

### Быстро создать категории из шаблона

```bash
python manage.py seed_categories
```

Команда создаст бизнес-категории и подкатегории из готовой структуры.

## Деплой на Render

В проект добавлен `render.yaml`, поэтому удобнее деплоить через Render Blueprint.

1. Загрузи проект в GitHub.
2. В Render выбери **New → Blueprint**.
3. Подключи репозиторий.
4. Render создаст:
   - web service `promptbase`
   - PostgreSQL database `promptbase-db`
5. В Render добавь секретные переменные:
   - `OPENAI_API_KEY`
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
   - `STRIPE_WEBHOOK_SECRET`
6. После деплоя открой URL вида `https://promptbase.onrender.com`.

`render.yaml` сам выполнит:

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py seed_categories
python manage.py seed_ai_tools
python manage.py seed_plans
gunicorn core.wsgi:application
```

Для своего домена добавь его в Render Custom Domains и пропиши:

```text
ALLOWED_HOSTS=your-domain.com,.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://*.onrender.com
```
