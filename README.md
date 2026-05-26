
# Documentation – mini moteur de jeu 2D en python pour calculatrice Numworks

## Présentation

Ce script implémente un **moteur de jeu 2D** optimisé pour les calculatrices **NumWorks**.  
Il permet :

* d’afficher des **sprites statiques ou animés**
* de gérer un **rendu optimisé** (dessin uniquement des pixels modifiés)
* d’exécuter une **boucle de jeu fluide**
* d’ajouter des **scripts de comportement** (gravité, déplacement, etc.)

Le moteur est conçu pour **limiter l’usage mémoire** et **éviter les appels C coûteux** (`get_pixel`) mais ne permet tout de même pas de créer un jeu compliqué dessus, il est sert de base. 
N'hésitez pas à le modifier !

Le but ici **n'est pas de créer un moteur de jeu en tant que tel** mais de comprendre **comment optimiser un programme python avec des structures de données adaptés**.

/!\ ***Attention***, les attributs sont tous publiques, c'est fait pour pouvoir les modifier dans le code d'exemple si celui-ci est à part. Suivant vos besoins modifiez ceci.

***

## Dépendances

```python
from kandinsky import fill_rect
from math import sin, pi
from time import sleep, monotonic
from ion import *
```

| Module      | Rôle                              |
| ----------- | --------------------------------- |
| `kandinsky` | Dessin de rectangles (pixels)     |
| `math`      | Génération de palette de couleurs |
| `time`      | Gestion du temps et FPS           |
| `ion`       | Gestion du clavier                |

***

## Configuration globale

### `LightMode`

```python
LightMode = True
```

| Valeur  | Effet                                                    |
| ------- | -------------------------------------------------------- |
| `True`  | Redessine tout à chaque frame (plus simple, plus rapide) |
| `False` | Compare les pixels précédents (économie CPU/mémoire)     |

***

## Palette de couleurs globale

```python
_COLORS = {}
```

* Générée dynamiquement avec des fonctions sinus
* Indexée de `0` à `9`
* Partagée entre tous les sprites (**pas de copie**)

si les couleurs ne vous conviennent pas vous pouvez les modifier directement ou utiliser une fonction qui vous permettra de générer les couleurs que vous souhaitez.

| Index | Couleur               |
| ----- | --------------------- |
| `0–7` | Dégradé RGB           |
| `8`   | Noir `(0,0,0)`        |
| `9`   | Blanc `(255,255,255)` |

***

## Classe `Sprite`

###  Description

Représente un **sprite statique** affichable sur la grille.

###  Responsabilités

* Décoder une image texte → pixels
* Mettre en cache le résultat pour améliorer les performances
* Gérer position et dimensions

###  Constructeur

```python
Sprite(image, x=0, y=0, w=0, h=0)
```

| Paramètre | Description                               |
| --------- | ----------------------------------------- |
| `image`   | Chaîne représentant l’image (`"9298929"`) |
| `x, y`    | Position sur la grille                    |
| `w, h`    | Largeur / hauteur du sprite               |

***

###  `decodeImage(posX, posY)`

```python
sprite.decodeImage(x, y)
```

Convertit l’image texte en une liste de pixels :

```python
(x, y, (R, G, B))
```

Utilise un **cache** pour éviter de recalculer inutilement  
Optimisé avec références locales (`append`)

***

### `SetImage(image)`

Change l’image du sprite.

***

## Classe `AnimatedSprite`

### Description

Extension de `Sprite` permettant de gérer des **animations image par image**.

### Fonctionnalités

* Plusieurs séquences d’animation
* Changement automatique d’image à chaque frame

### Constructeur

```python
AnimatedSprite(images, x, y, w, h)
```

| Paramètre | Description                               |
| --------- | ----------------------------------------- |
| `images`  | Liste de séquences (`[[frame1, frame2]]`) |

***

### `Animate(seq=0)`

* Sélectionne la séquence `seq`
* Change d’image
* Retourne les pixels décodés du sprite courant

***

## Classe `Canva`

### Description

Gère **l’affichage à l’écran** et l’optimisation du rendu.

### Rôles

* Stocker les sprites
* Détecter les pixels modifiés
* Dessiner uniquement ce qui change

***

### `addSprite(sprite)`

Ajoute un sprite (dessiné **au-dessus** des autres).

### `removeSprite(index=-1)`

Supprime un sprite.

***

### `genScreen()`

* Met à jour la matrice `mat`
* Compare les couleurs pixel par pixel
* Ne modifie que les pixels nécessaires

***

### `drawScreen()`

* Dessine les pixels avec `fill_rect`
* Compare avec `prev` si `LightMode == False`
* Évite les appels inutiles

***

## Classe `GameEngine`

### Description

Cœur du moteur de jeu.

### Gère

* L’écran (`Canva`)
* Les scripts
* La boucle principale
* Le joueur (optionnel)

***

### `update()`

* Met à jour les sprites
* Dessine l’écran

***

### `mainLoop(condition_fn, updateDelay=0, Scripts=None)`

Boucle principale du jeu.

| Paramètre      | Description                        |
| -------------- | ---------------------------------- |
| `condition_fn` | Fonction de sortie (`True = stop`) |
| `updateDelay`  | Délai entre les frames             |
| `Scripts`      | Liste de scripts à exécuter        |

Affiche les FPS (cette partie est commenté,peut être retirer tout comme le calcul des FPS)
Protégé contre surcharge CPU

***

## Classe `GravityScript`

### Description

Script simulant une **gravité simple**.

### Fonctionnement

* Saut avec `KEY_UP`
* Gravité progressive
* Position Y flottante pour plus de précision

Peu adapté aux petites grilles

***

## Classe `MoveScript`

### Description

Script de déplacement horizontal.

### Contrôles

| Touche | Action             |
| ------ | ------------------ |
| ←      | Déplacement gauche |
| →      | Déplacement droite |

***

## Exemple d’utilisation

ceci est exemple, il représente des yeux animés sur un font noir qui regardent de gauche à droite et qui peuvent se déplacer et sauter,
le background est **lourd pour une calculatrice** mais on peut utiliser d'autres méthodes pour faire le même effet.

```python
backgroungSprite = "8"*768
animation_1      = [["9298929", "9928992", "9928992", "9298929",
                      "9298929", "2998299", "2998299", "9298929"]]

sprite_animated_1 = AnimatedSprite(animation_1, 0, 0, 7, 1)
background = Sprite(backgroungSprite, 0, 0, 32, 24)

g = GameEngine(240, 320, 10)
Scripts = [GravityScript(sprite_animated_1), MoveScript(sprite_animated_1)]
g.screen.addSprite(background)
g.screen.addSprite(sprite_animated_1)
try:
    g.mainLoop(lambda: keydown(KEY_BACKSPACE), 0.1, Scripts)
except MemoryError:
    print("/!\ \nle script que vous avez fais\nest trop lourd\n/!\ ")

```

Quitter avec **BACKSPACE**  
Gestion d’erreur mémoire incluse

***
