"""Onboarding translations (pt / fr / de). English lives in onboarding.PILLARS and UI["en"]."""
import streamlit as st

# Pillar: (name, tagline, description, five starting levels) per language.
PILLAR_TEXT = {
    "pt": {
        "Adventure": ("Aventura", "Explora mais", "Novos lugares, experiências novas, pequenas aventuras.", [
            "Costumo ficar por sítios que conheço", "Experimento algo novo algumas vezes por ano",
            "Exploro um sítio novo todos os meses", "Procuro experiências novas quase todas as semanas",
            "Explorar já faz parte do meu dia a dia"]),
        "Finance": ("Finanças", "Ganha confiança com o dinheiro", "Pequenos hábitos de poupança e literacia financeira.", [
            "Estou a começar a perceber os meus gastos", "Registo algumas das minhas despesas",
            "Tenho um orçamento, mas custa-me ser consistente", "Faço orçamento e poupo regularmente",
            "Tenho objetivos claros e revejo as minhas finanças regularmente"]),
        "Fitness": ("Exercício", "Mexe-te com confiança", "Aproveita o movimento e cria uma rotina sustentável.", [
            "Faço muito pouco exercício intencional", "Mexo-me de vez em quando e quero começar com calma",
            "Sou ativo um ou dois dias por semana", "Treino regularmente na maioria das semanas",
            "Tenho uma rotina consistente e quero variedade"]),
        "Health": ("Saúde", "Sente-te melhor todos os dias", "Descanso, bem-estar diário e hábitos conscientes.", [
            "As minhas rotinas diárias são irregulares", "Tenho um hábito saudável que quero reforçar",
            "Mantenho algumas rotinas, mas perco muitas vezes a consistência",
            "As minhas rotinas de sono e bem-estar são quase sempre estáveis",
            "Tenho rotinas estáveis e quero aperfeiçoá-las"]),
        "Languages": ("Idiomas", "Descobre novas palavras", "Aprende, pratica e cria ligações através da língua.", [
            "Estou a começar pelas primeiras palavras", "Sei palavras básicas e frases simples",
            "Consigo ter conversas curtas do dia a dia", "Consigo falar à vontade sobre temas conhecidos",
            "Comunico com confiança e quero mais nuance"]),
        "Personal Growth": ("Desenvolvimento Pessoal", "Alimenta a tua curiosidade",
                            "Aprendizagem, reflexão e objetivos pessoais com significado.", [
            "Não sei bem por onde começar", "De vez em quando leio, aprendo ou reflito",
            "Reservo tempo para aprender cerca de uma vez por semana",
            "Aprendo regularmente e trabalho nos meus objetivos pessoais",
            "Tenho uma rotina de aprendizagem estável e procuro desafios maiores"]),
        "Social": ("Vida Social", "Sente-te mais ligado aos outros", "Fortalece amizades e conhece pessoas ao teu ritmo.", [
            "Prefiro interações pequenas e familiares", "Quero voltar a falar com pessoas que já conheço",
            "Sinto-me à vontade a dois, mas raramente tomo a iniciativa",
            "Faço planos muitas vezes e conheço pessoas novas", "Junto pessoas com confiança"]),
    },
    "fr": {
        "Adventure": ("Aventure", "Explore davantage", "De nouveaux lieux, des expériences inédites, de petites aventures.", [
            "Je reste généralement dans des lieux familiers", "J'essaie quelque chose de nouveau quelques fois par an",
            "J'explore un nouvel endroit chaque mois", "Je cherche de nouvelles expériences presque chaque semaine",
            "Explorer fait déjà partie de mon quotidien"]),
        "Finance": ("Finances", "Prends confiance avec l'argent",
                    "De petites habitudes d'épargne et une meilleure compréhension financière.", [
            "Je commence tout juste à comprendre mes dépenses", "Je note une partie de mes dépenses",
            "J'ai un budget mais j'ai du mal à m'y tenir", "Je fais un budget et j'épargne régulièrement",
            "J'ai des objectifs clairs et je fais régulièrement le point sur mes finances"]),
        "Fitness": ("Sport", "Bouge en confiance", "Prends plaisir à bouger et construis une routine durable.", [
            "Je bouge très peu de manière intentionnelle", "Je bouge de temps en temps et je veux commencer en douceur",
            "Je suis actif un ou deux jours par semaine", "Je fais du sport régulièrement la plupart des semaines",
            "J'ai une routine régulière et je cherche de la variété"]),
        "Health": ("Santé", "Te sentir mieux chaque jour", "Repos, bien-être au quotidien et habitudes attentives.", [
            "Mes routines quotidiennes sont irrégulières", "J'ai une bonne habitude sur laquelle je veux construire",
            "Je tiens quelques routines mais je perds souvent le rythme",
            "Mes routines de sommeil et de bien-être sont plutôt stables",
            "J'ai des routines stables et je veux les affiner"]),
        "Languages": ("Langues", "Découvre de nouveaux mots", "Apprends, pratique et crée des liens grâce aux langues.", [
            "Je commence par mes premiers mots", "Je connais des mots de base et des phrases simples",
            "Je peux tenir de courtes conversations du quotidien", "Je peux parler aisément de sujets familiers",
            "Je communique avec assurance et je veux plus de nuances"]),
        "Personal Growth": ("Développement personnel", "Nourris ta curiosité",
                            "Apprendre, réfléchir et se fixer des objectifs qui ont du sens.", [
            "Je ne sais pas trop par où commencer", "Je lis, j'apprends ou je réfléchis de temps en temps",
            "Je prends du temps pour apprendre environ une fois par semaine",
            "J'apprends régulièrement et j'avance sur mes objectifs personnels",
            "J'ai une routine d'apprentissage stable et je cherche des défis plus profonds"]),
        "Social": ("Vie sociale", "Te sentir plus entouré", "Renforce tes amitiés et rencontre des gens à ton rythme.", [
            "Je préfère de petites interactions familières", "Je veux renouer avec des gens que je connais déjà",
            "Je suis à l'aise en tête-à-tête mais je prends rarement l'initiative",
            "Je fais souvent des projets et je rencontre de nouvelles personnes",
            "Je rassemble les gens avec assurance"]),
    },
    "de": {
        "Adventure": ("Abenteuer", "Mehr entdecken", "Neue Orte, frische Erlebnisse, kleine Abenteuer.", [
            "Ich bleibe meist an vertrauten Orten", "Ich probiere ein paar Mal im Jahr etwas Neues aus",
            "Ich erkunde jeden Monat einen neuen Ort", "Ich suche fast jede Woche neue Erlebnisse",
            "Entdecken gehört schon zu meinem Alltag"]),
        "Finance": ("Finanzen", "Sicherer mit Geld werden", "Kleine Spargewohnheiten und Finanzwissen.", [
            "Ich fange gerade an, meine Ausgaben zu verstehen", "Ich notiere einen Teil meiner Ausgaben",
            "Ich habe ein Budget, halte es aber schwer durch", "Ich budgetiere und spare regelmäßig",
            "Ich habe klare Ziele und prüfe meine Finanzen regelmäßig"]),
        "Fitness": ("Fitness", "Selbstbewusst in Bewegung", "Freude an Bewegung und eine nachhaltige Routine.", [
            "Ich bewege mich kaum gezielt", "Ich bewege mich ab und zu und möchte sanft anfangen",
            "Ich bin ein bis zwei Tage pro Woche aktiv", "Ich trainiere in den meisten Wochen regelmäßig",
            "Ich habe eine feste Routine und möchte Abwechslung"]),
        "Health": ("Gesundheit", "Jeden Tag besser fühlen", "Erholung, Wohlbefinden im Alltag und achtsame Gewohnheiten.", [
            "Meine Tagesroutinen sind unregelmäßig", "Ich habe eine gesunde Gewohnheit, auf der ich aufbauen will",
            "Ich halte einige Routinen, verliere aber oft den Faden",
            "Meine Schlaf- und Wohlfühlroutinen sind meist stabil",
            "Ich habe stabile Routinen und möchte sie verfeinern"]),
        "Languages": ("Sprachen", "Neue Wörter entdecken", "Lernen, üben und durch Sprache verbinden.", [
            "Ich fange mit meinen ersten Wörtern an", "Ich kenne Grundwörter und einfache Sätze",
            "Ich komme in kurzen Alltagsgesprächen zurecht", "Ich kann mich über vertraute Themen gut unterhalten",
            "Ich kommuniziere sicher und möchte mehr Feinheiten"]),
        "Personal Growth": ("Persönliche Entwicklung", "Neugier wachsen lassen",
                            "Lernen, Reflexion und bedeutsame persönliche Ziele.", [
            "Ich weiß nicht genau, wo ich anfangen soll", "Ich lese, lerne oder reflektiere ab und zu",
            "Ich nehme mir etwa einmal pro Woche Zeit zum Lernen",
            "Ich lerne regelmäßig und arbeite an persönlichen Zielen",
            "Ich habe eine feste Lernroutine und suche tiefere Herausforderungen"]),
        "Social": ("Soziales", "Mehr Verbundenheit spüren",
                   "Freundschaften stärken und Menschen in deinem Tempo kennenlernen.", [
            "Ich bevorzuge kleine, vertraute Begegnungen", "Ich möchte wieder Kontakt zu Bekannten aufnehmen",
            "Zu zweit fühle ich mich wohl, ergreife aber selten die Initiative",
            "Ich plane oft etwas und lerne neue Leute kennen", "Ich bringe selbstbewusst Menschen zusammen"]),
    },
}

