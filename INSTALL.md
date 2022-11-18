# INSTALLATION


Instructions pour exécuter le projet en local. Pour déployer le projet sur un serveur consultez la documentation [DEPLOY.md](DEPLOY.md)

## Récupérer les sources
```bash
moi@ordinateur:~$ git clone https://github.com/c24b/codeislow
moi@ordinateur:~$ cd codeislaw
```

## Installer un environnement virtuel

```bash
moi@ordinateur:~/codeislow/$ virtualenv .venv --python=python3.8
moi@ordinateur:~/codeislow/$ source .venv/bin/activate
```

## Installer les dépendances

```
(.venv) moi@ordinateur:~/codeislow/$ pip install -r requirements.txt
```

## Enregistrer son application sur PISTE

- Se rendre sur https://piste.gouv.fr/
- Créer un compte https://piste.gouv.fr/registration
- Créer une application https://piste.gouv.fr/apps sur l'environnement `SANDBOX`
- Cocher la case accès à l'API Légifrance Beta
- Dans l'onglet authentification: 
  - générer la clé API
  - générer les identifiants Oauth 
  > ce sont ces derniers qui serviront dans l'application

## Enregister les clés authentifications API LEGIFRANCE 

- Ouvrir le fichier dotenv.example
- Ajouter les identifiants Oauth correspondants dans :
  `API_KEY=`
  `API_SECRET=`
- Renommer et sauvegarder le fichier en `.env`

## Lancer le projet

`(.venv) moi@ordinateur:~/codeislow/ python src/app.py`

Rendez vous sur [http://localhost:8080](http://localhost:8080)
