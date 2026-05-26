from kandinsky import fill_rect
from math import sin, pi
from time import sleep, monotonic
from ion import *

global LightMode
LightMode = True #variable qui définit si on utilise ou non le deuxième dictionnaire (perte de mémoire)

# Palette globale partagée
_COLORS = {}
for _i in range(8):
    _COLORS[_i] = (
        int(255 * sin(_i / 8 * pi)),
        int(255 * sin(_i / 8 * pi + (1 / 4) * pi / 3)),
        int(255 * sin(_i / 8 * pi + 1 * pi / 3)),
    )
_COLORS[8] = (0, 0, 0)
_COLORS[9] = (255, 255, 255)


class Sprite:
    """
    classe principale, permet de:
    - générer un sprite affichable sur la grille principale
    """
    def __init__(self, image: str, x: int = 0, y: int = 0, w: int = 0, h: int = 0):
        self.colors = _COLORS   # référence à la palette globale, pas de copie
        self.image = image
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._cached_decoded = None
        self._cache_key = None

    def decodeImage(self, posX, posY):
        """
        Decode l'image pour la mettre sous forme d'une liste contenant un tuple spécifiant la position et la couleur du pixel à dessiner
        """
        key = (self.image, posX, posY)
        if key == self._cache_key:
            return self._cached_decoded

        colors = _COLORS
        w = self.w
        spriteTexture = []
        append = spriteTexture.append   # référence locale à append : évite la résolution d'attribut en boucle
        x = -1
        y = 0

        for ch in self.image:
            if x >= w:
                y += 1
                x = 0
            else:
                x += 1
            append((x + posX, y + posY, colors[int(ch)]))

        self._cached_decoded = spriteTexture
        self._cache_key = key
        return spriteTexture

    def SetImage(self, image):
        self.image = image


class AnimatedSprite:
    """
    classe étendue de Sprite, permet de:
    - d'afficher plusieurs sprites différents les uns à la suite des autres pour faire une animation
    """
    def __init__(self, images, x: int = 0, y: int = 0, w: int = 0, h: int = 0):
        self.images = images
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.imageIndex = 0
        self.sprite = Sprite(None, x, y, w, h)

    def Animate(self, seq=0):
        """
        Change de sprite en fonction de la séquence
        """
        self.sprite.x = self.x
        self.sprite.y = self.y
        seq_frames = self.images[seq]   # référence locale
        idx = self.imageIndex
        self.imageIndex = 0 if idx + 1 >= len(seq_frames) else idx + 1
        self.sprite.SetImage(seq_frames[self.imageIndex])
        return self.sprite.decodeImage(self.x, self.y)


class Canva:
    """
    Classe qui gère la zone de dessin du sprite
    """
    def __init__(self, height, width, size):
        self.size = size
        self.height = height
        self.width = width
        self.sprites = []
        self.mat  = {}
        self.prev = {}

    def addSprite(self, sprite):
        """
        Ajoute un sprite qui sera affiché en dernier, cet à dire par dessus les autres
        """
        self.sprites.append(sprite)

    def removeSprite(self, index = -1):
        """
        Retire le dernier sprite, sauf si la variable 'index' est modifiée, dans ce cas là il retire le sprite à l'index i donné
        """
        self.sprites.pop(index)

    def genScreen(self):
        """
        Met à jour mat uniquement pour les pixels dont la couleur change.
        Les pixels inchangés ne sont pas retouchés → drawScreen les ignorera.
        """
        mat = self.mat

        for sprite in self.sprites:
            try:
                used = sprite.Animate()
            except AttributeError:
                used = sprite.decodeImage(sprite.x, sprite.y)

            for x, y, color in used:
                k = (y, x)
                if mat.get(k) != color:
                    mat[k] = color

    def drawScreen(self):
        """
        Compare mat et prev pixel par pixel.
        N'appelle fill_rect que sur les pixels réellement différents.
        get_pixel est complètement supprimé : prev joue ce rôle sans appel C lent.
        """
        mat  = self.mat
        if not LightMode:
            prev = self.prev
        size = self.size
        fill = fill_rect

        for k, color in mat.items():
            if not LightMode :
                if prev.get(k) != color:
                    x = k[1]
                    y = k[0]
                    fill(x * size, y * size, size, size, color)
                    prev[k] = color     # mise à jour du prev uniquement si on a dessiné
            else:
                x = k[1]
                y = k[0]
                fill(x * size, y * size, size, size, color)
            


