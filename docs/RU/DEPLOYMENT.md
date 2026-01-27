# PicoBlog - Руководство по установке и развертыванию

Это руководство содержит инструкции по настройке PicoBlog как для локальной разработки, так и для использования на сервере.

## Предварительные требования

- **Python 3.10+**
- **Node.js 18+** (для сборки CSS)
- **Git**
- **Docker и Docker Compose** (опционально, рекомендуется для продакшена)

---

## 1. Быстрый старт (Локально)

Выполните эти шаги, чтобы запустить PicoBlog локально за несколько минут.

### 1.1 Установка зависимостей

```bash
# Настройка виртуального окружения Python
uv venv
source .venv/bin/activate
uv sync

# Установка зависимостей Node
npm install
```

### 1.2 Настройка

```bash
cp .env.example .env
# Генерация безопасного секретного ключа
sed -i "s/^SECRET_KEY=.*/SECRET_KEY='$(python3 -c 'import secrets; print(secrets.token_hex(32))')'/" .env
```

### 1.3 Сборка и запуск

```bash
# Сборка CSS
npm run build:css

# Инициализация базы данных
export FLASK_APP=app
flask db upgrade

# Запуск сервера разработки
python run.py
```

Приложение будет доступно по адресу `http://127.0.0.1:5000`.

---

## 2. Развертывание через Docker (Рекомендуется)

Это самый простой способ развернуть PicoBlog. Он берет на себя все зависимости, сборку CSS и настройку WSGI-сервера.

### 2.1 Настройка

```bash
cp .env.example .env
# Установите FLASK_ENV в production
sed -i "s/FLASK_ENV=development/FLASK_ENV=production/" .env
# Генерация секретного ключа
sed -i "s/^SECRET_KEY=.*/SECRET_KEY='$(python3 -c 'import secrets; print(secrets.token_hex(32))')'/" .env
```

### 2.2 Запуск через Docker Compose

```bash
docker-compose up -d --build
```

Приложение будет доступно по адресу `http://127.0.0.1:8000`. Теперь вы можете настроить Nginx на проксирование к этому порту.

---

## 3. Ручное развертывание

Если вы предпочитаете не использовать Docker, следуйте этим шагам для традиционного развертывания в Linux.

### 3.1 Подготовка системы

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv nginx certbot python3-certbot-nginx nodejs npm
```

### 3.2 Настройка приложения

```bash
# Клонирование и настройка окружения
git clone https://github.com/Lowara1243/PicoBlog
cd PicoBlog
python3 -m venv .venv
source .venv/bin/activate
pip install uv
uv sync
npm install
npm run build:css
```

### 3.3 Настройка службы (systemd)

Создайте файл `/etc/systemd/system/PicoBlog.service`:

```ini
[Unit]
Description=PicoBlog Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/PicoBlog
Environment="PATH=/var/www/PicoBlog/.venv/bin"
ExecStart=/var/www/PicoBlog/.venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 "run:app"

Restart=always
[Install]
WantedBy=multi-user.target
```

## 4. Настройка Nginx

Выберите способ, соответствующий вашей инфраструктуре.

### Вариант А: Самостоятельный Nginx (управление SSL)
Используйте это, если PicoBlog — основное приложение на сервере.

1. **Копирование конфигурации:**
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/PicoBlog
   sudo ln -s /etc/nginx/sites-available/PicoBlog /etc/nginx/sites-enabled/
   ```
2. **Настройка SSL:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

### Вариант Б: За существующим Reverse Proxy
Если у вас уже есть прокси (например, Nginx Proxy Manager или другой экземпляр Nginx), который управляет SSL, просто перенаправьте трафик на адрес PicoBlog:

**Адрес для проксирования:** `http://127.0.0.1:8000`

**Пример для Nginx:**
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 5. Справочник переменных

| Переменная | Описание |
| :--- | :--- |
| `SECRET_KEY` | **Обязательно.** Случайная строка для безопасности сессий. |
| `FLASK_ENV` | Установите `production` для автоматических функций защиты. |
| `DATABASE_URL` | URL базы данных (По умолчанию: `sqlite:///data/app.db`). |
| `REQUIRE_LOGIN` | `True` (по умолчанию) для приватного режима. |

---

## Устранение неполадок

- **CSS не загружается?** Запустите `npm run build:css`.
- **502 Bad Gateway?** Проверьте, запущен ли Gunicorn или Docker на порту 8000.
- **Проблемы с правами?** Убедитесь, что `www-data` владеет папкой проекта при ручной настройке.

---

**Развертывание завершено!** Ваш экземпляр PicoBlog должен быть теперь безопасно запущен по адресу `https://your-domain.com`.