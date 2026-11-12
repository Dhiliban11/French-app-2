"""
================================================================================
EXPLORER QUEST: LYON EDITION (Édition Lyon)
Lead Python Developer & UI/UX Architect Build
Stack: Streamlit | Google GenAI (`google-genai`) | SQLite3 | ReportLab | Pillow
================================================================================
"""

import os
import io
import json
import uuid
import base64
import sqlite3
from datetime import date, datetime
from typing import Dict, List, Any, Optional

import streamlit as st
from PIL import Image

# LOGIC: Import ReportLab components for multi-theme styled PDF Album generation
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader, simpleSplit

# LOGIC: Import Google GenAI SDK with graceful fallback if not installed
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# ==============================================================================
# 1. APPLICATION CONSTANTS & CONFIGURATION
# ==============================================================================

# LOGIC: Core file paths and Lyon default GPS coordinates
DB_PATH = "explorer_lyon.db"
PHOTO_DIR = "explorer_photos"
LYON_DEFAULT_LAT = 45.7640
LYON_DEFAULT_LON = 4.8357

# LOGIC: Scoring and Explorer Tier thresholds
RIDDLE_POINTS = 50
QUEST_POINTS = 200

EXPLORER_TIERS = [
    {"name": "Rookie Explorer", "fr": "Explorateur Débutant", "min_pts": 0, "badge": "🧭"},
    {"name": "Adventurer", "fr": "Aventurier du Rhône", "min_pts": 200, "badge": "⚔️"},
    {"name": "Elite Explorer", "fr": "Explorateur d'Élite", "min_pts": 500, "badge": "🏛️"},
    {"name": "Premium Legend", "fr": "Légende de Lugdunum", "min_pts": 900, "badge": "👑"},
]

# UI EDITING: 10 Custom Google Fonts mapped to web CSS families and safe PDF fonts
CUSTOM_FONTS: Dict[str, Dict[str, str]] = {
    "Cinzel": {
        "css": "'Cinzel', serif",
        "pdf_title": "Times-Bold",
        "pdf_body": "Times-Roman",
        "vibe": "Classical Roman & Cathedral Stone",
    },
    "Playfair Display": {
        "css": "'Playfair Display', serif",
        "pdf_title": "Times-BoldItalic",
        "pdf_body": "Times-Roman",
        "vibe": "French Editorial & Haute Couture",
    },
    "Space Grotesk": {
        "css": "'Space Grotesk', sans-serif",
        "pdf_title": "Helvetica-Bold",
        "pdf_body": "Helvetica",
        "vibe": "Modern Architectural Geometry",
    },
    "Caveat": {
        "css": "'Caveat', cursive",
        "pdf_title": "Times-Italic",
        "pdf_body": "Times-Italic",
        "vibe": "Handwritten Field Notes",
    },
    "Lobster": {
        "css": "'Lobster', cursive",
        "pdf_title": "Times-BoldItalic",
        "pdf_body": "Helvetica",
        "vibe": "Vintage Bistro Signage",
    },
    "Montserrat": {
        "css": "'Montserrat', sans-serif",
        "pdf_title": "Helvetica-Bold",
        "pdf_body": "Helvetica",
        "vibe": "Clean Contemporary Travelogue",
    },
    "Pacifico": {
        "css": "'Pacifico', cursive",
        "pdf_title": "Times-BoldItalic",
        "pdf_body": "Helvetica",
        "vibe": "Postcard & Riviera Leisure",
    },
    "Oswald": {
        "css": "'Oswald', sans-serif",
        "pdf_title": "Helvetica-Bold",
        "pdf_body": "Helvetica",
        "vibe": "Bold Expedition Headlines",
    },
    "Syne": {
        "css": "'Syne', sans-serif",
        "pdf_title": "Helvetica-Bold",
        "pdf_body": "Helvetica",
        "vibe": "Avant-Garde Confluence Art",
    },
    "Special Elite": {
        "css": "'Special Elite', monospace",
        "pdf_title": "Courier-Bold",
        "pdf_body": "Courier",
        "vibe": "Secret Traboule Typewriter Dossier",
    },
}

# UI EDITING: 10 Album Visual Themes with synchronized Web CSS and ReportLab PDF palettes
ALBUM_THEMES: Dict[str, Dict[str, str]] = {
    "Vintage Map": {
        "bg": "#F4ECD8",
        "card_bg": "#FAF4E6",
        "text": "#3B2F2F",
        "accent": "#8B4513",
        "secondary": "#C19A6B",
        "border": "2px dashed #8B4513",
        "tag": "Cartographie Ancienne",
    },
    "Cyberpunk Neon": {
        "bg": "#0D0221",
        "card_bg": "#190B36",
        "text": "#F0F8FF",
        "accent": "#00F5D4",
        "secondary": "#FF007F",
        "border": "2px solid #00F5D4",
        "tag": "Lumières Futuristes",
    },
    "Minimalist Journal": {
        "bg": "#FFFFFF",
        "card_bg": "#F8F9FA",
        "text": "#1A1A1A",
        "accent": "#495057",
        "secondary": "#ADB5BD",
        "border": "1px solid #DEE2E6",
        "tag": "Épure Contemporaine",
    },
    "Golden Hour": {
        "bg": "#FFF3E0",
        "card_bg": "#FFE0B2",
        "text": "#4E342E",
        "accent": "#E65100",
        "secondary": "#FFB300",
        "border": "2px solid #FB8C00",
        "tag": "Crépuscule sur la Saône",
    },
    "Editorial Magazine": {
        "bg": "#F7F5F0",
        "card_bg": "#FFFFFF",
        "text": "#111111",
        "accent": "#9E2A2B",
        "secondary": "#D4A373",
        "border": "3px double #111111",
        "tag": "Revue Lyonnaise",
    },
    "Retro Stamp": {
        "bg": "#EFE6D5",
        "card_bg": "#FFFDF9",
        "text": "#2B3A42",
        "accent": "#C0392B",
        "secondary": "#2980B9",
        "border": "3px dotted #C0392B",
        "tag": "Carte Postale 1950",
    },
    "Dark Elegance": {
        "bg": "#121212",
        "card_bg": "#1E1E24",
        "text": "#EAE0D5",
        "accent": "#D4AF37",
        "secondary": "#8C7853",
        "border": "2px solid #D4AF37",
        "tag": "Nocturne Soie & Or",
    },
    "Pop Art": {
        "bg": "#FFF200",
        "card_bg": "#FFFFFF",
        "text": "#000000",
        "accent": "#FF1E56",
        "secondary": "#00A8E8",
        "border": "3px solid #000000",
        "tag": "Couleurs Vives",
    },
    "Botanical Travel": {
        "bg": "#EDF3EC",
        "card_bg": "#F9FCF8",
        "text": "#1E352F",
        "accent": "#2D6A4F",
        "secondary": "#74C69D",
        "border": "2px solid #52B788",
        "tag": "Parc de la Tête d'Or",
    },
    "Classic Blueprint": {
        "bg": "#0F2C59",
        "card_bg": "#163A70",
        "text": "#F8F9FA",
        "accent": "#90E0EF",
        "secondary": "#48CAE4",
        "border": "2px dashed #90E0EF",
        "tag": "Architecture & Plans",
    },
}


# ==============================================================================
# 2. CURATED LYON FALLBACK DATA (OFFLINE-READY ARCHIVE)
# ==============================================================================

# LOGIC: Iconic Lyon Landmarks for the Interactive Location Hub
LYON_LANDMARKS = [
    {
        "name_fr": "Basilique Notre-Dame de Fourvière",
        "name_en": "Basilica of Notre-Dame de Fourvière",
        "district": "Fourvière (5e)",
        "lat": 45.7623,
        "lon": 4.8226,
        "category": "History & Architecture",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Basilique_Notre-Dame_de_Fourvi%C3%A8re_Lyon.jpg/800px-Basilique_Notre-Dame_de_Fourvi%C3%A8re_Lyon.jpg",
        "desc_fr": "Surnommée l'éléphant renversé, cette basilique romano-byzantine domine Lyon depuis la colline qui prie.",
        "desc_en": "Nicknamed the 'upside-down elephant', this Romano-Byzantine basilica crowns Lyon from the 'hill that prays'.",
    },
    {
        "name_fr": "Les Traboules du Vieux Lyon",
        "name_en": "Secret Traboule Passages of Old Lyon",
        "district": "Saint-Jean (5e)",
        "lat": 45.7629,
        "lon": 4.8273,
        "category": "Cool Facts & Secret Passages",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Cour_des_Voraces_Lyon.jpg/800px-Cour_des_Voraces_Lyon.jpg",
        "desc_fr": "Passages couverts reliant les rues à travers les cours Renaissance, utilisés jadis par les Canuts et la Résistance.",
        "desc_en": "Hidden covered passageways threading through Renaissance courtyards, once used by silk weavers and Resistance fighters.",
    },
    {
        "name_fr": "Place Bellecour & Presqu'île",
        "name_en": "Bellecour Square & The Peninsula",
        "district": "Presqu'île (2e)",
        "lat": 45.7578,
        "lon": 4.8320,
        "category": "History & Urbanism",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Place_Bellecour_Lyon_2019.jpg/800px-Place_Bellecour_Lyon_2019.jpg",
        "desc_fr": "L'une des plus grandes places piétonnes d'Europe, nichée entre le Rhône et la Saône autour de Louis XIV.",
        "desc_en": "One of Europe's largest pedestrian squares, nestled between the Rhône and Saône rivers around Louis XIV's statue.",
    },
    {
        "name_fr": "Musée des Confluences",
        "name_en": "Confluences Science & Anthropology Museum",
        "district": "La Confluence (2e)",
        "lat": 45.7329,
        "lon": 4.8183,
        "category": "Modern Architecture",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Mus%C3%A9e_des_Confluences_-_Lyon.jpg/800px-Mus%C3%A9e_des_Confluences_-_Lyon.jpg",
        "desc_fr": "Nuage de cristal et d'acier posé à la rencontre exacte des fleuves Rhône et Saône.",
        "desc_en": "A deconstructivist cloud of crystal and steel poised at the exact meeting point of the Rhône and Saône rivers.",
    },
    {
        "name_fr": "Parc de la Tête d'Or",
        "name_en": "Golden Head Park & Botanical Conservatory",
        "district": "6e Arrondissement",
        "lat": 45.7772,
        "lon": 4.8552,
        "category": "Nature & Heritage",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Serres_du_parc_de_la_T%C3%AAte_d%27Or.jpg/800px-Serres_du_parc_de_la_T%C3%AAte_d%27Or.jpg",
        "desc_fr": "Plus grand parc urbain de France avec son lac, sa roseraie internationale et ses serres monumentales du XIXe siècle.",
        "desc_en": "France's largest urban park featuring a boating lake, international rose garden, and monumental 19th-century glasshouses.",
    },
    {
        "name_fr": "Théâtre Antique de Lugdunum",
        "name_en": "Ancient Roman Theatre of Lugdunum",
        "district": "Fourvière (5e)",
        "lat": 45.7597,
        "lon": 4.8197,
        "category": "Roman History",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Th%C3%A9%C3%A2tre_antique_de_Fourvi%C3%A8re_Lyon.jpg/800px-Th%C3%A9%C3%A2tre_antique_de_Fourvi%C3%A8re_Lyon.jpg",
        "desc_fr": "Construit en 15 av. J.-C. sous Auguste, cœur de la capitale des Trois Gaules.",
        "desc_en": "Built in 15 BC under Emperor Augustus, heart of the Roman capital of the Three Gauls.",
    },
]

