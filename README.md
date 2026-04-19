# Arivas Django Deployment Guide

## Dokploy + Cloudflare R2 (Recommended)

This project is now ready to deploy on Dokploy with product/media uploads served from Cloudflare R2.

### 1. Local install with uv

```bash
uv pip install -r requirements.txt
uv pip install django-storages boto3
```

### 2. Configure environment

Create `.env` from `.env.example` and set at least:

- `DEBUG=False`
- `SECRET_KEY=...`
- `ALLOWED_HOSTS=...`
- `CSRF_TRUSTED_ORIGINS=...`
- `USE_R2=True`
- `R2_ACCOUNT_ID=...`
- `R2_ACCESS_KEY_ID=...`
- `R2_SECRET_ACCESS_KEY=...`
- `R2_BUCKET_NAME=...`
- `R2_PUBLIC_MEDIA_URL=...` (custom domain or `*.r2.dev` URL)

### 3. Audit and upload initial product images to R2

Dry-run first:

```bash
uv run python scripts/sync_products_to_r2.py --dry-run --fix-missing
```

Then upload:

```bash
uv run python scripts/sync_products_to_r2.py --fix-missing --skip-existing
```

### 4. Dokploy service setup

- Build method: Dockerfile
- Dockerfile path: `./Dockerfile`
- Exposed port: `8000` (or set `PORT` env)
- Start command: already handled by `docker/entrypoint.sh`

The container startup does:

1. `python manage.py migrate --noinput`
2. `python manage.py collectstatic --noinput`
3. starts Gunicorn on `0.0.0.0:$PORT`

### 5. Persistent data note (SQLite)

If you continue using SQLite in production, mount a Dokploy persistent volume so `db.sqlite3` is not lost between deployments.

---

This guide provides step-by-step instructions to deploy the Arivas Django application on an Ubuntu server using Gunicorn and Nginx, with SSL via Certbot.

---

## 1. Clone the Repository

```bash
git clone <repo-url>
```

---

## 2. Install Dependencies

```bash
sudo apt update
sudo apt install python3-pip python3-dev nginx python3-virtualenv -y
```

---

## 3. Set Up Virtual Environment

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Transfer Database and Media Files

- **Download database from old server:**
    ```bash
    scp -i login-arivas.pem ubuntu@56.228.36.187:/home/ubuntu/arivas-django/db.sqlite3 .
    ```
- **Upload database to new server:**
    ```bash
    scp -i arivas-new.pem db.sqlite3 ubuntu@13.126.150.157:/home/ubuntu/arivas-django/
    ```
- **Copy media files:**
    ```bash
    scp -i login-arivas.pem -r ubuntu@56.228.36.187:/home/ubuntu/arivas-django/media .
    ```

---

## 5. Django Migrations & Static Files

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

---

## 6. Configure Gunicorn

Create the Gunicorn socket file:

```bash
sudo nano /etc/systemd/system/gunicorn.socket
```

Paste:
```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

Create the Gunicorn service file:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Paste:
```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/arivas-django
ExecStart=/home/ubuntu/arivas-django/venv/bin/gunicorn \
                    --access-logfile - \
                    --workers 3 \
                    --bind unix:/run/gunicorn.sock \
                    arivas.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start and enable Gunicorn:

```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```

---

## 7. Configure Nginx

Remove default sites:

```bash
cd /etc/nginx/sites-enabled
sudo rm *
```

Create Nginx config:

```bash
sudo nano /etc/nginx/sites-available/arivas
```

Paste:
```nginx
server {
        listen 80;
        server_name arivaspharma.co.in www.arivaspharma.co.in;

        root /home/ubuntu/arivas-django;
        index index.html index.htm;

        location /.well-known/acme-challenge/ {
                root /var/www/html;
        }

        location /static/ {
                alias /home/ubuntu/arivas-django/static/;
        }

        location /media/ {
                alias /home/ubuntu/arivas-django/media/;
        }

        location / {
                include proxy_params;
                proxy_pass http://unix:/run/gunicorn.sock;
        }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/arivas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo service gunicorn restart
sudo service nginx restart
```

---

## 8. Enable SSL with Certbot

Install Certbot:

```bash
sudo apt install certbot python3-certbot-nginx -y
```

Create your `.env` file as needed.

Obtain SSL certificates:

```bash
sudo certbot --nginx -d arivaspharma.co.in -d www.arivaspharma.co.in
sudo certbot renew --dry-run
```

---

## 9. Update Nginx for HTTPS

Edit your Nginx config to redirect HTTP to HTTPS and serve SSL:

```nginx
# Redirect HTTP to HTTPS
server {
        listen 80;
        server_name arivaspharma.co.in www.arivaspharma.co.in;

        location /.well-known/acme-challenge/ {
                root /var/www/html;
        }

        location / {
                return 301 https://$host$request_uri;
        }
}

# HTTPS server block
server {
        listen 443 ssl http2;
        server_name arivaspharma.co.in www.arivaspharma.co.in;

        ssl_certificate /etc/letsencrypt/live/arivaspharma.co.in/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/arivaspharma.co.in/privkey.pem;
        include /etc/letsencrypt/options-ssl-nginx.conf;
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

        location /staticfiles/ {
                root /home/ubuntu/arivas-django;
        }

        location /media/ {
                alias /home/ubuntu/arivas-django/media/;
        }

        location / {
                include proxy_params;
                proxy_pass http://unix:/run/gunicorn.sock;
        }
}
```

Reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 10. Maintenance

- To renew SSL certificates:
    ```bash
    sudo certbot renew
    ```
- To restart services:
    ```bash
    sudo systemctl restart gunicorn
    sudo systemctl restart nginx
    ```

---

**Deployment complete! Your Django app should now be live and secure.**