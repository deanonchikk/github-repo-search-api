# GitHub Repository Search API

FastAPI-сервис для поиска репозиториев на GitHub и экспорта результатов в CSV файлы.

## 📋 Описание

REST API для поиска GitHub репозиториев с фильтрацией по языку программирования, звёздам и форкам. Результаты автоматически сохраняются в CSV файлы.

## 🏗️ Архитектура

Проект построен на трёхслойной архитектуре:

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                            │
│              web/api/repositories/                      │
│      HTTP эндпойнты, валидация, Pydantic схемы          │
├─────────────────────────────────────────────────────────┤
│                  Service Layer                          │
│                    services/                            │
│       Бизнес-логика, генерация CSV файлов               │
├─────────────────────────────────────────────────────────┤
│               Infrastructure Layer                      │
│                  infrastructure/                        │
│          HTTP клиент для GitHub API                     │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Быстрый старт

### Требования

- `Python 3.12+`
- `uv` - менеджер зависимостей

### Установка

```bash
# Установка зависимостей
make install
# или
uv sync
```

### Запуск

```bash
# Production режим
make run

# Development режим с перезагрузкой
make dev
```

Сервер запустится на `http://127.0.0.1:8000`

## 🔍 Использование API

### Поиск репозиториев

**GET** `/api/repositories/search`

#### Параметры запроса

| Параметр    | Тип      | Обязательный | По умолчанию | Описание                              |
|-------------|----------|--------------|--------------|---------------------------------------|
| `lang`      | string   | ✅ Да        | —            | Язык программирования                 |
| `limit`     | integer  | Нет          | 10           | Количество репозиториев (1-1000)      |
| `offset`    | integer  | Нет          | 0            | Смещение для пагинации                |
| `stars_min` | integer  | Нет          | 0            | Минимальное количество звёзд          |
| `stars_max` | integer  | Нет          | None         | Максимальное количество звёзд         |
| `forks_min` | integer  | Нет          | 0            | Минимальное количество форков         |
| `forks_max` | integer  | Нет          | None         | Максимальное количество форков        |

Ожидаем следующий параметр запроса ответом в PR!

#### Пример запроса

```bash
curl "http://127.0.0.1:8000/api/repositories/search?lang=python&limit=10&stars_min=1000"
```

#### Пример ответа

```json
{
  "count": 10,
  "filename": "repositories_python_10_0.csv",
  "filepath": "/path/to/static/repositories_python_10_0.csv",
  "repositories": [
    {
      "name": "awesome-python",
      "description": "A curated list of awesome Python frameworks",
      "url": "https://github.com/vinta/awesome-python",
      "size": 5432,
      "stars": 150000,
      "forks": 20000,
      "issues": 50,
      "language": "Python",
      "license": "CC-BY-4.0"
    }
  ]
}
```

## 📄 Формат CSV

Генерируемые CSV файлы имеют следующую структуру:

```csv
name,description,url,size,stars,forks,issues,language,license
```

Файлы сохраняются в `github_repo_search_api/static/` с именем: `repositories_{lang}_{limit}_{offset}.csv`

## ⚙️ Конфигурация

Создайте файл `.env` в корне проекта (или скопируйте из `.env.example`):

```bash
cp .env.example .env
```

### Переменные окружения

```env
# GitHub API токен (опционально, увеличивает лимит запросов)
# Раскомментируйте и укажите ваш реальный токен:
# GITHUB_REPO_SEARCH_API_GITHUB_TOKEN=your_token_here

# Хост и порт сервера
GITHUB_REPO_SEARCH_API_HOST=127.0.0.1
GITHUB_REPO_SEARCH_API_PORT=8000

# Уровень логирования (NOTSET | DEBUG | INFO | WARNING | ERROR | FATAL)
GITHUB_REPO_SEARCH_API_LOG_LEVEL=INFO
```

## 🔍 Качество кода

```bash
# Проверка линтером (без исправлений)
make lint-check

# Линтинг с автоисправлением
make lint

# Форматирование кода
make format

# Покрытие тестами
make coverage
```

## 🐳 Docker

### Запуск в контейнере

```bash
# Сборка образа
make build

# Запуск контейнера
make up

# Остановка
make down

# Просмотр логов
make logs
```

API будет доступен на `http://localhost:8000`

### Docker Compose

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./github_repo_search_api/static:/app/github_repo_search_api/static
    environment:
      GITHUB_REPO_SEARCH_API_HOST: 0.0.0.0
```

## 📁 Структура проекта

```
github_repo_search_api/
├── github_repo_search_api/
│   ├── infrastructure/           # Внешние интеграции
│   │   └── github_client.py      # HTTP клиент для GitHub API
│   ├── services/                 # Бизнес-логика
│   │   └── github_search_service.py
│   ├── web/
│   │   ├── api/
│   │   │   └── repositories/     # API эндпойнты
│   │   │       ├── schema.py     # Pydantic модели
│   │   │       └── views.py      # Обработчики запросов
│   │   ├── application.py        # Фабрика FastAPI приложения
│   │   └── lifespan.py           # Жизненный цикл приложения
│   ├── static/                   # Генерируемые CSV файлы
│   ├── settings.py               # Конфигурация
│   └── __main__.py               # Точка входа
├── tests/                        # Тесты
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── README.md
```

## 📝 Makefile команды

| Команда          | Описание                             |
|------------------|--------------------------------------|
| `make install`   | Установка зависимостей               |
| `make run`       | Запуск сервера                       |
| `make dev`       | Запуск в режиме разработки           |
| `make test`      | Запуск тестов                        |
| `make lint`      | Линтинг с автоисправлением           |
| `make lint-check`| Проверка линтером                    |
| `make format`    | Форматирование кода                  |
| `make build`     | Сборка Docker образа                 |
| `make up`        | Запуск Docker контейнера             |
| `make down`      | Остановка Docker контейнера          |
| `make logs`      | Просмотр логов Docker                |
| `make restart`   | Перезапуск Docker контейнера         |

