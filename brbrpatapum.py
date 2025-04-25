import pygame
import random
import math

pygame.init()
pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 700, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")
FPS = 60

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 48)

# Загрузка звуков
explosion_sound = pygame.mixer.Sound("IGAMES/explosion.wav")
damage_sound = pygame.mixer.Sound("IGAMES/damage.wav")
pygame.mixer.music.load("IGAMES/background_music.wav")
pygame.mixer.music.play(-1)

def load_and_scale(path, size, fallback_color):
    try:
        img = pygame.image.load(path)
        return pygame.transform.scale(img, size)
    except pygame.error:
        surf = pygame.Surface(size)
        surf.fill(fallback_color)
        return surf

background = load_and_scale("IGAMES/beck.png", (WIDTH, HEIGHT), (0,0,0))
player_img = load_and_scale("IGAMES/pl.png", (50, 40), (255,255,255))
player_bullet_img = load_and_scale("IGAMES/rocket.png", (10, 20), (255, 0, 0))

enemy_imgs = {
    "ene": load_and_scale("IGAMES/ene.png", (50, 40), (200, 50, 50)),
    "ene1": load_and_scale("IGAMES/ene1.png", (50,100), (200, 100, 100)),
    "ene2": load_and_scale("IGAMES/ene2.png", (50,100), (150, 0, 150)),
    "ene3": load_and_scale("IGAMES/ene3.png", (114,200), (200, 200, 0)),
}

enemy_rocket_imgs = {
    "ene": load_and_scale("IGAMES/rocket1.png", (10,20), (255, 50, 50)),
    "ene1": load_and_scale("IGAMES/rocket2.png", (15,25), (255,100,100)),
    "ene2": load_and_scale("IGAMES/rocket2.png", (15,25), (150, 0,150)),
    "ene3": load_and_scale("IGAMES/rocket3.png", (20,30), (50,200,200)),
}

def draw_button(text, y_offset=0, color=(100,100,100)):
    text_surf = big_font.render(text, True, WHITE)
    rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
    pygame.draw.rect(WIN, color, rect.inflate(20,10))
    WIN.blit(text_surf, rect)
    return rect

def check_rect_collision(r, enemies):
    return any(r.colliderect(e["rect"]) for e in enemies)

def spawn_wave(wave_num, existing):
    new = []
    def try_spawn(kind, count):
        w,h = enemy_imgs[kind].get_size()
        for _ in range(count):
            for _ in range(20):
                x = random.randint(0, WIDTH-w)
                y = -h - random.randint(0, 50)
                r = pygame.Rect(x,y,w,h)
                if not check_rect_collision(r, existing+new):
                    new.append({
                        "kind": kind,
                        "rect": r,
                        "img": enemy_imgs[kind],
                        "speed": {"ene":2.5, "ene1":2.0, "ene2":1.5, "ene3":1.2}[kind],
                        "fire_rate": {"ene":70, "ene1":80, "ene2":70, "ene3":40}[kind],
                        "rocket_img": enemy_rocket_imgs[kind],
                        "rocket_size": enemy_rocket_imgs[kind].get_size(),
                        "health": {"ene":2, "ene1":6, "ene2":8, "ene3":100}[kind],
                        "shoot_timer": random.randint(0,60),
                        "move_timer": 0,
                        "direction": 1,
                        "attack_phase": 0,
                        "phase_timer": 0
                    })
                    break

    if wave_num == 1:
        try_spawn("ene", 10)
    elif wave_num == 2:
        try_spawn("ene", 12)
        try_spawn("ene1", 6)
    elif wave_num == 3:
        try_spawn("ene1", 8)
        try_spawn("ene2", 6)
    elif wave_num == 4:
        try_spawn("ene3", 1)
        for e in new:
            if e["kind"] == "ene3":
                e["rect"].x = WIDTH//2 - e["rect"].width//2
                e["rect"].y = 50
                e["speed"] = 3.0
                break

    return new

