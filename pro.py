"""Life Quest Pro: a demo subscription (no real payment; this is a student project).

Pro state lives in the user's auth metadata under `lifequest_pro`:
    {"active": true, "plan": "monthly" | "yearly", "since": "2026-11-18"}
Pro unlocks more than FREE_PILLAR_LIMIT pillars and (once a paid AI is connected)
quests personalised to the country of the user's city. The "coming soon" list shows
features that would need paid APIs (places/events, weather, health sync, calendar,
speech, AI reports); none of them are built.
"""
from datetime import date
import html

import streamlit as st

FREE_PILLAR_LIMIT = 3
PLANS = {
    "monthly": {"price": "€3.99", "en": "per month", "pt": "por mês", "fr": "par mois", "de": "pro Monat"},
    "yearly": {"price": "€29.99", "en": "per year · save 37%", "pt": "por ano · poupa 37%",
               "fr": "par an · 37 % d'économie", "de": "pro Jahr · 37 % sparen"},
}

TEXT = {
    "en": {
        "soon_title": 'Coming soon with Pro', "soon": ['📍 Quests at real places and events near you', '🌦️ Weather-aware quests, with indoor ideas on rainy days', '🏃 Steps and workouts synced from Apple Health or Google Fit complete fitness quests automatically'],
        "eyebrow": "Life Quest Pro", "title": "Go further with Pro",
        "f_country": "Quests personalised to your country: local language, currency and seasons",
        "f_pillars": "All 7 pillars (free plan: up to 3)",
        "f_badge": "Custom avatar styles on your profile and Home",
        "plan": "Plan", "monthly": "Monthly", "yearly": "Yearly",
        "subscribe": "Subscribe to Pro", "demo": "Demo only: no payment is taken and no card is needed.",
        "confirm_title": "Confirm your Pro subscription", "confirm": "Start Pro", "cancel_dialog": "Not now",
        "active": "You're on Pro", "since": "Since", "country_on": "Country quests use",
        "country_missing": "Add your city in your profile so Pro can personalise quests to your country.",
        "country_note": "Country quests switch on when the paid AI is connected.",
        "cancel": "Cancel Pro", "welcome": "Welcome to Pro! 🎉", "cancelled": "Pro cancelled. You're back on the free plan.",
        "error": "We couldn't update your plan. Please try again.",
    },
    "pt": {
        "soon_title": 'Brevemente no Pro', "soon": ['📍 Missões em locais e eventos reais perto de ti', '🌦️ Missões que se adaptam ao tempo, com ideias para dias de chuva', '🏃 Passos e treinos do Apple Health ou Google Fit concluem missões de exercício automaticamente'],
        "eyebrow": "Life Quest Pro", "title": "Vai mais longe com o Pro",
        "f_country": "Missões personalizadas para o teu país: língua, moeda e estações do ano",
        "f_pillars": "As 7 áreas (plano gratuito: até 3)",
        "f_badge": "Estilos de avatar personalizados no perfil e no início",
        "plan": "Plano", "monthly": "Mensal", "yearly": "Anual",
        "subscribe": "Subscrever o Pro", "demo": "Apenas demonstração: não é cobrado nenhum pagamento nem é preciso cartão.",
        "confirm_title": "Confirma a tua subscrição Pro", "confirm": "Ativar Pro", "cancel_dialog": "Agora não",
        "active": "Estás no Pro", "since": "Desde", "country_on": "As missões do país usam",
        "country_missing": "Adiciona a tua cidade no perfil para o Pro personalizar as missões ao teu país.",
        "country_note": "As missões do país ficam ativas quando a IA paga estiver ligada.",
        "cancel": "Cancelar Pro", "welcome": "Bem-vindo ao Pro! 🎉", "cancelled": "Pro cancelado. Voltaste ao plano gratuito.",
        "error": "Não foi possível atualizar o teu plano. Tenta novamente.",
    },
    "fr": {
        "soon_title": 'Bientôt avec Pro', "soon": ['📍 Des quêtes dans de vrais lieux et événements près de chez toi', '🌦️ Des quêtes adaptées à la météo, avec des idées pour les jours de pluie', "🏃 Les pas et entraînements d'Apple Santé ou Google Fit valident automatiquement les quêtes sportives"],
        "eyebrow": "Life Quest Pro", "title": "Va plus loin avec Pro",
        "f_country": "Des quêtes adaptées à ton pays : langue, monnaie et saisons",
        "f_pillars": "Les 7 domaines (offre gratuite : 3 maximum)",
        "f_badge": "Des styles d'avatar personnalisés sur ton profil et l'accueil",
        "plan": "Formule", "monthly": "Mensuelle", "yearly": "Annuelle",
        "subscribe": "S'abonner à Pro", "demo": "Démo uniquement : aucun paiement, aucune carte requise.",
        "confirm_title": "Confirme ton abonnement Pro", "confirm": "Activer Pro", "cancel_dialog": "Pas maintenant",
        "active": "Tu es Pro", "since": "Depuis le", "country_on": "Les quêtes du pays utilisent",
        "country_missing": "Ajoute ta ville dans ton profil pour que Pro adapte les quêtes à ton pays.",
        "country_note": "Les quêtes du pays s'activent quand l'IA payante est connectée.",
        "cancel": "Résilier Pro", "welcome": "Bienvenue dans Pro ! 🎉", "cancelled": "Pro résilié. Tu es revenu à l'offre gratuite.",
        "error": "Impossible de mettre à jour ton offre. Réessaie.",
    },
    "de": {
        "soon_title": 'Bald mit Pro', "soon": ['📍 Quests an echten Orten und Events in deiner Nähe', '🌦️ Wetterabhängige Quests mit Ideen für Regentage', '🏃 Schritte und Workouts aus Apple Health oder Google Fit schließen Fitness-Quests automatisch ab'],
        "eyebrow": "Life Quest Pro", "title": "Mehr erreichen mit Pro",
        "f_country": "Quests passend zu deinem Land: Sprache, Währung und Jahreszeiten",
        "f_pillars": "Alle 7 Bereiche (kostenlos: bis zu 3)",
        "f_badge": "Eigene Avatar-Stile in deinem Profil und auf der Startseite",
        "plan": "Tarif", "monthly": "Monatlich", "yearly": "Jährlich",
        "subscribe": "Pro abonnieren", "demo": "Nur eine Demo: Es wird nichts abgebucht und keine Karte benötigt.",
        "confirm_title": "Pro-Abo bestätigen", "confirm": "Pro starten", "cancel_dialog": "Jetzt nicht",
        "active": "Du hast Pro", "since": "Seit", "country_on": "Länder-Quests nutzen",
        "country_missing": "Füge deine Stadt im Profil hinzu, damit Pro Quests an dein Land anpassen kann.",
        "country_note": "Länder-Quests werden aktiv, sobald die kostenpflichtige KI verbunden ist.",
        "cancel": "Pro kündigen", "welcome": "Willkommen bei Pro! 🎉", "cancelled": "Pro gekündigt. Du bist wieder im kostenlosen Tarif.",
        "error": "Dein Tarif konnte nicht aktualisiert werden. Bitte versuche es erneut.",
    },
}


