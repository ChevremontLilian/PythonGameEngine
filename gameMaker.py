from kandinsky import fill_rect, get_pixel
from math import sin, pi
from time import sleep, monotonic
from ion import *

class Sprite:
    def __init__(self, image: str, x: int = 0, y: int = 0, w: int = 0, h: int = 0):
        self.colors: dict[int, tuple[int, int, int]] = {}

        # Génération d'une palette de 8 couleurs via des sinusoïdes décalées
        for i in range(8):
            r = int(255 * sin(i / 8 * pi))
            g = int(255 * sin(i / 8 * pi + (1 / 4) * pi / 3))
            b = int(255 * sin(i / 8 * pi + 1 * pi / 3))
            self.colors[i] = (r, g, b)

        # Couleurs fixes : 8 = noir, 9 = blanc
        self.colors[8] = (0, 0, 0)
        self.colors[9] = (255, 255, 255)

        self.image = image  # Chaîne de caractères représentant l'image (ex: "9298929")
        self.x = x
        self.y = y
        self.w = w          # Largeur en pixels du sprite
        self.h = h          # Hauteur en pixels du sprite

    def ShowPalette(self):
        """Affiche la palette de couleurs sous forme de carrés de 5px."""
        for i in range(9):
            fill_rect(i * 5, 0, 5, 5, self.colors[i])

    def decodeImage(self, posX, posY):
        """
        Convertit la chaîne self.image en liste de tuples (x, y, couleur).
        Chaque caractère de l'image correspond à un index dans la palette.
        posX, posY : décalage de position sur l'écran.
        """
        spriteTexture = []
        x = -1  # Colonne courante (repart à 0 à chaque nouvelle ligne)
        y = 0  # Ligne courante

        for i in range(len(self.image)):
            # Retour à la ligne quand on dépasse la largeur du sprite
            if x >= self.w:
                y += 1
                x = 0  # était x=1, ce qui sautait le premier pixel de chaque ligne
            else:
                x += 1

            couleur = self.colors[int(self.image[i])]
            spriteTexture.append((x + posX, y + posY, couleur))

        return spriteTexture

    def SetImage(self, image):
        """Remplace l'image courante du sprite."""
        self.image = image


class AnimatedSprite:
    def __init__(self, images, x: int = 0, y: int = 0, w: int = 0, h: int = 0):
        """
        images : liste de séquences d'animation.
                 Structure : images[seq][frame] = chaîne de pixels
        """
        self.images = images
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.imageIndex = 0                      # Index de la frame courante
        self.sprite = Sprite(None, x, y, w, h)   # Sprite interne utilisé pour le décodage

    def Animate(self, seq=0):
        """
        Avance d'une frame dans la séquence seq et retourne les pixels à dessiner.
        seq : index de la séquence d'animation à jouer.
        """
        self.sprite.x = self.x
        self.sprite.y = self.y

        # on vérifie les bornes AVANT d'accéder à la frame
        if self.imageIndex + 1 >= len(self.images[seq]):
            self.imageIndex = 0
        else:
            self.imageIndex += 1

        # Charger la frame courante dans le sprite interne
        image = self.images[seq][self.imageIndex]
        self.sprite.SetImage(image)

        return self.sprite.decodeImage(self.x, self.y)


class Canva:
    def __init__(self, height, width, size):
        """
        height, width : dimensions de l'écran en pixels.
        size : taille d'une cellule (un pixel de sprite = size×size pixels écran).
        """
        self.height = height
        self.width = width
        self.size = size
        self.sprites = []

        # Matrice [ligne][colonne] = couleur, donc indexée [y][x]
        self.mat = [[None for i in range(width // size)] for j in range(height // size)]
        print(len(self.mat), len(self.mat[0]))

    def addSprite(self, sprite):
        """Ajoute un Sprite ou AnimatedSprite à la scène."""
        self.sprites.append(sprite)

    def removeSprite(self, index):
        """Supprime le sprite à l'index donné."""
        self.sprites.pop(index)

    def genScreen(self):
        """
        Génère la frame courante dans self.mat.
        Pour chaque sprite : tente Animate(), sinon decodeImage().
        """
        for sprite in self.sprites:
            try:
                used = sprite.Animate()
            except AttributeError:
                # Le sprite n'est pas animé → on appelle decodeImage directement
                used = sprite.decodeImage(sprite.x, sprite.y)

            # self.mat est indexé [y][x], pas [x][y]
            for x, y, color in used:
                if 0 <= y < len(self.mat) and 0 <= x < len(self.mat[0]):
                    if self.mat[y][x] != color:
                        self.mat[y][x] = color  # On vérifie aussi qu'on ne sort pas des bornes

    def drawScreen(self):
        """
        Dessine self.mat à l'écran.
        Chaque cellule est un carré de self.size × self.size pixels.
        """
        for y in range(len(self.mat)):
            for x in range(len(self.mat[y])):
                color = self.mat[y][x]
                if color is not None and self.mat[y][x] != get_pixel(x * self.size, y * self.size):  # On peut aussi choisir de ne pas dessiner les pixels noirs
                    fill_rect(x * self.size, y * self.size, self.size, self.size, color)

class GameEngine:
    def __init__(self,height,width,size,player=None,collision = True):
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

    def mainLoop(self,condition,updateDelay=0.1,Scripts=None):
        start = monotonic()
        frameCount = 0
        while True:
            if condition:
                break
            else:
                try:
                    for Script in Scripts:
                        Script.run()
                except:
                    pass
                self.update()
                frameCount += 1
                elapsed = monotonic() - start
                print(f"fps {frameCount/elapsed:.2f}")
                sleep(updateDelay)

class GravityScript:
    def __init__(self,sprite):
        self.counter = 0
        self.sprite = sprite
        self.climb = 0
        self.gravityStrength = 1

    def run(self):
        if keydown(KEY_UP) and self.sprite.y >= 16:
            self.climb += 4
            self.sprite.y -= self.gravityStrength
        elif self.climb > 0:
            self.sprite.y -= self.gravityStrength
            self.climb -= 1
        elif self.sprite.y < 16 and self.climb <= 0:
            self.sprite.y += self.gravityStrength
        else:
            pass
        print(self.climb)

class MoveScript:
    def __init__(self,sprite):
        self.sprite = sprite

    def run(self):
        if keydown(KEY_LEFT) and self.sprite.x >= 0:
            self.sprite.x -= 1
        if keydown(KEY_RIGHT) and self.sprite.x <= 240 - self.sprite.w:
            self.sprite.x += 1    

# ---- exemple ----
background = (("9" * 23 * 32 ))
backgroundSprite = Sprite(background, 0, 0, 32, 24)
animation_1 = "9"
sprite_animated_1 = Sprite(animation_1, 0, 0, 1, 2)
g = GameEngine(220, 320, 10)
Scripts = [GravityScript(sprite_animated_1), MoveScript(sprite_animated_1)]
g.screen.addSprite(backgroundSprite)
g.screen.addSprite(sprite_animated_1)
g.mainLoop(keydown(KEY_BACKSPACE),0,Scripts)