from kandinsky import fill_rect
from math import sin, pi
from time import sleep, monotonic
from ion import *


class Sprite:
    def __init__(self, image: str, x: int = 0, y: int = 0, w: int = 0, h: int = 0):
        self.colors: dict[int, tuple[int, int, int]] = {}

        for i in range(8):
            r = int(255 * sin(i / 8 * pi))
            g = int(255 * sin(i / 8 * pi + (1 / 4) * pi / 3))
            b = int(255 * sin(i / 8 * pi + 1 * pi / 3))
            self.colors[i] = (r, g, b)

        self.colors[8] = (0, 0, 0)
        self.colors[9] = (255, 255, 255)

        self.image = image
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        # Cache du décodage : recalculé uniquement si l'image ou la position change
        self._cached_decoded = None
        self._cache_key = None  # (image, x, y)

    def ShowPalette(self):
        for i in range(9):
            fill_rect(i * 5, 0, 5, 5, self.colors[i])

    def decodeImage(self, posX, posY):
        """
        Décodage avec cache : si l'image et la position n'ont pas changé,
        retourne directement le résultat précédent sans recalculer.
        """
        key = (self.image, posX, posY)
        if key == self._cache_key:
            return self._cached_decoded  # pas de recalcul si rien n'a changé

        colors = self.colors  # référence locale pour éviter les accès self.colors répétés
        w = self.w
        spriteTexture = []
        x = -1
        y = 0

        for ch in self.image:  # itération directe sur les caractères, plus rapide que range(len())
            if x >= w:
                y += 1
                x = 0
            else:
                x += 1
            spriteTexture.append((x + posX, y + posY, colors[int(ch)]))

        self._cached_decoded = spriteTexture
        self._cache_key = key
        return spriteTexture

    def SetImage(self, image):
        self.image = image


class AnimatedSprite:
    def __init__(self, images, x: int = 0, y: int = 0, w: int = 0, h: int = 0):
        self.images = images
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.imageIndex = 0
        self.sprite = Sprite(None, x, y, w, h)

    def Animate(self, seq=0):
        self.sprite.x = self.x
        self.sprite.y = self.y

        if self.imageIndex + 1 >= len(self.images[seq]):
            self.imageIndex = 0
        else:
            self.imageIndex += 1

        self.sprite.SetImage(self.images[seq][self.imageIndex])
        return self.sprite.decodeImage(self.x, self.y)


class Canva:
    def __init__(self, height, width, size):
        self.height = height
        self.width = width
        self.size = size
        self.sprites = []

        cols = width // size
        rows = height // size
        # Matrice courante [y][x]
        self.mat = [[None] * cols for _ in range(rows)]
        # Matrice de l'ancienne frame : on ne redessine que les pixels qui ont changé
        # remplace l'appel get_pixel() qui est très lent
        self._prev = [[None] * cols for _ in range(rows)]

    def addSprite(self, sprite):
        self.sprites.append(sprite)

    def removeSprite(self, index):
        self.sprites.pop(index)

    def genScreen(self):
        """
        Remplit self.mat avec les couleurs de tous les sprites.
        """
        mat = self.mat          # référence locale (évite self.mat à chaque accès)
        rows = len(mat)
        cols = len(mat[0])

        for sprite in self.sprites:
            try:
                used = sprite.Animate()
            except AttributeError:
                used = sprite.decodeImage(sprite.x, sprite.y)

            for x, y, color in used:
                if 0 <= y < rows and 0 <= x < cols:
                    mat[y][x] = color

    def drawScreen(self):
        """
        Ne redessine que les pixels dont la couleur a changé depuis la frame précédente.
        """
        mat  = self.mat
        prev = self._prev
        size = self.size
        fill = fill_rect  # référence locale pour éviter la résolution globale à chaque appel

        for y in range(len(mat)):
            row      = mat[y]
            prev_row = prev[y]
            for x in range(len(row)):
                color = row[x]
                if color is not None and color != prev_row[x]:
                    fill(x * size, y * size, size, size, color)
                    prev_row[x] = color  # mise à jour de l'ancienne frame


class GameEngine:
    def __init__(self, height, width, size, player=None, collision=True):
        self.screen = Canva(height, width, size)
        self.player = player
        self.collision = collision

    def addPlayer(self, player):
        self.player = player

    def removePlayer(self):
        self.player = None

    def update(self):
        self.screen.genScreen()
        self.screen.drawScreen()

    def mainLoop(self, condition_fn, updateDelay=0.1, Scripts=None):
        """
        condition_fn : fonction évaluée à chaque tour (lambda ou callable).
        Exemple d'appel : g.mainLoop(lambda: keydown(KEY_BACKSPACE), 0, Scripts)
        """
        while True:
            if condition_fn():
                break

            if Scripts:
                for Script in Scripts:
                    Script.run()

            self.update()
            if updateDelay > 0:
                sleep(updateDelay)


class GravityScript:
    def __init__(self, sprite):
        self.counter = 0
        self.sprite = sprite
        self.climb = 0
        self.gravityStrength = 1

    def run(self):
        sprite = self.sprite  # référence locale
        if keydown(KEY_UP) and sprite.y >= 16:
            self.climb += 4
            sprite.y -= self.gravityStrength
        elif self.climb > 0:
            sprite.y -= self.gravityStrength
            self.climb -= 1
        elif sprite.y < 16 and self.climb <= 0:
            sprite.y += self.gravityStrength


class MoveScript:
    def __init__(self, sprite):
        self.sprite = sprite

    def run(self):
        sprite = self.sprite  # référence locale
        if keydown(KEY_LEFT) and sprite.x >= 0:
            sprite.x -= 1
        if keydown(KEY_RIGHT) and sprite.x <= 240 - sprite.w:
            sprite.x += 1

# ---- exemple ----
background = (("8" * 20 * 32 )+"1"*40)
backgroundSprite = Sprite(background, 0, 0, 32, 24)
animation_1 = [["9298929", "9928992", "9928992", "9298929", "9298929", "2998299", "2998299", "9298929"]]
sprite_animated_1 = AnimatedSprite(animation_1, 0, 0, 7, 1)
g = GameEngine(240, 320, 5)
Scripts = [GravityScript(sprite_animated_1), MoveScript(sprite_animated_1)]
g.screen.addSprite(backgroundSprite)
g.screen.addSprite(sprite_animated_1)
g.mainLoop(lambda: keydown(KEY_BACKSPACE), 0.1, Scripts)