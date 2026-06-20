"""
马里奥风格横版闯关游戏 - 精灵系统
包含所有游戏实体：玩家、敌人、道具、方块、特效
"""

import pygame
import math
from settings import *


def get_collision_rect(x, y, width, height):
    """创建碰撞矩形"""
    return pygame.Rect(x, y, width, height)


# ================================================================
#                       玩家角色（马里奥）
# ================================================================
class Player(pygame.sprite.Sprite):
    """
    玩家角色 - 马里奥
    状态机：idle, running, jumping, falling, dead, growing, shrinking
    支持：小/大两种形态，无敌星效果，受伤无敌帧
    """

    def __init__(self, x, y):
        super().__init__()
        # ---- 位置与物理 ----
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True

        # ---- 碰撞框 ----
        self.width = 24
        self.height = 32
        self.rect = pygame.Rect(x, y, self.width, self.height)

        # ---- 状态 ----
        self.state = 'idle'         # idle, running, jumping, falling, dead
        self.big = False            # 是否变大
        self.alive = True
        self.at_flag = False        # 是否到达终点

        # ---- 生命与分数 ----
        self.lives = INITIAL_LIVES
        self.coins = 0
        self.score = 0

        # ---- 特殊状态计时器 ----
        self.invincible_timer = 0   # 受伤无敌
        self.star_timer = 0         # 无敌星
        self.grow_timer = 0         # 变大动画

        # ---- 动画 ----
        self.anim_frame = 0
        self.anim_timer = 0

        # ---- 跳跃优化 ----
        self.jump_buffer_timer = 0   # 跳跃缓冲：落地前按跳，落地瞬间自动跳
        self.coyote_timer = 0        # 土狼时间：离开平台后仍可跳的时间
        self.was_on_ground = False   # 上一帧是否在地面

        # ---- 重生点 ----
        self.spawn_x = float(x)
        self.spawn_y = float(y)

        # ---- 死亡动画 ----
        self.death_timer = 0
        self.death_vel_y = 0

    @property
    def invincible(self):
        """是否处于无敌状态"""
        return self.invincible_timer > 0 or self.star_timer > 0

    @property
    def has_star(self):
        """是否拥有无敌星效果"""
        return self.star_timer > 0

    def set_big(self, big):
        """切换大/小状态，保持脚部位置不变"""
        if self.big == big:
            return
        old_bottom = self.rect.bottom
        self.big = big
        if big:
            self.height = 56
        else:
            self.height = 32
        self.rect = pygame.Rect(self.rect.x, old_bottom - self.height,
                                self.width, self.height)
        self.pos_y = float(self.rect.y)

    def request_jump(self):
        """
        请求跳跃（在按键事件中调用）
        实现跳跃缓冲：即使还没落地，也记住这个请求
        """
        self.jump_buffer_timer = 10  # 10帧缓冲窗口

    def jump(self):
        """执行跳跃（在update中自动调用）"""
        if self.alive and (self.on_ground or self.coyote_timer > 0):
            force = PLAYER_JUMP_FORCE_BIG if self.big else PLAYER_JUMP_FORCE
            self.vel_y = force
            self.on_ground = False
            self.coyote_timer = 0
            self.jump_buffer_timer = 0

    def die(self):
        """玩家死亡"""
        if not self.alive:
            return
        if self.invincible:
            return
        if self.big:
            # 大状态受伤变小
            self.set_big(False)
            self.invincible_timer = INVINCIBLE_TIME
            return
        # 小状态死亡
        self.alive = False
        self.state = 'dead'
        self.death_timer = 0
        self.death_vel_y = -10
        self.vel_x = 0
        self.vel_y = 0
        self.lives -= 1

    def respawn(self):
        """重生"""
        self.pos_x = self.spawn_x
        self.pos_y = self.spawn_y
        self.vel_x = 0
        self.vel_y = 0
        self.alive = True
        self.state = 'idle'
        self.big = False
        self.height = 32
        self.rect = pygame.Rect(int(self.pos_x), int(self.pos_y),
                                self.width, self.height)
        self.invincible_timer = 60  # 重生短暂无敌
        self.star_timer = 0
        self.death_timer = 0
        self.on_ground = False

    def collect_coin(self):
        """收集金币"""
        self.coins += 1
        self.score += 200
        if self.coins >= COINS_FOR_LIFE:
            self.coins -= COINS_FOR_LIFE
            self.lives = min(self.lives + 1, MAX_LIVES)

    def add_score(self, points):
        """增加分数"""
        self.score += points

    def update(self, tiles, enemies, items):
        """
        主更新逻辑
        tiles: 可碰撞的瓷砖列表 [(rect, type), ...]
        """
        if not self.alive:
            # 死亡动画：弹起再落下
            self.death_timer += 1
            self.death_vel_y += GRAVITY * 0.5
            self.pos_y += self.death_vel_y
            self.rect.y = int(self.pos_y)
            return

        # ---- 计时器更新 ----
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.star_timer > 0:
            self.star_timer -= 1
        if self.grow_timer > 0:
            self.grow_timer -= 1
            return  # 变大动画期间不移动

        # ---- 读取输入 ----
        keys = pygame.key.get_pressed()
        acc_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            acc_x = -PLAYER_ACC
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            acc_x = PLAYER_ACC
            self.facing_right = True

        # ---- 跳跃核心优化 ----
        # 1. 连跳与缓冲：如果按住空格，且满足地面或土狼时间条件，直接起跳
        if keys[pygame.K_SPACE]:
            if self.on_ground or self.coyote_timer > 0:
                self.jump()
        else:
            # 2. 蓄力跳控制：如果在上升过程中提早松开了空格键，则大幅衰减向上速度，实现微操跳跃高度
            if self.vel_y < -3.0:
                self.vel_y = -3.0

        # ---- 水平运动 ----
        self.vel_x += acc_x
        if acc_x == 0:
            # 摩擦减速
            self.vel_x += PLAYER_FRICTION * self.vel_x
            if abs(self.vel_x) < 0.3:
                self.vel_x = 0
        # 限速
        self.vel_x = max(-PLAYER_MAX_SPEED_X, min(PLAYER_MAX_SPEED_X, self.vel_x))

        # ---- 重力 ----
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # ---- 水平移动 + 碰撞检测 ----
        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)

        # 水平碰撞
        for tile_rect, tile_type in tiles:
            if self.rect.colliderect(tile_rect):
                if self.vel_x > 0:  # 向右撞
                    self.rect.right = tile_rect.left
                elif self.vel_x < 0:  # 向左撞
                    self.rect.left = tile_rect.right
                self.pos_x = float(self.rect.x)
                self.vel_x = 0

        # 不能走出地图左边界
        if self.rect.left < 0:
            self.rect.left = 0
            self.pos_x = 0
            self.vel_x = 0

        # ---- 垂直移动 + 碰撞检测 ----
        old_bottom = self.rect.bottom
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)
        self.on_ground = False

        for tile_rect, tile_type in tiles:
            if self.rect.colliderect(tile_rect):
                if self.vel_y > 0:  # 下落着地
                    if old_bottom <= tile_rect.top + 6:  # 略微放宽着地判定边缘
                        self.rect.bottom = tile_rect.top
                        self.pos_y = float(self.rect.y)
                        self.vel_y = 0
                        self.on_ground = True
                elif self.vel_y < 0:  # 头部撞击
                    if self.rect.top < tile_rect.bottom and self.rect.top >= tile_rect.top:
                        self.rect.top = tile_rect.bottom
                        self.pos_y = float(self.rect.y)
                        self.vel_y = 0
                        # 返回被撞击的方块信息
                        return ('head_hit', tile_rect, tile_type)

        # ---- 土狼时间衰减 ----
        if self.was_on_ground and not self.on_ground and self.vel_y >= 0:
            self.coyote_timer = 8  # 8帧土狼时间
        if self.coyote_timer > 0:
            self.coyote_timer -= 1

        self.was_on_ground = self.on_ground

        # ---- 掉落死亡 ----
        if self.rect.top > SCREEN_HEIGHT + 100:
            self.die()

        # ---- 更新状态 ----
        if not self.on_ground:
            if self.vel_y < 0:
                self.state = 'jumping'
            else:
                self.state = 'falling'
        elif abs(self.vel_x) > 0.5:
            self.state = 'running'
        else:
            self.state = 'idle'

        # ---- 动画帧 ----
        self.anim_timer += 1
        if self.anim_timer >= PLAYER_ANIM_SPEED:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 3

        return None

    def draw(self, surface, camera_x):
        """绘制玩家"""
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y

        # 无敌闪烁效果
        if self.invincible_timer > 0 and self.invincible_timer % 4 < 2:
            return  # 闪烁：每隔几帧不绘制
        if self.has_star and self.star_timer % 4 < 2:
            return

        # 无敌星颜色变化
        color = MARIO_RED
        if self.has_star:
            colors = [MARIO_RED, STAR_YELLOW, STAR_ORANGE, (255, 100, 100)]
            color = colors[(self.star_timer // 3) % len(colors)]

        if self.big:
            # ---- 大马里奥 ----
            # 帽子
            pygame.draw.rect(surface, color,
                           (draw_x - 2, draw_y, self.width + 4, 12))
            # 脸
            pygame.draw.rect(surface, MARIO_SKIN,
                           (draw_x, draw_y + 12, self.width, 12))
            # 身体
            pygame.draw.rect(surface, color,
                           (draw_x - 1, draw_y + 24, self.width + 2, 16))
            # 裤子
            pygame.draw.rect(surface, (0, 0, 180),
                           (draw_x, draw_y + 40, self.width, 10))
            # 鞋子
            shoe_offset = 0
            if self.state == 'running':
                shoe_offset = (self.anim_frame - 1) * 3
            pygame.draw.rect(surface, MARIO_BROWN,
                           (draw_x - 2 + shoe_offset, draw_y + 50, 12, 6))
            pygame.draw.rect(surface, MARIO_BROWN,
                           (draw_x + 14 - shoe_offset, draw_y + 50, 12, 6))
        else:
            # ---- 小马里奥 ----
            # 帽子
            pygame.draw.rect(surface, color,
                           (draw_x - 1, draw_y, self.width + 2, 8))
            # 脸
            pygame.draw.rect(surface, MARIO_SKIN,
                           (draw_x, draw_y + 8, self.width, 8))
            # 身体
            pygame.draw.rect(surface, color,
                           (draw_x, draw_y + 16, self.width, 8))
            # 腿
            shoe_offset = 0
            if self.state == 'running':
                shoe_offset = (self.anim_frame - 1) * 2
            pygame.draw.rect(surface, (0, 0, 180),
                           (draw_x + 2, draw_y + 24, self.width - 4, 4))
            pygame.draw.rect(surface, MARIO_BROWN,
                           (draw_x - 1 + shoe_offset, draw_y + 28, 10, 4))
            pygame.draw.rect(surface, MARIO_BROWN,
                           (draw_x + 15 - shoe_offset, draw_y + 28, 10, 4))

        # 跳跃时的腿部动作
        if self.state == 'jumping' or self.state == 'falling':
            if not self.big:
                pygame.draw.rect(surface, MARIO_BROWN,
                               (draw_x - 2, draw_y + 28, 8, 4))
                pygame.draw.rect(surface, MARIO_BROWN,
                               (draw_x + 18, draw_y + 26, 8, 4))


# ================================================================
#                          敌人系统
# ================================================================
class Goomba(pygame.sprite.Sprite):
    """
    板栗仔 - 最基础的敌人
    行为：左右巡逻，遇墙转向，可被踩灭
    """

    def __init__(self, x, y):
        super().__init__()
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vel_x = -ENEMY_SPEED
        self.vel_y = 0.0
        self.width = 28
        self.height = 28
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.alive = True
        self.squished = False
        self.squish_timer = 0
        self.on_ground = False
        self.anim_frame = 0
        self.anim_timer = 0

    def update(self, tiles):
        if not self.alive:
            if self.squished:
                self.squish_timer += 1
                if self.squish_timer > 30:
                    self.kill()
            return

        # 重力
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # 水平移动
        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)

        # 水平碰撞
        for tile_rect, _ in tiles:
            if self.rect.colliderect(tile_rect):
                if self.vel_x > 0:
                    self.rect.right = tile_rect.left
                    self.vel_x = -abs(self.vel_x)
                elif self.vel_x < 0:
                    self.rect.left = tile_rect.right
                    self.vel_x = abs(self.vel_x)
                self.pos_x = float(self.rect.x)

        # 垂直移动
        old_bottom = self.rect.bottom
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)
        self.on_ground = False

        for tile_rect, _ in tiles:
            if self.rect.colliderect(tile_rect):
                if self.vel_y > 0 and old_bottom <= tile_rect.top + 4:
                    self.rect.bottom = tile_rect.top
                    self.pos_y = float(self.rect.y)
                    self.vel_y = 0
                    self.on_ground = True

        # 掉出屏幕
        if self.rect.top > SCREEN_HEIGHT + 50:
            self.kill()

        # 动画
        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

    def stomp(self):
        """被踩灭"""
        self.alive = False
        self.squished = True
        self.squish_timer = 0
        self.vel_x = 0
        self.vel_y = 0

    def draw(self, surface, camera_x):
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y

        if self.squished:
            # 被踩扁的样子
            pygame.draw.rect(surface, GOOMBA_BROWN,
                           (draw_x - 2, draw_y + 20, self.width + 4, 8))
            return

        # 身体（圆形）
        center_x = draw_x + self.width // 2
        center_y = draw_y + 12
        pygame.draw.ellipse(surface, GOOMBA_BROWN,
                          (draw_x, draw_y, self.width, 20))

        # 深色底部
        pygame.draw.ellipse(surface, GOOMBA_DARK,
                          (draw_x + 2, draw_y + 10, self.width - 4, 12))

        # 眼睛
        eye_x1 = draw_x + 7
        eye_x2 = draw_x + 17
        eye_y = draw_y + 8
        pygame.draw.circle(surface, WHITE, (eye_x1, eye_y), 4)
        pygame.draw.circle(surface, WHITE, (eye_x2, eye_y), 4)
        pygame.draw.circle(surface, BLACK, (eye_x1 + 1, eye_y), 2)
        pygame.draw.circle(surface, BLACK, (eye_x2 + 1, eye_y), 2)

        # 眉毛（怒气）
        pygame.draw.line(surface, GOOMBA_DARK,
                        (eye_x1 - 2, eye_y - 5), (eye_x1 + 4, eye_y - 3), 2)
        pygame.draw.line(surface, GOOMBA_DARK,
                        (eye_x2 + 4, eye_y - 5), (eye_x2 - 2, eye_y - 3), 2)

        # 脚（交替动画）
        foot_y = draw_y + 20
        if self.anim_frame == 0:
            pygame.draw.ellipse(surface, GOOMBA_DARK,
                              (draw_x - 2, foot_y, 12, 8))
            pygame.draw.ellipse(surface, GOOMBA_DARK,
                              (draw_x + 18, foot_y, 12, 8))
        else:
            pygame.draw.ellipse(surface, GOOMBA_DARK,
                              (draw_x + 2, foot_y, 12, 8))
            pygame.draw.ellipse(surface, GOOMBA_DARK,
                              (draw_x + 14, foot_y, 12, 8))


