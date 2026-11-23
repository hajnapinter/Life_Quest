"""Practical, locally translated alternatives; targets and progression stay untouched."""
from personalization import LANGUAGE_NAMES, CURRENCIES, CUISINES, clean_preferences, tr
from profile_data import country_of
from quest_plan import clean_title

# Every entry is one activity in en/pt/fr/de, not four different tasks.
VARIANTS = {
 'steps': [
 ('Walk {n:,} steps, including a walk after a meal','Dá {n} passos, incluindo um passeio após uma refeição','Fais {n} pas, avec une promenade après un repas','Gehe {n} Schritte, mit einem Spaziergang nach einer Mahlzeit'),
 ('Reach {n:,} steps with a walk to a familiar destination','Dá {n} passos com um passeio até um destino conhecido','Atteins {n} pas avec une marche vers un lieu familier','Erreiche {n} Schritte mit einem Spaziergang zu einem vertrauten Ziel'),
 ('Walk {n:,} steps with a favourite playlist','Dá {n} passos a ouvir uma playlist de que gostas','Fais {n} pas avec ta playlist préférée','Gehe {n} Schritte mit deiner Lieblingsplaylist')],
 'new_sport': [
 ('Try a beginner dance class or free dance tutorial','Experimenta uma aula de dança para iniciantes ou um tutorial gratuito','Essaie un cours de danse débutant ou un tutoriel gratuit','Probiere einen Tanzkurs für Anfänger oder ein kostenloses Tutorial'),
 ('Try a beginner racket sport with borrowed equipment','Experimenta um desporto de raquete com material emprestado','Essaie un sport de raquette avec du matériel emprunté','Probiere einen Schlägersport mit geliehener Ausrüstung'),
 ('Try a beginner balance or coordination activity','Experimenta uma atividade de equilíbrio ou coordenação para iniciantes','Essaie une activité d’équilibre ou de coordination pour débutants','Probiere eine einfache Gleichgewichts- oder Koordinationsübung')],
 'mobility': [
 ('Spend {n} minutes gently stretching after sitting','Faz {n} minutos de alongamentos suaves depois de estares sentado','Étire-toi doucement pendant {n} minutes après être resté assis','Dehne dich nach dem Sitzen {n} Minuten sanft'),
 ('Follow a gentle {n}-minute mobility routine','Segue uma rotina suave de mobilidade de {n} minutos','Suis une routine douce de mobilité de {n} minutes','Mache eine sanfte Mobilitätsroutine von {n} Minuten'),
 ('Make {n} minutes for comfortable shoulder and hip movements','Dedica {n} minutos a movimentos confortáveis de ombros e ancas','Consacre {n} minutes à des mouvements doux des épaules et des hanches','Bewege Schultern und Hüften {n} Minuten in angenehmem Umfang')],
 'strength': [
 ('Do {n} minutes of comfortable equipment-free strength exercises','Faz {n} minutos de exercícios de força confortáveis sem equipamento','Fais {n} minutes de renforcement adapté sans matériel','Mache {n} Minuten angenehme Kraftübungen ohne Geräte'),
 ('Follow a {n}-minute strength routine suited to your level','Segue uma rotina de força de {n} minutos adequada ao teu nível','Suis une routine de renforcement de {n} minutes à ton niveau','Mache eine {n}-minütige Kraftroutine auf deinem Niveau'),
 ('Practise comfortable strength movements for {n} minutes, with breaks','Pratica movimentos de força confortáveis durante {n} minutos, com pausas','Pratique des mouvements de renforcement pendant {n} minutes, avec pauses','Übe angenehme Kraftbewegungen {n} Minuten lang, mit Pausen')],
 'yoga': [
 ('Try a free beginner chair-yoga tutorial','Experimenta um tutorial gratuito de yoga na cadeira para iniciantes','Essaie un tutoriel gratuit de yoga sur chaise pour débutants','Probiere ein kostenloses Stuhlyoga-Tutorial für Anfänger'),
 ('Learn a gentle beginner yoga sequence you have not tried','Aprende uma sequência suave de yoga que ainda não experimentaste','Apprends une nouvelle séquence douce de yoga pour débutants','Lerne eine neue sanfte Yoga-Abfolge für Anfänger'),
 ('Try a beginner yoga session with a friend','Experimenta uma sessão de yoga para iniciantes com um amigo','Essaie une séance de yoga débutant avec un ami','Probiere mit einem Freund eine Yoga-Einheit für Anfänger')],
 'spending_log': [
 ('Categorise {n} recent expenses in your tracker ({currency})','Classifica {n} despesas recentes no teu registo ({currency})','Classe {n} dépenses récentes dans ton suivi ({currency})','Ordne {n} aktuelle Ausgaben in deiner Übersicht zu ({currency})'),
 ('Add {n} receipts to a spreadsheet in {currency}','Adiciona {n} recibos a uma folha de cálculo em {currency}','Ajoute {n} tickets à un tableau en {currency}','Trage {n} Belege in eine Tabelle in {currency} ein'),
 ('Log {n} purchases and mark each as a need or a want','Regista {n} compras e assinala necessidade ou desejo','Note {n} achats et indique besoin ou envie','Erfasse {n} Einkäufe und markiere Bedarf oder Wunsch')],
 'financial_learning': [
 ('Listen to an educational podcast about emergency savings','Ouve um podcast educativo sobre um fundo de emergência','Écoute un podcast éducatif sur l’épargne de précaution','Höre einen Lernpodcast über einen finanziellen Notgroschen'),
 ('Learn how compound interest works from a free explainer','Aprende como funcionam os juros compostos numa explicação gratuita','Découvre les intérêts composés avec une explication gratuite','Lerne mit einer kostenlosen Erklärung, wie Zinseszins funktioniert'),
 ('Read a beginner guide to investment fees and risk','Lê um guia de iniciação sobre custos e risco dos investimentos','Lis un guide débutant sur les frais et les risques des placements','Lies einen Anfängerleitfaden zu Anlagekosten und Risiken')],
 'budget': [
 ('Compare planned and actual spending in {n} budget categories','Compara despesas previstas e reais em {n} categorias','Compare dépenses prévues et réelles dans {n} catégories','Vergleiche geplante und tatsächliche Ausgaben in {n} Budgetkategorien'),
 ('Set realistic limits for {n} flexible spending categories','Define limites realistas para {n} categorias de despesas flexíveis','Fixe des limites réalistes pour {n} catégories de dépenses variables','Setze realistische Grenzen für {n} variable Ausgabenkategorien')],
 'money_review': [
 ('Check the next renewal date of {n} recurring payments','Verifica a próxima renovação de {n} pagamentos recorrentes','Vérifie la prochaine échéance de {n} paiements récurrents','Prüfe das nächste Verlängerungsdatum von {n} regelmäßigen Zahlungen'),
 ('List the price and usefulness of {n} subscription(s)','Regista o preço e a utilidade de {n} subscrições','Note le prix et l’utilité de {n} abonnements','Notiere Preis und Nutzen von {n} Abonnements')],
 'saving_goal': [
 ('Write {n} savings goals with an amount and a reason','Escreve {n} objetivos de poupança com valor e motivo','Note {n} objectifs d’épargne avec montant et raison','Notiere {n} Sparziele mit Betrag und Grund'),
 ('Choose {n} practical next steps for your savings plan','Escolhe {n} próximos passos práticos para o teu plano de poupança','Choisis {n} prochaines étapes concrètes pour ton épargne','Wähle {n} konkrete nächste Schritte für deinen Sparplan')],
 'vocabulary': [
 ('Learn {n} {language} words for ordering food','Aprende {n} palavras em {language} para pedir comida','Apprends {n} mots en {language} pour commander à manger','Lerne {n} Wörter auf {language} zum Essenbestellen'),
 ('Learn {n} {language} words for a hobby you enjoy','Aprende {n} palavras em {language} sobre um passatempo de que gostas','Apprends {n} mots en {language} sur un loisir que tu aimes','Lerne {n} Wörter auf {language} zu einem Hobby, das dir gefällt'),
 ('Learn {n} {language} words you could use while travelling','Aprende {n} palavras em {language} úteis numa viagem','Apprends {n} mots en {language} utiles en voyage','Lerne {n} Wörter auf {language}, die du auf Reisen nutzen kannst')],
 'listening': [
 ('Listen to a {language} conversation for {n} minutes','Ouve uma conversa em {language} durante {n} minutos','Écoute une conversation en {language} pendant {n} minutes','Höre {n} Minuten ein Gespräch auf {language}'),
 ('Watch a {language} video about a hobby for {n} minutes','Vê um vídeo em {language} sobre um passatempo durante {n} minutos','Regarde une vidéo en {language} sur un loisir pendant {n} minutes','Sieh dir {n} Minuten ein Hobbyvideo auf {language} an')],
 'speaking': [
 ('Introduce yourself in {language} aloud for {n} minutes','Apresenta-te em {language} em voz alta durante {n} minutos','Présente-toi en {language} à voix haute pendant {n} minutes','Stelle dich {n} Minuten laut auf {language} vor'),
 ('Describe a favourite place in {language} for {n} minutes','Descreve um lugar favorito em {language} durante {n} minutos','Décris un lieu préféré en {language} pendant {n} minutes','Beschreibe {n} Minuten lang einen Lieblingsort auf {language}')],
 'writing': [
 ('Write {n} {language} sentences about your next trip','Escreve {n} frases em {language} sobre a tua próxima viagem','Écris {n} phrases en {language} sur ton prochain voyage','Schreibe {n} Sätze auf {language} über deine nächste Reise'),
 ('Write {n} {language} sentences about a favourite meal','Escreve {n} frases em {language} sobre uma refeição favorita','Écris {n} phrases en {language} sur un repas préféré','Schreibe {n} Sätze auf {language} über ein Lieblingsessen')],
 'reading': [
 ('Read a {language} story at your level for {n} minutes','Lê uma história em {language} ao teu nível durante {n} minutos','Lis une histoire en {language} à ton niveau pendant {n} minutes','Lies {n} Minuten eine Geschichte auf {language} auf deinem Niveau'),
 ('Read about a favourite hobby in {language} for {n} minutes','Lê sobre um passatempo em {language} durante {n} minutos','Lis sur un loisir en {language} pendant {n} minutes','Lies {n} Minuten über ein Hobby auf {language}')],
 'nonfiction': [
 ('Read {n} nonfiction pages and note a useful idea','Lê {n} páginas de não ficção e anota uma ideia útil','Lis {n} pages documentaires et note une idée utile','Lies {n} Sachbuchseiten und notiere eine nützliche Idee'),
 ('Read {n} pages of a book about a skill you want to build','Lê {n} páginas de um livro sobre uma competência que queres desenvolver','Lis {n} pages sur une compétence que tu veux développer','Lies {n} Buchseiten über eine Fähigkeit, die du entwickeln möchtest')],
 'new_hobby': [
 ('Make a simple origami model using scrap paper','Faz um origami simples com papel reutilizado','Réalise un origami simple avec du papier récupéré','Falte ein einfaches Origami aus Altpapier'),
 ('Try sketching an everyday object with a pencil','Experimenta desenhar um objeto do dia a dia a lápis','Essaie de dessiner un objet du quotidien au crayon','Versuche, einen Alltagsgegenstand mit Bleistift zu zeichnen'),
 ('Try a new creative technique with materials you own','Experimenta uma técnica criativa nova com materiais que já tens','Essaie une nouvelle technique créative avec ton matériel','Probiere mit vorhandenem Material eine neue kreative Technik')],
 'public_speaking': [
 ('Explain a favourite idea aloud for {n} minutes','Explica uma ideia de que gostas em voz alta durante {n} minutos','Explique une idée que tu aimes à voix haute pendant {n} minutes','Erkläre {n} Minuten laut eine Idee, die dir gefällt'),
 ('Practise a {n}-minute introduction for a presentation','Pratica uma introdução de {n} minutos para uma apresentação','Répète une introduction de {n} minutes pour une présentation','Übe eine {n}-minütige Einleitung für einen Vortrag')],
 'planning': [
 ('Break a personal goal into {n} small next actions','Divide um objetivo pessoal em {n} pequenas ações','Découpe un objectif personnel en {n} petites actions','Teile ein persönliches Ziel in {n} kleine nächste Schritte'),
 ('Write down {n} priorities before opening social media','Escreve {n} prioridades antes de abrires as redes sociais','Note {n} priorités avant d’ouvrir les réseaux sociaux','Notiere {n} Prioritäten, bevor du soziale Medien öffnest')],
 'focused_learning': [
 ('Practise a useful spreadsheet skill for {n} minutes','Pratica uma competência útil de folhas de cálculo durante {n} minutos','Travaille une compétence utile de tableur pendant {n} minutes','Übe {n} Minuten eine nützliche Tabellenkalkulationsfunktion'),
 ('Follow a free lesson on a skill you chose for {n} minutes','Segue uma aula gratuita de uma competência à tua escolha durante {n} minutos','Suis un cours gratuit sur une compétence choisie pendant {n} minutes','Arbeite {n} Minuten an einer kostenlosen Lektion zu deiner Wunschfähigkeit')],
 'reconnect': [
 ('Ask {n} friend(s) how a recent plan turned out','Pergunta a {n} amigos como correu um plano recente','Demande à {n} amis comment un projet récent s’est passé','Frage {n} Freunde, wie ein kürzliches Vorhaben lief'),
 ('Share a meaningful memory with {n} person(s) you know','Partilha uma memória especial com {n} pessoas que conheces','Partage un beau souvenir avec {n} personnes que tu connais','Teile mit {n} bekannten Personen eine schöne Erinnerung')],
 'kindness': [
 ('Thank {n} person(s) for a specific thing they did','Agradece a {n} pessoas por algo concreto que fizeram','Remercie {n} personnes pour une action précise','Bedanke dich bei {n} Personen für eine konkrete Sache'),
 ('Send {n} sincere messages of encouragement','Envia {n} mensagens sinceras de incentivo','Envoie {n} messages sincères d’encouragement','Sende {n} ehrliche ermutigende Nachrichten')],
 'new_conversation': [
 ('Ask classmates or colleagues about an interest: {n} conversations','Pergunta a {n} colegas sobre um interesse','Interroge {n} camarades ou collègues sur un centre d’intérêt','Frage {n} Mitschüler oder Kollegen nach einem Interesse'),
 ('Introduce yourself to {n} people at a shared activity','Apresenta-te a {n} pessoas numa atividade em comum','Présente-toi à {n} personnes lors d’une activité commune','Stelle dich bei einer gemeinsamen Aktivität {n} Personen vor')],
 'make_plans': [
 ('Suggest {n} free activities to do with a friend','Sugere {n} atividades gratuitas para fazer com um amigo','Propose {n} activités gratuites à faire avec un ami','Schlage {n} kostenlose Aktivitäten mit einem Freund vor'),
 ('Offer {n} possible dates for a catch-up with a friend','Propõe {n} datas possíveis para te encontrares com um amigo','Propose {n} dates pour retrouver un ami','Schlage {n} mögliche Termine für ein Treffen mit einem Freund vor')],
 'listen': [
 ('Listen to someone describe their day for {n} minutes','Ouve alguém contar como foi o dia durante {n} minutos','Écoute quelqu’un raconter sa journée pendant {n} minutes','Höre jemandem {n} Minuten zu, wie sein Tag war'),
 ('Have a {n}-minute conversation with your phone put away','Conversa durante {n} minutos com o telemóvel guardado','Discute pendant {n} minutes avec ton téléphone rangé','Führe {n} Minuten ein Gespräch mit weggelegtem Handy')],
 'new_place': [
 ('Explore a public garden you have not visited in {city}','Explora um jardim público que ainda não visitaste em {city}','Explore un jardin public que tu ne connais pas à {city}','Entdecke in {city} einen öffentlichen Garten, den du noch nicht kennst'),
 ('Visit a new neighbourhood or public square in {city}','Visita um bairro ou praça pública nova em {city}','Visite un nouveau quartier ou une nouvelle place à {city}','Besuche in {city} ein neues Viertel oder einen öffentlichen Platz'),
 ('Explore a free exhibition or library in {city}','Explora uma exposição gratuita ou biblioteca em {city}','Explore une exposition gratuite ou une bibliothèque à {city}','Entdecke in {city} eine kostenlose Ausstellung oder Bibliothek')],
 'new_route': [
 ('Take a different route to a familiar errand','Segue um percurso diferente numa tarefa habitual','Prends un autre chemin pour une course habituelle','Nimm für eine vertraute Besorgung einen anderen Weg'),
 ('Explore an unfamiliar path in a public park','Explora um caminho desconhecido num parque público','Explore un chemin inconnu dans un parc public','Entdecke einen unbekannten Weg in einem öffentlichen Park'),
 ('Find a new walk that connects two familiar places','Descobre um passeio novo entre dois lugares conhecidos','Découvre une nouvelle promenade entre deux lieux connus','Finde einen neuen Spazierweg zwischen zwei vertrauten Orten')],
 'local_event': [
 ('Find a free workshop in {city} and check how to join','Procura uma oficina gratuita em {city} e vê como participar','Trouve un atelier gratuit à {city} et vérifie comment participer','Suche in {city} einen kostenlosen Workshop und prüfe die Teilnahme'),
 ('Check a library or community centre programme in {city}','Consulta o programa de uma biblioteca ou centro comunitário em {city}','Consulte le programme d’une bibliothèque ou association à {city}','Sieh dir in {city} das Programm einer Bibliothek oder eines Treffpunkts an'),
 ('Find a free cultural event in {city} that interests you','Encontra um evento cultural gratuito em {city} que te interesse','Trouve un événement culturel gratuit à {city} qui te plaît','Finde in {city} eine kostenlose Kulturveranstaltung, die dich interessiert')],
 'new_experience': [
 ('Try a new {cuisine} recipe with ingredients you have','Experimenta uma receita {cuisine} nova com ingredientes que já tens','Essaie une nouvelle recette {cuisine} avec tes ingrédients','Probiere mit vorhandenen Zutaten ein neues Rezept aus der {cuisine} Küche'),
 ('Learn a new way to cook vegetables you already have','Aprende uma forma nova de cozinhar legumes que já tens','Apprends une nouvelle façon de cuisiner tes légumes','Lerne eine neue Zubereitung für Gemüse, das du schon hast'),
 ('Cook a familiar ingredient using an unfamiliar technique','Cozinha um ingrediente conhecido com uma técnica nova','Cuisine un ingrédient familier avec une nouvelle technique','Bereite eine bekannte Zutat mit einer neuen Technik zu')],
 'nature': [
 ('Learn to propagate a plant you or a friend already owns','Aprende a propagar uma planta tua ou de um amigo','Apprends à multiplier une plante que toi ou un ami possédez','Lerne, eine vorhandene Pflanze von dir oder einem Freund zu vermehren'),
 ('Arrange a free plant-cutting swap with a friend','Combina uma troca gratuita de estacas com um amigo','Organise un échange gratuit de boutures avec un ami','Verabrede einen kostenlosen Stecklingtausch mit einem Freund'),
 ('Visit a public garden and learn about a plant you like','Visita um jardim público e aprende sobre uma planta de que gostas','Visite un jardin public et découvre une plante qui te plaît','Besuche einen öffentlichen Garten und lerne etwas über eine Pflanze')],
 'sleep_routine': [
 ('Start a calm, screen-free routine {n} minutes before bed','Começa uma rotina calma sem ecrãs {n} minutos antes de dormir','Commence une routine calme sans écran {n} minutes avant le coucher','Beginne {n} Minuten vor dem Schlafen eine ruhige Routine ohne Bildschirm'),
 ('Put tomorrow’s worries on paper {n} minutes before bed','Escreve as preocupações de amanhã {n} minutos antes de dormir','Note les préoccupations de demain {n} minutes avant le coucher','Schreibe {n} Minuten vor dem Schlafen morgige Sorgen auf')],
 'screen_break': [
 ('Put your phone away during a {n}-minute offline activity','Guarda o telemóvel numa atividade sem ecrãs de {n} minutos','Range ton téléphone pour une activité hors ligne de {n} minutes','Lege dein Handy für eine {n}-minütige Offline-Aktivität weg'),
 ('Spend {n} minutes reading or drawing away from screens','Passa {n} minutos a ler ou desenhar sem ecrãs','Lis ou dessine sans écran pendant {n} minutes','Lies oder zeichne {n} Minuten ohne Bildschirm')],
 'meal_planning': [
 ('Plan {n} simple meals using ingredients you already have','Planeia {n} refeições simples com ingredientes que já tens','Prévois {n} repas simples avec tes ingrédients','Plane {n} einfache Mahlzeiten mit vorhandenen Zutaten'),
 ('Write down {n} easy meals for your busiest days','Anota {n} refeições fáceis para os dias mais ocupados','Note {n} repas faciles pour tes journées chargées','Notiere {n} einfache Mahlzeiten für besonders volle Tage')],
 'rest': [
 ('Spend {n} quiet minutes with a book or a warm drink','Passa {n} minutos tranquilos com um livro ou uma bebida quente','Passe {n} minutes au calme avec un livre ou une boisson chaude','Verbringe {n} ruhige Minuten mit einem Buch oder warmen Getränk'),
 ('Take {n} minutes to sit comfortably and unwind','Reserva {n} minutos para te sentares confortavelmente e relaxar','Prends {n} minutes pour t’installer et te détendre','Nimm dir {n} Minuten, um bequem zu sitzen und abzuschalten')],
 'daily_routine': [
 ('Prepare {n} useful things tonight for tomorrow morning','Prepara hoje à noite {n} coisas úteis para amanhã de manhã','Prépare ce soir {n} choses utiles pour demain matin','Bereite heute Abend {n} nützliche Dinge für morgen früh vor'),
 ('Remove {n} small obstacles from your morning routine','Remove {n} pequenos obstáculos da tua rotina da manhã','Élimine {n} petits obstacles de ta routine du matin','Beseitige {n} kleine Hindernisse in deiner Morgenroutine')],
}


