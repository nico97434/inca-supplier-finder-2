"""
INCA IMPORT — Supplier Finder
Application Streamlit pour rechercher des fournisseurs mondiaux
via les Actors Apify (Alibaba & Europages).

Auteur : INCA IMPORT SAS — La Réunion
"""

import io
from datetime import datetime

import pandas as pd
import streamlit as st
from apify_client import ApifyClient

# ======================================================================
# CONFIGURATION DE LA PAGE
# ======================================================================
st.set_page_config(
    page_title="INCA IMPORT — Supplier Finder",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================================================================
# CONSTANTES
# ======================================================================
ACTOR_ALIBABA = "zuzka/alibaba-scraper"
ACTOR_EUROPAGES = "apify/europages-scraper"

ZONES = {
    "🌏 Asie (Alibaba)": "alibaba",
    "🇪🇺 Europe (Europages)": "europages",
}

# ======================================================================
# AUTHENTIFICATION APIFY
# ======================================================================
def get_apify_client() -> ApifyClient | None:
    """Récupère le client Apify depuis st.secrets."""
    try:
        token = st.secrets["APIFY_TOKEN"]
        return ApifyClient(token)
    except (KeyError, FileNotFoundError):
        st.error(
            "🔐 **Token Apify manquant.** Configurez `APIFY_TOKEN` dans "
            "`.streamlit/secrets.toml` (local) ou dans les Secrets de Streamlit Cloud."
        )
        return None


# ======================================================================
# FONCTIONS DE SCRAPING
# ======================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def search_alibaba(client_token: str, query: str, max_results: int = 50) -> list[dict]:
    """
    Lance l'Actor Alibaba scraper.
    Note : on passe le token (string) plutôt que le client pour permettre le cache.
    """
    client = ApifyClient(client_token)
    run_input = {
        "search": query,
        "maxItems": max_results,
        "proxy": {"useApifyProxy": True},
    }
    run = client.actor(ACTOR_ALIBABA).call(run_input=run_input, timeout_secs=300)
    if run is None or run.get("status") != "SUCCEEDED":
        return []
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


@st.cache_data(ttl=3600, show_spinner=False)
def search_europages(client_token: str, query: str, max_results: int = 50) -> list[dict]:
    """Lance l'Actor Europages scraper."""
    client = ApifyClient(client_token)
    run_input = {
        "searchQuery": query,
        "maxItems": max_results,
    }
    run = client.actor(ACTOR_EUROPAGES).call(run_input=run_input, timeout_secs=300)
    if run is None or run.get("status") != "SUCCEEDED":
        return []
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


# ======================================================================
# NETTOYAGE & NORMALISATION
# ======================================================================
def normalize_alibaba(items: list[dict]) -> pd.DataFrame:
    """Standardise la sortie Alibaba vers le schéma cible."""
    rows = []
    for it in items:
        name = it.get("companyName") or it.get("supplierName") or it.get("name", "—")
        country = it.get("country") or it.get("location") or "Asie"
        years = it.get("yearsAsGoldSupplier") or it.get("years") or it.get("companyYears", 0)
        try:
            years = int(years) if years else 0
        except (ValueError, TypeError):
            years = 0
        score = it.get("rating") or it.get("score") or it.get("transactionLevel", "—")
        link = it.get("supplierUrl") or it.get("companyUrl") or it.get("url", "—")

        rows.append({
            "Entreprise": name,
            "Pays": country,
            "Score fiabilité": score,
            "Années d'existence": years,
            "Lien / Contact": link,
        })
    return pd.DataFrame(rows)


def normalize_europages(items: list[dict]) -> pd.DataFrame:
    """Standardise la sortie Europages vers le schéma cible."""
    rows = []
    for it in items:
        name = it.get("companyName") or it.get("name", "—")
        country = it.get("country") or it.get("address", {}).get("country", "Europe")
        years = it.get("foundedYear") or it.get("yearFounded")
        if years:
            try:
                years = datetime.now().year - int(years)
            except (ValueError, TypeError):
                years = 0
        else:
            years = 0
        score = it.get("verified", "Vérifié") if it.get("verified") else "Standard"
        link = it.get("url") or it.get("website") or it.get("companyUrl", "—")

        rows.append({
            "Entreprise": name,
            "Pays": country,
            "Score fiabilité": score,
            "Années d'existence": years,
            "Lien / Contact": link,
        })
    return pd.DataFrame(rows)


def add_import_note(df: pd.DataFrame, zone: str) -> pd.DataFrame:
    """
    Ajoute la colonne 'Note Import' :
      - Europe → 'Avantage douanier (EUR1)'
      - Asie    → 'Contrôle qualité requis'
    """
    if df.empty:
        return df
    if zone == "europages":
        df["Note Import"] = "🇪🇺 Avantage douanier (EUR1)"
    else:
        df["Note Import"] = "🔍 Contrôle qualité requis"
    return df


# ======================================================================
# EXPORT EXCEL (xlsxwriter en mémoire)
# ======================================================================
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convertit le DataFrame en fichier Excel (bytes) pour le download_button."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Fournisseurs")
        # Ajustement automatique de la largeur des colonnes
        worksheet = writer.sheets["Fournisseurs"]
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, min(max_len, 60))
    return buffer.getvalue()


