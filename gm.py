import pygame
import random
import math
import array

# Initialisation
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)
L_ECRAN, H_ECRAN = 800, 600
ecran = pygame.display.set_mode((L_ECRAN, H_ECRAN))
pygame.display.set_caption("Nebula Jump - Level Design Update")
horloge = pygame.time.Clock()

# --- GÉNÉRATEUR DE SONS ---
def generer_son_simple(frequence, duree, volume=0.1, decay=10):
    sample_rate = 22050
    n_samples = int(sample_rate * duree)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = float(i) / sample_rate
        enveloppe = math.exp(-t * decay)
        signal = math.sin(2.0 * math.pi * frequence * t)
        buf[i] = int(volume * 32767 * signal * enveloppe)
    return pygame.mixer.Sound(buf)

# Sons
son_saut = generer_son_simple(400, 0.15, 0.08, 15)
son_double_saut = generer_son_simple(600, 0.1, 0.07, 20)
son_mort = generer_son_simple(100, 0.4, 0.15, 5)
son_point = generer_son_simple(800, 0.08, 0.06, 25)
son_tir = generer_son_simple(1000, 0.05, 0.05, 30)
son_casse = generer_son_simple(300, 0.1, 0.1, 15)

# Polices
pol_menu = pygame.font.SysFont("Verdana", 60, bold=True)
pol_stats = pygame.font.SysFont("Verdana", 25, bold=True)
pol_info = pygame.font.SysFont("Verdana", 18, bold=True)

# Couleurs
NOIR = (10, 10, 25)
BLANC = (255, 255, 255)
OR = (255, 215, 0)
ENNEMI_NEON = (0, 255, 120)
PROJECTILE_BLEU = (0, 200, 255)
MUR_ORANGE = (255, 140, 0) # Couleur des obstacles destructibles
COULEURS_JOUEUR = [(255, 60, 60), (60, 150, 255), (100, 255, 100), (255, 255, 0)]

class Etoile:
    def __init__(self):
        self.x = random.randint(0, 15000)
        self.y = random.randint(0, H_ECRAN)
        self.t = random.randint(1, 3)
        self.v = self.t * 0.1
    def draw(self, surf, cam_x):
        pygame.draw.circle(surf, BLANC, (int(self.x - cam_x * self.v), self.y), self.t)

class Ennemi:
    def __init__(self, plat):
        self.plat = plat
        self.rect = pygame.Rect(plat.rect.x + 10, plat.rect.y - 30, 30, 30)
        self.v = 3
    def update(self):
        self.rect.x += self.v
        if self.v > 0 and self.rect.right + self.v > self.plat.rect.right:
            self.v *= -1
        elif self.v < 0 and self.rect.left + self.v < self.plat.rect.left:
            self.v *= -1

class Projectile:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.direction = direction
        self.vitesse = 15
        self.active = True
    def update(self):
        self.rect.x += self.direction * self.vitesse
        if self.rect.x < -100 or self.rect.x > 15000:
            self.active = False
    def draw(self, surf, cam_x):
        if self.active:
            pygame.draw.rect(surf, PROJECTILE_BLEU, (self.rect.x - cam_x, self.rect.y, 10, 10), 0, 3)

class Joueur:
    def __init__(self):
        self.rect = pygame.Rect(100, 400, 35, 35)
        self.vx = 0
        self.vy = 0
        self.vies = 3
        self.score = 0
        self.niv = 1
        self.c_index = 0
        self.nb_sauts = 0
        self.sur_sol = False
        self.dir_visuelle = 1
        self.tir_cooldown = 0
        self.power_tir_timer = 0

    def reset(self):
        self.rect.x, self.rect.y = 100, 400
        self.vx = self.vy = 0
        self.tir_cooldown = 0
        self.power_tir_timer = 0

class Plateforme:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

class ObstacleDestructible:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 60) # Un mur vertical
        self.pv = 2 # Il faut 2 tirs pour le casser