def render_variant(plan, preferences=None, location='', language='en'):
    variants=VARIANTS.get(plan.get('focus'))
    if not variants:
        return plan.get('title','')
    context=plan.get('context') or {}
    index=int(context.get('variant',0)) % len(variants)
    prefs=clean_preferences(preferences or context)
    goal=prefs.get('target_language')
    country=country_of(location)
    city=(location or '').split(',')[0].strip() or tr(('your area','a tua zona','ta région','deiner Umgebung'),language)
    target_language=tr(LANGUAGE_NAMES[goal],language) if goal else tr(('your chosen language','a língua que escolheste','ta langue choisie','deiner gewählten Sprache'),language)
    cuisine=tr(CUISINES.get(country,('regional','regional','régionale','regionalen')),language)
    currency=CURRENCIES.get(country,tr(('your currency','tua moeda','ta monnaie','deiner Währung'),language))
    return clean_title(tr(variants[index],language).format(n=plan.get('target',1),language=target_language,
                                                        city=city,cuisine=cuisine,currency=currency),plan.get('target'))


def varied_plan(plan, history, context):
    """Choose a different activity, including after skips; never modify numeric fields."""
    variants=VARIANTS.get(plan['focus'])
    if not variants:
        return {**plan,'context':context}
    previous=sorted((q for q in history if q.get('slot')==plan['slot'] and q.get('status') in ('completed','skipped')),
                    key=lambda q:q.get('completed_at') or q.get('created_at',''))
    recent={q.get('context',{}).get('variant') for q in previous[-(len(variants)-1):] if isinstance(q.get('context'),dict)}
    index=next((i for i in range(len(variants)) if i not in recent),len(previous)%len(variants))
    result={**plan,'context':{**context,'variety_version':1,'variant':index}}
    # Store the canonical English template; render it locally in the selected UI language.
    result['title']=render_variant(result)
    return result
