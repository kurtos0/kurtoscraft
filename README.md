# KURTOSCRAFT

**Kurtoscraft** est un jeu de type bac à sable en 3D, développé en Python avec Pygame, NumPy et OpenGL.

> Version annoncée dans le fichier : `beta-v0.2`.  
> Le fichier fourni porte le nom `kurtoscraft-beta_v0.1.5.py` : pense à harmoniser le nom du fichier et la version affichée avant une publication GitHub.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Configuration requise](#configuration-requise)
- [Installation](#installation)
- [Lancement](#lancement)
- [Commandes](#commandes)
- [Langues](#langues)
- [Sauvegardes et textures](#sauvegardes-et-textures)
- [Installer et gérer des mods](#installer-et-gérer-des-mods)
- [Créer un mod](#créer-un-mod)
- [Dépannage](#dépannage)
- [Contribuer](#contribuer)

## Fonctionnalités

- Monde 3D avec génération de terrain.
- Modes Survie et Créatif.
- Inventaire, fabrication, outils, armures et cuisson.
- Biomes, villages, structures et dimensions.
- Bateaux et navigation.
- Sauvegarde des mondes.
- Textures personnalisables.
- Système de mods installé monde par monde.

La liste exacte des fonctionnalités peut évoluer avec les versions bêta.

## Configuration requise

- Python 3.
- Une carte graphique et des pilotes compatibles OpenGL.
- Les bibliothèques Python suivantes :
  - `pygame`
  - `numpy`
  - `PyOpenGL`

Le jeu a été développé et utilisé sous Linux Mint. Les commandes ci-dessous sont données pour Linux Mint / Ubuntu.

## Installation

### 1. Installer Python et les outils nécessaires

Ouvre un terminal dans le dossier du projet et exécute :

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

### 2. Créer un environnement Python

Depuis le dossier où se trouve le fichier du jeu :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les bibliothèques

```bash
python -m pip install --upgrade pip
python -m pip install pygame numpy PyOpenGL
```

Pour les installations où pip ne peut pas installer les paquets graphiques, les paquets système Linux Mint peuvent aussi être utilisés :

```bash
sudo apt install python3-pygame python3-numpy python3-opengl
```

Il est préférable de choisir une seule méthode d'installation pour éviter de mélanger les paquets du système et ceux de l'environnement virtuel.

## Lancement

Dans le terminal, depuis le dossier du jeu :

```bash
source .venv/bin/activate
python kurtoscraft.py
```

Remplace `kurtoscraft.py` par le nom réel du fichier Python si tu ne l'as pas renommé.

Pour quitter l'environnement virtuel :

```bash
deactivate
```

## Commandes

| Touche / action | Fonction |
|---|---|
| `W A S D` | Se déplacer |
| `Espace` | Sauter / nager vers le haut |
| `Maj` (`Shift`) | Marcher lentement / descendre d'un bateau |
| `Ctrl` | Courir |
| Souris | Regarder autour de soi |
| Clic gauche maintenu | Casser un bloc / attaquer |
| Clic droit | Poser un bloc / utiliser / manger |
| `1` à `9` / molette | Choisir un emplacement de la barre rapide |
| `E` | Inventaire et fabrication |
| Double appui sur `Espace` | Voler en mode Créatif |
| `Q` | Jeter l'objet |
| `M` ou `Échap` | Ouvrir le menu du jeu |
| `F3` | Afficher les informations de débogage |

Les commandes affichées dans le menu du jeu restent la référence si elles changent dans une version ultérieure.

## Langues

La sélection de langue est accessible depuis le menu principal ou le menu de pause.

Langues proposées :

| Code | Langue |
|---|---|
| `en` | English |
| `fr` | Français |
| `de` | Deutsch |
| `es` | Español |
| `it` | Italiano |
| `ru` | Русский |
| `th` | ไทย |

La langue par défaut définie dans le code est le français.

## Sauvegardes et textures

Les données du jeu sont enregistrées dans le dossier :

```text
~/.kurtoscraft/
```

Les mondes se trouvent dans :

```text
~/.kurtoscraft/worlds/
```

Les textures personnelles peuvent être placées dans :

```text
~/.kurtoscraft/textures/
```

Utilise des images PNG de **16 × 16 pixels**. Le nom du fichier doit correspondre au nom de texture attendu par le jeu. Les textures de base sont normalement générées par le code : aucun pack d'images externe n'est nécessaire pour démarrer.

Pense à sauvegarder tes mondes avant de tester des mods ou des versions expérimentales.

## Installer et gérer des mods

Le jeu accepte trois formes de mods :

- une archive `.zip` ;
- un fichier `mod.json` ;
- un dossier contenant `mod.json` et les textures nécessaires.

### Installation depuis le jeu

1. Lance Kurtoscraft.
2. Choisis le monde concerné.
3. Ouvre la rubrique **Mods** de ce monde.
4. Choisis le fichier du mod (`.zip` ou `.json`) avec le navigateur de fichiers.
5. Vérifie que le mod apparaît dans la liste.

Le menu permet ensuite d'activer ou de désactiver un mod, ou de le supprimer.

**Important :** les mods sont associés à un monde précis. Un mod installé dans un monde n'est pas automatiquement installé dans les autres. Les changements prennent effet au chargement du monde ; quitte puis recharge le monde après avoir modifié les mods.

### Structure d'une archive ZIP

Le ZIP doit contenir un dossier de mod avec `mod.json` et les images PNG nécessaires. Exemple :

```text
mon_mod.zip
└── MonMod/
    ├── mod.json
    ├── bloc.png
    └── objet.png
```

Le programme recherche le dossier contenant le fichier `mod.json`. Les archives sont contrôlées : les chemins dangereux sont refusés et la taille est limitée (4 Mio par fichier et 24 Mio au total).

## Créer un mod

Un mod simple contient au minimum un fichier `mod.json` et ses textures PNG.

### Exemple : ajouter un bloc

Crée un dossier nommé `mon_mod` :

```text
mon_mod/
├── mod.json
└── bloc_bleu.png
```

Crée `mod.json` avec ce contenu :

```json
{
  "id": "mon_mod",
  "name": "Mon premier mod",
  "version": "1.0",
  "blocks": [
    {
      "id": "bloc_bleu",
      "name": {
        "en": "Blue Block",
        "fr": "Bloc bleu"
      },
      "texture": "bloc_bleu.png",
      "hardness": 1.5,
      "tool": null,
      "tier": 0,
      "drop": "self",
      "drop_count": [1, 1],
      "transparent": false,
      "solid": true,
      "shape": "cube"
    }
  ]
}
```

`bloc_bleu.png` doit être une image PNG de 16 × 16 pixels.

Compresse ensuite le dossier `mon_mod` en ZIP, puis installe l'archive depuis le menu Mods du monde.

### Identifiants

- L'identifiant du mod et ceux de ses blocs/objets doivent utiliser uniquement des lettres minuscules (`a-z`), des chiffres (`0-9`) et `_`.
- Un identifiant doit comporter entre 2 et 32 caractères.
- Les identifiants des blocs et objets doivent être uniques dans le mod.
- Pour référencer un élément d'un mod, utilise `id_du_mod:id_de_l_element`, par exemple `mon_mod:bloc_bleu`.

### Éléments pris en charge

Le format de mod actuel permet de déclarer :

| Clé JSON | Utilité |
|---|---|
| `blocks` | Ajouter des blocs et leurs propriétés |
| `items` | Ajouter des objets, nourriture, outils ou armures |
| `recipes` | Ajouter des recettes de fabrication |
| `ores` | Faire apparaître des minerais dans le terrain |
| `plants` | Faire apparaître des blocs végétaux |
| `smelting` | Ajouter des recettes de cuisson |
| `fuel` | Ajouter des combustibles |
| `texture_pack` | Remplacer certaines textures du jeu |

Les sections sont facultatives : un mod peut n'en utiliser qu'une partie.

### Exemple d'objet

Ajoute une image `pomme_bleue.png` de 16 × 16 pixels et ajoute cette entrée dans la liste `items` de `mod.json` :

```json
{
  "id": "pomme_bleue",
  "name": {
    "en": "Blue Apple",
    "fr": "Pomme bleue"
  },
  "texture": "pomme_bleue.png",
  "food": 5,
  "max_stack": 64
}
```

`food` indique la valeur de nourriture. `max_stack` définit la taille maximale de la pile.

### Exemple de recette

Les recettes utilisent une grille de 1 à 3 lignes et de 1 à 3 caractères par ligne. Chaque caractère utilisé doit être défini dans `key`.

```json
{
  "pattern": [
    " A ",
    " A ",
    "   "
  ],
  "key": {
    "A": "mon_mod:bloc_bleu"
  },
  "result": "mon_mod:pomme_bleue",
  "count": 1,
  "shapeless": false
}
```

Dans cet exemple, la recette utilise deux blocs bleus placés verticalement. Pour une recette sans disposition imposée, passe `shapeless` à `true`.

### Propriétés utiles d'un bloc

- `texture` : même image sur les six faces.
- `textures` : permet de préciser `all`, ou séparément `top`, `bottom` et `side`.
- `hardness` : résistance à la casse.
- `tool` : outil requis (`pickaxe`, `axe`, `shovel` ou `sword`).
- `tier` : niveau d'outil requis, de 1 à 4.
- `drop` : `self` pour laisser tomber le bloc lui-même, `none` pour ne rien laisser tomber, ou l'identifiant d'un objet/bloc.
- `drop_count` : quantité minimale et maximale, par exemple `[1, 2]`.
- `transparent` : indique si le bloc est transparent.
- `solid` : indique si le joueur peut être bloqué par le bloc.
- `shape` : `cube` ou `cross`.

### Limites du format actuel

Le chargeur impose notamment des plafonds par mod : 40 blocs, 60 objets, 100 recettes, 20 minerais, 40 recettes de cuisson, 20 combustibles et 40 plantes. Les textures du jeu et des mods sont soumises à une limite globale de 256 entrées.

Les mods ajoutent du contenu via le format JSON prévu par le jeu. Ce n'est pas un système permettant d'exécuter librement du code Python : ne place pas de scripts Python dans un mod et n'en attends pas l'exécution.

## Dépannage

### `ModuleNotFoundError`

Vérifie que l'environnement virtuel est activé, puis réinstalle les bibliothèques :

```bash
source .venv/bin/activate
python -m pip install pygame numpy PyOpenGL
```

### Erreur OpenGL ou fenêtre noire

Vérifie que les pilotes graphiques sont installés et que ton système prend en charge OpenGL. Une session distante ou une machine virtuelle peut ne pas fournir l'accélération graphique nécessaire.

### Le mod ne s'installe pas

- Vérifie que le fichier s'appelle bien `mod.json`.
- Vérifie que le JSON est valide (virgules, guillemets et accolades).
- Vérifie que tous les PNG indiqués existent et sont bien des fichiers PNG.
- Vérifie les identifiants et les références aux blocs/objets.
- Vérifie les limites de taille de l'archive.

## Contribuer

Les contributions, rapports de bugs et idées d'amélioration sont les bienvenus.

Avant d'envoyer une modification :
1. teste le lancement du jeu ;
2. teste la création et le chargement d'un monde ;
3. vérifie les sauvegardes ;
4. teste les mods concernés si tu modifies leur système.

---

**Kurtoscraft — projet indépendant en développement.**
