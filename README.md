# Data Studio

## Connexion

Le mot de passe de démonstration par défaut est `admin123`. Avant tout déploiement,
remplace-le avec la variable d’environnement `DATA_STUDIO_PASSWORD`.

Dans PowerShell :

```powershell
$env:DATA_STUDIO_PASSWORD = "un-mot-de-passe-fort"
streamlit run app.py
```

Cette connexion est une protection légère par session Streamlit, pas un système
d’authentification adapté aux données sensibles ou à un déploiement public.