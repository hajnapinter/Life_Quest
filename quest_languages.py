"""Display translations: quest IDs, targets and stored history never change."""
import re
from quest_plan import TRACKS, clean_title

# Each row corresponds to the English templates in TRACKS, in the same order.
TITLES = {
'steps': [('Caminha {n} passos hoje','Marche {n} pas aujourd’hui','Gehe heute {n} Schritte'),('Atinge {n} passos ao longo do dia','Atteins {n} pas dans ta journée','Erreiche über den Tag {n} Schritte')],
'new_sport': [('Experimenta um desporto novo','Essaie un sport que tu n’as jamais pratiqué','Probiere eine neue Sportart aus'),('Participa numa sessão de iniciação a um novo desporto','Participe à une initiation à un nouveau sport','Besuche einen Anfängerkurs in einer neuen Sportart')],
'mobility': [('Faz alongamentos durante {n} minutos','Étire-toi pendant {n} minutes','Dehne dich {n} Minuten lang'),('Faz uma pausa de mobilidade de {n} minutos','Fais une pause mobilité de {n} minutes','Mache eine Mobilitätspause von {n} Minuten')],
'strength': [('Faz uma sessão de força para iniciantes de {n} minutos','Fais une séance de renforcement débutant de {n} minutes','Mache ein {n}-minütiges Krafttraining für Anfänger'),('Faz {n} minutos de exercícios suaves com o peso do corpo','Fais {n} minutes d’exercices doux au poids du corps','Mache {n} Minuten sanfte Übungen mit deinem Körpergewicht')],
'yoga': [('Experimenta uma aula de ioga para iniciantes','Essaie un cours de yoga pour débutants','Probiere einen Yoga-Anfängerkurs aus'),('Aprende uma nova sequência de ioga para iniciantes','Apprends une nouvelle séquence de yoga pour débutants','Lerne eine neue Yoga-Abfolge für Anfänger')],
'spending_log': [('Regista {n} despesas numa folha de cálculo','Note {n} dépenses dans un tableur','Erfasse {n} Ausgaben in einer Tabelle'),('Adiciona as tuas últimas {n} compras ao registo de despesas','Ajoute tes {n} derniers achats à ton suivi des dépenses','Trage deine letzten {n} Einkäufe in deine Ausgabenübersicht ein')],
'financial_learning': [('Ouve um episódio sobre os princípios do investimento','Écoute un épisode sur les bases de l’investissement','Höre eine Folge über die Grundlagen des Investierens'),('Lê um artigo sobre como criar o hábito de poupar','Lis un article sur la façon de prendre l’habitude d’épargner','Lies einen Artikel darüber, wie du regelmäßig sparen kannst')],
'budget': [('Define um orçamento para {n} categorias de despesas','Fixe un budget pour {n} catégories de dépenses','Lege ein Budget für {n} Ausgabenkategorien fest'),('Revê {n} categorias do teu orçamento mensal','Passe en revue {n} catégories de ton budget mensuel','Prüfe {n} Kategorien deines Monatsbudgets')],
'money_review': [('Revê {n} pagamentos recorrentes','Passe en revue {n} paiements récurrents','Prüfe {n} regelmäßige Zahlungen'),('Verifica {n} subscrições ou contas regulares','Vérifie {n} abonnements ou factures régulières','Prüfe {n} Abonnements oder regelmäßige Rechnungen')],
'saving_goal': [('Escreve {n} objetivos de poupança','Note {n} objectifs d’épargne','Schreibe {n} Sparziele auf'),('Adiciona {n} pequenos passos ao teu plano de poupança','Ajoute {n} petites étapes à ton plan d’épargne','Ergänze deinen Sparplan um {n} kleine Schritte')],
'vocabulary': [('Aprende {n} palavras novas na língua que escolheste','Apprends {n} nouveaux mots dans la langue de ton choix','Lerne {n} neue Wörter in deiner gewählten Sprache'),('Pratica {n} palavras novas','Révise {n} nouveaux mots de vocabulaire','Übe {n} neue Vokabeln')],
'listening': [('Ouve {n} minutos na língua que escolheste','Écoute ta langue de choix pendant {n} minutes','Höre {n} Minuten etwas in deiner gewählten Sprache'),('Vê um vídeo de iniciação à língua de {n} minutos','Regarde une vidéo de langue pour débutants de {n} minutes','Sieh dir ein {n}-minütiges Sprachvideo für Anfänger an')],
'speaking': [('Fala em voz alta na língua que escolheste durante {n} minutos','Parle à voix haute dans ta langue de choix pendant {n} minutes','Sprich {n} Minuten laut in deiner gewählten Sprache'),('Descreve o teu dia em voz alta durante {n} minutos','Décris ta journée à voix haute pendant {n} minutes','Beschreibe deinen Tag {n} Minuten lang laut')],
'writing': [('Escreve {n} frases na língua que escolheste','Écris {n} phrases dans la langue de ton choix','Schreibe {n} Sätze in deiner gewählten Sprache'),('Descreve algo de que gostas em {n} frases','Décris quelque chose que tu aimes en {n} phrases','Beschreibe etwas, das du magst, in {n} Sätzen')],
'reading': [('Lê na língua que escolheste durante {n} minutos','Lis dans la langue de ton choix pendant {n} minutes','Lies {n} Minuten in deiner gewählten Sprache'),('Explora um artigo curto durante {n} minutos','Explore un court article pendant {n} minutes','Lies {n} Minuten in einem kurzen Artikel')],
'nonfiction': [('Lê {n} páginas de um livro de não ficção','Lis {n} pages d’un livre documentaire','Lies {n} Seiten eines Sachbuchs'),('Avança {n} páginas no teu livro de não ficção','Avance de {n} pages dans ton livre documentaire','Lies {n} weitere Seiten in deinem Sachbuch')],
'new_hobby': [('Experimenta um passatempo novo','Essaie un loisir que tu n’as jamais pratiqué','Probiere ein neues Hobby aus'),('Cria algo com uma técnica criativa nova','Crée quelque chose avec une nouvelle technique créative','Gestalte etwas mit einer neuen kreativen Technik')],
'public_speaking': [('Faz um discurso de {n} minutos ao espelho','Fais un discours de {n} minutes devant ton miroir','Halte eine {n}-minütige Rede vor dem Spiegel'),('Pratica a apresentação de uma ideia durante {n} minutos','Entraîne-toi à présenter une idée pendant {n} minutes','Übe {n} Minuten lang, eine Idee vorzustellen')],
'planning': [('Escolhe {n} prioridades para amanhã','Choisis {n} priorités pour demain','Wähle {n} Prioritäten für morgen'),('Planeia {n} próximos passos concretos para um objetivo pessoal','Prévois {n} prochaines étapes concrètes pour un objectif personnel','Plane {n} konkrete nächste Schritte für ein persönliches Ziel')],
'focused_learning': [('Aprende uma competência útil durante {n} minutos','Apprends une compétence utile pendant {n} minutes','Lerne {n} Minuten lang eine nützliche Fähigkeit'),('Dedica {n} minutos a um curso gratuito','Consacre {n} minutes à un cours gratuit','Arbeite {n} Minuten an einem kostenlosen Kurs')],
'reconnect': [('Pergunta a {n} amigos como estão','Prends des nouvelles de {n} amis','Melde dich bei {n} Freunden'),('Envia uma mensagem atenciosa a {n} pessoas','Envoie un message attentionné à {n} personnes','Schicke {n} Personen eine aufmerksame Nachricht')],
'kindness': [('Faz {n} elogios sinceros','Fais {n} compliments sincères','Mache {n} ehrliche Komplimente'),('Agradece a {n} pessoas por algo específico','Remercie {n} personnes pour quelque chose de précis','Bedanke dich bei {n} Personen für etwas Bestimmtes')],
'new_conversation': [('Inicia {n} conversas amigáveis','Engage {n} conversations amicales','Beginne {n} freundliche Gespräche'),('Diz olá a {n} pessoas novas','Dis bonjour à {n} nouvelles personnes','Begrüße {n} neue Personen')],
'make_plans': [('Sugere {n} planos simples para pôr a conversa em dia','Propose {n} occasions simples de se retrouver','Schlage {n} einfache Treffen zum Plaudern vor'),('Convida um amigo para {n} atividades gratuitas em conjunto','Invite un ami à {n} activités gratuites ensemble','Lade einen Freund zu {n} kostenlosen gemeinsamen Aktivitäten ein')],
'listen': [('Conversa sem telemóvel durante {n} minutos','Discute sans téléphone pendant {n} minutes','Führe {n} Minuten ein Gespräch ohne Handy'),('Dá toda a tua atenção a alguém durante {n} minutos','Accorde toute ton attention à quelqu’un pendant {n} minutes','Schenke jemandem {n} Minuten deine volle Aufmerksamkeit')],
'new_place': [('Explora um lugar novo perto de ti','Explore un nouvel endroit près de chez toi','Entdecke einen neuen Ort in deiner Nähe'),('Visita um sítio local onde nunca estiveste','Visite un lieu du quartier où tu n’es jamais allé','Besuche einen Ort in deiner Umgebung, den du noch nicht kennst'),('Descobre uma exposição gratuita ou um bairro novo','Découvre une exposition gratuite ou un nouveau quartier','Entdecke eine kostenlose Ausstellung oder ein neues Viertel')],
'new_route': [('Experimenta um percurso diferente a pé','Essaie un nouvel itinéraire à pied','Probiere einen anderen Spazierweg aus'),('Segue um caminho desconhecido até um lugar familiar','Prends un chemin inconnu vers un lieu familier','Nimm einen unbekannten Weg zu einem vertrauten Ort'),('Descobre um parque ou trilho novo perto de ti','Découvre un nouveau parc ou sentier près de chez toi','Entdecke einen neuen Park oder Wanderweg in deiner Nähe')],
'local_event': [('Encontra um evento local gratuito a que gostasses de ir','Trouve un événement local gratuit qui te plaît','Finde eine kostenlose Veranstaltung in deiner Nähe, die dich interessiert'),('Experimenta uma oficina gratuita ou atividade comunitária','Essaie un atelier gratuit ou une activité associative','Probiere einen kostenlosen Workshop oder eine Gemeinschaftsaktivität aus'),('Visita um mercado local que ainda não conheces','Visite un marché local que tu ne connais pas encore','Besuche einen Markt in deiner Nähe, den du noch nicht kennst')],
'new_experience': [('Experimenta uma receita de uma cozinha que nunca preparaste','Essaie une recette d’une cuisine que tu n’as jamais préparée','Probiere ein Rezept aus einer für dich neuen Länderküche'),('Prepara uma refeição com legumes de três cores diferentes','Prépare un repas avec des légumes de trois couleurs différentes','Koche eine Mahlzeit mit Gemüse in drei verschiedenen Farben'),('Aprende uma técnica culinária nova com ingredientes que já tens','Apprends une nouvelle technique culinaire avec tes ingrédients','Lerne eine neue Kochtechnik mit Zutaten, die du schon hast')],
'nature': [('Arranja uma planta nova ou troca uma estaca com um amigo','Adopte une plante ou échange une bouture avec un ami','Hole dir eine neue Pflanze oder tausche einen Steckling mit einem Freund'),('Visita um jardim onde nunca estiveste','Visite un jardin que tu ne connais pas encore','Besuche einen Garten, den du noch nicht kennst'),('Aprende a propagar uma planta que já tens','Apprends à multiplier une plante que tu possèdes déjà','Lerne, eine deiner Pflanzen zu vermehren')],
'sleep_routine': [('Começa a relaxar {n} minutos antes de dormir','Commence à te détendre {n} minutes avant le coucher','Komme {n} Minuten vor dem Schlafengehen zur Ruhe'),('Reserva {n} minutos para uma rotina calma antes de dormir','Prends {n} minutes pour une routine du soir calme','Nimm dir {n} Minuten für eine ruhige Abendroutine')],
'screen_break': [('Faz uma pausa sem ecrãs de {n} minutos','Fais une pause sans écran de {n} minutes','Mache eine {n}-minütige Bildschirmpause'),('Passa {n} minutos longe das redes sociais','Passe {n} minutes sans réseaux sociaux','Verbringe {n} Minuten ohne soziale Medien')],
'meal_planning': [('Planeia {n} refeições simples para a semana','Prévois {n} repas simples pour la semaine','Plane {n} einfache Mahlzeiten für die Woche'),('Prepara {n} ideias de refeições fáceis para um dia atarefado','Prépare {n} idées de repas faciles pour une journée chargée','Überlege dir {n} einfache Mahlzeiten für einen vollen Tag')],
'rest': [('Dedica {n} minutos a relaxar','Prends {n} minutes pour te détendre','Entspanne dich {n} Minuten lang'),('Reserva uma pausa tranquila de {n} minutos','Accorde-toi une pause calme de {n} minutes','Nimm dir eine ruhige Pause von {n} Minuten')],
'daily_routine': [('Prepara {n} coisas para uma manhã mais calma','Prépare {n} choses pour une matinée plus sereine','Bereite {n} Dinge für einen ruhigeren Morgen vor'),('Faz {n} pequenas melhorias na tua rotina da noite','Apporte {n} petites améliorations à ta routine du soir','Verbessere {n} Kleinigkeiten an deiner Abendroutine')],
}