# LOGIC: Deep cultural dossier categories for Lyon Location Hub
FALLBACK_LYON_GUIDE = {
    "Histoire (Fourvière & Presqu'île) | History": {
        "summary_fr": "Fondée en 43 av. J.-C. sous le nom de Lugdunum sur la colline de Fourvière, Lyon fut la capitale des Trois Gaules. À la Renaissance, la ville s'étendit vers la Saône (Vieux Lyon) puis sur la Presqu'île, devenant la capitale européenne de l'imprimerie et de la soie.",
        "summary_en": "Founded in 43 BC as Lugdunum atop Fourvière Hill, Lyon served as the capital of the Three Gauls. During the Renaissance, it expanded along the Saône (Vieux Lyon) and across the Presqu'île peninsula, becoming Europe's hub for silk weaving and printing.",
        "highlights": [
            "43 BC: Lucius Munatius Plancus founds Roman colony Lugdunum.",
            "1536: King François I grants Lyon a silk-weaving monopoly, creating the Canut guild.",
            "1831 & 1834: Historic Canut silk-worker uprisings on Croix-Rousse hill.",
            "1943: Jean Moulin unifies the French Resistance in Lyon (Caluire & Traboules).",
        ],
    },
    "Secrets & Traboules | Cool Facts": {
        "summary_fr": "Le mot 'traboule' vient du latin 'trans ambulare' (traverser). Lyon compte plus de 400 traboules cachées derrière de lourdes portes en bois dans le Vieux Lyon et la Croix-Rousse, permettant aux soyeux de transporter leurs étoffes à l'abri de la pluie.",
        "summary_en": "Derived from Latin 'trans ambulare' (to walk through), Lyon hides over 400 secret traboule passageways behind unassuming wooden doors in Vieux Lyon and Croix-Rousse, originally designed to shield delicate silk bolts from rain.",
        "highlights": [
            "La Longue Traboule (54 Rue Saint-Jean to 27 Rue du Bœuf) crosses four separate buildings.",
            "La Cour des Voraces in Croix-Rousse boasts a monumental six-story open stone staircase.",
            "Lyon has two rivers: locals say the Rhône is masculine & turbulent, while the Saône is feminine & tranquil.",
            "Cinema was invented in Lyon in 1895 by Auguste and Louis Lumière on Rue du Premier-Film.",
        ],
    },
    "Architecture & Fresques | Architecture": {
        "summary_fr": "Inscrit au patrimoine mondial de l'UNESCO, Lyon superpose 2 000 ans d'urbanisme : amphithéâtres romains, cours gothiques et Renaissance à galeries italiennes, immeubles haussmanniens de la Presqu'île, et audace contemporaine à la Confluence.",
        "summary_en": "A UNESCO World Heritage site, Lyon layers 2,000 years of architecture: Roman amphitheaters, Italianate Renaissance loggias, Haussmannian Presqu'île boulevards, and avant-garde buildings at La Confluence.",
        "highlights": [
            "Tour Rose (16 Rue du Bœuf): Iconic ochre spiral staircase tower in Vieux Lyon.",
            "Opéra Nouvel: Jean Nouvel's glass barrel-vault crowning a 19th-century neoclassical facade.",
            "Mur des Canuts: Europe's largest trompe-l'œil mural (1,200 m²) in Croix-Rousse.",
            "Hôtel-Dieu: Monumental 18th-century riverfront dome designed by Jacques-Germain Soufflot.",
        ],
    },
    "Bouchons Lyonnais | Top Gastronomy": {
        "summary_fr": "Célèbre critique culinaire Curnonsky sacra Lyon 'Capitale mondiale de la gastronomie' en 1935. Les authentiques Bouchons Lyonnais servent une cuisine conviviale autour de nappes à carreaux rouges et blancs.",
        "summary_en": "Famed food critic Curnonsky crowned Lyon 'World Capital of Gastronomy' in 1935. Certified Bouchons Lyonnais serve hearty heritage dishes on red-and-white checkered tablecloths.",
        "highlights": [
            "Café Comptoir Abel (Est. 1928) — Legendary Quenelle de Brochet sauce Nantua.",
            "Daniel et Denise (Créqui / Saint-Jean) — Run by Meilleur Ouvrier de France Joseph Viola; famous Pâté-Croûte.",
            "Le Musée (Rue des Forces) — Historic wood-paneled bouchon with theatrical storytelling.",
            "Les Halles de Lyon Paul Bocuse — Indoor gourmet temple for Saint-Marcellin cheese & Rosette sausage.",
        ],
    },
    "Fête des Lumières | Festivals": {
        "summary_fr": "Chaque année autour du 8 décembre, Lyon s'illumine pendant quatre nuits magiques. Née en 1852 lorsque les Lyonnais posèrent des lumignons à leurs fenêtres pour remercier la Vierge Marie, la Fête des Lumières attire aujourd'hui des millions de visiteurs.",
        "summary_en": "Every December around the 8th, Lyon transforms into an open-air light museum for four nights. Originating in 1852 when residents lit candles ('lumignons') on windowsills to honor the Virgin Mary, the Festival of Lights now draws millions.",
        "highlights": [
            "December 8 Tradition: Every window sill glows with small colored glass candle holders (lumignons).",
            "Place des Terreaux & Basilica of Fourvière host monumental 3D projection mapping.",
            "Nuits Sonores (May): Electronic music & digital arts festival across industrial spaces.",
            "Nuits de Fourvière (June–July): Open-air concerts and theater inside the Roman amphitheater.",
        ],
    },
}

# LOGIC: 12 Location-Bound Lyon Riddles (50 pts each = 600 pts total)
FALLBACK_RIDDLES = [
    {
        "id": "R01",
        "spot": "Basilique de Fourvière",
        "question_fr": "Je domine Lyon depuis la 'colline qui prie'. Les Lyonnais me surnomment affectueusement un animal renversé les quatre pattes en l'air. Quel animal ?",
        "question_en": "I overlook Lyon from the 'hill that prays'. Locals affectionately nickname me an upside-down animal with four legs in the air. Which animal?",
        "hint": "Think of a large gray mammal with tusks, flipped onto its back (4 towers = 4 legs).",
        "answer": "elephant",
        "accepted": ["elephant", "éléphant", "l'éléphant", "an elephant"],
    },
    {
        "id": "R02",
        "spot": "Vieux Lyon & Croix-Rousse",
        "question_fr": "Mon nom vient du latin 'trans ambulare'. Je suis un passage secret reliant deux rues à travers des cours intérieures pour protéger la soie de la pluie. Que suis-je ?",
        "question_en": "My name comes from Latin 'trans ambulare'. I am a secret passageway linking two streets through courtyards to shield silk from rain. What am I?",
        "hint": "Starts with T and rhymes with 'caboule'.",
        "answer": "traboule",
        "accepted": ["traboule", "traboules", "une traboule", "a traboule"],
    },
    {
        "id": "R03",
        "spot": "Institut Lumière (Monplaisir)",
        "question_fr": "En 1895, deux frères lyonnais ont inventé le Cinématographe et tourné le premier film à la sortie de leur usine. Quel est leur nom de famille ?",
        "question_en": "In 1895, two Lyon brothers invented the Cinematograph and filmed workers leaving their factory. What is their surname?",
        "hint": "Their surname literally means 'Light' in French.",
        "answer": "lumiere",
        "accepted": ["lumiere", "lumière", "les frères lumière", "lumiere brothers"],
    },
    {
        "id": "R04",
        "spot": "Place des Terreaux",
        "question_fr": "Ma fontaine monumentale sur la Place des Terreaux représente un char tiré par quatre chevaux fougueux, sculptée par le créateur de la Statue de la Liberté. Qui est le sculpteur ?",
        "question_en": "My monumental fountain on Place des Terreaux depicts a chariot pulled by four fierce horses, sculpted by the creator of the Statue of Liberty. Who is the sculptor?",
        "hint": "Frédéric Auguste B...",
        "answer": "bartholdi",
        "accepted": ["bartholdi", "frederic auguste bartholdi", "auguste bartholdi"],
    },
    {
        "id": "R05",
        "spot": "Fourvière (Roman Era)",
        "question_fr": "Fondée en 43 av. J.-C., je fus la capitale romaine des Trois Gaules. Mon nom latin signifie 'Colline des Corbeaux' ou 'Colline du dieu Lug'. Quel est mon nom antique ?",
        "question_en": "Founded in 43 BC, I was the Roman capital of the Three Gauls. What was Lyon's ancient Roman name?",
        "hint": "Starts with Lugd...",
        "answer": "lugdunum",
        "accepted": ["lugdunum"],
    },
    {
        "id": "R06",
        "spot": "La Confluence",
        "question_fr": "Deux cours d'eau s'embrassent à la pointe sud de la Presqu'île : la calme Saône et un fleuve impétueux venu des Alpes. Quel est ce fleuve ?",
        "question_en": "Two waterways embrace at the southern tip of the Presqu'île: the calm Saône and a mighty river flowing from the Alps. Name this river.",
        "hint": "Starts with R and rhymes with 'zone'.",
        "answer": "rhone",
        "accepted": ["rhone", "rhône", "le rhône", "the rhone"],
    },
    {
        "id": "R07",
        "spot": "Vieux Lyon (Théâtre de Marionnettes)",
        "question_fr": "Créé en 1808 par Laurent Mourguet pour divertir les clients d'un arracheur de dents, je suis la célèbre marionnette lyonnaise coiffée d'un tricorne. Qui suis-je ?",
        "question_en": "Created in 1808 by Laurent Mourguet to distract dental patients, I am Lyon's famous hand puppet wearing a tricorn hat. Who am I?",
        "hint": "Starts with G and ends with -ol.",
        "answer": "guignol",
        "accepted": ["guignol"],
    },
    {
        "id": "R08",
        "spot": "La Croix-Rousse",
        "question_fr": "On m'appelle la 'colline qui travaille', par opposition à Fourvière la 'colline qui prie'. Quel était le nom des célèbres ouvriers de la soie qui y vivaient ?",
        "question_en": "I am called the 'hill that works', contrasting with Fourvière's 'hill that prays'. What were the famous silk weavers who lived here called?",
        "hint": "5 letters, starts with C: C_n_t.",
        "answer": "canuts",
        "accepted": ["canut", "canuts", "les canuts"],
    },
    {
        "id": "R09",
        "spot": "Bouchons Lyonnais",
        "question_fr": "Je suis une spécialité gastronomique lyonnaise ovale et moelleuse à base de brochet, servie nappée d'une onctueuse sauce Nantua aux écrevisses. Quel plat suis-je ?",
        "question_en": "I am a pillowy oval Lyon culinary specialty made from pike fish, served smothered in creamy crayfish Nantua sauce. What dish am I?",
        "hint": "Starts with Q: Q_en_lle.",
        "answer": "quenelle",
        "accepted": ["quenelle", "quenelles", "quenelle de brochet"],
    },
    {
        "id": "R10",
        "spot": "Toute la Ville (8 Décembre)",
        "question_fr": "Chaque 8 décembre, les Lyonnais déposent ces petits verres colorés contenant une bougie sur le rebord de leurs fenêtres. Comment les appelle-t-on ?",
        "question_en": "Every December 8th, Lyon residents place these small colored glass candle holders on their windowsills. What are they called?",
        "hint": "Derived from 'lumière', starts with L-u-m-i...",
        "answer": "lumignons",
        "accepted": ["lumignon", "lumignons", "des lumignons"],
    },
    {
        "id": "R11",
        "spot": "Boulevard de la Croix-Rousse",
        "question_fr": "Je suis un bloc erratique de quartzite gris-blanc transporté par un glacier alpin il y a 140 000 ans, devenu le symbole minéral de la Croix-Rousse. Quel est mon surnom ?",
        "question_en": "I am a massive glacial boulder carried from the Alps 140,000 years ago, now the beloved stone landmark of Croix-Rousse. What is my nickname?",
        "hint": "Literally 'The Big Pebble' in French.",
        "answer": "gros caillou",
        "accepted": ["gros caillou", "le gros caillou"],
    },
    {
        "id": "R12",
        "spot": "Collonges-au-Mont-d'Or & Les Halles",
        "question_fr": "Surnommé 'Monsieur Paul', ce chef étoilé légendaire a donné son nom aux célèbres Halles gastronomiques de Lyon. Quel est son nom de famille ?",
        "question_en": "Nicknamed 'Monsieur Paul', this legendary Michelin-starred chef gave his name to Lyon's iconic indoor food market. What is his surname?",
        "hint": "Paul B_c_se.",
        "answer": "bocuse",
        "accepted": ["bocuse", "paul bocuse"],
    },
]