# --- NOUVEAU SYSTÈME DE MAPPING (Plus propre) ---
def generer_niveau(niv):
    plats = []
    enns = []
    murs = []
    bonus = None
    
    # Plateforme de départ
    plat_depart = Plateforme(50, 500, 300, 30)
    plats.append(plat_depart)
    
    cur_x = plat_depart.rect.right # On commence à la fin de la première plateforme
    cur_y = 500
    
    for i in range(30):
        # On force un espace vide (trou) entre 50 et 150 pixels pour être sûr de pouvoir sauter
        trou_x = random.randint(50, 150)
        new_x = cur_x + trou_x
        
        # Variation de hauteur raisonnable (-80 vers le haut, +80 vers le bas)
        new_y = max(200, min(550, cur_y + random.randint(-80, 80)))
        
        # Largeur de la plateforme
        w = random.randint(150, 250)
        
        # Création
        p = Plateforme(new_x, new_y, w, 20)
        plats.append(p)
        
        # Ajout d'ennemis (pas sur les toutes premières)
        if i > 2 and random.random() < 0.4:
            enns.append(Ennemi(p))
            
        # Ajout d'un mur destructible au milieu de la plateforme
        if i > 4 and random.random() < 0.2:
            murs.append(ObstacleDestructible(new_x + w//2, new_y - 60))
            
        # Un bonus par niveau environ
        if i == 15:
            bonus = pygame.Rect(new_x + w//2, new_y - 60, 25, 25)
            
        # Mise à jour de la position courante pour la prochaine boucle
        cur_x = new_x + w
        cur_y = new_y
        
    fin = pygame.Rect(cur_x + 100, cur_y - 80, 60, 100)
    etoiles = [Etoile() for _ in range(250)]
    return plats, enns, murs, etoiles, fin, bonus

# Variables globales
joueur = Joueur()
etat_jeu = "MENU"
plats, enns, murs, etoiles, fin, bonus_lvl = generer_niveau(1)
projectiles = []

while True:
    ecran.fill(NOIR)
    touches = pygame.key.get_pressed()

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit()
            exit()
        if ev.type == pygame.KEYDOWN:
            if etat_jeu == "MENU":
                if ev.key == pygame.K_RETURN: 
                    etat_jeu = "JEU"
                if ev.key == pygame.K_c: 
                    joueur.c_index = (joueur.c_index + 1) % len(COULEURS_JOUEUR)
            elif etat_jeu == "GAMEOVER":
                if ev.key == pygame.K_r: 
                    joueur = Joueur()
                    plats, enns, murs, etoiles, fin, bonus_lvl = generer_niveau(1)
                    etat_jeu = "JEU"
                    projectiles.clear()
            elif etat_jeu == "JEU":
                if ev.key == pygame.K_SPACE:
                    if joueur.sur_sol: 
                        joueur.vy = -16
                        joueur.nb_sauts = 1
                        son_saut.play()
                    elif joueur.nb_sauts < 2: 
                        joueur.vy = -14
                        joueur.nb_sauts += 1
                        son_double_saut.play()
                
                if ev.key == pygame.K_x and joueur.tir_cooldown <= 0:
                    son_tir.play()
                    if joueur.power_tir_timer > 0:
                        projectiles.append(Projectile(joueur.rect.centerx, joueur.rect.centery - 10, joueur.dir_visuelle))
                        projectiles.append(Projectile(joueur.rect.centerx, joueur.rect.centery, joueur.dir_visuelle))
                        projectiles.append(Projectile(joueur.rect.centerx, joueur.rect.centery + 10, joueur.dir_visuelle))
                    else:
                        projectiles.append(Projectile(joueur.rect.centerx, joueur.rect.centery, joueur.dir_visuelle))
                    joueur.tir_cooldown = 15

    if etat_jeu == "MENU":
        titre = pol_menu.render("NEBULA JUMP", True, COULEURS_JOUEUR[joueur.c_index])
        play = pol_stats.render("Appuie sur [ENTRÉE] pour Jouer", True, BLANC)
        color_info = pol_info.render("Appuie sur [C] pour changer de couleur", True, OR)
        
        demo_y = 350 + math.sin(pygame.time.get_ticks() * 0.005) * 20
        pygame.draw.rect(ecran, COULEURS_JOUEUR[joueur.c_index], (L_ECRAN//2 - 25, demo_y, 50, 50), 0, 10)
        
        ecran.blit(titre, (L_ECRAN//2 - 220, 150))
        ecran.blit(play, (L_ECRAN//2 - 200, 450))
        ecran.blit(color_info, (L_ECRAN//2 - 180, 500))

    elif etat_jeu == "JEU":
        cam_x = max(0, joueur.rect.centerx - L_ECRAN // 2)
        
        # Mouvements gauche/droite
        if touches[pygame.K_RIGHT]: 
            joueur.vx = 8
            joueur.dir_visuelle = 1
        elif touches[pygame.K_LEFT]: 
            joueur.vx = -8
            joueur.dir_visuelle = -1
        else: 
            joueur.vx = 0
            
        joueur.rect.x += joueur.vx
        
        if joueur.tir_cooldown > 0: joueur.tir_cooldown -= 1
        if joueur.power_tir_timer > 0: joueur.power_tir_timer -= 1

        # Collisions HORIZONTALES (Plateformes et Murs)
        obstacles_solides = [p.rect for p in plats] + [m.rect for m in murs]
        for obs in obstacles_solides:
            if joueur.rect.colliderect(obs):
                if joueur.vx > 0: joueur.rect.right = obs.left
                elif joueur.vx < 0: joueur.rect.left = obs.right
        
        # Gravité et Mouvement Y
        joueur.vy += 0.8
        joueur.rect.y += joueur.vy
        joueur.sur_sol = False
        
        # Collisions VERTICALES
        for obs in obstacles_solides:
            if joueur.rect.colliderect(obs):
                if joueur.vy > 0: 
                    joueur.rect.bottom = obs.top
                    joueur.vy = 0
                    joueur.sur_sol = True
                elif joueur.vy < 0: 
                    joueur.rect.top = obs.bottom
                    joueur.vy = 0

        # Chute dans le vide
        if joueur.rect.y > H_ECRAN + 100:
            joueur.vies -= 1
            son_mort.play()
            joueur.reset()
            if joueur.vies <= 0: etat_jeu = "GAMEOVER"

        # Gestion Ennemis
        for e in enns[:]:
            e.update()
            if joueur.rect.colliderect(e.rect):
                if joueur.vy > 0 and joueur.rect.bottom < e.rect.centery + 10:
                    enns.remove(e)
                    joueur.vy = -12
                    joueur.score += 250
                    son_casse.play()
                else:
                    joueur.vies -= 1
                    son_mort.play()
                    joueur.reset()
                    if joueur.vies <= 0: etat_jeu = "GAMEOVER"
        
        # Gestion Projectiles (Tir sur ennemis et murs destructibles)
        for proj in projectiles[:]:
            proj.update()
            if not proj.active:
                projectiles.remove(proj)
                continue
                
            # Toucher un ennemi
            touch_ennemi = False
            for e in enns[:]:
                if proj.rect.colliderect(e.rect) and proj.active:
                    enns.remove(e)
                    proj.active = False
                    joueur.score += 300
                    son_casse.play()
                    touch_ennemi = True
                    break
            
            # Toucher un mur destructible
            if not touch_ennemi:
                for m in murs[:]:
                    if proj.rect.colliderect(m.rect) and proj.active:
                        m.pv -= 1
                        proj.active = False
                        son_casse.play()
                        if m.pv <= 0:
                            murs.remove(m)
                            joueur.score += 100
                        break

        # Bonus
        if bonus_lvl and joueur.rect.colliderect(bonus_lvl):
            bonus_lvl = None
            joueur.power_tir_timer = 300
            son_point.play()

        # Fin du niveau
        if joueur.rect.colliderect(fin):
            joueur.niv += 1
            joueur.score += 1000
            son_point.play()
            joueur.reset()
            plats, enns, murs, etoiles, fin, bonus_lvl = generer_niveau(joueur.niv)
            projectiles.clear()

        # --- DESSIN ---
        for et in etoiles: 
            et.draw(ecran, cam_x)
        for p in plats: 
            pygame.draw.rect(ecran, (50, 70, 120), (p.rect.x - cam_x, p.rect.y, p.rect.width, p.rect.height), 0, 4)
        for m in murs:
            # Le mur devient plus sombre quand il perd un PV
            c_mur = MUR_ORANGE if m.pv == 2 else (150, 50, 0)
            pygame.draw.rect(ecran, c_mur, (m.rect.x - cam_x, m.rect.y, m.rect.width, m.rect.height), 0, 4)
        for e in enns: 
            pygame.draw.rect(ecran, ENNEMI_NEON, (e.rect.x - cam_x, e.rect.y, 30, 30), 0, 5)
        for proj in projectiles: 
            proj.draw(ecran, cam_x)
            
        if bonus_lvl: 
            pygame.draw.rect(ecran, OR, (bonus_lvl.x - cam_x, bonus_lvl.y, 25, 25), 0, 5)
        
        pygame.draw.rect(ecran, OR, (fin.x - cam_x, fin.y, 60, 100), 0, 5)
        pygame.draw.rect(ecran, COULEURS_JOUEUR[joueur.c_index], (joueur.rect.x - cam_x, joueur.rect.y, 35, 35), 0, 8)

        # --- UI et FPS ---
        fps = str(int(horloge.get_fps()))
        ui_txt = pol_info.render(f"NIV: {joueur.niv} | VIES: {joueur.vies} | SCORE: {joueur.score} | FPS: {fps}", True, BLANC)
        
        # Arrière-plan sombre pour l'UI (comme sur ta maquette)
        pygame.draw.rect(ecran, (20, 20, 20), (10, 10, ui_txt.get_width() + 20, 40), 0, 15)
        pygame.draw.rect(ecran, BLANC, (10, 10, ui_txt.get_width() + 20, 40), 2, 15) # Bordure
        ecran.blit(ui_txt, (20, 18))
        
        if joueur.power_tir_timer > 0:
            p_txt = pol_info.render("TRIPLE TIR", True, PROJECTILE_BLEU)
            pygame.draw.rect(ecran, (20, 20, 20), (L_ECRAN - 150, 10, 140, 40), 0, 15)
            pygame.draw.rect(ecran, PROJECTILE_BLEU, (L_ECRAN - 150, 10, 140, 40), 2, 15)
            ecran.blit(p_txt, (L_ECRAN - 135, 18))

    elif etat_jeu == "GAMEOVER":
        ecran.fill((30, 0, 0))
        zoom = 1 + (pygame.time.get_ticks() % 2000 / 2000.0) * 0.1
        txt_mort = pol_menu.render("GAME OVER", True, (255, 50, 50))
        txt_zoom = pygame.transform.scale(txt_mort, (int(txt_mort.get_width() * zoom), int(txt_mort.get_height() * zoom)))
        
        ecran.blit(txt_zoom, txt_zoom.get_rect(center=(L_ECRAN//2, 200)))
        ecran.blit(pol_stats.render(f"Niveau {joueur.niv} - Score {joueur.score}", True, BLANC), (L_ECRAN//2 - 140, 320))
        ecran.blit(pol_info.render("Appuie sur [R] pour recommencer", True, OR), (L_ECRAN//2 - 160, 450))

    pygame.display.flip()
    horloge.tick(60)