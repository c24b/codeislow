# DEPLOYER LE PROJET

Instructions pour déployer le projet sur un serveur. 

## Copier les sources sur le serveur


> Notez bien l'endroit où les sources sont installées!

scp -r codeislaw/ root@remotesrv:/

> Pensez bien à envoyer aussi le fichier .env
> Et eventuellement le virtualenv .venv

## Se Connecter au serveur et installer le projet


## Configurer le serveur http avec GUNICORN

Activer l'environnement virtuel

pip install gunicorn

gunicorn_config.py
bind = "0.0.0.0:8080"
workers = 2


## Activer le service avec Systemd

Créer un  fichier Systemd file `/etc/systemd/system/codeislaw.service`

Editer le fichier:

```
[Unit]
Description=Gunicorn instance to serve Code is Low
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/codeislow/src
Environment="PATH=/root/codeislow/venv/bin"
ExecStart=/root/codeislow/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

Modifier les droits d'accès
# chown -R root:www-data /root/codeislow
# chmod -R 775 /root/codeislow

systemctl daemon-reload

```
systemctl start codeislow
systemctl enable codeislow
systemctl status codeislow
```
## Configurer la résolution du nom de domaine avec NGINX

Configure NGINX

nano /etc/nginx/conf.d/codeislow.conf

```
server {
    listen 80;
    server_name codeislow.yourdomainname.com;

    location / {
        include proxy_params;
        proxy_pass  http://127.0.0.1:5000;

    }

}
```
nginx -t
systemctl restart nginx


## Tester

Rendez vous sur la page exemple: codeislow.yourdomainname.com