# LOGIC: 3 Real-Life Photo Quests (200 pts each = 600 pts High Reward)
FALLBACK_QUESTS = [
    {
        "id": "Q01",
        "title_fr": "Le Passage Secret des Canuts",
        "title_en": "Locate a Hidden Traboule Passage",
        "desc_fr": "Trouvez une traboule authentique dans le Vieux Lyon (ex: 54 Rue Saint-Jean) ou la Croix-Rousse (Cour des Voraces), capturez une photo de sa cour intérieure et enregistrez vos coordonnées GPS.",
        "desc_en": "Locate an authentic hidden Traboule passage in Vieux Lyon (e.g., 54 Rue Saint-Jean) or Croix-Rousse (Cour des Voraces), capture a photo of its courtyard, and log your GPS coordinates.",
        "target_lat": 45.7629,
        "target_lon": 4.8273,
        "points": QUEST_POINTS,
    },
    {
        "id": "Q02",
        "title_fr": "Panorama depuis la Colline qui Prie",
        "title_en": "Fourvière Esplanade Skyline Capture",
        "desc_fr": "Montez jusqu'à l'esplanade de la Basilique Notre-Dame de Fourvière, photographiez la vue panoramique sur les toits de Lyon et les Alpes au loin, puis validez votre position.",
        "desc_en": "Ascend to the esplanade of Basilica Notre-Dame de Fourvière, capture a panoramic photo overlooking Lyon's rooftops and the distant Alps, and log your location.",
        "target_lat": 45.7623,
        "target_lon": 4.8226,
        "points": QUEST_POINTS,
    },
    {
        "id": "Q03",
        "title_fr": "L'Étreinte du Rhône et de la Saône",
        "title_en": "The Confluence River Tip Expedition",
        "desc_fr": "Rendez-vous à l'extrême pointe sud de la Presqu'île derrière le Musée des Confluences, photographiez le point de rencontre des deux fleuves et consignez votre découverte.",
        "desc_en": "Journey to the southernmost tip of the Presqu'île behind Musée des Confluences, capture a photo where the Rhône and Saône rivers merge, and log your discovery.",
        "target_lat": 45.7329,
        "target_lon": 4.8183,
        "points": QUEST_POINTS,
    },
]

# LOGIC: Real-World Lyon Coupon Store Catalog
COUPON_CATALOG = [
    {
        "id": "CPN-BOUCHON-01",
        "partner": "Bouchon Lyonnais Daniel et Denise",
        "category": "Gastronomie / Dining",
        "offer_fr": "Apéritif Kir Lyonnais + Pâté-Croûte Champion du Monde offert pour tout menu",
        "offer_en": "Complimentary Kir Lyonnais Aperitif & World-Champion Pâté-Croûte with any set menu",
        "cost": 150,
        "district": "Saint-Jean / Créqui",
    },
    {
        "id": "CPN-CHOCO-02",
        "partner": "Maison Bernachon Chocolatier",
        "category": "Chocolaterie / Artisan",
        "offer_fr": "Un Palet d'Or signature & dégustation de chocolat chaud rue Franklin",
        "offer_en": "Signature Palet d'Or gold-leaf truffle & hot chocolate tasting on Rue Franklin",
        "cost": 100,
        "district": "Presqu'île (2e)",
    },
    {
        "id": "CPN-PRALINE-03",
        "partner": "Boulangerie Pralus Vieux Lyon",
        "category": "Pâtisserie / Bakery",
        "offer_fr": "Une Praluline individuelle aux pralines roses de Lyon offerte",
        "offer_en": "One freshly baked individual Praluline pink-praline brioche",
        "cost": 80,
        "district": "Rue Saint-Jean (5e)",
    },
    {
        "id": "CPN-MUSEE-04",
        "partner": "Musée Cinéma et Miniature",
        "category": "Culture & Musées",
        "offer_fr": "Entrée Coupe-File Explorer (-30%) dans la Maison des Avocats",
        "offer_en": "30% Off Skip-the-Line Explorer Admission inside the historic Maison des Avocats",
        "cost": 200,
        "district": "Vieux Lyon (5e)",
    },
    {
        "id": "CPN-SOIE-05",
        "partner": "Atelier de Soierie Croix-Rousse",
        "category": "Artisanat / Silk",
        "offer_fr": "Démonstration privée sur métier Jacquard + Carré de soie pochette (-25%)",
        "offer_en": "Private Jacquard loom weaving demo + 25% off a hand-printed Lyon silk pocket square",
        "cost": 250,
        "district": "Croix-Rousse (1er)",
    },
    {
        "id": "CPN-CROISIERE-06",
        "partner": "Les Bateaux Lyonnais",
        "category": "Croisière / River Tour",
        "offer_fr": "Billet Croisière 'Cap sur l'Île Barbe' le long de la Saône",
        "offer_en": "Scenic Saône River Cruise ticket toward historic Île Barbe",
        "cost": 350,
        "district": "Quai des Célestins (2e)",
    },
    {
        "id": "CPN-HOTEL-07",
        "partner": "Hôtel Cour des Loges Lyon",
        "category": "Hôtellerie / Boutique Stay",
        "offer_fr": "Surclassement Renaissance & Accès Spa Romain pour un séjour de 2 nuits",
        "offer_en": "Renaissance Suite Upgrade & Roman Thermal Baths access on a 2-night stay",
        "cost": 600,
        "district": "Rue du Bœuf (5e)",
    },
]


# ==============================================================================
# 3. SQLITE DATABASE PERSISTENCE LAYER
# ==============================================================================

