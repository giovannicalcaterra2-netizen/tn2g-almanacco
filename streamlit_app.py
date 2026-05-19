import uuid
from datetime import date, datetime, time

import pandas as pd
import requests
import streamlit as st


EXPECTED_COLUMNS = [
    "id",
    "pubblica",
    "tipo",
    "titolo",
    "nome",
    "data",
    "ora_inizio",
    "ora_fine",
    "categoria",
    "luogo",
    "segno",
    "oroscopo",
    "descrizione",
    "link",
    "ricorrente",
    "calendar_event_id",
]

CATEGORIE = [
    "compleanno",
    "evento",
    "aperitivo",
    "outdoor",
    "nerd",
    "cinema",
    "salotto",
    "musica",
    "sport",
]

TIPI = ["compleanno", "evento"]

SEGNI = [
    "Ariete",
    "Toro",
    "Gemelli",
    "Cancro",
    "Leone",
    "Vergine",
    "Bilancia",
    "Scorpione",
    "Sagittario",
    "Capricorno",
    "Acquario",
    "Pesci",
]


st.set_page_config(
    page_title="TN2G Almanacco Admin",
    page_icon="🔱",
    layout="wide",
)


def clean(value):
    return str(value or "").strip()


def zodiac_sign(day: int, month: int) -> str:
    if (month == 3 and day >= 21) or (month == 4 and day <= 19):
        return "Ariete"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return "Toro"
    if (month == 5 and day >= 21) or (month == 6 and day <= 20):
        return "Gemelli"
    if (month == 6 and day >= 21) or (month == 7 and day <= 22):
        return "Cancro"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "Leone"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "Vergine"
    if (month == 9 and day >= 23) or (month == 10 and day <= 22):
        return "Bilancia"
    if (month == 10 and day >= 23) or (month == 11 and day <= 21):
        return "Scorpione"
    if (month == 11 and day >= 22) or (month == 12 and day <= 21):
        return "Sagittario"
    if (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return "Capricorno"
    if (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return "Acquario"
    return "Pesci"


def make_id(tipo: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:6]
    return f"{tipo}_{stamp}_{short}"


def format_time(value):
    if isinstance(value, time):
        return value.strftime("%H:%M")
    return ""


@st.cache_data(ttl=30)
def load_archive(csv_url: str) -> pd.DataFrame:
    if not csv_url:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    try:
        df = pd.read_csv(csv_url)
    except Exception:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    return df[EXPECTED_COLUMNS]


def login_gate() -> bool:
    password = st.secrets.get("ADMIN_PASSWORD", "")

    if not password:
        return True

    if st.session_state.get("authenticated"):
        return True

    st.title("🔱 TN2G Almanacco Admin")
    entered = st.text_input("Password admin", type="password")

    if st.button("Entra"):
        if entered == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Password sbagliata.")

    return False


def post_to_apps_script(record: dict) -> dict:
    webhook_url = st.secrets.get("APPS_SCRIPT_URL", "")
    token = st.secrets.get("APPS_SCRIPT_TOKEN", "")

    if not webhook_url:
        return {
            "ok": False,
            "error": "Manca APPS_SCRIPT_URL nei secrets Streamlit.",
        }

    if not token:
        return {
            "ok": False,
            "error": "Manca APPS_SCRIPT_TOKEN nei secrets Streamlit.",
        }

    payload = dict(record)
    payload["token"] = token

    response = requests.post(webhook_url, json=payload, timeout=20)

    try:
        return response.json()
    except Exception:
        return {
            "ok": False,
            "error": response.text,
        }


def find_duplicates(df: pd.DataFrame, record: dict) -> pd.DataFrame:
    if df.empty:
        return df

    same_type = df["tipo"].astype(str).str.lower().str.strip() == record["tipo"].lower()
    same_date = df["data"].astype(str).str.strip() == record["data"]

    if record["tipo"] == "compleanno":
        same_name = df["nome"].astype(str).str.lower().str.strip() == record["nome"].lower()
        return df[same_type & same_date & same_name]

    same_title = df["titolo"].astype(str).str.lower().str.strip() == record["titolo"].lower()
    return df[same_type & same_date & same_title]


if not login_gate():
    st.stop()


st.title("🔱 TN2G Almanacco Admin")
st.caption("Tool semplice per caricare compleanni ed eventi senza toccare direttamente il Google Sheet.")

CSV_URL = st.secrets.get("CSV_URL", "")
df = load_archive(CSV_URL)

st.sidebar.header("📊 Riepilogo")
st.sidebar.metric("Record totali", len(df))

if not df.empty:
    published = df["pubblica"].astype(str).str.lower().isin(["si", "sì", "yes"]).sum()
    birthdays = (df["tipo"].astype(str).str.lower() == "compleanno").sum()
    events = (df["tipo"].astype(str).str.lower() == "evento").sum()

    st.sidebar.metric("Pubblicati", int(published))
    st.sidebar.metric("Compleanni", int(birthdays))
    st.sidebar.metric("Eventi", int(events))


tab_add, tab_archive, tab_setup = st.tabs(
    ["➕ Aggiungi", "📚 Archivio", "⚙️ Setup"]
)


with tab_add:
    st.subheader("Nuovo caricamento")

    with st.form("new_record_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            tipo = st.selectbox("Tipo", TIPI)

        with col2:
            default_category = "compleanno" if tipo == "compleanno" else "evento"
            categoria = st.selectbox(
                "Categoria",
                CATEGORIE,
                index=CATEGORIE.index(default_category),
            )

        with col3:
            pubblica = st.selectbox("Stato", ["si", "bozza"])

        data_evento = st.date_input(
            "Data",
            value=date.today(),
            format="YYYY-MM-DD",
        )

        nome = ""
        titolo = ""
        segno = ""
        oroscopo = ""
        descrizione = ""
        link = ""
        luogo = ""
        ora_inizio = ""
        ora_fine = ""
        ricorrente = "no"

        if tipo == "compleanno":
            c1, c2 = st.columns(2)

            with c1:
                nome = st.text_input("Nome persona", placeholder="Es. Leti")

            with c2:
                segno_auto = zodiac_sign(data_evento.day, data_evento.month)
                segno = st.selectbox(
                    "Segno zodiacale",
                    SEGNI,
                    index=SEGNI.index(segno_auto),
                )

            titolo = f"Compleanno di {nome} 🎂" if nome else ""
            ricorrente = "annuale"

            oroscopo = st.text_area(
                "Oroscopo / nota TN2G",
                placeholder="Es. Vietato ghostare gli auguri.",
                height=90,
            )

            descrizione = st.text_area(
                "Descrizione extra",
                placeholder="Opzionale.",
                height=80,
            )

        else:
            titolo = st.text_input(
                "Titolo evento",
                placeholder="Es. Aperitivo TN2G",
            )

            all_day = st.checkbox("Evento tutto il giorno", value=False)

            if not all_day:
                c1, c2 = st.columns(2)

                with c1:
                    ora_inizio = st.time_input(
                        "Ora inizio",
                        value=time(20, 30),
                        step=900,
                    )

                with c2:
                    ora_fine = st.time_input(
                        "Ora fine",
                        value=time(23, 30),
                        step=900,
                    )

            luogo = st.text_input("Luogo", placeholder="Es. Bar Verdi")

            descrizione = st.text_area(
                "Descrizione",
                placeholder="Info utili per i membri.",
                height=110,
            )

            link = st.text_input("Link opzionale", placeholder="https://...")

            ricorrente = st.selectbox("Ricorrenza", ["no", "annuale"])

        submitted = st.form_submit_button("Controlla riepilogo")

    if submitted:
        errors = []

        if tipo == "compleanno" and not clean(nome):
            errors.append("Inserisci il nome della persona.")

        if tipo == "evento" and not clean(titolo):
            errors.append("Inserisci il titolo dell'evento.")

        record = {
            "id": make_id(tipo),
            "pubblica": pubblica,
            "tipo": tipo,
            "titolo": clean(titolo),
            "nome": clean(nome),
            "data": data_evento.isoformat(),
            "ora_inizio": format_time(ora_inizio),
            "ora_fine": format_time(ora_fine),
            "categoria": categoria,
            "luogo": clean(luogo),
            "segno": clean(segno),
            "oroscopo": clean(oroscopo),
            "descrizione": clean(descrizione),
            "link": clean(link),
            "ricorrente": ricorrente,
            "calendar_event_id": "",
        }

        if errors:
            for error in errors:
                st.error(error)
        else:
            st.session_state["pending_record"] = record

    pending = st.session_state.get("pending_record")

    if pending:
        st.divider()
        st.subheader("Riepilogo prima del salvataggio")

        st.dataframe(
            pd.DataFrame([pending]),
            use_container_width=True,
            hide_index=True,
        )

        duplicates = find_duplicates(df, pending)

        if not duplicates.empty:
            st.warning("Possibile duplicato trovato. Controlla prima di salvare.")
            st.dataframe(
                duplicates,
                use_container_width=True,
                hide_index=True,
            )

        c1, c2 = st.columns(2)

        with c1:
            if st.button("✅ Salva nel Google Sheet", type="primary"):
                result = post_to_apps_script(pending)

                if result.get("ok"):
                    st.success("Elemento salvato correttamente nel Google Sheet.")
                    del st.session_state["pending_record"]
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(result.get("error", "Errore sconosciuto."))

        with c2:
            if st.button("Annulla"):
                del st.session_state["pending_record"]
                st.rerun()


with tab_archive:
    st.subheader("Archivio già caricato")

    if df.empty:
        st.info("Nessun elemento caricato oppure CSV non configurato.")
    else:
        c1, c2, c3 = st.columns(3)

        with c1:
            tipo_filter = st.selectbox("Tipo", ["tutti"] + TIPI)

        with c2:
            categoria_filter = st.selectbox("Categoria", ["tutte"] + CATEGORIE)

        with c3:
            stato_filter = st.selectbox("Stato", ["tutti", "si", "bozza"])

        filtered = df.copy()

        if tipo_filter != "tutti":
            filtered = filtered[
                filtered["tipo"].astype(str).str.lower() == tipo_filter
            ]

        if categoria_filter != "tutte":
            filtered = filtered[
                filtered["categoria"].astype(str).str.lower() == categoria_filter
            ]

        if stato_filter != "tutti":
            filtered = filtered[
                filtered["pubblica"].astype(str).str.lower() == stato_filter
            ]

        filtered = filtered.sort_values("data", ascending=True)

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Scarica CSV filtrato",
            filtered.to_csv(index=False).encode("utf-8"),
            "tn2g_almanacco_export.csv",
            "text/csv",
        )


with tab_setup:
    st.subheader("Setup Streamlit secrets")

    st.markdown(
        """
        Su Streamlit Cloud vai su:

        `Settings → Secrets`

        e inserisci queste variabili:

        ```toml
        ADMIN_PASSWORD = "password-per-le-ragazze"
        APPS_SCRIPT_URL = "url-della-web-app-google-apps-script"
        APPS_SCRIPT_TOKEN = "stesso-token-scritto-in-apps-script"
        CSV_URL = "url-csv-pubblico-del-google-sheet"
        ```
        """
    )