class PiranhaPlant(pygame.sprite.Sprite):
    """
    食人花 - 从水管中定时伸出缩回
    状态：hidden -> rising -> exposed -> falling -> hidden
    """

    def __init__(self, x, y, pipe_top_y):
        super().__init__()
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.pipe_top_y = pipe_top_y  # 水管顶部Y坐标
        self.hidden_y = pipe_top_y + 40  # 完全隐藏时的Y
        self.exposed_y = pipe_top_y - 20  # 完全露出时的Y
        self.width = 28
        self.height = 36
        self.rect = pygame.Rect(x, int(self.pos_y), self.width, self.height)

        # 状态机
        self.state = 'hidden'   # hidden, rising, exposed, falling
        self.timer = 0
        self.hidden_duration = 90   # 隐藏持续帧数
        self.exposed_duration = 120 # 暴露持续帧数
        self.move_speed = 1

        self.alive = True

    def update(self, player=None):
        if not self.alive:
            return

        # 如果玩家站在水管上方或距离太近，压制食人花不露头
        if player and self.state == 'hidden':
            dist = math.hypot(player.rect.centerx - self.rect.centerx,
                              player.rect.centery - self.rect.centery)
            if dist < 96:
                self.timer = 0  # 重置计时器，不让它出来
                return

        self.timer += 1

        if self.state == 'hidden':
            if self.timer >= self.hidden_duration:
                self.state = 'rising'
                self.timer = 0

        elif self.state == 'rising':
            self.pos_y -= self.move_speed
            self.rect.y = int(self.pos_y)
            if self.pos_y <= self.exposed_y:
                self.pos_y = self.exposed_y
                self.state = 'exposed'
                self.timer = 0

        elif self.state == 'exposed':
            if self.timer >= self.exposed_duration:
                self.state = 'falling'
                self.timer = 0

        elif self.state == 'falling':
            self.pos_y += self.move_speed
            self.rect.y = int(self.pos_y)
            if self.pos_y >= self.hidden_y:
                self.pos_y = self.hidden_y
                self.state = 'hidden'
                self.timer = 0

    def is_visible(self):
        """是否可见（可以被碰撞）"""
        return self.state in ('rising', 'exposed')

    def draw(self, surface, camera_x):
        if self.state == 'hidden':
            return

        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y

        # 茎（绿色）
        pygame.draw.rect(surface, PIRANHA_GREEN,
                        (draw_x + 6, draw_y + 16, 16, 20))

        # 头部（红绿相间）
        # 上半部分
        pygame.draw.ellipse(surface, PIRANHA_RED,
                          (draw_x, draw_y, self.width, 18))
        # 白色斑点
        pygame.draw.circle(surface, PIRANHA_WHITE,
                         (draw_x + 7, draw_y + 6), 3)
        pygame.draw.circle(surface, PIRANHA_WHITE,
                         (draw_x + 21, draw_y + 6), 3)

        # 嘴巴（白色锯齿）
        mouth_y = draw_y + 12
        for i in range(4):
            tx = draw_x + 3 + i * 6
            pygame.draw.polygon(surface, WHITE, [
                (tx, mouth_y),
                (tx + 3, mouth_y + 5),
                (tx + 6, mouth_y)
            ])