def init_db() -> None:
    """
    # LOGIC: Initialize SQLite database `explorer_lyon.db` with required tables:
    - `explorer_profile`: Stores Explorer name, total points, current tier, solved riddles/quests, and redeemed coupons.
    - `diary_entries`: Stores date, Lyon spot tag, diary text, saved image path, and chosen album theme/font.
    """
    os.makedirs(PHOTO_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # LOGIC: Create `explorer_profile` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS explorer_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            explorer_name TEXT NOT NULL DEFAULT 'Explorer',
            total_points INTEGER NOT NULL DEFAULT 0,
            current_tier TEXT NOT NULL DEFAULT 'Rookie Explorer',
            solved_riddles TEXT NOT NULL DEFAULT '[]',
            solved_quests TEXT NOT NULL DEFAULT '[]',
            redeemed_coupons TEXT NOT NULL DEFAULT '[]'
        )
    """)

    # LOGIC: Create `diary_entries` table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diary_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date TEXT NOT NULL,
            lyon_spot TEXT NOT NULL,
            diary_text TEXT NOT NULL,
            image_path TEXT,
            album_theme TEXT NOT NULL DEFAULT 'Vintage Map',
            album_font TEXT NOT NULL DEFAULT 'Playfair Display'
        )
    """)

    # LOGIC: Seed default Explorer row if not yet initialized
    cursor.execute("SELECT COUNT(*) FROM explorer_profile WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO explorer_profile
            (id, explorer_name, total_points, current_tier, solved_riddles, solved_quests, redeemed_coupons)
            VALUES (1, 'Explorer', 0, 'Rookie Explorer', '[]', '[]', '[]')
            """
        )

    conn.commit()
    conn.close()


def calculate_tier(total_points: int) -> Dict[str, Any]:
    """# LOGIC: Determine Explorer Tier metadata based on cumulative earned points."""
    current = EXPLORER_TIERS[0]
    next_tier = None
    for idx, tier in enumerate(EXPLORER_TIERS):
        if total_points >= tier["min_pts"]:
            current = tier
            next_tier = EXPLORER_TIERS[idx + 1] if idx + 1 < len(EXPLORER_TIERS) else None
    return {"current": current, "next": next_tier}


def load_explorer_profile() -> Dict[str, Any]:
    """# LOGIC: Load saved Explorer profile stats and JSON arrays from SQLite on startup."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM explorer_profile WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    solved_riddles = json.loads(row["solved_riddles"] or "[]")
    solved_quests = json.loads(row["solved_quests"] or "[]")
    redeemed_coupons = json.loads(row["redeemed_coupons"] or "[]")
    total_points = int(row["total_points"])
    spent_points = sum(int(c.get("cost", 0)) for c in redeemed_coupons)
    available_points = max(0, total_points - spent_points)

    tier_info = calculate_tier(total_points)
    return {
        "explorer_name": row["explorer_name"],
        "total_points": total_points,
        "spent_points": spent_points,
        "available_points": available_points,
        "current_tier": tier_info["current"]["name"],
        "tier_fr": tier_info["current"]["fr"],
        "tier_badge": tier_info["current"]["badge"],
        "next_tier": tier_info["next"],
        "solved_riddles": solved_riddles,
        "solved_quests": solved_quests,
        "redeemed_coupons": redeemed_coupons,
    }


def save_explorer_profile(
    explorer_name: str,
    total_points: int,
    solved_riddles: List[str],
    solved_quests: List[str],
    redeemed_coupons: List[Dict[str, Any]],
) -> None:
    """# LOGIC: Persist updated Explorer profile, tier, points, and achievements to SQLite."""
    tier_name = calculate_tier(total_points)["current"]["name"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE explorer_profile
        SET explorer_name = ?,
            total_points = ?,
            current_tier = ?,
            solved_riddles = ?,
            solved_quests = ?,
            redeemed_coupons = ?
        WHERE id = 1
        """,
        (
            explorer_name.strip() or "Explorer",
            total_points,
            tier_name,
            json.dumps(solved_riddles, ensure_ascii=False),
            json.dumps(solved_quests, ensure_ascii=False),
            json.dumps(redeemed_coupons, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def insert_diary_entry(
    entry_date: str,
    lyon_spot: str,
    diary_text: str,
    image_path: Optional[str],
    album_theme: str,
    album_font: str,
) -> None:
    """# LOGIC: Insert a new dated Lyon travel diary entry into SQLite `diary_entries`."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO diary_entries (entry_date, lyon_spot, diary_text, image_path, album_theme, album_font)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entry_date, lyon_spot, diary_text, image_path, album_theme, album_font),
    )
    conn.commit()
    conn.close()


def load_diary_entries() -> List[Dict[str, Any]]:
    """# LOGIC: Retrieve all saved diary entries ordered from newest to oldest."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM diary_entries ORDER BY entry_date DESC, id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def delete_diary_entry(entry_id: int) -> None:
    """# LOGIC: Delete a specific diary entry by ID from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM diary_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


# ==============================================================================
# 4. GOOGLE GEMINI AI INTEGRATION (`google-genai`) WITH FALLBACKS
# ==============================================================================

def get_gemini_client(api_key: str):
    """# LOGIC: Instantiate Google GenAI SDK client if package and API key exist."""
    if not GENAI_AVAILABLE or not api_key or not api_key.strip():
        return None
    try:
        return genai.Client(api_key=api_key.strip())
    except Exception:
        return None


def ai_fetch_lyon_insider(api_key: str, topic_title: str) -> Optional[Dict[str, Any]]:
    """
    # LOGIC: Prompt Gemini (`gemini-2.5-flash`) for bilingual French/English insider
    facts about a specific Lyon cultural category, returning structured JSON.
    """
    client = get_gemini_client(api_key)
    if not client:
        return None

    prompt = f"""
    You are an expert Lyon, France historian and local guide speaking to an 'Explorer'.
    Provide fresh, deeply authentic insider knowledge about Lyon for the topic: "{topic_title}".
    Return ONLY valid JSON with these exact keys:
    {{
        "summary_fr": "2-3 vivid sentences in French",
        "summary_en": "2-3 vivid sentences in English translating the French summary",
        "highlights": ["4 concrete, specific Lyon historical/cultural bullet points with street names or dates"]
    }}
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
        data = json.loads(response.text)
        if "summary_fr" in data and "summary_en" in data and isinstance(data.get("highlights"), list):
            return data
    except Exception:
        return None
    return None


def ai_generate_riddles_and_quests(api_key: str) -> Optional[Dict[str, Any]]:
    """
    # LOGIC: Generate 12 location-bound Lyon riddles and 3 real-life photo quests
    using `google-genai` structured JSON output.
    """
    client = get_gemini_client(api_key)
    if not client:
        return None

    prompt = """
    Create an interactive location-based game in Lyon, France for a player addressed as 'Explorer'.
    Generate:
    1) Exactly 12 location-bound riddles grounded exclusively in Lyon's real history, landmarks, traboules, gastronomy, Roman Lugdunum, silk Canuts, or Lumière brothers. Each riddle must have a short 1-to-3 word answer.
    2) Exactly 3 Real-Life Photo Quests set at real Lyon coordinates.

    Return ONLY valid JSON matching this exact schema:
    {
      "riddles": [
        {
          "id": "R01",
          "spot": "Lyon Landmark Name",
          "question_fr": "Riddle question in French",
          "question_en": "English translation of the riddle question",
          "hint": "Helpful clue in English",
          "answer": "canonical lowercase answer",
          "accepted": ["canonical lowercase answer", "french or english variant"]
        }
      ],
      "quests": [
        {
          "id": "Q01",
          "title_fr": "Quest title in French",
          "title_en": "Quest title in English",
          "desc_fr": "Actionable real-world photo instructions in French",
          "desc_en": "Actionable real-world photo instructions in English",
          "target_lat": 45.7629,
          "target_lon": 4.8273,
          "points": 200
        }
      ]
    }
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8,
            ),
        )
        parsed = json.loads(response.text)
        if len(parsed.get("riddles", [])) >= 12 and len(parsed.get("quests", [])) >= 3:
            parsed["riddles"] = parsed["riddles"][:12]
            parsed["quests"] = parsed["quests"][:3]
            for idx, r in enumerate(parsed["riddles"], 1):
                r["id"] = f"AI-R{idx:02d}"
            for idx, q in enumerate(parsed["quests"], 1):
                q["id"] = f"AI-Q{idx:02d}"
                q["points"] = QUEST_POINTS
            return parsed
    except Exception:
        return None
    return None


def ai_verify_quest_photo(api_key: str, quest: Dict[str, Any], image_bytes: bytes) -> str:
    """
    # LOGIC: Optional Gemini multimodal check to inspect the Explorer's uploaded
    quest photo and deliver an enthusiastic bilingual field-agent verification note.
    """
    client = get_gemini_client(api_key)
    if not client:
        return "Preuve photo enregistrée dans votre dossier d'Explorateur ! | Photo evidence logged to your Explorer dossier!"

    try:
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        prompt = (
            f"You are the Lyon Quest Master addressing 'Explorer'. "
            f"The Explorer uploaded this photo for the real-life Lyon quest: '{quest['title_en']}' ({quest['desc_en']}). "
            f"Write a short, encouraging 2-sentence field verification note (first sentence in French, second in English) "
            f"acknowledging what you see in their photo."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, pil_img],
        )
        return response.text.strip()
    except Exception:
        return "Preuve photo validée par le QG de Lyon ! | Photo proof validated by Lyon HQ!"


# ==============================================================================
# 5. REPORTLAB PDF ALBUM EXPORT ENGINE
# ==============================================================================