# ======================================================================
# INTERFACE UTILISATEUR
# ======================================================================
def render_sidebar() -> dict:
    """Construit la barre latérale et retourne les paramètres."""
    with st.sidebar:
        st.markdown("## 🌍 Recherche fournisseurs")
        st.caption("INCA IMPORT SAS — La Réunion")
        st.divider()

        product = st.text_input(
            "📦 Produit recherché",
            placeholder="ex: monster energy, pokka coffee, croissant frozen…",
            help="Mots-clés du produit à sourcer (en anglais de préférence pour Alibaba).",
        )

        zone_label = st.selectbox(
            "🗺️ Zone de recherche",
            list(ZONES.keys()),
            help="Alibaba pour l'Asie, Europages pour l'Europe.",
        )

        min_years = st.slider(
            "📅 Années d'expérience minimum",
            min_value=0,
            max_value=30,
            value=3,
            help="Filtre les fournisseurs trop récents (recommandé : 3+ ans).",
        )

        max_results = st.slider(
            "🔢 Nombre maximum de résultats",
            min_value=10,
            max_value=100,
            value=50,
            step=10,
        )

        st.divider()
        launch = st.button("🚀 Lancer la recherche", type="primary", use_container_width=True)

        with st.expander("ℹ️ À propos"):
            st.caption(
                "Outil de sourcing pour INCA IMPORT. Les résultats sont mis en cache "
                "1 heure pour économiser les crédits Apify."
            )

    return {
        "product": product.strip(),
        "zone_label": zone_label,
        "zone": ZONES[zone_label],
        "min_years": min_years,
        "max_results": max_results,
        "launch": launch,
    }


def render_header() -> None:
    """En-tête de la page principale."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🌍 INCA IMPORT — Supplier Finder")
        st.markdown(
            "Recherche de fournisseurs internationaux pour le sourcing "
            "boissons & snacks (3 stations OLA / TOTAL / VITO — La Réunion)."
        )
    with col2:
        st.metric("Statut", "🟢 Opérationnel")


def render_results(df: pd.DataFrame, params: dict) -> None:
    """Affiche les résultats, statistiques et bouton d'export."""
    if df.empty:
        st.warning("Aucun fournisseur trouvé avec ces critères. Essayez des mots-clés différents.")
        return

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fournisseurs trouvés", len(df))
    c2.metric("Pays distincts", df["Pays"].nunique())
    avg_years = df["Années d'existence"].mean()
    c3.metric("Ancienneté moy.", f"{avg_years:.1f} ans")
    c4.metric("Zone", params["zone_label"].split(" ", 1)[1])

    st.divider()

    # Tableau interactif
    st.subheader("📊 Résultats")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Lien / Contact": st.column_config.LinkColumn("Lien / Contact"),
            "Années d'existence": st.column_config.NumberColumn(format="%d ans"),
        },
    )

    # Boutons d'export
    st.subheader("📥 Export")
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="⬇️ Télécharger en Excel (.xlsx)",
            data=to_excel_bytes(df),
            file_name=f"fournisseurs_{params['zone']}_{datetime.now():%Y%m%d_%H%M}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col2:
        csv_bytes = df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ Télécharger en CSV",
            data=csv_bytes,
            file_name=f"fournisseurs_{params['zone']}_{datetime.now():%Y%m%d_%H%M}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ======================================================================
# MAIN
# ======================================================================
def main() -> None:
    render_header()
    params = render_sidebar()

    if not params["launch"]:
        st.info(
            "👈 Saisissez un produit dans la barre latérale et lancez la recherche. "
            "Les résultats apparaîtront ici."
        )
        return

    if not params["product"]:
        st.error("⚠️ Veuillez saisir un produit avant de lancer la recherche.")
        return

    client = get_apify_client()
    if client is None:
        return

    # Récupération du token (même valeur, mais string pour le cache)
    token = st.secrets["APIFY_TOKEN"]

    # Lancement scraping
    with st.spinner(f"🔎 Recherche en cours sur {params['zone_label']}…"):
        try:
            if params["zone"] == "alibaba":
                items = search_alibaba(token, params["product"], params["max_results"])
                df = normalize_alibaba(items)
            else:
                items = search_europages(token, params["product"], params["max_results"])
                df = normalize_europages(items)
        except Exception as e:
            st.error(f"❌ Erreur lors de l'appel à Apify : {e}")
            return

    # Filtrage par ancienneté
    if not df.empty:
        df = df[df["Années d'existence"] >= params["min_years"]].reset_index(drop=True)
        df = add_import_note(df, params["zone"])

    render_results(df, params)


if __name__ == "__main__":
    main()