def main():
    clock = pygame.time.Clock()
    player_rect = pygame.Rect(WIDTH//2-25, HEIGHT-60, 50, 40)
    player_health = 3
    player_bullets = []
    enemy_bullets = []
    enemies = []
    
    wave = 1
    boss_done = False
    victory = False
    score = 0
    game_over = False
    paused = False
    shoot_timer = 0

    run = True
    while run:
        clock.tick(FPS)
        WIN.blit(background, (0,0))

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                run = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    paused = not paused
                if ev.key == pygame.K_r and (game_over or victory):
                    return main()
            if ev.type == pygame.MOUSEBUTTONDOWN and (game_over or victory):
                if restart_btn.collidepoint(ev.pos):
                    return main()

        if not paused and not game_over and not victory:
            keys = pygame.key.get_pressed()
            player_rect.x = max(0, min(WIDTH-player_rect.width, 
                player_rect.x + (keys[pygame.K_d] - keys[pygame.K_a])*5))
            player_rect.y = max(0, min(HEIGHT-player_rect.height, 
                player_rect.y + (keys[pygame.K_s] - keys[pygame.K_w])*5))

            shoot_timer += 1
            if shoot_timer >= 15:
                shoot_timer = 0
                w,h = player_bullet_img.get_size()
                player_bullets.append({
                    "rect": pygame.Rect(player_rect.centerx-w//2, player_rect.top-h, w,h),
                    "img": player_bullet_img, 
                    "vy": -9
                })

            player_bullets = [b for b in player_bullets if b["rect"].y > -20]
            for b in player_bullets: 
                b["rect"].y += b["vy"]

            if not enemies and not boss_done and not victory:
                new_wave = spawn_wave(wave, enemies)
                if new_wave:
                    enemies.extend(new_wave)
                    if wave == 4:
                        boss_done = True
                        pygame.mixer.music.fadeout(1000)
                        pygame.mixer.music.load("IGAMES/boss_music.wav")
                        pygame.mixer.music.play(-1)
                    wave += 1

            for e in enemies[:]:
                if e["kind"] == "ene3":
                    e["phase_timer"] += 1
                    if e["phase_timer"] >= 300:
                        e["phase_timer"] = 0
                        e["attack_phase"] = 1 - e["attack_phase"]

                    if e["attack_phase"] == 0:
                        e["rect"].x += e["speed"] * e["direction"] * 1.5
                        if e["rect"].right > WIDTH - 20: 
                            e["direction"] = -1
                        elif e["rect"].left < 20:
                            e["direction"] = 1
                    else:
                        e["rect"].x += e["speed"] * e["direction"] * 0.5
                        if e["rect"].right > WIDTH - 100:
                            e["direction"] = -1
                        elif e["rect"].left < 100:
                            e["direction"] = 1

                    e["shoot_timer"] += 1
                    if e["attack_phase"] == 0:
                        if e["shoot_timer"] >= 15:
                            e["shoot_timer"] = 0
                            rw, rh = e["rocket_size"]
                            enemy_bullets.append({
                                "rect": pygame.Rect(e["rect"].centerx-rw//2, e["rect"].bottom, rw, rh),
                                "img": e["rocket_img"], 
                                "vy": 6
                            })
                    else:
                        if e["shoot_timer"] >= 60:
                            e["shoot_timer"] = 0
                            rw, rh = e["rocket_size"]
                            for i in range(-2, 3):
                                enemy_bullets.append({
                                    "rect": pygame.Rect(
                                        e["rect"].centerx - rw//2 + i*20,
                                        e["rect"].bottom,
                                        rw, rh
                                    ),
                                    "img": e["rocket_img"],
                                    "vy": 4
                                })
                else:
                    e["shoot_timer"] += 1
                    if e["shoot_timer"] >= e["fire_rate"]:
                        e["shoot_timer"] = 0
                        rw, rh = e["rocket_size"]
                        vy = 5 if e["kind"] == "ene" else 3
                        enemy_bullets.append({
                            "rect": pygame.Rect(e["rect"].centerx-rw//2, e["rect"].bottom, rw, rh),
                            "img": e["rocket_img"],
                            "vy": vy
                        })

                    e["rect"].y += e["speed"]
                    if e["kind"] == "ene2":
                        e["rect"].x += int(3*math.sin(e["move_timer"]/10))
                        e["move_timer"] += 1

                if e["rect"].colliderect(player_rect):
                    player_health -= 2
                    damage_sound.play()
                    enemies.remove(e)
                    if player_health <= 0:
                        game_over = True

                for b in player_bullets[:]:
                    if e["rect"].colliderect(b["rect"]):
                        player_bullets.remove(b)
                        e["health"] -= 1
                        if e["health"] <= 0:
                            explosion_sound.play()
                            enemies.remove(e)
                            score += 50 if e["kind"]=="ene3" else 1
                            if e["kind"] == "ene3":
                                victory = True
                        break

                if e["rect"].top > HEIGHT and e["kind"] != 'ene3':
                    enemies.remove(e)

            enemy_bullets = [b for b in enemy_bullets if b["rect"].y < HEIGHT]
            for b in enemy_bullets[:]:
                b["rect"].y += b["vy"]
                if b["rect"].colliderect(player_rect):
                    enemy_bullets.remove(b)
                    player_health -= 1
                    damage_sound.play()
                    if player_health <= 0:
                        game_over = True

            WIN.blit(player_img, player_rect)
            for b in player_bullets: WIN.blit(b["img"], b["rect"])
            for b in enemy_bullets: WIN.blit(b["img"], b["rect"])
            for e in enemies: WIN.blit(e["img"], e["rect"])

            WIN.blit(font.render(f"Счет: {score}", True, WHITE), (10, 10))
            WIN.blit(font.render(f"Волна: {min(wave-1, 4)}", True, WHITE), (10, 40))
            WIN.blit(font.render(f"HP: {player_health}", True, GREEN if player_health >1 else RED), (10, 70))

        if paused:
            WIN.blit(big_font.render("PAUSED", True, WHITE), (WIDTH//2-60, HEIGHT//2-20))
        elif game_over:
            WIN.blit(big_font.render("GAME OVER", True, RED), (WIDTH//2-100, HEIGHT//2-60))
            restart_btn = draw_button("RESTART", 40, (80, 0, 0))
        elif victory:
            WIN.blit(big_font.render("VICTORY!", True, GREEN), (WIDTH//2-80, HEIGHT//2-60))
            restart_btn = draw_button("PLAY AGAIN", 40, (0, 80, 0))

        pygame.display.update()

if __name__ == "__main__":
    main()