def safe_pdf_text(text: str) -> str:
    """
    # LOGIC: Normalize French typography characters (such as 'œ', curly quotes,
    and em-dashes) so ReportLab's built-in Latin-1 Type1 fonts render French accents
    ('é, è, ê, à, ç, ô, î, û') cleanly without encoding exceptions.
    """
    if not text:
        return ""
    replacements = {
        "œ": "oe",
        "Œ": "OE",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
        "…": "...",
        "•": "*",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_album_pdf(
    profile: Dict[str, Any],
    entries: List[Dict[str, Any]],
    default_theme_name: str,
    default_font_name: str,
) -> bytes:
    """
    # LOGIC: Render a multi-page, theme-styled PDF Travel Album using ReportLab.
    - Page 1: Custom Explorer Expedition Cover Page (Lyon coordinates, Explorer Rank, XP).
    - Subsequent Pages: One full-bleed styled journal spread per diary entry using each
      entry's saved Theme palette, decorative border style, font family, and embedded photo.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4

    # LOGIC: Cover Page Styling using the Explorer's active Studio Theme
    cover_theme = ALBUM_THEMES.get(default_theme_name, ALBUM_THEMES["Vintage Map"])
    cover_font = CUSTOM_FONTS.get(default_font_name, CUSTOM_FONTS["Playfair Display"])

    c.setFillColor(colors.HexColor(cover_theme["bg"]))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Decorative Outer Frame
    c.setStrokeColor(colors.HexColor(cover_theme["accent"]))
    c.setLineWidth(3)
    c.rect(28, 28, page_w - 56, page_h - 56, fill=0, stroke=1)
    c.setStrokeColor(colors.HexColor(cover_theme["secondary"]))
    c.setLineWidth(1)
    c.rect(36, 36, page_w - 72, page_h - 72, fill=0, stroke=1)

    # Cover Header Badge
    c.setFillColor(colors.HexColor(cover_theme["accent"]))
    c.setFont(cover_font["pdf_body"], 11)
    c.drawCentredString(page_w / 2, page_h - 110, safe_pdf_text("EXPLORER QUEST : ÉDITION LYON  |  45.7640° N, 4.8357° E"))

    # Cover Main Title (French Primary + English Subtitle)
    c.setFillColor(colors.HexColor(cover_theme["text"]))
    c.setFont(cover_font["pdf_title"], 28)
    c.drawCentredString(page_w / 2, page_h - 165, safe_pdf_text("Carnet d'Expédition à Lyon"))

    c.setFillColor(colors.HexColor(cover_theme["accent"]))
    c.setFont(cover_font["pdf_body"], 14)
    c.drawCentredString(page_w / 2, page_h - 192, safe_pdf_text("Official Lyon Expedition Diary & Photo Album"))

    # Divider Line
    c.setStrokeColor(colors.HexColor(cover_theme["accent"]))
    c.setLineWidth(1.5)
    c.line(120, page_h - 215, page_w - 120, page_h - 215)

    # Explorer Dossier Summary Card on Cover
    card_x, card_y, card_w, card_h = 80, page_h - 430, page_w - 160, 175
    c.setFillColor(colors.HexColor(cover_theme["card_bg"]))
    c.setStrokeColor(colors.HexColor(cover_theme["accent"]))
    c.setLineWidth(1.5)
    c.roundRect(card_x, card_y, card_w, card_h, 10, fill=1, stroke=1)

    c.setFillColor(colors.HexColor(cover_theme["text"]))
    c.setFont(cover_font["pdf_title"], 16)
    c.drawCentredString(page_w / 2, card_y + card_h - 36, safe_pdf_text(f"Explorateur / Explorer : {profile['explorer_name']}"))

    c.setFont(cover_font["pdf_body"], 12)
    c.drawCentredString(
        page_w / 2,
        card_y + card_h - 68,
        safe_pdf_text(f"Rang / Tier : {profile['current_tier']} ({profile['tier_fr']})"),
    )
    c.drawCentredString(
        page_w / 2,
        card_y + card_h - 96,
        safe_pdf_text(f"Points Cumulés / Total XP : {profile['total_points']} pts"),
    )
    c.drawCentredString(
        page_w / 2,
        card_y + card_h - 124,
        safe_pdf_text(
            f"Énigmes Résolues : {len(profile['solved_riddles'])}/12   |   Quêtes Réelles : {len(profile['solved_quests'])}/3"
        ),
    )
    c.drawCentredString(
        page_w / 2,
        card_y + card_h - 150,
        safe_pdf_text(f"Souvenirs Archivés / Diary Entries : {len(entries)}"),
    )

    c.setFillColor(colors.HexColor(cover_theme["text"]))
    c.setFont(cover_font["pdf_body"], 10)
    c.drawCentredString(
        page_w / 2,
        65,
        safe_pdf_text(f"Généré le / Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} — Lugdunum Archives"),
    )
    c.showPage()

    # LOGIC: Render each diary entry page using its own saved Theme & Font
    if not entries:
        c.setFillColor(colors.HexColor(cover_theme["bg"]))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor(cover_theme["text"]))
        c.setFont(cover_font["pdf_title"], 18)
        c.drawCentredString(page_w / 2, page_h / 2 + 12, safe_pdf_text("Aucune entrée de journal pour le moment."))
        c.setFont(cover_font["pdf_body"], 13)
        c.drawCentredString(page_w / 2, page_h / 2 - 14, safe_pdf_text("No diary entries recorded yet, Explorer!"))
        c.showPage()
    else:
        for idx, entry in enumerate(entries, start=1):
            t_name = entry.get("album_theme") or default_theme_name
            f_name = entry.get("album_font") or default_font_name
            theme = ALBUM_THEMES.get(t_name, cover_theme)
            font_cfg = CUSTOM_FONTS.get(f_name, cover_font)

            # Page Background
            c.setFillColor(colors.HexColor(theme["bg"]))
            c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

            # Inner Card Container
            margin = 36
            c.setFillColor(colors.HexColor(theme["card_bg"]))
            c.setStrokeColor(colors.HexColor(theme["accent"]))
            c.setLineWidth(2)
            c.roundRect(margin, margin, page_w - 2 * margin, page_h - 2 * margin, 12, fill=1, stroke=1)

            # Top Metadata Ribbon
            y_cursor = page_h - margin - 34
            c.setFillColor(colors.HexColor(theme["accent"]))
            c.setFont(font_cfg["pdf_body"], 10)
            c.drawString(
                margin + 24,
                y_cursor,
                safe_pdf_text(f"ENTRÉE #{idx:02d}  |  DATE : {entry['entry_date']}  |  THÈME : {t_name.upper()}"),
            )

            # Spot Title (French + English Subtitle)
            y_cursor -= 28
            c.setFillColor(colors.HexColor(theme["text"]))
            c.setFont(font_cfg["pdf_title"], 20)
            c.drawString(margin + 24, y_cursor, safe_pdf_text(entry["lyon_spot"]))

            y_cursor -= 18
            c.setFillColor(colors.HexColor(theme["accent"]))
            c.setFont(font_cfg["pdf_body"], 11)
            c.drawString(margin + 24, y_cursor, safe_pdf_text(f"Étape Lyonnaise — Police / Font : {f_name}"))

            # Accent Rule
            y_cursor -= 12
            c.setStrokeColor(colors.HexColor(theme["secondary"]))
            c.setLineWidth(1.2)
            c.line(margin + 24, y_cursor, page_w - margin - 24, y_cursor)
            y_cursor -= 18

            # Embed Photo if saved on disk
            img_path = entry.get("image_path")
            if img_path and os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path).convert("RGB")
                    orig_w, orig_h = pil_img.size
                    max_w = page_w - 2 * margin - 48
                    max_h = 275
                    scale = min(max_w / orig_w, max_h / orig_h)
                    draw_w, draw_h = orig_w * scale, orig_h * scale
                    img_x = (page_w - draw_w) / 2
                    img_y = y_cursor - draw_h

                    # Photo Frame
                    c.setStrokeColor(colors.HexColor(theme["accent"]))
                    c.setLineWidth(1.5)
                    c.rect(img_x - 3, img_y - 3, draw_w + 6, draw_h + 6, fill=0, stroke=1)

                    img_buf = io.BytesIO()
                    pil_img.save(img_buf, format="JPEG", quality=88)
                    img_buf.seek(0)
                    c.drawImage(ImageReader(img_buf), img_x, img_y, width=draw_w, height=draw_h)
                    y_cursor = img_y - 24
                except Exception:
                    y_cursor -= 10

            # Diary Narrative Body (Word-wrapped cleanly)
            c.setFillColor(colors.HexColor(theme["text"]))
            c.setFont(font_cfg["pdf_body"], 12)
            text_max_w = page_w - 2 * margin - 48
            paragraphs = (entry.get("diary_text") or "").split("\n")

            for para in paragraphs:
                wrapped_lines = simpleSplit(safe_pdf_text(para), font_cfg["pdf_body"], 12, text_max_w)
                if not wrapped_lines:
                    y_cursor -= 14
                for line in wrapped_lines:
                    if y_cursor < margin + 45:
                        break
                    c.drawString(margin + 24, y_cursor, line)
                    y_cursor -= 18
                y_cursor -= 6

            # Footer
            c.setFillColor(colors.HexColor(theme["accent"]))
            c.setFont(font_cfg["pdf_body"], 9)
            c.drawCentredString(
                page_w / 2,
                margin + 16,
                safe_pdf_text(f"Explorer Quest: Lyon Edition  •  {profile['explorer_name']}  •  Page {idx}"),
            )
            c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ==============================================================================
# 6. UI/UX ARCHITECT COMPONENTS & STYLING
# ==============================================================================

def inject_global_styles() -> None:
    """
    # UI EDITING: Inject Google Fonts (all 10 custom studio fonts) and global Lyon
    expedition theme CSS (Rhône Navy #14213D, Silk Crimson #9E2A2B, Parchment #FAF7F2).
    """
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Cinzel:wght@600;700&family=Lobster&family=Montserrat:wght@400;600;700&family=Oswald:wght@500;700&family=Pacifico&family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Space+Grotesk:wght@400;600;700&family=Special+Elite&family=Syne:wght@600;700&display=swap" rel="stylesheet">

        <style>
            /* UI EDITING: Main App Canvas & Typography */
            .stApp {
                background-color: #FAF7F2;
                color: #1B2432;
                font-family: 'Montserrat', sans-serif;
            }
            /* UI EDITING: Sidebar Command Deck */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #14213D 0%, #1D2D50 100%);
                color: #FAF7F2;
            }
            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] span {
                color: #FAF7F2 !important;
            }
            section[data-testid="stSidebar"] input {
                color: #14213D !important;
                background-color: #FAF7F2 !important;
            }
            /* UI EDITING: Hero Banner */
            .lyon-hero {
                background: linear-gradient(135deg, #14213D 0%, #2B2D42 55%, #9E2A2B 100%);
                padding: 1.75rem 2rem;
                border-radius: 16px;
                border-bottom: 4px solid #D4A373;
                color: #FFFFFF;
                margin-bottom: 1.25rem;
                box-shadow: 0 10px 25px rgba(20, 33, 61, 0.18);
            }
            .lyon-hero-fr {
                font-family: 'Cinzel', serif;
                font-size: 2.1rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                margin: 0;
                color: #FFFFFF;
            }
            .lyon-hero-en {
                font-family: 'Montserrat', sans-serif;
                font-size: 1.0rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.14em;
                color: #F4D58D;
                margin-top: 0.25rem;
            }
            /* UI EDITING: Dual-Language Section Headers */
            .dual-header {
                border-left: 5px solid #9E2A2B;
                padding-left: 0.9rem;
                margin: 1.1rem 0 0.85rem 0;
            }
            .dual-header-fr {
                font-family: 'Playfair Display', serif;
                font-size: 1.45rem;
                font-weight: 700;
                color: #14213D;
                line-height: 1.2;
                margin: 0;
            }
            .dual-header-en {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.85rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #9E2A2B;
                margin-top: 0.18rem;
            }
            /* UI EDITING: Landmark & Quest Cards */
            .lyon-card {
                background: #FFFFFF;
                border: 1px solid #E5DEC9;
                border-radius: 14px;
                padding: 1.1rem;
                box-shadow: 0 4px 14px rgba(20, 33, 61, 0.06);
                margin-bottom: 1rem;
            }
            .badge-pill {
                display: inline-block;
                background: #14213D;
                color: #F4D58D;
                padding: 0.2rem 0.65rem;
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 600;
                letter-spacing: 0.04em;
            }
            .pts-pill {
                display: inline-block;
                background: #9E2A2B;
                color: #FFFFFF;
                padding: 0.2rem 0.65rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dual_header(fr_title: str, en_subtitle: str, dark_bg: bool = False) -> None:
    """
    # UI EDITING: Enforce Dual-Language UI Rule across every main topic, section title,
    and header: French primary text above, English subtitle directly below.
    """
    fr_color = "#FFFFFF" if dark_bg else "#14213D"
    en_color = "#F4D58D" if dark_bg else "#9E2A2B"
    border_color = "#F4D58D" if dark_bg else "#9E2A2B"
    st.markdown(
        f"""
        <div class="dual-header" style="border-left-color: {border_color};">
            <div class="dual-header-fr" style="color: {fr_color};">{fr_title}</div>
            <div class="dual-header-en" style="color: {en_color};">{en_subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def image_file_to_base64(path: str) -> Optional[str]:
    """# LOGIC: Convert a local saved photo into a base64 data URI for Live Album Preview."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None


def render_album_preview_card(
    entry_date: str,
    lyon_spot: str,
    diary_text: str,
    theme_name: str,
    font_name: str,
    image_b64: Optional[str] = None,
) -> None:
    """
    # UI EDITING: Live Album Studio HTML/CSS renderer applying the Explorer's
    chosen Visual Theme (1 of 10) and Custom Google Font (1 of 10).
    """
    theme = ALBUM_THEMES.get(theme_name, ALBUM_THEMES["Vintage Map"])
    font_css = CUSTOM_FONTS.get(font_name, CUSTOM_FONTS["Playfair Display"])["css"]

    img_html = ""
    if image_b64:
        img_html = f"""
        <div style="margin: 0.85rem 0; text-align: center;">
            <img src="{image_b64}" style="max-width: 100%; max-height: 290px; border-radius: 8px; border: 2px solid {theme['accent']}; object-fit: cover;" />
        </div>
        """

    safe_text = (diary_text or "Écrivez vos souvenirs de Lyon ici... / Write your Lyon memories here...").replace("\n", "<br>")

    st.markdown(
        f"""
        <div style="
            background: {theme['bg']};
            padding: 1.35rem;
            border-radius: 14px;
            border: {theme['border']};
            box-shadow: 0 8px 22px rgba(0,0,0,0.12);
            margin-bottom: 1rem;
        ">
            <div style="
                background: {theme['card_bg']};
                color: {theme['text']};
                font-family: {font_css};
                padding: 1.35rem;
                border-radius: 10px;
                border: 1px solid {theme['secondary']};
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; font-size: 0.82rem; color: {theme['accent']}; font-weight: 700; letter-spacing: 0.05em;">
                    <span>📍 {lyon_spot}</span>
                    <span>📅 {entry_date}  •  🎨 {theme_name} ({theme['tag']})</span>
                </div>
                <h3 style="margin: 0.55rem 0 0.15rem 0; color: {theme['text']}; font-family: {font_css}; font-size: 1.55rem;">
                    Carnet de Voyage — {lyon_spot}
                </h3>
                <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.09em; color: {theme['accent']}; margin-bottom: 0.75rem;">
                    Lyon Expedition Journal  •  Font: {font_name}
                </div>
                <hr style="border: none; border-top: 1px solid {theme['secondary']}; margin: 0.5rem 0;" />
                {img_html}
                <p style="font-size: 1.08rem; line-height: 1.65; color: {theme['text']}; margin-top: 0.65rem;">
                    {safe_text}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# 7. MAIN STREAMLIT APPLICATION FLOW
# ==============================================================================

def main() -> None:
    # UI EDITING: Page Metadata & Layout
    st.set_page_config(
        page_title="Explorer Quest: Lyon Edition",
        page_icon="🦁",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_global_styles()

    # LOGIC: Auto-initialize SQLite database on app startup
    init_db()

    # LOGIC: Initialize Session State from SQLite and fallback datasets
    if "profile" not in st.session_state:
        st.session_state.profile = load_explorer_profile()
    if "diary_entries" not in st.session_state:
        st.session_state.diary_entries = load_diary_entries()
    if "riddles" not in st.session_state:
        st.session_state.riddles = FALLBACK_RIDDLES
    if "quests" not in st.session_state:
        st.session_state.quests = FALLBACK_QUESTS
    if "gps_lat" not in st.session_state:
        st.session_state.gps_lat = LYON_DEFAULT_LAT
    if "gps_lon" not in st.session_state:
        st.session_state.gps_lon = LYON_DEFAULT_LON
    if "ai_guide_cache" not in st.session_state:
        st.session_state.ai_guide_cache = {}

    profile = st.session_state.profile

    # --------------------------------------------------------------------------
    # SIDEBAR: EXPLORER COMMAND DECK & PROFILE PERSISTENCE
    # --------------------------------------------------------------------------
    with st.sidebar:
        render_dual_header("Tableau de l'Explorateur", "Explorer Command Deck", dark_bg=True)

        # LOGIC: Explorer Name Editor with SQLite persistence
        new_name = st.text_input(
            "Nom de l'Explorateur / Explorer Name",
            value=profile["explorer_name"],
            key="explorer_name_input",
        )
        if new_name.strip() and new_name.strip() != profile["explorer_name"]:
            save_explorer_profile(
                explorer_name=new_name.strip(),
                total_points=profile["total_points"],
                solved_riddles=profile["solved_riddles"],
                solved_quests=profile["solved_quests"],
                redeemed_coupons=profile["redeemed_coupons"],
            )
            st.session_state.profile = load_explorer_profile()
            profile = st.session_state.profile
            st.toast(f"Bienvenue, Explorer {profile['explorer_name']} ! | Welcome, Explorer!")

        # UI EDITING: Rank & Points Display Card
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.08); padding: 1rem; border-radius: 12px; border: 1px solid #F4D58D; margin: 0.75rem 0;">
                <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: #F4D58D;">
                    Rang Actuel / Current Tier
                </div>
                <div style="font-size: 1.3rem; font-weight: 700; margin: 0.2rem 0;">
                    {profile['tier_badge']} {profile['current_tier']}
                </div>
                <div style="font-size: 0.85rem; opacity: 0.9;">
                    {profile['tier_fr']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # LOGIC: Progress bar toward next Explorer Tier
        if profile["next_tier"]:
            nxt = profile["next_tier"]
            cur_min = calculate_tier(profile["total_points"])["current"]["min_pts"]
            span = max(1, nxt["min_pts"] - cur_min)
            progress_val = min(1.0, (profile["total_points"] - cur_min) / span)
            st.progress(progress_val)
            st.caption(
                f"Prochain rang / Next Tier: **{nxt['name']}** ({nxt['min_pts'] - profile['total_points']} pts restants)"
            )
        else:
            st.progress(1.0)
            st.caption("Rang Maximum Atteint ! | Maximum Legend Tier Reached!")

        col_sb1, col_sb2 = st.columns(2)
        col_sb1.metric("XP Total", f"{profile['total_points']} pts")
        col_sb2.metric("Solde / Wallet", f"{profile['available_points']} pts")

        col_sb3, col_sb4 = st.columns(2)
        col_sb3.metric("Énigmes / Riddles", f"{len(profile['solved_riddles'])}/12")
        col_sb4.metric("Quêtes / Quests", f"{len(profile['solved_quests'])}/3")

        st.markdown("---")
        render_dual_header("Configuration IA Gemini", "Gemini AI Engine", dark_bg=True)
        default_env_key = os.environ.get("GEMINI_API_KEY", "")
        api_key = st.text_input(
            "Clé API Google Gemini / Gemini API Key",
            value=default_env_key,
            type="password",
            help="Optional: Enter your Gemini API key for live AI riddles, quests & Lyon insider lore. Offline Lyon archives work automatically without a key.",
        )
        if get_gemini_client(api_key):
            st.success("IA Gemini Connectée | AI Live Mode Active")
        else:
            st.info("Mode Archive Locale | Offline Lyon Data Active")

    # --------------------------------------------------------------------------
    # HERO BANNER (DUAL LANGUAGE FRENCH + ENGLISH)
    # --------------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="lyon-hero">
            <div class="lyon-hero-fr">🦁 Explorer Quest : Édition Lyon</div>
            <div class="lyon-hero-en">Interactive Heritage Expedition, AI Riddles & Travel Album Studio  •  45.7640° N, 4.8357° E</div>
            <div style="margin-top: 0.7rem; font-size: 0.92rem; color: #F8F9FA;">
                Bienvenue, <strong>Explorer {profile['explorer_name']}</strong> ! Explorez les traboules secrètes, résolvez les énigmes de Lugdunum et créez votre album souvenir.<br/>
                <em>Welcome, Explorer {profile['explorer_name']}! Uncover secret traboules, solve Lugdunum riddles, and craft your travel album.</em>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------------------------
    # MAIN 5-TAB NAVIGATION ARCHITECTURE
    # --------------------------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🗺️ Guide Interactif | Lyon Hub",
            "🧩 Énigmes et Quêtes | AI Quests",
            "📔 Journal & Album PDF | Studio",
            "🎟️ Boutique de Coupons | Rewards",
            "🗄️ Profil & Base SQLite | Archives",
        ]
    )

    # ==========================================================================
    # TAB 1: LYON LOCATION HUB (GUIDE INTERACTIF)
    # ==========================================================================
    with tab1:
        render_dual_header(
            "Les Incontournables de Lyon & Position GPS",
            "Must-Visit Places in Lyon & Live GPS Lock",
        )

        # LOGIC: GPS Coordinate Lock & Landmark Quick-Teleport
        gps_col1, gps_col2 = st.columns([1.1, 1.4])
        with gps_col1:
            st.markdown('<div class="lyon-card">', unsafe_allow_html=True)
            render_dual_header("Verrouillage GPS Lyon", "GPS Coordinate Lock")
            lat_in = st.number_input(
                "Latitude (° N)",
                value=float(st.session_state.gps_lat),
                format="%.4f",
                step=0.0005,
            )
            lon_in = st.number_input(
                "Longitude (° E)",
                value=float(st.session_state.gps_lon),
                format="%.4f",
                step=0.0005,
            )
            st.session_state.gps_lat = lat_in
            st.session_state.gps_lon = lon_in

            btn_c1, btn_c2 = st.columns(2)
            if btn_c1.button("📍 Verrouiller Lyon Centre | Lock Lyon Center", use_container_width=True):
                st.session_state.gps_lat = LYON_DEFAULT_LAT
                st.session_state.gps_lon = LYON_DEFAULT_LON
                st.toast("Explorer verrouillé sur Lyon (45.7640° N, 4.8357° E) ! | Locked onto Lyon!")
                st.rerun()

            selected_lm_name = btn_c2.selectbox(
                "Saut Rapide / Quick Landmark",
                options=[lm["name_fr"] for lm in LYON_LANDMARKS],
                label_visibility="collapsed",
            )
            if st.button("🧭 Téléporter vers ce Monument | Jump to Landmark", use_container_width=True):
                chosen = next(lm for lm in LYON_LANDMARKS if lm["name_fr"] == selected_lm_name)
                st.session_state.gps_lat = chosen["lat"]
                st.session_state.gps_lon = chosen["lon"]
                st.toast(f"Explorer positionné à : {chosen['name_fr']} | Positioned at {chosen['name_en']}")
                st.rerun()

            st.caption(
                f"Position actuelle de l'Explorer / Current Explorer Coordinates: **{st.session_state.gps_lat:.4f}° N, {st.session_state.gps_lon:.4f}° E**"
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with gps_col2:
            # LOGIC: Interactive Map plotting current Explorer coordinates + iconic Lyon landmarks
            map_points = [
                {"lat": st.session_state.gps_lat, "lon": st.session_state.gps_lon},
                *[{"lat": lm["lat"], "lon": lm["lon"]} for lm in LYON_LANDMARKS],
            ]
            st.map(map_points, zoom=12)

        # LOGIC: Cultural Dossier Explorer (History, Traboules, Architecture, Bouchons, Festivals)
        render_dual_header(
            "Encyclopédie Culturelle de Lyon",
            "Lyon Cultural Dossier: History, Traboules, Architecture, Bouchons & Festivals",
        )
        topic_choice = st.selectbox(
            "Choisissez un thème à explorer / Select a Lyon Cultural Topic",
            options=list(FALLBACK_LYON_GUIDE.keys()),
        )

        # LOGIC: Allow Explorer to enrich the topic with live Gemini AI insights
        if st.button("✨ Demander à l'IA Gemini des Secrets Supplémentaires | Fetch AI Insider Lore"):
            with st.spinner("Consultation des archives IA de Lyon... | Consulting Lyon AI archives..."):
                ai_dossier = ai_fetch_lyon_insider(api_key, topic_choice)
                if ai_dossier:
                    st.session_state.ai_guide_cache[topic_choice] = ai_dossier
                    st.success("Nouvelles anecdotes IA chargées pour l'Explorer ! | Fresh AI insider lore loaded!")
                else:
                    st.warning(
                        "Clé API Gemini absente ou hors ligne — affichage des archives vérifiées de Lyon. | No active Gemini API key — displaying verified Lyon archives."
                    )

        active_dossier = st.session_state.ai_guide_cache.get(topic_choice, FALLBACK_LYON_GUIDE[topic_choice])
        st.markdown(
            f"""
            <div class="lyon-card">
                <p style="font-size: 1.05rem; color: #14213D; font-weight: 600; margin-bottom: 0.4rem;">
                    🇫🇷 {active_dossier['summary_fr']}
                </p>
                <p style="font-size: 0.96rem; color: #4A5568; font-style: italic; margin-bottom: 0.85rem;">
                    🇬🇧 {active_dossier['summary_en']}
                </p>
                <div style="font-weight: 700; color: #9E2A2B; margin-bottom: 0.4rem;">
                    Points Clés de l'Explorateur / Explorer Key Facts:
                </div>
                <ul style="margin: 0; padding-left: 1.25rem; color: #1B2432;">
                    {''.join(f'<li style="margin-bottom: 0.3rem;">{item}</li>' for item in active_dossier['highlights'])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # LOGIC: Interactive Photo Cards for Iconic Lyon Landmarks
        render_dual_header(
            "Cartes Photo des Monuments Emblématiques",
            "Interactive Photo Cards of Iconic Lyon Landmarks",
        )
        cols = st.columns(3)
        for idx, lm in enumerate(LYON_LANDMARKS):
            with cols[idx % 3]:
                # UI EDITING: Fallback SVG data URI ensures crisp card art even if offline
                fallback_svg = (
                    "data:image/svg+xml;utf8,"
                    "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='360'>"
                    "<rect width='100%' height='100%' fill='%2314213D'/>"
                    "<text x='50%' y='48%' fill='%23F4D58D' font-size='22' font-family='serif' text-anchor='middle'>"
                    f"{lm['name_fr'].replace('&', 'et')}"
                    "</text>"
                    "<text x='50%' y='60%' fill='%23FFFFFF' font-size='14' font-family='sans-serif' text-anchor='middle'>"
                    "Lyon, France • 45.7640° N, 4.8357° E"
                    "</text></svg>"
                )
                st.markdown(
                    f"""
                    <div class="lyon-card" style="padding: 0; overflow: hidden;">
                        <img src="{lm['image_url']}" onerror="this.onerror=null;this.src='{fallback_svg}';"
                             style="width: 100%; height: 185px; object-fit: cover; display: block;" />
                        <div style="padding: 1rem;">
                            <span class="badge-pill">{lm['district']}</span>
                            <h4 style="font-family: 'Playfair Display', serif; color: #14213D; margin: 0.5rem 0 0.1rem 0;">
                                {lm['name_fr']}
                            </h4>
                            <div style="font-size: 0.78rem; text-transform: uppercase; color: #9E2A2B; font-weight: 700; margin-bottom: 0.55rem;">
                                {lm['name_en']}
                            </div>
                            <p style="font-size: 0.88rem; color: #1B2432; margin-bottom: 0.35rem;">{lm['desc_fr']}</p>
                            <p style="font-size: 0.82rem; color: #5C677D; font-style: italic; margin-bottom: 0.5rem;">{lm['desc_en']}</p>
                            <div style="font-size: 0.76rem; color: #6C757D;">📍 {lm['lat']:.4f}° N, {lm['lon']:.4f}° E</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ==========================================================================
    # TAB 2: AI RIDDLES & QUESTS (ÉNIGMES ET QUÊTES)
    # ==========================================================================
    with tab2:
        render_dual_header(
            "Énigmes Historiques & Quêtes Réelles",
            "12 Location-Bound Riddles (50 pts) & 3 Real-Life Photo Quests (200 pts)",
        )

        # LOGIC: Generate new AI Riddles & Quests via Gemini or restore classics
        gen_c1, gen_c2 = st.columns([1.5, 1])
        if gen_c1.button("🤖 Générer 12 Nouvelles Énigmes & 3 Quêtes avec Gemini | Generate AI Riddles & Quests", use_container_width=True):
            with st.spinner("L'IA Gemini compose de nouveaux défis lyonnais pour l'Explorer... | Crafting new Lyon challenges..."):
                ai_pack = ai_generate_riddles_and_quests(api_key)
                if ai_pack:
                    st.session_state.riddles = ai_pack["riddles"]
                    st.session_state.quests = ai_pack["quests"]
                    st.success("12 nouvelles énigmes et 3 quêtes photo générées pour l'Explorer ! | Fresh AI Riddles & Quests ready!")
                else:
                    st.warning(
                        "Clé API Gemini requise pour la génération dynamique — utilisation des 12 énigmes et 3 quêtes classiques de Lyon. | Gemini API key needed for dynamic generation — using classic Lyon Riddles & Quests."
                    )

        if gen_c2.button("🏛️ Charger les Défis Classiques de Lyon | Load Classic Lyon Set", use_container_width=True):
            st.session_state.riddles = FALLBACK_RIDDLES
            st.session_state.quests = FALLBACK_QUESTS
            st.info("Défis classiques de Lyon chargés ! | Classic Lyon Riddles & Quests loaded!")

        st.markdown("---")
        render_dual_header(
            "Les 12 Énigmes de Lugdunum (50 pts chacune)",
            "12 Location-Bound Riddles & Trivia (50 pts each)",
        )

        # LOGIC: Render all 12 Riddles in a responsive 2-column grid
        r_cols = st.columns(2)
        for idx, riddle in enumerate(st.session_state.riddles):
            rid = riddle["id"]
            is_solved = rid in profile["solved_riddles"]
            with r_cols[idx % 2]:
                status_badge = "✅ RÉSOLUE / SOLVED (+50 pts)" if is_solved else "🔒 À DÉCOUVRIR / UNSOLVED (50 pts)"
                st.markdown(
                    f"""
                    <div class="lyon-card" style="border-left: 4px solid {'#2D6A4F' if is_solved else '#9E2A2B'};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="badge-pill">📍 {riddle['spot']}</span>
                            <span class="pts-pill" style="background: {'#2D6A4F' if is_solved else '#9E2A2B'};">{status_badge}</span>
                        </div>
                        <p style="font-weight: 600; color: #14213D; margin: 0.65rem 0 0.25rem 0;">
                            #{idx + 1}. {riddle['question_fr']}
                        </p>
                        <p style="font-size: 0.88rem; color: #4A5568; font-style: italic; margin-bottom: 0.4rem;">
                            {riddle['question_en']}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.expander(f"💡 Indice / Hint — Énigme #{idx + 1}"):
                    st.write(riddle.get("hint", "Explorez l'histoire de Lyon !"))

                if is_solved:
                    st.success(f"Réponse validée / Verified Answer: **{riddle['answer'].title()}**")
                else:
                    ans_col, btn_col = st.columns([2.2, 1])
                    user_ans = ans_col.text_input(
                        f"Votre réponse / Answer #{idx + 1}",
                        key=f"ans_{rid}",
                        placeholder="Entrez votre réponse...",
                        label_visibility="collapsed",
                    )
                    if btn_col.button("Valider / Submit", key=f"sub_{rid}", use_container_width=True):
                        cleaned = user_ans.strip().lower()
                        accepted_list = [a.lower() for a in riddle.get("accepted", [riddle["answer"]])]
                        if cleaned and any(acc in cleaned or cleaned == acc for acc in accepted_list):
                            updated_riddles = list(profile["solved_riddles"]) + [rid]
                            new_total = profile["total_points"] + RIDDLE_POINTS
                            save_explorer_profile(
                                explorer_name=profile["explorer_name"],
                                total_points=new_total,
                                solved_riddles=updated_riddles,
                                solved_quests=profile["solved_quests"],
                                redeemed_coupons=profile["redeemed_coupons"],
                            )
                            st.session_state.profile = load_explorer_profile()
                            st.balloons()
                            st.toast(f"Bravo Explorer ! +{RIDDLE_POINTS} pts ajoutés à votre profil !")
                            st.rerun()
                        else:
                            st.error("Réponse incorrecte, Explorer ! Consultez l'indice et réessayez. | Incorrect answer, Explorer!")

        st.markdown("---")
        render_dual_header(
            "Les 3 Quêtes Photo Réelles (200 pts — Haute Récompense)",
            "3 Real-Life Photo Quests (200 pts High Reward Each)",
        )

        # LOGIC: Render 3 Real-Life Photo Quests with image upload & GPS logging
        for q_idx, quest in enumerate(st.session_state.quests, start=1):
            qid = quest["id"]
            q_solved = qid in profile["solved_quests"]
            st.markdown(
                f"""
                <div class="lyon-card" style="border-left: 5px solid {'#2D6A4F' if q_solved else '#D4A373'};">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <h4 style="font-family: 'Playfair Display', serif; color: #14213D; margin: 0;">
                            Quête #{q_idx} : {quest['title_fr']}
                        </h4>
                        <span class="pts-pill" style="background: {'#2D6A4F' if q_solved else '#14213D'};">
                            {'✅ ACCOMPLIE / COMPLETED' if q_solved else f'🏆 +{quest["points"]} PTS'}
                        </span>
                    </div>
                    <div style="font-size: 0.84rem; text-transform: uppercase; color: #9E2A2B; font-weight: 700; margin-bottom: 0.5rem;">
                        {quest['title_en']}
                    </div>
                    <p style="color: #1B2432; margin-bottom: 0.25rem;">🇫🇷 {quest['desc_fr']}</p>
                    <p style="color: #4A5568; font-style: italic; font-size: 0.9rem; margin-bottom: 0.4rem;">🇬🇧 {quest['desc_en']}</p>
                    <div style="font-size: 0.8rem; color: #6C757D;">
                        🎯 Coordonnées Cibles / Target GPS: {quest['target_lat']:.4f}° N, {quest['target_lon']:.4f}° E
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if q_solved:
                st.success(f"Quête #{q_idx} validée ! +200 pts attribués à Explorer {profile['explorer_name']}.")
            else:
                qc1, qc2, qc3 = st.columns([1.4, 1, 1])
                quest_photo = qc1.file_uploader(
                    f"Preuve Photo / Upload Quest Photo #{q_idx}",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"q_photo_{qid}",
                )
                q_lat = qc2.number_input(
                    "Latitude relevée / Logged Lat",
                    value=float(quest["target_lat"]),
                    format="%.4f",
                    key=f"q_lat_{qid}",
                )
                q_lon = qc3.number_input(
                    "Longitude relevée / Logged Lon",
                    value=float(quest["target_lon"]),
                    format="%.4f",
                    key=f"q_lon_{qid}",
                )

                if st.button(f"📸 Valider la Quête #{q_idx} (+200 pts) | Complete Quest", key=f"q_btn_{qid}"):
                    if quest_photo is None:
                        st.warning("Explorer, veuillez téléverser une photo preuve pour valider cette quête ! | Please upload a proof photo first!")
                    else:
                        # LOGIC: Save quest photo to disk & award 200 points in SQLite
                        img_bytes = quest_photo.getvalue()
                        saved_q_path = os.path.join(PHOTO_DIR, f"quest_{qid}_{uuid.uuid4().hex[:6]}.jpg")
                        Image.open(io.BytesIO(img_bytes)).convert("RGB").save(saved_q_path, format="JPEG", quality=88)

                        ai_note = ai_verify_quest_photo(api_key, quest, img_bytes)
                        updated_quests = list(profile["solved_quests"]) + [qid]
                        new_total = profile["total_points"] + QUEST_POINTS
                        save_explorer_profile(
                            explorer_name=profile["explorer_name"],
                            total_points=new_total,
                            solved_riddles=profile["solved_riddles"],
                            solved_quests=updated_quests,
                            redeemed_coupons=profile["redeemed_coupons"],
                        )
                        st.session_state.profile = load_explorer_profile()
                        st.balloons()
                        st.success(f"🎉 +{QUEST_POINTS} pts ! Position ({q_lat:.4f}, {q_lon:.4f}) enregistrée. {ai_note}")
                        st.rerun()

    # ==========================================================================
    # TAB 3: EXPLORER DIARY, ALBUM STUDIO & PDF EXPORT
    # ==========================================================================
    with tab3:
        render_dual_header(
            "Journal de l'Explorateur, Studio d'Album & Export PDF",
            "Explorer Diary, 10 Visual Themes, 10 Google Fonts & Formatted PDF Album Export",
        )

        studio_col1, studio_col2 = st.columns([1.05, 1.15])

        with studio_col1:
            st.markdown('<div class="lyon-card">', unsafe_allow_html=True)
            render_dual_header("Nouvelle Page de Journal", "Compose Diary Entry")

            entry_date_val = st.date_input("Date de l'étape / Entry Date", value=date.today())
            spot_options = [lm["name_fr"] for lm in LYON_LANDMARKS] + [
                "Les Halles de Lyon Paul Bocuse",
                "La Croix-Rousse & Mur des Canuts",
                "Bouchon Lyonnais Traditionnel",
                "Autre lieu secret de Lyon / Custom Lyon Spot",
            ]
            selected_spot = st.selectbox("Lieu à Lyon / Lyon Spot Tag", options=spot_options)
            if "Autre lieu" in selected_spot:
                selected_spot = st.text_input("Nom du lieu / Custom Spot Name", value="Rue Saint-Jean, Vieux Lyon")

            # UI EDITING: Selectors for the 10 Visual Themes and 10 Google Fonts
            theme_col, font_col = st.columns(2)
            chosen_theme = theme_col.selectbox(
                "Thème Visuel (10) / Album Theme",
                options=list(ALBUM_THEMES.keys()),
                index=0,
            )
            chosen_font = font_col.selectbox(
                "Police Google Fonts (10) / Custom Font",
                options=list(CUSTOM_FONTS.keys()),
                index=1,
            )
            st.caption(f"Style typographique : *{CUSTOM_FONTS[chosen_font]['vibe']}*")

            uploaded_diary_photo = st.file_uploader(
                "Photo Souvenir / Upload Lyon Photo",
                type=["jpg", "jpeg", "png", "webp"],
                key="diary_photo_uploader",
            )

            diary_narrative = st.text_area(
                "Récit de l'Explorateur / Travel Diary Narrative",
                height=145,
                placeholder="Aujourd'hui à Lyon, j'ai franchi une porte discrète du Vieux Lyon pour découvrir une cour Renaissance illuminée...",
            )

            if st.button("💾 Enregistrer dans l'Album SQLite | Save Diary Entry", type="primary", use_container_width=True):
                if not diary_narrative.strip():
                    st.warning("Explorer, écrivez quelques lignes dans votre journal avant d'enregistrer ! | Please write a diary entry before saving.")
                else:
                    saved_img_path = None
                    if uploaded_diary_photo is not None:
                        saved_img_path = os.path.join(
                            PHOTO_DIR,
                            f"diary_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg",
                        )
                        pil_photo = Image.open(io.BytesIO(uploaded_diary_photo.getvalue())).convert("RGB")
                        pil_photo.save(saved_img_path, format="JPEG", quality=90)

                    insert_diary_entry(
                        entry_date=entry_date_val.strftime("%Y-%m-%d"),
                        lyon_spot=selected_spot,
                        diary_text=diary_narrative.strip(),
                        image_path=saved_img_path,
                        album_theme=chosen_theme,
                        album_font=chosen_font,
                    )
                    st.session_state.diary_entries = load_diary_entries()
                    st.toast("Page enregistrée dans votre album lyonnais ! | Diary entry saved to SQLite!")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with studio_col2:
            render_dual_header("Aperçu en Direct de l'Album", "Live Album Studio Preview")
            preview_b64 = None
            if uploaded_diary_photo is not None:
                preview_b64 = f"data:image/jpeg;base64,{base64.b64encode(uploaded_diary_photo.getvalue()).decode('utf-8')}"

            render_album_preview_card(
                entry_date=entry_date_val.strftime("%Y-%m-%d"),
                lyon_spot=selected_spot,
                diary_text=diary_narrative,
                theme_name=chosen_theme,
                font_name=chosen_font,
                image_b64=preview_b64,
            )

            # LOGIC: PDF Export Engine Download Button
            render_dual_header("Exportation PDF Haute Définition", "PDF Album Export Engine")
            pdf_bytes = generate_album_pdf(
                profile=profile,
                entries=st.session_state.diary_entries,
                default_theme_name=chosen_theme,
                default_font_name=chosen_font,
            )
            st.download_button(
                label="📥 Télécharger l'Album Photo & Journal (.PDF) | Download Styled PDF Album",
                data=pdf_bytes,
                file_name=f"Explorer_Quest_Lyon_{profile['explorer_name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        # LOGIC: Display Saved Diary Entries Archive with Live Theme Styling
        st.markdown("---")
        render_dual_header(
            f"Pages Enregistrées dans l'Album ({len(st.session_state.diary_entries)})",
            "Saved Lyon Diary & Photo Archive",
        )
        if not st.session_state.diary_entries:
            st.info("Votre album est prêt, Explorer ! Ajoutez votre première photo et note de voyage ci-dessus. | Your album is ready, Explorer!")
        else:
            for item in st.session_state.diary_entries:
                img_uri = image_file_to_base64(item.get("image_path"))
                render_album_preview_card(
                    entry_date=item["entry_date"],
                    lyon_spot=item["lyon_spot"],
                    diary_text=item["diary_text"],
                    theme_name=item["album_theme"],
                    font_name=item["album_font"],
                    image_b64=img_uri,
                )
                if st.button(f"🗑️ Supprimer l'entrée #{item['id']} | Delete Entry", key=f"del_entry_{item['id']}"):
                    delete_diary_entry(item["id"])
                    st.session_state.diary_entries = load_diary_entries()
                    st.rerun()

    # ==========================================================================
    # TAB 4: REAL-WORLD COUPON STORE (BOUTIQUE DE COUPONS)
    # ==========================================================================
    with tab4:
        render_dual_header(
            "Boutique de Coupons Partenaires à Lyon",
            "Real-World Coupon Store — Redeem Explorer Points for Local Lyon Vouchers",
        )

        st.markdown(
            f"""
            <div class="lyon-card" style="background: #14213D; color: #FFFFFF;">
                <span style="font-size: 1.05rem;">
                    💰 Solde Disponible / Available Wallet : <strong style="color: #F4D58D; font-size: 1.25rem;">{profile['available_points']} pts</strong>
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    🏅 XP Total (Rang / Tier) : <strong>{profile['total_points']} pts</strong>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cpn_cols = st.columns(2)
        for idx, cpn in enumerate(COUPON_CATALOG):
            with cpn_cols[idx % 2]:
                can_afford = profile["available_points"] >= cpn["cost"]
                st.markdown(
                    f"""
                    <div class="lyon-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span class="badge-pill">{cpn['category']}</span>
                            <span class="pts-pill">{cpn['cost']} PTS</span>
                        </div>
                        <h4 style="font-family: 'Playfair Display', serif; color: #14213D; margin: 0.6rem 0 0.15rem 0;">
                            {cpn['partner']}
                        </h4>
                        <div style="font-size: 0.78rem; color: #6C757D; margin-bottom: 0.5rem;">📍 {cpn['district']}</div>
                        <p style="font-weight: 600; color: #1B2432; margin-bottom: 0.25rem;">🇫🇷 {cpn['offer_fr']}</p>
                        <p style="font-size: 0.88rem; color: #4A5568; font-style: italic; margin-bottom: 0.4rem;">🇬🇧 {cpn['offer_en']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"🎟️ Échanger ({cpn['cost']} pts) | Redeem Voucher",
                    key=f"redeem_{cpn['id']}",
                    disabled=not can_afford,
                    use_container_width=True,
                ):
                    voucher_code = f"LYON-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
                    new_coupon_record = {
                        "coupon_id": cpn["id"],
                        "partner": cpn["partner"],
                        "offer_en": cpn["offer_en"],
                        "cost": cpn["cost"],
                        "code": voucher_code,
                        "redeemed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    updated_coupons = list(profile["redeemed_coupons"]) + [new_coupon_record]
                    save_explorer_profile(
                        explorer_name=profile["explorer_name"],
                        total_points=profile["total_points"],
                        solved_riddles=profile["solved_riddles"],
                        solved_quests=profile["solved_quests"],
                        redeemed_coupons=updated_coupons,
                    )
                    st.session_state.profile = load_explorer_profile()
                    st.balloons()
                    st.success(f"Coupon débloqué pour Explorer ! Code : **{voucher_code}**")
                    st.rerun()

        # LOGIC: Wallet of Redeemed Real-World Lyon Vouchers
        st.markdown("---")
        render_dual_header(
            f"Portefeuille de Coupons Actifs ({len(profile['redeemed_coupons'])})",
            "Explorer's Redeemed Lyon Voucher Wallet",
        )
        if not profile["redeemed_coupons"]:
            st.info("Aucun coupon échangé pour l'instant. Résolvez des énigmes pour gagner des points ! | No vouchers redeemed yet.")
        else:
            for v in reversed(profile["redeemed_coupons"]):
                st.markdown(
                    f"""
                    <div class="lyon-card" style="border-left: 5px solid #2D6A4F;">
                        <strong>🎟️ {v['partner']}</strong> — <code>{v['code']}</code><br/>
                        <span style="font-size: 0.9rem;">{v['offer_en']}</span><br/>
                        <span style="font-size: 0.78rem; color: #6C757D;">Échangé le / Redeemed: {v['redeemed_at']} ({v['cost']} pts)</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ==========================================================================
    # TAB 5: SQLITE DATABASE PERSISTENCE INSPECTOR (PROFIL & JOURNAL)
    # ==========================================================================
    with tab5:
        render_dual_header(
            "Base de Données SQLite & Sauvegarde Automatique",
            "SQLite Persistence Inspector (`explorer_lyon.db`)",
        )
        st.write(
            f"Toutes vos statistiques d'Explorer, énigmes résolues, quêtes photo, coupons et pages d'album sont persistés automatiquement dans **`{DB_PATH}`**."
        )

        db_c1, db_c2 = st.columns(2)
        with db_c1:
            st.subheader("Table: `explorer_profile`")
            st.json(
                {
                    "explorer_name": profile["explorer_name"],
                    "total_points": profile["total_points"],
                    "available_points": profile["available_points"],
                    "current_tier": profile["current_tier"],
                    "solved_riddles": profile["solved_riddles"],
                    "solved_quests": profile["solved_quests"],
                    "redeemed_coupons_count": len(profile["redeemed_coupons"]),
                }
            )
        with db_c2:
            st.subheader("Table: `diary_entries`")
            st.json(st.session_state.diary_entries)

        st.markdown("---")
        if st.button("⚠️ Réinitialiser la Progression (Garder le Journal) | Reset Points & Quests"):
            save_explorer_profile(
                explorer_name=profile["explorer_name"],
                total_points=0,
                solved_riddles=[],
                solved_quests=[],
                redeemed_coupons=[],
            )
            st.session_state.profile = load_explorer_profile()
            st.toast("Progression réinitialisée pour une nouvelle expédition à Lyon !")
            st.rerun()


if __name__ == "__main__":
    main()