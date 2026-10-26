import unittest

from text_utils import spellcheck, get_language, parse_spellchecker_output


class SpellcheckerTests(unittest.TestCase):
    def test_1(self) -> None:
        text = """Il generale passò tutta la notte successiva ad allestire le difese della città, in vista dell'assedio nemico che sarebbe cominciato il giorno successivo.
Tuttavia in alcune circostanze l'uomo può anticipare la fine della sua vita De Senectute, Milano, BUR Rizzoli, 1958, paragrafi 72-73.
; i personaggi femminili che si trovano in questi romanzi sono ancora tutti perennemente in cerca di un marito.
Questa voce raccoglie le informazioni riguardanti la VakıfBank Güneş Sigorta Spor Kulübü nella stagione 2009-2010.
Eracle, punito per la sua pazzia, dovette sottostare a dodici prove, che una volta superate l'avrebbero aperto la strada per l'
Sulla sinistra vediamo Domenico inginocchiato di fronte ai due santi ricevere il bastone e il libro.
Secondo un accordo i primi passarono sotto il controllo della Giunta, i secondi del Consiglio.
Nel 1999 MTV lo inserì al tredicesimo posto tra i peggiori video mai realizzati.
La struttura del bacino è molto complessa e di grande valore economico in quanto contiene grandi riserve petrolifere molto sfruttate.
Infine, occorre astenersi dal giocare nuovamente dopo una vincita, giacché ciò ha l'effetto inverso a quello della martingala: aumentare la probabilità della perdita.
Ironicamente, in un altro componimento poetico, Dues gentils donzellas say que•z an, Guillem difende il suo amore per una ragazza ventiduenne, mentre Joan Berenguer esprime una preferenza per le ventenni.
Ha fatto parte dei Second Opinion (insieme a Cone) e dei Norman.
A 5,85 entrambi sbagliano la prima prova; ripetono l'errore alla seconda.
scappatoia
Anche i continui inserimenti ed estrazioni possono alla lunga causare problemi ai piedini, soprattutto se le suddette operazioni sono condotte da persone senza specifiche attrezzature (estrattori) oppure con poca esperienza nel maneggiare integrati.
contengono
Simmetrico, in quanto dall'esterno il corsetto è quasi perfettamente simmetrico per ottenere una bassa visibilità e il teorico buon aspetto corporeo.
Spesso Carson coglie l'occasione per punzecchiare il figlioccio in proposito, apostrofandolo con "giovane gaudente" o simili epiteti.
Nella fortezza di Harrenhal, intanto, lo strano rapporto tra Tywin Lannister e Arya continua ad intensificarsi.
La varietà del clima, la presenza di altopiani e la qualità dei terreni ingranditi, sono all'origine di una produzione agricola estremamente diversificata, che unisce coltivazioni tropicali a coltivazioni di climi temperati.
        """.strip()
        gotool = """SpellChecker v0.9.1a
Language is ita (confidence: 55.8)

Invalid word: '72-73'

Invalid word: '2009-2010'

Invalid word: 'l''
""".strip()

        language, confidence = get_language(text)
        result = spellcheck(text, language, confidence)
        self.assertListEqual(parse_spellchecker_output(result), parse_spellchecker_output(gotool))

    def test_2(self) -> None:
        text = '''Rilasciata il 27 giugno 2014, questa voce è portata per il genere rock rispetto alla voce originale.
Queste cinture vulcaniche sono chiamate catene vulcaniche.
Entrato giovanissimo in magistratura, vi rimase fino al 1933, quando divenne ordinario di diritto e procedura penale presso l'
Secondo il criterio rappresentato nella prima carta si includono nell'Europa centrale (indicata con il colore azzurro) Polonia, Repubblica Ceca, Slovacchia, Ungheria, Liechtenstein, Austria, Slovenia, Germania.
Nell'ultimo turno, Green Bay ospitò i Lions con in palio la vittoria di division, vincendo per 30-20.
Il più controverso degli studi di Ivanov è il suo tentativo di creare un ibrido uomo-scimmia.
fornitogli
La durabilità dei motori fu compromessa e la società soffrì di questa perdita di reputazione.
Hernández
tasti'''.strip()
        gotool = """SpellChecker v0.9.1a
Language is ita (confidence: 36.5)

Invalid word: 'l''

Invalid word: '30-20'
""".strip()

        language, confidence = get_language(text)
        result = spellcheck(text, language, confidence)
        self.assertListEqual(parse_spellchecker_output(result), parse_spellchecker_output(gotool))

    def test_3(self) -> None:
        text = '''L'équipage « Cap Sport » emmené par Bernard Mallaret et Xavier Lecœur remporte la course.
Le parcours de la Rhosnes forme de nombreux méandres à partir d'
Elles ont donc probablement été réalisées moyennant une reprise en sous-œuvre du mur gouttereau sud de la nef, ce qui a permis de conserver sa charpente, sans doute déjà refaite quelque temps auparavant.
Ce dernier avait la volonté de découvrir de jeunes talents et de leur ouvrir les portes du monde littéraire.
Une fois l'affaire réglée, les spartiates démarrent la construction d'une tranchée défensive parallèle au camp de Pyrrhus.
Installée dans un bâtiment de 4 étages et ², cette fabrique fait travailler plus de 250 ouvriers, la plupart des artisans spécialisés, qui réalisent toutes les malles Moynat.
Le safarbarlik (en ) désigne la politique de conscription mise en place dans l'
Le lendemain, Bond et Reiko vont rendre visite au cousin de l'ex petit ami de Mayumi (Takuya Abo) et lui posent des questions.
Martos est notamment un patronyme hispanique.'''.strip()
        gotool = """SpellChecker v0.9.1a
Language is fra (confidence: 42.5)

Invalid word: 'd''

Invalid word: '²'

Invalid word: 'l''""".strip()

        language, confidence = get_language(text)
        result = spellcheck(text, language, confidence)
        self.assertListEqual(parse_spellchecker_output(result), parse_spellchecker_output(gotool))

    def test_4(self) -> None:
        text = '''A pithos is a very large jar, usually made of rough-grained terra cotta, used for storage.
Dunham's television debut came in 1976 when the still prepubescent performer caught the attention of Dallas reporters like Bill O'Reilly, who interviewed Dunham for a local news story.
He was a Minister of the Navy in the 1970s, and President of the NATO Assembly in the 1980s.
This, with commercial launch vehicles (
It was also made into the story 'The Reluctant Dragon' by Ken Ransom, which was made into a Disney film.
Contemporary graphic designs tends to feature modern geometric forms and shapes and bold typefaces.
Dippers are a group of perching birds whose habitat includes aquatic environments in the Americas, Europe and Asia.
This makes distant objects look blurry.
The R46 was the second order of 75-foot cars to be ordered for the New York City Subway, after the R44s.
element
The flight, carried on a Boeing 727-86, was making a flight from Mashad Airport to Tehran-Mehrabad Airport in Iran.
Ján Kollár was a representative of the Panslavism ideology.
There are 37 million speakers in Ukraine.
These rules describe what composers of the past did, rather than telling composers of today what to do -- in fact, music composed today can have completely different rules than the music of the past.
Complex objects may by themselves be modular and used to create even more complex objects by piecing them together.
In the mid 1900s, people were buying less tobacco, so Durham became poorer.
A twist for this season sent one player from the tribe winning reward to steal one item from the other tribe's camp.
Another well-known orchestral work is Three Places in New England.
Kaia Wilson'''.strip()
        gotool = """SpellChecker v0.9.1a
Language is eng (confidence: 47.7)

Invalid word: ''The'
Did you mean one of: 'Othe', 'Tthe', '‘the', '‘thee', '‬The'?

Invalid word: 'Dragon''

Invalid word: '727-86'

Invalid word: '--'""".strip()

        language, confidence = get_language(text)
        result = spellcheck(text, language, confidence)
        self.assertListEqual(parse_spellchecker_output(result), parse_spellchecker_output(gotool))

    def test_5(self) -> None:
        text = '''Qabel l-1999 u l-Kampjonati Ewropej 2000, l-istadju kien magħruf bħala Olympiastadion, l-Istadju Olimpiku bl-Olandiż, u kellu 18,000 siġġu.
Perjodu minn nofs Mejju sa nofs Lulju meta l-għabex jista’ jdum il-lejl kollu.
L-ewwel legs intlagħbu fit-30 u l-31 ta' Lulju, u t-tieni legs intlagħbu fis-6 u s-7 ta' Awwissu 2013.
Fis-sena 2000, ir-rivalità reġgħet tkebbset wara d-deċiżjoni kontroversajli ta' Luís Figo li jħalli lil Barça biex jingħaqad ma' Real Madrid.
Fl-1977, meta l-Uffiċju tal-Prim Ministru ħareġ ċirkolari li stqarr li avolja l-Gvern kien jirrikonoxxi d-dritt tal-ħaddiema għall-istrajk, id-dritt għall-azzjonijiet industrijali parzjali ma kienux ser jibqgħu rikonoxxuti.
Marques
L-Eritrea (Ge'ez: ኤርትራ ʾErtrā ; Għarbi: إرتريا  Iritrijá ), huwa pajjiż li jinsab fil-"qarn" tal-
ċereali
Xi 65 wara, it-Teatru Rjal reġa’ kellu xorti ħażina ferm: It-Tlieta filgħaxija, is-7 ta’ April 1942, it-teatru nqered mill-bumbardamenti tal-inġenji tal-ajru tat-tip Luftwaffe.
mill-Inkjesta
Fl-1937 issieħeb ma' SK Jugoslavija fejn lagħab sal-1938 meta ssieħeb ma' BASK.
Fi Troas Pawlu jiltaqa’ ma’ Luqa, li kien jaf tajjeb il-Maċedonja u l-Greċja u jsir kollaboratur tieghu.'''.strip()
        gotool = """SpellChecker v0.9.1a
Language is mlt (confidence: 32.6)

Invalid word: 'ta''

Invalid word: 'ta''

Invalid word: 'ta''

Invalid word: 'ma''

Invalid word: 'ኤርትራ'

Invalid word: 'إرتريا'

Invalid word: 'ma''

Invalid word: 'ma''""".strip()

        language, confidence = get_language(text)
        result = spellcheck(text, language, confidence)
        self.assertListEqual(parse_spellchecker_output(result), parse_spellchecker_output(gotool))