class GameEngine:
    """
    fonction principale du moteur de jeu, elle s'occupe d'organiser chaque étape pour garder l'affichage et les processus non visibles fluident
    """
    def __init__(self, height, width, size, player=None, collision=True):
        self.screen = Canva(height, width, size)
        self.player = player
        self.collision = collision

    def addPlayer(self, player):
        """
        Ajoute un joueur, n'est pas utilisé dans le script de base mais permet de lui attribuer des actions particulières ou des scripts
        """
        self.player = player

    def removePlayer(self):
        """
        retire le joueur
        """
        self.player = None

    def update(self):
        """
        Met à jour l'écran et les sprite
        """
        self.screen.genScreen()
        self.screen.drawScreen()

    def mainLoop(self, condition_fn, updateDelay=0, Scripts=None):
        """
        boucle d'exécution principale, avec condition de fin sous forme d'un booléen.
        à modifier en fonction du script.
        """
        counter = 0
        start = monotonic()
        while True:
            if condition_fn():
                break
            if Scripts:
                for s in Scripts:
                    s.run()
            self.update()
            if updateDelay > 0:
                sleep(updateDelay)
            counter += 1
            now = monotonic()
            if now >= start + 1:
                #print("fps:", counter)
                counter = 0
                start = now


class GravityScript:
    """
    Script simple qui simule la gravité, mais est peu adapté au petite grille
    """
    def __init__(self, sprite):
        self.sprite = sprite
        self.climb = 0
        self.gravityStrength = 1.89 #ne doit pas être en dessous de 0
        self.hypotetyc_float_y_pos = float(sprite.y)

    def run(self):
        """
        run() est obligatoire pour n'importe quel script afin de l'exécuter
        """
        sprite = self.sprite
        if keydown(KEY_UP) and sprite.y >= 16:
            self.climb += 10
            sprite.y -= 1 
        elif self.climb > 0:
            sprite.y -= 1
            self.climb -= 1
            self.hypotetyc_float_y_pos = sprite.y
        elif sprite.y < 16 and self.climb <= 0:
            self.hypotetyc_float_y_pos += self.gravityStrength
            sprite.y = round(self.hypotetyc_float_y_pos)

class MoveScript:
    """
    Script permettant de déplacer le sprite choisi avec les flèches (peut utiliser la variable player de la classe GameEngine)
    """
    def __init__(self, sprite):
        self.sprite = sprite
    """
    run() est obligatoire pour n'importe quel script afin de l'exécuter
    """
    def run(self):
        sprite = self.sprite
        if keydown(KEY_LEFT) and sprite.x >= 0:
            sprite.x -= 1
        if keydown(KEY_RIGHT) and sprite.x <= 240 - sprite.w:
            sprite.x += 1
            
            
# ---- exemple ----

animation_1      = [["9298929", "9928992", "9928992", "9298929",
                      "9298929", "2998299", "2998299", "9298929"]]
sprite_animated_1 = AnimatedSprite(animation_1, 0, 0, 7, 1)

g = GameEngine(240, 320, 10)
Scripts = [GravityScript(sprite_animated_1), MoveScript(sprite_animated_1)]

g.screen.addSprite(sprite_animated_1)
try:
    g.mainLoop(lambda: keydown(KEY_BACKSPACE), 0, Scripts)
except MemoryError:
    print("/!\ \nle script que vous avez fais\nest trop lourd\n/!\ ")
