import pygame
import sys
import time
import random

# -------------------------------
# 常量与参数设置
# -------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TILE_SIZE = 40  # 每个地图块的尺寸

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (100, 100, 100)
GREEN = (0, 255, 0)       # 旗帜颜色
RED   = (255, 0, 0)       # 障碍物颜色

# -------------------------------
# 三个关卡地图（字符地图）
# 说明：
#   "X" 表示砖块（平台）
#   "O" 表示障碍物（碰到则关卡失败）
#   "P" 表示玩家起始位置（仅一处）
#   "F" 表示终点旗帜（过关目标）
# -------------------------------
level1_map = [
    "                                        ",
    "                                        ",
    "                                        ",
    "                                        ",
    "                                        ",
    "                                        ",
    "                                        ",
    "           XXXX                         ",
    "                                        ",
    "       P        XXX         XXX         ",
    "XXXXXXXXXXXX  XXXXXXXXX  XXXXXXXXXXXXXXXF"
]

level2_map = [
    "                                        ",
    "                                        ",
    "                                        ",
    "                                        ",
    "              O                         ",
    "           XXXX          O              ",
    "                                        ",
    "       P        XXX         XXX         ",
    "XXXXXXXXXXXX  XXXXXXXXX  XXXXXXXXXXXXXXXF"
]

level3_map = [
    "                                        ",
    "                                        ",
    "                           O            ",
    "                                        ",
    "           OXXXX           XXX           ",
    "       P        XXX   O    XXXXXXX       ",
    "XXXXXXXXXXXX  XXXXXXXXX  XXXXXXXXXXXXXXXF"
]

levels = [level1_map, level2_map, level3_map]

# -------------------------------
# 辅助函数：加载图片
# -------------------------------
def load_image(path, width=None, height=None):
    try:
        image = pygame.image.load(path).convert_alpha()
        if width and height:
            image = pygame.transform.scale(image, (width, height))
        return image
    except Exception as e:
        print(f"加载 {path} 失败：", e)
        # 返回一个填充色的 Surface
        surface = pygame.Surface((width or TILE_SIZE, height or TILE_SIZE))
        surface.fill(WHITE)
        return surface

# -------------------------------
# 精灵类定义
# -------------------------------
class Block(pygame.sprite.Sprite):
    """地图中的砖块"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))

class Obstacle(pygame.sprite.Sprite):
    """障碍物（碰到则关卡失败）"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x, y))

