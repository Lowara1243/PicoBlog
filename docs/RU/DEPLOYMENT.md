# PicoBlog - Руководство по развертыванию в производственной среде

Это руководство описывает развертывание PicoBlog на производственном сервере с использованием Nginx, Gunicorn и SSL-сертификатов.

## Предварительные требования

- Сервер с Ubuntu/Debian и root-доступом
- Доменное имя, указывающее на IP-адрес вашего сервера
- Git
- Python 3.10+
- Node.js 18+ (для сборки CSS)

## 1. Настройка сервера

### Установка системных зависимостей:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv nginx certbot python3-certbot-nginx nodejs npm
```

### Создание каталога для приложения и клонирование репозитория:

```bash
# Создание родительского каталога
sudo mkdir -p /var/www
sudo chown $USER:$USER /var/www
cd /var/www

# Клонирование репозитория
git clone https://github.com/Lowara1243/PicoBlog.git
cd PicoBlog
```
> **Примечание:** Замените `<YOUR_REPOSITORY_URL>` на фактический URL вашего Git-репозитория.

## 2. Настройка приложения

### Создание виртуального окружения Python:

```bash
cd /var/www/PicoBlog
python3 -m venv .venv
source .venv/bin/activate
```

### Установка зависимостей Python:

```bash
# Если используется uv (рекомендуется):
pip install uv
uv sync
```

### Установка зависимостей Node и сборка CSS:

```bash
npm install
npm run build:css
```

### Создание файла .env:

Создайте файл `.env`, скопировав пример:
```bash
cp .env.example .env
```

Теперь отредактируйте файл `.env` и установите ваш `SECRET_KEY`.
```bash
nano .env
```

**ВАЖНО:** Сгенерируйте надежный `SECRET_KEY` с помощью этой команды и добавьте его в файл `.env`:
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Ваш `.env` должен выглядеть примерно так:
```ini
# Сгенерировать с помощью: python -c 'import secrets; print(secrets.token_hex(32))'
SECRET_KEY=your-generated-secret-key-here

# База данных (SQLite для небольших развертываний, PostgreSQL рекомендуется для производственной среды)
DATABASE_URL=sqlite:////var/www/PicoBlog/data/app.db

# Окружение
FLASK_ENV=production
```

### Создание каталогов для данных и загрузок:

```bash
mkdir -p /var/www/PicoBlog/data
mkdir -p /var/www/PicoBlog/app/static/uploads
chmod 755 /var/www/PicoBlog/data /var/www/PicoBlog/app/static/uploads
```

### Инициализация базы данных:

```bash
export FLASK_APP=app
.venv/bin/flask db upgrade

# Создание пользователя-администратора
.venv/bin/flask shell
```
Внутри оболочки Flask выполните следующий код на Python:
```python
from app.models import User
from app import db
# Замените на желаемые имя пользователя, email и надежный пароль администратора
admin = User(username='admin', email='admin@example.com', is_admin=True)
admin.set_password(r'your-strong-password-here')
db.session.add(admin)
db.session.commit()
exit()
```

## 3. Настройка Gunicorn

### Установка Gunicorn:

```bash
.venv/bin/pip install gunicorn
```

### Создание файла службы systemd:

```bash
sudo nano /etc/systemd/system/PicoBlog.service
```

Добавьте следующее содержимое:

```ini
[Unit]
Description=PicoBlog Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/PicoBlog
Environment="PATH=/var/www/PicoBlog/.venv/bin"
ExecStart=/var/www/PicoBlog/.venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/PicoBlog/access.log \
    --error-logfile /var/log/PicoBlog/error.log \
    --log-level info \
    "app:app"

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

### Создание каталога для логов:

```bash
sudo mkdir -p /var/log/PicoBlog
sudo chown www-data:www-data /var/log/PicoBlog
```

### Установка правильных прав доступа:

```bash
sudo chown -R www-data:www-data /var/www/PicoBlog
sudo chmod -R 755 /var/www/PicoBlog
```

### Включение и запуск службы:

```bash
sudo systemctl daemon-reload
sudo systemctl enable PicoBlog
sudo systemctl start PicoBlog
sudo systemctl status PicoBlog
```

## 4. Конфигурация Nginx

### Копирование конфигурации nginx:

```bash
sudo cp /var/www/PicoBlog/nginx.conf /etc/nginx/sites-available/PicoBlog
```

### Редактирование конфигурации с вашим доменом:

```bash
sudo nano /etc/nginx/sites-available/PicoBlog
```

Замените `your-domain.com` на ваше фактическое доменное имя.

> [!TIP]
> Предоставленный `nginx.conf` уже включает настройки сжатия Gzip. Это значительно уменьшает размер файлов HTML, CSS и JS, улучшая производительность на медленных сетях и мобильных устройствах.

### Создание каталога для certbot:

```bash
sudo mkdir -p /var/www/certbot
```

### Включение сайта:

```bash
sudo ln -s /etc/nginx/sites-available/PicoBlog /etc/nginx/sites-enabled/
sudo nginx -t  # Проверка конфигурации
sudo systemctl reload nginx
```

## 5. SSL-сертификат с помощью Certbot

### Получение сертификата:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Следуйте инструкциям. Certbot:
- Проверит владение доменом
- Получит SSL-сертификат
- Автоматически обновит конфигурацию nginx

### Проверка автоматического обновления:

```bash
sudo certbot renew --dry-run
```

Certbot автоматически настраивает cron-задачу для обновления.

## 6. Конфигурация для производственной среды

### Обновление настроек безопасности в config.py:

Отредактируйте `/var/www/PicoBlog/config.py` и раскомментируйте:

```python
SESSION_COOKIE_SECURE = True  # Отправлять cookie только через HTTPS
REMEMBER_COOKIE_SECURE = True
```

### Перезапуск приложения:

```bash
sudo systemctl restart PicoBlog
```

## 7. Проверка развертывания

### Проверка служб:

```bash
sudo systemctl status PicoBlog
sudo systemctl status nginx
```

### Проверка логов:

```bash
# Логи приложения
sudo tail -f /var/log/PicoBlog/error.log

# Логи Nginx
sudo tail -f /var/log/nginx/PicoBlog_error.log
```

### Тестирование сайта:

Посетите `https://your-domain.com` и проверьте:
- [ ] Сайт загружается по HTTPS
- [ ] HTTP перенаправляется на HTTPS
- [ ] Статические файлы загружаются корректно
- [ ] Вход в систему работает
- [ ] Панель администратора доступна
- [ ] Загрузка изображений работает

## 8. Обслуживание

### Обновление приложения:

```bash
cd /var/www/PicoBlog
git pull origin main
source .venv/bin/activate

# Обновление зависимостей
uv sync

# Пересборка CSS
npm run build:css

# Применение миграций базы данных
.venv/bin/flask db upgrade

# Установка правильных прав доступа и перезапуск
sudo chown -R www-data:www-data /var/www/PicoBlog
sudo systemctl restart PicoBlog
```

### Резервное копирование базы данных:

```bash
# Для SQLite
sudo cp /var/www/PicoBlog/data/app.db /var/backups/PicoBlog-$(date +%Y%m%d).db

# Для PostgreSQL
pg_dump PicoBlog > /var/backups/PicoBlog-$(date +%Y%m%d).sql
```

### Просмотр логов:

```bash
# Логи приложения
sudo journalctl -u PicoBlog -f

# Логи доступа Nginx
sudo tail -f /var/log/nginx/PicoBlog_access.log
```

## 9. Устранение неполадок

### Приложение не запускается:

```bash
sudo journalctl -u PicoBlog -n 50
```

Проверьте:
- Отсутствие `SECRET_KEY` в `.env`
- Ошибки подключения к базе данных
- Проблемы с правами доступа

### 502 Bad Gateway:

- Проверьте, запущен ли Gunicorn: `sudo systemctl status PicoBlog`
- Проверьте, слушается ли порт 8000: `sudo netstat -tlnp | grep 8000`
- Проверьте лог ошибок nginx: `sudo tail /var/log/nginx/PicoBlog_error.log`

### Статические файлы не загружаются:

- Убедитесь, что путь в `nginx.conf` соответствует фактическому местоположению
- Проверьте права доступа: `ls -la /var/www/PicoBlog/app/static/`
- Пересоберите CSS: `npm run build:css`

### Ошибки при загрузке:

- Проверьте, что каталог для загрузок существует и доступен для записи
- Убедитесь, что `MAX_CONTENT_LENGTH` в `config.py` соответствует `client_max_body_size` в nginx

## 10. Безопасность

### Настройка брандмауэра:

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## 11. Необязательно: Настройка PostgreSQL

Для производственной среды с несколькими пользователями рекомендуется PostgreSQL:

```bash
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Создание базы данных и пользователя
sudo -u postgres psql
CREATE DATABASE PicoBlog;
CREATE USER PicoBlog_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE PicoBlog TO PicoBlog_user;
\q

# Обновление .env
DATABASE_URL=postgresql://PicoBlog_user:secure-password@localhost/PicoBlog

# Установка адаптера PostgreSQL
.venv/bin/pip install psycopg2-binary

# Инициализация базы данных
.venv/bin/flask db upgrade
```

## Поддержка

При возникновении проблем проверьте:
- Логи приложения: `/var/log/PicoBlog/`
- Логи Nginx: `/var/log/nginx/`
- Журнал systemd: `sudo journalctl -u PicoBlog`

---

**Развертывание завершено!** Ваш экземпляр PicoBlog должен быть теперь безопасно запущен по адресу `https://your-domain.com`.