# ================================================================
#                          道具系统
# ================================================================
class Coin(pygame.sprite.Sprite):
    """金币 - 静态收集品或从方块弹出"""

    def __init__(self, x, y, popup=False):
        super().__init__()
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect = pygame.Rect(x + 6, y + 4, 20, 24)
        self.alive = True
        self.popup = popup          # 是否从方块弹出
        self.popup_vel_y = -10 if popup else 0
        self.anim_frame = 0
        self.anim_timer = 0
        self.popup_timer = 0

    def update(self):
        if self.popup:
            self.popup_vel_y += 0.5
            self.pos_y += self.popup_vel_y
            self.rect.y = int(self.pos_y)
            self.popup_timer += 1
            if self.popup_timer > 40:
                self.kill()
                return
        # 动画
        self.anim_timer += 1
        if self.anim_timer >= COIN_ANIM_SPEED:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4

    def draw(self, surface, camera_x):
        draw_x = self.rect.x - camera_x + 4
        draw_y = self.rect.y + 2

        # 旋转效果：改变宽度模拟3D旋转
        widths = [16, 12, 4, 12]
        w = widths[self.anim_frame]
        cx = draw_x + 8  # 中心x
        if w > 2:
            pygame.draw.ellipse(surface, COIN_YELLOW,
                              (cx - w // 2, draw_y, w, 20))
            pygame.draw.ellipse(surface, COIN_LIGHT,
                              (cx - w // 2 + 2, draw_y + 3, max(w - 4, 2), 14))
        else:
            # 侧面（细线）
            pygame.draw.line(surface, COIN_YELLOW,
                           (cx, draw_y), (cx, draw_y + 20), 2)


class Mushroom(pygame.sprite.Sprite):
    """
    蘑菇道具 - 从问号方块弹出后向右移动
    效果：小马里奥变大
    """

    def __init__(self, x, y):
        super().__init__()
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vel_x = ITEM_MOVE_SPEED
        self.vel_y = 0.0
        self.width = 28
        self.height = 28
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.alive = True
        self.spawning = True
        self.spawn_target_y = y
        self.pos_y = float(y + TILE_SIZE)  # 从方块内部开始
        self.rect.y = int(self.pos_y)

    def update(self, tiles):
        # 从方块中升起
        if self.spawning:
            self.pos_y -= 2
            self.rect.y = int(self.pos_y)
            if self.pos_y <= self.spawn_target_y:
                self.pos_y = self.spawn_target_y
                self.spawning = False
            return

        # 重力
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # 水平移动
        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)

        # 水平碰撞
        for tile_rect, _ in tiles:
            if self.rect.colliderect(tile_rect):
                if self.vel_x > 0:
                    self.rect.right = tile_rect.left
                    self.vel_x = -abs(self.vel_x)
                elif self.vel_x < 0:
                    self.rect.left = tile_rect.right
                    self.vel_x = abs(self.vel_x)
                self.pos_x = float(self.rect.x)

        # 垂直移动
        old_bottom = self.rect.bottom
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)

        for tile_rect, _ in tiles:
            if self.rect.colliderect(tile_rect):
                if self.vel_y > 0 and old_bottom <= tile_rect.top + 4:
                    self.rect.bottom = tile_rect.top
                    self.pos_y = float(self.rect.y)
                    self.vel_y = 0

        # 掉出屏幕
        if self.rect.top > SCREEN_HEIGHT + 50:
            self.kill()

    def draw(self, surface, camera_x):
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y

        # 蘑菇帽（红色圆顶）
        pygame.draw.ellipse(surface, MUSHROOM_RED,
                          (draw_x - 2, draw_y, self.width + 4, 18))
        # 白色斑点
        pygame.draw.circle(surface, WHITE,
                         (draw_x + self.width // 2, draw_y + 5), 5)
        pygame.draw.circle(surface, WHITE,
                         (draw_x + 5, draw_y + 10), 3)
        pygame.draw.circle(surface, WHITE,
                         (draw_x + self.width - 5, draw_y + 10), 3)

        # 茎（肤色）
        pygame.draw.rect(surface, MUSHROOM_TAN,
                        (draw_x + 6, draw_y + 14, 16, 14))
        # 眼睛
        pygame.draw.circle(surface, BLACK, (draw_x + 10, draw_y + 20), 2)
        pygame.draw.circle(surface, BLACK, (draw_x + 18, draw_y + 20), 2)


class Star(pygame.sprite.Sprite):
    """
    无敌星 - 从方块弹出后弹跳移动
    效果：短时间无敌 + 加速
    """

    def __init__(self, x, y):
        super().__init__()
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vel_x = ITEM_MOVE_SPEED
        self.vel_y = 0.0
        self.width = 28
        self.height = 28
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.alive = True
        self.spawning = True
        self.spawn_target_y = y
        self.pos_y = float(y + TILE_SIZE)
        self.rect.y = int(self.pos_y)
        self.anim_timer = 0

    def update(self, tiles):
        if self.spawning:
            self.pos_y -= 2
            self.rect.y = int(self.pos_y)
            if self.pos_y <= self.spawn_target_y:
                self.pos_y = self.spawn_target_y
                self.spawning = False
            return

        # 重力
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # 弹跳效果
        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)

        for tile_rect, _ in tiles:
            if self.rect.colliderect(tile_rect):
                if self.vel_x > 0:
                    self.rect.right = tile_rect.left
                    self.vel_x = -abs(self.vel_x)
                elif self.vel_x < 0:
                    self.rect.left = tile_rect.right
                    self.vel_x = abs(self.vel_x)
                self.pos_x = float(self.rect.x)

        old_bottom = self.rect.bottom
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)

        for tile_rect, _ in tiles:
            if self.rect.colliderect(tile_rect):
                if self.vel_y > 0 and old_bottom <= tile_rect.top + 4:
                    self.rect.bottom = tile_rect.top
                    self.pos_y = float(self.rect.y)
                    self.vel_y = ITEM_BOUNCE  # 弹跳

        if self.rect.top > SCREEN_HEIGHT + 50:
            self.kill()

        self.anim_timer += 1

    def draw(self, surface, camera_x):
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y
        cx = draw_x + self.width // 2
        cy = draw_y + self.height // 2

        # 闪烁颜色
        colors = [STAR_YELLOW, STAR_ORANGE, WHITE, STAR_YELLOW]
        color = colors[(self.anim_timer // 3) % len(colors)]

        # 绘制五角星
        r = 12
        points = []
        for i in range(5):
            angle = math.radians(-90 + i * 72)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            angle2 = math.radians(-90 + i * 72 + 36)
            points.append((cx + r * 0.4 * math.cos(angle2),
                          cy + r * 0.4 * math.sin(angle2)))

        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, BLACK, points, 2)

        # 眼睛
        pygame.draw.circle(surface, BLACK, (cx - 3, cy - 2), 2)
        pygame.draw.circle(surface, BLACK, (cx + 3, cy - 2), 2)


# ================================================================
#                         方块系统
# ================================================================
class QuestionBlock(pygame.sprite.Sprite):
    """问号方块 - 被顶后弹出道具"""

    def __init__(self, x, y, contains='coin'):
        super().__init__()
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.contains = contains  # 'coin', 'mushroom', 'star'
        self.used = False
        self.bump_offset = 0    # 被顶时的弹跳偏移
        self.bump_vel = 0
        self.anim_frame = 0
        self.anim_timer = 0

    def hit(self):
        """被从下方顶到"""
        if self.used:
            return None
        self.used = True
        self.bump_vel = -4  # 弹起

        if self.contains == 'coin':
            return ('coin', self.rect.x, self.rect.y - TILE_SIZE)
        elif self.contains == 'mushroom':
            return ('mushroom', self.rect.x, self.rect.y - TILE_SIZE)
        elif self.contains == 'star':
            return ('star', self.rect.x, self.rect.y - TILE_SIZE)
        return None

    def update(self):
        # 弹跳动画
        if self.bump_offset != 0 or self.bump_vel != 0:
            self.bump_vel += 0.5
            self.bump_offset += self.bump_vel
            if self.bump_offset >= 0:
                self.bump_offset = 0
                self.bump_vel = 0

        # 动画
        if not self.used:
            self.anim_timer += 1
            if self.anim_timer >= 12:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 4

    def draw(self, surface, camera_x):
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y + int(self.bump_offset)

        if self.used:
            # 已使用的方块
            pygame.draw.rect(surface, USED_BLOCK,
                           (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(surface, (120, 95, 60),
                           (draw_x, draw_y, TILE_SIZE, TILE_SIZE), 2)
        else:
            # 问号方块
            pygame.draw.rect(surface, QUESTION_YELLOW,
                           (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
            # 高光
            pygame.draw.rect(surface, QUESTION_LIGHT,
                           (draw_x + 2, draw_y + 2, 6, TILE_SIZE - 4))
            # 边框
            pygame.draw.rect(surface, QUESTION_DARK,
                           (draw_x, draw_y, TILE_SIZE, TILE_SIZE), 2)
            # "?" 文字
            # 闪烁效果
            if self.anim_frame < 2:
                text_color = QUESTION_DARK
            else:
                text_color = WHITE
            font = pygame.font.SysFont('Arial', 18, bold=True)
            text = font.render('?', True, text_color)
            text_rect = text.get_rect(center=(draw_x + TILE_SIZE // 2,
                                              draw_y + TILE_SIZE // 2))
            surface.blit(text, text_rect)


class BrickBlock(pygame.sprite.Sprite):
    """砖块 - 大状态可击碎，小状态只弹跳"""

    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.alive = True
        self.bump_offset = 0
        self.bump_vel = 0
        self.fragments = []  # 碎片动画

    def hit(self, is_big):
        """被从下方顶到"""
        if is_big:
            # 击碎 - 生成碎片
            self.alive = False
            self.fragments = [
                {'x': self.rect.x, 'y': self.rect.y, 'vx': -3, 'vy': -8},
                {'x': self.rect.x + 16, 'y': self.rect.y, 'vx': 3, 'vy': -8},
                {'x': self.rect.x, 'y': self.rect.y + 16, 'vx': -2, 'vy': -5},
                {'x': self.rect.x + 16, 'y': self.rect.y + 16, 'vx': 2, 'vy': -5},
            ]
            return 'break'
        else:
            # 只弹跳
            self.bump_vel = -4
            return 'bump'

    def update(self):
        if self.bump_offset != 0 or self.bump_vel != 0:
            self.bump_vel += 0.5
            self.bump_offset += self.bump_vel
            if self.bump_offset >= 0:
                self.bump_offset = 0
                self.bump_vel = 0

        # 碎片动画
        for f in self.fragments:
            f['vy'] += 0.4
            f['x'] += f['vx']
            f['y'] += f['vy']

    def draw(self, surface, camera_x):
        if not self.alive:
            # 绘制碎片
            for f in self.fragments:
                fx = f['x'] - camera_x
                fy = f['y']
                if fy < SCREEN_HEIGHT + 50:
                    pygame.draw.rect(surface, BRICK_COLOR,
                                   (int(fx), int(fy), 12, 12))
                    pygame.draw.rect(surface, BRICK_DARK,
                                   (int(fx), int(fy), 12, 12), 1)
            return

        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y + int(self.bump_offset)

        # 砖块主体
        pygame.draw.rect(surface, BRICK_COLOR,
                        (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
        # 砖块纹路
        pygame.draw.line(surface, BRICK_DARK,
                        (draw_x, draw_y + 8), (draw_x + TILE_SIZE, draw_y + 8), 1)
        pygame.draw.line(surface, BRICK_DARK,
                        (draw_x, draw_y + 20), (draw_x + TILE_SIZE, draw_y + 20), 1)
        pygame.draw.line(surface, BRICK_DARK,
                        (draw_x + 16, draw_y), (draw_x + 16, draw_y + 12), 1)
        pygame.draw.line(surface, BRICK_DARK,
                        (draw_x + 8, draw_y + 12), (draw_x + 8, draw_y + TILE_SIZE), 1)
        pygame.draw.line(surface, BRICK_DARK,
                        (draw_x + 24, draw_y + 12), (draw_x + 24, draw_y + TILE_SIZE), 1)
        # 高光
        pygame.draw.line(surface, BRICK_LIGHT,
                        (draw_x, draw_y), (draw_x + TILE_SIZE, draw_y), 1)
        pygame.draw.line(surface, BRICK_LIGHT,
                        (draw_x, draw_y), (draw_x, draw_y + TILE_SIZE), 1)
        # 边框
        pygame.draw.rect(surface, BRICK_DARK,
                        (draw_x, draw_y, TILE_SIZE, TILE_SIZE), 1)


# ================================================================
#                         特效粒子
# ================================================================
class ScorePopup(pygame.sprite.Sprite):
    """分数弹出特效（踩敌、收集金币时显示）"""

    def __init__(self, x, y, text):
        super().__init__()
        self.x = x
        self.y = y
        self.text = text
        self.timer = 0
        self.duration = 40

    def update(self):
        self.timer += 1
        self.y -= 1.5
        if self.timer >= self.duration:
            self.kill()

    def draw(self, surface, camera_x):
        alpha = 255 - int(255 * self.timer / self.duration)
        font = pygame.font.SysFont('Arial', 14, bold=True)
        text_surf = font.render(self.text, True, WHITE)
        text_surf.set_alpha(max(0, alpha))
        surface.blit(text_surf, (self.x - camera_x, self.y))


# ================================================================
#                         终点旗帜
# ================================================================
class Flagpole(pygame.sprite.Sprite):
    """终点旗帜 - 触碰后播放过关动画"""

    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.pole_height = TILE_SIZE * 10
        self.pole_rect = pygame.Rect(x + 12, y, 4, self.pole_height)
        self.flag_y = y + 8
        self.flag_target_y = y + self.pole_height - TILE_SIZE
        self.triggered = False
        self.flag_descending = False

    def trigger(self):
        """触碰旗帜"""
        if not self.triggered:
            self.triggered = True
            self.flag_descending = True

    def update(self):
        if self.flag_descending:
            self.flag_y += 3
            if self.flag_y >= self.flag_target_y:
                self.flag_y = self.flag_target_y
                self.flag_descending = False

    def is_complete(self):
        """旗帜动画是否完成"""
        return self.triggered and not self.flag_descending

    def draw(self, surface, camera_x):
        draw_x = self.x - camera_x

        # 旗杆
        pygame.draw.rect(surface, FLAGPOLE_GRAY,
                        (draw_x + 14, self.y, 4, self.pole_height))
        # 顶部圆球
        pygame.draw.circle(surface, FLAGPOLE_GRAY,
                         (draw_x + 16, self.y), 6)

        # 旗帜
        if self.triggered:
            flag_color = FLAG_GREEN
        else:
            flag_color = RED

        flag_points = [
            (draw_x + 18, int(self.flag_y)),
            (draw_x + 48, int(self.flag_y) + 12),
            (draw_x + 18, int(self.flag_y) + 24),
        ]
        pygame.draw.polygon(surface, flag_color, flag_points)
        pygame.draw.polygon(surface, BLACK, flag_points, 1)

        # 旗杆底部基座
        pygame.draw.rect(surface, DARK_GREEN,
                        (draw_x + 4, self.y + self.pole_height - 8, 24, 8))