# Static shared quests and score units use the exact database wording as their keys.
SHARED = {
'Explore a new place together': ('Explorem um lugar novo juntos','Explorez un nouvel endroit ensemble','Entdeckt gemeinsam einen neuen Ort'),
'Teach one another a new skill': ('Ensinem uma competência nova uns aos outros','Apprenez-vous une nouvelle compétence','Bringt einander eine neue Fähigkeit bei'),
'Cook a recipe from a new cuisine together': ('Preparem juntos uma receita de uma cozinha nova','Cuisinez ensemble une recette d’une nouvelle cuisine','Kocht gemeinsam ein Rezept aus einer neuen Länderküche'),
'Try a new sport together': ('Experimentem um desporto novo juntos','Essayez un nouveau sport ensemble','Probiert gemeinsam eine neue Sportart aus'),
'Organise a screen-free catch-up': ('Organizem um encontro sem ecrãs','Organisez des retrouvailles sans écran','Organisiert ein Treffen ohne Bildschirme'),
'Visit a free exhibition together': ('Visitem uma exposição gratuita juntos','Visitez une exposition gratuite ensemble','Besucht gemeinsam eine kostenlose Ausstellung'),
'Discover a new walking route together': ('Descubram um percurso novo a pé juntos','Découvrez un nouvel itinéraire à pied ensemble','Entdeckt gemeinsam einen neuen Spazierweg'),
'Join a free workshop as a squad': ('Participem numa oficina gratuita em equipa','Participez à un atelier gratuit en équipe','Besucht als Team einen kostenlosen Workshop'),
'Organise a plant, book or recipe swap': ('Organizem uma troca de plantas, livros ou receitas','Organisez un échange de plantes, livres ou recettes','Organisiert einen Tausch von Pflanzen, Büchern oder Rezepten'),
'Who can walk more steps today?': ('Quem consegue dar mais passos hoje?','Qui fera le plus de pas aujourd’hui ?','Wer schafft heute die meisten Schritte?'),
'Who can read more book pages today?': ('Quem consegue ler mais páginas hoje?','Qui lira le plus de pages aujourd’hui ?','Wer liest heute die meisten Buchseiten?'),
'Who can learn more new words today?': ('Quem consegue aprender mais palavras novas hoje?','Qui apprendra le plus de nouveaux mots aujourd’hui ?','Wer lernt heute die meisten neuen Wörter?'),
'Who can cook more new recipes today?': ('Quem consegue preparar mais receitas novas hoje?','Qui cuisinera le plus de nouvelles recettes aujourd’hui ?','Wer kocht heute die meisten neuen Rezepte?'),
'Who can explore more new places today?': ('Quem consegue explorar mais lugares novos hoje?','Qui explorera le plus de nouveaux endroits aujourd’hui ?','Wer entdeckt heute die meisten neuen Orte?'),
'steps': ('passos','pas','Schritte'), 'pages': ('páginas','pages','Seiten'),
'words': ('palavras','mots','Wörter'), 'recipes': ('receitas','recettes','Rezepte'), 'places': ('lugares','lieux','Orte'),
}


