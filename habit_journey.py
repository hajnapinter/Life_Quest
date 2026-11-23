"""Broad habit identities and evidence-based journeys; never changes quest progression."""
from progress_insights import HABITS
from personalization import tr
from quest_plan import TRACKS, EXPERIENCE_FOCUSES

# Long-term purpose per pillar, phrased as an aim rather than a promised outcome.
PURPOSES={
 'Fitness':('Build a comfortable movement routine you can return to.', 'Cria uma rotina de movimento confortável a que possas voltar.', 'Construis une routine de mouvement confortable et durable.', 'Baue eine angenehme Bewegungsroutine auf, zu der du zurückkehren kannst.'),
 'Finance':('Understand your money and practise informed everyday decisions.', 'Compreende o teu dinheiro e pratica decisões informadas no dia a dia.', 'Comprends ton argent et entraîne-toi à décider de façon éclairée.', 'Verstehe dein Geld und übe bewusste Alltagsentscheidungen.'),
 'Languages':('Use your chosen language in situations that matter to you.', 'Usa a língua que escolheste em situações importantes para ti.', 'Utilise ta langue choisie dans des situations qui comptent pour toi.', 'Nutze deine gewählte Sprache in Situationen, die dir wichtig sind.'),
 'Personal Growth':('Make room for learning, creativity and expressing your ideas.', 'Dá espaço à aprendizagem, criatividade e expressão das tuas ideias.', 'Fais de la place à l’apprentissage, à la créativité et à tes idées.', 'Schaffe Raum für Lernen, Kreativität und deine eigenen Ideen.'),
 'Social':('Practise thoughtful connections while respecting everyone’s boundaries.', 'Cultiva ligações atenciosas respeitando os limites de todos.', 'Cultive des liens attentionnés en respectant les limites de chacun.', 'Pflege aufmerksame Kontakte und respektiere dabei alle Grenzen.'),
 'Adventure':('Keep discovering accessible experiences beyond your usual routine.', 'Continua a descobrir experiências acessíveis fora da rotina habitual.', 'Continue à découvrir des expériences accessibles hors de ta routine.', 'Entdecke weiterhin erreichbare Erlebnisse außerhalb deiner gewohnten Routine.'),
 'Health':('Build everyday routines that leave space for rest and preparation.', 'Cria rotinas diárias com espaço para descanso e preparação.', 'Construis des routines quotidiennes avec du repos et de la préparation.', 'Baue Alltagsroutinen mit Raum für Ruhe und Vorbereitung auf.'),
}
FOCUS_PURPOSES={
 'steps':('Make walking a familiar part of everyday journeys.','Integra as caminhadas nas deslocações diárias.','Intègre la marche à tes déplacements quotidiens.','Integriere das Gehen in deine alltäglichen Wege.'),
 'mobility':('Practise comfortable movement after time spent sitting.','Pratica movimentos confortáveis depois de estares sentado.','Pratique des mouvements confortables après être resté assis.','Übe angenehme Bewegung nach längerem Sitzen.'),
 'strength':('Build familiarity with strength movements at your own level.','Ganha familiaridade com exercícios de força ao teu nível.','Familiarise-toi avec des mouvements de renforcement adaptés.','Werde mit Kraftbewegungen auf deinem Niveau vertraut.'),
 'new_sport':('Discover forms of movement you actually enjoy.','Descobre formas de movimento de que gostas.','Découvre des activités physiques qui te plaisent.','Entdecke Bewegungsarten, die dir Freude machen.'),
 'yoga':('Explore gentle sequences and adapt them to your comfort.','Explora sequências suaves e adapta-as ao teu conforto.','Explore des séquences douces adaptées à ton confort.','Entdecke sanfte Abfolgen und passe sie deinem Wohlbefinden an.'),
 'spending_log':('See where your money goes before deciding what to change.','Percebe para onde vai o dinheiro antes de decidires o que mudar.','Vois où va ton argent avant de décider quoi changer.','Erkenne, wohin dein Geld fließt, bevor du Änderungen planst.'),
 'financial_learning':('Understand financial concepts before making money decisions.','Compreende conceitos financeiros antes de tomares decisões.','Comprends les notions financières avant de décider.','Verstehe Finanzbegriffe, bevor du Geldentscheidungen triffst.'),
 'budget':('Give everyday spending a realistic plan.','Dá às despesas diárias um plano realista.','Donne un cadre réaliste aux dépenses quotidiennes.','Gib deinen Alltagsausgaben einen realistischen Plan.'),
 'money_review':('Notice regular costs and decide which still serve you.','Revê custos regulares e decide quais continuam a ser úteis.','Repère les frais réguliers et ceux qui te sont encore utiles.','Prüfe regelmäßige Kosten und entscheide, welche dir noch nützen.'),
 'saving_goal':('Turn a vague wish into a clear savings plan.','Transforma um desejo num plano de poupança claro.','Transforme une envie en un plan d’épargne clair.','Mache aus einem Wunsch einen klaren Sparplan.'),
 'vocabulary':('Make useful words easier to recall in real conversations.','Pratica recordar palavras úteis em conversas reais.','Entraîne-toi à retrouver des mots utiles en conversation.','Übe, nützliche Wörter in echten Gesprächen abzurufen.'),
 'listening':('Get used to the sounds and expressions of your chosen language.','Habitua-te aos sons e expressões da língua escolhida.','Habitue-toi aux sons et expressions de ta langue choisie.','Gewöhne dich an die Klänge und Ausdrücke deiner gewählten Sprache.'),
 'speaking':('Practise putting your own ideas into spoken words.','Pratica expressar as tuas ideias em voz alta.','Entraîne-toi à exprimer tes idées à voix haute.','Übe, deine eigenen Ideen laut auszudrücken.'),
 'writing':('Use new vocabulary to express something meaningful to you.','Usa vocabulário novo para expressar algo importante para ti.','Utilise du vocabulaire nouveau pour exprimer quelque chose qui compte.','Nutze neue Wörter, um etwas auszudrücken, das dir wichtig ist.'),
 'reading':('Meet words and phrases in a context that interests you.','Descobre palavras e frases num contexto que te interessa.','Découvre mots et expressions dans un contexte intéressant.','Begegne Wörtern und Ausdrücken in einem Kontext, der dich interessiert.'),
 'nonfiction':('Keep learning from books and bring useful ideas into everyday life.','Aprende com livros e leva ideias úteis para o dia a dia.','Apprends dans les livres et retiens des idées pour le quotidien.','Lerne aus Büchern und nimm nützliche Ideen für den Alltag mit.'),
 'new_hobby':('Discover creative activities you want to return to.','Descobre atividades criativas a que queiras voltar.','Découvre des activités créatives que tu aimerais retrouver.','Entdecke kreative Tätigkeiten, zu denen du zurückkehren möchtest.'),
 'public_speaking':('Practise a clear opening, a useful idea and a simple ending.','Pratica uma abertura clara, uma ideia útil e um final simples.','Pratique une ouverture claire, une idée utile et une conclusion simple.','Übe einen klaren Einstieg, eine nützliche Idee und einen einfachen Schluss.'),
 'planning':('Make your next action clear enough to start.','Define a próxima ação de forma concreta para começares.','Rends ta prochaine action assez concrète pour commencer.','Mache deinen nächsten Schritt konkret genug, um anzufangen.'),
 'focused_learning':('Turn a small lesson into something you can try yourself.','Transforma uma pequena lição em algo que possas experimentar.','Transforme une petite leçon en quelque chose à essayer.','Mache aus einer kleinen Lektion etwas, das du selbst ausprobieren kannst.'),
 'reconnect':('Keep meaningful connections from getting lost in a busy week.','Cuida das ligações importantes mesmo numa semana ocupada.','Entretiens les liens importants même pendant une semaine chargée.','Pflege wichtige Verbindungen auch in einer vollen Woche.'),
 'kindness':('Practise specific, thoughtful appreciation.','Pratica demonstrar apreço de forma concreta e atenciosa.','Pratique une reconnaissance précise et attentionnée.','Übe konkrete und aufmerksame Wertschätzung.'),
 'new_conversation':('Practise starting respectful conversations in shared settings.','Pratica iniciar conversas respeitosas em contextos partilhados.','Entraîne-toi à engager des conversations respectueuses.','Übe, in gemeinsamen Situationen respektvolle Gespräche zu beginnen.'),
 'make_plans':('Turn wanting to meet into a simple invitation.','Transforma a vontade de estar junto num convite simples.','Transforme l’envie de se voir en une invitation simple.','Mache aus dem Wunsch nach einem Treffen eine einfache Einladung.'),
 'listen':('Give another person your attention without competing distractions.','Dá atenção a outra pessoa sem distrações a competir.','Accorde ton attention à quelqu’un sans distractions.','Schenke einer anderen Person deine Aufmerksamkeit ohne Ablenkungen.'),
 'new_place':('Expand the places you know and can enjoy nearby.','Alarga os lugares que conheces e podes aproveitar perto de ti.','Élargis les lieux que tu connais et apprécies près de chez toi.','Erweitere die Orte in deiner Nähe, die du kennst und genießen kannst.'),
 'new_route':('Add fresh, accessible routes to familiar journeys.','Acrescenta percursos novos e acessíveis às deslocações habituais.','Ajoute des itinéraires nouveaux et accessibles à tes trajets.','Ergänze vertraute Wege um neue, erreichbare Routen.'),
 'local_event':('Discover real community activities that fit your interests.','Descobre atividades comunitárias reais que combinam contigo.','Découvre des activités locales réelles qui te plaisent.','Entdecke echte lokale Aktivitäten, die zu deinen Interessen passen.'),
 'new_experience':('Build a repertoire of dishes and techniques you enjoy.','Cria um repertório de pratos e técnicas de que gostas.','Élargis ton répertoire de plats et de techniques.','Erweitere dein Repertoire an Gerichten und Techniken, die dir gefallen.'),
 'nature':('Make space to learn about plants and nearby green places.','Dá espaço para aprender sobre plantas e espaços verdes próximos.','Fais de la place aux plantes et aux espaces verts proches.','Schaffe Raum, um Pflanzen und nahe Grünflächen kennenzulernen.'),
 'sleep_routine':('Create a repeatable transition from a busy day to bedtime.','Cria uma transição repetível entre o dia e a hora de dormir.','Crée une transition régulière entre la journée et le coucher.','Schaffe einen wiederholbaren Übergang vom Tag zur Schlafenszeit.'),
 'screen_break':('Practise choosing an offline activity on purpose.','Pratica escolher uma atividade sem ecrãs de forma intencional.','Entraîne-toi à choisir volontairement une activité sans écran.','Übe, dich bewusst für eine bildschirmfreie Aktivität zu entscheiden.'),
 'meal_planning':('Have manageable meal options ready for busy days.','Tem opções de refeições simples para os dias ocupados.','Prévois des repas réalisables pour les journées chargées.','Halte machbare Essensideen für volle Tage bereit.'),
 'rest':('Make a deliberate pause without needing to be productive.','Faz uma pausa intencional sem precisares de ser produtivo.','Accorde-toi une pause sans devoir être productif.','Nimm dir bewusst eine Pause, ohne produktiv sein zu müssen.'),
 'daily_routine':('Reduce small obstacles before the next day begins.','Reduz pequenos obstáculos antes de começar o dia seguinte.','Réduis les petits obstacles avant le lendemain.','Verringere kleine Hindernisse, bevor der nächste Tag beginnt.'),
}
UNITS={
 'steps':('steps','passos','pas','Schritte'), 'vocabulary':('words','palavras','mots','Wörter'),
 'writing':('sentences','frases','phrases','Sätze'),'nonfiction':('pages','páginas','pages','Seiten'),
 'spending_log':('expenses','despesas','dépenses','Ausgaben'),'budget':('categories','categorias','catégories','Kategorien'),
 'money_review':('payments','pagamentos','paiements','Zahlungen'),'saving_goal':('goals','objetivos','objectifs','Ziele'),
 'reconnect':('people','pessoas','personnes','Personen'),'kindness':('acts of appreciation','gestos de apreço','gestes de reconnaissance','Gesten der Wertschätzung'),
 'new_conversation':('conversations','conversas','conversations','Gespräche'),'make_plans':('plans','planos','projets','Pläne'),
 'meal_planning':('meals','refeições','repas','Mahlzeiten'),'daily_routine':('preparations','preparações','préparatifs','Vorbereitungen'),
 'planning':('priorities','prioridades','priorités','Prioritäten'),
}
MINUTE_FOCUSES={'mobility','strength','listening','speaking','reading','public_speaking','focused_learning','listen','sleep_routine','screen_break','rest'}


