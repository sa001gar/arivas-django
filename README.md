git clone repo url

sudo apt install python3-pip python3-dev nginx

sudo apt install python3-virtualenv

virtualenv venv

source venv/bin/activate

pip install -r requirements.txt

for getting files..

scp -i login-arivas.pem ubuntu@56.228.36.187:/home/ubuntu/arivas-django/db.sqlite3 . 
scp -i arivas-new.pem db.sqlite3 ubuntu@13.126.150.157:/home/ubuntu/arivas-django/ 

copy media and products in local device

scp -i login-arivas.pem -r ubuntu@56.228.36.187:/home/ubuntu/arivas-django/media .


python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput


sudo nano /etc/systemd/system/gunicorn.socket

```bash
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

sudo nano /etc/systemd/system/gunicorn.service

```bash
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

sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket

cd /etc/nginx/sites-enabled
sudo rm *

sudo nano /etc/nginx/sites-available/arivas

```bash
# Serve HTTP for now — no redirect until SSL is configured
server {
    listen 80;
    server_name arivaspharma.co.in www.arivaspharma.co.in;

    root /home/ubuntu/arivas-django;  # adjust to your actual Django project path
    index index.html index.htm;

    # Required for Certbot challenge later
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


sudo ln -s /etc/nginx/sites-available/arivas /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl restart nginx
sudo service gunicorn restart
sudo service nginx restart

sudo apt install certbot python3-certbot-nginx -y

sudo nano .env

sudo certbot --nginx -d arivaspharma.co.in -d www.arivaspharma.co.in
sudo certbot renew --dry-run

```bash
# Redirect all HTTP requests to HTTPS
server {
    listen 80;
    server_name arivaspharma.co.in www.arivaspharma.co.in;

    location /.well-known/acme-challenge/ {
        root /var/www/html;  # keep this for certbot renewals
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# Main HTTPS server block
server {
    listen 443 ssl http2;
    server_name arivaspharma.co.in www.arivaspharma.co.in;

    ssl_certificate /etc/letsencrypt/live/arivaspharma.co.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/arivaspharma.co.in/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Static files
    location /staticfiles/ {
        root /home/ubuntu/arivas-django;
    }

    location /media/ {
        alias /home/ubuntu/arivas-django/media/;
    }

    # Proxy to Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```