class Flag(pygame.sprite.Sprite):
    """关卡终点的旗帜"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))

class Player(pygame.sprite.Sprite):
    """玩家控制的角色，使用图片 mario.png"""
    def __init__(self, x, y, blocks):
        super().__init__()
        # 尝试加载 mario.png 图片（在 images 目录下）
        self.image = load_image("images/mario.png", TILE_SIZE, TILE_SIZE)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.blocks = blocks  # 用于碰撞检测

        # 物理属性
        self.speed = 5
        self.jump_speed = -12
        self.gravity = 0.5
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False

    def update(self):
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
        if keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
        # 按空格键跳跃（仅在落地时允许）
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = self.jump_speed
            self.on_ground = False

        # 重力影响
        self.vel_y += self.gravity

        # 水平移动并检测碰撞
        self.rect.x += self.vel_x
        self.collide(self.vel_x, 0)

        # 垂直移动并检测碰撞
        self.rect.y += self.vel_y
        self.on_ground = False
        self.collide(0, self.vel_y)

    def collide(self, vel_x, vel_y):
        for block in self.blocks:
            if self.rect.colliderect(block.rect):
                if vel_x > 0:   # 向右移动碰撞：贴左边
                    self.rect.right = block.rect.left
                if vel_x < 0:   # 向左移动碰撞
                    self.rect.left = block.rect.right
                if vel_y > 0:   # 下落碰撞：贴上
                    self.rect.bottom = block.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                if vel_y < 0:   # 上升碰撞
                    self.rect.top = block.rect.bottom
                    self.vel_y = 0

# -------------------------------
# 关卡数据生成
# -------------------------------
def create_level(level_map):
    """
    根据传入的字符地图生成砖块、障碍物、旗帜和玩家起始位置
    """
    blocks = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    flag = None
    player_start = None

    rows = len(level_map)
    cols = max(len(row) for row in level_map)
    # 计算关卡宽高（用于摄像机边界控制）
    level_width = cols * TILE_SIZE
    level_height = rows * TILE_SIZE

    for row_idx, row in enumerate(level_map):
        for col_idx, char in enumerate(row):
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE
            if char == "X":
                block = Block(x, y)
                blocks.add(block)
            elif char == "O":
                obs = Obstacle(x, y)
                obstacles.add(obs)
            elif char == "P":
                player_start = (x, y)
            elif char == "F":
                flag = Flag(x, y)
            elif char == "G":
                flag = Flag(x, y)
    return blocks, obstacles, flag, player_start, level_width, level_height

# -------------------------------
# 辅助函数：显示信息
# -------------------------------
def show_message(screen, text, duration=2):
    font = pygame.font.SysFont(None, 72)
    render = font.render(text, True, RED)
    rect = render.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(render, rect)
    pygame.display.flip()
    time.sleep(duration)

def show_game_over(screen):
    show_message(screen, "Game Over", duration=2)

def show_level_complete(screen, text="Level Complete! Next", duration=2):
    show_message(screen, text, duration=duration)

# -------------------------------
# 运行单个关卡
# -------------------------------
def run_level(level_map, screen, clock, bg_img):
    blocks, obstacles, flag, player_start, level_width, level_height = create_level(level_map)
    all_sprites = pygame.sprite.Group()
    all_sprites.add(blocks)
    all_sprites.add(obstacles)
    if flag:
        all_sprites.add(flag)

    # 创建玩家精灵（使用 mario.png）
    player = Player(player_start[0], player_start[1], blocks)
    all_sprites.add(player)

    level_complete = False
    running = True

    # 摄像机偏移值
    camera_x = 0
    camera_y = 0

    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        player.update()

        # 检查与障碍物碰撞（失败）
        if pygame.sprite.spritecollide(player, obstacles, False):
            show_game_over(screen)
            return "restart"

        # 检查是否碰到旗帜（过关）
        if flag and player.rect.colliderect(flag.rect):
            level_complete = True

        # 计算摄像机偏移，使玩家尽量位于屏幕中央
        camera_x = player.rect.centerx - SCREEN_WIDTH // 2
        camera_y = player.rect.centery - SCREEN_HEIGHT // 2
        camera_x = max(0, min(camera_x, level_width - SCREEN_WIDTH))
        camera_y = max(0, min(camera_y, level_height - SCREEN_HEIGHT))

        # 绘制背景（先绘制背景图片）
        screen.blit(bg_img, (0, 0))
        # 绘制所有精灵，坐标减去摄像机偏移
        for sprite in all_sprites:
            screen.blit(sprite.image, (sprite.rect.x - camera_x, sprite.rect.y - camera_y))
        pygame.display.flip()

        if level_complete:
            show_level_complete(screen)
            return "complete"

# -------------------------------
# 主函数：循环三个关卡
# -------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mario-like Game")
    clock = pygame.time.Clock()

    # 加载背景图片 background.png，并缩放到屏幕大小
    bg_img = load_image("images/background.png", SCREEN_WIDTH, SCREEN_HEIGHT)

    current_level = 0
    total_levels = len(levels)
    while current_level < total_levels:
        result = run_level(levels[current_level], screen, clock, bg_img)
        if result == "complete":
            current_level += 1
        elif result == "restart":
            continue

    # 三关全部通过后显示最终提示
    show_message(screen, "Game Completed!", duration=3)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
