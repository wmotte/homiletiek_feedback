# Homiletiek Feedback
## Systematische feedback op preken

### Het belang van feedback voor voorgangers

Preken is het centrale ambacht van het predikantschap. Een dominee die niet kan preken is, zoals Dr. W.M. Dekker het formuleert, "als een fietsenmaker die het wiel van de fiets niet goed monteert." Toch is het opvallend hoe weinig structurele, inhoudelijk-theologische feedback voorgangers ontvangen op hun preken.

Na een eredienst krijgt een predikant vaak algemene complimenten ("mooie preek") of praktische opmerkingen ("te lang"), maar zelden een grondige theologische analyse:
- Was de uitleg van de Schrift adequaat?
- Kwam de toepassing voldoende concreet?
- Werd de hoorder werkelijk in de tekst getrokken?
- Was Christus het telos van de preek?

**Structurele feedback is essentieel** voor de groei van elke voorganger. Net zoals een kunstenaar zijn werk laat recenseren of een wetenschapper zijn publicatie aan peer review onderwerpt, zo verdient ook de prediking systematische evaluatie aan de hand van heldere criteria.

Dit project biedt een hulpmiddel voor die evaluatie door te illustreren hoe een grondige, professionele *feedback loop* zou kunnen functioneren.

---

### Wat doet dit project?

Dit project analyseert preken systematisch aan de hand van de **acht thesen** die Dr. Willem Maarten Dekker formuleerde in zijn artikel **"Wat is een preek? Thesen"** (*In de Waagschaal*, nr. 2, 8 februari 2025).
Er zijn vele manieren om preken te analyseren, maar deze thesen zijn gekozen omdat ze preek geïsoleerd benaderen. 
Meer contextuele theologische analyses vragen ook om het meenemen van situationele informatie, de inhoud van de gebeden en liederen, etc. 

De huidige analyse gebeurt met behulp van een Large Language Model, die de preektekst beoordeelt op:

1. **Specifiek Bijbelgedeelte** - Ligt één specifieke pericoop ten grondslag?
2. **Exegese** - Is er adequate uitleg van de oorspronkelijke context?
3. **Toepassing** - Is de actualisering concreet en niet algemeen?
4. **Verwevenheid** - Zijn uitleg en toepassing met elkaar verweven?
5. **Drie stukken** - Zijn ellende, verlossing en dankbaarheid aanwezig?
6. **Twee wegen** - Wordt de ernst van de menselijke keuze zichtbaar?
7. **Christocentrisch** - Is Christus het telos van de preek?
8. **Diepgang en lengte** - Duurt de preek minimaal 20 minuten?

Elke these krijgt een score (1-10), onderbouwing met letterlijke citaten uit de preek, bevindingen en concrete verbeterpunten.

**Artikel online:** Het volledige artikel van Dekker is te lezen op [In de Waagschaal](https://indewaagschaal.nl) en is opgenomen in de repository onder `misc/wat_is_een_preek_dekker.md`.

---

### Voorbeelden

In de map `input/` staan **twee eigen voorbeeldpreken**, ambachtelijk geschreven door W.M. Otte:
- `voorbeeld_31_maart_2024_Otte.txt` (Paasmaandag)
- `voorbeeld_5_mei_2025_Otte.txt` (Zondag na Hemelvaart)

Deze preken zijn geanalyseerd met het systeem. De resultaten staan in `outputs/` als JSON-bestanden met gedetailleerde feedback per criterium.

---

### Projectstructuur

```
homiletiek_feedback/
├── README.md                          # Dit bestand
├── analyze_sermon_dekker.py           # Hoofdscript voor analyse
├── .env                               # API-sleutel configuratie (niet in git)
├── input/                             # Preekteksten (*.txt)
│   ├── voorbeeld_31_maart_2024_Otte.txt
│   └── voorbeeld_5_mei_2025_Otte.txt
├── outputs/                           # Analyse-resultaten (*.json)
├── prompts/                           # LLM prompt met Dekker-criteria
│   └── analyze_sermon_dekker.md
├── misc/                              # Achtergronddocumentatie
│   └── wat_is_een_preek_dekker.md     # Volledige tekst van het artikel
└── technical/                         # Hulpscripts
```

---

### Installatie & gebruik

#### 1. Vereisten
- Python 3.8+
- Google Gemini API-sleutel ([verkrijg hier](https://ai.google.dev/))

#### 2. Installeer dependencies
```bash
pip install google-generativeai python-dotenv
```

#### 3. Configureer API-sleutel
Maak een `.env` bestand in de hoofdmap:
```
GEMINI_API_KEY=jouw_api_sleutel_hier
```

#### 4. Voer een analyse uit
```bash
python analyze_sermon_dekker.py --i input/voorbeeld_31_maart_2024_Otte.txt
```

Of gebruik de standaard input:
```bash
python analyze_sermon_dekker.py
```

#### 5. Bekijk de resultaten
Het script genereert een JSON-bestand in `outputs/` met:
- Metadata (geschatte lengte, tijdsduur)
- Score per criterium (1-10)
- Bevindingen met letterlijke quotes uit de preek
- Verbeterpunten
- Algehele beoordeling

---

### Belangrijke opmerkingen

**Liturgische vereiste:** Het script vereist dat de **schriftlezingen bovenaan de preektekst** staan. Zonder deze context kan de analyse niet plaatsvinden.

**Taal:** De feedback wordt gegenereerd in het Nederlands.

**Tone of voice:** De feedback is professioneel, theologisch inhoudelijk, opbouwend maar scherp - passend bij de ernst van het preekambacht.

**Tijdsberekening:** Het script rekent met 110 woorden per minuut spreektijd.

---

### Achtergrond: De thesen van Dekker (3-2-1-regel)

Dekker vat de inhoudelijke kern van de preek samen in de **3-2-1-regel**:

**3 stukken:** Ellende, verlossing en dankbaarheid (Heidelbergse Catechismus)
**2 wegen:** De smalle weg ten leven, de brede weg ten verderve
**1 Heer:** Christus als telos van de preek

Deze regel bewaart de prediking tegen zowel te objectieve als te subjectieve uitwassen en zorgt ervoor dat de mens als verantwoordelijk wezen én God als genadige Heer beide volledig ter sprake komen.

---

### Verantwoording

Dit project is ontwikkeld als een **prototype voor theologische feedbacksystemen**. Het vervangt geen menselijke, pastorale begeleiding, maar kan dienen als:
- Eerste zelfevaluatie voor voorgangers
- Objectieve second opinion naast collegiaal overleg
- Hulpmiddel voor homiletisch onderwijs

De twee voorbeeldpreken zijn geschreven door W.M. Otte en dienen als demonstratie van het systeem.

---

### Bronnen

Dekker, W.M. (2025). "Wat is een preek? Thesen." *In de Waagschaal*, nr. 2, 8 februari 2025.