def _t(lang: str) -> dict:
    return TEXT.get(lang, TEXT["en"])


def pro_state() -> dict:
    user = st.session_state.get("user") or {}
    return (user.get("user_metadata") or {}).get("lifequest_pro") or {}


def is_pro() -> bool:
    return bool(pro_state().get("active"))


def pillar_limit(current: int = 0) -> int:
    """Max pillars this user may have. Free accounts that already had more keep them."""
    return 7 if is_pro() else max(FREE_PILLAR_LIMIT, current)


def country_of(location: str | None) -> str:
    """'Lisbon, Portugal' -> 'Portugal' (the country is the last part of the saved city label)."""
    return (location or "").split(",")[-1].strip()


def save_user_data(api, data: dict) -> str | None:
    """Merge `data` into the user's auth metadata. Returns an error message or None."""
    user, error = api("PUT", "/auth/v1/user", {"data": data}, st.session_state.access_token)
    if error:
        return error
    if isinstance(user, dict) and user.get("id"):
        st.session_state.user = user
    else:
        st.session_state.user.setdefault("user_metadata", {}).update(data)
    return None


def render_pro_card(api, lang: str) -> None:
    """Settings card: Pro offer (free users) or Pro status (subscribers)."""
    t = _t(lang)
    if st.session_state.get("pro_toast"):
        st.toast(st.session_state.pop("pro_toast"), icon="✨")
    if is_pro():
        state = pro_state()
        plan = PLANS.get(state.get("plan"), PLANS["monthly"])
        country = country_of(st.session_state.profile.get("location"))
        st.markdown(
            f'<div class="lq-pro on"><span class="lq-pro-badge">PRO</span><h3>{html.escape(t["active"])}</h3>'
            f'<p>{html.escape(plan["price"])} {html.escape(plan.get(lang, plan["en"]))} · '
            f'{html.escape(t["since"])} {html.escape(str(state.get("since", "")))}</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="lq-pro-soon">{_soon_html(t)}</div>', unsafe_allow_html=True)
        if country:
            st.write(f'🌍 {t["country_on"]} **{country}**')
            st.caption(t["country_note"])
        else:
            st.info(t["country_missing"])
        if st.button(t["cancel"], key="pro_cancel", width="stretch"):
            error = save_user_data(api, {"lifequest_pro": {"active": False}})
            if error:
                st.error(t["error"])
            else:
                st.session_state.pro_toast = t["cancelled"]
                st.rerun()
        return

    features = "".join(f"<li>{html.escape(t[k])}</li>" for k in ("f_country", "f_pillars", "f_badge"))
    st.markdown(
        f'<div class="lq-pro"><span class="lq-pro-badge">PRO</span><h3>{html.escape(t["title"])}</h3>'
        f'<ul>{features}</ul>{_soon_html(t)}</div>',
        unsafe_allow_html=True,
    )
    plan = st.segmented_control(
        t["plan"], list(PLANS), default="yearly", key="pro_plan",
        format_func=lambda p: f'{t[p]} · {PLANS[p]["price"]}',
    ) or "yearly"
    st.caption(f'{PLANS[plan]["price"]} {PLANS[plan].get(lang, PLANS[plan]["en"])}')
    if st.button(t["subscribe"], type="primary", key="pro_subscribe", width="stretch"):
        _confirm_dialog(api, lang, plan)


def _soon_html(t: dict) -> str:
    """Features that need paid services (places, weather, health, calendar, speech, AI reports)."""
    items = "".join(f"<li>{html.escape(x)}</li>" for x in t["soon"])
    return f'<div class="soon"><span>{html.escape(t["soon_title"])}</span><ul>{items}</ul></div>'


def _confirm_dialog(api, lang: str, plan: str) -> None:
    t = _t(lang)

    @st.dialog(t["confirm_title"])
    def confirm():
        price = PLANS[plan]
        st.markdown(f'### {price["price"]} <small>{html.escape(price.get(lang, price["en"]))}</small>',
                    unsafe_allow_html=True)
        left, right = st.columns(2)
        if left.button(t["cancel_dialog"], width="stretch"):
            st.rerun()
        if right.button(t["confirm"], type="primary", width="stretch"):
            error = save_user_data(api, {"lifequest_pro": {"active": True, "plan": plan,
                                                           "since": date.today().isoformat()}})
            if error:
                st.error(t["error"])
            else:
                st.session_state.pro_toast = t["welcome"]
                st.rerun()

    confirm()