def habit_name(focus,language='en'):
    names={'steps':('Step rhythm','Ritmo de passos','Le rythme des pas','Dein Schrittrhythmus'),
           'vocabulary':('Word power','Vocabulário em ação','Le pouvoir des mots','Dein Wortschatz'),
           'nonfiction':('Reading for growth','Ler para crescer','Lire pour grandir','Lesen und wachsen'),
           'spending_log':('Money awareness','Consciência financeira','Comprendre ses dépenses','Deine Geldübersicht')}
    return tr(names.get(focus,HABITS.get(focus,('Your habit','O teu hábito','Ton habitude','Deine Gewohnheit'))),language)


def journey_facts(plan,rows):
    own=sorted((q for q in rows if q.get('slot')==plan['slot'] and q.get('category')==plan['category'] and q.get('status')=='completed'),key=lambda q:q.get('completed_at') or '')
    return {'completed':len(own),'first':own[0].get('target') if own else None,'latest':own[-1].get('target') if own else None,
            'next':plan.get('target'),'goal':12000 if plan['focus']=='steps' else TRACKS[plan['category']][plan['slot']-1][1][-1],
            'stage':'starting' if not own else 'building' if len(own)<5 else 'established_practice'}


def journey_texts(plan,rows,language='en'):
    f=journey_facts(plan,rows);focus=plan['focus']
    purpose=tr(FOCUS_PURPOSES.get(focus,PURPOSES[plan['category']]),language)
    if focus in EXPERIENCE_FOCUSES:
        progress=tr(('Every completed experience adds another option to your life. Choose a fresh version that still feels manageable.',
                     'Cada experiência concluída acrescenta uma opção à tua vida. Escolhe uma versão nova e acessível.',
                     'Chaque expérience terminée ajoute une possibilité à ta vie. Choisis une nouvelle version accessible.',
                     'Jedes abgeschlossene Erlebnis erweitert deine Möglichkeiten. Wähle eine neue, machbare Variante.'),language)
        goal=tr(('Long-term direction: keep exploring different experiences at your own pace.',
                 'Objetivo a longo prazo: continuar a explorar experiências diferentes ao teu ritmo.',
                 'Cap à long terme : continuer à explorer des expériences variées à ton rythme.',
                 'Langfristige Richtung: Entdecke weiter unterschiedliche Erlebnisse in deinem Tempo.'),language)
    else:
        unit=tr(UNITS.get(focus,('minutes','minutos','minutes','Minuten') if focus in MINUTE_FOCUSES else ('actions','ações','actions','Aktionen')),language)
        if f['completed']:
            progress=tr(('First completed target: {first} → latest completed: {latest} {unit}. Next quest: {next} {unit}.',
                         'Primeiro objetivo concluído: {first} → último: {latest} {unit}. Próxima missão: {next} {unit}.',
                         'Premier objectif terminé : {first} → dernier : {latest} {unit}. Prochaine quête : {next} {unit}.',
                         'Erstes abgeschlossenes Ziel: {first} → zuletzt: {latest} {unit}. Nächste Quest: {next} {unit}.'),language).format(**f,unit=unit)
        else:
            progress=tr(('Your first quest starts at {next} {unit}. Complete it to begin your personal history.',
                         'A primeira missão começa em {next} {unit}. Conclui-a para começares o teu histórico.',
                         'Ta première quête commence à {next} {unit}. Termine-la pour commencer ton parcours.',
                         'Deine erste Quest beginnt bei {next} {unit}. Schließe sie ab, um deinen Verlauf zu starten.'),language).format(**f,unit=unit)
        goal=tr(('Long-term milestone: {goal} {unit} per quest, then maintain a pace that suits you.',
                 'Marco a longo prazo: {goal} {unit} por missão; depois mantém um ritmo adequado a ti.',
                 'Étape à long terme : {goal} {unit} par quête, puis garder un rythme adapté.',
                 'Langfristiger Meilenstein: {goal} {unit} pro Quest; danach ein Tempo halten, das zu dir passt.'),language).format(**f,unit=unit)
        if f['latest'] and f['latest']>=f['goal']:
            goal=tr(('You have reached this track’s current milestone. Focus on sustainable repetition and variety.',
                     'Atingiste o marco atual deste hábito. Dá prioridade à repetição sustentável e à variedade.',
                     'Tu as atteint l’étape actuelle de cette activité. Privilégie la régularité durable et la variété.',
                     'Du hast den aktuellen Meilenstein erreicht. Konzentriere dich auf machbare Wiederholung und Vielfalt.'),language)
    stage=tr(('Start small: discover what fits your routine.','Começa devagar: descobre o que combina com a tua rotina.','Commence petit : découvre ce qui te convient.','Beginne klein: Finde heraus, was in deinen Alltag passt.'),language) if not f['completed'] else tr(('You are building your own practice. Your next target follows your recorded progress.','Estás a construir a tua prática. O próximo objetivo segue o progresso registado.','Tu construis ta pratique. Ton prochain objectif suit tes progrès enregistrés.','Du baust deine eigene Praxis auf. Dein nächstes Ziel folgt deinem erfassten Fortschritt.'),language)
    if f['completed']>=5:
        stage=tr(('You now have a growing practice history. Focus on quality, variety and a pace you can keep returning to.',
                  'Já tens um histórico de prática a crescer. Dá prioridade à qualidade, variedade e a um ritmo sustentável.',
                  'Ton historique de pratique grandit. Privilégie la qualité, la variété et un rythme durable.',
                  'Dein Übungsverlauf wächst. Achte auf Qualität, Vielfalt und ein Tempo, zu dem du zurückkehren kannst.'),language)
    return [purpose,progress,goal,stage]
