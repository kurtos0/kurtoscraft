#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 KURTOSCRAFT  -  un jeu de type Minecraft en Python + pygame + OpenGL
==========================================================================
 Installation (une seule fois) :
     pip install pygame PyOpenGL numpy
 Lancement :
     python kurtoscraft.py          (ou "Run file as script" dans Pyzo)

 Les sauvegardes sont dans le dossier  ~/.kurtoscraft/
 Les textures sont GENEREES par le code (aucun fichier image necessaire).
 Si vous voulez vos propres textures, mettez des PNG 16x16 dans
 ~/.kurtoscraft/textures/  (ex : stone.png, dirt.png, grass_top.png ...)
 Le nom du fichier = le nom de la texture (voir la liste TILE_NAMES plus bas).
==========================================================================
"""
import os, sys, math, time, json, random, shutil, ctypes, struct, zlib, zipfile, tempfile, subprocess, re

try:
    import numpy as np
    import OpenGL
    OpenGL.ERROR_CHECKING = False      # beaucoup plus rapide
    OpenGL.ERROR_LOGGING = False
    import pygame
    from OpenGL import GL as gl
except ImportError as _e:                                   # pragma: no cover
    print("\n*** Il manque un module : %s" % _e)
    print("*** Sur Linux Mint, tapez dans un terminal :")
    print("***     sudo apt install python3-numpy python3-pygame python3-opengl")
    print("*** (ou :  pip install pygame PyOpenGL numpy )\n")
    raise

# ----------------------------------------------------------------------------
# REGLAGES TECHNIQUES (vous pouvez les modifier)
# ----------------------------------------------------------------------------
WIN_W, WIN_H = 1280, 720      # taille de la fenetre
FULLSCREEN = False            # True = plein ecran
EXPORT_TEXTURES = False       # True = ecrit toutes les textures en PNG dans ~/.kurtoscraft/textures/ (une fois)
GUI_W, GUI_H = 960, 540       # resolution logique des menus / de l'interface
CHUNK = 16                    # taille d'un chunk (X et Z)
WORLD_H = 128                 # hauteur du monde (Y)
WORLD_SIZE = 1000             # le monde fait 1000 x 1000 blocs
NCH = (WORLD_SIZE + CHUNK - 1) // CHUNK   # nombre de chunks par cote (63)
SEA = 32                      # niveau de la mer
DAY_LEN = 720.0               # duree d'un jour complet (secondes)
SAVE_DIR = os.path.join(os.path.expanduser("~"), ".kurtoscraft")
WORLDS_DIR = os.path.join(SAVE_DIR, "worlds")
TEXTURE_DIR = os.path.join(SAVE_DIR, "textures")

# ----------------------------------------------------------------------------
# LANGUES
# ----------------------------------------------------------------------------
LANGS = ["en", "fr", "de", "es", "it", "ru", "th"]
LANG_LABEL = {"en": "English", "fr": "Français", "de": "Deutsch", "es": "Español",
              "it": "Italiano", "ru": "Русский", "th": "ไทย"}
_lang = ["fr"]


def set_lang(code):
    _lang[0] = code if code in LANGS else "en"


def tr(key):
    v = STR.get(key)
    if v is None:
        return key
    return v[LANGS.index(_lang[0])]


STR = {
    "play": ("Play", "Jouer", "Spielen", "Jugar"),
    "settings": ("Settings", "Paramètres", "Einstellungen", "Ajustes"),
    "language": ("Language", "Langue", "Sprache", "Idioma"),
    "quit": ("Quit game", "Quitter le jeu", "Spiel beenden", "Salir del juego"),
    "back": ("Back", "Retour", "Zurück", "Volver"),
    "select_world": ("Select World", "Choisir un monde", "Welt auswählen", "Seleccionar mundo"),
    "play_selected": ("Play selected world", "Jouer au monde sélectionné", "Gewählte Welt spielen", "Jugar al mundo seleccionado"),
    "new_world": ("Create New World", "Créer un nouveau monde", "Neue Welt erstellen", "Crear mundo nuevo"),
    "delete_world": ("Delete", "Supprimer", "Löschen", "Eliminar"),
    "no_worlds": ("No worlds yet. Create one!", "Aucun monde pour l'instant. Crées-en un !",
                  "Noch keine Welten. Erstelle eine!", "Aún no hay mundos. ¡Crea uno!"),
    "world_name": ("World name", "Nom du monde", "Weltname", "Nombre del mundo"),
    "seed": ("Seed (optional)", "Graine (facultatif)", "Startwert (optional)", "Semilla (opcional)"),
    "mode_survival": ("Game mode: Survival", "Mode de jeu : Survie", "Spielmodus: Überleben", "Modo de juego: Supervivencia"),
    "mode_creative": ("Game mode: Creative", "Mode de jeu : Créatif", "Spielmodus: Kreativ", "Modo de juego: Creativo"),
    "survival": ("Survival", "Survie", "Überleben", "Supervivencia"),
    "creative": ("Creative", "Créatif", "Kreativ", "Creativo"),
    "creative_inv": ("Creative Inventory", "Inventaire créatif", "Kreativ-Inventar", "Inventario creativo"),
    "creative_hint": ("Press E for the creative inventory - double-tap Space to fly",
                      "E : inventaire créatif - double appui sur Espace pour voler",
                      "E: Kreativ-Inventar - Leertaste doppelt drücken zum Fliegen",
                      "E: inventario creativo - doble toque en Espacio para volar"),
    "create_world": ("Create World", "Créer le monde", "Welt erstellen", "Crear mundo"),
    "create_title": ("Create New World", "Créer un nouveau monde", "Neue Welt erstellen", "Crear mundo nuevo"),
    "default_world": ("New World", "Nouveau monde", "Neue Welt", "Mundo nuevo"),
    "loading": ("Loading world...", "Chargement du monde...", "Welt wird geladen...", "Cargando mundo..."),
    "generating": ("Generating terrain", "Génération du terrain", "Gelände wird erzeugt", "Generando terreno"),
    "saving": ("Saving world...", "Sauvegarde du monde...", "Welt wird gespeichert...", "Guardando mundo..."),
    "resume": ("Back to game", "Retour au jeu", "Zurück zum Spiel", "Volver al juego"),
    "save_quit": ("Save and quit to title", "Sauvegarder et quitter", "Speichern und beenden", "Guardar y salir"),
    "game_menu": ("Game Menu", "Menu du jeu", "Spielmenü", "Menú del juego"),
    "you_died": ("You died!", "Vous êtes mort !", "Du bist gestorben!", "¡Has muerto!"),
    "respawn": ("Respawn", "Réapparaître", "Wiederbeleben", "Reaparecer"),
    "controls": ("Controls", "Touches", "Steuerung", "Controles"),
    "render_dist": ("Render distance", "Distance de rendu", "Sichtweite", "Distancia de renderizado"),
    "sens": ("Mouse sensitivity", "Sensibilité souris", "Mausempfindlichkeit", "Sensibilidad del ratón"),
    "inventory": ("Inventory", "Inventaire", "Inventar", "Inventario"),
    "crafting": ("Crafting", "Fabrication", "Handwerk", "Fabricación"),
    "last_played": ("Last played", "Dernière partie", "Zuletzt gespielt", "Última partida"),
    "world_border": ("You reached the edge of the world", "Vous avez atteint le bord du monde",
                     "Du hast den Rand der Welt erreicht", "Has llegado al borde del mundo"),
    "name_taken": ("A world with this name exists", "Un monde porte déjà ce nom",
                   "Diese Welt existiert bereits", "Ya existe un mundo con ese nombre"),
    "confirm_delete": ("Click again to delete", "Cliquez encore pour supprimer",
                       "Nochmals klicken zum Löschen", "Haz clic otra vez para eliminar"),
}

CONTROLS = [
    ("W A S D", ("Move", "Se déplacer", "Bewegen", "Moverse")),
    ("Space", ("Jump / swim up", "Sauter / nager vers le haut", "Springen / hochschwimmen", "Saltar / nadar hacia arriba")),
    ("Shift", ("Sneak (slower)", "Marcher lentement", "Schleichen (langsamer)", "Caminar despacio")),
    ("Ctrl", ("Sprint", "Courir", "Sprinten", "Correr")),
    ("Mouse", ("Look around", "Regarder autour", "Umschauen", "Mirar alrededor")),
    ("Left click", ("Break block / attack (hold)", "Casser un bloc / attaquer (maintenir)",
                    "Block abbauen / angreifen (halten)", "Romper bloque / atacar (mantener)")),
    ("Right click", ("Place block / use / eat", "Poser un bloc / utiliser / manger",
                     "Block setzen / benutzen / essen", "Colocar bloque / usar / comer")),
    ("1-9 / Wheel", ("Select hotbar slot", "Choisir l'emplacement de la barre",
                     "Schnellleiste wählen", "Elegir ranura de la barra")),
    ("E", ("Inventory & crafting", "Inventaire et fabrication", "Inventar & Handwerk", "Inventario y fabricación")),
    ("2 x Space", ("Fly (creative mode)", "Voler (mode créatif)", "Fliegen (Kreativ)", "Volar (modo creativo)")),
    ("Q", ("Drop item", "Jeter l'objet", "Gegenstand fallen lassen", "Soltar objeto")),
    ("M / Esc", ("Game menu", "Menu du jeu", "Spielmenü", "Menú del juego")),
    ("F3", ("Debug info", "Infos de debug", "Debug-Infos", "Información de depuración")),
]

# ----------------------------------------------------------------------------
# BLOCS ET OBJETS
# ----------------------------------------------------------------------------
(AIR, STONE, GRASS, DIRT, COBBLE, PLANKS, BEDROCK, WATER, SAND, GRAVEL, LOG, LEAVES,
 COAL_ORE, IRON_ORE, GOLD_ORE, DIAMOND_ORE, TABLE) = range(17)
NUM_BLOCKS = 17
(STICK, COAL, IRON_INGOT, GOLD_INGOT, DIAMOND) = range(100, 105)
(RAW_PORK, RAW_BEEF, RAW_CHICKEN, FEATHER, LEATHER, BONE, GUNPOWDER, ROTTEN) = range(130, 138)

# --- blocs ajoutes (les variantes = orientations / etats) ---
CHEST, FURNACE, FURNACE_LIT = 140, 144, 148        # 140-143 coffre, 144-147 four, 148-151 four allume
COAL_BLOCK, IRON_BLOCK, GOLD_BLOCK, DIAMOND_BLOCK, GLASS = 152, 153, 154, 155, 156
DOOR0 = 160            # 160..175 : 160 + 8*(moitie haute) + 4*(ouverte) + orientation
# --- objets ajoutes ---
RAW_IRON, RAW_GOLD, COOKED_PORK, COOKED_BEEF, COOKED_CHICKEN, DOOR_ITEM = 300, 301, 302, 303, 304, 305
GOLD_TOOL0 = 310       # 310..313 : pioche, hache, pelle, epee en or
ARMOR0 = 320           # 320..335 : 320 + 4*materiau (cuir, fer, or, diamant) + piece (casque, plastron, jambieres, bottes)

# --- module bateaux ---
NAVAL_TABLE = 240                                      # bloc : table de construction navale
BUCKET, WATER_BUCKET = 5000, 5001
ROWBOAT, DRAKKAR, MOTORBOAT, LINER = 5010, 5011, 5012, 5013
ENGINE, HULL_IRON, WINDSHIELD = 5020, 5021, 5022
L_BOW, L_STERN, L_MID1, L_MID2 = 5030, 5031, 5032, 5033
L_WS_TOP, L_WS_BOT = 5034, 5035
L_HULL, L_WS, L_ENGINE = 5040, 5041, 5042
SLOT_LOCK = 5090                                       # case "occupee" (le paquebot prend 6 cases)
BOAT_ITEMS = {ROWBOAT: "rowboat", DRAKKAR: "drakkar", MOTORBOAT: "motorboat", LINER: "liner"}
WATER_SECONDS = 50.0                                   # secondes de vapeur par seau d'eau

MATS = ["wood", "stone", "iron", "diamond"]
KINDS = ["pickaxe", "axe", "shovel", "sword"]
TOOLS = {}          # id -> (kind, tier 1..4, vitesse, degats)
_SPEED = [2.0, 4.0, 6.0, 8.0]
_DMG = {"pickaxe": [2, 3, 4, 5], "axe": [3, 4, 5, 6], "shovel": [1.5, 2.5, 3.5, 4.5], "sword": [4, 5, 6, 7]}
TOOL_ID = {}
for _ki, _k in enumerate(KINDS):
    for _ti, _m in enumerate(MATS):
        _id = 110 + _ki * 4 + _ti
        TOOLS[_id] = (_k, _ti + 1, _SPEED[_ti], _DMG[_k][_ti])
        TOOL_ID[(_k, _ti)] = _id

GOLD_TOOL = {}         # genre -> identifiant de l'outil en or
for _ki, _k in enumerate(KINDS):
    GOLD_TOOL[_k] = GOLD_TOOL0 + _ki
    TOOLS[GOLD_TOOL0 + _ki] = (_k, 1, 12.0, _DMG[_k][0])      # comme le bois mais tres rapide

ARMOR = {}             # objet -> (piece 0..3, points de protection)
_ARMOR_POINTS = [[1, 3, 2, 1], [2, 6, 5, 2], [2, 5, 3, 1], [3, 8, 6, 3]]
for _mi in range(4):
    for _pi in range(4):
        ARMOR[ARMOR0 + 4 * _mi + _pi] = (_pi, _ARMOR_POINTS[_mi][_pi])

FOODS = {RAW_PORK: 3, RAW_BEEF: 3, RAW_CHICKEN: 2, ROTTEN: 1, COOKED_PORK: 8, COOKED_BEEF: 8, COOKED_CHICKEN: 6}
SMELT_TIME = 10.0      # secondes pour cuire un objet
SMELT = {RAW_IRON: (IRON_INGOT, 1), RAW_GOLD: (GOLD_INGOT, 1), COBBLE: (STONE, 1), SAND: (GLASS, 1),
         RAW_PORK: (COOKED_PORK, 1), RAW_BEEF: (COOKED_BEEF, 1), RAW_CHICKEN: (COOKED_CHICKEN, 1)}
FUEL = {COAL: 80.0, COAL_BLOCK: 800.0, LOG: 15.0, PLANKS: 15.0, STICK: 5.0}   # secondes de combustion

NAMES = {
    STONE: ("Stone", "Pierre", "Stein", "Piedra"),
    GRASS: ("Grass Block", "Bloc d'herbe", "Grasblock", "Bloque de hierba"),
    DIRT: ("Dirt", "Terre", "Erde", "Tierra"),
    COBBLE: ("Cobblestone", "Pavé", "Bruchstein", "Adoquín"),
    PLANKS: ("Wood Planks", "Planches de chêne", "Eichenbretter", "Tablones de roble"),
    BEDROCK: ("Bedrock", "Bedrock", "Grundgestein", "Lecho de roca"),
    WATER: ("Water", "Eau", "Wasser", "Agua"),
    SAND: ("Sand", "Sable", "Sand", "Arena"),
    GRAVEL: ("Gravel", "Gravier", "Kies", "Grava"),
    LOG: ("Oak Log", "Bûche de chêne", "Eichenstamm", "Tronco de roble"),
    LEAVES: ("Leaves", "Feuilles", "Blätter", "Hojas"),
    COAL_ORE: ("Coal Ore", "Minerai de charbon", "Kohleerz", "Mineral de carbón"),
    IRON_ORE: ("Iron Ore", "Minerai de fer", "Eisenerz", "Mineral de hierro"),
    GOLD_ORE: ("Gold Ore", "Minerai d'or", "Golderz", "Mineral de oro"),
    DIAMOND_ORE: ("Diamond Ore", "Minerai de diamant", "Diamanterz", "Mineral de diamante"),
    TABLE: ("Crafting Table", "Établi", "Werkbank", "Mesa de crafteo"),
    STICK: ("Stick", "Bâton", "Stock", "Palo"),
    COAL: ("Coal", "Charbon", "Kohle", "Carbón"),
    IRON_INGOT: ("Iron Ingot", "Lingot de fer", "Eisenbarren", "Lingote de hierro"),
    GOLD_INGOT: ("Gold Ingot", "Lingot d'or", "Goldbarren", "Lingote de oro"),
    DIAMOND: ("Diamond", "Diamant", "Diamant", "Diamante"),
    RAW_PORK: ("Raw Porkchop", "Porc cru", "Rohes Schweinefleisch", "Cerdo crudo"),
    RAW_BEEF: ("Raw Beef", "Bœuf cru", "Rohes Rindfleisch", "Ternera cruda"),
    RAW_CHICKEN: ("Raw Chicken", "Poulet cru", "Rohes Hühnchen", "Pollo crudo"),
    FEATHER: ("Feather", "Plume", "Feder", "Pluma"),
    LEATHER: ("Leather", "Cuir", "Leder", "Cuero"),
    BONE: ("Bone", "Os", "Knochen", "Hueso"),
    GUNPOWDER: ("Gunpowder", "Poudre à canon", "Schießpulver", "Pólvora"),
    ROTTEN: ("Rotten Flesh", "Chair putréfiée", "Verrottetes Fleisch", "Carne podrida"),
}
_MATN = [("Wooden", "Stone", "Iron", "Diamond"), ("en bois", "en pierre", "en fer", "en diamant"),
         ("Holz", "Stein", "Eisen", "Diamant"), ("de madera", "de piedra", "de hierro", "de diamante")]
_KINDN = [("Pickaxe", "Axe", "Shovel", "Sword"), ("Pioche", "Hache", "Pelle", "Épée"),
          ("spitzhacke", "axt", "schaufel", "schwert"), ("Pico", "Hacha", "Pala", "Espada")]
for (_k, _t), _id in TOOL_ID.items():
    _ki = KINDS.index(_k)
    NAMES[_id] = ("%s %s" % (_MATN[0][_t], _KINDN[0][_ki]),
                  "%s %s" % (_KINDN[1][_ki], _MATN[1][_t]),
                  "%s%s" % (_MATN[2][_t], _KINDN[2][_ki]),
                  "%s %s" % (_KINDN[3][_ki], _MATN[3][_t]))


# ---------------------------------------------------------------------------
# LANGUES SUPPLEMENTAIRES : italien, russe, thai (ajoutees aux tuples ci-dessus)
# ---------------------------------------------------------------------------
STR_X = {
    "play": ("Gioca", "Играть", "เล่น"),
    "settings": ("Impostazioni", "Настройки", "การตั้งค่า"),
    "language": ("Lingua", "Язык", "ภาษา"),
    "quit": ("Esci dal gioco", "Выйти из игры", "ออกจากเกม"),
    "back": ("Indietro", "Назад", "กลับ"),
    "select_world": ("Seleziona mondo", "Выбор мира", "เลือกโลก"),
    "play_selected": ("Gioca nel mondo selezionato", "Играть в выбранный мир", "เล่นโลกที่เลือก"),
    "new_world": ("Crea nuovo mondo", "Создать новый мир", "สร้างโลกใหม่"),
    "delete_world": ("Elimina", "Удалить", "ลบ"),
    "no_worlds": ("Nessun mondo ancora. Creane uno!", "Миров пока нет. Создайте новый!", "ยังไม่มีโลก สร้างโลกใหม่เลย!"),
    "world_name": ("Nome del mondo", "Название мира", "ชื่อโลก"),
    "seed": ("Seme (facoltativo)", "Зерно генерации (необязательно)", "ซีด (ไม่บังคับ)"),
    "mode_survival": ("Modalità di gioco: Sopravvivenza", "Режим игры: Выживание", "โหมดเกม: เอาชีวิตรอด"),
    "mode_creative": ("Modalità di gioco: Creativa", "Режим игры: Творческий", "โหมดเกม: สร้างสรรค์"),
    "survival": ("Sopravvivenza", "Выживание", "เอาชีวิตรอด"),
    "creative": ("Creativa", "Творческий", "สร้างสรรค์"),
    "creative_inv": ("Inventario creativo", "Творческий инвентарь", "คลังสร้างสรรค์"),
    "creative_hint": ("E: inventario creativo - doppio tocco su Spazio per volare",
                      "E: творческий инвентарь - дважды нажмите Пробел, чтобы лететь",
                      "E: คลังสร้างสรรค์ - กดเว้นวรรคสองครั้งเพื่อบิน"),
    "create_title": ("Crea nuovo mondo", "Создание нового мира", "สร้างโลกใหม่"),
    "create_world": ("Crea mondo", "Создать мир", "สร้างโลก"),
    "default_world": ("Nuovo mondo", "Новый мир", "โลกใหม่"),
    "loading": ("Caricamento del mondo...", "Загрузка мира...", "กำลังโหลดโลก..."),
    "generating": ("Generazione del terreno", "Генерация местности", "กำลังสร้างภูมิประเทศ"),
    "saving": ("Salvataggio del mondo...", "Сохранение мира...", "กำลังบันทึกโลก..."),
    "resume": ("Torna al gioco", "Вернуться в игру", "กลับไปเล่นต่อ"),
    "save_quit": ("Salva ed esci", "Сохранить и выйти", "บันทึกและออก"),
    "game_menu": ("Menu di gioco", "Меню игры", "เมนูเกม"),
    "you_died": ("Sei morto!", "Вы погибли!", "คุณตายแล้ว!"),
    "respawn": ("Rinasci", "Возродиться", "เกิดใหม่"),
    "controls": ("Controlli", "Управление", "การควบคุม"),
    "render_dist": ("Distanza di rendering", "Дальность прорисовки", "ระยะการมองเห็น"),
    "sens": ("Sensibilità mouse", "Чувствительность мыши", "ความไวเมาส์"),
    "inventory": ("Inventario", "Инвентарь", "คลังของ"),
    "crafting": ("Creazione", "Крафт", "คราฟต์"),
    "last_played": ("Ultima partita", "Последняя игра", "เล่นล่าสุด"),
    "world_border": ("Hai raggiunto il confine del mondo", "Вы достигли края мира", "คุณมาถึงขอบโลกแล้ว"),
    "name_taken": ("Esiste già un mondo con questo nome", "Мир с таким названием уже существует", "มีโลกชื่อนี้อยู่แล้ว"),
    "confirm_delete": ("Clicca ancora per eliminare", "Нажмите ещё раз для удаления", "กดอีกครั้งเพื่อลบ"),
}
for _k, _v in STR_X.items():
    STR[_k] = STR[_k] + _v

STR.update({
    "mods": ("Mods", "Mods", "Mods", "Mods", "Mod", "Моды", "ม็อด"),
    "mods_title": ("Mods of this world", "Mods de ce monde", "Mods dieser Welt", "Mods de este mundo",
                   "Mod di questo mondo", "Моды этого мира", "ม็อดของโลกนี้"),
    "mods_drop": ("Drag and drop the mod file here (.zip or .json)",
                  "Glissez-déposez ici le fichier du mod (.zip ou .json)",
                  "Mod-Datei hierher ziehen (.zip oder .json)",
                  "Arrastra aquí el archivo del mod (.zip o .json)",
                  "Trascina qui il file del mod (.zip o .json)",
                  "Перетащите сюда файл мода (.zip или .json)",
                  "ลากไฟล์ม็อดมาวางที่นี่ (.zip หรือ .json)"),
    "mods_choose": ("Choose a file...", "Choisir un fichier...", "Datei auswählen...", "Elegir un archivo...",
                    "Scegli un file...", "Выбрать файл...", "เลือกไฟล์..."),
    "mods_none": ("No mods installed in this world", "Aucun mod installé dans ce monde",
                  "Keine Mods in dieser Welt installiert", "No hay mods instalados en este mundo",
                  "Nessun mod installato in questo mondo", "В этом мире нет модов", "ยังไม่มีม็อดในโลกนี้"),
    "mods_on": ("Enabled", "Activé", "Aktiv", "Activado", "Attivo", "Включён", "เปิดอยู่"),
    "mods_off": ("Disabled", "Désactivé", "Inaktiv", "Desactivado", "Disattivo", "Выключен", "ปิดอยู่"),
    "mods_remove": ("Remove", "Supprimer", "Entfernen", "Quitar", "Rimuovi", "Удалить", "ลบ"),
    "mods_ok": ("Mod installed: %s", "Mod installé : %s", "Mod installiert: %s", "Mod instalado: %s",
                "Mod installato: %s", "Мод установлен: %s", "ติดตั้งม็อดแล้ว: %s"),
    "mods_fail": ("Could not install: %s", "Installation impossible : %s", "Installation fehlgeschlagen: %s",
                  "No se pudo instalar: %s", "Impossibile installare: %s", "Не удалось установить: %s",
                  "ติดตั้งไม่สำเร็จ: %s"),
    "mods_note": ("Changes apply when the world is loaded", "Les changements s'appliquent au chargement du monde",
                  "Änderungen gelten beim Laden der Welt", "Los cambios se aplican al cargar el mundo",
                  "Le modifiche si applicano al caricamento del mondo", "Изменения вступят в силу при загрузке мира",
                  "การเปลี่ยนแปลงจะมีผลเมื่อโหลดโลก"),
    "mods_browse": ("Select a mod file", "Choisissez le fichier du mod", "Mod-Datei wählen",
                    "Elige el archivo del mod", "Scegli il file del mod", "Выберите файл мода", "เลือกไฟล์ม็อด"),
    "mods_up": ("Parent folder", "Dossier parent", "Übergeordneter Ordner", "Carpeta superior",
                "Cartella superiore", "Родительская папка", "โฟลเดอร์ก่อนหน้า"),
    "mods_waiting": ("Waiting for the file window...", "En attente de la fenêtre de sélection...",
                     "Warte auf das Dateifenster...", "Esperando la ventana de selección...",
                     "In attesa della finestra di selezione...", "Ожидание окна выбора файла...",
                     "กำลังรอหน้าต่างเลือกไฟล์..."),
    "mods_world": ("World", "Monde", "Welt", "Mundo", "Mondo", "Мир", "โลก"),
})

STR.update({
    "recipes": ("Recipes", "Recettes", "Rezepte", "Recetas", "Ricette", "Рецепты", "สูตร"),
    "armor": ("Armor", "Armure", "Rüstung", "Armadura", "Armatura", "Броня", "เกราะ"),
    "no_recipes": ("Nothing to craft yet", "Rien à fabriquer pour l'instant", "Noch nichts herstellbar",
                   "Nada que fabricar todavía", "Niente da creare per ora", "Пока нечего создавать",
                   "ยังไม่มีอะไรให้คราฟต์"),
    "needs": ("Needs:", "Nécessite :", "Benötigt:", "Necesita:", "Richiede:", "Нужно:", "ต้องใช้:"),
})

CONTROLS_X = [
    ("Muoversi", "Движение", "เดิน"),
    ("Salta / nuota verso l'alto", "Прыжок / плыть вверх", "กระโดด / ว่ายขึ้น"),
    ("Cammina piano", "Красться (медленнее)", "ย่องเดิน (ช้าลง)"),
    ("Corri", "Бег", "วิ่ง"),
    ("Guardati intorno", "Осмотреться", "มองรอบๆ"),
    ("Rompi blocco / attacca (tieni premuto)", "Ломать / атаковать (держать)", "ทุบบล็อก / โจมตี (กดค้าง)"),
    ("Piazza blocco / usa / mangia", "Поставить блок / использовать / есть", "วางบล็อก / ใช้ / กิน"),
    ("Scegli slot della barra", "Выбор ячейки панели", "เลือกช่องแถบด่วน"),
    ("Inventario e creazione", "Инвентарь и крафт", "คลังของและคราฟต์"),
    ("Vola (modalità creativa)", "Полёт (творческий режим)", "บิน (โหมดสร้างสรรค์)"),
    ("Getta l'oggetto", "Выбросить предмет", "ทิ้งไอเทม"),
    ("Menu di gioco", "Меню игры", "เมนูเกม"),
    ("Info di debug", "Отладочная информация", "ข้อมูลดีบัก"),
]
CONTROLS[:] = [(k, acts + CONTROLS_X[i]) for i, (k, acts) in enumerate(CONTROLS)]

NAMES_X = {
    STONE: ("Pietra", "Камень", "หิน"), GRASS: ("Blocco d'erba", "Блок травы", "บล็อกหญ้า"),
    DIRT: ("Terra", "Земля", "ดิน"), COBBLE: ("Ciottolo", "Булыжник", "หินกรวด"),
    PLANKS: ("Assi di quercia", "Дубовые доски", "แผ่นไม้โอ๊ก"),
    BEDROCK: ("Substrato roccioso", "Коренная порода", "หินฐานราก"),
    WATER: ("Acqua", "Вода", "น้ำ"), SAND: ("Sabbia", "Песок", "ทราย"), GRAVEL: ("Ghiaia", "Гравий", "กรวด"),
    LOG: ("Tronco di quercia", "Дубовое бревно", "ท่อนไม้โอ๊ก"), LEAVES: ("Foglie", "Листва", "ใบไม้"),
    COAL_ORE: ("Minerale di carbone", "Угольная руда", "แร่ถ่านหิน"),
    IRON_ORE: ("Minerale di ferro", "Железная руда", "แร่เหล็ก"),
    GOLD_ORE: ("Minerale d'oro", "Золотая руда", "แร่ทอง"),
    DIAMOND_ORE: ("Minerale di diamante", "Алмазная руда", "แร่เพชร"),
    TABLE: ("Banco da lavoro", "Верстак", "โต๊ะคราฟต์"),
    STICK: ("Bastone", "Палка", "ไม้"), COAL: ("Carbone", "Уголь", "ถ่านหิน"),
    IRON_INGOT: ("Lingotto di ferro", "Железный слиток", "แท่งเหล็ก"),
    GOLD_INGOT: ("Lingotto d'oro", "Золотой слиток", "แท่งทอง"),
    DIAMOND: ("Diamante", "Алмаз", "เพชร"),
    RAW_PORK: ("Maiale crudo", "Сырая свинина", "เนื้อหมูดิบ"),
    RAW_BEEF: ("Manzo crudo", "Сырая говядина", "เนื้อวัวดิบ"),
    RAW_CHICKEN: ("Pollo crudo", "Сырая курица", "เนื้อไก่ดิบ"),
    FEATHER: ("Piuma", "Перо", "ขนนก"), LEATHER: ("Cuoio", "Кожа", "หนัง"), BONE: ("Osso", "Кость", "กระดูก"),
    GUNPOWDER: ("Polvere da sparo", "Порох", "ดินปืน"), ROTTEN: ("Carne marcia", "Гнилая плоть", "เนื้อเน่า"),
}
_RU_TOOLS = {"pickaxe": ["Деревянная кирка", "Каменная кирка", "Железная кирка", "Алмазная кирка"],
             "axe": ["Деревянный топор", "Каменный топор", "Железный топор", "Алмазный топор"],
             "shovel": ["Деревянная лопата", "Каменная лопата", "Железная лопата", "Алмазная лопата"],
             "sword": ["Деревянный меч", "Каменный меч", "Железный меч", "Алмазный меч"]}
_IT_KIND = ["Piccone", "Ascia", "Pala", "Spada"]
_IT_MAT = ["di legno", "di pietra", "di ferro", "di diamante"]
_TH_KIND = ["อีเต้อ", "ขวาน", "พลั่ว", "ดาบ"]
_TH_MAT = ["ไม้", "หิน", "เหล็ก", "เพชร"]
for (_k, _t), _id in TOOL_ID.items():
    _ki = KINDS.index(_k)
    NAMES_X[_id] = ("%s %s" % (_IT_KIND[_ki], _IT_MAT[_t]), _RU_TOOLS[_k][_t], "%s%s" % (_TH_KIND[_ki], _TH_MAT[_t]))
for _id, _v in NAMES_X.items():
    NAMES[_id] = NAMES[_id] + _v


# --- noms des objets ajoutes (7 langues : en fr de es it ru th) ---
NAMES.update({
    RAW_IRON: ("Raw Iron", "Fer brut", "Roheisen", "Hierro en bruto", "Ferro grezzo", "Необработанное железо", "เหล็กดิบ"),
    RAW_GOLD: ("Raw Gold", "Or brut", "Rohgold", "Oro en bruto", "Oro grezzo", "Необработанное золото", "ทองดิบ"),
    COOKED_PORK: ("Cooked Porkchop", "Porc cuit", "Gebratenes Schweinefleisch", "Cerdo cocinado", "Maiale cotto",
                  "Жареная свинина", "เนื้อหมูสุก"),
    COOKED_BEEF: ("Steak", "Steak", "Steak", "Filete", "Bistecca", "Стейк", "สเต็ก"),
    COOKED_CHICKEN: ("Cooked Chicken", "Poulet cuit", "Gebratenes Hühnchen", "Pollo cocinado", "Pollo cotto",
                     "Жареная курица", "ไก่สุก"),
    DOOR_ITEM: ("Oak Door", "Porte en chêne", "Eichentür", "Puerta de roble", "Porta di quercia", "Дубовая дверь",
                "ประตูไม้โอ๊ก"),
    CHEST: ("Chest", "Coffre", "Truhe", "Cofre", "Baule", "Сундук", "หีบ"),
    FURNACE: ("Furnace", "Four", "Ofen", "Horno", "Fornace", "Печь", "เตาหลอม"),
    COAL_BLOCK: ("Block of Coal", "Bloc de charbon", "Kohleblock", "Bloque de carbón", "Blocco di carbone",
                 "Угольный блок", "บล็อกถ่านหิน"),
    IRON_BLOCK: ("Block of Iron", "Bloc de fer", "Eisenblock", "Bloque de hierro", "Blocco di ferro",
                 "Железный блок", "บล็อกเหล็ก"),
    GOLD_BLOCK: ("Block of Gold", "Bloc d'or", "Goldblock", "Bloque de oro", "Blocco d'oro", "Золотой блок",
                 "บล็อกทอง"),
    DIAMOND_BLOCK: ("Block of Diamond", "Bloc de diamant", "Diamantblock", "Bloque de diamante",
                    "Blocco di diamante", "Алмазный блок", "บล็อกเพชร"),
    GLASS: ("Glass", "Verre", "Glas", "Vidrio", "Vetro", "Стекло", "กระจก"),
})
for _b in range(CHEST + 1, CHEST + 4):
    NAMES[_b] = NAMES[CHEST]
for _b in list(range(FURNACE + 1, FURNACE + 4)) + list(range(FURNACE_LIT, FURNACE_LIT + 4)):
    NAMES[_b] = NAMES[FURNACE]
for _b in range(DOOR0, DOOR0 + 16):
    NAMES[_b] = NAMES[DOOR_ITEM]
_GOLD_N = {"pickaxe": ("Golden Pickaxe", "Pioche en or", "Goldspitzhacke", "Pico de oro", "Piccone d'oro",
                       "Золотая кирка", "อีเต้อทอง"),
           "axe": ("Golden Axe", "Hache en or", "Goldaxt", "Hacha de oro", "Ascia d'oro", "Золотой топор", "ขวานทอง"),
           "shovel": ("Golden Shovel", "Pelle en or", "Goldschaufel", "Pala de oro", "Pala d'oro", "Золотая лопата",
                      "พลั่วทอง"),
           "sword": ("Golden Sword", "Épée en or", "Goldschwert", "Espada de oro", "Spada d'oro", "Золотой меч",
                     "ดาบทอง")}
for _k, _id in GOLD_TOOL.items():
    NAMES[_id] = _GOLD_N[_k]
_AP = [("Helmet", "Chestplate", "Leggings", "Boots"), ("Casque", "Plastron", "Jambières", "Bottes"),
       ("helm", "brustplatte", "beinschutz", "stiefel"), ("Casco", "Peto", "Pantalones", "Botas"),
       ("Elmo", "Corazza", "Gambali", "Stivali"), ("Шлем", "Нагрудник", "Поножи", "Ботинки"),
       ("หมวกเกราะ", "เสื้อเกราะ", "กางเกงเกราะ", "รองเท้าบู๊ต")]
_AM = [("Leather", "Iron", "Golden", "Diamond"), ("en cuir", "en fer", "en or", "en diamant"),
       ("Leder", "Eisen", "Gold", "Diamant"), ("de cuero", "de hierro", "de oro", "de diamante"),
       ("di cuoio", "di ferro", "d'oro", "di diamante"), None, ("หนัง", "เหล็ก", "ทอง", "เพชร")]
_RU_ADJ = [("Кожаный", "Железный", "Золотой", "Алмазный"), ("Кожаные", "Железные", "Золотые", "Алмазные")]
for _mi in range(4):
    for _pi in range(4):
        _n = []
        for _li in range(7):
            if _li == 0:
                _n.append("%s %s" % (_AM[0][_mi], _AP[0][_pi]))
            elif _li in (1, 3, 4):
                _n.append("%s %s" % (_AP[_li][_pi], _AM[_li][_mi]))
            elif _li == 2:
                _n.append(_AM[2][_mi] + _AP[2][_pi])
            elif _li == 5:
                _n.append("%s %s" % (_RU_ADJ[0 if _pi < 2 else 1][_mi], _AP[5][_pi].lower()))
            else:
                _n.append(_AP[6][_pi] + _AM[6][_mi])
        NAMES[ARMOR0 + 4 * _mi + _pi] = tuple(_n)


def item_name(i):
    n = NAMES.get(i)
    if n is None:
        return "?"
    if isinstance(n, dict):                      # objet ajoute par un mod
        return n.get(_lang[0]) or n.get("en") or next(iter(n.values()), "?")
    return n[LANGS.index(_lang[0])]


MAXSTACK = {}          # tailles de pile speciales (mods)
BDROPN = {}            # nombre d'objets lâchés par un bloc (mods) : bloc -> (min, max)


def max_stack(i):
    return MAXSTACK.get(i, 1 if (i in TOOLS or i in ARMOR) else 64)


_BOAT_NAMES = {
    NAVAL_TABLE: ("Shipwright's Table", "Table de construction navale", "Schiffbautisch", "Mesa de astillero",
                  "Tavolo da costruzione navale", "Корабельный верстак", "โต๊ะต่อเรือ"),
    BUCKET: ("Bucket", "Seau", "Eimer", "Cubo", "Secchio", "Ведро", "ถัง"),
    WATER_BUCKET: ("Water Bucket", "Seau d'eau", "Wassereimer", "Cubo de agua", "Secchio d'acqua", "Ведро воды", "ถังน้ำ"),
    ROWBOAT: ("Wooden Boat", "Bateau en bois", "Holzboot", "Bote de madera", "Barca di legno", "Деревянная лодка", "เรือไม้"),
    DRAKKAR: ("Longship (Drakkar)", "Drakkar", "Drachenboot", "Drakkar", "Drakkar", "Драккар", "เรือดรัคการ์"),
    MOTORBOAT: ("Iron Motorboat", "Bateau à moteur en fer", "Eisen-Motorboot", "Lancha de hierro", "Motoscafo di ferro",
                "Железный моторный катер", "เรือยนต์เหล็ก"),
    LINER: ("Ocean Liner", "Paquebot", "Ozeandampfer", "Transatlántico", "Transatlantico", "Океанский лайнер",
            "เรือเดินสมุทร"),
    ENGINE: ("Steam Engine", "Moteur à vapeur", "Dampfmaschine", "Motor de vapor", "Motore a vapore",
             "Паровой двигатель", "เครื่องยนต์ไอน้ำ"),
    HULL_IRON: ("Iron Hull", "Coque en fer", "Eisenrumpf", "Casco de hierro", "Scafo di ferro", "Железный корпус",
                "ตัวเรือเหล็ก"),
    WINDSHIELD: ("Windshield", "Pare-brise", "Windschutzscheibe", "Parabrisas", "Parabrezza", "Лобовое стекло", "กระจกหน้า"),
    L_BOW: ("Liner Hull: Bow", "Coque de paquebot : proue", "Dampfer-Rumpf: Bug", "Casco de transatlántico: proa",
            "Scafo del transatlantico: prua", "Корпус лайнера: нос", "ตัวเรือเดินสมุทร: หัวเรือ"),
    L_STERN: ("Liner Hull: Stern", "Coque de paquebot : poupe", "Dampfer-Rumpf: Heck", "Casco de transatlántico: popa",
              "Scafo del transatlantico: poppa", "Корпус лайнера: корма", "ตัวเรือเดินสมุทร: ท้ายเรือ"),
    L_MID1: ("Liner Hull: Front Middle", "Coque de paquebot : milieu avant", "Dampfer-Rumpf: Mitte vorn",
             "Casco de transatlántico: centro delantero", "Scafo del transatlantico: centro anteriore",
             "Корпус лайнера: середина (перед)", "ตัวเรือเดินสมุทร: กลางเรือ (หน้า)"),
    L_MID2: ("Liner Hull: Rear Middle", "Coque de paquebot : milieu arrière", "Dampfer-Rumpf: Mitte hinten",
             "Casco de transatlántico: centro trasero", "Scafo del transatlantico: centro posteriore",
             "Корпус лайнера: середина (зад)", "ตัวเรือเดินสมุทร: กลางเรือ (หลัง)"),
    L_WS_TOP: ("Liner Windshield: Top", "Pare-brise de paquebot : haut", "Dampfer-Scheibe: oben",
               "Parabrisas de transatlántico: arriba", "Parabrezza del transatlantico: alto",
               "Лобовое стекло лайнера: верх", "กระจกเรือเดินสมุทร: บน"),
    L_WS_BOT: ("Liner Windshield: Bottom", "Pare-brise de paquebot : bas", "Dampfer-Scheibe: unten",
               "Parabrisas de transatlántico: abajo", "Parabrezza del transatlantico: basso",
               "Лобовое стекло лайнера: низ", "กระจกเรือเดินสมุทร: ล่าง"),
    L_HULL: ("Liner Hull (assembled)", "Coque de paquebot (assemblée)", "Dampfer-Rumpf (montiert)",
             "Casco de transatlántico (montado)", "Scafo del transatlantico (assemblato)",
             "Корпус лайнера (собранный)", "ตัวเรือเดินสมุทร (ประกอบแล้ว)"),
    L_WS: ("Liner Windshield (assembled)", "Pare-brise de paquebot (assemblé)", "Dampfer-Scheibe (montiert)",
           "Parabrisas de transatlántico (montado)", "Parabrezza del transatlantico (assemblato)",
           "Лобовое стекло лайнера (собранное)", "กระจกเรือเดินสมุทร (ประกอบแล้ว)"),
    L_ENGINE: ("Liner Machinery (2 engines + furnace)", "Machinerie de paquebot (2 moteurs + four)",
               "Dampfer-Maschinen (2 Motoren + Ofen)", "Maquinaria de transatlántico (2 motores + horno)",
               "Macchinario del transatlantico (2 motori + fornace)", "Машины лайнера (2 двигателя + печь)",
               "เครื่องจักรเรือเดินสมุทร (เครื่องยนต์ 2 + เตา)"),
    SLOT_LOCK: ("Occupied slot (liner)", "Emplacement occupé (paquebot)", "Belegter Platz (Dampfer)",
                "Espacio ocupado (transatlántico)", "Posto occupato (transatlantico)", "Занятая ячейка (лайнер)",
                "ช่องถูกใช้ (เรือเดินสมุทร)"),
}
NAMES.update(_BOAT_NAMES)
MAXSTACK.update({BUCKET: 16, WATER_BUCKET: 1, ROWBOAT: 1, DRAKKAR: 1, MOTORBOAT: 1, LINER: 1, ENGINE: 16, HULL_IRON: 16,
                 WINDSHIELD: 16, L_BOW: 16, L_STERN: 16, L_MID1: 16, L_MID2: 16, L_WS_TOP: 16, L_WS_BOT: 16,
                 L_HULL: 1, L_WS: 1, L_ENGINE: 1, SLOT_LOCK: 1})
STR.update({
    "b_engine_empty": ("The engine is out of coal or water!  (E: open the engine)",
                       "Le moteur n'a plus de charbon ou d'eau !  (E : ouvrir le moteur)",
                       "Dem Motor fehlt Kohle oder Wasser!  (E: Motor öffnen)",
                       "¡Al motor le falta carbón o agua!  (E: abrir el motor)",
                       "Il motore è senza carbone o acqua!  (E: apri il motore)",
                       "В двигателе нет угля или воды!  (E: открыть двигатель)",
                       "เครื่องยนต์ไม่มีถ่านหินหรือน้ำ!  (E: เปิดเครื่องยนต์)"),
    "b_no_room": ("Not enough water or room here for this boat.", "Pas assez d'eau ou de place ici pour ce bateau.",
                  "Hier ist nicht genug Wasser oder Platz für dieses Boot.",
                  "No hay suficiente agua o espacio aquí para este barco.",
                  "Non c'è abbastanza acqua o spazio qui per questa barca.",
                  "Здесь недостаточно воды или места для этой лодки.", "น้ำหรือพื้นที่ตรงนี้ไม่พอสำหรับเรือลำนี้"),
    "b_already": ("There is already a boat here.", "Il y a déjà un bateau ici.", "Hier ist schon ein Boot.",
                  "Ya hay un barco aquí.", "C'è già una barca qui.", "Здесь уже есть лодка.", "ที่นี่มีเรืออยู่แล้ว"),
    "b_helm": ("At the helm!  W/S: forward / back   A/D: steer   Shift: leave   E: storage / engine",
               "Aux commandes !  W/S : avancer / reculer   A/D : tourner   Maj : descendre   E : coffre / moteur",
               "Am Steuer!  W/S: vor / zurück   A/D: lenken   Umschalt: aussteigen   E: Lager / Motor",
               "¡Al timón!  W/S: avanzar / retroceder   A/D: girar   Mayús: bajar   E: bodega / motor",
               "Al timone!  W/S: avanti / indietro   A/D: sterzare   Maiusc: scendere   E: stiva / motore",
               "У штурвала!  W/S: вперёд / назад   A/D: поворот   Shift: уйти   E: трюм / двигатель",
               "คุณอยู่ที่พวงมาลัย!  W/S: ไปหน้า / ถอยหลัง   A/D: เลี้ยว   Shift: ลง   E: ที่เก็บของ / เครื่องยนต์"),
    "b_left_helm": ("You left the helm. You can walk on the deck.", "Vous quittez la barre. Vous pouvez marcher sur le pont.",
                    "Du hast das Steuer verlassen. Du kannst über das Deck gehen.",
                    "Has dejado el timón. Puedes caminar por la cubierta.",
                    "Hai lasciato il timone. Puoi camminare sul ponte.",
                    "Вы отошли от штурвала. Можно ходить по палубе.", "คุณออกจากพวงมาลัยแล้ว เดินบนดาดฟ้าได้"),
    "b_need6_carry": ("You need 6 free inventory slots to carry the liner!",
                      "Il faut 6 cases libres dans l'inventaire pour porter le paquebot !",
                      "Du brauchst 6 freie Inventarplätze, um den Dampfer zu tragen!",
                      "¡Necesitas 6 espacios libres en el inventario para llevar el transatlántico!",
                      "Servono 6 posti liberi nell'inventario per portare il transatlantico!",
                      "Нужно 6 свободных ячеек, чтобы нести лайнер!", "ต้องมีช่องว่าง 6 ช่องเพื่อถือเรือเดินสมุทร!"),
    "b_need6_pick": ("You need 6 free inventory slots to pick up the liner!",
                     "Il faut 6 cases libres dans l'inventaire pour reprendre le paquebot !",
                     "Du brauchst 6 freie Inventarplätze, um den Dampfer aufzunehmen!",
                     "¡Necesitas 6 espacios libres en el inventario para recoger el transatlántico!",
                     "Servono 6 posti liberi nell'inventario per recuperare il transatlantico!",
                     "Нужно 6 свободных ячеек, чтобы забрать лайнер!", "ต้องมีช่องว่าง 6 ช่องเพื่อเก็บเรือเดินสมุทร!"),
    "b_need6_craft": ("You need 6 free inventory slots to craft the liner!",
                      "Il faut 6 cases libres dans l'inventaire pour fabriquer le paquebot !",
                      "Du brauchst 6 freie Inventarplätze, um den Dampfer herzustellen!",
                      "¡Necesitas 6 espacios libres en el inventario para fabricar el transatlántico!",
                      "Servono 6 posti liberi nell'inventario per costruire il transatlantico!",
                      "Нужно 6 свободных ячеек, чтобы создать лайнер!", "ต้องมีช่องว่าง 6 ช่องเพื่อสร้างเรือเดินสมุทร!"),
    "b_dismantle": ("Taking the boat apart… %d %%", "Démontage du bateau… %d %%", "Boot wird abgebaut… %d %%",
                    "Desmontando el barco… %d %%", "Smontaggio della barca… %d %%", "Разборка лодки… %d %%",
                    "กำลังรื้อเรือ… %d %%"),
    "b_speed": ("Speed: %.1f blocks/s", "Vitesse : %.1f blocs/s", "Geschwindigkeit: %.1f Blöcke/s",
                "Velocidad: %.1f bloques/s", "Velocità: %.1f blocchi/s", "Скорость: %.1f блоков/с",
                "ความเร็ว: %.1f บล็อก/วินาที"),
    "b_power": ("Power: %d %%", "Puissance : %d %%", "Leistung: %d %%", "Potencia: %d %%", "Potenza: %d %%",
                "Мощность: %d %%", "กำลัง: %d %%"),
    "b_hint": ("Right-click: steer | Shift + right-click: storage / engine | Hold left-click: dismantle",
               "Clic droit : piloter | Maj + clic droit : coffre / moteur | Clic gauche maintenu : démonter",
               "Rechtsklick: steuern | Umschalt + Rechtsklick: Lager / Motor | Linksklick halten: abbauen",
               "Clic derecho: pilotar | Mayús + clic derecho: bodega / motor | Mantener clic izquierdo: desmontar",
               "Clic destro: pilotare | Maiusc + clic destro: stiva / motore | Tieni premuto clic sinistro: smontare",
               "ПКМ: управлять | Shift + ПКМ: трюм / двигатель | Удерживать ЛКМ: разобрать",
               "คลิกขวา: ขับ | Shift + คลิกขวา: ที่เก็บของ / เครื่องยนต์ | กดค้างคลิกซ้าย: รื้อ"),
    "b_engine_room": ("Engine room", "Salle des machines", "Maschinenraum", "Sala de máquinas", "Sala macchine",
                      "Машинное отделение", "ห้องเครื่อง"),
    "b_steam_engine": ("Steam engine", "Moteur à vapeur", "Dampfmaschine", "Motor de vapor", "Motore a vapore",
                       "Паровой двигатель", "เครื่องยนต์ไอน้ำ"),
    "b_coal_wood": ("Coal / wood", "Charbon / bois", "Kohle / Holz", "Carbón / madera", "Carbone / legno",
                    "Уголь / дрова", "ถ่านหิน / ไม้"),
    "b_buckets": ("Water buckets", "Seaux d'eau", "Wassereimer", "Cubos de agua", "Secchi d'acqua", "Вёдра с водой", "ถังน้ำ"),
    "b_fire": ("Fire", "Feu", "Feuer", "Fuego", "Fuoco", "Огонь", "ไฟ"),
    "b_steam": ("Steam (water)", "Vapeur (eau)", "Dampf (Wasser)", "Vapor (agua)", "Vapore (acqua)", "Пар (вода)", "ไอน้ำ (น้ำ)"),
})



HARD = {STONE: 1.5, GRASS: 0.6, DIRT: 0.5, COBBLE: 2.0, PLANKS: 2.0, SAND: 0.5, GRAVEL: 0.6,
        LOG: 2.0, LEAVES: 0.2, COAL_ORE: 3.0, IRON_ORE: 3.0, GOLD_ORE: 3.0, DIAMOND_ORE: 3.0, TABLE: 2.5}
BTOOL = {STONE: "pickaxe", COBBLE: "pickaxe", COAL_ORE: "pickaxe", IRON_ORE: "pickaxe",
         GOLD_ORE: "pickaxe", DIAMOND_ORE: "pickaxe", PLANKS: "axe", LOG: "axe", TABLE: "axe",
         DIRT: "shovel", GRASS: "shovel", SAND: "shovel", GRAVEL: "shovel"}
NEED_TIER = {STONE: 1, COBBLE: 1, COAL_ORE: 1, IRON_ORE: 2, GOLD_ORE: 3, DIAMOND_ORE: 3}
BDROP = {STONE: COBBLE, GRASS: DIRT, COAL_ORE: COAL, IRON_ORE: RAW_IRON, GOLD_ORE: RAW_GOLD,
         DIAMOND_ORE: DIAMOND, LEAVES: 0, BEDROCK: 0, GLASS: 0}

# --- proprietes des blocs ajoutes ---
_CHESTS = list(range(CHEST, CHEST + 4))
_FURNACES = list(range(FURNACE, FURNACE + 4)) + list(range(FURNACE_LIT, FURNACE_LIT + 4))
_DOORS = list(range(DOOR0, DOOR0 + 16))
for _b in _CHESTS:
    HARD[_b], BTOOL[_b], BDROP[_b] = 2.5, "axe", CHEST
for _b in _FURNACES:
    HARD[_b], BTOOL[_b], NEED_TIER[_b], BDROP[_b] = 3.5, "pickaxe", 1, FURNACE
for _b, _h, _t in ((COAL_BLOCK, 5.0, 1), (IRON_BLOCK, 5.0, 2), (GOLD_BLOCK, 3.0, 3), (DIAMOND_BLOCK, 5.0, 3)):
    HARD[_b], BTOOL[_b], NEED_TIER[_b] = _h, "pickaxe", _t
HARD[GLASS] = 0.3
for _b in _DOORS:
    HARD[_b], BTOOL[_b], BDROP[_b] = 3.0, "axe", (DOOR_ITEM if _b < DOOR0 + 8 else 0)

OPAQUE = np.zeros(256, bool)
OPAQUE[1:NUM_BLOCKS] = True
OPAQUE[WATER] = False
OPAQUE[LEAVES] = False
SOLID = np.zeros(256, bool)
SOLID[1:NUM_BLOCKS] = True
SOLID[WATER] = False
HARD[NAVAL_TABLE], BTOOL[NAVAL_TABLE] = 2.5, "axe"
for _b in _CHESTS + _FURNACES + [COAL_BLOCK, IRON_BLOCK, GOLD_BLOCK, DIAMOND_BLOCK, GLASS, NAVAL_TABLE]:
    OPAQUE[_b] = True
    SOLID[_b] = True
OPAQUE[GLASS] = False
CUBELESS = np.zeros(256, bool)       # blocs qui ne sont pas des cubes (portes, fleurs) : maillage special
CROSS = np.zeros(256, bool)          # blocs en forme de croix (fleurs ajoutees par les mods)
for _b in _DOORS:
    CUBELESS[_b] = True
    SOLID[_b] = (_b - DOOR0) // 4 % 2 == 0          # une porte ouverte se traverse
SOLID_PY = SOLID.tolist()
SAMEHIDE = np.zeros(256, bool)
SAMEHIDE[WATER] = True
SAMEHIDE[LEAVES] = True
SAMEHIDE[GLASS] = True
LIGHTBLOCK = OPAQUE.copy()          # blocs qui arretent la lumiere du ciel
BLOCK_ITEMS = (set(range(1, NUM_BLOCKS)) - {WATER, BEDROCK}) | {CHEST, FURNACE, COAL_BLOCK, IRON_BLOCK,
                                                                 GOLD_BLOCK, DIAMOND_BLOCK, GLASS, NAVAL_TABLE}   # blocs posables
CREATIVE_ITEMS = (sorted(BLOCK_ITEMS) + [STICK, COAL, IRON_INGOT, GOLD_INGOT, DIAMOND, RAW_IRON, RAW_GOLD, DOOR_ITEM]
                  + sorted(TOOLS) + sorted(ARMOR) + list(range(130, 138)) + [COOKED_PORK, COOKED_BEEF, COOKED_CHICKEN]
                  + [BUCKET, WATER_BUCKET, ROWBOAT, DRAKKAR, MOTORBOAT, LINER, ENGINE, HULL_IRON, WINDSHIELD, L_BOW,
                     L_STERN, L_MID1, L_MID2, L_WS_TOP, L_WS_BOT, L_HULL, L_WS, L_ENGINE])


def break_time(block, held):
    """Temps (s) pour casser un bloc + True si le bloc donne un objet."""
    hard = HARD.get(block)
    if hard is None:
        return 1e9, False
    tool = TOOLS.get(held)
    need = NEED_TIER.get(block, 0)
    kind = BTOOL.get(block)
    tier = tool[1] if tool else 0
    ok_kind = tool is not None and tool[0] == kind
    can_harvest = (need == 0) or (ok_kind and tier >= need)
    if ok_kind:
        t = hard * 1.5 / tool[2]
        if not can_harvest:
            t = hard * 5.0
    else:
        t = hard * (5.0 if need else 1.5)
    return max(t, 0.05), can_harvest


# ----------------------------------------------------------------------------
# RECETTES DE FABRICATION (grille 2x2 dans l'inventaire, 3x3 sur l'établi)
# ----------------------------------------------------------------------------
RECIPES = []
SHAPELESS = {}          # (objets tries) -> (resultat, quantite) : recettes sans forme ajoutees par les mods


def _recipe(rows, key, result, count=1):
    pat = tuple(tuple(key.get(ch, 0) for ch in row) for row in rows)
    RECIPES.append((pat, result, count))


_recipe(["L"], {"L": LOG}, PLANKS, 4)
_recipe(["P", "P"], {"P": PLANKS}, STICK, 4)
_recipe(["PP", "PP"], {"P": PLANKS}, TABLE, 1)
for _t, _m in enumerate([PLANKS, COBBLE, IRON_INGOT, DIAMOND]):
    _key = {"M": _m, "S": STICK}
    _recipe(["MMM", " S ", " S "], _key, TOOL_ID[("pickaxe", _t)])
    _recipe(["MM", "MS", " S"], _key, TOOL_ID[("axe", _t)])
    _recipe(["M", "S", "S"], _key, TOOL_ID[("shovel", _t)])
    _recipe(["M", "M", "S"], _key, TOOL_ID[("sword", _t)])


_recipe(["PPP", "P P", "PPP"], {"P": PLANKS}, CHEST)
_recipe(["CCC", "C C", "CCC"], {"C": COBBLE}, FURNACE)
_recipe(["PP", "PP", "PP"], {"P": PLANKS}, DOOR_ITEM, 3)
for _it, _bl in ((COAL, COAL_BLOCK), (IRON_INGOT, IRON_BLOCK), (GOLD_INGOT, GOLD_BLOCK), (DIAMOND, DIAMOND_BLOCK)):
    _recipe(["III", "III", "III"], {"I": _it}, _bl)
    _recipe(["B"], {"B": _bl}, _it, 9)
for _k in KINDS:
    _key = {"M": GOLD_INGOT, "S": STICK}
    _pat = {"pickaxe": ["MMM", " S ", " S "], "axe": ["MM", "MS", " S"], "shovel": ["M", "S", "S"],
            "sword": ["M", "M", "S"]}[_k]
    _recipe(_pat, _key, GOLD_TOOL[_k])
for _mi, _mat in enumerate([LEATHER, IRON_INGOT, GOLD_INGOT, DIAMOND]):
    for _pi, _pat in enumerate([["MMM", "M M"], ["M M", "MMM", "MMM"], ["MMM", "M M", "M M"], ["M M", "M M"]]):
        _recipe(_pat, {"M": _mat}, ARMOR0 + 4 * _mi + _pi)


def _mirror(p):
    return tuple(tuple(reversed(r)) for r in p)


def _trim(grid, n):
    rows = [list(grid[r * n:(r + 1) * n]) for r in range(n)]
    rows = [r for r in rows if any(r)]
    if not rows:
        return ()
    cols = [c for c in range(n) if any(r[c] for r in rows)]
    c0, c1 = min(cols), max(cols)
    return tuple(tuple(r[c0:c1 + 1]) for r in rows)


def find_recipe(grid, n):
    """grid : liste de n*n identifiants (0 = vide). Retourne (objet, quantite) ou None."""
    pat = _trim(grid, n)
    if not pat:
        return None
    for rp, res, cnt in RECIPES:
        if pat == rp or pat == _mirror(rp):
            return res, cnt
    if SHAPELESS:                                   # recette "en vrac" : l'ordre des objets ne compte pas
        r = SHAPELESS.get(tuple(sorted(i for i in grid if i)))
        if r:
            return r
    return None


# --- recettes des bateaux ---
BOAT_RECIPES = []          # recettes qui ne marchent QUE sur la table de construction navale (5x5)


def _boat_recipe(rows, key, result, count=1):
    BOAT_RECIPES.append((tuple(tuple(key.get(ch, 0) for ch in row) for row in rows), result, count))


def find_boat_recipe(grid):
    pat = _trim(grid, 5)
    if not pat:
        return None
    for rp, res, cnt in BOAT_RECIPES:
        if pat == rp or pat == _mirror(rp):
            return res, cnt
    return None


_recipe(["I I", " I "], {"I": IRON_INGOT}, BUCKET)
_recipe(["LLL", "PTP", "LLL"], {"L": LOG, "P": PLANKS, "T": TABLE}, NAVAL_TABLE)
_recipe(["EHW"], {"E": ENGINE, "H": HULL_IRON, "W": WINDSHIELD}, MOTORBOAT)
_recipe(["BM", "NS"], {"B": L_BOW, "M": L_MID1, "N": L_MID2, "S": L_STERN}, L_HULL)
_recipe(["T", "B"], {"T": L_WS_TOP, "B": L_WS_BOT}, L_WS)
_recipe(["EFE"], {"E": ENGINE, "F": FURNACE}, L_ENGINE)
_recipe(["EHW"], {"E": L_ENGINE, "H": L_HULL, "W": L_WS}, LINER)
_boat_recipe(["P   P", "PPPPP"], {"P": PLANKS}, ROWBOAT)
_boat_recipe(["  S  ", " ESE ", "LPPPL", "PPPPP", " PPP "], {"S": STICK, "E": LEATHER, "L": LOG, "P": PLANKS}, DRAKKAR)
_boat_recipe(["PIIIP", "ICBCI", "PPPPP"], {"P": PLANKS, "I": IRON_INGOT, "C": COBBLE, "B": BUCKET}, ENGINE)
_boat_recipe(["I   I", "IPPPI", " III "], {"I": IRON_INGOT, "P": PLANKS}, HULL_IRON)
_boat_recipe(["ISISI", "I   I"], {"I": IRON_INGOT, "S": STICK}, WINDSHIELD)
_boat_recipe(["  I  ", " III ", "IIIPI"], {"I": IRON_INGOT, "P": PLANKS}, L_BOW)
_boat_recipe(["I   I", "IIPII", " III "], {"I": IRON_INGOT, "P": PLANKS}, L_STERN)
_boat_recipe(["IIIII", "IPPPI"], {"I": IRON_INGOT, "P": PLANKS}, L_MID1)
_boat_recipe(["IPPPI", "IIIII"], {"I": IRON_INGOT, "P": PLANKS}, L_MID2)
_boat_recipe(["IIIII", "S   S"], {"I": IRON_INGOT, "S": STICK}, L_WS_TOP)
_boat_recipe(["I   I", "IIIII"], {"I": IRON_INGOT}, L_WS_BOT)


# ----------------------------------------------------------------------------
# INVENTAIRE (liste de 36 cases : 0-8 = barre rapide)
# ----------------------------------------------------------------------------
def _inv_add_basic(inv, item, count):
    """Ajoute des objets. Retourne le reste qui n'a pas pu etre ajoute."""
    ms = max_stack(item)
    for i, s in enumerate(inv):
        if count <= 0:
            return 0
        if s is not None and s[0] == item and s[1] < ms:
            n = min(count, ms - s[1])
            s[1] += n
            count -= n
    for i, s in enumerate(inv):
        if count <= 0:
            return 0
        if s is None:
            n = min(count, ms)
            inv[i] = [item, n]
            count -= n
    return count


def inv_add(inv, item, count):
    """Comme _inv_add_basic, mais le paquebot occupe 6 cases (1 objet + 5 cases 'occupees')."""
    if item == SLOT_LOCK:
        return 0
    if item == LINER:
        while count > 0 and sum(1 for s in inv if s is None) >= 6:
            _inv_add_basic(inv, item, 1)
            fill_locks(inv)
            count -= 1
        return count
    return _inv_add_basic(inv, item, count)


# ============================================================================
# TEXTURES GENEREES PAR LE CODE (style pixel-art des premieres versions)
# ============================================================================
_rng = np.random.RandomState(20241018)


def _fill(c, a=255):
    im = np.zeros((16, 16, 4), np.uint8)
    im[:, :, 0], im[:, :, 1], im[:, :, 2], im[:, :, 3] = c[0], c[1], c[2], a
    return im


def _noise(im, amt):
    n = _rng.randint(-amt, amt + 1, (16, 16, 1))
    im[:, :, :3] = np.clip(im[:, :, :3].astype(np.int16) + n, 0, 255).astype(np.uint8)
    return im


def _shift(im, x0, x1, y0, y1, d):
    reg = im[y0:y1 + 1, x0:x1 + 1, :3].astype(np.int16) + d
    im[y0:y1 + 1, x0:x1 + 1, :3] = np.clip(reg, 0, 255).astype(np.uint8)


def _px(im, x, y, c, a=255):
    if 0 <= x < 16 and 0 <= y < 16:
        im[y, x, 0], im[y, x, 1], im[y, x, 2], im[y, x, 3] = c[0], c[1], c[2], a


def _rect(im, x0, y0, x1, y1, c, a=255):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            _px(im, x, y, c, a)


def _line(im, x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        _px(im, x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _speckle(im, n, d):
    for _ in range(n):
        x, y = _rng.randint(0, 16), _rng.randint(0, 16)
        if im[y, x, 3] > 0:
            _shift(im, x, x, y, y, d)


def _jit(c, d=10):
    return tuple(int(max(0, min(255, v + _rng.randint(-d, d + 1)))) for v in c)


def t_stone():
    im = _noise(_fill((127, 127, 127)), 8)
    _speckle(im, 16, -24)
    _speckle(im, 9, 16)
    return im


def t_dirt():
    im = _noise(_fill((134, 96, 67)), 11)
    _speckle(im, 18, -26)
    _speckle(im, 8, 18)
    return im


def t_grass_top():
    im = _noise(_fill((95, 159, 53)), 13)
    _speckle(im, 20, -18)
    _speckle(im, 10, 14)
    return im


def t_grass_side():
    im = t_dirt()
    for x in range(16):
        depth = 3 + int(_rng.randint(0, 3))
        for y in range(depth):
            _px(im, x, y, _jit((95, 159, 53), 12))
    return im


def t_cobble():
    pts = _rng.randint(0, 16, (9, 2))
    yy, xx = np.mgrid[0:16, 0:16]
    d = np.stack([np.sqrt((xx - px) ** 2 + (yy - py) ** 2) for px, py in pts])
    idx = d.argmin(0)
    s = np.sort(d, axis=0)
    border = (s[1] - s[0]) < 1.0
    shades = _rng.randint(108, 150, 9)
    v = shades[idx].astype(np.int16) + _rng.randint(-6, 7, (16, 16))
    v = np.where(border, 70, v)
    im = _fill((0, 0, 0))
    im[:, :, :3] = np.clip(v, 0, 255)[:, :, None].astype(np.uint8)
    return im


def t_planks():
    im = _fill((160, 130, 75))
    for b in range(4):
        base = np.array([160, 130, 75]) + int(_rng.randint(-8, 9))
        im[b * 4:b * 4 + 4, :, :3] = np.clip(base, 0, 255)
        im[b * 4 + 3, :, :3] = np.clip(base - 48, 0, 255)
        jx = int(_rng.randint(0, 16))
        im[b * 4:b * 4 + 3, jx, :3] = np.clip(base - 30, 0, 255)
    _noise(im, 4)
    for _ in range(10):
        x, y = int(_rng.randint(0, 12)), int(_rng.randint(0, 16))
        if y % 4 != 3:
            _shift(im, x, x + int(_rng.randint(2, 5)), y, y, -14)
    return im


def t_bedrock():
    im = _noise(_fill((88, 88, 88)), 28)
    _speckle(im, 26, -45)
    _speckle(im, 10, 25)
    return im


def t_water():
    im = _noise(_fill((46, 96, 214), 165), 7)
    _speckle(im, 14, 24)
    return im


def t_sand():
    im = _noise(_fill((220, 208, 160)), 7)
    _speckle(im, 14, -16)
    return im


def t_gravel():
    pal = [(132, 126, 122), (100, 98, 95), (152, 146, 140), (116, 111, 106), (84, 82, 80)]
    im = _fill((0, 0, 0))
    for y in range(16):
        for x in range(16):
            _px(im, x, y, _jit(pal[int(_rng.randint(0, 5))], 4))
    return im


def t_log_side():
    im = _fill((104, 82, 50))
    for x in range(16):
        d = int(_rng.randint(-16, 9))
        _shift(im, x, x, 0, 15, d)
    _noise(im, 5)
    return im


def t_log_top():
    im = _fill((0, 0, 0))
    for y in range(16):
        for x in range(16):
            d = max(abs(x - 7.5), abs(y - 7.5))
            if d >= 6.5:
                c = (104, 82, 50)
            else:
                c = (182, 146, 92) if int(d) % 2 == 0 else (150, 116, 68)
            _px(im, x, y, _jit(c, 5))
    return im


def t_leaves():
    im = _noise(_fill((50, 126, 32)), 22)
    _speckle(im, 25, -25)
    mask = _rng.rand(16, 16) < 0.27
    im[mask, 3] = 0
    return im


def _ore(col, n=5):
    im = t_stone()
    for _ in range(n):
        cx, cy = int(_rng.randint(2, 14)), int(_rng.randint(2, 14))
        cells = [(0, 0), (1, 0), (0, 1), (-1, 0), (1, 1), (0, -1)]
        for k in _rng.choice(6, 3 + int(_rng.randint(0, 2)), replace=False):
            _px(im, cx + cells[k][0], cy + cells[k][1], _jit(col, 8))
    return im


def t_table_top():
    im = t_planks()
    for k in (5, 10):
        _shift(im, 0, 15, k, k, -42)
        _shift(im, k, k, 0, 15, -42)
    _shift(im, 0, 15, 0, 0, -30)
    _shift(im, 0, 15, 15, 15, -30)
    _shift(im, 0, 0, 0, 15, -30)
    _shift(im, 15, 15, 0, 15, -30)
    return im


def t_table_side():
    im = t_planks()
    _rect(im, 0, 0, 15, 2, (92, 66, 34))
    _noise(im, 3)
    _line(im, 2, 12, 6, 6, (190, 190, 195))       # scie
    _line(im, 3, 12, 7, 6, (150, 150, 155))
    _rect(im, 9, 7, 12, 8, (120, 120, 125))       # marteau
    _line(im, 10, 9, 10, 13, (110, 78, 40))
    return im


def t_table_front():
    im = t_planks()
    _rect(im, 0, 0, 15, 2, (92, 66, 34))
    _noise(im, 3)
    for k in (6, 10):
        _shift(im, 2, 13, k, k, -45)
        _shift(im, k, k, 4, 14, -45)
    _line(im, 2, 14, 13, 14, (92, 66, 34))
    return im


def _crack_lines():
    lines = []
    for _ in range(16):
        x, y = int(_rng.randint(3, 13)), int(_rng.randint(3, 13))
        pts = []
        for _s in range(9):
            pts.append((x, y))
            x += int(_rng.randint(-1, 2))
            y += int(_rng.randint(-1, 2))
        lines.append(pts)
    return lines


_CRACKS = _crack_lines()


def t_crack(stage):
    im = _fill((0, 0, 0), 0)
    for pts in _CRACKS[:2 + stage * 3 // 2]:
        for (x, y) in pts:
            _px(im, x, y, (20, 20, 20), 190)
    return im


def t_sun():
    im = _fill((255, 236, 110))
    _rect(im, 2, 2, 13, 13, (255, 248, 170))
    _rect(im, 4, 4, 11, 11, (255, 255, 230))
    return im


def t_moon():
    im = _fill((205, 208, 224))
    _rect(im, 1, 1, 14, 14, (226, 228, 240))
    for (x, y, w) in [(3, 3, 3), (9, 5, 2), (5, 9, 3), (10, 10, 3)]:
        _rect(im, x, y, x + w - 1, y + w - 1, (184, 188, 206))
    return im


# --- objets ---------------------------------------------------------------
HANDLE = (118, 84, 42)
MAT_COL = [(160, 130, 75), (130, 130, 130), (226, 226, 226), (88, 226, 216), (250, 214, 60)]


def i_stick():
    im = _fill((0, 0, 0), 0)
    _line(im, 3, 13, 12, 4, HANDLE)
    _line(im, 4, 13, 13, 4, (150, 108, 56))
    return im


def i_tool(kind, m):
    c = MAT_COL[m]
    dk = tuple(int(v * 0.7) for v in c)
    im = _fill((0, 0, 0), 0)
    if kind == "pickaxe":
        _line(im, 2, 14, 11, 5, HANDLE)
        _line(im, 3, 14, 12, 5, (150, 108, 56))
        for (x, y) in [(3, 5), (4, 4), (5, 3), (6, 2), (7, 2), (8, 2), (9, 2), (10, 2),
                       (11, 3), (12, 4), (13, 5), (13, 6), (13, 7)]:
            _px(im, x, y, c)
        for (x, y) in [(5, 4), (6, 3), (7, 3), (8, 3), (9, 3), (10, 3), (11, 4), (12, 5), (12, 6)]:
            _px(im, x, y, dk)
    elif kind == "axe":
        _line(im, 2, 14, 10, 6, HANDLE)
        _line(im, 3, 14, 11, 6, (150, 108, 56))
        for (x0, x1, y) in [(9, 10, 1), (8, 12, 2), (7, 13, 3), (7, 13, 4), (8, 13, 5), (9, 12, 6)]:
            for x in range(x0, x1 + 1):
                _px(im, x, y, c)
        for (x, y) in [(13, 3), (13, 4), (13, 5), (12, 6), (7, 3), (7, 4)]:
            _px(im, x, y, dk)
    elif kind == "shovel":
        _line(im, 2, 14, 10, 6, HANDLE)
        _line(im, 3, 14, 11, 6, (150, 108, 56))
        for (x0, x1, y) in [(12, 13, 1), (11, 14, 2), (11, 14, 3), (11, 14, 4), (11, 14, 5), (11, 13, 6)]:
            for x in range(x0, x1 + 1):
                _px(im, x, y, c)
        for (x, y) in [(14, 2), (14, 3), (14, 4), (14, 5), (13, 6)]:
            _px(im, x, y, dk)
    else:  # sword
        lt = tuple(min(255, v + 28) for v in c)
        _line(im, 5, 9, 12, 2, lt)
        _line(im, 5, 10, 13, 2, c)
        _line(im, 6, 10, 14, 2, dk)
        _px(im, 13, 1, lt)
        _line(im, 3, 8, 7, 12, HANDLE)           # garde
        _line(im, 4, 9, 8, 13, (150, 108, 56))
        _line(im, 4, 11, 2, 13, HANDLE)          # poignee
        _px(im, 1, 14, (90, 60, 30))
    return im


def i_coal():
    im = _fill((0, 0, 0), 0)
    for (x0, x1, y) in [(5, 9, 4), (4, 11, 5), (3, 12, 6), (3, 12, 7), (3, 12, 8), (4, 11, 9), (5, 10, 10), (6, 9, 11)]:
        for x in range(x0, x1 + 1):
            _px(im, x, y, _jit((44, 44, 48), 6))
    for (x, y) in [(5, 5), (6, 6), (9, 7)]:
        _px(im, x, y, (92, 92, 100))
    for (x, y) in [(10, 9), (9, 10), (11, 8)]:
        _px(im, x, y, (18, 18, 20))
    return im


def _ingot(c, light, dark):
    im = _fill((0, 0, 0), 0)
    _rect(im, 3, 6, 12, 10, c)
    _rect(im, 5, 4, 14, 5, light)
    _rect(im, 13, 5, 14, 8, dark)
    _rect(im, 3, 10, 12, 11, dark)
    _rect(im, 4, 6, 6, 7, light)
    return im


def i_diamond():
    im = _fill((0, 0, 0), 0)
    widths = [2, 4, 6, 7, 7, 6, 5, 4, 2, 1]
    for k, w in enumerate(widths):
        y = 3 + k
        for x in range(8 - w // 2 - (w % 2 == 0) * 0, 8 + (w + 1) // 2):
            c = (88, 226, 216)
            if k < 3:
                c = (190, 255, 250)
            elif x > 9 or k > 6:
                c = (40, 160, 170)
            _px(im, x, y, c)
    return im


def i_raw(base, fat, dark):
    im = _fill((0, 0, 0), 0)
    for (x0, x1, y) in [(4, 10, 4), (3, 12, 5), (3, 12, 6), (3, 12, 7), (4, 12, 8), (5, 11, 9), (6, 10, 10)]:
        for x in range(x0, x1 + 1):
            _px(im, x, y, _jit(base, 8))
    _rect(im, 5, 6, 9, 6, fat)
    _rect(im, 10, 8, 11, 9, dark)
    _rect(im, 4, 9, 8, 9, dark)
    return im


def i_chicken():
    im = i_raw((236, 190, 168), (250, 224, 206), (200, 140, 120))
    _line(im, 10, 10, 13, 13, (240, 236, 224))
    _px(im, 13, 14, (240, 236, 224))
    _px(im, 14, 13, (240, 236, 224))
    return im


def i_feather():
    im = _fill((0, 0, 0), 0)
    _line(im, 3, 13, 13, 3, (150, 150, 150))
    for k in range(5):
        _px(im, 5 + k * 2, 11 - k * 2 - 1, (236, 236, 236))
        _px(im, 6 + k * 2, 11 - k * 2, (255, 255, 255))
        _px(im, 4 + k * 2, 12 - k * 2, (220, 220, 220))
    return im


def i_leather():
    im = _fill((0, 0, 0), 0)
    _rect(im, 3, 3, 12, 12, (158, 94, 52))
    _noise(im, 8)
    for k in range(3, 13, 2):
        _px(im, 3, k, (110, 62, 32))
        _px(im, 12, k, (110, 62, 32))
    return im


def i_bone():
    im = _fill((0, 0, 0), 0)
    _line(im, 4, 12, 12, 4, (232, 232, 220))
    _line(im, 5, 12, 12, 5, (200, 200, 188))
    for (x, y) in [(2, 12), (3, 13), (4, 14), (3, 11), (13, 3), (12, 2), (11, 1), (14, 4)]:
        _px(im, x, y, (240, 240, 228))
    return im


def i_gunpowder():
    im = _fill((0, 0, 0), 0)
    for _ in range(60):
        x, y = int(_rng.randint(3, 13)), int(_rng.randint(3, 13))
        if (x - 8) ** 2 + (y - 8) ** 2 < 22:
            _px(im, x, y, _jit((96, 96, 98), 20))
    return im


def i_rotten():
    im = i_raw((112, 132, 62), (146, 160, 84), (74, 92, 40))
    _speckle(im, 8, -20)
    return im


# --- mobs ------------------------------------------------------------------
def _mt(base, n=9, spots=None, sd=-22, cnt=14):
    im = _noise(_fill(base), n)
    if spots:
        _speckle(im, cnt, sd)
    return im


def _eyes(im, ys, xs, c, w=1, h=1):
    for x in xs:
        _rect(im, x, ys, x + w - 1, ys + h - 1, c)


def m_cow_body():
    im = _noise(_fill((236, 236, 236)), 6)
    for (cx, cy, r) in [(3, 4, 3), (11, 9, 3), (6, 12, 2), (12, 2, 2)]:
        for y in range(16):
            for x in range(16):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    _px(im, x, y, _jit((92, 62, 40), 6))
    return im


def m_cow_head():
    return _mt((100, 68, 44), 8)


def m_cow_face():
    im = _mt((100, 68, 44), 8)
    _eyes(im, 5, (2, 12), (20, 20, 20), 2, 2)
    _rect(im, 4, 10, 11, 14, (205, 176, 150))
    _eyes(im, 12, (5, 9), (80, 56, 40), 1, 1)
    return im


def m_cow_leg():
    im = _mt((100, 68, 44), 8)
    _rect(im, 0, 12, 15, 15, (210, 210, 205))
    return im


def m_pig():
    return _mt((240, 162, 162), 7, True, -16, 10)


def m_pig_face():
    im = _mt((240, 162, 162), 7)
    _eyes(im, 4, (2, 12), (30, 30, 30), 2, 2)
    _rect(im, 4, 9, 11, 13, (222, 130, 130))
    _eyes(im, 10, (6, 9), (110, 60, 60), 1, 2)
    return im


def m_pig_leg():
    return _mt((228, 150, 150), 7)


def m_chicken():
    return _mt((240, 240, 240), 6, True, -18, 10)


def m_chicken_face():
    im = _mt((240, 240, 240), 5)
    _eyes(im, 5, (3, 11), (20, 20, 20), 2, 2)
    _rect(im, 5, 8, 10, 10, (244, 190, 40))
    _rect(im, 6, 11, 9, 13, (210, 40, 40))
    return im


def m_chicken_leg():
    return _mt((232, 190, 50), 6)


def m_horse():
    return _mt((140, 92, 52), 8, True, -22, 14)


def m_horse_face():
    im = _mt((140, 92, 52), 8)
    _eyes(im, 4, (2, 12), (20, 20, 20), 2, 2)
    _rect(im, 3, 10, 12, 15, (196, 160, 130))
    _eyes(im, 11, (4, 10), (60, 40, 30), 1, 2)
    return im


def m_horse_mane():
    return _mt((52, 32, 22), 8)


def m_horse_leg():
    im = _mt((130, 84, 48), 8)
    _rect(im, 0, 12, 15, 15, (52, 36, 28))
    return im


def m_creeper():
    im = _fill((72, 164, 70))
    for _ in range(30):
        x, y = int(_rng.randint(0, 14)), int(_rng.randint(0, 14))
        _rect(im, x, y, x + int(_rng.randint(1, 4)), y + int(_rng.randint(1, 4)),
              _jit((46, 120, 46) if _rng.rand() < .6 else (104, 196, 98), 6))
    return im


def m_creeper_face():
    im = m_creeper()
    _rect(im, 2, 4, 5, 7, (12, 12, 12))
    _rect(im, 10, 4, 13, 7, (12, 12, 12))
    _rect(im, 6, 8, 9, 10, (12, 12, 12))
    _rect(im, 5, 10, 10, 14, (12, 12, 12))
    _rect(im, 6, 11, 9, 14, (72, 164, 70))
    _rect(im, 7, 11, 8, 12, (12, 12, 12))
    return im


def m_zombie_skin():
    return _mt((84, 146, 72), 9, True, -24, 18)


def m_zombie_face():
    im = _mt((84, 146, 72), 9)
    _rect(im, 2, 5, 5, 7, (240, 240, 240))
    _rect(im, 10, 5, 13, 7, (240, 240, 240))
    _rect(im, 4, 5, 5, 7, (40, 40, 120))
    _rect(im, 10, 5, 11, 7, (40, 40, 120))
    _rect(im, 6, 8, 9, 9, (60, 100, 52))
    _rect(im, 4, 11, 11, 12, (50, 80, 44))
    return im


def m_zombie_shirt():
    return _mt((0, 170, 170), 9, True, -30, 14)


def m_zombie_pants():
    return _mt((52, 52, 156), 8, True, -22, 12)


def m_skel_skin():
    return _mt((206, 206, 196), 8, True, -34, 12)


def m_skel_face():
    im = _mt((206, 206, 196), 7)
    _rect(im, 2, 5, 5, 7, (30, 30, 30))
    _rect(im, 10, 5, 13, 7, (30, 30, 30))
    _rect(im, 7, 9, 8, 10, (120, 120, 112))
    _rect(im, 4, 12, 11, 13, (50, 50, 46))
    for x in (5, 7, 9):
        _px(im, x, 12, (220, 220, 210))
    return im


def m_skel_ribs():
    im = _mt((196, 196, 186), 7)
    for y in (2, 5, 8, 11):
        _rect(im, 1, y, 14, y + 1, (60, 60, 56))
    _rect(im, 7, 0, 8, 15, (150, 150, 142))
    return im


def m_skel_limb():
    return _mt((200, 200, 190), 6, True, -34, 8)


def m_arrow():
    im = _fill((0, 0, 0), 0)
    _rect(im, 7, 0, 8, 15, (150, 150, 150))
    return im


TILES = {}


def _reg(name, im):
    TILES[name] = im


for _n, _f in [("stone", t_stone), ("dirt", t_dirt), ("grass_top", t_grass_top), ("grass_side", t_grass_side),
               ("cobble", t_cobble), ("planks", t_planks), ("bedrock", t_bedrock), ("water", t_water),
               ("sand", t_sand), ("gravel", t_gravel), ("log_side", t_log_side), ("log_top", t_log_top),
               ("leaves", t_leaves), ("table_top", t_table_top), ("table_side", t_table_side),
               ("table_front", t_table_front), ("sun", t_sun), ("moon", t_moon)]:
    _reg(_n, _f())
_reg("coal_ore", _ore((30, 30, 32)))
_reg("iron_ore", _ore((218, 176, 150)))
_reg("gold_ore", _ore((252, 238, 70)))
_reg("diamond_ore", _ore((90, 222, 214)))
for _s in range(10):
    _reg("crack%d" % _s, t_crack(_s))
_reg("i_stick", i_stick())
_reg("i_coal", i_coal())
_reg("i_iron", _ingot((222, 222, 228), (250, 250, 255), (160, 160, 168)))
_reg("i_gold", _ingot((250, 216, 60), (255, 244, 150), (196, 150, 30)))
_reg("i_diamond", i_diamond())
for (_k, _t), _id in TOOL_ID.items():
    _reg("tool_%s_%d" % (_k, _t), i_tool(_k, _t))
_reg("i_pork", i_raw((240, 160, 150), (252, 206, 196), (200, 110, 104)))
_reg("i_beef", i_raw((176, 52, 52), (222, 120, 110), (120, 30, 30)))
_reg("i_chicken", i_chicken())
_reg("i_feather", i_feather())
_reg("i_leather", i_leather())
_reg("i_bone", i_bone())
_reg("i_gunpowder", i_gunpowder())
_reg("i_rotten", i_rotten())
for _n, _f in [("cow_body", m_cow_body), ("cow_head", m_cow_head), ("cow_face", m_cow_face), ("cow_leg", m_cow_leg),
               ("pig", m_pig), ("pig_face", m_pig_face), ("pig_leg", m_pig_leg),
               ("chicken", m_chicken), ("chicken_face", m_chicken_face), ("chicken_leg", m_chicken_leg),
               ("horse", m_horse), ("horse_face", m_horse_face), ("horse_mane", m_horse_mane),
               ("horse_leg", m_horse_leg), ("creeper", m_creeper), ("creeper_face", m_creeper_face),
               ("zombie_skin", m_zombie_skin), ("zombie_face", m_zombie_face), ("zombie_shirt", m_zombie_shirt),
               ("zombie_pants", m_zombie_pants), ("skel_skin", m_skel_skin), ("skel_face", m_skel_face),
               ("skel_ribs", m_skel_ribs), ("skel_limb", m_skel_limb), ("arrow", m_arrow)]:
    _reg(_n, _f())

_reg("skin", _noise(_fill((198, 152, 114)), 5))


def t_missing():
    im = _fill((12, 12, 12))
    _rect(im, 0, 0, 7, 7, (248, 0, 248))
    _rect(im, 8, 8, 15, 15, (248, 0, 248))
    return im


_reg("missing", t_missing())


# --- textures des blocs et objets ajoutes (coffre, four, porte, minerais bruts, armures...) ---
def _outline(im, col):
    a = im[:, :, 3] > 0
    pad = np.pad(a, 1, constant_values=False)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    for y, x in zip(*np.nonzero(edge)):
        _px(im, int(x), int(y), col)
    return im


def t_mineral(col, chips=False):
    im = _noise(_fill(col), 6)
    dark = tuple(int(v * 0.6) for v in col)
    light = tuple(min(255, int(v * 1.25) + 12) for v in col)
    if chips:
        _speckle(im, 24, 16)
    for k in range(16):
        _px(im, k, 0, light)
        _px(im, 0, k, light)
        _px(im, k, 15, dark)
        _px(im, 15, k, dark)
    _rect(im, 3, 3, 6, 4, light)
    _px(im, 3, 5, light)
    return im


def t_glass():
    im = _fill((0, 0, 0), 0)
    for k in range(16):
        for (x, y) in ((k, 0), (k, 15), (0, k), (15, k)):
            _px(im, x, y, (196, 224, 236))
    for (x, y) in ((3, 3), (4, 3), (3, 4), (11, 11), (10, 11), (11, 10)):
        _px(im, x, y, (255, 255, 255), 230)
    return im


def t_chest(part):
    wood = (160, 108, 46)
    im = _noise(_fill(wood), 5)
    dark = (92, 58, 24)
    for k in range(16):
        _px(im, k, 0, dark)
        _px(im, k, 15, dark)
        _px(im, 0, k, dark)
        _px(im, 15, k, dark)
    if part == "top":
        _rect(im, 2, 2, 13, 13, (176, 122, 54))
        _noise(im, 3)
        return im
    _shift(im, 1, 14, 5, 6, -42)
    _shift(im, 1, 14, 7, 7, 18)
    if part == "front":
        _rect(im, 7, 5, 8, 9, (214, 214, 220))
        _rect(im, 7, 8, 8, 9, (70, 70, 78))
    return im


def t_furnace(part):
    im = t_stone()
    _shift(im, 0, 15, 0, 15, -8)
    for k in range(16):
        _shift(im, k, k, 0, 0, -30)
        _shift(im, k, k, 15, 15, -30)
        _shift(im, 0, 0, k, k, -30)
        _shift(im, 15, 15, k, k, -30)
    if part == "top":
        _rect(im, 3, 3, 12, 12, (74, 74, 78))
    elif part in ("front", "front_on"):
        _rect(im, 3, 2, 12, 4, (58, 58, 62))
        _rect(im, 3, 8, 12, 13, (24, 24, 26))
        if part == "front_on":
            for (x, y, c) in ((4, 12, (255, 120, 20)), (5, 11, (255, 170, 30)), (6, 12, (255, 220, 70)),
                              (7, 10, (255, 150, 30)), (8, 12, (255, 200, 60)), (9, 11, (255, 120, 20)),
                              (10, 12, (255, 220, 70)), (11, 11, (255, 170, 30)), (6, 13, (255, 100, 20)),
                              (9, 13, (255, 100, 20)), (8, 9, (255, 190, 50))):
                _px(im, x, y, c)
    return im


def t_door(upper):
    im = _noise(_fill((158, 110, 52)), 5)
    dark = (96, 62, 26)
    for k in range(16):
        _px(im, k, 0, dark)
        _px(im, k, 15, dark)
        _px(im, 0, k, dark)
        _px(im, 15, k, dark)
    if upper:
        for (x0, y0, x1, y1) in ((3, 3, 6, 6), (9, 3, 12, 6), (3, 9, 6, 12), (9, 9, 12, 12)):
            _rect(im, x0, y0, x1, y1, (150, 192, 216))
            _rect(im, x0, y0, x1, y0, (96, 62, 26))
            _rect(im, x0, y0, x0, y1, (96, 62, 26))
    else:
        for (x0, y0, x1, y1) in ((3, 2, 12, 6), (3, 9, 12, 13)):
            _rect(im, x0, y0, x1, y1, (178, 126, 62))
            _shift(im, x0, x1, y1, y1, -40)
            _shift(im, x1, x1, y0, y1, -40)
        _rect(im, 12, 7, 12, 8, (214, 214, 220))
    return im


def i_door():
    im = _fill((0, 0, 0), 0)
    _rect(im, 4, 1, 11, 14, (158, 110, 52))
    for (x0, y0, x1, y1) in ((5, 2, 10, 6), (5, 8, 10, 13)):
        _rect(im, x0, y0, x1, y1, (180, 128, 62))
    _rect(im, 10, 8, 10, 9, (220, 220, 226))
    _rect(im, 5, 3, 10, 3, (150, 192, 216))
    return _outline(im, (86, 56, 24))


def i_armor(piece, col):
    dk = tuple(int(v * 0.62) for v in col)
    lt = tuple(min(255, int(v * 1.15) + 22) for v in col)
    im = _fill((0, 0, 0), 0)
    if piece == 0:
        _rect(im, 4, 2, 11, 3, col)
        _rect(im, 3, 4, 12, 8, col)
        _rect(im, 3, 9, 5, 12, col)
        _rect(im, 10, 9, 12, 12, col)
        _rect(im, 4, 3, 6, 4, lt)
        _rect(im, 3, 8, 12, 8, dk)
    elif piece == 1:
        _rect(im, 4, 2, 11, 14, col)
        _rect(im, 1, 2, 4, 7, col)
        _rect(im, 11, 2, 14, 7, col)
        _rect(im, 6, 2, 9, 4, (0, 0, 0))
        im[2:5, 6:10, 3] = 0
        _rect(im, 7, 5, 8, 14, dk)
        _rect(im, 4, 13, 11, 14, dk)
        _rect(im, 5, 5, 6, 7, lt)
    elif piece == 2:
        _rect(im, 4, 2, 11, 5, col)
        _rect(im, 4, 6, 7, 14, col)
        _rect(im, 8, 6, 11, 14, col)
        _rect(im, 7, 6, 8, 14, dk)
        _rect(im, 4, 4, 11, 5, dk)
        _rect(im, 5, 6, 5, 9, lt)
    else:
        _rect(im, 3, 4, 6, 10, col)
        _rect(im, 2, 10, 7, 12, col)
        _rect(im, 9, 4, 12, 10, col)
        _rect(im, 8, 10, 13, 12, col)
        _rect(im, 2, 12, 7, 12, dk)
        _rect(im, 8, 12, 13, 12, dk)
        _rect(im, 3, 4, 3, 7, lt)
        _rect(im, 9, 4, 9, 7, lt)
    return _outline(im, dk)


ARMOR_COL = [(152, 94, 54), (224, 224, 230), (252, 214, 60), (96, 228, 218)]
_reg("coal_block", t_mineral((30, 30, 34), True))
_reg("iron_block", t_mineral((218, 218, 224)))
_reg("gold_block", t_mineral((250, 214, 64)))
_reg("diamond_block", t_mineral((94, 224, 214)))
_reg("glass", t_glass())
for _p in ("top", "side", "front"):
    _reg("chest_" + _p, t_chest(_p))
for _p in ("top", "side", "front", "front_on"):
    _reg("furnace_" + _p, t_furnace(_p))
_reg("door_lower", t_door(False))
_reg("door_upper", t_door(True))
_reg("i_door", i_door())
_reg("i_raw_iron", i_raw((196, 156, 128), (228, 196, 168), (140, 100, 78)))
_reg("i_raw_gold", i_raw((238, 204, 74), (255, 238, 140), (192, 142, 32)))
_reg("i_cooked_pork", i_raw((176, 104, 70), (210, 146, 104), (112, 62, 40)))
_reg("i_cooked_beef", i_raw((124, 68, 44), (156, 94, 62), (82, 42, 28)))
_reg("i_cooked_chicken", i_chicken())
_TILES_CK = TILES["i_cooked_chicken"]
_TILES_CK[:] = i_raw((206, 150, 82), (238, 194, 124), (152, 102, 52))
_line(_TILES_CK, 10, 10, 13, 13, (240, 236, 224))
_px(_TILES_CK, 13, 14, (240, 236, 224))
_px(_TILES_CK, 14, 13, (240, 236, 224))
for _k in KINDS:
    _reg("tool_%s_4" % _k, i_tool(_k, 4))
for _mi in range(4):
    for _pi in range(4):
        _reg("armor_%d_%d" % (_mi, _pi), i_armor(_pi, ARMOR_COL[_mi]))
TILE_NAMES = list(TILES.keys())
TILE_INDEX = {}
TILE_UV = np.zeros((256, 4), np.float32)
ATLAS = np.zeros((256, 256, 4), np.uint8)


def _img_bytes(surface, fmt, flip=False):
    f = getattr(pygame.image, "tobytes", None) or pygame.image.tostring
    return f(surface, fmt, flip)


def export_textures():
    """Ecrit toutes les textures du jeu en PNG 16x16 pour que vous puissiez les modifier."""
    os.makedirs(TEXTURE_DIR, exist_ok=True)
    for n in TILE_NAMES:
        surf = pygame.image.frombuffer(TILES[n].tobytes(), (16, 16), "RGBA")
        pygame.image.save(surf, os.path.join(TEXTURE_DIR, n + ".png"))
    print("Textures exportees dans :", TEXTURE_DIR)


def _try_override(name, arr):
    p = os.path.join(TEXTURE_DIR, name + ".png")
    if not os.path.isfile(p):
        return arr
    try:
        s = pygame.image.load(p).convert_alpha()
        s = pygame.transform.scale(s, (16, 16))
        raw = _img_bytes(s, "RGBA")
        return np.frombuffer(raw, np.uint8).reshape(16, 16, 4).copy()
    except Exception:
        return arr


def build_atlas():
    """Assemble toutes les textures dans une grande image 256x256 (peut etre rappelee apres un mod)."""
    e = 0.001
    TILE_NAMES[:] = list(TILES.keys())
    TILE_INDEX.clear()
    TILE_UV[:] = 0
    ATLAS[:] = 0
    for i, n in enumerate(TILE_NAMES):
        if ":" not in n:
            TILES[n] = _try_override(n, TILES[n])
        col, row = i % 16, i // 16
        ATLAS[row * 16:(row + 1) * 16, col * 16:(col + 1) * 16] = TILES[n]
        TILE_INDEX[n] = i
        TILE_UV[i] = (col / 16.0 + e, row / 16.0 + e, (col + 1) / 16.0 - e, (row + 1) / 16.0 - e)
    _build_face_table()
    return ATLAS


BLOCK_TILES = {
    STONE: ("stone", "stone", "stone"), GRASS: ("grass_top", "dirt", "grass_side"),
    DIRT: ("dirt", "dirt", "dirt"), COBBLE: ("cobble",) * 3, PLANKS: ("planks",) * 3,
    BEDROCK: ("bedrock",) * 3, WATER: ("water",) * 3, SAND: ("sand",) * 3, GRAVEL: ("gravel",) * 3,
    LOG: ("log_top", "log_top", "log_side"), LEAVES: ("leaves",) * 3, COAL_ORE: ("coal_ore",) * 3,
    IRON_ORE: ("iron_ore",) * 3, GOLD_ORE: ("gold_ore",) * 3, DIAMOND_ORE: ("diamond_ore",) * 3,
    TABLE: ("table_top", "planks", "table_side"),
}
for _d in range(4):
    _FACE_OF = [5, 0, 4, 1][_d]            # face (dans l'ordre +x -x +y -y +z -z) tournee vers l'avant
    BLOCK_TILES[CHEST + _d] = ("chest_top", "planks", "chest_side")
    BLOCK_TILES[FURNACE + _d] = ("furnace_top", "furnace_top", "furnace_side")
    BLOCK_TILES[FURNACE_LIT + _d] = ("furnace_top", "furnace_top", "furnace_side")
FRONT_TILES = {}                          # bloc -> (face, texture de la face avant)
for _d in range(4):
    _fi = [5, 0, 4, 1][_d]
    FRONT_TILES[CHEST + _d] = (_fi, "chest_front")
    FRONT_TILES[FURNACE + _d] = (_fi, "furnace_front")
    FRONT_TILES[FURNACE_LIT + _d] = (_fi, "furnace_front_on")
for _b in (COAL_BLOCK, IRON_BLOCK, GOLD_BLOCK, DIAMOND_BLOCK):
    BLOCK_TILES[_b] = ({COAL_BLOCK: "coal_block", IRON_BLOCK: "iron_block", GOLD_BLOCK: "gold_block",
                        DIAMOND_BLOCK: "diamond_block"}[_b],) * 3
BLOCK_TILES[GLASS] = ("glass",) * 3
BLOCK_TILES[NAVAL_TABLE] = ("bt_table_top", "planks", "bt_table_side")
ITEM_TILES = {BUCKET: "bi_bucket", WATER_BUCKET: "bi_water_bucket", ROWBOAT: "bi_rowboat", DRAKKAR: "bi_drakkar",
              MOTORBOAT: "bi_motorboat", LINER: "bi_liner", ENGINE: "bi_engine", HULL_IRON: "bi_hull_iron",
              WINDSHIELD: "bi_windshield", L_BOW: "bi_l_bow", L_STERN: "bi_l_stern", L_MID1: "bi_l_mid1",
              L_MID2: "bi_l_mid2", L_WS_TOP: "bi_l_ws_top", L_WS_BOT: "bi_l_ws_bot", L_HULL: "bi_l_hull",
              L_WS: "bi_l_ws", L_ENGINE: "bi_l_engine", SLOT_LOCK: "bi_slot_lock",
              RAW_IRON: "i_raw_iron", RAW_GOLD: "i_raw_gold", COOKED_PORK: "i_cooked_pork",
              COOKED_BEEF: "i_cooked_beef", COOKED_CHICKEN: "i_cooked_chicken", DOOR_ITEM: "i_door",
              STICK: "i_stick", COAL: "i_coal", IRON_INGOT: "i_iron", GOLD_INGOT: "i_gold",
              DIAMOND: "i_diamond", RAW_PORK: "i_pork", RAW_BEEF: "i_beef", RAW_CHICKEN: "i_chicken",
              FEATHER: "i_feather", LEATHER: "i_leather", BONE: "i_bone", GUNPOWDER: "i_gunpowder",
              ROTTEN: "i_rotten"}
for (_k, _t), _id in TOOL_ID.items():
    ITEM_TILES[_id] = "tool_%s_%d" % (_k, _t)
for _k, _id in GOLD_TOOL.items():
    ITEM_TILES[_id] = "tool_%s_4" % _k
for _id, (_pi, _pts) in ARMOR.items():
    ITEM_TILES[_id] = "armor_%d_%d" % ((_id - ARMOR0) // 4, _pi)

FACE_TILE = np.zeros((256, 6), np.int32)       # [+x, -x, +y, -y, +z, -z]


def _build_face_table():
    FACE_TILE[:] = 0
    for b, (top, bot, side) in BLOCK_TILES.items():
        t, bt, s = TILE_INDEX[top], TILE_INDEX[bot], TILE_INDEX[side]
        FACE_TILE[b] = [s, s, t, bt, s, s]
    f = TILE_INDEX["table_front"]
    FACE_TILE[TABLE][1] = f
    FACE_TILE[TABLE][4] = f
    for b, (fi, tn) in FRONT_TILES.items():
        FACE_TILE[b][fi] = TILE_INDEX[tn]
    if "bt_table_front" in TILE_INDEX:                  # la table navale a une face avant, comme l'etabli
        FACE_TILE[NAVAL_TABLE][1] = TILE_INDEX["bt_table_front"]
        FACE_TILE[NAVAL_TABLE][4] = TILE_INDEX["bt_table_front"]


def iso_icon(top, left, right):
    """Petit cube isometrique 32x32 pour l'inventaire (numpy)."""
    S = 32
    ys, xs = np.mgrid[0:S, 0:S]
    xc, yc = xs + 0.5, ys + 0.5
    out = np.zeros((S, S, 4), np.uint8)
    ul = (xc - 2) / 14.0
    vl = (yc - 9 - 7 * ul) / 14.0
    ml = (ul >= 0) & (ul < 1) & (vl >= 0) & (vl < 1)
    ur = (xc - 16) / 14.0
    vr = (yc - 16 + 7 * ur) / 14.0
    mr = (ur >= 0) & (ur < 1) & (vr >= 0) & (vr < 1)
    s = ((yc - 2) / 7.0 + (xc - 16) / 14.0) / 2
    t = ((yc - 2) / 7.0 - (xc - 16) / 14.0) / 2
    mt = (s >= 0) & (s < 1) & (t >= 0) & (t < 1)

    def put(mask, tex, u, v, shade):
        px = np.clip((u * 16).astype(int), 0, 15)
        py = np.clip((v * 16).astype(int), 0, 15)
        samp = tex[py, px].astype(np.float32)
        samp[:, :, :3] *= shade
        out[mask] = np.clip(samp, 0, 255).astype(np.uint8)[mask]
    put(ml, left, ul, vl, 0.82)
    put(mr, right, ur, vr, 0.62)
    put(mt, top, s, t, 1.0)
    return out


def icon_array(item):
    """Retourne un tableau RGBA (16x16 pour un objet, 32x32 pour un bloc)."""
    if item in ITEM_TILES:
        return TILES[ITEM_TILES[item]]
    if item in BLOCK_TILES:
        top, bot, side = BLOCK_TILES[item]
        left = TILES[side]
        right = TILES["table_front"] if item == TABLE else TILES[side]
        if item == NAVAL_TABLE:
            right = TILES["bt_table_front"]
        if item in FRONT_TILES:
            right = TILES[FRONT_TILES[item][1]]
        return iso_icon(TILES[top], left, right)
    return TILES["missing"]


# ============================================================================
# MODULE BATEAUX : textures (16x16, generees par le code) - table navale, bateaux, pieces, moteur
# ============================================================================
PAL = {
    "K": (28, 28, 34), "k": (60, 60, 68), "D": (74, 74, 84),
    "W": (236, 236, 240), "w": (252, 252, 252), "G": (160, 160, 168), "g": (104, 104, 112),
    "B": (150, 108, 58), "b": (100, 70, 36), "p": (190, 152, 94),
    "R": (192, 52, 46), "r": (126, 32, 30),
    "U": (52, 112, 204), "u": (140, 196, 238), "N": (30, 48, 104),
    "Y": (240, 206, 72), "O": (232, 140, 48), "C": (134, 134, 134), "c": (98, 98, 98),
    "T": (62, 64, 76),
}


def _ascii(rows, pal=PAL):
    im = _fill((0, 0, 0), 0)
    for y, row in enumerate(rows[:16]):
        for x, ch in enumerate(row[:16]):
            if ch != "." and ch in pal:
                _px(im, x, y, pal[ch])
    return im


def _dark(im, f):
    out = im.copy()
    out[:, :, :3] = np.clip(out[:, :, :3].astype(np.float32) * f, 0, 255).astype(np.uint8)
    return out


def t_plates(base, seam=-34, rivet=30, step=8):
    im = _noise(_fill(base), 5)
    for k in range(0, 16, step):
        _shift(im, 0, 15, k, k, seam)
        _shift(im, k, k, 0, 15, seam)
    for ky in range(0, 16, step):
        for kx in range(0, 16, step):
            _shift(im, kx + 2, kx + 2, ky + 2, ky + 2, rivet)
            _shift(im, kx + 5, kx + 5, ky + 5, ky + 5, rivet)
    return im


def t_white():
    im = _noise(_fill((236, 236, 230)), 3)
    for k in (3, 7, 11, 15):
        _shift(im, 0, 15, k, k, -26)
    return im


def t_sail():
    im = _fill((236, 228, 206))
    for x in range(16):
        if (x // 4) % 2 == 0:
            im[:, x, :3] = (192, 46, 40)
    _noise(im, 6)
    for k in (4, 9, 14):
        _shift(im, 0, 15, k, k, -18)
    return im


def t_funnel():
    im = _noise(_fill((226, 172, 66)), 4)
    for x in range(16):
        _shift(im, x, x, 0, 15, 20 - int(x * 2.6))
    return im


def t_funnel_top():
    return _noise(_fill((30, 30, 34)), 3)


def t_window():
    im = t_white()
    for (x0, x1) in ((1, 6), (9, 14)):
        _rect(im, x0, 4, x1, 11, (36, 56, 108))
        _rect(im, x0, 4, x1, 4, (150, 160, 175))
        _px(im, x0 + 1, 5, (130, 160, 210))
        _px(im, x0 + 2, 6, (110, 140, 195))
    return im


def t_boat_glass():
    im = _fill((0, 0, 0), 0)
    fr = (150, 152, 160)
    _rect(im, 0, 0, 15, 0, fr)
    _rect(im, 0, 15, 15, 15, fr)
    _rect(im, 0, 0, 0, 15, fr)
    _rect(im, 15, 0, 15, 15, fr)
    _rect(im, 7, 0, 8, 15, fr)
    for (x, y) in ((2, 3), (3, 4), (4, 5), (10, 7), (11, 8), (12, 9)):
        _px(im, x, y, (206, 232, 250))
    return im


def t_engine():
    im = _noise(_fill((76, 80, 90)), 4)
    for y0 in (2, 12):
        _rect(im, 0, y0, 15, y0 + 1, (176, 108, 58))
        _rect(im, 0, y0, 15, y0, (214, 150, 92))
    for y in range(5, 12):
        for x in range(5, 12):
            d = math.hypot(x - 8, y - 8)
            if d <= 3.6:
                _px(im, x, y, (228, 228, 232) if d <= 2.6 else (40, 40, 46))
    _line(im, 8, 8, 10, 6, (200, 40, 40))
    return im


def t_rail():
    im = _noise(_fill((240, 240, 240)), 3)
    _shift(im, 0, 15, 0, 1, -40)
    _shift(im, 0, 15, 14, 15, -40)
    for x in (0, 8):
        _shift(im, x, x + 1, 0, 15, -50)
    return im


def t_naval_top():
    im = t_planks()
    for k in (0, 15):
        _shift(im, 0, 15, k, k, -64)
        _shift(im, k, k, 0, 15, -64)
    for k in (1, 14):
        _shift(im, 1, 14, k, k, -26)
        _shift(im, k, k, 1, 14, -26)
    for y in range(16):                               # barre (roue de gouvernail)
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if 3.6 <= d <= 5.0:
                _px(im, x, y, (46, 34, 24))
            elif d <= 1.6:
                _px(im, x, y, (214, 168, 70))
    for a in range(0, 360, 45):
        x = 7.5 + 6.6 * math.cos(math.radians(a))
        y = 7.5 + 6.6 * math.sin(math.radians(a))
        _line(im, 7, 7, int(round(x)), int(round(y)), (46, 34, 24))
        _px(im, int(round(x)), int(round(y)), (214, 168, 70))
    return im


def t_naval_side():
    im = t_planks()
    _rect(im, 0, 0, 15, 2, (74, 54, 30))
    _noise(im, 3)
    nv = (28, 44, 92)
    _rect(im, 7, 5, 8, 12, nv)                      # ancre
    _rect(im, 5, 6, 10, 6, nv)
    _px(im, 7, 4, nv)
    _px(im, 8, 4, nv)
    for (x, y) in ((4, 10), (5, 11), (6, 12), (9, 12), (10, 11), (11, 10)):
        _px(im, x, y, nv)
    return im


def t_naval_front():
    im = t_planks()
    _rect(im, 0, 0, 15, 2, (74, 54, 30))
    _noise(im, 3)
    for k in (5, 12):
        _shift(im, 2, 13, k, k, -46)
    for x in (2, 13):
        _shift(im, x, x, 5, 12, -46)
    _rect(im, 6, 8, 9, 9, (214, 168, 70))           # poignee
    for x in range(2, 14):                            # vagues
        _px(im, x, 14, (40, 70, 150))
    return im


def _hull_piece(kind, accent):
    rows = {
        "bow": ["................", "................", "................", "................", "................",
                "...........KK...", "..........KTTK..", "..KKKKKKKKTTTTK.", "..KTTTTTTTTTTTK.",
                "..KTTTTTTTTTTK..", "..KRRRRRRRRRK...", "..KRRRRRRRRK....", "..KKKKKKKKK.....",
                "................", "................", "................"],
        "stern": ["................", "................", "................", "................", "................",
                  "...KK...........", "..KTTK..........", ".KTTTTKKKKKKKK..", ".KTTTTTTTTTTTK..",
                  "..KTTTTTTTTTTK..", "...KRRRRRRRRRK..", "....KRRRRRRRRK..", ".....KKKKKKKKK..",
                  "................", "................", "................"],
        "mid": ["................", "................", "................", "................", "................",
               "................", "..KKKKKKKKKKKK..", "..KTTTTTTTTTTK..", "..KTTTTTTTTTTK..",
               "..KTTTTTTTTTTK..", "..KRRRRRRRRRRK..", "..KRRRRRRRRRRK..", "..KKKKKKKKKKKK..",
               "................", "................", "................"],
    }[kind]
    im = _ascii(rows)
    for x in range(3, 13):                            # bande de couleur + rivets
        _px(im, x, 8, accent)
    for x in (4, 7, 10):
        _px(im, x, 9, PAL["G"])
    return im


def _icons():
    I = {}
    bucket = ["................", "................", "...KKKKKKKKKK...", "..KWWGGGGGGGGK..",
              "..KGgggggggggK..", "..KGGGGGGGGGGK..", "...KGGGGGGGGK...", "...KGGGGGGGGK...",
              "...KGGGGGGGGK...", "...KGGggGGGGK...", "....KGGGGGGK....", "....KGGGGGGK....",
              "....KKKKKKKK....", "................", "................", "................"]
    I["bi_bucket"] = _ascii(bucket)
    wb = list(bucket)
    wb[4] = "..KUuuUUUUUUUK.."
    wb[5] = "..KGUUUUUUUUGK.."
    I["bi_water_bucket"] = _ascii(wb)
    I["bi_rowboat"] = _ascii([
        "................", "................", "................", "................", "................",
        ".K............K.", ".KB..........BK.", ".KpB........BpK.", "..KpBBBBBBBBpK..",
        "..KpppppppppbK..", "...KbppppppbK...", "....KbbbbbbK....", ".....KKKKKK.....",
        "uUuUuUuUuUuUuUuU", "................", "................"])
    I["bi_drakkar"] = _ascii([
        ".......K........", "...KKKKKKKKKK...", "...RWRWKRWRWR...", "...RWRWKRWRWR...",
        "...RWRWKRWRWR...", "....RWRKRWRW....", ".....RWKRWR.....", ".......K........",
        "..K....K.....K..", ".KB..........BK.", ".KBbbbbbbbbbbBK.", "..KbBBBBBBBBbK..",
        "...KbbbbbbbbK...", "....KKKKKKKK....", "uUuUuUuUuUuUuUuU", "................"])
    I["bi_motorboat"] = _ascii([
        "................", "................", ".....KK.........", ".....DD.........",
        "...KKKKKKK......", "...KuuKuuK......", "...KuuKuuKK.....", "..KKGGGGGGKKK...",
        ".KWGGGGGGGGGGK..", ".KGGGGGGGGGGGGK.", "..KgGGGGGGGGGK..", "...KrrrrrrrrK...",
        "....KKKKKKKK....", "uUuUuUuUuUuUuUuU", "................", "................"])
    I["bi_liner"] = _ascii([
        "..KK.KK.KK.KK...", "..YY.YY.YY.YY...", "..YY.YY.YY.YY...", ".KWWWWWWWWWWWWK.",
        ".KWuWuWuWuWuWWK.", "KKTTTTTTTTTTTTKK", ".KTTTTTTTTTTTTK.", "..KRRRRRRRRRRK..",
        "...KKKKKKKKKK...", "uUuUuUuUuUuUuUuU", "................", "................",
        "................", "................", "................", "................"])
    I["bi_engine"] = _ascii([
        "................", "...KKKKKK.......", "..KWGGGGGK.KKK..", "..KGGGGGGKKGWGK.",
        "..KGgGGGgGKGKGK.", "..KGGGGGGGKGWGK.", "..KGgGGGgGKKKK..", "..KGGGGGGGK.....",
        "..KKKKKKKKK.....", ".KBBBBBBBBBBK...", ".KbbbbbbbbbbK...", "..KKKKKKKKKK....",
        "................", "................", "................", "................"])
    I["bi_hull_iron"] = _ascii([
        "................", "................", "................", ".KK..........KK.",
        ".KWK........KGK.", ".KWGKKKKKKKKGGK.", ".KWGGGGGGGGGGGK.", "..KGGGGGGGGGGK..",
        "..KGgGGGGGGgGK..", "...KGGGGGGGGK...", "....KgggggggK...", "....KKKKKKKK....",
        "................", "................", "................", "................"])
    I["bi_windshield"] = _ascii([
        "................", "................", "..KKKKKKKKKKKK..", ".KWuuuuKuuuuWGK.",
        ".KuuuWuKuuuuuGK.", ".KuuWuuKuuuuuGK.", ".KuuuuuKuuuuuGK.", ".KuuuuuKuuuuuGK.",
        ".KKKKKKKKKKKKKK.", "..KG........GK..", "..KK........KK..", "................",
        "................", "................", "................", "................"])
    I["bi_l_bow"] = _hull_piece("bow", (240, 240, 240))
    I["bi_l_stern"] = _hull_piece("stern", (240, 240, 240))
    I["bi_l_mid1"] = _hull_piece("mid", (240, 206, 72))
    I["bi_l_mid2"] = _hull_piece("mid", (232, 140, 48))
    I["bi_l_ws_top"] = _ascii([
        "................", "................", "..KKKKKKKKKKKK..", ".KWuuuuKuuuuWGK.",
        ".KuuuWuKuuuuuGK.", ".KuuWuuKuuuuuGK.", ".KuuuuuKuuuuuGK.", ".KKKKKKKKKKKKKK.",
        "................", "................", "................", "................",
        "................", "................", "................", "................"])
    I["bi_l_ws_bot"] = _ascii([
        "................", "................", "................", "................",
        ".KKKKKKKKKKKKKK.", ".KuuuuuKuuuuuGK.", ".KuuuuuKuuuuuGK.", ".KuuuuuKuuuuuGK.",
        ".KKKKKKKKKKKKKK.", "..KG........GK..", "..KK........KK..", "................",
        "................", "................", "................", "................"])
    I["bi_l_hull"] = _ascii([
        "................", "................", "................", "................", "................",
        ".KK.........KK..", ".KTK.......KTTK.", ".KTTKKKKKKKKTTTK", ".KTTTTTTTTTTTTK.",
        "..KTTTTTTTTTTK..", "..KRRRRRRRRRRK..", "...KRRRRRRRRK...", "....KKKKKKKK....",
        "................", "................", "................"])
    I["bi_l_ws"] = _ascii([
        "................", "................", "...KKKKKKKKKK...", "..KWWWWWWWWWWK..",
        "..KWNNWNNWNNWK..", "..KWNuWNuWNuWK..", "..KWNNWNNWNNWK..", "..KWWWWWWWWWWK..",
        "..KKKKKKKKKKKK..", "..KGGGGGGGGGGK..", "..KKKKKKKKKKKK..", "................",
        "................", "................", "................", "................"])
    I["bi_l_engine"] = _ascii([
        "................", "................", "..KKKK..KKKK....", ".KWGGK..KWGGK...",
        ".KGGgK..KGGgK...", ".KGGGKKKKGGGK...", ".KGGGGGGGGGGK...", ".KKKKKKKKKKKK...",
        ".KCCKKKKKKCCK...", ".KCCKgOOgKCCK...", ".KCCKOYYOKCCK...", ".KKKKKKKKKKKK...",
        "................", "................", "................", "................"])
    lock = _fill((70, 70, 78))
    _rect(lock, 0, 0, 15, 0, (20, 20, 24))
    _rect(lock, 0, 15, 15, 15, (20, 20, 24))
    _rect(lock, 0, 0, 0, 15, (20, 20, 24))
    _rect(lock, 15, 0, 15, 15, (20, 20, 24))
    for i in range(1, 15):
        _px(lock, i, i, (110, 110, 120))
        _px(lock, 15 - i, i, (110, 110, 120))
    I["bi_slot_lock"] = lock
    return I


def build_tiles():
    T_ = {}
    T_["bt_table_top"] = t_naval_top()
    T_["bt_table_side"] = t_naval_side()
    T_["bt_table_front"] = t_naval_front()
    T_["bt_plank_dark"] = _dark(t_planks(), 0.62)
    T_["bt_sail"] = t_sail()
    T_["bt_iron"] = t_plates((172, 174, 182))
    T_["bt_deckplate"] = t_plates((112, 116, 124), seam=-26, rivet=22)
    T_["bt_hull_black"] = t_plates((44, 46, 54), seam=-16, rivet=26)
    T_["bt_hull_red"] = t_plates((128, 36, 32), seam=-26, rivet=24)
    T_["bt_white"] = t_white()
    T_["bt_funnel"] = t_funnel()
    T_["bt_funnel_top"] = t_funnel_top()
    T_["bt_window"] = t_window()
    T_["bt_glass"] = t_boat_glass()
    T_["bt_engine"] = t_engine()
    T_["bt_rail"] = t_rail()
    T_.update(_icons())
    return T_




TILES.update(build_tiles())


# ============================================================================
# GENERATION DU MONDE (bruit de valeur vectorise avec numpy)
# ============================================================================
def _hash2(ix, iz, seed):
    h = (ix * 374761393 + iz * 668265263 + seed * 1442695041 + 12345) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF) / 65535.0


def _hash3(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 1103515245 + iz * 668265263 + seed * 1442695041 + 777) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF) / 65535.0


def vnoise2(x, z, seed):
    x0 = np.floor(x).astype(np.int64)
    z0 = np.floor(z).astype(np.int64)
    fx, fz = x - x0, z - z0
    sx, sz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b = _hash2(x0, z0, seed), _hash2(x0 + 1, z0, seed)
    c, d = _hash2(x0, z0 + 1, seed), _hash2(x0 + 1, z0 + 1, seed)
    return a + (b - a) * sx + (c - a) * sz + (a - b - c + d) * sx * sz


def vnoise3(x, y, z, seed):
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    z0 = np.floor(z).astype(np.int64)
    fx, fy, fz = x - x0, y - y0, z - z0
    sx, sy, sz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)

    def L(a, b, t):
        return a + (b - a) * t
    c000, c100 = _hash3(x0, y0, z0, seed), _hash3(x0 + 1, y0, z0, seed)
    c010, c110 = _hash3(x0, y0 + 1, z0, seed), _hash3(x0 + 1, y0 + 1, z0, seed)
    c001, c101 = _hash3(x0, y0, z0 + 1, seed), _hash3(x0 + 1, y0, z0 + 1, seed)
    c011, c111 = _hash3(x0, y0 + 1, z0 + 1, seed), _hash3(x0 + 1, y0 + 1, z0 + 1, seed)
    return L(L(L(c000, c100, sx), L(c010, c110, sx), sy), L(L(c001, c101, sx), L(c011, c111, sx), sy), sz)


def fbm2(x, z, seed, octaves=3):
    total, amp, norm, f = 0.0, 1.0, 0.0, 1.0
    for o in range(octaves):
        total = total + amp * vnoise2(x * f, z * f, seed + o * 131)
        norm += amp
        amp *= 0.5
        f *= 2.0
    return total / norm


def _smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


_CONT_OFF = {}


def _cont_offset(seed):
    """Recentre le bruit 'continents' pour que chaque graine ait ~30% de mer."""
    if seed not in _CONT_OFF:
        g = np.arange(0, WORLD_SIZE, 25, dtype=np.float64)
        gx, gz = np.meshgrid(g, g, indexing="ij")
        c = fbm2(gx / 190.0, gz / 190.0, seed, 3)
        _CONT_OFF[seed] = 0.485 - float(np.median(c))
    return _CONT_OFF[seed]


def column_data(seed, X, Z):
    """Hauteur du terrain, desert, force de la riviere pour des tableaux X, Z."""
    xf, zf = X.astype(np.float64), Z.astype(np.float64)
    cont = fbm2(xf / 190.0, zf / 190.0, seed, 3) + _cont_offset(seed)
    hills = fbm2(xf / 70.0, zf / 70.0, seed + 7, 4)
    detail = fbm2(xf / 14.0, zf / 14.0, seed + 13, 2)
    mount = _smooth(0.52, 0.64, cont)
    base = 40.0 + (cont - 0.5) * 100.0
    h = base + (hills - 0.5) * (14.0 + 130.0 * mount) + (detail - 0.5) * 3.0
    rv = np.abs(fbm2(xf / 190.0, zf / 190.0, seed + 29, 2) - 0.5)
    rw = _smooth(0.045, 0.0, rv)
    rw = rw * _smooth(SEA + 16.0, SEA + 2.0, h)
    h = h - rw * (h - (SEA - 3.0))
    h = np.clip(h, 3, WORLD_H - 24).astype(np.int64)
    temp = fbm2(xf / 200.0, zf / 200.0, seed + 41, 2)
    desert = (temp > 0.68) & (rw < 0.2)
    return h, desert, rw


def spawn_point(seed):
    """Cherche un point de depart sur la terre ferme, pres du centre du monde."""
    c = WORLD_SIZE // 2
    for r in range(0, 400, 4):
        for k in range(max(1, r // 2)):
            a = k * (2 * math.pi / max(1, r // 2))
            x, z = int(c + r * math.cos(a)), int(c + r * math.sin(a))
            h, desert, rw = column_data(seed % 1000003, np.array([x]), np.array([z]))
            if h[0] >= SEA + 2 and rw[0] < 0.05 and not desert[0]:
                return x, z
    return c, c


def generate_chunk(seed, cx, cz):
    seed = seed % 1000003
    H = WORLD_H
    x0, z0 = cx * CHUNK, cz * CHUNK
    X = np.repeat((x0 + np.arange(CHUNK))[:, None], CHUNK, axis=1)
    Z = np.repeat((z0 + np.arange(CHUNK))[None, :], CHUNK, axis=0)
    h, desert, rw = column_data(seed, X, Z)
    rs = np.random.RandomState((seed * 7919 + cx * 104729 + cz * 1299709) & 0x7FFFFFFF)
    Y = np.arange(H)[None, :, None]
    hh = h[:, None, :]
    stone = Y <= hh
    blocks = np.where(stone, STONE, AIR).astype(np.uint8)
    depth = hh - Y
    dirtmask = stone & (depth <= 3)
    sand_col = desert[:, None, :] | ((hh <= SEA + 1) & (hh >= SEA - 6))
    gravel_col = (hh < SEA - 6) & (rs.rand(CHUNK, 1, CHUNK) < 0.3)
    top_mat = np.where(sand_col, SAND, np.where(gravel_col, GRAVEL, DIRT)).astype(np.uint8)
    blocks = np.where(dirtmask, top_mat, blocks).astype(np.uint8)
    grass = stone & (depth == 0) & (top_mat == DIRT) & (hh >= SEA)
    blocks[grass] = GRASS
    blocks[(~stone) & (Y <= SEA)] = WATER
    # grottes (tunnels) + minerais
    ymax = int(h.max()) - 3
    if ymax > 8:
        Xf = (x0 + np.arange(CHUNK))[:, None, None].astype(np.float64)
        Zf = (z0 + np.arange(CHUNK))[None, None, :].astype(np.float64)
        ys = np.arange(5, ymax)[None, :, None].astype(np.float64)
        sub = blocks[:, 5:ymax, :]
        n1 = vnoise3(Xf / 22.0, ys / 13.0, Zf / 22.0, seed + 1000)
        n2 = vnoise3(Xf / 22.0, ys / 13.0, Zf / 22.0, seed + 2000)
        cave = (np.abs(n1 - 0.5) < 0.05) & (np.abs(n2 - 0.5) < 0.05) & (ys < (hh - 3))
        sub[cave & (sub == STONE)] = AIR
        for blk, off, thr, ylim, ylow in [(COAL_ORE, 3000, 0.87, 90, 2), (IRON_ORE, 4000, 0.90, 58, 2),
                                          (GOLD_ORE, 5000, 0.93, 30, 2), (DIAMOND_ORE, 6000, 0.945, 16, 2)] + MOD_ORES:
            top = min(ymax, ylim)
            if top <= ylow:
                continue
            ys2 = np.arange(ylow, top)[None, :, None].astype(np.float64)
            n = vnoise3(Xf / 2.6, ys2 / 2.6, Zf / 2.6, seed + off)
            s2 = blocks[:, ylow:top, :]
            s2[(n > thr) & (s2 == STONE)] = blk
    # bedrock
    blocks[:, 0, :] = BEDROCK
    blocks[:, 1:3, :][rs.rand(CHUNK, 2, CHUNK) < 0.5] = BEDROCK
    _place_trees(seed, cx, cz, blocks)
    _place_plants(seed, cx, cz, blocks)
    return blocks


def _place_trees(seed, cx, cz, blocks):
    cell = 6
    x0, z0 = cx * CHUNK, cz * CHUNK
    gx0, gx1 = (x0 - 3) // cell, (x0 + CHUNK + 2) // cell
    gz0, gz1 = (z0 - 3) // cell, (z0 + CHUNK + 2) // cell
    GX, GZ = np.meshgrid(np.arange(gx0, gx1 + 1), np.arange(gz0, gz1 + 1), indexing="ij")
    TX = GX * cell + (_hash2(GX, GZ, seed + 502) * cell).astype(np.int64)
    TZ = GZ * cell + (_hash2(GZ, GX, seed + 504) * cell).astype(np.int64)
    forest = fbm2(TX / 110.0, TZ / 110.0, seed + 55, 2)
    p = 0.05 + 0.8 * _smooth(0.50, 0.64, forest)
    ok = _hash2(GX, GZ, seed + 503) < p
    ok &= (TX >= 0) & (TZ >= 0) & (TX < WORLD_SIZE) & (TZ < WORLD_SIZE)
    ok &= (TX >= x0 - 2) & (TX <= x0 + CHUNK + 1) & (TZ >= z0 - 2) & (TZ <= z0 + CHUNK + 1)
    if not ok.any():
        return
    th_, dsr, rwv = column_data(seed, TX, TZ)
    ok &= (th_ > SEA) & (~dsr) & (rwv < 0.08)
    for i, j in zip(*np.nonzero(ok)):
        tx, tz, gh = int(TX[i, j]), int(TZ[i, j]), int(th_[i, j])
        r = _hash2(int(GX[i, j]), int(GZ[i, j]), seed + 505)
        th = 4 + int(r * 3)
        top = gh + th
        if top + 3 >= WORLD_H:
            continue
        for y in range(gh + 1, top + 1):
            lx, lz = tx - x0, tz - z0
            if 0 <= lx < CHUNK and 0 <= lz < CHUNK:
                blocks[lx, y, lz] = LOG
        for dy in (-2, -1, 0, 1):
            y = top + dy
            rad = 2 if dy < 0 else 1
            for dx in range(-rad, rad + 1):
                for dz in range(-rad, rad + 1):
                    if rad == 2 and abs(dx) == 2 and abs(dz) == 2 and _hash3(tx + dx, y, tz + dz, seed) < 0.5:
                        continue
                    if dy == 1 and abs(dx) + abs(dz) > 1:
                        continue
                    lx, lz = tx + dx - x0, tz + dz - z0
                    if 0 <= lx < CHUNK and 0 <= lz < CHUNK and blocks[lx, y, lz] == AIR:
                        blocks[lx, y, lz] = LEAVES


MOD_ORES = []        # (bloc, decalage_bruit, seuil, y_max, y_min) ajoutes par les mods
MOD_PLANTS = []      # (bloc, decalage_bruit, seuil_massif, probabilite) : fleurs ajoutees par les mods
PLANT_CHANCE = 0.25  # probabilite d'une fleur dans un massif
_PATCH_COVER = [0.0008, 0.002, 0.005, 0.01, 0.02, 0.04, 0.08, 0.12, 0.2]     # part du terrain en massifs
_PATCH_THR = [0.9216, 0.8989, 0.8705, 0.8444, 0.8128, 0.7746, 0.7280, 0.6951, 0.6445]   # seuil du bruit qui y correspond


def _place_plants(seed, cx, cz, blocks):
    """Fleurs des mods : par massifs (comme dans Minecraft), sur l'herbe, jamais sous un autre bloc."""
    if not MOD_PLANTS:
        return
    free = (blocks[:, :-1, :] == GRASS) & (blocks[:, 1:, :] == AIR)         # herbe avec de l'air au-dessus
    if not free.any():
        return
    x0, z0 = cx * CHUNK, cz * CHUNK
    X = np.repeat((x0 + np.arange(CHUNK))[:, None], CHUNK, axis=1)
    Z = np.repeat((z0 + np.arange(CHUNK))[None, :], CHUNK, axis=0)
    taken = np.zeros((CHUNK, CHUNK), bool)
    for blk, off, thr, prob in MOD_PLANTS:
        patch = fbm2(X / 7.0, Z / 7.0, seed + off, 2) > thr
        pick = patch & (_hash2(X, Z, seed + off + 17) < prob) & ~taken
        if not pick.any():
            continue
        for i, j in zip(*np.nonzero(pick)):
            ys = np.nonzero(free[i, :, j])[0]
            if len(ys):
                blocks[i, int(ys[-1]) + 1, j] = blk
                taken[i, j] = True


class Chunk:
    __slots__ = ("cx", "cz", "blocks", "dirty", "need_mesh", "vbo_o", "n_o", "vbo_w", "n_w", "meshed")

    def __init__(self, cx, cz, blocks):
        self.cx, self.cz, self.blocks = cx, cz, blocks
        self.dirty = False
        self.need_mesh = True
        self.meshed = False
        self.vbo_o = self.vbo_w = 0
        self.n_o = self.n_w = 0


class World:
    def __init__(self, seed, path=None):
        self.seed = seed
        self.path = path
        self.chunks = {}
        self.urgent = []                # chunks a re-mailler tout de suite
        self.tiles = {}                 # coffres et fours : (x, y, z) -> donnees
        if path:
            os.makedirs(os.path.join(path, "chunks"), exist_ok=True)
            self._load_tiles()

    def _load_tiles(self):
        try:
            with open(os.path.join(self.path, "tiles.json"), "r", encoding="utf-8") as f:
                for k, v in json.load(f).items():
                    x, y, z = (int(n) for n in k.split(","))
                    self.tiles[(x, y, z)] = v
        except Exception:
            pass

    def save_tiles(self):
        if self.path:
            with open(os.path.join(self.path, "tiles.json"), "w", encoding="utf-8") as f:
                json.dump({"%d,%d,%d" % k: v for k, v in self.tiles.items()}, f)

    def tile(self, pos, kind):
        """Donnees d'un coffre / four (creees si besoin)."""
        t = self.tiles.get(pos)
        if t is None or t.get("type") != kind:
            if kind == "chest":
                t = {"type": "chest", "items": [None] * 27}
            else:
                t = {"type": "furnace", "items": [None] * 3, "burn": 0.0, "burn_max": 1.0, "cook": 0.0}
            self.tiles[pos] = t
        return t

    @staticmethod
    def in_bounds(cx, cz):
        return 0 <= cx < NCH and 0 <= cz < NCH

    def load_chunk(self, cx, cz):
        if (cx, cz) in self.chunks or not self.in_bounds(cx, cz):
            return self.chunks.get((cx, cz))
        arr = None
        if self.path:
            fn = os.path.join(self.path, "chunks", "%d_%d.npy" % (cx, cz))
            if os.path.isfile(fn):
                try:
                    arr = np.load(fn)
                    if arr.shape != (CHUNK, WORLD_H, CHUNK):
                        arr = None
                except Exception:
                    arr = None
        loaded = arr is not None
        if arr is None:
            arr = generate_chunk(self.seed, cx, cz)
        ch = Chunk(cx, cz, arr)
        ch.dirty = False
        self.chunks[(cx, cz)] = ch
        return ch

    def save_chunk(self, ch):
        if self.path and ch.dirty:
            np.save(os.path.join(self.path, "chunks", "%d_%d.npy" % (ch.cx, ch.cz)), ch.blocks)
            ch.dirty = False

    def save_all(self):
        for ch in self.chunks.values():
            self.save_chunk(ch)
        self.save_tiles()

    def get_block(self, x, y, z):
        if y < 0:
            return BEDROCK
        if y >= WORLD_H:
            return AIR
        if x < 0 or z < 0 or x >= WORLD_SIZE or z >= WORLD_SIZE:
            return BEDROCK
        ch = self.chunks.get((x >> 4, z >> 4))
        if ch is None:
            return STONE
        return int(ch.blocks[x & 15, y, z & 15])

    def is_solid(self, x, y, z):
        return SOLID_PY[self.get_block(x, y, z)]

    def set_block(self, x, y, z, b):
        if y < 0 or y >= WORLD_H or x < 0 or z < 0 or x >= WORLD_SIZE or z >= WORLD_SIZE:
            return False
        ch = self.chunks.get((x >> 4, z >> 4))
        if ch is None:
            return False
        lx, lz = x & 15, z & 15
        ch.blocks[lx, y, lz] = b
        ch.dirty = True
        self._remesh(ch)
        if lx == 0:
            self._remesh_at(ch.cx - 1, ch.cz)
        if lx == 15:
            self._remesh_at(ch.cx + 1, ch.cz)
        if lz == 0:
            self._remesh_at(ch.cx, ch.cz - 1)
        if lz == 15:
            self._remesh_at(ch.cx, ch.cz + 1)
        return True

    def _remesh_at(self, cx, cz):
        ch = self.chunks.get((cx, cz))
        if ch:
            self._remesh(ch)

    def _remesh(self, ch):
        ch.need_mesh = True
        if ch not in self.urgent:
            self.urgent.append(ch)

    def surface_y(self, x, z):
        """Plus haut bloc solide de la colonne (x, z)."""
        for y in range(WORLD_H - 1, -1, -1):
            if SOLID_PY[self.get_block(x, y, z)]:
                return y
        return 0

    def neighbors_ready(self, ch):
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = ch.cx + dx, ch.cz + dz
            if self.in_bounds(nx, nz) and (nx, nz) not in self.chunks:
                return False
        return True


# ============================================================================
# MAILLAGE (transforme un chunk en triangles pour OpenGL, tout en numpy)
# ============================================================================
_FACES = [
    (1, 0, 0, [(1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)], 0.80),
    (-1, 0, 0, [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], 0.80),
    (0, 1, 0, [(0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)], 1.00),
    (0, -1, 0, [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], 0.50),
    (0, 0, 1, [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 0.65),
    (0, 0, -1, [(1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)], 0.65),
]
_UVF = np.array([(0, 1), (1, 1), (1, 0), (0, 0)], np.float32)
_DT = 3.0 / 16.0


def _door_quads(wx, wy, wz, bid):
    """Une porte = une planche fine : fermee au milieu du bloc, ouverte contre un cote."""
    k = bid - DOOR0
    upper, opened, facing = k // 8, (k // 4) % 2, k % 4
    c0, c1 = 0.5 - _DT / 2, 0.5 + _DT / 2
    if not opened:
        box, big = ((0, 1, c0, c1), (4, 5)) if facing in (0, 2) else ((c0, c1, 0, 1), (0, 1))
    elif facing == 0:
        box, big = (0, _DT, 0, 1), (0, 1)
    elif facing == 2:
        box, big = (1 - _DT, 1, 0, 1), (0, 1)
    elif facing == 1:
        box, big = (0, 1, 0, _DT), (4, 5)
    else:
        box, big = (0, 1, 1 - _DT, 1), (4, 5)
    x0, x1, z0, z1 = box
    tdoor = TILE_INDEX["door_upper" if upper else "door_lower"]
    tedge = TILE_INDEX["planks"]
    verts = np.empty((6, 4, 8), np.float32)
    for f, (dx, dy, dz, corners, shade) in enumerate(_FACES):
        u0, v0, u1, v1 = TILE_UV[tdoor if f in big else tedge]
        for j, ((cx, cy, cz), (uf, vf)) in enumerate(zip(corners, _UVF)):
            s = shade * 0.95
            verts[f, j] = (wx + (x1 if cx else x0), wy + cy, wz + (z1 if cz else z0),
                           u0 + (u1 - u0) * uf, v0 + (v1 - v0) * vf, s, s, s)
    return verts.reshape(24, 8)


def _cross_quads(wx, wy, wz, bid, light):
    """Une fleur = deux plans qui se croisent en X (comme l'herbe haute de Minecraft)."""
    u0, v0, u1, v1 = TILE_UV[FACE_TILE[bid, 0]]
    a, b = 0.10, 0.90
    s = 0.92 * light
    verts = np.empty((8, 8), np.float32)
    planes = (((a, a), (b, b)), ((a, b), (b, a)))        # (x0, z0) -> (x1, z1)
    for k, ((xa, za), (xb, zb)) in enumerate(planes):
        for j, (px, py, pz, u, v) in enumerate(((xa, 0, za, u0, v1), (xb, 0, zb, u1, v1),
                                                (xb, 1, zb, u1, v0), (xa, 1, za, u0, v0))):
            verts[k * 4 + j] = (wx + px, wy + py, wz + pz, u, v, s, s, s)
    return verts


def build_chunk_mesh(world, ch):
    """Retourne (sommets_opaques, sommets_eau) : tableaux float32 (n, 8) :
    x y z  u v  r g b   (4 sommets par face, dessines en GL_QUADS)."""
    H = WORLD_H
    P = np.full((18, H, 18), STONE, np.uint8)
    P[1:17, :, 1:17] = ch.blocks
    P[0, :, :] = P[17, :, :] = P[:, :, 0] = P[:, :, 17] = STONE
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = world.chunks.get((ch.cx + dx, ch.cz + dz))
        if nb is None:
            continue
        if dx == 1:
            P[17, :, 1:17] = nb.blocks[0, :, :]
        elif dx == -1:
            P[0, :, 1:17] = nb.blocks[15, :, :]
        elif dz == 1:
            P[1:17, :, 17] = nb.blocks[:, :, 0]
        else:
            P[1:17, :, 0] = nb.blocks[:, :, 15]
    B = P[1:17, :, 1:17]
    # hauteur de la lumiere du ciel pour chaque colonne (18 x 18)
    lb = LIGHTBLOCK[P]
    anyl = lb.any(axis=1)
    hm = np.where(anyl, H - 1 - np.argmax(lb[:, ::-1, :], axis=1), -1)
    above = np.zeros_like(B)
    above[:, :-1, :] = B[:, 1:, :]
    out_o, out_w = [], []
    ox, oz = ch.cx * CHUNK, ch.cz * CHUNK
    for f, (dx, dy, dz, corners, shade) in enumerate(_FACES):
        if dx == 1:
            N = P[2:18, :, 1:17]
        elif dx == -1:
            N = P[0:16, :, 1:17]
        elif dz == 1:
            N = P[1:17, :, 2:18]
        elif dz == -1:
            N = P[1:17, :, 0:16]
        elif dy == 1:
            N = np.zeros_like(B)
            N[:, :-1, :] = B[:, 1:, :]
        else:
            N = np.full_like(B, STONE)
            N[:, 1:, :] = B[:, :-1, :]
        mask = (B != 0) & (~OPAQUE[N]) & (~((N == B) & SAMEHIDE[B])) & (~CUBELESS[B])
        if not mask.any():
            continue
        cor = np.array(corners, np.float32)
        for water in (False, True):
            sel = mask & ((B == WATER) if water else (B != WATER))
            xs, ys, zs = np.nonzero(sel)
            n = xs.shape[0]
            if n == 0:
                continue
            ids = B[xs, ys, zs]
            uv = TILE_UV[FACE_TILE[ids, f]]
            pos = np.empty((n, 4, 3), np.float32)
            pos[:, :, 0] = xs[:, None] + cor[None, :, 0] + ox
            pos[:, :, 2] = zs[:, None] + cor[None, :, 2] + oz
            if water:
                lower = (above[xs, ys, zs] != WATER)[:, None] & (cor[None, :, 1] == 1)
                pos[:, :, 1] = ys[:, None] + np.where(lower, 0.88, cor[None, :, 1])
                light = np.full(n, 0.95, np.float32)
            else:
                pos[:, :, 1] = ys[:, None] + cor[None, :, 1]
                nh = hm[xs + 1 + dx, zs + 1 + dz]
                ny = ys + dy
                d = nh - ny
                light = np.where(d < 0, 1.0, np.maximum(0.28, 0.88 - 0.06 * d)).astype(np.float32)
            col = (shade * light)[:, None, None] * np.ones((1, 4, 3), np.float32)
            verts = np.empty((n, 4, 8), np.float32)
            verts[:, :, 0:3] = pos
            verts[:, :, 3] = uv[:, 0:1] + (uv[:, 2:3] - uv[:, 0:1]) * _UVF[None, :, 0]
            verts[:, :, 4] = uv[:, 1:2] + (uv[:, 3:4] - uv[:, 1:2]) * _UVF[None, :, 1]
            verts[:, :, 5:8] = col
            (out_w if water else out_o).append(verts.reshape(n * 4, 8))
    ddx, ddy, ddz = np.nonzero(CUBELESS[B])
    if len(ddx):
        parts = []
        for x, y, z in zip(ddx, ddy, ddz):
            bid = int(B[x, y, z])
            if CROSS[bid]:
                d = int(hm[x + 1, z + 1]) - int(y)
                light = 1.0 if d < 0 else max(0.28, 0.88 - 0.06 * d)
                parts.append(_cross_quads(ox + int(x), int(y), oz + int(z), bid, light))
            else:
                parts.append(_door_quads(ox + int(x), int(y), oz + int(z), bid))
        out_o.append(np.concatenate(parts))
    zero = np.zeros((0, 8), np.float32)
    return (np.concatenate(out_o) if out_o else zero), (np.concatenate(out_w) if out_w else zero)


# ============================================================================
# PHYSIQUE ET ENTITES
# ============================================================================
EPS = 1e-4
GRAV = 30.0


def _axis_move(world, e, axis, d):
    hw = e.w / 2.0
    if axis == 0:
        e.x += d
    elif axis == 1:
        e.y += d
    else:
        e.z += d
    x0, x1 = int(math.floor(e.x - hw + EPS)), int(math.floor(e.x + hw - EPS))
    y0, y1 = int(math.floor(e.y + EPS)), int(math.floor(e.y + e.h - EPS))
    z0, z1 = int(math.floor(e.z - hw + EPS)), int(math.floor(e.z + hw - EPS))
    hit = None
    for bx in range(x0, x1 + 1):
        for by in range(y0, y1 + 1):
            for bz in range(z0, z1 + 1):
                if world.is_solid(bx, by, bz):
                    c = (bx, by, bz)[axis]
                    if d > 0:
                        hit = c if hit is None else min(hit, c)
                    else:
                        hit = c + 1 if hit is None else max(hit, c + 1)
    if hit is None:
        return
    if axis == 0:
        e.x = (hit - hw - EPS) if d > 0 else (hit + hw + EPS)
        e.vx = 0.0
        e.hit_wall = True
    elif axis == 2:
        e.z = (hit - hw - EPS) if d > 0 else (hit + hw + EPS)
        e.vz = 0.0
        e.hit_wall = True
    else:
        if d > 0:
            e.y = hit - e.h - EPS
            e.vy = min(e.vy, 0.0)
        else:
            e.y = float(hit)
            e.vy = max(e.vy, 0.0)
            e.on_ground = True


def move_entity(world, e, dx, dy, dz):
    n = max(1, int(math.ceil(max(abs(dx), abs(dy), abs(dz)) / 0.4)))
    sx, sy, sz = dx / n, dy / n, dz / n
    e.on_ground = False
    e.hit_wall = False
    for _ in range(n):
        if sy:
            _axis_move(world, e, 1, sy)
        if sx:
            _axis_move(world, e, 0, sx)
        if sz:
            _axis_move(world, e, 2, sz)


def raycast(world, ox, oy, oz, dx, dy, dz, maxd=5.0):
    """Rayon dans les blocs. Retourne (bloc_touche, cellule_avant, distance) ou None."""
    x, y, z = int(math.floor(ox)), int(math.floor(oy)), int(math.floor(oz))
    inf = 1e30
    sx, sy, sz = (1 if dx > 0 else -1), (1 if dy > 0 else -1), (1 if dz > 0 else -1)
    tdx = abs(1.0 / dx) if dx else inf
    tdy = abs(1.0 / dy) if dy else inf
    tdz = abs(1.0 / dz) if dz else inf
    tmx = ((x + 1 - ox) if dx > 0 else (ox - x)) * tdx if dx else inf
    tmy = ((y + 1 - oy) if dy > 0 else (oy - y)) * tdy if dy else inf
    tmz = ((z + 1 - oz) if dz > 0 else (oz - z)) * tdz if dz else inf
    prev = None
    t = 0.0
    while t <= maxd:
        b = world.get_block(x, y, z)
        if b != AIR and b != WATER:
            return (x, y, z), prev, t
        prev = (x, y, z)
        if tmx < tmy and tmx < tmz:
            x += sx
            t = tmx
            tmx += tdx
        elif tmy < tmz:
            y += sy
            t = tmy
            tmy += tdy
        else:
            z += sz
            t = tmz
            tmz += tdz
    return None


def ray_aabb(ox, oy, oz, dx, dy, dz, mn, mx):
    tmin, tmax = 0.0, 1e30
    for o, d, a, b in ((ox, dx, mn[0], mx[0]), (oy, dy, mn[1], mx[1]), (oz, dz, mn[2], mx[2])):
        if abs(d) < 1e-9:
            if o < a or o > b:
                return None
        else:
            t1, t2 = (a - o) / d, (b - o) / d
            if t1 > t2:
                t1, t2 = t2, t1
            tmin, tmax = max(tmin, t1), min(tmax, t2)
            if tmin > tmax:
                return None
    return tmin


def water_at(world, x, y, z):
    return world.get_block(int(math.floor(x)), int(math.floor(y)), int(math.floor(z))) == WATER


class Player:
    w, h, eye = 0.6, 1.8, 1.62

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z
        self.vx = self.vy = self.vz = 0.0
        self.yaw, self.pitch = 0.0, 0.0
        self.health = 20.0
        self.on_ground = False
        self.hit_wall = False
        self.in_water = False
        self.head_water = False
        self.fall = 0.0
        self.air = 15.0
        self.hurt = 0.0
        self.regen = 0.0
        self.since_hurt = 99.0
        self.inv = [None] * 36
        self.sel = 0
        self.dead = False
        self.drown_t = 0.0
        self.armor = [None] * 4               # casque, plastron, jambieres, bottes
        self.creative = False
        self.flying = False
        self.walk_dist = 0.0
        self.bob_amt = 0.0

    def eye_pos(self):
        return self.x, self.y + self.eye, self.z

    def look(self):
        cp = math.cos(math.radians(self.pitch))
        return (math.sin(math.radians(self.yaw)) * cp, math.sin(math.radians(self.pitch)),
                -math.cos(math.radians(self.yaw)) * cp)

    def held(self):
        s = self.inv[self.sel]
        return s[0] if s else 0

    def armor_points(self):
        return sum(ARMOR[s[0]][1] for s in self.armor if s and s[0] in ARMOR)

    def take_damage(self, amount, ignore_armor=False):
        if self.dead or amount <= 0 or self.creative:
            return
        if not ignore_armor:
            amount *= 1.0 - min(20, self.armor_points()) / 25.0     # 20 points = 80 % de degats en moins
        self.health -= amount
        self.hurt = 0.5
        self.since_hurt = 0.0
        if self.health <= 0:
            self.health = 0
            self.dead = True

    def update(self, dt, world, keys, in_ui):
        """keys : dict avec fwd, back, left, right, jump, sneak, sprint (bool)."""
        self.in_water = water_at(world, self.x, self.y + 0.4, self.z)
        self.head_water = water_at(world, self.x, self.y + self.eye, self.z)
        fwd = (1 if keys.get("fwd") else 0) - (1 if keys.get("back") else 0)
        strafe = (1 if keys.get("right") else 0) - (1 if keys.get("left") else 0)
        if in_ui:
            fwd = strafe = 0
        yr = math.radians(self.yaw)
        mx = math.sin(yr) * fwd + math.cos(yr) * strafe
        mz = -math.cos(yr) * fwd + math.sin(yr) * strafe
        ln = math.hypot(mx, mz)
        if ln > 0:
            mx, mz = mx / ln, mz / ln
        jump = keys.get("jump") and not in_ui
        if self.flying and self.creative:
            fs = 15.0 if keys.get("sprint") else 7.5
            k = min(1.0, 10.0 * dt)
            self.vx += (mx * fs - self.vx) * k
            self.vz += (mz * fs - self.vz) * k
            ty = (fs * 0.7 if jump else 0.0) - (fs * 0.7 if (keys.get("sneak") and not in_ui) else 0.0)
            self.vy += (ty - self.vy) * k
            self.fall = 0.0
        else:
            self.flying = False
            speed = 4.3
            if keys.get("sprint") and fwd > 0:
                speed = 5.8
            if keys.get("sneak"):
                speed = 1.6
            if self.in_water:
                speed *= 0.55
            accel = 55.0 if self.on_ground else (20.0 if not self.in_water else 14.0)
            tvx, tvz = mx * speed, mz * speed
            k = min(1.0, accel * dt / max(speed, 1.0))
            self.vx += (tvx - self.vx) * k
            self.vz += (tvz - self.vz) * k
            if self.in_water:
                self.vy -= 6.0 * dt
                if jump:
                    self.vy += 20.0 * dt
                self.vy = max(-3.0, min(self.vy, 3.6))
                self.fall = 0.0
            else:
                self.vy = max(self.vy - GRAV * dt, -60.0)
                if jump and self.on_ground:
                    self.vy = 8.9
        prev_vy = self.vy
        move_entity(world, self, self.vx * dt, self.vy * dt, self.vz * dt)
        if self.flying and self.on_ground and prev_vy < -0.5:
            self.flying = False
        # balancement de la main quand on marche
        hs = math.hypot(self.vx, self.vz)
        walking = self.on_ground and hs > 0.5 and not self.flying
        if walking:
            self.walk_dist += hs * dt * 0.55
        self.bob_amt += ((1.0 if walking else 0.0) - self.bob_amt) * min(1.0, 8.0 * dt)
        # degats de chute
        if not self.in_water and not self.on_ground and prev_vy < 0 and not self.flying:
            self.fall += -prev_vy * dt
        if self.on_ground:
            if self.fall > 3.2:
                self.take_damage(math.ceil(self.fall - 3.0), True)
            self.fall = 0.0
        # air / noyade
        if self.head_water:
            self.air -= dt
            if self.air <= 0:
                self.drown_t += dt
                if self.drown_t >= 1.0:
                    self.drown_t = 0.0
                    self.take_damage(2, True)
        else:
            self.air = min(15.0, self.air + dt * 5)
            self.drown_t = 0.0
        # limites du monde
        self.x = max(0.35, min(WORLD_SIZE - 0.35, self.x))
        self.z = max(0.35, min(WORLD_SIZE - 0.35, self.z))
        if self.y < -30:
            self.take_damage(4, True)
            self.y = WORLD_H
        self.hurt = max(0.0, self.hurt - dt)
        self.since_hurt += dt
        if not self.dead and self.health < 20 and self.since_hurt > 4.0:
            self.regen += dt
            if self.regen >= 3.0:
                self.regen = 0.0
                self.health = min(20.0, self.health + 1.0)


MOBS = {
    "cow": dict(hp=10, w=0.9, h=1.4, speed=1.3, hostile=False, sight=0,
                drops=[(RAW_BEEF, 1, 3), (LEATHER, 0, 2)]),
    "pig": dict(hp=10, w=0.9, h=0.9, speed=1.3, hostile=False, sight=0, drops=[(RAW_PORK, 1, 3)]),
    "chicken": dict(hp=4, w=0.4, h=0.7, speed=1.1, hostile=False, sight=0,
                    drops=[(FEATHER, 0, 2), (RAW_CHICKEN, 1, 1)]),
    "horse": dict(hp=22, w=1.3, h=1.6, speed=1.9, hostile=False, sight=0, drops=[(LEATHER, 0, 2)]),
    "creeper": dict(hp=20, w=0.6, h=1.7, speed=2.7, hostile=True, sight=16, drops=[(GUNPOWDER, 0, 2)]),
    "zombie": dict(hp=20, w=0.6, h=1.9, speed=2.4, hostile=True, sight=18, drops=[(ROTTEN, 0, 2)]),
    "skeleton": dict(hp=20, w=0.6, h=1.9, speed=2.4, hostile=True, sight=18, drops=[(BONE, 0, 2)]),
}


class Mob:
    def __init__(self, kind, x, y, z):
        d = MOBS[kind]
        self.kind = kind
        self.x, self.y, self.z = x, y, z
        self.vx = self.vy = self.vz = 0.0
        self.kx = self.kz = 0.0
        self.yaw = random.random() * math.tau
        self.w, self.h = d["w"], d["h"]
        self.hp = float(d["hp"])
        self.hostile = d["hostile"]
        self.on_ground = False
        self.hit_wall = False
        self.hurt = 0.0
        self.walk = random.random() * 10
        self.state = "idle"
        self.timer = random.random() * 3
        self.dir = random.random() * math.tau
        self.attack_cd = 0.0
        self.shoot_cd = 2.0
        self.fuse = -1.0
        self.flee = 0.0
        self.dead = False
        self.burn_t = 0.0
        self.exposed = False
        self.check_t = random.random()
        self.speed_now = 0.0
        self.age = 0.0

    def damage(self, amount, fx, fz):
        self.hp -= amount
        self.hurt = 0.4
        ln = math.hypot(fx, fz) or 1.0
        self.kx, self.kz = fx / ln * 5.0, fz / ln * 5.0
        self.vy = max(self.vy, 5.0)
        if not self.hostile:
            self.flee = 5.0
        if self.hp <= 0:
            self.dead = True

    def update(self, dt, S):
        world, pl = S.world, S.player
        if (int(math.floor(self.x)) >> 4, int(math.floor(self.z)) >> 4) not in world.chunks:
            return
        self.age += dt
        d = MOBS[self.kind]
        sp = d["speed"]
        self.hurt = max(0.0, self.hurt - dt)
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.flee = max(0.0, self.flee - dt)
        dx, dz = pl.x - self.x, pl.z - self.z
        dist = math.hypot(dx, dz)
        dy = pl.y - self.y
        tvx = tvz = 0.0
        in_water = water_at(world, self.x, self.y + 0.3, self.z)
        chasing = self.hostile and (not pl.dead) and (not pl.creative) and dist < d["sight"] and abs(dy) < 12
        if chasing:
            ang = math.atan2(dx, dz)
            self.yaw = ang
            fx, fz = math.sin(ang), math.cos(ang)
            if self.kind == "zombie":
                if dist > 0.9:
                    tvx, tvz = fx * sp, fz * sp
                if dist < 1.5 and abs(dy) < 1.6 and self.attack_cd <= 0:
                    self.attack_cd = 1.0
                    S.hurt_player(3, fx, fz)
            elif self.kind == "creeper":
                if self.fuse >= 0:
                    self.fuse += dt
                    if dist > 5.0:
                        self.fuse = -1.0
                    elif self.fuse >= 1.5:
                        S.explode(self.x, self.y + 0.8, self.z, 3.2)
                        self.dead = True
                        self.hp = -1
                        self.fuse = -2
                        return
                else:
                    if dist < 2.8:
                        self.fuse = 0.0
                if self.fuse < 0 and dist > 1.5:
                    tvx, tvz = fx * sp, fz * sp
            else:  # skeleton
                if dist > 11:
                    tvx, tvz = fx * sp, fz * sp
                elif dist < 6:
                    tvx, tvz = -fx * sp, -fz * sp
                else:
                    s = 1.0 if (int(self.age / 3) % 2) else -1.0
                    tvx, tvz = -fz * sp * 0.6 * s, fx * sp * 0.6 * s
                self.shoot_cd -= dt
                if self.shoot_cd <= 0 and dist < 18:
                    self.shoot_cd = 2.0
                    S.shoot_arrow(self)
        else:
            self.fuse = -1.0 if self.kind == "creeper" else self.fuse
            if self.flee > 0 and dist < 24:
                ang = math.atan2(-dx, -dz)
                tvx, tvz = math.sin(ang) * sp * 1.7, math.cos(ang) * sp * 1.7
                self.yaw = ang
            else:
                self.timer -= dt
                if self.timer <= 0:
                    if self.state == "idle":
                        self.state = "walk"
                        self.dir = random.random() * math.tau
                        self.timer = 1.5 + random.random() * 3.5
                    else:
                        self.state = "idle"
                        self.timer = 1.0 + random.random() * 4.0
                if self.state == "walk":
                    tvx, tvz = math.sin(self.dir) * sp * 0.8, math.cos(self.dir) * sp * 0.8
                    self.yaw = self.dir
        # sol / eau
        k = min(1.0, 8.0 * dt)
        self.vx += (tvx - self.vx) * k
        self.vz += (tvz - self.vz) * k
        if in_water:
            self.vy = min(self.vy + 22.0 * dt, 2.5)
        else:
            self.vy = max(self.vy - GRAV * dt, -50.0)
        if self.hit_wall and self.on_ground and (tvx or tvz):
            self.vy = 8.4
        mvx, mvz = self.vx + self.kx, self.vz + self.kz
        self.kx *= max(0.0, 1.0 - 6.0 * dt)
        self.kz *= max(0.0, 1.0 - 6.0 * dt)
        move_entity(world, self, mvx * dt, self.vy * dt, mvz * dt)
        self.speed_now = math.hypot(self.vx, self.vz)
        self.walk += self.speed_now * dt * 1.6
        # brulure au soleil (zombies, squelettes)
        if self.kind in ("zombie", "skeleton") and S.is_day():
            self.check_t -= dt
            if self.check_t <= 0:
                self.check_t = 0.5
                self.exposed = S.sky_exposed(self.x, self.y + self.h, self.z)
            if self.exposed:
                self.burn_t += dt
                if self.burn_t >= 1.0:
                    self.burn_t = 0.0
                    self.hp -= 2
                    self.hurt = 0.3
                    if self.hp <= 0:
                        self.dead = True
                        self.hp = -99
        if self.y < -10:
            self.dead = True
            self.hp = -99


class DropItem:
    w = h = 0.25

    def __init__(self, item, count, x, y, z, vx=0.0, vy=3.5, vz=0.0):
        self.item, self.count = item, count
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.age = 0.0
        self.on_ground = False
        self.hit_wall = False
        self.spin = random.random() * 6.28

    def update(self, dt, world):
        self.age += dt
        self.spin += dt * 2.0
        if water_at(world, self.x, self.y + 0.1, self.z):
            self.vy = min(self.vy + 14 * dt, 1.0)
            self.vx *= 0.9
            self.vz *= 0.9
        else:
            self.vy = max(self.vy - GRAV * dt, -40.0)
        move_entity(world, self, self.vx * dt, self.vy * dt, self.vz * dt)
        if self.on_ground:
            self.vx *= 0.6
            self.vz *= 0.6


class Arrow:
    def __init__(self, x, y, z, vx, vy, vz):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = 8.0
        self.dead = False

    def update(self, dt, S):
        self.life -= dt
        if self.life <= 0:
            self.dead = True
            return
        self.vy -= 18.0 * dt
        n = max(1, int(math.ceil(math.sqrt(self.vx ** 2 + self.vy ** 2 + self.vz ** 2) * dt / 0.4)))
        for _ in range(n):
            self.x += self.vx * dt / n
            self.y += self.vy * dt / n
            self.z += self.vz * dt / n
            if S.world.is_solid(int(math.floor(self.x)), int(math.floor(self.y)), int(math.floor(self.z))):
                self.dead = True
                return
            pl = S.player
            if (not pl.dead and abs(self.x - pl.x) < 0.4 and pl.y - 0.1 < self.y < pl.y + pl.h + 0.1
                    and abs(self.z - pl.z) < 0.4):
                S.hurt_player(random.choice((2, 3, 3, 4)), self.vx, self.vz)
                self.dead = True
                return


# ============================================================================
# MODULE BATEAUX : formes, physique, pilotage, pont, paquebot (6 cases d'inventaire)
# ============================================================================
def BB(x0, y0, z0, x1, y1, z1, side, top=None, bottom=None, solid=True):
    return (min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1),
            side, top or side, bottom or side, solid)


def sym(x0, y0, z0, x1, y1, z1, side, top=None, bottom=None, solid=True):
    """Une boite et son symetrique par rapport a l'axe du bateau."""
    return [BB(x0, y0, z0, x1, y1, z1, side, top, bottom, solid),
            BB(-x1, y0, z0, -x0, y1, z1, side, top, bottom, solid)]


def _rowboat():
    P = "planks"
    return [BB(-.75, -.15, -1.3, .75, .2, 1.3, P),
            *sym(.6, .2, -1.3, .75, .6, 1.3, P),
            BB(-.6, .2, -1.3, .6, .6, -1.15, P),
            BB(-.6, .2, 1.15, .6, .75, 1.3, P),
            BB(-.6, .2, .1, .6, .38, .4, "bt_plank_dark", "planks", solid=False)]


def _drakkar():
    D, L, LT = "bt_plank_dark", "log_side", "log_top"
    boxes = [BB(-1.3, -.3, -3.0, 1.3, .25, 3.0, D, "planks", D),
             BB(-.9, -.3, 3.0, .9, .25, 3.5, D, "planks", D),
             BB(-.9, -.3, -3.5, .9, .25, -3.0, D, "planks", D),
             *sym(1.15, .25, -3.0, 1.3, .95, 3.0, D),
             *sym(.75, .25, 3.0, .9, .95, 3.5, D),
             *sym(.75, .25, -3.5, .9, .95, -3.0, D),
             BB(-.15, .25, 3.3, .15, 2.4, 3.6, L, LT),
             BB(-.2, 2.2, 3.3, .2, 2.6, 4.1, L, LT, solid=False),
             BB(-.15, .25, -3.6, .15, 1.9, -3.3, L, LT),
             BB(-.14, .25, .4, .14, 5.6, .68, L, LT),
             BB(-1.7, 4.5, .45, 1.7, 4.7, .63, L, LT, solid=False),
             BB(-1.6, 2.0, .5, 1.6, 4.5, .56, "bt_sail", solid=False),
             BB(-1.15, .25, -1.9, 1.15, .45, -1.55, D, "planks", solid=False),
             BB(-1.15, .25, 1.4, 1.15, .45, 1.75, D, "planks", solid=False)]
    for zc in (-2.3, -1.3, -.3, .7, 1.7, 2.6):                    # boucliers sur les flancs
        boxes += [BB(-1.38, .3, zc, -1.3, .8, zc + .5, "bt_sail", solid=False),
                  BB(1.3, .3, zc, 1.38, .8, zc + .5, "bt_sail", solid=False)]
    return boxes


def _motorboat():
    I, DK = "bt_iron", "bt_deckplate"
    return [BB(-1.1, -.4, -2.6, 1.1, .3, 1.0, I, DK, "bt_hull_red"),
            BB(-.85, -.4, 1.0, .85, .3, 1.8, I, DK, "bt_hull_red"),
            BB(-.55, -.4, 1.8, .55, .3, 2.6, I, DK, "bt_hull_red"),
            *sym(.95, .3, -2.6, 1.1, 1.0, 1.0, I),
            *sym(.7, .3, 1.0, .85, 1.0, 1.8, I),
            *sym(.4, .3, 1.8, .55, 1.0, 2.6, I),
            BB(-.95, .3, -2.6, .95, 1.0, -2.45, I),
            BB(-.55, .3, 2.2, .55, .55, 2.6, I, DK),
            BB(-.5, .3, -2.4, .5, 1.0, -1.5, "bt_engine", "bt_iron"),
            BB(-.15, 1.0, -2.1, .15, 1.9, -1.8, "bt_funnel", "bt_funnel_top"),
            BB(-.9, .9, .45, .9, 1.75, .55, "bt_glass", solid=False),
            BB(-.95, .9, .4, -.85, 1.8, .6, I, solid=False),
            BB(.85, .9, .4, .95, 1.8, .6, I, solid=False),
            BB(-.95, 1.75, .4, .95, 1.85, .6, I, solid=False),
            BB(-.35, .3, .1, .35, .8, .35, "bt_engine", "bt_iron", solid=False)]


def _liner():
    RD, BK, W, WN = "bt_hull_red", "bt_hull_black", "bt_white", "bt_window"
    boxes = [BB(-2.3, -1.6, -9.5, 2.3, -.1, 6.5, RD),
             BB(-1.6, -1.6, 6.5, 1.6, -.1, 8.5, RD),
             BB(-.8, -1.6, 8.5, .8, -.1, 10.0, RD),
             BB(-1.9, -1.6, -10.5, 1.9, -.1, -9.5, RD),
             BB(-2.5, -.1, -10.5, 2.5, .8, 7.0, BK, "planks", BK),
             BB(-2.0, -.1, 7.0, 2.0, .8, 8.5, BK, "planks", BK),
             BB(-1.4, -.1, 8.5, 1.4, .8, 10.0, BK, "planks", BK),
             BB(-.6, -.1, 10.0, .6, .8, 11.0, BK, "planks", BK),
             BB(-2.0, -.1, -11.5, 2.0, .8, -10.5, BK, "planks", BK),
             # superstructure blanche (deux etages : on peut monter dessus en sautant)
             BB(-1.3, .8, -6.0, 1.3, 2.0, 3.5, W),
             BB(-.7, 2.0, -5.0, .7, 3.2, 2.5, W),
             BB(-1.4, .8, 5.0, 1.4, 2.2, 7.0, W),
             BB(-1.5, 2.2, 4.9, 1.5, 2.4, 7.1, "bt_iron", solid=False),
             BB(-1.3, 1.2, 7.0, 1.3, 2.0, 7.06, WN, solid=False),
             BB(-1.34, 1.2, -5.6, -1.3, 1.8, 3.0, WN, solid=False),
             BB(1.3, 1.2, -5.6, 1.34, 1.8, 3.0, WN, solid=False),
             BB(-.72, 2.4, -4.6, -.68, 2.9, 2.0, WN, solid=False),
             BB(.68, 2.4, -4.6, .72, 2.9, 2.0, WN, solid=False),
             # mats
             BB(-.12, .8, 8.0, .12, 6.4, 8.24, "bt_iron"),
             BB(-.12, .8, -8.6, .12, 5.8, -8.36, "bt_iron"),
             # rambardes
             BB(-2.5, .8, -10.5, -2.4, 1.5, 7.0, "bt_rail"),
             BB(2.4, .8, -10.5, 2.5, 1.5, 7.0, "bt_rail"),
             BB(-2.4, .8, -10.6, 2.4, 1.5, -10.5, "bt_rail")]
    for zc in (-4.0, -2.4, -0.8, 0.8):                             # 4 cheminees
        boxes += [BB(-.45, 3.2, zc - .5, .45, 5.8, zc + .5, "bt_funnel"),
                  BB(-.47, 5.8, zc - .52, .47, 6.3, zc + .52, "bt_funnel_top")]
    return boxes


SPECS = {
    "rowboat": dict(item=ROWBOAT, slots=5, engine=0, vmax=3.2, vback=1.2, accel=2.0, turn=100.0, depth=1, clear=1,
                    helm=(0.0, .2, -.45), foot=[(-.75, -1.3, .75, 1.3)], boxes=_rowboat(),
                    name=("Wooden Boat", "Bateau en bois")),
    "drakkar": dict(item=DRAKKAR, slots=20, engine=0, vmax=5.0, vback=1.6, accel=1.5, turn=70.0, depth=1, clear=1,
                    helm=(0.0, .25, -2.7), foot=[(-1.3, -3.0, 1.3, 3.0), (-.9, -3.5, .9, 3.5)], boxes=_drakkar(),
                    name=("Longship", "Drakkar")),
    "motorboat": dict(item=MOTORBOAT, slots=50, engine=1, vmax=10.0, vback=2.5, accel=2.2, turn=105.0, depth=1,
                      clear=2, helm=(0.0, .3, -.3),
                      foot=[(-1.1, -2.6, 1.1, 1.0), (-.85, 1.0, .85, 1.8), (-.55, 1.8, .55, 2.6)],
                      boxes=_motorboat(), name=("Iron Motorboat", "Bateau à moteur")),
    "liner": dict(item=LINER, slots=200, engine=2, vmax=7.5, vback=1.8, accel=0.6, turn=24.0, depth=2, clear=2,
                  helm=(0.0, .8, 4.2),
                  foot=[(-2.4, -11.4, 2.4, 7.0), (-1.6, 7.0, 1.6, 9.0), (-.6, 9.0, .6, 10.8)],
                  boxes=_liner(), name=("Ocean Liner", "Paquebot")),
}


def _finish_specs():
    for kind, sp in SPECS.items():
        sp["kind"] = kind
        sp["solids"] = [b[:6] for b in sp["boxes"] if b[9]]
        step = 0.85
        pts = []
        for (x0, z0, x1, z1) in sp["foot"]:
            nx = max(1, int(math.ceil((x1 - x0) / step)))
            nz = max(1, int(math.ceil((z1 - z0) / step)))
            for i in range(nx + 1):
                for j in range(nz + 1):
                    pts.append((x0 + (x1 - x0) * i / nx, z0 + (z1 - z0) * j / nz))
        sp["samples"] = pts
        rad = 0.0
        for b in sp["boxes"]:
            for x in (b[0], b[3]):
                for z in (b[2], b[5]):
                    rad = max(rad, math.hypot(x, z))
        sp["radius"] = rad + 2.5


_finish_specs()


# ============================================================================
# LE BATEAU (entite du monde)
# ============================================================================
def to_world(bx, bz, yaw, lx, lz):
    c, s = math.cos(yaw), math.sin(yaw)
    return bx + lx * c + lz * s, bz - lx * s + lz * c


def to_local(bx, bz, yaw, wx, wz):
    c, s = math.cos(yaw), math.sin(yaw)
    dx, dz = wx - bx, wz - bz
    return dx * c - dz * s, dx * s + dz * c


def _obb_overlap(ac, au, av, ah, bc, bu, bv, bh):
    """Deux rectangles orientes (centre, axes, demi-tailles) se chevauchent-ils ?"""
    dx, dz = bc[0] - ac[0], bc[1] - ac[1]
    for ax in (au, av, bu, bv):
        dist = abs(dx * ax[0] + dz * ax[1])
        ra = ah[0] * abs(au[0] * ax[0] + au[1] * ax[1]) + ah[1] * abs(av[0] * ax[0] + av[1] * ax[1])
        rb = bh[0] * abs(bu[0] * ax[0] + bu[1] * ax[1]) + bh[1] * abs(bv[0] * ax[0] + bv[1] * ax[1])
        if dist > ra + rb:
            return False
    return True


def _cp(s):
    return [s[0], s[1]] if s else None


class Boat:
    def __init__(self, kind, x, y, z, yaw=0.0):
        self.kind = kind
        self.spec = SPECS[kind]
        self.x, self.y, self.z, self.yaw = float(x), float(y), float(z), float(yaw)
        self.last = (self.x, self.z, self.yaw)
        self.speed = 0.0
        self.power = 0.0
        self.storage = [None] * self.spec["slots"]
        self.fuel = [None] * 4
        self.water = [None] * 6
        self.fuel_left = self.fuel_total = 0.0
        self.water_left = self.water_total = 0.0
        self.hit = 0.0
        self.phase = random.random() * 6.28

    # ---------- reperes ----------
    def helm_world(self):
        hx, hy, hz = self.spec["helm"]
        wx, wz = to_world(self.x, self.z, self.yaw, hx, hz)
        return wx, self.y + hy, wz

    def to_local(self, wx, wz):
        return to_local(self.x, self.z, self.yaw, wx, wz)

    def to_world(self, lx, lz):
        return to_world(self.x, self.z, self.yaw, lx, lz)

    # ---------- navigation : il faut de l'eau sous la coque et de la place au-dessus ----------
    def fits(self, world, x, z, yaw):
        y0 = int(round(self.y))
        depth, clear = self.spec["depth"], self.spec["clear"]
        c, s = math.cos(yaw), math.sin(yaw)
        gb = world.get_block
        solid = SOLID_PY
        seen = set()
        for (lx, lz) in self.spec["samples"]:
            bx = int(math.floor(x + lx * c + lz * s))
            bz = int(math.floor(z - lx * s + lz * c))
            if (bx, bz) in seen:
                continue
            seen.add((bx, bz))
            for k in range(1, depth + 1):
                if gb(bx, y0 - k, bz) != WATER:
                    return False
            for k in range(clear):
                if solid[gb(bx, y0 + k, bz)]:
                    return False
        return True

    # ---------- les bateaux ne se traversent pas ----------
    def _rects(self, x, z, yaw):
        out = []
        c, s = math.cos(yaw), math.sin(yaw)
        for (x0, z0, x1, z1) in self.spec["foot"]:
            lcx, lcz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
            out.append((x + lcx * c + lcz * s, z - lcx * s + lcz * c,
                        (x1 - x0) / 2.0 + 0.1, (z1 - z0) / 2.0 + 0.1))
        return out

    def clear_of_boats(self, S, x, z, yaw):
        mine = None
        ua, va = (math.cos(yaw), -math.sin(yaw)), (math.sin(yaw), math.cos(yaw))
        for o in S.boats:
            if o is self or math.hypot(o.x - x, o.z - z) > self.spec["radius"] + o.spec["radius"]:
                continue
            if mine is None:
                mine = self._rects(x, z, yaw)
            ub, vb = (math.cos(o.yaw), -math.sin(o.yaw)), (math.sin(o.yaw), math.cos(o.yaw))
            for (ax, az, ahx, ahz) in mine:
                for (bx, bz, bhx, bhz) in o._rects(o.x, o.z, o.yaw):
                    if _obb_overlap((ax, az), ua, va, (ahx, ahz), (bx, bz), ub, vb, (bhx, bhz)):
                        return False
        return True

    def _can(self, S, x, z, yaw):
        return self.fits(S.world, x, z, yaw) and self.clear_of_boats(S, x, z, yaw)

    # ---------- moteur a vapeur : charbon (ou bois) + seaux d'eau ----------
    def _load_fuel(self):
        for i, s in enumerate(self.fuel):
            if s and s[0] in FUEL:
                v = FUEL[s[0]]
                s[1] -= 1
                if s[1] <= 0:
                    self.fuel[i] = None
                self.fuel_left = self.fuel_total = v
                return

    def _load_water(self):
        for i, s in enumerate(self.water):
            if s and s[0] == WATER_BUCKET:
                self.water[i] = [BUCKET, 1]            # le seau se vide
                self.water_left = self.water_total = WATER_SECONDS
                return

    def engine_step(self, S, dt, throttle, driven):
        mult = self.spec["engine"]
        if not mult:
            return
        run = False
        if driven and throttle != 0:
            if self.fuel_left <= 0:
                self._load_fuel()
            if self.water_left <= 0:
                self._load_water()
            if self.fuel_left > 0 and self.water_left > 0:
                self.fuel_left = max(0.0, self.fuel_left - dt * mult)
                self.water_left = max(0.0, self.water_left - dt * mult)
                run = True
            elif S.engine_msg_t <= 0:
                S.engine_msg_t = 4.0
                S.msg(tr("b_engine_empty"))
        if run:
            self.power = min(1.0, self.power + dt * (0.7 if mult == 1 else 0.4))
        else:
            self.power = max(0.0, self.power - dt * 0.9)

    # ---------- mouvement ----------
    def update(self, S, dt, throttle, steer, driven):
        """Retourne la rotation effectuee (radians)."""
        sp = self.spec
        self.engine_step(S, dt, throttle, driven)
        tgt = throttle * (sp["vmax"] if throttle > 0 else sp["vback"])
        if sp["engine"]:
            tgt *= self.power
        k = min(1.0, (sp["accel"] if throttle else 0.5) * dt)
        self.speed += (tgt - self.speed) * k
        if abs(self.speed) < 0.02 and not throttle:
            self.speed = 0.0
        dyaw = 0.0
        if steer:
            f = min(1.0, abs(self.speed) / (0.35 * sp["vmax"]))
            if driven and throttle:
                f = max(f, 0.25)
            d = -steer * math.radians(sp["turn"]) * f * dt
            if self.speed < -0.05:
                d = -d
            if d and self._can(S, self.x, self.z, self.yaw + d):
                self.yaw += d
                dyaw = d
        if self.speed:
            dist = self.speed * dt
            nx = self.x + math.sin(self.yaw) * dist
            nz = self.z + math.cos(self.yaw) * dist
            if self._can(S, nx, nz, self.yaw):
                self.x, self.z = nx, nz
            elif self._can(S, nx, self.z, self.yaw):
                self.x = nx
                self.speed *= 0.6
            elif self._can(S, self.x, nz, self.yaw):
                self.z = nz
                self.speed *= 0.6
            else:
                self.speed = 0.0
        return dyaw

    # ---------- sauvegarde (JSON) ----------
    def to_dict(self):
        return {"kind": self.kind, "x": self.x, "y": self.y, "z": self.z, "yaw": self.yaw,
                "storage": self.storage, "fuel": self.fuel, "water": self.water,
                "fuel_left": self.fuel_left, "fuel_total": self.fuel_total,
                "water_left": self.water_left, "water_total": self.water_total}

    @staticmethod
    def from_dict(d):
        kind = d.get("kind")
        if kind not in SPECS:
            return None
        b = Boat(kind, d["x"], d["y"], d["z"], d.get("yaw", 0.0))

        def fill(dst, src):
            for i, s in enumerate((src or [])[:len(dst)]):
                if isinstance(s, (list, tuple)) and len(s) == 2:
                    dst[i] = [int(s[0]), int(s[1])]
        fill(b.storage, d.get("storage"))
        fill(b.fuel, d.get("fuel"))
        fill(b.water, d.get("water"))
        b.fuel_left = float(d.get("fuel_left", 0.0))
        b.fuel_total = float(d.get("fuel_total", 0.0))
        b.water_left = float(d.get("water_left", 0.0))
        b.water_total = float(d.get("water_total", 0.0))
        return b


def load_boats(path):
    fn = os.path.join(path, "boats.json")
    out = []
    try:
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)
        for d in data.get("boats", []):
            b = Boat.from_dict(d)
            if b is not None:
                out.append(b)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return out


def save_boats(path, boats):
    fn = os.path.join(path, "boats.json")
    tmp = fn + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "boats": [b.to_dict() for b in boats]}, f)
        os.replace(tmp, fn)
    except OSError as e:
        print("Erreur de sauvegarde des bateaux :", e)


# ============================================================================
# OUTILS : rayon dans l'eau, rayon dans les bateaux
# ============================================================================
def water_ray(world, ox, oy, oz, dx, dy, dz, maxd=5.0):
    """Premier point d'eau vise (s'arrete sur un bloc plein). -> (x, z, hauteur_de_surface, distance)"""
    t = 0.0
    while t <= maxd:
        x, y, z = ox + dx * t, oy + dy * t, oz + dz * t
        bx, by, bz = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
        b = world.get_block(bx, by, bz)
        if b == WATER:
            yy = by
            while world.get_block(bx, yy + 1, bz) == WATER:
                yy += 1
            surf = float(yy + 1)
            if abs(dy) > 1e-6:                       # point exact ou le regard touche la surface
                ts = (surf - oy) / dy
                if 0.0 <= ts <= t + 0.06:
                    x, z = ox + dx * ts, oz + dz * ts
            return x, z, surf, t
        if b != AIR:
            return None
        t += 0.05
    return None


def ray_boats(boats, ox, oy, oz, dx, dy, dz, maxd):
    """Bateau vise par le regard. -> (bateau, distance) ou (None, 99)."""
    best, bt = None, maxd
    for b in boats:
        ddx, ddz = b.x - ox, b.z - oz
        if ddx * ddx + ddz * ddz > (b.spec["radius"] + maxd) ** 2:
            continue
        lx, lz = b.to_local(ox, oz)
        c, s = math.cos(b.yaw), math.sin(b.yaw)
        dlx, dlz = dx * c - dz * s, dx * s + dz * c
        for bx in b.spec["boxes"]:
            t = ray_aabb(lx, oy - b.y, lz, dlx, dy, dlz, (bx[0], bx[1], bx[2]), (bx[3], bx[4], bx[5]))
            if t is not None and t < bt:
                best, bt = b, t
    return (best, bt) if best else (None, 99.0)


# ============================================================================
# PAQUEBOT = 6 CASES D'INVENTAIRE (1 objet + 5 cases "occupees")
# ============================================================================
def _free_slots(inv):
    return sum(1 for s in inv if s is None)


def fill_locks(inv):
    """Met autant de cases 'occupees' que necessaire (5 par paquebot). Retourne False si pas assez de place."""
    nl = sum(s[1] for s in inv if s and s[0] == LINER)
    locks = [i for i, s in enumerate(inv) if s and s[0] == SLOT_LOCK]
    need = 5 * nl
    while len(locks) > need:
        inv[locks.pop()] = None
    i = len(inv) - 1
    while len(locks) < need and i >= 0:
        if inv[i] is None:
            inv[i] = [SLOT_LOCK, 1]
            locks.append(i)
        i -= 1
    return len(locks) >= need


def normalize_inventory(S):
    """Appelee a chaque image : garde le bon nombre de cases occupees ; sinon ejecte le paquebot."""
    inv = S.player.inv
    for _ in range(4):
        if fill_locks(inv):
            return
        for i, s in enumerate(inv):
            if s and s[0] == LINER:
                inv[i] = None
                S.drop_at(LINER, 1, S.player.x, S.player.y + 1.0, S.player.z)
                S.msg(tr("b_need6_carry"))
                break





# ============================================================================
# ACTIONS DU JOUEUR : poser, monter, descendre, demonter
# ============================================================================
def place_boat(S, kind, hit):
    p, w = S.player, S.world
    x, z, y0, _t = hit
    yaw = math.pi - math.radians(p.yaw)
    b = Boat(kind, x, y0, z, yaw)
    if not b.fits(w, x, z, yaw):
        S.msg(tr("b_no_room"))
        return False
    if not b.clear_of_boats(S, x, z, yaw):
        S.msg(tr("b_already"))
        return False
    S.boats.append(b)
    if not S.creative:
        S._consume_held()
    return True


def fill_bucket(S):
    p = S.player
    s = p.inv[p.sel]
    if s and s[0] == BUCKET:
        if s[1] == 1:
            p.inv[p.sel] = [WATER_BUCKET, 1]
        else:
            s[1] -= 1
            left = inv_add(p.inv, WATER_BUCKET, 1)
            if left:
                S.drop_stack(WATER_BUCKET, left)


def board(S, b):
    p = S.player
    S.driving = b
    S.standing_boat = None
    hx, hy, hz = b.helm_world()
    p.x, p.y, p.z = hx, hy, hz
    p.vx = p.vy = p.vz = 0.0
    p.flying = False
    p.yaw = math.degrees(math.pi - b.yaw) % 360.0
    S.msg(tr("b_helm"), 6.0)


def dismount(S):
    S.driving = None
    S.msg(tr("b_left_helm"))


def dismantle(S, b):
    p = S.player
    if b.kind == "liner" and _free_slots(p.inv) < 6 and not S.creative:
        S.msg(tr("b_need6_pick"))
        return
    for st in b.storage + b.fuel + b.water:
        if st:
            S.drop_at(st[0], st[1], b.x, b.y + 1.2, b.z)
    left = inv_add(p.inv, b.spec["item"], 1)
    if left:
        S.drop_at(b.spec["item"], 1, p.x, p.y + 1.0, p.z)
    if b in S.boats:
        S.boats.remove(b)
    if S.driving is b:
        S.driving = None
    if S.standing_boat is b:
        S.standing_boat = None
    S.target_boat = None


# ============================================================================
# LE JOUEUR MARCHE SUR LE PONT (collision avec les formes du bateau)
# ============================================================================
def resolve_player(S, jump):
    p = S.player
    standing = None
    r = 0.3
    can_climb = bool(jump and p.in_water)          # grimper a bord depuis l'eau (Espace), une seule fois
    for b in S.boats:
        dx, dz = p.x - b.x, p.z - b.z
        if dx * dx + dz * dz > b.spec["radius"] ** 2 or abs(p.y - b.y) > 14:
            continue
        for _ in range(2):
            lx, lz = b.to_local(p.x, p.z)
            ly = p.y - b.y
            c, s = math.cos(b.yaw), math.sin(b.yaw)
            changed = False
            for (x0, y0, z0, x1, y1, z1) in b.spec["solids"]:
                if ly + 1.8 <= y0 + 0.02:
                    continue
                if not (x0 - r < lx < x1 + r and z0 - r < lz < z1 + r):
                    continue
                rel = ly - y1
                if rel > 0.06:
                    continue
                inside = x0 <= lx <= x1 and z0 <= lz <= z1
                if rel >= -0.6:                                   # marche / sol
                    if inside:
                        ly = y1
                        if p.vy < 0:
                            p.vy = 0.0
                        standing, changed = b, True
                    continue
                if can_climb and (y1 - ly) <= 1.45:               # on s'accroche et on grimpe a bord
                    can_climb = False
                    ly = y1
                    lx = min(max(lx, x0 + 0.2), x1 - 0.2) if (x1 - x0) > 0.4 else (x0 + x1) / 2.0
                    lz = min(max(lz, z0 + 0.2), z1 - 0.2) if (z1 - z0) > 0.4 else (z0 + z1) / 2.0
                    p.vy = 0.0
                    standing, changed = b, True
                    continue
                opts = ((x1 + r - lx, 1, 0), (lx - (x0 - r), -1, 0), (z1 + r - lz, 0, 1), (lz - (z0 - r), 0, -1))
                pen, nx, nz = min(opts, key=lambda o: o[0])
                lx += nx * pen
                lz += nz * pen
                wnx, wnz = nx * c + nz * s, -nx * s + nz * c
                vn = p.vx * wnx + p.vz * wnz
                if vn < 0:
                    p.vx -= vn * wnx
                    p.vz -= vn * wnz
                changed = True
            if not changed:
                break
            p.x, p.z = b.to_world(lx, lz)
            p.y = b.y + ly
    if standing is not None:
        p.on_ground = True
        if p.fall > 3.2 and not p.creative:
            p.take_damage(math.ceil(p.fall - 3.0), True)
        p.fall = 0.0
    S.standing_boat = standing




def tiled_quads(box):
    """Une boite -> liste de quads (x, y, z, u, v, ombre), la texture est repetee tous les ~1 bloc."""
    x0, y0, z0, x1, y1, z1, side, top, bottom, _s = box
    mn, mx = (x0, y0, z0), (x1, y1, z1)
    size = (x1 - x0, y1 - y0, z1 - z0)
    quads = []
    for f, (nx, ny, nz, corners, shade) in enumerate(_FACES):
        name = top if f == 2 else (bottom if f == 3 else side)
        u0, v0, u1, v1 = [float(v) for v in TILE_UV[TILE_INDEX[name]]]
        nrm = (nx, ny, nz)
        fixed = [a for a in range(3) if nrm[a] != 0][0]
        fa, fb = [a for a in range(3) if a != fixed]
        n1 = max(1, int(round(size[fa])))
        n2 = max(1, int(round(size[fb])))
        for i in range(n1):
            a0, a1 = i / float(n1), (i + 1) / float(n1)
            for j in range(n2):
                b0, b1 = j / float(n2), (j + 1) / float(n2)
                quad = []
                for (cx, cy, cz), (uf, vf) in zip(corners, _UVF):
                    c = (cx, cy, cz)
                    pos = [0.0, 0.0, 0.0]
                    pos[fixed] = mx[fixed] if c[fixed] else mn[fixed]
                    pos[fa] = mn[fa] + size[fa] * (a1 if c[fa] else a0)
                    pos[fb] = mn[fb] + size[fb] * (b1 if c[fb] else b0)
                    quad.append((pos[0], pos[1], pos[2], u0 + (u1 - u0) * float(uf),
                                 v0 + (v1 - v0) * float(vf), float(shade)))
                quads.append(quad)
    return quads


def _boat_list(R, kind):
    lists = getattr(R, "_boat_lists", None)
    if lists is None:
        lists = R._boat_lists = {}
    if kind not in lists:
        lid = gl.glGenLists(1)
        gl.glNewList(lid, gl.GL_COMPILE)
        gl.glBegin(gl.GL_QUADS)
        for box in SPECS[kind]["boxes"]:
            for quad in tiled_quads(box):
                for (x, y, z, u, v, sh) in quad:
                    gl.glColor3f(sh, sh, sh)
                    gl.glTexCoord2f(u, v)
                    gl.glVertex3f(x, y, z)
        gl.glEnd()
        gl.glEndList()
        lists[kind] = lid
    return lists[kind]




# ============================================================================
# RENDU OPENGL
# ============================================================================
def sky_state(t):
    """Retourne (angle du soleil, hauteur du soleil, facteur de jour 0..1)."""
    u = (t / DAY_LEN) % 1.0
    ang = u * math.tau
    elev = math.sin(ang)
    x = max(0.0, min(1.0, elev * 3.0 + 0.5))
    return ang, elev, x * x * (3 - 2 * x)


def sky_color(t):
    ang, elev, f = sky_state(t)
    day, night = (0.52, 0.70, 1.0), (0.012, 0.016, 0.055)
    c = [night[i] + (day[i] - night[i]) * f for i in range(3)]
    dusk = max(0.0, 1.0 - abs(elev) / 0.3) * 0.55
    for i, v in enumerate((0.95, 0.45, 0.25)):
        c[i] += (v - c[i]) * dusk
    return c


# Modeles des mobs (unites = pixels, 16 px = 1 bloc, +z = avant)
# (tuile, tuile_avant, coin_min, taille, pivot, animation)
MODELS = {
    "cow": dict(scale=0.92, parts=[
        ("cow_body", None, (-6, 12, -9), (12, 10, 18), None, "none"),
        ("cow_head", "cow_face", (-4, 17, 8), (8, 8, 6), None, "none"),
        ("cow_leg", None, (2, 0, 5), (4, 12, 4), None, "A"), ("cow_leg", None, (-6, 0, 5), (4, 12, 4), None, "B"),
        ("cow_leg", None, (2, 0, -9), (4, 12, 4), None, "B"), ("cow_leg", None, (-6, 0, -9), (4, 12, 4), None, "A")]),
    "pig": dict(scale=0.95, parts=[
        ("pig", None, (-5, 6, -8), (10, 8, 16), None, "none"),
        ("pig", "pig_face", (-4, 7, 8), (8, 8, 8), None, "none"),
        ("pig_leg", None, (1, 0, 4), (4, 6, 4), None, "A"), ("pig_leg", None, (-5, 0, 4), (4, 6, 4), None, "B"),
        ("pig_leg", None, (1, 0, -8), (4, 6, 4), None, "B"), ("pig_leg", None, (-5, 0, -8), (4, 6, 4), None, "A")]),
    "chicken": dict(scale=0.8, parts=[
        ("chicken", None, (-3, 5, -4), (6, 6, 8), None, "none"),
        ("chicken", "chicken_face", (-2, 9, 3), (4, 6, 3), None, "none"),
        ("chicken_leg", None, (-2.5, 0, -1), (2, 5, 2), None, "A"), ("chicken_leg", None, (0.5, 0, -1), (2, 5, 2), None, "B"),
        ("chicken", None, (-4, 6, -3), (1, 4, 6), None, "none"), ("chicken", None, (3, 6, -3), (1, 4, 6), None, "none")]),
    "horse": dict(scale=0.8, parts=[
        ("horse", None, (-5, 16, -11), (10, 10, 22), None, "none"),
        ("horse", None, (-2, 20, 8), (4, 12, 5), None, "none"),
        ("horse", "horse_face", (-2.5, 27, 9), (5, 6, 11), None, "none"),
        ("horse_mane", None, (-0.5, 21, 6.5), (1, 12, 2), None, "none"),
        ("horse_mane", None, (-1, 15, -13), (2, 10, 2), None, "none"),
        ("horse_leg", None, (1, 0, 7), (4, 16, 4), None, "A"), ("horse_leg", None, (-5, 0, 7), (4, 16, 4), None, "B"),
        ("horse_leg", None, (1, 0, -11), (4, 16, 4), None, "B"), ("horse_leg", None, (-5, 0, -11), (4, 16, 4), None, "A")]),
    "creeper": dict(scale=1.05, parts=[
        ("creeper", "creeper_face", (-4, 18, -4), (8, 8, 8), None, "none"),
        ("creeper", None, (-4, 6, -2), (8, 12, 4), None, "none"),
        ("creeper", None, (0, 0, 0), (4, 6, 4), None, "A"), ("creeper", None, (-4, 0, 0), (4, 6, 4), None, "B"),
        ("creeper", None, (0, 0, -4), (4, 6, 4), None, "B"), ("creeper", None, (-4, 0, -4), (4, 6, 4), None, "A")]),
    "zombie": dict(scale=1.0, parts=[
        ("zombie_skin", "zombie_face", (-4, 24, -4), (8, 8, 8), None, "none"),
        ("zombie_shirt", None, (-4, 12, -2), (8, 12, 4), None, "none"),
        ("zombie_skin", None, (4, 12, -2), (4, 12, 4), (6, 24, 0), "F"),
        ("zombie_skin", None, (-8, 12, -2), (4, 12, 4), (-6, 24, 0), "F"),
        ("zombie_pants", None, (0, 0, -2), (4, 12, 4), None, "A"), ("zombie_pants", None, (-4, 0, -2), (4, 12, 4), None, "B")]),
    "skeleton": dict(scale=1.0, parts=[
        ("skel_skin", "skel_face", (-4, 24, -4), (8, 8, 8), None, "none"),
        ("skel_ribs", None, (-4, 12, -2), (8, 12, 4), None, "none"),
        ("skel_limb", None, (4, 12, -1), (2, 12, 2), (5, 24, 0), "F"),
        ("skel_limb", None, (-6, 12, -1), (2, 12, 2), (-5, 24, 0), "F"),
        ("skel_limb", None, (1, 0, -1), (2, 12, 2), None, "A"), ("skel_limb", None, (-3, 0, -1), (2, 12, 2), None, "B")]),
}

# ---------------------------------------------------------------------------
# OBJET TENU EN MAIN : modele 3D extrude (comme Minecraft) + animation de coup
# ---------------------------------------------------------------------------
def sprite_quads(tile):
    """Objet plat 'extrude' : chaque pixel de la texture a une epaisseur (1/16 de bloc)."""
    arr = TILES[tile]
    idx = TILE_INDEX[tile]
    col, row = idx % 16, idx // 16
    solid = arr[:, :, 3] > 102
    u0, v0, u1, v1 = [float(v) for v in TILE_UV[idx]]
    t = 1.0 / 32.0
    out = []

    def Q(pts, shade, uvs):
        out.append([(p[0], p[1], p[2], uv[0], uv[1], shade, shade, shade) for p, uv in zip(pts, uvs)])
    Q([(-.5, -.5, t), (.5, -.5, t), (.5, .5, t), (-.5, .5, t)], 1.0, [(u0, v1), (u1, v1), (u1, v0), (u0, v0)])
    Q([(.5, -.5, -t), (-.5, -.5, -t), (-.5, .5, -t), (.5, .5, -t)], 0.8, [(u0, v1), (u1, v1), (u1, v0), (u0, v0)])
    for py in range(16):
        for px in range(16):
            if not solid[py, px]:
                continue
            uc, vc = (col * 16 + px + 0.5) / 256.0, (row * 16 + py + 0.5) / 256.0
            uv = [(uc, vc)] * 4
            x0 = -0.5 + px / 16.0
            x1 = x0 + 1 / 16.0
            y1 = 0.5 - py / 16.0
            y0 = y1 - 1 / 16.0
            if px == 0 or not solid[py, px - 1]:
                Q([(x0, y0, -t), (x0, y0, t), (x0, y1, t), (x0, y1, -t)], 0.7, uv)
            if px == 15 or not solid[py, px + 1]:
                Q([(x1, y0, t), (x1, y0, -t), (x1, y1, -t), (x1, y1, t)], 0.7, uv)
            if py == 0 or not solid[py - 1, px]:
                Q([(x0, y1, t), (x1, y1, t), (x1, y1, -t), (x0, y1, -t)], 0.95, uv)
            if py == 15 or not solid[py + 1, px]:
                Q([(x0, y0, -t), (x1, y0, -t), (x1, y0, t), (x0, y0, t)], 0.6, uv)
    return out


def box_quads(tile_of_face, sx, sy, sz):
    """Boite centree. tile_of_face(f) -> indice de tuile pour la face f (ordre de _FACES)."""
    out = []
    for f, (dx, dy, dz, corners, shade) in enumerate(_FACES):
        u0, v0, u1, v1 = [float(v) for v in TILE_UV[tile_of_face(f)]]
        out.append([((cx - .5) * sx, (cy - .5) * sy, (cz - .5) * sz, u0 + (u1 - u0) * uf, v0 + (v1 - v0) * vf,
                     shade, shade, shade) for (cx, cy, cz), (uf, vf) in zip(corners, _UVF)])
    return out


def hand_quads(item):
    if item in BLOCK_TILES and item not in ITEM_TILES:
        return box_quads(lambda f: int(FACE_TILE[item][f]), 1.0, 1.0, 1.0)
    if item in ITEM_TILES:
        return sprite_quads(ITEM_TILES[item])
    return box_quads(lambda f: TILE_INDEX["skin"], 0.32, 0.32, 1.25)          # bras


def hand_kind(item):
    return "block" if (item in BLOCK_TILES and item not in ITEM_TILES) else ("item" if item in ITEM_TILES else "arm")


def hand_ops(kind, sw, equip, bobx, boby):
    """Suite de transformations (comme dans Minecraft) : ('t',x,y,z) ('r',angle,x,y,z) ('s',k)."""
    a = math.sin(sw * sw * math.pi)
    b = math.sin(math.sqrt(sw) * math.pi)
    c = math.sin(math.sqrt(sw) * math.pi * 2.0)
    if kind == "arm":
        return [("t", -0.3 * b + bobx, 0.4 * c + boby, -0.4 * a),
                ("t", 0.68, -0.55, -1.0), ("t", 0, (1 - equip) * -0.6, 0),
                ("r", b * 40, 0, 1, 0), ("r", a * -20, 0, 0, 1),
                ("t", -0.1, 0.1, 0.0), ("r", -25, 0, 1, 0), ("r", 12, 1, 0, 0)]
    ops = [("t", -b * 0.4 + bobx, c * 0.2 + boby, -a * 0.2),
           ("t", 0.56, -0.52, -0.72), ("t", 0, (1 - equip) * -0.6, 0),
           ("r", 45, 0, 1, 0), ("r", a * -20, 0, 1, 0), ("r", b * -20, 0, 0, 1), ("r", b * -80, 1, 0, 0),
           ("s", 0.4)]
    if kind == "item":
        ops += [("t", 0, 0.4, 0.125), ("r", -135, 0, 1, 0), ("r", 25, 0, 0, 1), ("s", 2.2)]
    else:
        ops += [("t", -0.3, 0.55, 0.1), ("r", -20, 0, 1, 0), ("r", 15, 1, 0, 0)]
    return ops

_BOX_EDGES = [((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (1, 1, 0)), ((0, 0, 1), (1, 0, 1)), ((0, 1, 1), (1, 1, 1)),
              ((0, 0, 0), (0, 1, 0)), ((1, 0, 0), (1, 1, 0)), ((0, 0, 1), (0, 1, 1)), ((1, 0, 1), (1, 1, 1)),
              ((0, 0, 0), (0, 0, 1)), ((1, 0, 0), (1, 0, 1)), ((0, 1, 0), (0, 1, 1)), ((1, 1, 0), (1, 1, 1))]


class Renderer:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.atlas_tex = self._make_tex(ATLAS.tobytes(), 256, 256)
        self.gui_tex = self._make_tex(bytes(GUI_W * GUI_H * 4), GUI_W, GUI_H)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glFogi(gl.GL_FOG_MODE, gl.GL_LINEAR)
        self.models = {}
        self.item_lists = {}
        self.hand_lists = {}
        self._build_models()
        rs = np.random.RandomState(5)
        v = rs.randn(160, 3)
        v[:, 1] = np.abs(v[:, 1]) * 0.9 + 0.05
        self.stars = (v / np.linalg.norm(v, axis=1)[:, None] * 90.0).tolist()

    # ---------- utilitaires GL ----------
    def _make_tex(self, data, w, h):
        t = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, t)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        return t

    def reload_atlas(self):
        """A appeler quand les textures changent (mods) : renvoie l'atlas a la carte graphique."""
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.atlas_tex)
        gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, 256, 256, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, ATLAS.tobytes())
        for d in (self.item_lists, self.hand_lists, getattr(self, "_boat_lists", {})):
            for lid in d.values():
                gl.glDeleteLists(lid, 1)
            d.clear()

    def _vbo(self, arr):
        arr = np.ascontiguousarray(arr, np.float32)
        b = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, b)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, arr.nbytes, arr, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        return b

    def free_chunk(self, ch):
        if ch.vbo_o:
            gl.glDeleteBuffers(1, [ch.vbo_o])
        if ch.vbo_w:
            gl.glDeleteBuffers(1, [ch.vbo_w])
        ch.vbo_o = ch.vbo_w = 0
        ch.n_o = ch.n_w = 0
        ch.meshed = False

    def upload_chunk(self, ch, vo, vw):
        self.free_chunk(ch)
        if len(vo):
            ch.vbo_o, ch.n_o = self._vbo(vo), len(vo)
        if len(vw):
            ch.vbo_w, ch.n_w = self._vbo(vw), len(vw)
        ch.meshed = True
        ch.need_mesh = False

    def _draw_vbo(self, vbo, n):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glVertexPointer(3, gl.GL_FLOAT, 32, ctypes.c_void_p(0))
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 32, ctypes.c_void_p(12))
        gl.glColorPointer(3, gl.GL_FLOAT, 32, ctypes.c_void_p(20))
        gl.glDrawArrays(gl.GL_QUADS, 0, n)

    # ---------- modeles ----------
    def _box_list(self, mn, sz, pivot, tile, front, mode):
        lid = gl.glGenLists(1)
        gl.glNewList(lid, gl.GL_COMPILE)
        gl.glBegin(gl.GL_QUADS)
        x0, y0, z0 = mn[0] - pivot[0], mn[1] - pivot[1], mn[2] - pivot[2]
        x1, y1, z1 = x0 + sz[0], y0 + sz[1], z0 + sz[2]
        for f, (dx, dy, dz, corners, shade) in enumerate(_FACES):
            tname = front if (f == 4 and front) else tile
            u0, v0, u1, v1 = TILE_UV[TILE_INDEX[tname]]
            for (cx, cy, cz), (uf, vf) in zip(corners, _UVF):
                if mode == 0:
                    gl.glColor3f(shade, shade, shade)
                elif mode == 1:
                    gl.glColor4f(1.0, 0.1, 0.1, 0.45)
                else:
                    gl.glColor4f(1.0, 1.0, 1.0, 0.65)
                gl.glTexCoord2f(float(u0 + (u1 - u0) * uf), float(v0 + (v1 - v0) * vf))
                gl.glVertex3f(x1 if cx else x0, y1 if cy else y0, z1 if cz else z0)
        gl.glEnd()
        gl.glEndList()
        return lid

    def _build_models(self):
        for kind, M in MODELS.items():
            parts = []
            for (tile, front, mn, sz, pivot, anim) in M["parts"]:
                if pivot is None:
                    if anim == "none":
                        pivot = (mn[0] + sz[0] / 2.0, mn[1] + sz[1] / 2.0, mn[2] + sz[2] / 2.0)
                    else:
                        pivot = (mn[0] + sz[0] / 2.0, mn[1] + sz[1], mn[2] + sz[2] / 2.0)
                lists = [self._box_list(mn, sz, pivot, tile, front, m) for m in (0, 1, 2)]
                parts.append((lists, pivot, anim))
            self.models[kind] = (M["scale"] / 16.0, parts)

    def _hand_list(self, item):
        key = item if hand_kind(item) != "arm" else 0
        if key in self.hand_lists:
            return self.hand_lists[key]
        lid = gl.glGenLists(1)
        gl.glNewList(lid, gl.GL_COMPILE)
        gl.glBegin(gl.GL_QUADS)
        for q in hand_quads(item):
            for (x, y, z, u, v, r, g, b) in q:
                gl.glColor3f(r, g, b)
                gl.glTexCoord2f(u, v)
                gl.glVertex3f(x, y, z)
        gl.glEnd()
        gl.glEndList()
        self.hand_lists[key] = lid
        return lid

    def draw_hand(self, S):
        p = S.player
        if p.dead:
            return
        held = p.held()
        kind = hand_kind(held)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glEnable(gl.GL_ALPHA_TEST)
        gl.glDisable(gl.GL_BLEND)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.atlas_tex)
        near = 0.05
        top = near * math.tan(math.radians(70.0) / 2.0)
        right = top * self.w / float(self.h)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glFrustum(-right, right, -top, top, near, 20.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        wd = p.walk_dist * math.pi
        bobx = math.sin(wd) * 0.03 * p.bob_amt
        boby = -abs(math.cos(wd)) * 0.04 * p.bob_amt
        for op in hand_ops(kind, min(1.0, S.swing), S.equip, bobx, boby):
            if op[0] == "t":
                gl.glTranslatef(op[1], op[2], op[3])
            elif op[0] == "r":
                gl.glRotatef(op[1], op[2], op[3], op[4])
            else:
                gl.glScalef(op[1], op[1], op[1])
        gl.glColor4f(1, 1, 1, 1)
        gl.glCallList(self._hand_list(held))
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def _item_list(self, item):
        if item in self.item_lists:
            return self.item_lists[item]
        lid = gl.glGenLists(1)
        gl.glNewList(lid, gl.GL_COMPILE)
        gl.glBegin(gl.GL_QUADS)
        if item in BLOCK_TILES and item not in ITEM_TILES:
            r = 0.13
            for f, (dx, dy, dz, corners, shade) in enumerate(_FACES):
                u0, v0, u1, v1 = TILE_UV[FACE_TILE[item][f]]
                for (cx, cy, cz), (uf, vf) in zip(corners, _UVF):
                    gl.glColor3f(shade, shade, shade)
                    gl.glTexCoord2f(float(u0 + (u1 - u0) * uf), float(v0 + (v1 - v0) * vf))
                    gl.glVertex3f((cx * 2 - 1) * r, (cy * 2 - 1) * r, (cz * 2 - 1) * r)
        else:
            t = ITEM_TILES.get(item, "i_stick")
            u0, v0, u1, v1 = TILE_UV[TILE_INDEX[t]]
            r = 0.17
            for axis in (0, 1):
                for (px, py, uu, vv) in ((-r, -r, u0, v1), (r, -r, u1, v1), (r, r, u1, v0), (-r, r, u0, v0)):
                    gl.glColor3f(1, 1, 1)
                    gl.glTexCoord2f(float(uu), float(vv))
                    if axis == 0:
                        gl.glVertex3f(px, py, 0)
                    else:
                        gl.glVertex3f(0, py, px)
        gl.glEnd()
        gl.glEndList()
        self.item_lists[item] = lid
        return lid

    # ---------- dessin de la scene ----------
    def begin_3d(self):
        gl.glViewport(0, 0, self.w, self.h)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthMask(True)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glEnable(gl.GL_ALPHA_TEST)
        gl.glAlphaFunc(gl.GL_GREATER, 0.4)
        gl.glDisable(gl.GL_BLEND)
        gl.glColor4f(1, 1, 1, 1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.atlas_tex)

    def clear_2d(self, color=(0.0, 0.0, 0.0)):
        gl.glViewport(0, 0, self.w, self.h)
        gl.glClearColor(color[0], color[1], color[2], 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    def render_world(self, S):
        p = S.player
        sc = sky_color(S.time)
        under = p.head_water
        fogc = (0.04, 0.12, 0.30) if under else tuple(sc)
        gl.glClearColor(fogc[0], fogc[1], fogc[2], 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.begin_3d()
        near, far = 0.06, 420.0
        top = near * math.tan(math.radians(S.settings["fov"]) / 2.0)
        right = top * self.w / float(self.h)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glFrustum(-right, right, -top, top, near, far)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        gl.glRotatef(-p.pitch, 1, 0, 0)
        gl.glRotatef(p.yaw, 0, 1, 0)
        if not under:
            self._draw_sky(S)
        ex, ey, ez = p.eye_pos()
        gl.glTranslatef(-ex, -ey, -ez)
        gl.glEnable(gl.GL_FOG)
        gl.glFogfv(gl.GL_FOG_COLOR, (fogc[0], fogc[1], fogc[2], 1.0))
        dist = S.settings["render"] * CHUNK
        if under:
            gl.glFogf(gl.GL_FOG_START, 1.0)
            gl.glFogf(gl.GL_FOG_END, 20.0)
        else:
            gl.glFogf(gl.GL_FOG_START, dist * 0.55)
            gl.glFogf(gl.GL_FOG_END, dist * 0.97)
        vis = self._visible_chunks(S, ex, ez)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        for ch in vis:
            if ch.n_o:
                self._draw_vbo(ch.vbo_o, ch.n_o)
        gl.glDisableClientState(gl.GL_COLOR_ARRAY)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glColor4f(1, 1, 1, 1)
        self._draw_entities(S, ex, ey, ez)
        if S.target and not S.ui_open:
            self._draw_target(S)
        gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        for ch in vis:
            if ch.n_w:
                self._draw_vbo(ch.vbo_w, ch.n_w)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glDisableClientState(gl.GL_COLOR_ARRAY)
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisable(gl.GL_FOG)
        self.draw_hand(S)
        # filtres d'ecran : nuit, sous l'eau, degats
        ang, elev, f = sky_state(S.time)
        night = (1.0 - f) * 0.60
        if night > 0.02:
            self._overlay(0.02, 0.03, 0.12, night)
        if under:
            self._overlay(0.1, 0.25, 0.7, 0.30)
        if p.hurt > 0:
            self._overlay(0.9, 0.0, 0.0, min(0.45, p.hurt * 0.9))

    def _overlay(self, r, g, b, a):
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_ALPHA_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, 1, 1, 0, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glColor4f(r, g, b, a)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex2f(0, 0)
        gl.glVertex2f(1, 0)
        gl.glVertex2f(1, 1)
        gl.glVertex2f(0, 1)
        gl.glEnd()
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_ALPHA_TEST)
        gl.glColor4f(1, 1, 1, 1)

    def _draw_sky(self, S):
        ang, elev, f = sky_state(S.time)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDepthMask(False)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_ALPHA_TEST)
        night = 1.0 - f
        if night > 0.05:
            gl.glDisable(gl.GL_TEXTURE_2D)
            gl.glPushMatrix()
            gl.glRotatef(math.degrees(ang), 0, 0, 1)
            gl.glPointSize(2.0)
            gl.glColor4f(1, 1, 1, min(1.0, night * 1.3))
            gl.glBegin(gl.GL_POINTS)
            for (sx, sy, sz) in self.stars:
                gl.glVertex3f(sx, sy, sz)
            gl.glEnd()
            gl.glPopMatrix()
            gl.glEnable(gl.GL_TEXTURE_2D)
        d = (math.cos(ang), math.sin(ang), 0.15)
        ln = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
        d = (d[0] / ln, d[1] / ln, d[2] / ln)
        rx, ry, rz = d[2], 0.0, -d[0]            # d x (0,1,0)
        rl = math.sqrt(rx * rx + rz * rz) or 1.0
        rx, rz = rx / rl, rz / rl
        ux, uy, uz = d[1] * rz - d[2] * ry, d[2] * rx - d[0] * rz, d[0] * ry - d[1] * rx
        for tile, sgn, size in (("sun", 1.0, 14.0), ("moon", -1.0, 10.0)):
            u0, v0, u1, v1 = TILE_UV[TILE_INDEX[tile]]
            cx, cy, cz = d[0] * 100 * sgn, d[1] * 100 * sgn, d[2] * 100 * sgn
            gl.glColor4f(1, 1, 1, 1)
            gl.glBegin(gl.GL_QUADS)
            for (a, b, uu, vv) in ((-1, -1, u0, v1), (1, -1, u1, v1), (1, 1, u1, v0), (-1, 1, u0, v0)):
                gl.glTexCoord2f(float(uu), float(vv))
                gl.glVertex3f(cx + (rx * a + ux * b) * size, cy + (ry * a + uy * b) * size,
                              cz + (rz * a + uz * b) * size)
            gl.glEnd()
        gl.glDisable(gl.GL_BLEND)
        gl.glEnable(gl.GL_ALPHA_TEST)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthMask(True)

    def _visible_chunks(self, S, ex, ez):
        out = []
        R = S.settings["render"] * CHUNK + 24
        R2 = R * R
        yr = math.radians(S.player.yaw)
        fx, fz = math.sin(yr), -math.cos(yr)
        for ch in S.world.chunks.values():
            if not ch.meshed or (not ch.n_o and not ch.n_w):
                continue
            rx, rz = ch.cx * CHUNK + 8 - ex, ch.cz * CHUNK + 8 - ez
            d2 = rx * rx + rz * rz
            if d2 > R2:
                continue
            if d2 > 1600.0:
                d = math.sqrt(d2)
                if (rx * fx + rz * fz) / d < 0.20 - 12.0 / d:
                    continue
            out.append(ch)
        return out

    def _draw_entities(self, S, ex, ey, ez):
        lim = 56.0 * 56.0
        for m in S.mobs:
            if (m.x - ex) ** 2 + (m.z - ez) ** 2 > lim:
                continue
            scale, parts = self.models[m.kind]
            gl.glPushMatrix()
            gl.glTranslatef(m.x, m.y, m.z)
            gl.glRotatef(math.degrees(m.yaw), 0, 1, 0)
            if m.hp <= 0:
                gl.glRotatef(80, 0, 0, 1)
            gl.glScalef(scale, scale, scale)
            amp = min(1.0, m.speed_now / 1.2)
            ang = math.sin(m.walk * 2.0) * 45.0 * amp
            flash = 0
            if m.hurt > 0:
                flash = 1
            if m.kind == "creeper" and m.fuse >= 0 and int(m.fuse * 8) % 2 == 0:
                flash = 2
            for (lists, pv, anim) in parts:
                gl.glPushMatrix()
                gl.glTranslatef(pv[0], pv[1], pv[2])
                if anim == "A":
                    gl.glRotatef(ang, 1, 0, 0)
                elif anim == "B":
                    gl.glRotatef(-ang, 1, 0, 0)
                elif anim == "F":
                    base = -88.0 if m.kind == "zombie" else -70.0
                    gl.glRotatef(base + math.sin(m.age * 2.0) * 4.0, 1, 0, 0)
                gl.glCallList(lists[0])
                if flash:
                    gl.glDisable(gl.GL_TEXTURE_2D)
                    gl.glEnable(gl.GL_BLEND)
                    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
                    gl.glCallList(lists[flash])
                    gl.glDisable(gl.GL_BLEND)
                    gl.glEnable(gl.GL_TEXTURE_2D)
                gl.glPopMatrix()
            gl.glPopMatrix()
        for d in S.drops:
            if (d.x - ex) ** 2 + (d.z - ez) ** 2 > 40.0 * 40.0:
                continue
            gl.glPushMatrix()
            gl.glTranslatef(d.x, d.y + 0.17 + 0.05 * math.sin(d.age * 3.0), d.z)
            gl.glRotatef(math.degrees(d.spin), 0, 1, 0)
            gl.glCallList(self._item_list(d.item))
            gl.glPopMatrix()
        if S.boats:                                       # les bateaux (listes d'affichage)
            gl.glEnable(gl.GL_TEXTURE_2D)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.atlas_tex)
            for b in S.boats:
                if (b.x - ex) ** 2 + (b.z - ez) ** 2 > 150.0 * 150.0:
                    continue
                bob = 0.02 * math.sin(S.time * 1.7 + b.phase)
                gl.glPushMatrix()
                gl.glTranslatef(b.x, b.y + bob, b.z)
                gl.glRotatef(math.degrees(b.yaw), 0, 1, 0)
                gl.glCallList(_boat_list(self, b.kind))
                gl.glPopMatrix()
            gl.glColor4f(1, 1, 1, 1)
        if S.arrows:
            gl.glDisable(gl.GL_TEXTURE_2D)
            gl.glLineWidth(3.0)
            gl.glColor3f(0.8, 0.8, 0.8)
            gl.glBegin(gl.GL_LINES)
            for a in S.arrows:
                n = math.sqrt(a.vx ** 2 + a.vy ** 2 + a.vz ** 2) or 1.0
                gl.glVertex3f(a.x, a.y, a.z)
                gl.glVertex3f(a.x - a.vx / n * 0.7, a.y - a.vy / n * 0.7, a.z - a.vz / n * 0.7)
            gl.glEnd()
            gl.glColor3f(1, 1, 1)
            gl.glEnable(gl.GL_TEXTURE_2D)

    def _draw_target(self, S):
        bx, by, bz = S.target
        e = 0.003
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glLineWidth(2.0)
        gl.glColor3f(0.0, 0.0, 0.0)
        gl.glBegin(gl.GL_LINES)
        for (a, b) in _BOX_EDGES:
            gl.glVertex3f(bx - e + a[0] * (1 + 2 * e), by - e + a[1] * (1 + 2 * e), bz - e + a[2] * (1 + 2 * e))
            gl.glVertex3f(bx - e + b[0] * (1 + 2 * e), by - e + b[1] * (1 + 2 * e), bz - e + b[2] * (1 + 2 * e))
        gl.glEnd()
        gl.glColor3f(1, 1, 1)
        gl.glEnable(gl.GL_TEXTURE_2D)
        if S.break_progress > 0.02:
            stage = min(9, int(S.break_progress * 10))
            u0, v0, u1, v1 = TILE_UV[TILE_INDEX["crack%d" % stage]]
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)
            gl.glPolygonOffset(-2.0, -2.0)
            gl.glBegin(gl.GL_QUADS)
            for (dx, dy, dz, corners, shade) in _FACES:
                for (cx, cy, cz), (uf, vf) in zip(corners, _UVF):
                    gl.glTexCoord2f(float(u0 + (u1 - u0) * uf), float(v0 + (v1 - v0) * vf))
                    gl.glVertex3f(bx - e + cx * (1 + 2 * e), by - e + cy * (1 + 2 * e), bz - e + cz * (1 + 2 * e))
            gl.glEnd()
            gl.glDisable(gl.GL_POLYGON_OFFSET_FILL)
            gl.glDisable(gl.GL_BLEND)

    # ---------- interface 2D ----------
    def draw_gui(self, surf):
        data = _img_bytes(surf, "RGBA", False)
        gl.glDisable(gl.GL_FOG)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_ALPHA_TEST)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.gui_tex)
        gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, GUI_W, GUI_H, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, 1, 1, 0, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glColor4f(1, 1, 1, 1)
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 0)
        gl.glVertex2f(0, 0)
        gl.glTexCoord2f(1, 0)
        gl.glVertex2f(1, 0)
        gl.glTexCoord2f(1, 1)
        gl.glVertex2f(1, 1)
        gl.glTexCoord2f(0, 1)
        gl.glVertex2f(0, 1)
        gl.glEnd()
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glDisable(gl.GL_BLEND)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.atlas_tex)


# ============================================================================
# INTERFACE 2D (menus, barre rapide, inventaire) dessinee avec pygame
# ============================================================================
FONTS = {}
_ICONS = {}
_HEARTS = {}


_FONT_SIZES = {"s": 20, "m": 26, "l": 40, "xl": 100}
_SAMPLES = {"ru": "Привет", "th": "สวัสดี"}
_FONT_PREFS = ["notosansthai", "notosansthaiui", "loma", "garuda", "norasi", "waree", "umpush", "kinnari",
               "laksaman", "sawasdee", "tlwgtypo", "purisa", "thsarabunnew", "dejavusans", "liberationsans",
               "freesans", "notosans", "ubuntu", "arial", "verdana"]


def _supports(font, sample):
    try:
        m = font.metrics(sample)
    except Exception:
        return True
    return bool(m) and all(g is not None for g in m)


def find_font_path(lang):
    """None = la police par defaut de pygame suffit. Sinon chemin d'une police systeme qui a les glyphes."""
    sample = _SAMPLES.get(lang, "éèçñßàù")
    if _supports(pygame.font.Font(None, 20), sample):
        return None
    try:
        names = pygame.font.get_fonts()
    except Exception:
        return None
    cands = [n for n in _FONT_PREFS if n in names] + [n for n in names if "thai" in n and n not in _FONT_PREFS]
    for n in cands:
        p = pygame.font.match_font(n)
        if p:
            try:
                if _supports(pygame.font.Font(p, 20), sample):
                    return p
            except Exception:
                pass
    return None


def init_fonts(lang=None):
    """(Re)cree les polices : certaines langues (thai, russe) ont besoin d'une police systeme."""
    path = find_font_path(lang or _lang[0])
    k = 0.85 if path else 1.0
    for name, size in _FONT_SIZES.items():
        FONTS[name] = pygame.font.Font(path, int(size * k))
    FONTS["title"] = pygame.font.Font(None, 120)
    _ICONS.clear()


_LANG_FONTS = {}


def lang_font(code, size="m"):
    """Police qui sait afficher le nom d'une langue (pour le menu des langues)."""
    k = (code, size)
    if k not in _LANG_FONTS:
        path = find_font_path(code)
        _LANG_FONTS[k] = pygame.font.Font(path, int(_FONT_SIZES[size] * (0.85 if path else 1.0)))
    return _LANG_FONTS[k]


def clear_icon_cache():
    _ICONS.clear()


def inside(r, p):
    return r[0] <= p[0] < r[0] + r[2] and r[1] <= p[1] < r[1] + r[3]


def draw_text(surf, s, size, color, pos, anchor="l", shadow=True):
    f = FONTS[size]
    img = f.render(s, True, color)
    w, h = img.get_width(), img.get_height()
    x, y = pos
    if anchor == "c":
        x -= w // 2
    elif anchor == "r":
        x -= w
    if shadow:
        sh = f.render(s, True, (40, 40, 40))
        surf.blit(sh, (x + 2, y + 2))
    surf.blit(img, (x, y))
    return w


def get_icon(item, size):
    k = (item, size)
    if k not in _ICONS:
        arr = icon_array(item)
        h, w = arr.shape[0], arr.shape[1]
        s = pygame.image.frombuffer(arr.tobytes(), (w, h), "RGBA")
        _ICONS[k] = pygame.transform.scale(s, (size, size))
    return _ICONS[k]


_HEART = ["  XX   XX  ", " XXXX XXXX ", "XXXXXXXXXXX", "XXXXXXXXXXX", " XXXXXXXXX ", "  XXXXXXX  ",
          "   XXXXX   ", "    XXX    ", "     X     "]


def get_heart(kind):
    """kind : 2 = plein, 1 = moitie, 0 = vide"""
    if kind in _HEARTS:
        return _HEARTS[kind]
    sc = 2
    w, h = len(_HEART[0]) * sc + 2, len(_HEART) * sc + 2
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cells = [(x, y) for y, row in enumerate(_HEART) for x, c in enumerate(row) if c == "X"]
    for (x, y) in cells:
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pygame.draw.rect(s, (30, 0, 0), (1 + x * sc + ox, 1 + y * sc + oy, sc, sc))
    for (x, y) in cells:
        col = (214, 30, 30)
        if kind == 0 or (kind == 1 and x > 5):
            col = (70, 48, 48)
        elif (x, y) in ((1, 2), (2, 2), (2, 3)):
            col = (255, 140, 140)
        pygame.draw.rect(s, col, (1 + x * sc, 1 + y * sc, sc, sc))
    _HEARTS[kind] = s
    return s


_ARMOR_ICON = ["XXXXXXXXXXX", "XXXXXXXXXXX", "XXXXXXXXXXX", "XXXXXXXXXXX", " XXXXXXXXX ", " XXXXXXXXX ",
               "  XXXXXXX  ", "   XXXXX   ", "    XXX    "]
_ARMOR_SURFS = {}


def get_armor_icon(kind):
    if kind in _ARMOR_SURFS:
        return _ARMOR_SURFS[kind]
    sc = 2
    s = pygame.Surface((len(_ARMOR_ICON[0]) * sc + 2, len(_ARMOR_ICON) * sc + 2), pygame.SRCALPHA)
    cells = [(x, y) for y, row in enumerate(_ARMOR_ICON) for x, c in enumerate(row) if c == "X"]
    for (x, y) in cells:
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pygame.draw.rect(s, (30, 30, 36), (1 + x * sc + ox, 1 + y * sc + oy, sc, sc))
    for (x, y) in cells:
        col = (200, 204, 214)
        if kind == 0 or (kind == 1 and x > 5):
            col = (70, 72, 82)
        elif y < 2 or x < 2:
            col = (240, 244, 255)
        pygame.draw.rect(s, col, (1 + x * sc, 1 + y * sc, sc, sc))
    _ARMOR_SURFS[kind] = s
    return s


def draw_panel(surf, r):
    x, y, w, h = r
    pygame.draw.rect(surf, (0, 0, 0), (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(surf, (198, 198, 198), r)
    pygame.draw.rect(surf, (255, 255, 255), (x, y, w, 3))
    pygame.draw.rect(surf, (255, 255, 255), (x, y, 3, h))
    pygame.draw.rect(surf, (85, 85, 85), (x, y + h - 3, w, 3))
    pygame.draw.rect(surf, (85, 85, 85), (x + w - 3, y, 3, h))


def draw_slot(surf, r, hover=False):
    x, y, w, h = r
    pygame.draw.rect(surf, (139, 139, 139), r)
    pygame.draw.rect(surf, (55, 55, 55), (x, y, w, 2))
    pygame.draw.rect(surf, (55, 55, 55), (x, y, 2, h))
    pygame.draw.rect(surf, (255, 255, 255), (x, y + h - 2, w, 2))
    pygame.draw.rect(surf, (255, 255, 255), (x + w - 2, y, 2, h))
    if hover:
        pygame.draw.rect(surf, (178, 178, 178), (x + 2, y + 2, w - 4, h - 4))


def draw_stack(surf, stack, x, y, size=32):
    if not stack:
        return
    surf.blit(get_icon(stack[0], size), (x, y))
    if stack[1] > 1:
        draw_text(surf, str(stack[1]), "s", (255, 255, 255), (x + size + 2, y + size - 12), "r")


def draw_button(surf, r, label, hover=False, enabled=True, size="m"):
    x, y, w, h = r
    if not enabled:
        base, top, bot, tc = (72, 72, 72), (95, 95, 95), (50, 50, 50), (150, 150, 150)
    elif hover:
        base, top, bot, tc = (118, 130, 196), (150, 162, 226), (80, 90, 150), (255, 255, 160)
    else:
        base, top, bot, tc = (112, 112, 112), (160, 160, 160), (70, 70, 70), (235, 235, 235)
    pygame.draw.rect(surf, (0, 0, 0), r)
    pygame.draw.rect(surf, base, (x + 2, y + 2, w - 4, h - 4))
    pygame.draw.rect(surf, top, (x + 2, y + 2, w - 4, 3))
    pygame.draw.rect(surf, top, (x + 2, y + 2, 3, h - 4))
    pygame.draw.rect(surf, bot, (x + 2, y + h - 5, w - 4, 3))
    pygame.draw.rect(surf, bot, (x + w - 5, y + 2, 3, h - 4))
    f = FONTS[size]
    th = f.get_height()
    draw_text(surf, label, size, tc, (x + w // 2, y + (h - th) // 2 + 1), "c")


def make_dirt_bg():
    s = pygame.Surface((GUI_W, GUI_H))
    arr = TILES["dirt"]
    t = pygame.image.frombuffer(arr.tobytes(), (16, 16), "RGBA")
    t = pygame.transform.scale(t, (64, 64)).convert()
    dark = pygame.Surface((64, 64))
    dark.fill((95, 95, 95))
    t.blit(dark, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    for y in range(0, GUI_H, 64):
        for x in range(0, GUI_W, 64):
            s.blit(t, (x, y))
    return s


class TextInput:
    def __init__(self, text="", maxlen=24, numeric=False):
        self.text, self.maxlen, self.numeric = text, maxlen, numeric

    def key(self, ev):
        if ev.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif ev.unicode and ev.unicode.isprintable() and len(self.text) < self.maxlen:
            if self.numeric and not (ev.unicode.isdigit() or ev.unicode == "-"):
                return
            if ev.unicode in '\\/:*?"<>|':
                return
            self.text += ev.unicode

    def draw(self, surf, r, active):
        x, y, w, h = r
        pygame.draw.rect(surf, (200, 200, 200) if active else (120, 120, 120), (x - 2, y - 2, w + 4, h + 4))
        pygame.draw.rect(surf, (0, 0, 0), r)
        cur = "_" if active and int(time.time() * 2) % 2 == 0 else ""
        draw_text(surf, self.text + cur, "m", (255, 255, 255), (x + 8, y + (h - 18) // 2), "l", False)


# ---------------------------------------------------------------------------
# HUD (barre rapide, coeurs, bulles, texte de debug)
# ---------------------------------------------------------------------------
def draw_hud(surf, S, fps):
    p = S.player
    cx, cy = GUI_W // 2, GUI_H // 2
    for (rx, ry, rw, rh) in ((cx - 9, cy - 1, 18, 2), (cx - 1, cy - 9, 2, 18)):
        pygame.draw.rect(surf, (20, 20, 20), (rx - 1, ry - 1, rw + 2, rh + 2))
        pygame.draw.rect(surf, (235, 235, 235), (rx, ry, rw, rh))
    hx = (GUI_W - 9 * 40) // 2
    hy = GUI_H - 46
    pygame.draw.rect(surf, (0, 0, 0, 150), (hx - 3, hy - 3, 9 * 40 + 6, 46))
    for i in range(9):
        r = (hx + i * 40, hy, 40, 40)
        pygame.draw.rect(surf, (90, 90, 90, 140), (r[0] + 1, r[1] + 1, 38, 38))
        if i == p.sel:
            pygame.draw.rect(surf, (255, 255, 255), (r[0] - 2, r[1] - 2, 44, 44), 3)
        draw_stack(surf, p.inv[i], r[0] + 4, r[1] + 4)
    # coeurs
    hp = int(math.ceil(p.health))
    for i in range(0 if S.creative else 10):
        v = hp - i * 2
        k = 2 if v >= 2 else (1 if v == 1 else 0)
        off = random.randint(-1, 1) if hp <= 4 and hp > 0 else 0
        surf.blit(get_heart(k), (hx + i * 20, hy - 26 + off))
    # armure
    ap = p.armor_points()
    if ap > 0 and not S.creative:
        for i in range(10):
            v = ap - i * 2
            surf.blit(get_armor_icon(2 if v >= 2 else (1 if v == 1 else 0)), (hx + i * 20, hy - 46))
    # bulles d'air
    if p.air < 14.9 and not S.creative:
        nb = int(math.ceil(max(0.0, p.air) / 1.5))
        for i in range(nb):
            bx, by = hx + 9 * 40 - 10 - i * 18, hy - 18
            pygame.draw.circle(surf, (20, 40, 90), (bx, by), 7)
            pygame.draw.circle(surf, (170, 215, 255), (bx, by), 6)
            pygame.draw.circle(surf, (255, 255, 255), (bx - 2, by - 2), 2)
    held = p.inv[p.sel]
    if S.name_timer > 0 and held:
        draw_text(surf, item_name(held[0]), "m", (255, 255, 255), (GUI_W // 2, hy - 56), "c")
    y = 12
    for (msg, t) in S.messages:
        draw_text(surf, msg, "m", (255, 255, 120), (GUI_W // 2, y), "c")
        y += 24
    cx = GUI_W // 2                                   # informations de pilotage des bateaux
    b = S.driving
    if b is not None:
        line = tr("b_speed") % abs(b.speed)
        if b.spec["engine"]:
            line += "     " + tr("b_power") % int(b.power * 100)
        draw_text(surf, line, "m", (255, 255, 255), (cx, GUI_H - 108), "c")
    elif S.target_boat is not None and not S.ui_open:
        draw_text(surf, tr("b_hint"), "m", (255, 255, 255), (cx, GUI_H // 2 + 40), "c")
    if S.show_debug:
        lines = ["Kurtoscraft  %d FPS" % fps,
                 "XYZ: %.1f / %.1f / %.1f" % (p.x, p.y, p.z),
                 "Chunk: %d %d   (charges: %d)" % (int(p.x) >> 4, int(p.z) >> 4, len(S.world.chunks)),
                 "Mobs: %d   Temps: %d%%" % (len(S.mobs), int((S.time / DAY_LEN) % 1.0 * 100)),
                 "Seed: %s" % S.world.seed]
        for i, l in enumerate(lines):
            draw_text(surf, l, "s", (255, 255, 255), (8, 8 + i * 16))


# ---------------------------------------------------------------------------
# ECRANS A CASES : base commune (inventaire + fabrication, coffre, four)
# ---------------------------------------------------------------------------
def draw_tooltip(surf, lines, mouse):
    w = max(FONTS["m"].size(l)[0] for l in lines) + 14
    h = 10 + 22 * len(lines)
    tx = min(mouse[0] + 14, GUI_W - w - 4)
    ty = max(4, min(mouse[1] - 8, GUI_H - h - 4))
    pygame.draw.rect(surf, (20, 0, 30), (tx, ty, w, h))
    pygame.draw.rect(surf, (80, 30, 160), (tx, ty, w, h), 2)
    for i, l in enumerate(lines):
        draw_text(surf, l, "m", (255, 255, 255) if i == 0 else (180, 180, 190), (tx + 7, ty + 6 + i * 22), "l", False)


class ContainerScreen:
    PW, PH = 352, 332
    INV_Y, HOTBAR_Y, LABEL_Y = 168, 284, 148

    def __init__(self, S, title):
        self.S, self.title = S, title
        self.cursor = None
        self.px = (GUI_W - self.PW) // 2
        self.py = (GUI_H - self.PH) // 2
        self.slots = {}
        inv = S.player.inv
        for i in range(9):
            self.add(("inv", i), (self.px + 16 + i * 36, self.py + self.HOTBAR_Y), inv, i)
        for i in range(9, 36):
            r, c = (i - 9) // 9, (i - 9) % 9
            self.add(("inv", i), (self.px + 16 + c * 36, self.py + self.INV_Y + r * 36), inv, i)

    def in_panel(self, pos):
        return inside((self.px, self.py, self.PW, self.PH), pos)

    def add(self, key, xy, cont, idx, kind="normal", accept=None):
        self.slots[key] = {"r": (xy[0], xy[1], 36, 36), "cont": cont, "i": idx, "kind": kind, "accept": accept}

    def slot_at(self, pos):
        for k, sl in self.slots.items():
            if inside(sl["r"], pos):
                return k
        return None

    def stack(self, key):
        sl = self.slots[key]
        return sl["cont"][sl["i"]]

    # --- a redefinir ---
    def changed(self):
        pass

    def virtual_click(self, key, button, shift):
        return False

    def panel_click(self, pos, button):
        pass

    def scroll_by(self, dy):
        pass

    def draw_extra(self, surf, mouse):
        pass

    def tooltip_for(self, key):
        st = self.stack(key)
        return [item_name(st[0])] if st else None

    # --- logique des clics ---
    def click(self, pos, button, shift=False):
        S = self.S
        key = self.slot_at(pos)
        if key is None:
            if self.in_panel(pos):
                return
            if self.cursor and not self.panel_click(pos, button):
                S.drop_stack(self.cursor[0], self.cursor[1] if button == 1 else 1)
                self.cursor[1] -= self.cursor[1] if button == 1 else 1
                if self.cursor[1] <= 0:
                    self.cursor = None
            elif not self.cursor:
                self.panel_click(pos, button)
            return
        if self.virtual_click(key, button, shift):
            return
        sl = self.slots[key]
        cont, i = sl["cont"], sl["i"]
        s, c, acc = cont[i], self.cursor, sl["accept"]
        if key[0] == "inv" and s and s[0] == SLOT_LOCK:          # case occupee par le paquebot
            return
        if sl["kind"] == "take":
            if s:
                if shift:
                    left = inv_add(S.player.inv, s[0], s[1])
                    cont[i] = [s[0], left] if left else None
                elif c is None:
                    cont[i], self.cursor = None, s
                elif c[0] == s[0] and c[1] + s[1] <= max_stack(c[0]):
                    c[1] += s[1]
                    cont[i] = None
            self.changed()
            return
        if shift:
            self._shift_move(key)
            self.changed()
            return
        if button == 1:
            if c is None:
                cont[i], self.cursor = None, s
            elif s is None:
                if acc and not acc(c[0]):
                    return
                cont[i], self.cursor = c, None
            elif s[0] == c[0]:
                n = min(c[1], max_stack(s[0]) - s[1])
                s[1] += n
                c[1] -= n
                if c[1] <= 0:
                    self.cursor = None
            else:
                if acc and not acc(c[0]):
                    return
                cont[i], self.cursor = c, s
        else:
            if c is None:
                if s:
                    half = (s[1] + 1) // 2
                    self.cursor = [s[0], half]
                    s[1] -= half
                    if s[1] <= 0:
                        cont[i] = None
            else:
                if acc and not acc(c[0]):
                    return
                if s is None:
                    cont[i] = [c[0], 1]
                    c[1] -= 1
                elif s[0] == c[0] and s[1] < max_stack(s[0]):
                    s[1] += 1
                    c[1] -= 1
                elif s[0] != c[0]:
                    cont[i], self.cursor = c, s
                if self.cursor and self.cursor[1] <= 0:
                    self.cursor = None
        self.changed()

    def _shift_move(self, key):
        sl = self.slots[key]
        cont, i = sl["cont"], sl["i"]
        s = cont[i]
        if not s or s[0] == SLOT_LOCK:
            return
        if key[0] == "inv":
            targets = [k for k, v in self.slots.items() if k[0] != "inv" and v["kind"] == "normal"
                       and (v["accept"] is None or v["accept"](s[0]))]
            if not targets:
                targets = [("inv", j) for j in (range(9, 36) if i < 9 else range(0, 9))]
        else:
            targets = [("inv", j) for j in range(36)]
        for empty in (False, True):
            for k in targets:
                t = self.slots[k]
                if t["cont"] is cont and t["i"] == i:
                    continue
                d = t["cont"][t["i"]]
                if not empty and d and d[0] == s[0] and d[1] < max_stack(d[0]):
                    n = min(s[1], max_stack(d[0]) - d[1])
                    d[1] += n
                    s[1] -= n
                elif empty and d is None and s[1] > 0:
                    n = min(s[1], max_stack(s[0]))
                    t["cont"][t["i"]] = [s[0], n]
                    s[1] -= n
                if s[1] <= 0:
                    cont[i] = None
                    return

    def close(self):
        S = self.S
        for cont in self.loose_lists():
            for i, s in enumerate(cont):
                if s:
                    left = inv_add(S.player.inv, s[0], s[1])
                    if left:
                        S.drop_stack(s[0], left)
                    cont[i] = None
        if self.cursor:
            left = inv_add(S.player.inv, self.cursor[0], self.cursor[1])
            if left:
                S.drop_stack(self.cursor[0], left)
            self.cursor = None

    def loose_lists(self):
        return []

    # --- dessin ---
    def draw(self, surf, mouse):
        dim = pygame.Surface((GUI_W, GUI_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        surf.blit(dim, (0, 0))
        draw_panel(surf, (self.px, self.py, self.PW, self.PH))
        draw_text(surf, self.title, "m", (60, 60, 60), (self.px + 16, self.py + 12), "l", False)
        draw_text(surf, tr("inventory"), "m", (60, 60, 60), (self.px + 16, self.py + self.LABEL_Y), "l", False)
        hover = self.slot_at(mouse)
        for key, sl in self.slots.items():
            draw_slot(surf, sl["r"], key == hover)
            draw_stack(surf, sl["cont"][sl["i"]], sl["r"][0] + 2, sl["r"][1] + 2)
        self.draw_extra(surf, mouse)
        if self.cursor:
            draw_stack(surf, self.cursor, mouse[0] - 16, mouse[1] - 16)
        elif hover:
            lines = self.tooltip_for(hover)
            if lines:
                draw_tooltip(surf, lines, mouse)


class InvScreen(ContainerScreen):
    """Inventaire (grille 2x2 + armure) ou etabli (grille 3x3), avec le menu des recettes."""

    def __init__(self, S, n):
        if n == 5:                                          # table de construction navale
            self.PH, self.INV_Y, self.HOTBAR_Y, self.LABEL_Y = 400, 232, 352, 214
        ContainerScreen.__init__(self, S, tr("crafting") if n == 2 else item_name(NAVAL_TABLE if n == 5 else TABLE))
        self.n = n
        self.rows_vis = (self.PH - 54) // 40
        self.grid = [None] * (n * n)
        self._out = [None]
        self.result = None
        px, py = self.px, self.py
        gx, gy, ox, oy = {2: (px + 176, py + 52, px + 288, py + 72), 3: (px + 60, py + 34, px + 248, py + 70),
                          5: (px + 34, py + 34, px + 280, py + 106)}[n]
        for i in range(n * n):
            self.add(("craft", i), (gx + (i % n) * 36, gy + (i // n) * 36), self.grid, i)
        self.add(("out", 0), (ox, oy), self._out, 0, "take")
        self.arrow = (gx + n * 36 + 6, oy + 6)
        if n == 2:
            for i in range(4):
                self.add(("armor", i), (px + 16 + i * 36, py + 36), S.player.armor, i, "normal",
                         lambda it, i=i: ARMOR.get(it, (None,))[0] == i)
        self.rec_rect = (px + self.PW + 14, py, 262, self.PH)
        self.rscroll = 0
        self.recompute()

    def loose_lists(self):
        return [self.grid]

    def recompute(self):
        ids = [s[0] if s else 0 for s in self.grid]
        self.result = (find_boat_recipe(ids) if self.n == 5 else None) or find_recipe(ids, self.n)
        self._out[0] = [self.result[0], self.result[1]] if self.result else None

    def changed(self):
        self.recompute()

    def virtual_click(self, key, button, shift):
        if key == ("out", 0):
            self.take_result(shift)
            return True
        return False

    def take_result(self, shift=False):
        S = self.S
        for _ in range(64 if shift else 1):
            if not self.result:
                break
            item, cnt = self.result
            if item == LINER and sum(1 for s in S.player.inv if s is None) < 6:
                S.msg(tr("b_need6_craft"))
                break
            if shift:
                left = inv_add(S.player.inv, item, cnt)
                if left:
                    S.drop_stack(item, left)
            else:
                c = self.cursor
                if c is not None and (c[0] != item or c[1] + cnt > max_stack(item)):
                    break
                if c is None:
                    self.cursor = [item, cnt]
                else:
                    c[1] += cnt
            for i, s in enumerate(self.grid):
                if s:
                    s[1] -= 1
                    if s[1] <= 0:
                        self.grid[i] = None
            self.recompute()
            if not shift:
                break

    # --- menu des recettes ---
    def recipe_list(self):
        have = {}
        for s in list(self.S.player.inv) + list(self.grid):
            if s:
                have[s[0]] = have.get(s[0], 0) + s[1]
        out = []
        for rec in (RECIPES + BOAT_RECIPES if self.n == 5 else RECIPES):
            pat = rec[0]
            if len(pat) > self.n or len(pat[0]) > self.n:
                continue
            need = {}
            for row in pat:
                for it in row:
                    if it:
                        need[it] = need.get(it, 0) + 1
            out.append((all(have.get(it, 0) >= k for it, k in need.items()), rec, need))
        out.sort(key=lambda t: not t[0])
        return out

    def _cell(self, j):
        r, c = divmod(j, 6)
        return (self.rec_rect[0] + 10 + c * 40, self.rec_rect[1] + 44 + r * 40, 38, 38)

    def scroll_by(self, dy):
        rows = (len(self.recipe_list()) + 5) // 6
        self.rscroll = max(0, min(max(0, rows - self.rows_vis), self.rscroll - dy))

    def panel_click(self, pos, button):
        if not inside(self.rec_rect, pos):
            return False
        lst = self.recipe_list()
        for j in range(self.rows_vis * 6):
            idx = self.rscroll * 6 + j
            if idx < len(lst) and inside(self._cell(j), pos):
                ok, rec, need = lst[idx]
                if ok:
                    self.fill_recipe(rec)
                return True
        return True

    def fill_recipe(self, rec):
        S = self.S
        pat = rec[0]
        for i, s in enumerate(self.grid):                       # on range d'abord ce qui est dans la grille
            if s:
                left = inv_add(S.player.inv, s[0], s[1])
                if left:
                    S.drop_stack(s[0], left)
                self.grid[i] = None
        for r, row in enumerate(pat):
            for c, it in enumerate(row):
                if not it:
                    continue
                for j, s in enumerate(S.player.inv):
                    if s and s[0] == it:
                        s[1] -= 1
                        if s[1] <= 0:
                            S.player.inv[j] = None
                        self.grid[r * self.n + c] = [it, 1]
                        break
        self.recompute()

    def tooltip_for(self, key):
        if key[0] == "armor" and not self.stack(key):
            return [tr("armor")]
        return ContainerScreen.tooltip_for(self, key)

    def draw_extra(self, surf, mouse):
        ax, ay = self.arrow
        pygame.draw.polygon(surf, (90, 90, 90), [(ax, ay + 8), (ax + 16, ay + 8), (ax + 16, ay), (ax + 28, ay + 12),
                                                 (ax + 16, ay + 24), (ax + 16, ay + 16), (ax, ay + 16)])
        if self.n == 2:
            draw_text(surf, tr("armor"), "s", (60, 60, 60), (self.px + 16, self.py + 20), "l", False)
            draw_text(surf, "%d / 20" % self.S.player.armor_points(), "m", (60, 60, 60),
                      (self.px + 16, self.py + 84), "l", False)
        # panneau des recettes
        draw_panel(surf, self.rec_rect)
        draw_text(surf, tr("recipes"), "m", (60, 60, 60), (self.rec_rect[0] + 12, self.rec_rect[1] + 12), "l", False)
        lst = self.recipe_list()
        if not any(t[0] for t in lst):
            draw_text(surf, tr("no_recipes"), "s", (90, 90, 90), (self.rec_rect[0] + 12, self.rec_rect[1] + 300), "l", False)
        hover_tip = None
        for j in range(self.rows_vis * 6):
            idx = self.rscroll * 6 + j
            if idx >= len(lst):
                break
            ok, rec, need = lst[idx]
            r = self._cell(j)
            h = inside(r, mouse)
            draw_slot(surf, r, h and ok)
            draw_stack(surf, [rec[1], rec[2]], r[0] + 3, r[1] + 3)
            if not ok:
                dimv = pygame.Surface((r[2] - 4, r[3] - 4), pygame.SRCALPHA)
                dimv.fill((90, 90, 100, 170))
                surf.blit(dimv, (r[0] + 2, r[1] + 2))
            if h:
                hover_tip = ["%s x%d" % (item_name(rec[1]), rec[2]), tr("needs")] + \
                            ["  %d x %s" % (k, item_name(it)) for it, k in need.items()]
        if hover_tip and not self.cursor:
            draw_tooltip(surf, hover_tip, mouse)


class ChestScreen(ContainerScreen):
    def __init__(self, S, pos):
        ContainerScreen.__init__(self, S, item_name(CHEST))
        self.t = S.world.tile(pos, "chest")
        for i in range(27):
            r, c = divmod(i, 9)
            self.add(("chest", i), (self.px + 16 + c * 36, self.py + 36 + r * 36), self.t["items"], i)


class FurnaceScreen(ContainerScreen):
    def __init__(self, S, pos):
        ContainerScreen.__init__(self, S, item_name(FURNACE))
        self.t = S.world.tile(pos, "furnace")
        it = self.t["items"]
        self.add(("in", 0), (self.px + 112, self.py + 34), it, 0, "normal", lambda x: x in SMELT)
        self.add(("fuel", 0), (self.px + 112, self.py + 106), it, 1, "normal", lambda x: x in FUEL)
        self.add(("fout", 0), (self.px + 232, self.py + 70), it, 2, "take")

    def draw_extra(self, surf, mouse):
        t = self.t
        fx, fy = self.px + 120, self.py + 72
        flame = [(fx + 10, fy), (fx + 18, fy + 12), (fx + 20, fy + 22), (fx + 10, fy + 30), (fx, fy + 22),
                 (fx + 2, fy + 12), (fx + 8, fy + 14)]
        pygame.draw.polygon(surf, (110, 110, 110), flame)
        frac = max(0.0, min(1.0, t["burn"] / max(0.01, t["burn_max"]))) if t["burn"] > 0 else 0.0
        if frac > 0:
            h = int(32 * frac)
            surf.set_clip((fx - 2, fy + 32 - h, 26, h + 2))
            pygame.draw.polygon(surf, (255, 150, 20), flame)
            surf.set_clip(None)
        ax, ay = self.px + 168, self.py + 78
        pygame.draw.rect(surf, (110, 110, 110), (ax, ay, 52, 16))
        pygame.draw.rect(surf, (250, 250, 250), (ax, ay, int(52 * min(1.0, t["cook"] / SMELT_TIME)), 16))


# ---------------------------------------------------------------------------
# MENU D'UN BATEAU : soute (5 / 20 / 50 / 200 cases) + moteur a vapeur (4 cases combustible, 6 seaux d'eau)
# ---------------------------------------------------------------------------
BOAT_KIND_ITEM = {v: k for k, v in BOAT_ITEMS.items()}


class BoatScreen(ContainerScreen):
    PW = 352
    ENG_W, ENG_H = 196, 284
    COLS = 9

    def __init__(self, S, boat):
        self.S, self.boat = S, boat
        self.cursor = None
        self.scroll = 0
        self.title = item_name(BOAT_KIND_ITEM[boat.kind])
        n = len(boat.storage)
        self.rows_total = int(math.ceil(n / float(self.COLS)))
        self.rows_vis = min(6, self.rows_total)
        self.has_engine = bool(boat.spec["engine"])
        self.PH = 34 + self.rows_vis * 36 + 6 + 20 + 108 + 8 + 36 + 14
        total_w = self.PW + ((12 + self.ENG_W) if self.has_engine else 0)
        self.px = (GUI_W - total_w) // 2
        self.py = max(4, (GUI_H - self.PH) // 2)
        self.ex, self.ey = self.px + self.PW + 12, self.py
        self.layout()

    def layout(self):
        px, py = self.px, self.py
        self.slots = {}
        if self.has_engine:                                      # combustible / eau d'abord (Shift-clic)
            ex, ey = self.ex, self.ey
            for i in range(4):
                self.add(("fuel", i), (ex + 14 + (i % 2) * 36, ey + 66 + (i // 2) * 36), self.boat.fuel, i,
                         "normal", lambda it: it in FUEL)
            for i in range(6):
                self.add(("water", i), (ex + 114 + (i % 2) * 36, ey + 66 + (i // 2) * 36), self.boat.water, i,
                         "normal", lambda it: it == WATER_BUCKET)
        first = self.scroll * self.COLS
        n = len(self.boat.storage)
        for k in range(self.rows_vis * self.COLS):
            i = first + k
            if i >= n:
                break
            r, c = divmod(k, self.COLS)
            self.add(("sto", i), (px + 16 + c * 36, py + 34 + r * 36), self.boat.storage, i, "normal",
                     lambda it: it not in BOAT_ITEMS and it != SLOT_LOCK)
        iy = py + 34 + self.rows_vis * 36 + 6 + 20
        inv = self.S.player.inv
        for i in range(9, 36):
            r, c = (i - 9) // 9, (i - 9) % 9
            self.add(("inv", i), (px + 16 + c * 36, iy + r * 36), inv, i)
        for i in range(9):
            self.add(("inv", i), (px + 16 + i * 36, iy + 108 + 8), inv, i)
        self.inv_label_y = iy - 18
        self.btn_up = (px + self.PW - 66, py + 8, 24, 20)
        self.btn_dn = (px + self.PW - 38, py + 8, 24, 20)

    def scroll_by(self, dy):
        mx = max(0, self.rows_total - self.rows_vis)
        self.scroll = max(0, min(mx, self.scroll - int(dy)))
        self.layout()

    def in_panel(self, pos):
        if inside((self.px, self.py, self.PW, self.PH), pos):
            return True
        return self.has_engine and inside((self.ex, self.ey, self.ENG_W, self.ENG_H), pos)

    def click(self, pos, button, shift=False):
        if self.rows_total > self.rows_vis and button == 1:
            if inside(self.btn_up, pos):
                self.scroll_by(1)
                return
            if inside(self.btn_dn, pos):
                self.scroll_by(-1)
                return
        ContainerScreen.click(self, pos, button, shift)

    def _bar(self, surf, x, y, w, ratio, col, label):
        draw_text(surf, label, "s", (60, 60, 60), (x, y - 14), "l", False)
        pygame.draw.rect(surf, (40, 40, 40), (x, y, w, 12))
        pygame.draw.rect(surf, (90, 90, 90), (x + 1, y + 1, w - 2, 10))
        ratio = max(0.0, min(1.0, ratio))
        if ratio > 0:
            pygame.draw.rect(surf, col, (x + 1, y + 1, int((w - 2) * ratio), 10))

    def draw(self, surf, mouse):
        b = self.boat
        dim = pygame.Surface((GUI_W, GUI_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        surf.blit(dim, (0, 0))
        draw_panel(surf, (self.px, self.py, self.PW, self.PH))
        draw_text(surf, "%s  (%d)" % (self.title, len(b.storage)), "m", (60, 60, 60), (self.px + 16, self.py + 12), "l", False)
        draw_text(surf, tr("inventory"), "m", (60, 60, 60), (self.px + 16, self.inv_label_y), "l", False)
        if self.rows_total > self.rows_vis:
            for (r, up) in ((self.btn_up, True), (self.btn_dn, False)):
                draw_button(surf, r, "", inside(r, mouse))
                cx, cy = r[0] + r[2] // 2, r[1] + r[3] // 2
                pts = [(cx - 6, cy + 4), (cx + 6, cy + 4), (cx, cy - 5)] if up else \
                      [(cx - 6, cy - 4), (cx + 6, cy - 4), (cx, cy + 5)]
                pygame.draw.polygon(surf, (255, 255, 255), pts)
        if self.has_engine:
            self._draw_engine(surf)
        hover = self.slot_at(mouse)
        for key, sl in self.slots.items():
            draw_slot(surf, sl["r"], key == hover)
            draw_stack(surf, sl["cont"][sl["i"]], sl["r"][0] + 2, sl["r"][1] + 2)
        if self.cursor:
            draw_stack(surf, self.cursor, mouse[0] - 16, mouse[1] - 16)
        elif hover:
            st = self.stack(hover)
            if st:
                draw_tooltip(surf, [item_name(st[0])], mouse)

    def _draw_engine(self, surf):
        b, ex, ey = self.boat, self.ex, self.ey
        draw_panel(surf, (ex, ey, self.ENG_W, self.ENG_H))
        title = tr("b_engine_room") if b.spec["engine"] == 2 else tr("b_steam_engine")
        draw_text(surf, title, "m", (60, 60, 60), (ex + 14, ey + 12), "l", False)
        draw_text(surf, tr("b_coal_wood"), "s", (60, 60, 60), (ex + 14, ey + 48), "l", False)
        draw_text(surf, tr("b_buckets"), "s", (60, 60, 60), (ex + 114, ey + 48), "l", False)
        fx, fy = ex + 100, ey + 104
        lit = b.fuel_left > 0 and b.water_left > 0
        pygame.draw.polygon(surf, (235, 140, 40) if lit else (120, 120, 120),
                            [(fx, fy + 22), (fx - 8, fy + 8), (fx - 2, fy + 10), (fx, fy - 6), (fx + 3, fy + 8),
                             (fx + 9, fy + 6), (fx + 8, fy + 22)])
        if lit:
            pygame.draw.polygon(surf, (250, 220, 90), [(fx, fy + 22), (fx - 4, fy + 14), (fx, fy + 6), (fx + 4, fy + 14)])
        by = ey + 66 + 3 * 36 + 26
        self._bar(surf, ex + 14, by, self.ENG_W - 28, b.fuel_left / b.fuel_total if b.fuel_total else 0.0,
                  (230, 120, 30), tr("b_fire"))
        self._bar(surf, ex + 14, by + 30, self.ENG_W - 28, b.water_left / b.water_total if b.water_total else 0.0,
                  (60, 120, 220), tr("b_steam"))
        self._bar(surf, ex + 14, by + 60, self.ENG_W - 28, b.power, (235, 235, 235), tr("b_power") % int(b.power * 100))


# ---------------------------------------------------------------------------
# INVENTAIRE CREATIF : tous les blocs et objets (defilement a la molette) + la barre rapide
# ---------------------------------------------------------------------------
class CreativeScreen:
    PW, PH = 352, 332
    COLS, ROWS = 9, 6

    def __init__(self, S):
        self.S = S
        self.cursor = None
        self.px = (GUI_W - self.PW) // 2
        self.py = (GUI_H - self.PH) // 2
        self.items = list(CREATIVE_ITEMS)
        self.scroll = 0

    def _max_scroll(self):
        return max(0, (len(self.items) + self.COLS - 1) // self.COLS - self.ROWS)

    def scroll_by(self, dy):
        self.scroll = max(0, min(self._max_scroll(), self.scroll - dy))

    def _item_rect(self, j):
        r, c = divmod(j, self.COLS)
        return (self.px + 16 + c * 36, self.py + 40 + r * 36, 36, 36)

    def _inv_rect(self, i):
        return (self.px + 16 + i * 36, self.py + 284, 36, 36)

    def slot_at(self, pos):
        for j in range(self.COLS * self.ROWS):
            idx = self.scroll * self.COLS + j
            if idx < len(self.items) and inside(self._item_rect(j), pos):
                return ("item", idx)
        for i in range(9):
            if inside(self._inv_rect(i), pos):
                return ("inv", i)
        return None

    def click(self, pos, button, shift=False):
        key = self.slot_at(pos)
        S = self.S
        if key is None:
            if not inside((self.px, self.py, self.PW, self.PH), pos) and self.cursor:
                S.drop_stack(self.cursor[0], self.cursor[1])
                self.cursor = None
            return
        if key[0] == "item":
            if self.cursor is not None:
                self.cursor = None                       # on repose l'objet : il disparait
            else:
                it = self.items[key[1]]
                if shift:
                    inv_add(S.player.inv, it, max_stack(it))
                else:
                    self.cursor = [it, max_stack(it) if button == 1 else 1]
            return
        cont, i = S.player.inv, key[1]
        s, c = cont[i], self.cursor
        if s and s[0] == SLOT_LOCK:
            return
        if button == 1:
            if c is None:
                cont[i], self.cursor = None, s
            elif s is None:
                cont[i], self.cursor = c, None
            elif s[0] == c[0]:
                n = min(c[1], max_stack(s[0]) - s[1])
                s[1] += n
                c[1] -= n
                if c[1] <= 0:
                    self.cursor = None
            else:
                cont[i], self.cursor = c, s
        elif c is not None:
            if s is None:
                cont[i] = [c[0], 1]
                c[1] -= 1
            elif s[0] == c[0] and s[1] < max_stack(s[0]):
                s[1] += 1
                c[1] -= 1
            if self.cursor and self.cursor[1] <= 0:
                self.cursor = None
        elif s:
            cont[i] = None

    def close(self):
        S = self.S
        if self.cursor:
            left = inv_add(S.player.inv, self.cursor[0], self.cursor[1])
            if left:
                S.drop_stack(self.cursor[0], left)
            self.cursor = None

    def draw(self, surf, mouse):
        dim = pygame.Surface((GUI_W, GUI_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        surf.blit(dim, (0, 0))
        draw_panel(surf, (self.px, self.py, self.PW, self.PH))
        draw_text(surf, tr("creative_inv"), "m", (60, 60, 60), (self.px + 16, self.py + 12), "l", False)
        hover = self.slot_at(mouse)
        for j in range(self.COLS * self.ROWS):
            idx = self.scroll * self.COLS + j
            if idx >= len(self.items):
                break
            r = self._item_rect(j)
            draw_slot(surf, r, hover == ("item", idx))
            draw_stack(surf, [self.items[idx], 1], r[0] + 2, r[1] + 2)
        ms = self._max_scroll()
        if ms > 0:
            pygame.draw.rect(surf, (120, 120, 120), (self.px + 16 + 9 * 36 + 4, self.py + 40, 6, 216))
            bh = max(20, 216 // (ms + 1))
            pygame.draw.rect(surf, (230, 230, 230), (self.px + 16 + 9 * 36 + 4,
                                                     self.py + 40 + (216 - bh) * self.scroll // ms, 6, bh))
        for i in range(9):
            r = self._inv_rect(i)
            draw_slot(surf, r, hover == ("inv", i))
            draw_stack(surf, self.S.player.inv[i], r[0] + 2, r[1] + 2)
        if self.cursor:
            draw_stack(surf, self.cursor, mouse[0] - 16, mouse[1] - 16)
        elif hover:
            st = [self.items[hover[1]], 1] if hover[0] == "item" else self.S.player.inv[hover[1]]
            if st:
                draw_tooltip(surf, [item_name(st[0])], mouse)


# ============================================================================
# SAUVEGARDES, PARTIE EN COURS (Session)
# ============================================================================
def load_settings():
    d = {"lang": "fr", "render": 6, "sens": 0.13, "fov": 72}
    try:
        with open(os.path.join(SAVE_DIR, "settings.json"), "r", encoding="utf-8") as f:
            d.update(json.load(f))
    except Exception:
        pass
    d["render"] = max(2, min(14, int(d["render"])))
    return d


def save_settings(d):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(os.path.join(SAVE_DIR, "settings.json"), "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass


def list_worlds():
    out = []
    if os.path.isdir(WORLDS_DIR):
        for d in os.listdir(WORLDS_DIR):
            fn = os.path.join(WORLDS_DIR, d, "world.json")
            if os.path.isfile(fn):
                try:
                    with open(fn, "r", encoding="utf-8") as f:
                        m = json.load(f)
                    m["dir"] = d
                    m["mods_n"] = mods_count(os.path.join(WORLDS_DIR, d))
                    out.append(m)
                except Exception:
                    pass
    out.sort(key=lambda m: -m.get("last_played", 0))
    return out


def parse_seed(t):
    t = t.strip()
    if not t:
        return random.randint(1, 2 ** 30)
    try:
        return abs(int(t)) % (2 ** 30)
    except ValueError:
        h = 7
        for ch in t:
            h = (h * 31 + ord(ch)) & 0x3FFFFFFF
        return h


def create_world_files(name, seed_text, mode="survival"):
    """Cree le dossier du monde. Retourne le nom de dossier ou None si le nom existe."""
    safe = "".join(c for c in name.strip() if c not in '\\/:*?"<>|').strip(". ") or "world"
    path = os.path.join(WORLDS_DIR, safe)
    if os.path.exists(path):
        return None
    os.makedirs(os.path.join(path, "chunks"), exist_ok=True)
    meta = {"name": name.strip() or safe, "seed": parse_seed(seed_text), "created": time.time(),
            "last_played": time.time(), "time": DAY_LEN * 0.08, "player": None,
            "mode": "creative" if mode == "creative" else "survival"}
    with open(os.path.join(path, "world.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    return safe


class Session:
    def __init__(self, dirname, settings):
        self.dir = dirname
        self.path = os.path.join(WORLDS_DIR, dirname)
        with open(os.path.join(self.path, "world.json"), "r", encoding="utf-8") as f:
            self.meta = json.load(f)
        self.settings = settings
        self.world = World(int(self.meta["seed"]), self.path)
        self.player = Player()
        self.creative = self.meta.get("mode") == "creative"
        self.player.creative = self.creative
        self.break_cd = 0.0
        self.equip = 0.0
        self._held = -1
        self.mobs, self.drops, self.arrows = [], [], []
        self.time = float(self.meta.get("time", DAY_LEN * 0.08))
        self.target = self.target_prev = self.target_mob = None
        self.target_dist = 99.0
        self.break_block = None
        self.break_progress = 0.0
        self.ui_open = False
        self.swing = 0.0
        self.name_timer = 0.0
        self.messages = []
        self.show_debug = False
        self.spawn_timer = 2.0
        self.save_timer = 0.0
        self.attack_cd = 0.0
        self.place_cd = 0.0
        self.unload_t = 0.0
        self.border_t = 0.0
        self.want_ui = None                 # ("table"|"chest"|"furnace"|"naval"|"boat", position) demande par un clic droit
        self.boats = load_boats(self.path)
        self.driving = None                 # bateau que le joueur pilote
        self.standing_boat = None           # bateau sur lequel le joueur marche
        self.target_boat = None
        self.target_boat_t = 99.0
        self.engine_msg_t = 0.0
        self._sneak_prev = False
        self.need_cache = None
        pl = self.meta.get("player")
        sx, sz = spawn_point(int(self.meta["seed"]))
        self.spawn = (sx + 0.5, sz + 0.5)
        self.fix_spawn = pl is None
        if pl:
            p = self.player
            p.x, p.y, p.z = pl["x"], pl["y"], pl["z"]
            p.yaw, p.pitch, p.health, p.sel = pl["yaw"], pl["pitch"], pl["health"], pl.get("sel", 0)
            inv = pl.get("inv") or [None] * 36
            p.inv = [list(s) if s else None for s in inv][:36] + [None] * (36 - len(inv))
            arm = pl.get("armor") or [None] * 4
            p.armor = [list(s) if s else None for s in arm][:4] + [None] * (4 - len(arm))
            if p.health <= 0:
                p.health = 20.0
            self.spawn = tuple(pl.get("spawn", self.spawn))
        else:
            self.player.x, self.player.y, self.player.z = self.spawn[0], 90.0, self.spawn[1]
        self._migrate_legacy()

    # ---------- utilitaires ----------
    def _migrate_legacy(self):
        """Anciens mondes du mod bateaux : son 'four' (objet 5002) devient le vrai four du jeu."""
        lists = [self.player.inv] + [b.storage for b in self.boats] + [b.fuel for b in self.boats]
        for lst in lists:
            for s in lst:
                if s and s[0] == 5002:
                    s[0] = FURNACE

    def msg(self, text, secs=3.0):
        self.messages = [[text, secs]]

    def is_day(self):
        return sky_state(self.time)[2] > 0.45

    def sky_exposed(self, x, y, z):
        xi, zi = int(math.floor(x)), int(math.floor(z))
        for yy in range(int(y), min(WORLD_H, int(y) + 90)):
            if OPAQUE[self.world.get_block(xi, yy, zi)]:
                return False
        return True

    def hurt_player(self, amount, fx, fz):
        p = self.player
        if p.dead or self.creative:
            return
        p.take_damage(amount)
        ln = math.hypot(fx, fz) or 1.0
        p.vx += fx / ln * 5.0
        p.vz += fz / ln * 5.0
        p.vy = max(p.vy, 4.0)

    def shoot_arrow(self, m):
        p = self.player
        ox, oy, oz = m.x, m.y + 1.5, m.z
        dx, dy, dz = p.x - ox, (p.y + 1.1) - oy, p.z - oz
        dist = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        sp = 20.0
        t = dist / sp
        vy = (dy + 0.5 * 18.0 * t * t) / t
        sx = random.uniform(-1.3, 1.3)
        sz = random.uniform(-1.3, 1.3)
        self.arrows.append(Arrow(ox, oy, oz, dx / t + sx, vy, dz / t + sz))

    def explode(self, x, y, z, r):
        w, p = self.world, self.player
        R = int(math.ceil(r))
        for bx in range(int(x) - R, int(x) + R + 1):
            for by in range(int(y) - R, int(y) + R + 1):
                for bz in range(int(z) - R, int(z) + R + 1):
                    if (bx + .5 - x) ** 2 + (by + .5 - y) ** 2 + (bz + .5 - z) ** 2 <= r * r:
                        b = w.get_block(bx, by, bz)
                        if b not in (AIR, BEDROCK, WATER):
                            w.set_block(bx, by, bz, AIR)
        dist = math.sqrt((p.x - x) ** 2 + (p.y + 0.9 - y) ** 2 + (p.z - z) ** 2)
        if dist < 7.0 and not p.dead:
            self.hurt_player((1.0 - dist / 7.0) * 17.0, p.x - x, p.z - z)
        for m in self.mobs:
            d = math.sqrt((m.x - x) ** 2 + (m.y - y) ** 2 + (m.z - z) ** 2)
            if d < 7.0 and m.fuse != -2:
                m.damage((1.0 - d / 7.0) * 17.0, m.x - x, m.z - z)

    def drop_stack(self, item, count):
        p = self.player
        lx, ly, lz = p.look()
        ex, ey, ez = p.eye_pos()
        self.drops.append(DropItem(item, count, ex + lx * 0.6, ey - 0.3, ez + lz * 0.6,
                                   lx * 4.5, 2.0, lz * 4.5))
        self.drops[-1].age = -0.6

    def drop_at(self, item, count, x, y, z):
        self.drops.append(DropItem(item, count, x, y, z, random.uniform(-1.2, 1.2), 3.0, random.uniform(-1.2, 1.2)))

    def kill_mob(self, m):
        if m.hp <= -50 or m.fuse == -2:
            return
        for (item, lo, hi) in MOBS[m.kind]["drops"]:
            n = random.randint(lo, hi)
            if n > 0:
                self.drop_at(item, n, m.x, m.y + 0.5, m.z)

    def on_death(self):
        p = self.player
        p.inv = [None if (s and s[0] == SLOT_LOCK) else s for s in p.inv]
        self.driving = None
        self.standing_boat = None
        for s in p.inv + p.armor:
            if s:
                self.drop_at(s[0], s[1], p.x, p.y + 1.0, p.z)
        p.inv = [None] * 36
        p.armor = [None] * 4

    def respawn(self):
        self.driving = None
        self.standing_boat = None
        old = self.player
        p = Player(self.spawn[0], 0, self.spawn[1])
        p.y = self.world.surface_y(int(p.x), int(p.z)) + 1.0
        p.yaw = old.yaw
        p.creative = self.creative
        self.player = p

    # ---------- chunks ----------
    def _mesh(self, renderer, ch):
        vo, vw = build_chunk_mesh(self.world, ch)
        renderer.upload_chunk(ch, vo, vw)

    def stream(self, renderer, budget=0.007, radius=None):
        """Charge / genere / dessine les chunks autour du joueur (avec un budget de temps)."""
        w, p = self.world, self.player
        R = radius if radius is not None else self.settings["render"]
        pcx, pcz = int(p.x) >> 4, int(p.z) >> 4
        t0 = time.perf_counter()
        while w.urgent:
            ch = w.urgent.pop(0)
            if w.chunks.get((ch.cx, ch.cz)) is ch and w.neighbors_ready(ch):
                self._mesh(renderer, ch)
        key = (pcx, pcz, R)
        if self.need_cache is None or self.need_cache[0] != key:
            lst = [(dx, dz) for dx in range(-R - 1, R + 2) for dz in range(-R - 1, R + 2)
                   if dx * dx + dz * dz <= (R + 1) * (R + 1)]
            lst.sort(key=lambda d: d[0] * d[0] + d[1] * d[1])
            self.need_cache = (key, lst)
        lst = self.need_cache[1]
        for (dx, dz) in lst:
            cx, cz = pcx + dx, pcz + dz
            if (cx, cz) not in w.chunks and w.in_bounds(cx, cz):
                w.load_chunk(cx, cz)
                if time.perf_counter() - t0 > budget:
                    return
        for (dx, dz) in lst:
            ch = w.chunks.get((pcx + dx, pcz + dz))
            if ch is not None and ch.need_mesh and dx * dx + dz * dz <= R * R and w.neighbors_ready(ch):
                self._mesh(renderer, ch)
                if time.perf_counter() - t0 > budget:
                    return

    def progress(self, radius):
        w, p = self.world, self.player
        pcx, pcz = int(p.x) >> 4, int(p.z) >> 4
        tot = done = 0
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx * dx + dz * dz <= radius * radius and w.in_bounds(pcx + dx, pcz + dz):
                    tot += 1
                    ch = w.chunks.get((pcx + dx, pcz + dz))
                    if ch is not None and ch.meshed:
                        done += 1
        return done / float(max(1, tot))

    def unload_far(self, renderer):
        w, p = self.world, self.player
        pcx, pcz = int(p.x) >> 4, int(p.z) >> 4
        R = self.settings["render"] + 3
        for k in [k for k in w.chunks if abs(k[0] - pcx) > R or abs(k[1] - pcz) > R]:
            ch = w.chunks.pop(k)
            w.save_chunk(ch)
            renderer.free_chunk(ch)

    def finish_loading(self):
        w, p = self.world, self.player
        if self.fix_spawn:
            p.y = w.surface_y(int(p.x), int(p.z)) + 1.0
            self.fix_spawn = False
            made = tries = 0
            while made < 7 and tries < 150:
                tries += 1
                if self.try_spawn(passive=True, near=True):
                    made += 1
        self.spawn_timer = 2.0
        if self.creative:
            self.msg(tr("creative_hint"), 6.0)

    # ---------- apparition des mobs ----------
    def can_stand(self, x, y, z, h):
        w = self.world
        if y < 2 or y + h >= WORLD_H:
            return False
        if not w.is_solid(x, y - 1, z) or w.get_block(x, y - 1, z) in (LEAVES,):
            return False
        for k in range(int(math.ceil(h))):
            if w.is_solid(x, y + k, z) or w.get_block(x, y + k, z) == WATER:
                return False
        return True

    def try_spawn(self, passive, near=False, underground=False):
        p, w = self.player, self.world
        ang = random.random() * math.tau
        dist = random.uniform(8, 30) if near else random.uniform(18, 46)
        x = int(p.x + math.cos(ang) * dist)
        z = int(p.z + math.sin(ang) * dist)
        if (x >> 4, z >> 4) not in w.chunks:
            return False
        if underground:
            y = random.randint(4, max(5, int(p.y) + 6))
            if self.sky_exposed(x, y + 1, z):
                return False
        else:
            y = w.surface_y(x, z) + 1
        if passive:
            if w.get_block(x, y - 1, z) != GRASS:
                return False
            kind = random.choice(["cow", "cow", "pig", "pig", "chicken", "chicken", "horse"])
        else:
            kind = random.choice(["zombie", "zombie", "skeleton", "creeper"])
        h = MOBS[kind]["h"]
        if not self.can_stand(x, y, z, h):
            return False
        n = random.randint(1, 3) if passive and kind != "horse" else 1
        for i in range(n):
            self.mobs.append(Mob(kind, x + 0.5 + random.uniform(-1.5, 1.5) * (i > 0), y,
                                 z + 0.5 + random.uniform(-1.5, 1.5) * (i > 0)))
        return True

    def spawn_tick(self, dt):
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return
        self.spawn_timer = 1.2
        p = self.player
        pas = sum(1 for m in self.mobs if not m.hostile)
        hos = len(self.mobs) - pas
        for m in list(self.mobs):
            d2 = (m.x - p.x) ** 2 + (m.z - p.z) ** 2
            if d2 > (90 ** 2 if not m.hostile else 70 ** 2):
                self.mobs.remove(m)
        if pas < 22:
            for _ in range(4):
                if self.try_spawn(True):
                    break
        if hos < 14:
            if not self.is_day():
                for _ in range(6):
                    if self.try_spawn(False):
                        break
            else:
                for _ in range(6):
                    if self.try_spawn(False, underground=True):
                        break

    # ---------- joueur : casser / poser ----------
    def update_target(self):
        w, p = self.world, self.player
        ex, ey, ez = p.eye_pos()
        dx, dy, dz = p.look()
        hit = raycast(w, ex, ey, ez, dx, dy, dz, 5.0)
        self.target, self.target_prev, self.target_dist = (hit[0], hit[1], hit[2]) if hit else (None, None, 99.0)
        best, bt = None, 3.6
        for m in self.mobs:
            if (m.x - ex) ** 2 + (m.z - ez) ** 2 > 36:
                continue
            t = ray_aabb(ex, ey, ez, dx, dy, dz, (m.x - m.w / 2, m.y, m.z - m.w / 2),
                         (m.x + m.w / 2, m.y + m.h, m.z + m.w / 2))
            if t is not None and t < bt and t < self.target_dist:
                best, bt = m, t
        self.target_mob = best
        if best:
            self.target = None
        self.target_boat, self.target_boat_t = None, 99.0           # viser un bateau
        if self.driving is None and best is None and self.boats and not self.player.dead:
            ex, ey, ez = self.player.eye_pos()
            dx, dy, dz = self.player.look()
            b, t = ray_boats(self.boats, ex, ey, ez, dx, dy, dz, min(4.5, self.target_dist))
            if b is not None:
                self.target_boat, self.target_boat_t = b, t
                self.target = self.target_prev = None

    def _consume_held(self):
        p = self.player
        s = p.inv[p.sel]
        if s:
            s[1] -= 1
            if s[1] <= 0:
                p.inv[p.sel] = None

    def _settle_sand(self, x, y, z):
        """Le sable et le gravier tombent."""
        w = self.world
        while y > 0 and w.get_block(x, y, z) in (SAND, GRAVEL) and w.get_block(x, y - 1, z) in (AIR, WATER):
            b = w.get_block(x, y, z)
            w.set_block(x, y - 1, z, b)
            w.set_block(x, y, z, AIR)
            y -= 1

    def break_target(self, ok):
        x, y, z = self.target
        w = self.world
        b = w.get_block(x, y, z)
        if DOOR0 <= b < DOOR0 + 16:                       # une porte = 2 blocs : on enleve les deux
            ly = y if b < DOOR0 + 8 else y - 1
            w.set_block(x, ly, z, AIR)
            w.set_block(x, ly + 1, z, AIR)
            if ok:
                self.drop_at(DOOR_ITEM, 1, x + 0.5, ly + 0.5, z + 0.5)
            self.break_progress = 0.0
            self.break_block = None
            return
        t = w.tiles.pop((x, y, z), None)                  # coffre / four : le contenu tombe par terre
        if t:
            for s in t["items"]:
                if s:
                    self.drop_at(s[0], s[1], x + 0.5, y + 0.5, z + 0.5)
        w.set_block(x, y, z, AIR)
        item = BDROP.get(b, b)
        if ok and item:
            lo, hi = BDROPN.get(b, (1, 1))
            self.drop_at(item, random.randint(lo, hi), x + 0.5, y + 0.5, z + 0.5)
        up = w.get_block(x, y + 1, z)
        if CROSS[up] and not CROSS[b]:                    # une fleur ne flotte pas : elle part avec son sol
            w.set_block(x, y + 1, z, AIR)
            up_item = BDROP.get(up, up)
            if up_item:
                self.drop_at(up_item, 1, x + 0.5, y + 1.5, z + 0.5)
        yy = y + 1
        while w.get_block(x, yy, z) in (SAND, GRAVEL):
            yy += 1
        for k in range(y + 1, yy):
            self._settle_sand(x, k, z)
        self.break_progress = 0.0
        self.break_block = None

    def attack(self, m):
        p = self.player
        tool = TOOLS.get(p.held())
        dmg = tool[3] if tool else 1.0
        m.damage(dmg, m.x - p.x, m.z - p.z)

    def _overlaps(self, x, y, z):
        p = self.player
        if p.x - 0.3 < x + 1 and p.x + 0.3 > x and p.y < y + 1 and p.y + 1.8 > y and p.z - 0.3 < z + 1 and p.z + 0.3 > z:
            return True
        for m in self.mobs:
            if m.x - m.w / 2 < x + 1 and m.x + m.w / 2 > x and m.y < y + 1 and m.y + m.h > y \
                    and m.z - m.w / 2 < z + 1 and m.z + m.w / 2 > z:
                return True
        return False

    def _try_use_boat(self, sneak):
        """Clic droit : table navale, seau, pose d'un bateau, monter a bord. True si traite."""
        p, w = self.player, self.world
        tgt = self.target
        if tgt and not sneak and w.get_block(*tgt) == NAVAL_TABLE:
            self.want_ui = ("naval", tgt)
            return True
        held = p.held()
        if held in FOODS and p.health < 20:
            return False
        bt = self.target_boat
        if held == BUCKET or held in BOAT_ITEMS:
            ex, ey, ez = p.eye_pos()
            dx, dy, dz = p.look()
            hit = water_ray(w, ex, ey, ez, dx, dy, dz, 5.0)
            if hit and (bt is None or hit[3] < self.target_boat_t):
                if held == BUCKET:
                    fill_bucket(self)
                    self.place_cd = 0.4
                else:
                    placed = place_boat(self, BOAT_ITEMS[held], hit)
                    self.place_cd = 0.5 if placed else 0.4
                    if placed:
                        self.swing = max(self.swing, 0.001)
                return True
        if bt is not None:
            self.place_cd = 0.35
            if sneak:
                self.want_ui = ("boat", bt)
            else:
                board(self, bt)
            return True
        return False

    def _dismantle_tick(self, dt, lmb):
        b = self.target_boat
        p = self.player
        ok = bool(lmb) and b is not None and not self.ui_open and self.driving is None and not p.dead \
            and self.standing_boat is not b
        for o in self.boats:
            if not (ok and o is b):
                o.hit = 0.0
        if ok:
            need = 0.25 if self.creative else 1.2
            b.hit += dt
            if b.hit >= need:
                dismantle(self, b)
            else:
                self.msg(tr("b_dismantle") % int(100 * b.hit / need), 0.3)

    def use_item(self, sneak):
        if self._try_use_boat(sneak):
            return
        p, w = self.player, self.world
        tgt, prev = self.target, self.target_prev
        if tgt and not sneak:
            b = w.get_block(*tgt)
            if b == TABLE:
                self.want_ui = ("table", tgt)
                return
            if CHEST <= b < CHEST + 4:
                self.want_ui = ("chest", tgt)
                return
            if FURNACE <= b < FURNACE + 4 or FURNACE_LIT <= b < FURNACE_LIT + 4:
                self.want_ui = ("furnace", tgt)
                return
            if DOOR0 <= b < DOOR0 + 16:
                self.toggle_door(*tgt)
                self.place_cd = 0.25
                return
        held = p.held()
        if held in ARMOR:                                 # clic droit : on enfile l'armure
            slot = ARMOR[held][0]
            old = p.armor[slot]
            p.armor[slot] = [held, 1]
            p.inv[p.sel] = old
            self.place_cd = 0.4
            return
        if held == DOOR_ITEM and tgt and prev:
            x, y, z = prev
            if (w.get_block(x, y, z) == AIR and w.get_block(x, y + 1, z) == AIR and y + 1 < WORLD_H
                    and w.is_solid(x, y - 1, z) and not self._overlaps(x, y, z) and not self._overlaps(x, y + 1, z)):
                f = self.facing_toward_player()
                w.set_block(x, y, z, DOOR0 + f)
                w.set_block(x, y + 1, z, DOOR0 + 8 + f)
                if not self.creative:
                    self._consume_held()
                self.swing = max(self.swing, 0.001)
                self.place_cd = 0.25
            return
        if held in FOODS:
            if p.health < 20:
                p.health = min(20.0, p.health + FOODS[held])
                self._consume_held()
                self.place_cd = 0.7
            return
        if held in BLOCK_ITEMS and tgt and prev:
            x, y, z = prev
            if w.get_block(x, y, z) in (AIR, WATER) and 0 <= y < WORLD_H and not self._overlaps(x, y, z):
                bid = held
                if held == CHEST or held == FURNACE:
                    bid = held + self.facing_toward_player()
                if w.set_block(x, y, z, bid):
                    if held == CHEST:
                        w.tile((x, y, z), "chest")
                    elif held == FURNACE:
                        w.tile((x, y, z), "furnace")
                    if not self.creative:
                        self._consume_held()
                    self.swing = max(self.swing, 0.001)
                    self.place_cd = 0.22
                    if held in (SAND, GRAVEL):
                        self._settle_sand(x, y, z)

    def facing_toward_player(self):
        """Orientation (0 N, 1 E, 2 S, 3 O) pour qu'un bloc pose regarde le joueur."""
        lx, ly, lz = self.player.look()
        if abs(lx) > abs(lz):
            return 3 if lx > 0 else 1
        return 0 if lz > 0 else 2

    def toggle_door(self, x, y, z):
        w = self.world
        b = w.get_block(x, y, z)
        ly = y if b < DOOR0 + 8 else y - 1
        k = w.get_block(x, ly, z) - DOOR0
        if not (0 <= k < 8):
            return
        opened, f = (k // 4) % 2, k % 4
        w.set_block(x, ly, z, DOOR0 + (1 - opened) * 4 + f)
        w.set_block(x, ly + 1, z, DOOR0 + 8 + (1 - opened) * 4 + f)

    def tick_furnace(self, pos, t, dt):
        inp, fuel, out = t["items"]
        rec = SMELT.get(inp[0]) if inp else None
        can = rec is not None and (out is None or (out[0] == rec[0] and out[1] + rec[1] <= max_stack(out[0])))
        if t["burn"] <= 0 and can and fuel and fuel[0] in FUEL:
            t["burn"] = t["burn_max"] = FUEL[fuel[0]]
            fuel[1] -= 1
            if fuel[1] <= 0:
                t["items"][1] = None
        if t["burn"] > 0:
            t["burn"] -= dt
            if can:
                t["cook"] += dt
                if t["cook"] >= SMELT_TIME:
                    t["cook"] = 0.0
                    inp[1] -= 1
                    if inp[1] <= 0:
                        t["items"][0] = None
                    if out is None:
                        t["items"][2] = [rec[0], rec[1]]
                    else:
                        out[1] += rec[1]
            else:
                t["cook"] = max(0.0, t["cook"] - dt * 2)
        else:
            t["burn"] = 0.0
            t["cook"] = max(0.0, t["cook"] - dt * 2)
        b = self.world.get_block(*pos)
        if t["burn"] > 0 and FURNACE <= b < FURNACE + 4:
            self.world.set_block(pos[0], pos[1], pos[2], b - FURNACE + FURNACE_LIT)
        elif t["burn"] <= 0 and FURNACE_LIT <= b < FURNACE_LIT + 4:
            self.world.set_block(pos[0], pos[1], pos[2], b - FURNACE_LIT + FURNACE)

    # ---------- boucle de mise a jour ----------
    def update(self, dt, keys, lmb, rmb):
        """Bateaux (pilotage, pont) autour de la mise a jour normale de la partie."""
        p = self.player
        sneak = bool(keys.get("sneak"))
        pk = keys
        self.engine_msg_t = max(0.0, self.engine_msg_t - dt)
        if self.driving is not None and (p.dead or self.driving not in self.boats):
            self.driving = None
        throttle = steer = 0
        if self.driving is not None:
            if not self.ui_open:
                throttle = (1 if keys.get("fwd") else 0) - (1 if keys.get("back") else 0)
                steer = (1 if keys.get("right") else 0) - (1 if keys.get("left") else 0)
                if sneak and not self._sneak_prev:
                    dismount(self)
            if self.driving is not None:
                pk = {}
        self._sneak_prev = sneak
        self._dismantle_tick(dt, lmb)
        for b in self.boats:
            b.last = (b.x, b.z, b.yaw)
            if (b.x - p.x) ** 2 + (b.z - p.z) ** 2 > 160.0 * 160.0:
                continue
            if (int(math.floor(b.x)) >> 4, int(math.floor(b.z)) >> 4) not in self.world.chunks:
                continue
            driven = b is self.driving
            dyaw = b.update(self, dt, throttle if driven else 0, steer if driven else 0, driven)
            if driven and dyaw:
                p.yaw = (p.yaw - math.degrees(dyaw)) % 360.0
        sb = self.standing_boat                       # le pont emporte le joueur
        if sb is not None and self.driving is None and not p.dead and sb.last != (sb.x, sb.z, sb.yaw):
            ox, oz, oyaw = sb.last
            lx, lz = to_local(ox, oz, oyaw, p.x, p.z)
            p.x, p.z = to_world(sb.x, sb.z, sb.yaw, lx, lz)
        self._update_core(dt, pk, lmb, rmb)
        p = self.player
        if not p.dead:
            if self.driving is not None:
                p.x, p.y, p.z = self.driving.helm_world()
                p.vx = p.vy = p.vz = 0.0
                p.on_ground = True
                p.fall = 0.0
                p.flying = False
                self.standing_boat = None
            else:
                resolve_player(self, bool(keys.get("jump")) and not self.ui_open)
        normalize_inventory(self)

    def _update_core(self, dt, keys, lmb, rmb):
        w, p = self.world, self.player
        self.time += dt
        if not p.dead:
            p.update(dt, w, keys, self.ui_open)
        self.update_target()
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.place_cd = max(0.0, self.place_cd - dt)
        self.break_cd = max(0.0, self.break_cd - dt)
        if self.creative:
            p.health = 20.0
        held_now = p.held()
        if held_now != self._held:
            self._held = held_now
            self.equip = 0.0
        self.equip = min(1.0, self.equip + dt * 5.0)
        active = lmb and not self.ui_open and not p.dead and (self.target or self.target_mob)
        if active:
            if self.target_mob:
                self.break_progress = 0.0
                if self.attack_cd <= 0:
                    self.attack_cd = 0.45
                    self.attack(self.target_mob)
            else:
                b = w.get_block(*self.target)
                if self.creative:
                    if self.break_cd <= 0 and (b in HARD or (b == BEDROCK and self.target[1] > 0)):
                        self.break_target(False)
                        self.break_cd = 0.2
                elif b in HARD:
                    if self.break_block != self.target:
                        self.break_block = self.target
                        self.break_progress = 0.0
                    t, ok = break_time(b, p.held())
                    self.break_progress += dt / t
                    if self.break_progress >= 1.0:
                        self.break_target(ok)
        else:
            self.break_progress = 0.0
            self.break_block = None
        if rmb and self.place_cd <= 0 and not self.ui_open and not p.dead:
            self.use_item(keys.get("sneak"))
        if active and self.swing <= 0:
            self.swing = 0.001
        if self.swing > 0:
            self.swing += dt * 3.5
            if self.swing >= 1.0:
                self.swing = 0.001 if active else 0.0
        # entites
        for m in self.mobs:
            m.update(dt, self)
        for m in [m for m in self.mobs if m.dead]:
            self.kill_mob(m)
            self.mobs.remove(m)
        pcx = p.x
        for d in list(self.drops):
            d.update(dt, w)
            if d.age > 300 or d.y < -20:
                self.drops.remove(d)
                continue
            if d.age > 0.4 and not p.dead and (d.x - p.x) ** 2 + (d.y - p.y - 0.8) ** 2 + (d.z - p.z) ** 2 < 2.0:
                left = inv_add(p.inv, d.item, d.count)
                if left == 0:
                    self.drops.remove(d)
                else:
                    d.count = left
        for a in list(self.arrows):
            a.update(dt, self)
            if a.dead:
                self.arrows.remove(a)
        for pos, t in list(w.tiles.items()):              # les fours cuisent tant que leur zone est chargee
            if t.get("type") == "furnace" and (pos[0] >> 4, pos[2] >> 4) in w.chunks:
                self.tick_furnace(pos, t, dt)
        self.spawn_tick(dt)
        # divers
        self.name_timer = max(0.0, self.name_timer - dt)
        for m in self.messages:
            m[1] -= dt
        self.messages = [m for m in self.messages if m[1] > 0]
        if p.x <= 0.4 or p.z <= 0.4 or p.x >= WORLD_SIZE - 0.4 or p.z >= WORLD_SIZE - 0.4:
            self.border_t -= dt
            if self.border_t <= 0:
                self.msg(tr("world_border"))
                self.border_t = 6.0
        self.save_timer += dt
        if self.save_timer > 90:
            self.save_timer = 0.0
            self.save()

    def save(self):
        p = self.player
        self.meta["last_played"] = time.time()
        self.meta["time"] = self.time
        self.meta["player"] = {"x": p.x, "y": p.y, "z": p.z, "yaw": p.yaw, "pitch": p.pitch,
                               "health": p.health, "sel": p.sel, "inv": p.inv, "armor": p.armor, "spawn": list(self.spawn)}
        try:
            with open(os.path.join(self.path, "world.json"), "w", encoding="utf-8") as f:
                json.dump(self.meta, f)
            self.world.save_all()
            save_boats(self.path, self.boats)
        except Exception as e:
            print("Erreur de sauvegarde :", e)


# ============================================================================
# MODS (JSON + images PNG) : installes separement dans chaque monde
# ----------------------------------------------------------------------------
# Un mod = un fichier  mod.json  + des images PNG (16x16 conseille).
# Il peut etre livre en .zip, en .json (PNG dans le meme dossier) ou en dossier.
# Voir le fichier LISEZMOI_MODS.md pour le format complet.
# Nouveautes de la v0_3 :
#   - bloc  "shape": "cross"      : bloc en croix (fleur) : traversable, se casse tout de suite
#   - mod   "plants": [{"block": "rose", "density": 0.003}] : fleurs qui poussent toutes seules sur l'herbe,
#                                   par massifs (density = part de l'herbe couverte, 0.0002 a 0.03)
#   - recette "shapeless": true   : recette "en vrac" (l'ordre des objets dans la grille ne compte pas)
# ============================================================================
class ModError(Exception):
    pass


_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
BASE_NAMES = {
    "stone": STONE, "grass": GRASS, "dirt": DIRT, "cobblestone": COBBLE, "cobble": COBBLE, "planks": PLANKS,
    "sand": SAND, "gravel": GRAVEL, "log": LOG, "leaves": LEAVES, "coal_ore": COAL_ORE, "iron_ore": IRON_ORE,
    "gold_ore": GOLD_ORE, "diamond_ore": DIAMOND_ORE, "crafting_table": TABLE, "table": TABLE,
    "stick": STICK, "coal": COAL, "iron_ingot": IRON_INGOT, "gold_ingot": GOLD_INGOT, "diamond": DIAMOND,
    "raw_porkchop": RAW_PORK, "raw_pork": RAW_PORK, "raw_beef": RAW_BEEF, "raw_chicken": RAW_CHICKEN,
    "feather": FEATHER, "leather": LEATHER, "bone": BONE, "gunpowder": GUNPOWDER, "rotten_flesh": ROTTEN,
    "chest": CHEST, "furnace": FURNACE, "coal_block": COAL_BLOCK, "iron_block": IRON_BLOCK,
    "gold_block": GOLD_BLOCK, "diamond_block": DIAMOND_BLOCK, "glass": GLASS, "door": DOOR_ITEM,
    "oak_door": DOOR_ITEM, "raw_iron": RAW_IRON, "raw_gold": RAW_GOLD, "cooked_porkchop": COOKED_PORK,
    "cooked_beef": COOKED_BEEF, "cooked_chicken": COOKED_CHICKEN,
}
for _k, _i in GOLD_TOOL.items():
    BASE_NAMES["golden_%s" % _k] = _i
for _mi, _mn in enumerate(("leather", "iron", "golden", "diamond")):
    for _pi, _pn in enumerate(("helmet", "chestplate", "leggings", "boots")):
        BASE_NAMES["%s_%s" % (_mn, _pn)] = ARMOR0 + 4 * _mi + _pi
ARMOR_SLOTS = ("helmet", "chestplate", "leggings", "boots")
BASE_NAMES.update({"bucket": BUCKET, "water_bucket": WATER_BUCKET, "rowboat": ROWBOAT, "drakkar": DRAKKAR,
                   "motorboat": MOTORBOAT, "liner": LINER, "steam_engine": ENGINE, "iron_hull": HULL_IRON,
                   "windshield": WINDSHIELD, "naval_table": NAVAL_TABLE})
for (_k, _t), _i in TOOL_ID.items():
    BASE_NAMES["%s_%s" % (("wooden", "stone", "iron", "diamond")[_t], _k)] = _i

_BASE_SNAP = {}
_DICTS = ("TILES", "BLOCK_TILES", "ITEM_TILES", "NAMES", "HARD", "BTOOL", "NEED_TIER", "BDROP", "BDROPN",
          "TOOLS", "FOODS", "MAXSTACK", "SMELT", "FUEL", "ARMOR", "SHAPELESS")
_ARRAYS = ("OPAQUE", "SOLID", "SAMEHIDE", "LIGHTBLOCK", "CUBELESS", "CROSS")


def mods_snapshot():
    """Memorise l'etat du jeu de base (avant tout mod)."""
    g = globals()
    for n in _DICTS:
        _BASE_SNAP[n] = dict(g[n])
    for n in _ARRAYS:
        _BASE_SNAP[n] = g[n].copy()
    _BASE_SNAP["BLOCK_ITEMS"] = set(BLOCK_ITEMS)
    _BASE_SNAP["CREATIVE_ITEMS"] = list(CREATIVE_ITEMS)
    _BASE_SNAP["RECIPES"] = list(RECIPES)


def mods_reset():
    """Retire tous les mods : retour au jeu de base."""
    if not _BASE_SNAP:
        return
    g = globals()
    for n in _DICTS:
        g[n].clear()
        g[n].update(_BASE_SNAP[n])
    for n in _ARRAYS:
        g[n][:] = _BASE_SNAP[n]
    BLOCK_ITEMS.clear()
    BLOCK_ITEMS.update(_BASE_SNAP["BLOCK_ITEMS"])
    CREATIVE_ITEMS[:] = _BASE_SNAP["CREATIVE_ITEMS"]
    RECIPES[:] = _BASE_SNAP["RECIPES"]
    MOD_ORES.clear()
    MOD_PLANTS.clear()
    SOLID_PY[:] = SOLID.tolist()
    build_atlas()


# ---------------------------------------------------------------------------
# Lecture des images PNG
# ---------------------------------------------------------------------------
def _decode_png(path):
    """Lecteur PNG de secours (8 bits, non entrelace) -> tableau (16, 16, 4)."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ModError("PNG invalide : %s" % os.path.basename(path))
    pos, idat, plte, trns = 8, b"", None, None
    w = h = bd = ct = il = 0
    while pos + 8 <= len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            w, h, bd, ct, _c, _f, il = struct.unpack(">IIBBBBB", body)
        elif typ == b"PLTE":
            plte = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
    if bd != 8 or il != 0 or ct not in (0, 2, 3, 4, 6) or not (0 < w <= 512 and 0 < h <= 512):
        raise ModError("PNG non pris en charge (8 bits, sans entrelacement) : %s" % os.path.basename(path))
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    stride = w * ch
    raw = zlib.decompress(idat)
    img = np.zeros((h, stride), np.uint8)
    prev = bytearray(stride)
    for y in range(h):
        ft = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - ch] if i >= ch else 0
            b = prev[i]
            c = prev[i - ch] if i >= ch else 0
            if ft == 1:
                line[i] = (line[i] + a) & 255
            elif ft == 2:
                line[i] = (line[i] + b) & 255
            elif ft == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        img[y] = np.frombuffer(bytes(line), np.uint8)
        prev = line
    px = img.reshape(h, w, ch)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[:, :, 3] = 255
    if ct == 6:
        rgba[:] = px
    elif ct == 2:
        rgba[:, :, :3] = px
    elif ct == 0:
        rgba[:, :, :3] = px
    elif ct == 4:
        rgba[:, :, :3] = px[:, :, 0:1]
        rgba[:, :, 3] = px[:, :, 1]
    else:
        pal = np.frombuffer(plte or b"", np.uint8).reshape(-1, 3)
        idx = px[:, :, 0]
        rgba[:, :, :3] = pal[np.minimum(idx, len(pal) - 1)]
        if trns:
            al = np.full(256, 255, np.uint8)
            al[:len(trns)] = np.frombuffer(trns, np.uint8)
            rgba[:, :, 3] = al[idx]
    ys = np.minimum(((np.arange(16) + 0.5) * h / 16.0).astype(int), h - 1)
    xs = np.minimum(((np.arange(16) + 0.5) * w / 16.0).astype(int), w - 1)
    return rgba[ys][:, xs].copy()


def load_png_rgba(path):
    """Charge un PNG et le ramene a 16x16 RGBA."""
    try:
        s = pygame.image.load(path).convert_alpha()
        if tuple(s.get_size()) != (16, 16):
            s = pygame.transform.scale(s, (16, 16))
        raw = _img_bytes(s, "RGBA")
        return np.frombuffer(raw, np.uint8).reshape(16, 16, 4).copy()
    except Exception:
        return _decode_png(path)


# ---------------------------------------------------------------------------
# Lecture et verification d'un mod.json
# ---------------------------------------------------------------------------
def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _num(v, lo, hi, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ModError("%s : un nombre est attendu" % what)
    if v < lo or v > hi:
        raise ModError("%s : doit etre entre %s et %s" % (what, lo, hi))
    return v


def _ident(v, what):
    if not isinstance(v, str) or not _ID_RE.match(v):
        raise ModError('%s : identifiant invalide (a-z, 0-9 et _ seulement, 2 a 32 caracteres)' % what)
    return v


def _names(v, fallback):
    if v is None:
        return {"en": fallback}
    if isinstance(v, str):
        return {"en": v[:40]}
    if isinstance(v, dict):
        d = {k: x[:40] for k, x in v.items() if k in LANGS and isinstance(x, str)}
        if not d:
            d = {"en": fallback}
        if "en" not in d:
            d["en"] = next(iter(d.values()))
        return d
    raise ModError("nom invalide pour %s" % fallback)


def _png_name(moddir, fname, what):
    if (not isinstance(fname, str) or not fname.lower().endswith(".png") or any(c in fname for c in "/\\:")
            or fname.startswith(".")):
        raise ModError("%s : nom de fichier PNG invalide" % what)
    if not os.path.isfile(os.path.join(moddir, fname)):
        raise ModError("%s : fichier %s introuvable" % (what, fname))
    return fname


def parse_mod(moddir, jsonname="mod.json"):
    j = _read_json(os.path.join(moddir, jsonname))
    if not isinstance(j, dict):
        raise ModError("%s illisible (JSON invalide)" % jsonname)
    mid = _ident(j.get("id"), '"id"')
    mod = {"id": mid, "name": str(j.get("name", mid))[:40], "version": str(j.get("version", "1.0"))[:12],
           "blocks": [], "items": [], "recipes": [], "ores": [], "textures": set(), "pack": {},
           "smelting": [], "fuel": [], "plants": [], "files": set()}
    seen = set()
    for key, limit in (("blocks", 40), ("items", 60), ("recipes", 100), ("ores", 20), ("smelting", 40), ("fuel", 20),
                       ("plants", 40)):
        if not isinstance(j.get(key, []), list) or len(j.get(key, [])) > limit:
            raise ModError('"%s" doit etre une liste de %d elements maximum' % (key, limit))
    for b in j.get("blocks", []):
        if not isinstance(b, dict):
            raise ModError("bloc invalide")
        bid = _ident(b.get("id"), "bloc")
        if bid in seen:
            raise ModError("identifiant en double : %s" % bid)
        seen.add(bid)
        if "texture" in b:
            t = _png_name(moddir, b["texture"], "bloc " + bid)
            faces = (t, t, t)
        elif isinstance(b.get("textures"), dict):
            tx = b["textures"]
            allf = tx.get("all")
            top, bottom, side = tx.get("top", allf), tx.get("bottom", allf), tx.get("side", allf)
            if top is None or bottom is None or side is None:
                raise ModError('bloc %s : il faut "all" ou bien "top", "bottom" et "side"' % bid)
            faces = tuple(_png_name(moddir, f, "bloc " + bid) for f in (top, bottom, side))
        else:
            raise ModError('bloc %s : "texture" manquante' % bid)
        shape = b.get("shape", "cube")
        if shape not in ("cube", "cross"):
            raise ModError('bloc %s : "shape" doit etre "cube" ou "cross"' % bid)
        tool = b.get("tool")
        if tool is not None and tool not in KINDS:
            raise ModError("bloc %s : tool doit etre %s" % (bid, ", ".join(KINDS)))
        tier = int(_num(b.get("tier", 0), 0, 4, "bloc %s tier" % bid))
        if tier > 0 and tool is None:
            raise ModError('bloc %s : "tier" demande aussi un "tool"' % bid)
        drop = b.get("drop", "self")
        if not isinstance(drop, str):
            raise ModError("bloc %s : drop invalide" % bid)
        dc = b.get("drop_count", [1, 1])
        if not (isinstance(dc, list) and len(dc) == 2 and all(isinstance(x, int) and 1 <= x <= 64 for x in dc)
                and dc[0] <= dc[1]):
            raise ModError("bloc %s : drop_count doit etre [min, max] entre 1 et 64" % bid)
        mod["blocks"].append({"id": bid, "name": _names(b.get("name"), bid), "faces": faces,
                              "hardness": float(_num(b.get("hardness", 1.5), -1, 100, "bloc %s hardness" % bid)),
                              "tool": tool, "tier": tier, "drop": drop, "drop_count": (dc[0], dc[1]),
                              "transparent": bool(b.get("transparent", shape == "cross")),
                              "solid": bool(b.get("solid", shape != "cross")), "shape": shape})
        mod["textures"].update(faces)
    for it in j.get("items", []):
        if not isinstance(it, dict):
            raise ModError("objet invalide")
        iid = _ident(it.get("id"), "objet")
        if iid in seen:
            raise ModError("identifiant en double : %s" % iid)
        seen.add(iid)
        t = _png_name(moddir, it.get("texture"), "objet " + iid)
        food = it.get("food")
        if food is not None:
            food = int(_num(food, 1, 20, "objet %s food" % iid))
        tool = it.get("tool")
        if tool is not None:
            if not isinstance(tool, dict) or tool.get("kind") not in KINDS:
                raise ModError("objet %s : tool.kind doit etre %s" % (iid, ", ".join(KINDS)))
            tool = (tool["kind"], int(_num(tool.get("tier", 1), 1, 4, "objet %s tier" % iid)),
                    float(_num(tool.get("speed", 4), 0.5, 30, "objet %s speed" % iid)),
                    float(_num(tool.get("damage", 2), 0.5, 30, "objet %s damage" % iid)))
        ms = it.get("max_stack")
        if ms is not None:
            ms = int(_num(ms, 1, 64, "objet %s max_stack" % iid))
        arm = it.get("armor")
        if arm is not None:
            if not isinstance(arm, dict) or arm.get("slot") not in ARMOR_SLOTS:
                raise ModError("objet %s : armor.slot doit etre %s" % (iid, ", ".join(ARMOR_SLOTS)))
            arm = (ARMOR_SLOTS.index(arm["slot"]), int(_num(arm.get("points", 1), 1, 8, "objet %s armor.points" % iid)))
        mod["items"].append({"id": iid, "name": _names(it.get("name"), iid), "texture": t, "food": food,
                             "tool": tool, "max_stack": ms, "armor": arm})
        mod["textures"].add(t)
    for r in j.get("recipes", []):
        if not isinstance(r, dict):
            raise ModError("recette invalide")
        pat, key = r.get("pattern"), r.get("key")
        if not (isinstance(pat, list) and 1 <= len(pat) <= 3 and all(isinstance(x, str) and 1 <= len(x) <= 3 for x in pat)):
            raise ModError('recette : "pattern" = 1 a 3 lignes de 1 a 3 caracteres')
        if not isinstance(key, dict) or any(not (isinstance(k, str) and len(k) == 1 and isinstance(v, str)) for k, v in key.items()):
            raise ModError('recette : "key" invalide')
        if not isinstance(r.get("result"), str):
            raise ModError('recette : "result" manquant')
        mod["recipes"].append({"pattern": pat, "key": key, "result": r["result"],
                               "count": int(_num(r.get("count", 1), 1, 64, "recette count")),
                               "shapeless": bool(r.get("shapeless", False))})
    for sm in j.get("smelting", []):
        if not (isinstance(sm, dict) and isinstance(sm.get("input"), str) and isinstance(sm.get("output"), str)):
            raise ModError('cuisson : "input" et "output" sont obligatoires')
        mod["smelting"].append({"input": sm["input"], "output": sm["output"],
                                "count": int(_num(sm.get("count", 1), 1, 64, "cuisson count"))})
    for fu in j.get("fuel", []):
        if not (isinstance(fu, dict) and isinstance(fu.get("item"), str)):
            raise ModError('combustible : "item" est obligatoire')
        mod["fuel"].append({"item": fu["item"], "seconds": float(_num(fu.get("seconds", 10), 1, 2000, "combustible seconds"))})
    pack = j.get("texture_pack", {})
    if not isinstance(pack, dict) or len(pack) > 250:
        raise ModError('"texture_pack" doit etre un dictionnaire {texture_du_jeu: fichier.png}')
    base_tiles = set(_BASE_SNAP.get("TILES", TILES))
    for tname, fname in pack.items():
        if tname not in base_tiles:
            raise ModError("texture inconnue dans texture_pack : %s" % tname)
        mod["pack"][tname] = _png_name(moddir, fname, "texture_pack " + tname)
    for pl in j.get("plants", []):
        if not isinstance(pl, dict) or not isinstance(pl.get("block"), str):
            raise ModError('fleur : "block" manquant')
        mod["plants"].append({"block": pl["block"],
                              "density": float(_num(pl.get("density", 0.003), 0.0002, 0.03, "fleur density"))})
    for o in j.get("ores", []):
        if not isinstance(o, dict) or not isinstance(o.get("block"), str):
            raise ModError('minerai : "block" manquant')
        lo = int(_num(o.get("min_y", 2), 1, 120, "minerai min_y"))
        hi = int(_num(o.get("max_y", 40), 2, 125, "minerai max_y"))
        if lo >= hi:
            raise ModError("minerai : min_y doit etre plus petit que max_y")
        mod["ores"].append({"block": o["block"], "min_y": lo, "max_y": hi,
                            "density": float(_num(o.get("density", 0.005), 0.0005, 0.06, "minerai density"))})
    mod["files"] = set(mod["textures"]) | set(mod["pack"].values())
    return mod


# ---------------------------------------------------------------------------
# Application d'un mod aux registres du jeu
# ---------------------------------------------------------------------------
def _resolve(ref, local, ids_all):
    if ":" in ref:
        if ref in ids_all:
            return ids_all[ref]
        raise ModError("objet inconnu : %s" % ref)
    if ref in local:
        return local[ref]
    if ref in BASE_NAMES:
        return BASE_NAMES[ref]
    raise ModError("objet inconnu : %s" % ref)


def _alloc(section, key, lo, hi, what):
    if key in section:
        return section[key]
    used = set(section.values())
    for n in range(lo, hi + 1):
        if n not in used:
            section[key] = n
            return n
    raise ModError("trop de %s dans ce monde" % what)


def _register_mod(mod, moddir, reg, ids_all):
    mid = mod["id"]
    local = {}
    for b in mod["blocks"]:
        local[b["id"]] = _alloc(reg["blocks"], "%s:%s" % (mid, b["id"]), 17, 99, "blocs")
    for it in mod["items"]:
        local[it["id"]] = _alloc(reg["items"], "%s:%s" % (mid, it["id"]), 1000, 4999, "objets")
    drops = {}
    for b in mod["blocks"]:
        d = b["drop"]
        drops[b["id"]] = None if d == "self" else (0 if d == "none" else _resolve(d, local, ids_all))
    recipes = []
    shapeless = {}
    for r in mod["recipes"]:
        used = set("".join(r["pattern"])) - {" "}
        if used - set(r["key"].keys()):
            raise ModError("recette : la lettre %s n'est pas dans key" % sorted(used - set(r["key"]))[0])
        ing = {k: _resolve(v, local, ids_all) for k, v in r["key"].items()}
        pat = tuple(tuple(ing.get(ch, 0) if ch != " " else 0 for ch in row) for row in r["pattern"])
        res = _resolve(r["result"], local, ids_all)
        recipes.append((pat, res, r["count"]))
        if r["shapeless"]:                                  # "en vrac" : seuls les objets comptent, pas leur place
            shapeless[tuple(sorted(i for row in pat for i in row if i))] = (res, r["count"])
    plants = []
    for pl in mod["plants"]:
        bid = _resolve(pl["block"], local, ids_all)
        if bid not in [local[b["id"]] for b in mod["blocks"]]:
            raise ModError("fleur : %s doit etre un bloc de ce mod" % pl["block"])
        cover = pl["density"] / PLANT_CHANCE                 # part du terrain couverte par les massifs
        thr = float(np.interp(cover, _PATCH_COVER, _PATCH_THR))
        plants.append((bid, 8000 + bid * 41, thr, PLANT_CHANCE))
    ores = []
    for o in mod["ores"]:
        bid = _resolve(o["block"], local, ids_all)
        if bid not in BLOCK_TILES and bid not in [local[b["id"]] for b in mod["blocks"]]:
            raise ModError("minerai : %s n'est pas un bloc" % o["block"])
        thr = float(np.interp(o["density"], [0.0024, 0.0051, 0.009, 0.0143, 0.0258, 0.0546],
                              [0.94, 0.92, 0.90, 0.88, 0.85, 0.80]))
        ores.append((bid, 7000 + bid * 37, thr, o["max_y"], o["min_y"]))
    smelts = [(_resolve(s["input"], local, ids_all), (_resolve(s["output"], local, ids_all), s["count"]))
              for s in mod["smelting"]]
    fuels = [(_resolve(f["item"], local, ids_all), f["seconds"]) for f in mod["fuel"]]
    packed = {name: load_png_rgba(os.path.join(moddir, f)) for name, f in mod["pack"].items()}
    loaded = {}
    for t in mod["textures"]:
        name = "%s:%s" % (mid, t[:-4])
        if name not in TILES:
            loaded[name] = load_png_rgba(os.path.join(moddir, t))
    if len(TILES) + len(loaded) > 256:
        raise ModError("trop de textures (256 au total, dont %d pour le jeu de base)" % len(_BASE_SNAP["TILES"]))
    # ---- tout est valide : on applique
    TILES.update(loaded)
    TILES.update(packed)                                  # pack de textures : remplace des textures du jeu

    def tile(f):
        return "%s:%s" % (mid, f[:-4])
    for b in mod["blocks"]:
        n = local[b["id"]]
        top, bottom, side = b["faces"]
        BLOCK_TILES[n] = (tile(top), tile(bottom), tile(side))
        NAMES[n] = b["name"]
        if b["hardness"] >= 0:
            HARD[n] = b["hardness"]
        if b["tool"]:
            BTOOL[n] = b["tool"]
        if b["tier"]:
            NEED_TIER[n] = b["tier"]
        if drops[b["id"]] is not None:
            BDROP[n] = drops[b["id"]]
        BDROPN[n] = b["drop_count"]
        OPAQUE[n] = not b["transparent"]
        SAMEHIDE[n] = b["transparent"]
        LIGHTBLOCK[n] = not b["transparent"]
        SOLID[n] = b["solid"]
        if b["shape"] == "cross":                            # fleur : croix dans le monde, objet plat en main
            CUBELESS[n] = True
            CROSS[n] = True
            ITEM_TILES[n] = tile(top)
        BLOCK_ITEMS.add(n)
        CREATIVE_ITEMS.append(n)
        ids_all["%s:%s" % (mid, b["id"])] = n
    for it in mod["items"]:
        n = local[it["id"]]
        ITEM_TILES[n] = tile(it["texture"])
        NAMES[n] = it["name"]
        if it["food"]:
            FOODS[n] = it["food"]
        if it["tool"]:
            TOOLS[n] = it["tool"]
        if it["max_stack"]:
            MAXSTACK[n] = it["max_stack"]
        if it["armor"]:
            ARMOR[n] = it["armor"]
        CREATIVE_ITEMS.append(n)
        ids_all["%s:%s" % (mid, it["id"])] = n
    RECIPES.extend(recipes)
    SHAPELESS.update(shapeless)
    MOD_PLANTS.extend(plants)
    MOD_ORES.extend(ores)
    SMELT.update(dict(smelts))
    FUEL.update(dict(fuels))


def _mods_dir(world_dir):
    return os.path.join(world_dir, "mods")


def list_mods(world_dir):
    out = []
    md = _mods_dir(world_dir)
    if not os.path.isdir(md):
        return out
    disabled = set((_read_json(os.path.join(md, "state.json"), {}) or {}).get("disabled", []))
    for d in sorted(os.listdir(md)):
        j = _read_json(os.path.join(md, d, "mod.json"))
        if isinstance(j, dict):
            out.append({"id": d, "name": str(j.get("name", d))[:40], "version": str(j.get("version", ""))[:12],
                        "enabled": d not in disabled})
    return out


def mods_count(world_dir):
    return sum(1 for m in list_mods(world_dir) if m["enabled"])


def set_mod_enabled(world_dir, mid, enabled):
    p = os.path.join(_mods_dir(world_dir), "state.json")
    st = _read_json(p, {}) or {}
    dis = set(st.get("disabled", []))
    (dis.discard if enabled else dis.add)(mid)
    st["disabled"] = sorted(dis)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(st, f)


def remove_mod(world_dir, mid):
    if _ID_RE.match(mid):
        shutil.rmtree(os.path.join(_mods_dir(world_dir), mid), ignore_errors=True)


def apply_mods(world_dir):
    """Active les mods du monde. Retourne la liste des erreurs (un mod en erreur est ignore)."""
    mods_reset()
    errors = []
    md = _mods_dir(world_dir)
    reg = _read_json(os.path.join(md, "registry.json"), {}) or {}
    if not isinstance(reg.get("blocks"), dict):
        reg["blocks"] = {}
    if not isinstance(reg.get("items"), dict):
        reg["items"] = {}
    before = json.dumps(reg, sort_keys=True)
    ids_all = {}
    for info in list_mods(world_dir):
        if not info["enabled"]:
            continue
        try:
            mod = parse_mod(os.path.join(md, info["id"]))
            if mod["id"] != info["id"]:
                raise ModError("l'id du mod ne correspond pas a son dossier")
            _register_mod(mod, os.path.join(md, info["id"]), reg, ids_all)
        except ModError as e:
            errors.append("%s - %s" % (info["id"], e))
        except Exception as e:
            errors.append("%s - %s" % (info["id"], e))
    # blocs d'un mod retire ou desactive : ils restent dans le monde, affiches comme "manquants"
    for key, n in reg["blocks"].items():
        if n not in BLOCK_TILES:
            BLOCK_TILES[n] = ("missing", "missing", "missing")
            NAMES[n] = {"en": "Missing block (%s)" % key}
            HARD[n] = 1.0
            BDROP[n] = 0
            OPAQUE[n] = True
            SOLID[n] = True
            LIGHTBLOCK[n] = True
    SOLID_PY[:] = SOLID.tolist()
    if json.dumps(reg, sort_keys=True) != before:
        try:
            os.makedirs(md, exist_ok=True)
            with open(os.path.join(md, "registry.json"), "w", encoding="utf-8") as f:
                json.dump(reg, f)
        except OSError:
            pass
    build_atlas()
    return errors


# ---------------------------------------------------------------------------
# Installation d'un mod (zip, json ou dossier)
# ---------------------------------------------------------------------------
def _find_modroot(d):
    if os.path.isfile(os.path.join(d, "mod.json")):
        return d
    subs = [os.path.join(d, x) for x in os.listdir(d) if os.path.isfile(os.path.join(d, x, "mod.json"))]
    if len(subs) == 1:
        return subs[0]
    raise ModError("mod.json introuvable")


def _extract_zip(zpath, tmp):
    try:
        zf = zipfile.ZipFile(zpath)
    except Exception:
        raise ModError("archive .zip illisible")
    total = 0
    infos = zf.infolist()
    if len(infos) > 400:
        raise ModError("archive trop grosse")
    for info in infos:
        name = info.filename.replace("\\", "/")
        if info.is_dir() or not name.lower().endswith((".json", ".png")):
            continue
        parts = [p for p in name.split("/") if p not in ("", ".")]
        if not parts or ".." in parts or os.path.isabs(name) or ":" in name:
            raise ModError("archive non sure (chemin interdit)")
        total += info.file_size
        if info.file_size > 4 * 1024 * 1024 or total > 24 * 1024 * 1024:
            raise ModError("archive trop grosse")
        dest = os.path.join(tmp, *parts)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(zf.read(info))
    return _find_modroot(tmp)


def install_mod(world_dir, src):
    """Installe un mod dans le monde. Retourne (id, nom) ou leve ModError."""
    src = os.path.abspath(src)
    tmp = tempfile.mkdtemp(prefix="kc_mod_")
    try:
        jsonname = "mod.json"
        if os.path.isdir(src):
            srcdir = _find_modroot(src)
        elif src.lower().endswith(".zip"):
            srcdir = _extract_zip(src, tmp)
        elif src.lower().endswith(".json"):
            srcdir, jsonname = os.path.dirname(src), os.path.basename(src)
        else:
            raise ModError("format non pris en charge (.zip, .json ou dossier)")
        mod = parse_mod(srcdir, jsonname)
        for t in mod["files"]:
            load_png_rgba(os.path.join(srcdir, t))
        dest = os.path.join(_mods_dir(world_dir), mod["id"])
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.makedirs(dest)
        shutil.copyfile(os.path.join(srcdir, jsonname), os.path.join(dest, "mod.json"))
        for t in mod["files"]:
            shutil.copyfile(os.path.join(srcdir, t), os.path.join(dest, t))
        set_mod_enabled(world_dir, mod["id"], True)
        return mod["id"], mod["name"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Fenetre "choisir un fichier" (zenity / kdialog / tkinter, sinon navigateur integre)
# ---------------------------------------------------------------------------
_TK_SNIPPET = ("import sys\n"
               "try:\n"
               "    import tkinter\n"
               "    from tkinter import filedialog\n"
               "    r = tkinter.Tk(); r.withdraw()\n"
               "    print(filedialog.askopenfilename(title=sys.argv[1], filetypes=[('Mods', '*.zip *.json')]))\n"
               "except Exception:\n"
               "    print('__NOTK__')\n")


def start_file_dialog(title):
    cmds = []
    if shutil.which("zenity"):
        cmds.append(["zenity", "--file-selection", "--title=" + title, "--file-filter=Mods | *.zip *.json"])
    if shutil.which("kdialog"):
        cmds.append(["kdialog", "--getopenfilename", os.path.expanduser("~"), "*.zip *.json|Mods"])
    cmds.append([sys.executable, "-c", _TK_SNIPPET, title])
    for c in cmds:
        try:
            return subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    universal_newlines=True)
        except Exception:
            continue
    return None


def finish_file_dialog(proc):
    """Retourne ('ok', chemin) | ('cancel', None) | ('fallback', None)."""
    try:
        out = (proc.communicate()[0] or "").strip()
    except Exception:
        return "fallback", None
    if out == "__NOTK__":
        return "fallback", None
    if out:
        return "ok", out.splitlines()[0]
    return "cancel", None


def default_browse_dir():
    home = os.path.expanduser("~")
    for n in ("Téléchargements", "Downloads", "Bureau", "Desktop"):
        p = os.path.join(home, n)
        if os.path.isdir(p):
            return p
    return home


def list_browse_dir(path):
    """Dossiers puis fichiers .zip/.json d'un dossier (pour le navigateur integre)."""
    dirs, files = [], []
    try:
        for n in sorted(os.listdir(path), key=lambda s: s.lower()):
            if n.startswith("."):
                continue
            p = os.path.join(path, n)
            if os.path.isdir(p):
                dirs.append(n)
            elif n.lower().endswith((".zip", ".json")):
                files.append(n)
    except OSError:
        pass
    return dirs, files


# ============================================================================
# APPLICATION : menus, etats, boucle principale
# ============================================================================
LOAD_R = 4


class App:
    def __init__(self):
        os.makedirs(WORLDS_DIR, exist_ok=True)
        os.makedirs(TEXTURE_DIR, exist_ok=True)
        self.settings = load_settings()
        set_lang(self.settings["lang"])
        pygame.init()
        pygame.display.set_caption("Kurtoscraft")
        try:
            pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        except Exception:
            pass
        flags = pygame.OPENGL | pygame.DOUBLEBUF | (pygame.FULLSCREEN if FULLSCREEN else 0)
        size = (0, 0) if FULLSCREEN else (WIN_W, WIN_H)
        try:
            pygame.display.set_mode(size, flags, vsync=1)
        except TypeError:
            pygame.display.set_mode(size, flags)
        self.win_w, self.win_h = pygame.display.get_surface().get_size()
        if EXPORT_TEXTURES or "--export-textures" in sys.argv:
            export_textures()
        build_atlas()
        mods_snapshot()
        init_fonts()
        self.renderer = Renderer(self.win_w, self.win_h)
        self.gui = pygame.Surface((GUI_W, GUI_H), pygame.SRCALPHA)
        self.bg = make_dirt_bg()
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "main"
        self.return_to = "main"
        self.btns = []
        self.S = None
        self.inv = None
        self.worlds = []
        self.sel_world = -1
        self.world_scroll = 0
        self.last_click = (0, -1)
        self.confirm_delete = -1
        self.in_name = TextInput("", 24)
        self.in_seed = TextInput("", 16)
        self.focus = 0
        self.err = ""
        self.new_mode = "survival"
        self.last_space = 0.0
        self.mods_world = None
        self.mods_list = []
        self.mods_msg = ("", True)
        self.mod_errors = []
        self.picker = None
        self.br_path = ""
        self.br_dirs, self.br_files = [], []
        self.br_scroll = 0
        self.load_prog = 0.0
        self.load_t = 0.0
        self.fps = 60
        self.unload_t = 0.0

    # ---------- souris ----------
    def gui_mouse(self):
        mx, my = pygame.mouse.get_pos()
        return (mx * GUI_W / float(self.win_w), my * GUI_H / float(self.win_h))

    def set_mouse(self, grab):
        pygame.mouse.set_visible(not grab)
        pygame.event.set_grab(bool(grab))
        if grab:
            pygame.mouse.get_rel()
        else:
            pygame.mouse.set_pos((self.win_w // 2, self.win_h // 2))

    # ---------- boucle ----------
    def run(self):
        while self.running:
            dt = min(self.clock.tick(120) / 1000.0, 0.05)
            self.fps = int(self.clock.get_fps())
            for ev in pygame.event.get():
                self.handle(ev)
            self.update(dt)
            self.render()
            pygame.display.flip()
        self.shutdown()

    def shutdown(self):
        if self.S is not None:
            self.S.save()
            self.S = None
        save_settings(self.settings)

    # ---------- evenements ----------
    def handle(self, ev):
        if ev.type == pygame.QUIT:
            self.running = False
            return
        if ev.type == pygame.DROPFILE:                      # fichier glisse sur la fenetre
            if self.state in ("mods", "browser"):
                self.state = "mods"
                self.install_from(ev.file)
            return
        st = self.state
        if st == "playing":
            self.ev_playing(ev)
        elif st == "inv":
            self.ev_inv(ev)
        elif st != "loading":
            self.ev_menu(ev)

    def ev_playing(self, ev):
        S = self.S
        p = S.player
        if ev.type == pygame.KEYDOWN:
            k = ev.key
            if k == pygame.K_e and S.driving is not None and not p.dead:     # au volant : coffre / moteur du bateau
                self.open_ui("boat", S.driving)
                return
            if k == pygame.K_q and p.inv[p.sel] and p.inv[p.sel][0] == SLOT_LOCK:
                return
            if k in (pygame.K_ESCAPE, pygame.K_m):
                self.state = "pause"
                self.set_mouse(False)
            elif k == pygame.K_e:
                if S.creative:
                    self.open_creative()
                else:
                    self.open_inv(2)
            elif k == pygame.K_SPACE and p.creative:
                now = time.time()
                if now - self.last_space < 0.3:
                    p.flying = not p.flying
                    p.vy = 0.0
                self.last_space = now
            elif k == pygame.K_F3:
                S.show_debug = not S.show_debug
            elif k == pygame.K_q:
                s = p.inv[p.sel]
                if s:
                    S.drop_stack(s[0], 1)
                    S._consume_held()
            elif pygame.K_1 <= k <= pygame.K_9:
                p.sel = k - pygame.K_1
                S.name_timer = 2.0
        elif ev.type == pygame.MOUSEWHEEL:
            p.sel = (p.sel - ev.y) % 9
            S.name_timer = 2.0

    def ev_inv(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_m):
            self.close_inv()
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 3):
            shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
            self.inv.click(self.gui_mouse(), 1 if ev.button == 1 else 3, shift)
        elif ev.type == pygame.MOUSEWHEEL:
            self.inv.scroll_by(ev.y)

    def ev_menu(self, ev):
        st = self.state
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            pos = self.gui_mouse()
            for (bid, r, en) in self.btns:
                if en and inside(r, pos):
                    self.click(bid)
                    return
            if st == "worlds":
                for i in range(len(self.worlds)):
                    r = self.world_row(i)
                    if r and inside(r, pos):
                        now = time.time()
                        if self.sel_world == i and now - self.last_click[0] < 0.45:
                            self.start_session(self.worlds[i]["dir"])
                            return
                        self.sel_world = i
                        self.confirm_delete = -1
                        self.last_click = (now, i)
            elif st == "create":
                if inside((240, 112, 480, 36), pos):
                    self.focus = 0
                elif inside((240, 238, 480, 36), pos):
                    self.focus = 1
        elif ev.type == pygame.MOUSEWHEEL and st == "worlds":
            self.world_scroll = max(0, min(max(0, len(self.worlds) - 6), self.world_scroll - ev.y))
        elif ev.type == pygame.MOUSEWHEEL and st == "browser":
            total = len(self.br_dirs) + len(self.br_files)
            self.br_scroll = max(0, min(max(0, total - 11), self.br_scroll - ev.y))
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.back()
            elif st == "create":
                if ev.key == pygame.K_TAB:
                    self.focus = 1 - self.focus
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.click("create")
                else:
                    (self.in_name if self.focus == 0 else self.in_seed).key(ev)

    def world_row(self, i):
        j = i - self.world_scroll
        if 0 <= j < 6:
            return (180, 70 + j * 54, 600, 50)
        return None

    # ---------- actions des boutons ----------
    def back(self):
        st = self.state
        if st == "worlds":
            self.state = "main"
        elif st == "mods":
            self.worlds = list_worlds()
            self.state = "worlds"
        elif st == "browser":
            self.state = "mods"
        elif st == "create":
            self.state = "worlds"
        elif st in ("settings", "language"):
            save_settings(self.settings)
            self.state = self.return_to
        elif st == "pause":
            self.state = "playing"
            self.set_mouse(True)

    def click(self, bid):
        S = self.settings
        if bid == "mods":
            self.open_mods()
        elif bid == "modchoose":
            self.picker = start_file_dialog(tr("mods_browse"))
            if self.picker is None:
                self.open_browser()
            else:
                self.mods_msg = (tr("mods_waiting"), True)
        elif bid.startswith("modt:") or bid.startswith("modr:"):
            mid = bid[5:]
            wdir = os.path.join(WORLDS_DIR, self.mods_world)
            if bid.startswith("modt:"):
                cur = [m for m in self.mods_list if m["id"] == mid]
                set_mod_enabled(wdir, mid, not (cur and cur[0]["enabled"]))
            else:
                remove_mod(wdir, mid)
            self.mods_list = list_mods(wdir)
        elif bid == "brup":
            self.br_path = os.path.dirname(self.br_path) or self.br_path
            self.br_dirs, self.br_files = list_browse_dir(self.br_path)
            self.br_scroll = 0
        elif bid.startswith("br:"):
            allv = [(n, True) for n in self.br_dirs] + [(n, False) for n in self.br_files]
            i = int(bid[3:])
            if 0 <= i < len(allv):
                name, isdir = allv[i]
                if isdir:
                    self.br_path = os.path.join(self.br_path, name)
                    self.br_dirs, self.br_files = list_browse_dir(self.br_path)
                    self.br_scroll = 0
                else:
                    self.state = "mods"
                    self.install_from(os.path.join(self.br_path, name))
        elif bid == "play":
            self.worlds = list_worlds()
            self.sel_world = 0 if self.worlds else -1
            self.world_scroll = 0
            self.confirm_delete = -1
            self.state = "worlds"
        elif bid in ("settings", "language"):
            self.return_to = self.state
            self.state = bid
        elif bid == "quit":
            self.running = False
        elif bid == "back":
            self.back()
        elif bid.startswith("lang_"):
            S["lang"] = bid[5:]
            set_lang(S["lang"])
            init_fonts(S["lang"])
            save_settings(S)
        elif bid in ("rd-", "rd+"):
            opts = [2, 3, 4, 5, 6, 8, 10, 12]
            i = min(range(len(opts)), key=lambda k: abs(opts[k] - S["render"]))
            S["render"] = opts[max(0, min(len(opts) - 1, i + (1 if bid == "rd+" else -1)))]
        elif bid in ("sens-", "sens+"):
            S["sens"] = round(max(0.03, min(0.4, S["sens"] + (0.02 if bid == "sens+" else -0.02))), 2)
        elif bid in ("fov-", "fov+"):
            S["fov"] = max(50, min(100, S["fov"] + (5 if bid == "fov+" else -5)))
        elif bid == "newworld":
            self.in_name.text = tr("default_world")
            n, base = 2, self.in_name.text
            existing = {w["name"] for w in self.worlds}
            while self.in_name.text in existing:
                self.in_name.text = "%s %d" % (base, n)
                n += 1
            self.in_seed.text = ""
            self.focus = 0
            self.err = ""
            self.new_mode = "survival"
            self.state = "create"
        elif bid == "mode":
            self.new_mode = "creative" if self.new_mode == "survival" else "survival"
        elif bid == "create":
            d = create_world_files(self.in_name.text, self.in_seed.text, self.new_mode)
            if d is None:
                self.err = tr("name_taken")
            else:
                self.start_session(d)
        elif bid == "playsel":
            if 0 <= self.sel_world < len(self.worlds):
                self.start_session(self.worlds[self.sel_world]["dir"])
        elif bid == "delete":
            if 0 <= self.sel_world < len(self.worlds):
                if self.confirm_delete == self.sel_world:
                    shutil.rmtree(os.path.join(WORLDS_DIR, self.worlds[self.sel_world]["dir"]), ignore_errors=True)
                    self.worlds = list_worlds()
                    self.sel_world = min(self.sel_world, len(self.worlds) - 1)
                    self.confirm_delete = -1
                else:
                    self.confirm_delete = self.sel_world
        elif bid == "resume":
            self.back()
        elif bid == "savequit":
            self.quit_to_title()
        elif bid == "respawn":
            self.S.respawn()
            self.state = "playing"
            self.set_mouse(True)

    # ---------- mods ----------
    def open_mods(self):
        if not (0 <= self.sel_world < len(self.worlds)):
            return
        self.mods_world = self.worlds[self.sel_world]["dir"]
        self.mods_list = list_mods(os.path.join(WORLDS_DIR, self.mods_world))
        self.mods_msg = ("", True)
        self.state = "mods"

    def install_from(self, path):
        wdir = os.path.join(WORLDS_DIR, self.mods_world)
        try:
            mid, name = install_mod(wdir, path)
            self.mods_msg = (tr("mods_ok") % name, True)
        except ModError as e:
            self.mods_msg = (tr("mods_fail") % e, False)
        except Exception as e:
            self.mods_msg = (tr("mods_fail") % e, False)
        self.mods_list = list_mods(wdir)

    def open_browser(self):
        self.br_path = default_browse_dir()
        self.br_dirs, self.br_files = list_browse_dir(self.br_path)
        self.br_scroll = 0
        self.state = "browser"

    def start_session(self, dirname):
        try:
            self.mod_errors = apply_mods(os.path.join(WORLDS_DIR, dirname))
            self.renderer.reload_atlas()
            clear_icon_cache()
            self.S = Session(dirname, self.settings)
        except Exception as e:
            self.err = str(e)
            mods_reset()
            self.renderer.reload_atlas()
            return
        self.state = "loading"
        self.load_t = 0.0
        self.load_prog = 0.0

    def quit_to_title(self):
        if self.S is not None:
            self.S.save()
            for ch in self.S.world.chunks.values():
                self.renderer.free_chunk(ch)
            self.S = None
        self.inv = None
        mods_reset()                         # le monde suivant n'a pas forcement les memes mods
        self.renderer.reload_atlas()
        clear_icon_cache()
        self.state = "main"
        self.set_mouse(False)

    def open_inv(self, n):
        self.inv = InvScreen(self.S, n)
        self.S.ui_open = True
        self.state = "inv"
        self.set_mouse(False)

    def open_ui(self, kind, pos):
        S = self.S
        if kind == "table":
            self.inv = InvScreen(S, 3)
        elif kind == "naval":
            self.inv = InvScreen(S, 5)
        elif kind == "boat":
            self.inv = BoatScreen(S, pos)
        elif kind == "chest":
            self.inv = ChestScreen(S, pos)
        else:
            self.inv = FurnaceScreen(S, pos)
        S.ui_open = True
        self.state = "inv"
        self.set_mouse(False)

    def open_creative(self):
        self.inv = CreativeScreen(self.S)
        self.S.ui_open = True
        self.state = "inv"
        self.set_mouse(False)

    def close_inv(self):
        self.inv.close()
        self.inv = None
        self.S.ui_open = False
        self.state = "playing"
        self.set_mouse(True)

    # ---------- mise a jour ----------
    def update(self, dt):
        st = self.state
        S = self.S
        if self.picker is not None and self.picker.poll() is not None:
            status, path = finish_file_dialog(self.picker)
            self.picker = None
            if status == "ok":
                self.install_from(path)
            elif status == "fallback":
                self.open_browser()
            else:
                self.mods_msg = ("", True)
        if st == "loading":
            self.load_t += dt
            S.stream(self.renderer, 0.03, LOAD_R)
            self.load_prog = S.progress(LOAD_R)
            if self.load_prog >= 1.0 and self.load_t > 0.6:
                S.finish_loading()
                self.state = "playing"
                self.set_mouse(True)
                if self.mod_errors:
                    S.msg(tr("mods_fail") % self.mod_errors[0], 9.0)
        elif st in ("playing", "inv"):
            p = S.player
            keys = {}
            if st == "playing":
                dx, dy = pygame.mouse.get_rel()
                sens = self.settings["sens"]
                p.yaw = (p.yaw + dx * sens) % 360.0
                p.pitch = max(-89.9, min(89.9, p.pitch - dy * sens))
                pr = pygame.key.get_pressed()
                keys = {"fwd": pr[pygame.K_w], "back": pr[pygame.K_s], "left": pr[pygame.K_a],
                        "right": pr[pygame.K_d], "jump": pr[pygame.K_SPACE],
                        "sneak": pr[pygame.K_LSHIFT] or pr[pygame.K_RSHIFT],
                        "sprint": pr[pygame.K_LCTRL] or pr[pygame.K_RCTRL]}
                mb = pygame.mouse.get_pressed()
                lmb, rmb = mb[0], mb[2]
            else:
                lmb = rmb = False
            S.update(dt, keys, lmb, rmb)
            if S.want_ui:
                kind, pos = S.want_ui
                S.want_ui = None
                self.open_ui(kind, pos)
            S.stream(self.renderer, 0.006)
            self.unload_t += dt
            if self.unload_t > 2.0:
                self.unload_t = 0.0
                S.unload_far(self.renderer)
            if p.dead and self.state in ("playing", "inv"):
                if self.state == "inv":
                    self.inv.close()
                    self.inv = None
                    S.ui_open = False
                S.on_death()
                self.state = "dead"
                self.set_mouse(False)

    # ---------- dessin ----------
    def btn(self, g, bid, r, label, enabled=True, size="m"):
        hover = enabled and inside(r, self.gui_mouse())
        draw_button(g, r, label, hover, enabled, size)
        self.btns.append((bid, r, enabled))

    def title(self, g, s, y=24):
        draw_text(g, s, "l", (255, 255, 255), (GUI_W // 2, y), "c")

    def render(self):
        R, st, S = self.renderer, self.state, self.S
        g = self.gui
        self.btns = []
        if S is not None and st in ("playing", "pause", "inv", "dead"):
            R.render_world(S)
            g.fill((0, 0, 0, 0))
            draw_hud(g, S, self.fps)
            if st != "playing":
                dim = pygame.Surface((GUI_W, GUI_H), pygame.SRCALPHA)
                dim.fill((120, 0, 0, 140) if st == "dead" else (0, 0, 0, 110))
                g.blit(dim, (0, 0))
            if st == "inv":
                self.inv.draw(g, self.gui_mouse())
            elif st == "pause":
                self.draw_pause(g)
            elif st == "dead":
                draw_text(g, tr("you_died"), "xl", (255, 255, 255), (GUI_W // 2, 130), "c")
                self.btn(g, "respawn", (330, 280, 300, 44), tr("respawn"))
        else:
            R.clear_2d((0.0, 0.0, 0.0))
            g.blit(self.bg, (0, 0))
            if st == "main":
                self.draw_main(g)
            elif st == "worlds":
                self.draw_worlds(g)
            elif st == "create":
                self.draw_create(g)
            elif st == "settings":
                self.draw_settings(g)
            elif st == "language":
                self.draw_language(g)
            elif st == "mods":
                self.draw_mods(g)
            elif st == "browser":
                self.draw_browser(g)
            elif st == "loading":
                self.draw_loading(g)
        R.draw_gui(g)

    def draw_main(self, g):
        for k, c in enumerate([(30, 30, 30), (70, 70, 70), (214, 214, 214)]):
            off = [(6, 6), (3, 3), (0, 0)][k]
            draw_text(g, "KURTOSCRAFT", "title", c, (GUI_W // 2 + off[0], 40 + off[1]), "c", False)
        draw_text(g, "Python + pygame", "m", (255, 255, 90), (GUI_W // 2 + 170, 150), "c")
        self.btn(g, "play", (310, 220, 340, 44), tr("play"))
        self.btn(g, "settings", (310, 276, 340, 44), tr("settings"))
        self.btn(g, "language", (310, 332, 340, 44), tr("language"))
        self.btn(g, "quit", (380, 420, 200, 36), tr("quit"), True, "s")
        draw_text(g, "Kurtoscraft", "s", (200, 200, 200), (8, GUI_H - 22))

    def draw_worlds(self, g):
        self.title(g, tr("select_world"))
        draw_panel_dark(g, (170, 62, 620, 330))
        if not self.worlds:
            draw_text(g, tr("no_worlds"), "m", (200, 200, 200), (GUI_W // 2, 210), "c")
        for i, wd in enumerate(self.worlds):
            r = self.world_row(i)
            if not r:
                continue
            if i == self.sel_world:
                pygame.draw.rect(g, (255, 255, 255), (r[0] - 2, r[1] - 2, r[2] + 4, r[3] + 4), 2)
            pygame.draw.rect(g, (20, 20, 20), r)
            draw_text(g, wd.get("name", "?"), "m", (255, 255, 255), (r[0] + 10, r[1] + 6), "l", False)
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(wd.get("last_played", 0)))
            mode = tr("creative") if wd.get("mode") == "creative" else tr("survival")
            extra = ("  -  %d mod" % wd["mods_n"] + ("s" if wd["mods_n"] > 1 else "")) if wd.get("mods_n") else ""
            draw_text(g, "%s - %s: %s   (seed %s)%s" % (mode, tr("last_played"), when, wd.get("seed"), extra), "s",
                      (150, 150, 150), (r[0] + 10, r[1] + 29), "l", False)
        ok = 0 <= self.sel_world < len(self.worlds)
        self.btn(g, "playsel", (170, 404, 300, 40), tr("play_selected"), ok)
        self.btn(g, "newworld", (490, 404, 300, 40), tr("new_world"))
        dl = tr("confirm_delete") if (ok and self.confirm_delete == self.sel_world) else tr("delete_world")
        self.btn(g, "mods", (170, 456, 150, 40), tr("mods"), ok)
        self.btn(g, "delete", (335, 456, 290, 40), dl, ok, "s" if self.confirm_delete == self.sel_world else "m")
        self.btn(g, "back", (640, 456, 150, 40), tr("back"))
        if self.err:
            draw_text(g, self.err, "s", (255, 120, 120), (GUI_W // 2, 510), "c")

    def draw_create(self, g):
        self.title(g, tr("create_title"))
        draw_text(g, tr("world_name"), "m", (200, 200, 200), (240, 86), "l")
        self.in_name.draw(g, (240, 112, 480, 36), self.focus == 0)
        self.btn(g, "mode", (240, 162, 480, 42),
                 tr("mode_creative") if self.new_mode == "creative" else tr("mode_survival"))
        draw_text(g, tr("seed"), "m", (200, 200, 200), (240, 216), "l")
        self.in_seed.draw(g, (240, 238, 480, 36), self.focus == 1)
        self.btn(g, "create", (240, 322, 480, 44), tr("create_world"), bool(self.in_name.text.strip()))
        self.btn(g, "back", (240, 376, 480, 40), tr("back"))
        if self.err:
            draw_text(g, self.err, "m", (255, 120, 120), (GUI_W // 2, 432), "c")

    def draw_settings(self, g):
        self.title(g, tr("settings") + " - " + tr("controls"))
        y = 80
        for (key, acts) in CONTROLS:
            draw_text(g, key, "m", (255, 230, 90), (110, y), "l")
            draw_text(g, acts[LANGS.index(_lang[0])], "m", (235, 235, 235), (270, y), "l")
            y += 30
        S = self.settings
        x = 700
        draw_text(g, "%s: %d" % (tr("render_dist"), S["render"]), "m", (255, 255, 255), (x + 50, 90), "c")
        self.btn(g, "rd-", (x, 116, 44, 32), "-")
        self.btn(g, "rd+", (x + 56, 116, 44, 32), "+")
        draw_text(g, "%s: %.2f" % (tr("sens"), S["sens"]), "m", (255, 255, 255), (x + 50, 175), "c")
        self.btn(g, "sens-", (x, 201, 44, 32), "-")
        self.btn(g, "sens+", (x + 56, 201, 44, 32), "+")
        draw_text(g, "FOV: %d" % S["fov"], "m", (255, 255, 255), (x + 50, 260), "c")
        self.btn(g, "fov-", (x, 286, 44, 32), "-")
        self.btn(g, "fov+", (x + 56, 286, 44, 32), "+")
        self.btn(g, "back", (310, 480, 340, 40), tr("back"))

    def draw_language(self, g):
        self.title(g, tr("language"))
        for i, code in enumerate(LANGS):
            label = LANG_LABEL[code]
            if code == self.settings["lang"]:
                label = "> " + label + " <"
            r = (330, 72 + i * 50, 300, 42)
            self.btn(g, "lang_" + code, r, "")
            f = lang_font(code)
            hover = inside(r, self.gui_mouse())
            img = f.render(label, True, (255, 255, 160) if hover else (235, 235, 235))
            sh = f.render(label, True, (40, 40, 40))
            tx, ty = r[0] + (r[2] - img.get_width()) // 2, r[1] + (r[3] - img.get_height()) // 2 + 1
            g.blit(sh, (tx + 2, ty + 2))
            g.blit(img, (tx, ty))
        self.btn(g, "back", (330, 440, 300, 40), tr("back"))

    def draw_mods(self, g):
        self.title(g, tr("mods_title"), 14)
        wname = ""
        for wd in self.worlds:
            if wd.get("dir") == self.mods_world:
                wname = wd.get("name", "")
        draw_text(g, "%s: %s" % (tr("mods_world"), wname), "s", (200, 200, 200), (GUI_W // 2, 52), "c")
        draw_panel_dark(g, (180, 76, 600, 104))
        dashed_rect(g, (190, 84, 580, 88), (150, 150, 150))
        draw_text(g, tr("mods_drop"), "m", (235, 235, 235), (GUI_W // 2, 112), "c")
        draw_text(g, "mod.json + *.png", "s", (150, 150, 150), (GUI_W // 2, 146), "c")
        self.btn(g, "modchoose", (180, 190, 600, 38), tr("mods_choose"), self.picker is None)
        msg, ok = self.mods_msg
        if msg:
            draw_text(g, msg[:110], "s", (140, 255, 140) if ok else (255, 130, 130), (GUI_W // 2, 238), "c")
        draw_panel_dark(g, (180, 260, 600, 176))
        if not self.mods_list:
            draw_text(g, tr("mods_none"), "m", (190, 190, 190), (GUI_W // 2, 335), "c")
        for i, m in enumerate(self.mods_list[:4]):
            y = 264 + i * 42
            draw_text(g, ("%s  %s" % (m["name"], m["version"]))[:34], "m", (255, 255, 255), (196, y + 10), "l", False)
            self.btn(g, "modt:" + m["id"], (500, y + 2, 130, 34),
                     tr("mods_on") if m["enabled"] else tr("mods_off"), True, "s")
            self.btn(g, "modr:" + m["id"], (640, y + 2, 130, 34), tr("mods_remove"), True, "s")
        draw_text(g, tr("mods_note"), "s", (170, 170, 170), (GUI_W // 2, 446), "c")
        self.btn(g, "back", (330, 474, 300, 40), tr("back"))

    def draw_browser(self, g):
        self.title(g, tr("mods_browse"), 14)
        draw_text(g, self.br_path[-90:], "s", (200, 200, 200), (GUI_W // 2, 54), "c")
        self.btn(g, "brup", (180, 74, 220, 30), tr("mods_up"), True, "s")
        draw_panel_dark(g, (180, 110, 600, 346))
        allv = [(n, True) for n in self.br_dirs] + [(n, False) for n in self.br_files]
        for j, (name, isdir) in enumerate(allv[self.br_scroll:self.br_scroll + 11]):
            i = j + self.br_scroll
            self.btn(g, "br:%d" % i, (186, 114 + j * 31, 588, 29), ("[ %s ]" % name) if isdir else name, True, "s")
        self.btn(g, "back", (330, 474, 300, 40), tr("back"))

    def draw_pause(self, g):
        draw_text(g, tr("game_menu"), "l", (255, 255, 255), (GUI_W // 2, 110), "c")
        self.btn(g, "resume", (330, 170, 300, 42), tr("resume"))
        self.btn(g, "settings", (330, 224, 300, 42), tr("settings"))
        self.btn(g, "language", (330, 278, 300, 42), tr("language"))
        self.btn(g, "savequit", (330, 350, 300, 42), tr("save_quit"))

    def draw_loading(self, g):
        draw_text(g, tr("loading"), "l", (255, 255, 255), (GUI_W // 2, 170), "c")
        draw_text(g, "%s  %d%%" % (tr("generating"), int(self.load_prog * 100)), "m", (210, 210, 210),
                  (GUI_W // 2, 214), "c")
        cx, cy = GUI_W // 2, 300
        n = 12
        head = (self.load_t * 10.0) % n
        for i in range(n):
            a = i * math.tau / n
            v = ((head - i) % n) / float(n)
            c = int(255 * (1.0 - v) ** 2) + 30
            c = min(255, c)
            pygame.draw.circle(g, (c, c, c), (int(cx + math.cos(a) * 30), int(cy + math.sin(a) * 30)),
                               6 if v < 0.25 else 4)
        pygame.draw.rect(g, (0, 0, 0), (GUI_W // 2 - 152, 372, 304, 22))
        pygame.draw.rect(g, (60, 60, 60), (GUI_W // 2 - 150, 374, 300, 18))
        pygame.draw.rect(g, (90, 210, 90), (GUI_W // 2 - 150, 374, int(300 * min(1.0, self.load_prog)), 18))


def dashed_rect(g, r, color):
    x, y, w, h = r
    for k in range(0, w, 14):
        pygame.draw.rect(g, color, (x + k, y, 8, 2))
        pygame.draw.rect(g, color, (x + k, y + h - 2, 8, 2))
    for k in range(0, h, 14):
        pygame.draw.rect(g, color, (x, y + k, 2, 8))
        pygame.draw.rect(g, color, (x + w - 2, y + k, 2, 8))


def draw_panel_dark(g, r):
    pygame.draw.rect(g, (0, 0, 0), r)
    pygame.draw.rect(g, (40, 40, 40), (r[0] + 2, r[1] + 2, r[2] - 4, r[3] - 4))


def main():
    app = None
    try:
        app = App()
        app.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