def _format(template, target, language):
    n = f'{target:,}' if target >= 1000 else str(target)
    n = n.replace(',', '.' if language == 'de' else ' ') if language != 'en' else n
    text = template.format(n=n)
    if target == 1:
        replacements = {
            'pt': {'amigos':'amigo','pessoas':'pessoa','elogios':'elogio','conversas':'conversa','planos':'plano','atividades':'atividade','categorias':'categoria','pagamentos':'pagamento','objetivos':'objetivo','passos':'passo','prioridades':'prioridade','refeições':'refeição','ideias':'ideia','coisas':'coisa','melhorias':'melhoria'},
            'fr': {'amis':'ami','personnes':'personne','compliments':'compliment','conversations':'conversation','occasions':'occasion','activités':'activité','catégories':'catégorie','paiements':'paiement','objectifs':'objectif','étapes':'étape','priorités':'priorité','choses':'chose','améliorations':'amélioration'},
            'de': {'Schritte':'Schritt','Ausgabenkategorien':'Ausgabenkategorie','Zahlungen':'Zahlung','Sparziele':'Sparziel','Prioritäten':'Priorität','Dinge':'Ding','Kleinigkeiten':'Kleinigkeit','Komplimente':'Kompliment','Gespräche':'Gespräch','Personen':'Person','Aktivitäten':'Aktivität','Mahlzeiten':'Mahlzeit'},
        }
        for plural, singular in replacements.get(language, {}).items():
            text = re.sub(r'\b' + plural + r'\b', singular, text)
    return text


def known_translation(text, language):
    """Match templates in any supported language; never infer a different quest from its focus."""
    if language not in ('en','pt','fr','de'):
        language = 'en'
    index = {'pt':0,'fr':1,'de':2}
    for english, variants in SHARED.items():
        if text in (english, *variants):
            return english if language == 'en' else variants[index[language]]
    # Detect the target in the text, including localized thousands separators.
    numbers = re.findall(r'\d+(?:[, .\u00a0\u202f]\d{3})*', text)
    target = int(re.sub(r'\D', '', numbers[0])) if numbers else 1
    for tracks in TRACKS.values():
        for focus, _, templates, _ in tracks:
            for i, template in enumerate(templates):
                english = clean_title(template.format(n=target), target)
                variants = [_format(t, target, lang) for t, lang in zip(TITLES[focus][i], ('pt','fr','de'))]
                if text in (english, *variants):
                    return english if language == 'en' else variants[index[language]]
    return None
