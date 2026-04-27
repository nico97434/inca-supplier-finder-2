# 🌍 INCA IMPORT — Supplier Finder

Outil Streamlit pour rechercher des fournisseurs mondiaux (Alibaba & Europages) via l'API Apify.

Conçu pour **INCA IMPORT SAS** — centrale d'achat du groupe Incana (stations OLA / TOTAL / VITO, La Réunion).

---

## ✨ Fonctionnalités

- 🔍 Recherche par mot-clé produit
- 🗺️ 2 zones : Asie (Alibaba) ou Europe (Europages)
- 📅 Filtrage par années d'expérience minimum
- 🏷️ Note Import automatique :
  - Europe → *Avantage douanier (EUR1)*
  - Asie → *Contrôle qualité requis*
- 📥 Export Excel (.xlsx) et CSV (séparateur `;` compatible Excel FR)
- 🔐 Token Apify géré via `st.secrets` (jamais exposé sur GitHub)
- ⚡ Cache 1h pour économiser les crédits Apify

---

## 🚀 Installation locale

```bash
# 1. Cloner le repo
git clone https://github.com/<votre-user>/inca-supplier-finder.git
cd inca-supplier-finder

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer le token Apify (voir section ci-dessous)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Éditer le fichier et coller votre vrai token

# 5. Lancer l'app
streamlit run app.py
```

L'app s'ouvre sur http://localhost:8501

---

## 🔐 Configuration des Secrets (token Apify)

### Obtenir un token Apify

1. Créer un compte sur [https://apify.com](https://apify.com) (plan gratuit dispo)
2. Aller dans **Settings → Integrations → Personal API tokens**
3. Copier le token (format : `apify_api_xxxxxxxxxxxx`)

### Configuration en LOCAL

Créer le fichier `.streamlit/secrets.toml` à la racine du projet :

```toml
APIFY_TOKEN = "apify_api_VOTRE_VRAI_TOKEN"
```

⚠️ **Ce fichier est dans `.gitignore` — il ne sera jamais poussé sur GitHub.**

### Configuration sur STREAMLIT CLOUD

1. Pousser le code sur GitHub (sans `secrets.toml` !)
2. Aller sur [https://share.streamlit.io](https://share.streamlit.io)
3. Cliquer sur **New app** → sélectionner votre repo + branche `main` + `app.py`
4. Avant de déployer, cliquer sur **Advanced settings…**
5. Dans la section **Secrets**, coller :
   ```toml
   APIFY_TOKEN = "apify_api_VOTRE_VRAI_TOKEN"
   ```
6. Cliquer sur **Deploy**

✅ L'app récupère automatiquement le token via `st.secrets["APIFY_TOKEN"]`.

### Modifier les secrets après déploiement

Sur Streamlit Cloud : **Manage app → Settings → Secrets → Edit secrets**.
Pas besoin de re-déployer, le redémarrage est automatique.

---

## 📦 Structure du projet

```
inca-supplier-finder/
├── app.py                              # Application Streamlit
├── requirements.txt                    # Dépendances Python
├── .gitignore                          # Protège secrets.toml
├── README.md                           # Ce fichier
└── .streamlit/
    ├── secrets.toml.example            # Template (commitable)
    └── secrets.toml                    # Vraie clé (JAMAIS commitée)
```

---

## ⚙️ Actors Apify utilisés

| Zone | Actor | Lien |
|---|---|---|
| Asie | `zuzka/alibaba-scraper` | [apify.com/zuzka/alibaba-scraper](https://apify.com/zuzka/alibaba-scraper) |
| Europe | `apify/europages-scraper` | [apify.com/apify/europages-scraper](https://apify.com/apify/europages-scraper) |

> 💡 Les Actors Apify sont **payants à l'usage** (quelques centimes par recherche). Le cache 1h évite les appels répétés sur la même requête.

---

## 🧪 Tests rapides

Exemples de recherches utiles pour INCA IMPORT :

| Produit | Zone recommandée |
|---|---|
| `monster energy 500ml` | 🇪🇺 Europe (Pologne, Allemagne) |
| `pokka coffee 240ml` | 🌏 Asie (Singapour, source officielle) |
| `frozen croissant pain au chocolat` | 🇪🇺 Europe (France/Espagne — Bridor, Europastry) |
| `chips snack` | 🇪🇺 Europe |

---

## 🛠️ Dépannage

| Erreur | Solution |
|---|---|
| `Token Apify manquant` | Vérifier `.streamlit/secrets.toml` ou les Secrets sur Cloud |
| `Aucun résultat` | Élargir les mots-clés, baisser le filtre années d'expérience |
| `Timeout` | L'Actor Apify est lent — réessayer ou réduire `max_results` |
| Crédits Apify épuisés | Vérifier votre plan sur [console.apify.com](https://console.apify.com) |

---

## 📜 Licence

Usage interne INCA IMPORT SAS — La Réunion.
