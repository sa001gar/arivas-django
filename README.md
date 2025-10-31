# Arivas Django Deployment Guide

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