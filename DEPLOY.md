# DEPLOYER LE PROJET

Instructions pour déployer le projet sur un serveur Debian. 

## Copier les sources sur le serveur

> A noter: Les sources du code sont dans src

- Depuis github:

git clone git@github.com:c24b/codeislow.git

- Depuis votre ordinateur personnel

scp -r ~/codeislow/ root@srv:/

> Notez bien le chemin absolu des sources installées sur le serveur!

## Installer les minimum requis sur le serveur

`sudo apt-get install python3-pip libssl-dev libffi-dev python3-dev build-essential python3-setuptools virtualenv python3-venv -y`

## Installer un environnement virtuel

```bash
root@srv:~/codeislow/$ virtualenv .venv --python=python3.8
root@srv:~/codeislow/$ source .venv/bin/activate
```

## Installer les dépendances

```
(.venv) root@srv:~/codeislow/$ pip install -r requirements.txt
```

## Créer ou copier un fichier .env
A partir du fichier dotenv.example

```
API_KEY=
API_SECRET=
APP_LOCATION=
APP_PORT=
```

Pour obtenir des clés API de PISTE se reporter à la [notice d'installation](INSTALL.md#enregistrer-son-application-sur-piste)

> Déplacer le contenu du fichier `src/` à la racine du projet

## Configurer l'application avec GUNICORN

- Dans l'environnement virtuel installer gunicorn

`pip install gunicorn`

- Déplacer les fichiers src/ à la racine de projets

- Tester l'application avec gunicorn:

`$ gunicorn --bind 0.0.0.0:5000 app:app`

## Activer le service avec Systemd

Créer et éditer un  fichier Systemd: `/etc/systemd/system/codeislaw.service`

```
[Unit]
Description=Gunicorn instance to serve Code is Low
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/codeislow/
Environment="PATH=/root/codeislow/venv/bin"
ExecStart=/root/codeislow/venv/bin/gunicorn --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

- Modifier les droits d'accès
`chown -R root:www-data /root/codeislow`
`chmod -R 775 /root/codeislow`

- Redémarrer system d
  
`systemctl daemon-reload`

- Activer le service:

```
systemctl start codeislow
systemctl enable codeislow
systemctl status codeislow
```

## Configurer la résolution du nom de domaine avec NGINX

- Configurer avec nginx en créant un fichier : 
`/etc/nginx/conf.d/codeislow.conf`

```
server {
    listen 80;
    server_name codeislow.example.com;

    location / {
        include proxy_params;
        proxy_pass  http://127.0.0.1:5000;

    }

}
```

nginx -t
systemctl restart nginx


## Tester

Rendez vous sur la page: codeislow.example.com