UI = {
    "en": {
        "eyebrow": "Life Quest · Your fresh start", "intro": "A few small questions. A journey that feels like you.",
        "step": "Step {a} of {b}", "back": "← Back", "continue": "Continue →",
        "name_title": "First, what should we call you?", "name_text": "Your name, your nickname, whatever feels like you.",
        "name_label": "Your nickname", "name_placeholder": "e.g. Hajna", "name_button": "Let's begin →",
        "name_error": "Add a nickname so we know what to call you.",
        "hi_tag": "A small step. A new chapter.", "hi_title": "Hi, {name}!",
        "hi_body": "You don't need to change everything today. Let's start with one small quest that feels right for you.",
        "hi_button": "Make it mine →",
        "pillars_title": "Where would you like to grow?", "pillars_limit": "Choose up to {n} pillars. This is your journey.",
        "pillars_any": "Choose as many pillars as you like. This is your journey.",
        "pillars_button": "Find my starting point →",
        "level_title": "What feels most like you today?", "level_text": "No right answers. We'll start at your pace, not somebody else's.",
        "level_label": "Your starting point",
        "shown_title": "How many quests should we show?",
        "shown_text": "We always keep five quests ready for each pillar. Pick how many you want to see at once; a new one appears whenever you finish one. You can change this for each pillar in Settings.",
        "shown_label": "Quests shown per pillar",
        "shown_1": "Just one · keep it simple", "shown_2": "Two at a time", "shown_3": "Three · a light list",
        "shown_5": "All five · show me everything",
        "final_title": "Your next chapter is ready to begin ✨",
        "final_text": "Small steps, chosen around your interests and your starting point.",
        "final_level": "Starting point {level}/5", "final_shown": "Quests shown", "final_per": "{n} per pillar",
        "city_label": "Your city (optional)", "city_placeholder": "Start typing your city, for example Lisbon",
        "city_none": "No matching city found. Check the spelling.",
        "city_down": "City search is unavailable right now. You can skip this and add your city later in Settings.",
        "city_note": "City search uses OpenStreetMap (Photon): only what you type is sent. Your city and country help personalise quests and are sent to the AI provider with your preferences.",
        "ai_note": "When AI quests are enabled, your chosen pillars, starting levels and quest feedback are shared with Requesty and its free model provider to personalise your quests. Your name and email are not sent.",
        "prepare": "Prepare my quests →", "preparing": "Preparing your personalised quests…",
        "saving": "Saving your interests and starting points…", "ready": "Your journey is ready!",
        "failed": "We couldn't finish preparing your journey. Please try again.",
    },
    "pt": {
        "eyebrow": "Life Quest · Um novo começo", "intro": "Algumas perguntas rápidas. Uma jornada à tua medida.",
        "step": "Passo {a} de {b}", "back": "← Voltar", "continue": "Continuar →",
        "name_title": "Primeiro, como te devemos chamar?", "name_text": "O teu nome, a tua alcunha, o que te fizer sentido.",
        "name_label": "A tua alcunha", "name_placeholder": "ex.: Hajna", "name_button": "Vamos começar →",
        "name_error": "Escreve uma alcunha para sabermos como te chamar.",
        "hi_tag": "Um pequeno passo. Um novo capítulo.", "hi_title": "Olá, {name}!",
        "hi_body": "Não precisas de mudar tudo hoje. Vamos começar com uma pequena missão que faça sentido para ti.",
        "hi_button": "Quero começar →",
        "pillars_title": "Em que áreas queres crescer?", "pillars_limit": "Escolhe até {n} áreas. A jornada é tua.",
        "pillars_any": "Escolhe as áreas que quiseres. A jornada é tua.",
        "pillars_button": "Encontrar o meu ponto de partida →",
        "level_title": "O que mais se parece contigo hoje?", "level_text": "Não há respostas certas. Começamos ao teu ritmo, não ao de outra pessoa.",
        "level_label": "O teu ponto de partida",
        "shown_title": "Quantas missões devemos mostrar?",
        "shown_text": "Temos sempre cinco missões prontas para cada área. Escolhe quantas queres ver de cada vez; aparece uma nova sempre que concluis uma. Podes mudar isto para cada área nas Definições.",
        "shown_label": "Missões mostradas por área",
        "shown_1": "Só uma · simples", "shown_2": "Duas de cada vez", "shown_3": "Três · uma lista leve",
        "shown_5": "Todas as cinco · mostra-me tudo",
        "final_title": "O teu próximo capítulo está pronto ✨",
        "final_text": "Pequenos passos, escolhidos à volta dos teus interesses e do teu ponto de partida.",
        "final_level": "Ponto de partida {level}/5", "final_shown": "Missões mostradas", "final_per": "{n} por área",
        "city_label": "A tua cidade (opcional)", "city_placeholder": "Começa a escrever a tua cidade, por exemplo Lisboa",
        "city_none": "Nenhuma cidade encontrada. Verifica a ortografia.",
        "city_down": "A pesquisa de cidades não está disponível agora. Podes saltar este passo e adicionar a cidade mais tarde nas Definições.",
        "city_note": "A pesquisa usa o OpenStreetMap (Photon): só é enviado o que escreves. A tua cidade e país ajudam a personalizar missões e são enviados ao fornecedor de IA com as tuas preferências.",
        "ai_note": "Quando as missões com IA estão ativas, as áreas escolhidas, os níveis iniciais e o teu feedback são partilhados com o Requesty e o seu fornecedor de modelo gratuito para personalizar as missões. O teu nome e email não são enviados.",
        "prepare": "Preparar as minhas missões →", "preparing": "A preparar as tuas missões personalizadas…",
        "saving": "A guardar os teus interesses e pontos de partida…", "ready": "A tua jornada está pronta!",
        "failed": "Não foi possível preparar a tua jornada. Tenta novamente.",
    },
    "fr": {
        "eyebrow": "Life Quest · Un nouveau départ", "intro": "Quelques petites questions. Un parcours qui te ressemble.",
        "step": "Étape {a} sur {b}", "back": "← Retour", "continue": "Continuer →",
        "name_title": "D'abord, comment devons-nous t'appeler ?", "name_text": "Ton prénom, ton surnom, ce qui te ressemble.",
        "name_label": "Ton surnom", "name_placeholder": "ex. : Hajna", "name_button": "C'est parti →",
        "name_error": "Ajoute un surnom pour que nous sachions comment t'appeler.",
        "hi_tag": "Un petit pas. Un nouveau chapitre.", "hi_title": "Salut, {name} !",
        "hi_body": "Pas besoin de tout changer aujourd'hui. Commençons par une petite quête qui te convient.",
        "hi_button": "C'est pour moi →",
        "pillars_title": "Dans quels domaines veux-tu progresser ?", "pillars_limit": "Choisis jusqu'à {n} domaines. C'est ton parcours.",
        "pillars_any": "Choisis autant de domaines que tu veux. C'est ton parcours.",
        "pillars_button": "Trouver mon point de départ →",
        "level_title": "Qu'est-ce qui te ressemble le plus aujourd'hui ?", "level_text": "Pas de bonne réponse. On commence à ton rythme, pas à celui des autres.",
        "level_label": "Ton point de départ",
        "shown_title": "Combien de quêtes afficher ?",
        "shown_text": "Nous gardons toujours cinq quêtes prêtes pour chaque domaine. Choisis combien tu veux en voir à la fois ; une nouvelle apparaît à chaque quête terminée. Tu peux changer cela pour chaque domaine dans les Paramètres.",
        "shown_label": "Quêtes affichées par domaine",
        "shown_1": "Une seule · tout simple", "shown_2": "Deux à la fois", "shown_3": "Trois · une liste légère",
        "shown_5": "Les cinq · montre-moi tout",
        "final_title": "Ton prochain chapitre est prêt ✨",
        "final_text": "De petits pas, choisis selon tes centres d'intérêt et ton point de départ.",
        "final_level": "Point de départ {level}/5", "final_shown": "Quêtes affichées", "final_per": "{n} par domaine",
        "city_label": "Ta ville (facultatif)", "city_placeholder": "Commence à écrire ta ville, par exemple Lisbonne",
        "city_none": "Aucune ville trouvée. Vérifie l'orthographe.",
        "city_down": "La recherche de villes est indisponible pour le moment. Tu peux passer cette étape et ajouter ta ville plus tard dans les Paramètres.",
        "city_note": "La recherche utilise OpenStreetMap (Photon) : seul ce que tu tapes est envoyé. Ta ville et ton pays personnalisent les quêtes et sont envoyés au fournisseur d’IA avec tes préférences.",
        "ai_note": "Quand les quêtes IA sont activées, tes domaines, niveaux de départ et retours sont partagés avec Requesty et son fournisseur de modèle gratuit pour personnaliser tes quêtes. Ton nom et ton e-mail ne sont pas envoyés.",
        "prepare": "Préparer mes quêtes →", "preparing": "Préparation de tes quêtes personnalisées…",
        "saving": "Enregistrement de tes centres d'intérêt et points de départ…", "ready": "Ton parcours est prêt !",
        "failed": "Impossible de terminer la préparation. Réessaie.",
    },
    "de": {
        "eyebrow": "Life Quest · Dein Neustart", "intro": "Ein paar kurze Fragen. Ein Weg, der zu dir passt.",
        "step": "Schritt {a} von {b}", "back": "← Zurück", "continue": "Weiter →",
        "name_title": "Wie sollen wir dich nennen?", "name_text": "Dein Name, dein Spitzname, was zu dir passt.",
        "name_label": "Dein Spitzname", "name_placeholder": "z. B. Hajna", "name_button": "Los geht's →",
        "name_error": "Gib einen Spitznamen ein, damit wir wissen, wie wir dich nennen sollen.",
        "hi_tag": "Ein kleiner Schritt. Ein neues Kapitel.", "hi_title": "Hallo, {name}!",
        "hi_body": "Du musst heute nicht alles ändern. Fangen wir mit einer kleinen Quest an, die zu dir passt.",
        "hi_button": "Das passt zu mir →",
        "pillars_title": "Wo möchtest du wachsen?", "pillars_limit": "Wähle bis zu {n} Bereiche. Es ist dein Weg.",
        "pillars_any": "Wähle so viele Bereiche, wie du möchtest. Es ist dein Weg.",
        "pillars_button": "Meinen Startpunkt finden →",
        "level_title": "Was passt heute am besten zu dir?", "level_text": "Es gibt keine falschen Antworten. Wir starten in deinem Tempo, nicht in dem von anderen.",
        "level_label": "Dein Startpunkt",
        "shown_title": "Wie viele Quests sollen wir zeigen?",
        "shown_text": "Für jeden Bereich halten wir immer fünf Quests bereit. Wähle, wie viele du auf einmal sehen möchtest; nach jedem Abschluss erscheint eine neue. Du kannst das für jeden Bereich in den Einstellungen ändern.",
        "shown_label": "Angezeigte Quests pro Bereich",
        "shown_1": "Nur eine · ganz einfach", "shown_2": "Zwei auf einmal", "shown_3": "Drei · eine kurze Liste",
        "shown_5": "Alle fünf · zeig mir alles",
        "final_title": "Dein nächstes Kapitel kann beginnen ✨",
        "final_text": "Kleine Schritte, passend zu deinen Interessen und deinem Startpunkt.",
        "final_level": "Startpunkt {level}/5", "final_shown": "Angezeigte Quests", "final_per": "{n} pro Bereich",
        "city_label": "Deine Stadt (optional)", "city_placeholder": "Gib deine Stadt ein, zum Beispiel Lissabon",
        "city_none": "Keine passende Stadt gefunden. Prüfe die Schreibweise.",
        "city_down": "Die Städtesuche ist gerade nicht verfügbar. Du kannst das überspringen und deine Stadt später in den Einstellungen hinzufügen.",
        "city_note": "Die Suche nutzt OpenStreetMap (Photon): Nur deine Eingabe wird gesendet. Deine Stadt und dein Land personalisieren Quests und werden mit deinen Vorlieben an den KI-Anbieter gesendet.",
        "ai_note": "Wenn KI-Quests aktiv sind, werden deine Bereiche, Startlevel und dein Feedback mit Requesty und dessen kostenlosem Modellanbieter geteilt, um deine Quests zu personalisieren. Dein Name und deine E-Mail werden nicht gesendet.",
        "prepare": "Meine Quests vorbereiten →", "preparing": "Deine persönlichen Quests werden vorbereitet…",
        "saving": "Deine Interessen und Startpunkte werden gespeichert…", "ready": "Dein Weg ist bereit!",
        "failed": "Wir konnten die Vorbereitung nicht abschließen. Bitte versuche es erneut.",
    },
}


def lang() -> str:
    value = st.session_state.get("language", "en")
    return value if value in UI else "en"


def ob(key: str, **values) -> str:
    """Onboarding text in the current language (falls back to English)."""
    text = UI[lang()].get(key) or UI["en"][key]
    return text.format(**values) if values else text


def pillar_text(pillar: str, english: tuple) -> tuple:
    """(name, tagline, description, levels) in the current language; `english` is the PILLARS entry."""
    translated = PILLAR_TEXT.get(lang(), {}).get(pillar)
    if translated:
        return translated
    _, tagline, description, levels = english
    return pillar, tagline, description, levels
