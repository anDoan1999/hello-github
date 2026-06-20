"""
马里奥风格横版闯关游戏 - 主程序
包含：游戏主循环、碰撞检测、游戏状态管理、摄像机、HUD
"""

import pygame
import sys
from settings import *
from sprites import (Player, Goomba, PiranhaPlant, Coin, Mushroom, Star,
                     QuestionBlock, BrickBlock, Flagpole, ScorePopup)
from levels import load_level


# ================================================================
#                         摄像机系统
# ================================================================
class Camera:
    """
    摄像机 - 跟随玩家水平滚动
    平滑跟随，不超出地图边界
    """

    def __init__(self, level_width):
        self.x = 0.0
        self.level_width = level_width

    def update(self, target_rect):
        """让摄像机跟随目标"""
        # 让玩家保持在屏幕左侧 1/3 处
        target_x = target_rect.centerx - SCREEN_WIDTH // 3
        self.x += (target_x - self.x) * 0.1  # 平滑跟随

        # 边界限制
        if self.x < 0:
            self.x = 0
        max_x = self.level_width - SCREEN_WIDTH
        if max_x < 0:
            max_x = 0
        if self.x > max_x:
            self.x = max_x


# ================================================================
#                        HUD 界面绘制
# ================================================================
class HUD:
    """游戏界面信息显示"""

    def __init__(self):
        self.font_large = pygame.font.SysFont('Arial', 24, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 18)

    def draw(self, surface, player, time_left):
        """绘制HUD"""
        # 背景半透明条
        hud_bg = pygame.Surface((SCREEN_WIDTH, 40), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 100))
        surface.blit(hud_bg, (0, 0))

        # 金币图标 + 数量
        pygame.draw.circle(surface, COIN_YELLOW, (20, 20), 8)
        pygame.draw.circle(surface, COIN_LIGHT, (20, 20), 5)
        coin_text = self.font_large.render(f'x {player.coins:02d}', True, WHITE)
        surface.blit(coin_text, (32, 8))

        # 生命数
        life_text = self.font_large.render(f'♥ {player.lives}', True, RED)
        surface.blit(life_text, (150, 8))

        # 分数
        score_text = self.font_large.render(f'SCORE: {player.score:06d}', True, WHITE)
        surface.blit(score_text, (280, 8))

        # 时间
        time_color = RED if time_left < 60 else WHITE
        time_text = self.font_large.render(f'TIME: {int(time_left):03d}', True, time_color)
        surface.blit(time_text, (SCREEN_WIDTH - 160, 8))


# ================================================================
#                       游戏主类
# ================================================================
class Game:
    """
    游戏主控制器
    状态机：menu -> playing -> level_complete / game_over -> menu
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # 字体
        self.font_title = pygame.font.SysFont('Arial', 48, bold=True)
        self.font_large = pygame.font.SysFont('Arial', 32, bold=True)
        self.font_medium = pygame.font.SysFont('Arial', 24)
        self.font_small = pygame.font.SysFont('Arial', 18)

        # HUD
        self.hud = HUD()

        # 游戏状态
        self.state = 'menu'
        self.current_level = 1
        self.time_left = LEVEL_TIME
        self.time_counter = 0

        # 关卡数据（在 start_level 中初始化）
        self.player = None
        self.solid_tiles = []
        self.question_blocks = []
        self.brick_blocks = []
        self.coins = []
        self.enemies = []
        self.items = []           # 蘑菇、星星等活动道具
        self.flagpole = None
        self.camera = None
        self.popups = []          # 分数弹出特效

        # 过关动画
        self.level_complete_timer = 0
        self.game_over_timer = 0

    def start_level(self, level_num=1):
        """加载并开始关卡"""
        level_data = load_level(level_num)

        self.player = level_data['player']
        self.solid_tiles = level_data['solid_tiles']
        self.question_blocks = level_data['question_blocks']
        self.brick_blocks = level_data['brick_blocks']
        self.coins = level_data['coins']
        self.enemies = level_data['enemies']
        self.items = []
        self.flagpole = level_data['flagpole']
        self.popups = []

        self.camera = Camera(level_data['level_width'])
        self.camera.x = 0

        self.time_left = LEVEL_TIME
        self.time_counter = 0
        self.state = 'playing'
        self.level_complete_timer = 0

    # ============================================================
    #                    游戏逻辑更新
    # ============================================================
    def update_playing(self):
        """游戏进行中的更新逻辑"""
        player = self.player

        # ---- 时间 ----
        self.time_counter += 1
        if self.time_counter >= FPS:
            self.time_counter = 0
            self.time_left -= 1
            if self.time_left <= 0:
                player.die()

        # ---- 玩家更新 ----
        head_hit_result = player.update(self.solid_tiles, self.enemies, self.items)

        # 处理头部撞击方块
        if head_hit_result and head_hit_result[0] == 'head_hit':
            _, hit_rect, hit_type = head_hit_result
            self._handle_block_hit(hit_rect, hit_type)

        # ---- 敌人更新 ----
        for enemy in self.enemies[:]:
            if isinstance(enemy, Goomba):
                enemy.update(self.solid_tiles)
            elif isinstance(enemy, PiranhaPlant):
                enemy.update(player)

        # ---- 道具更新 ----
        for item in self.items[:]:
            if isinstance(item, (Mushroom, Star)):
                item.update(self.solid_tiles)
            if not item.alive:
                self.items.remove(item)

        # ---- 金币更新 ----
        for coin in self.coins[:]:
            coin.update()
            if not coin.alive:
                self.coins.remove(coin)

        # ---- 问号方块/砖块更新 ----
        for block in self.question_blocks:
            block.update()
        for block in self.brick_blocks[:]:
            block.update()
            if not block.alive and not block.fragments:
                self.brick_blocks.remove(block)

        # ---- 旗帜更新 ----
        if self.flagpole:
            self.flagpole.update()

        # ---- 分数弹出更新 ----
        for popup in self.popups[:]:
            popup.update()
            if not popup.alive:
                self.popups.remove(popup)

        # ---- 碰撞检测 ----
        self._check_enemy_collisions()
        self._check_item_collisions()
        self._check_coin_collisions()
        self._check_flagpole_collision()

        # ---- 摄像机 ----
        self.camera.update(player.rect)

        # ---- 玩家死亡处理 ----
        if not player.alive:
            if player.death_timer > 90:  # 1.5秒后重生
                if player.lives > 0:
                    player.respawn()
                    self.time_left = LEVEL_TIME
                else:
                    self.state = 'game_over'
                    self.game_over_timer = 0

        # ---- 过关完成 ----
        if self.flagpole and self.flagpole.is_complete():
            self.level_complete_timer += 1
            if self.level_complete_timer > 120:  # 2秒后
                self.state = 'level_complete'

    def _handle_block_hit(self, hit_rect, hit_type):
        """处理玩家头部撞击方块"""
        # 找到被撞击的方块
        for block in self.question_blocks:
            if block.rect == hit_rect:
                result = block.hit()
                if result:
                    item_type, ix, iy = result
                    if item_type == 'coin':
                        # 弹出金币
                        popup_coin = Coin(ix, iy, popup=True)
                        self.coins.append(popup_coin)
                        self.player.collect_coin()
                        self.popups.append(ScorePopup(ix, iy, '200'))
                    elif item_type == 'mushroom':
                        self.items.append(Mushroom(ix, iy))
                    elif item_type == 'star':
                        self.items.append(Star(ix, iy))
                return

        for block in self.brick_blocks:
            if block.rect == hit_rect:
                result = block.hit(self.player.big)
                if result == 'break':
                    self.player.add_score(50)
                    # 从碰撞列表中移除
                    self.solid_tiles = [(r, t) for r, t in self.solid_tiles
                                        if r != hit_rect]
                return

    def _check_enemy_collisions(self):
        """检测玩家与敌人的碰撞"""
        player = self.player
        if not player.alive or player.at_flag:
            return

        for enemy in self.enemies[:]:
            if isinstance(enemy, Goomba):
                if not enemy.alive:
                    continue
                if not player.rect.colliderect(enemy.rect):
                    continue

                # 判断是否踩踏（玩家从上方落下）
                if (player.vel_y > 0 and
                        player.rect.bottom - enemy.rect.top < 16):
                    # 踩踏！
                    enemy.stomp()
                    player.vel_y = -8  # 弹起
                    player.add_score(100)
                    self.popups.append(ScorePopup(
                        enemy.rect.x, enemy.rect.y - 20, '100'))
                else:
                    # 被敌击中
                    player.die()

            elif isinstance(enemy, PiranhaPlant):
                if not enemy.is_visible():
                    continue
                if player.rect.colliderect(enemy.rect):
                    player.die()

    def _check_item_collisions(self):
        """检测玩家与道具的碰撞"""
        player = self.player
        if not player.alive:
            return

        for item in self.items[:]:
            if not item.alive or item.spawning:
                continue
            if not player.rect.colliderect(item.rect):
                continue

            if isinstance(item, Mushroom):
                if not player.big:
                    player.set_big(True)
                    player.grow_timer = GROW_ANIMATION_TIME
                player.add_score(1000)
                self.popups.append(ScorePopup(
                    item.rect.x, item.rect.y - 20, '1000'))
                item.alive = False

            elif isinstance(item, Star):
                player.star_timer = STAR_DURATION
                player.add_score(1000)
                self.popups.append(ScorePopup(
                    item.rect.x, item.rect.y - 20, 'STAR!'))
                item.alive = False

    def _check_coin_collisions(self):
        """检测玩家与金币的碰撞"""
        player = self.player
        if not player.alive:
            return

        for coin in self.coins[:]:
            if not coin.alive:
                continue
            if player.rect.colliderect(coin.rect):
                player.collect_coin()
                coin.alive = False
                self.popups.append(ScorePopup(
                    coin.rect.x, coin.rect.y - 10, '200'))

    def _check_flagpole_collision(self):
        """检测玩家到达终点"""
        if not self.flagpole or self.player.at_flag:
            return
        if not self.player.alive:
            return

        if self.player.rect.colliderect(self.flagpole.pole_rect):
            self.player.at_flag = True
            self.player.vel_x = 0
            self.player.vel_y = 0
            self.flagpole.trigger()
            # 根据剩余时间加分
            time_bonus = int(self.time_left) * 50
            self.player.add_score(time_bonus)

    # ============================================================
    #                      绘制方法
    # ============================================================
    def draw_menu(self):
        """绘制主菜单"""
        self.screen.fill(SKY_BLUE)

        # 标题
        title = self.font_title.render('SUPER MARIO', True, MARIO_RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)

        # 副标题
        sub = self.font_large.render('MVP Edition', True, WHITE)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 240))
        self.screen.blit(sub, sub_rect)

        # 绘制小马里奥预览
        mx = SCREEN_WIDTH // 2 - 12
        my = 300
        pygame.draw.rect(self.screen, MARIO_RED, (mx - 1, my, 26, 8))
        pygame.draw.rect(self.screen, MARIO_SKIN, (mx, my + 8, 24, 8))
        pygame.draw.rect(self.screen, MARIO_RED, (mx, my + 16, 24, 8))
        pygame.draw.rect(self.screen, (0, 0, 180), (mx + 2, my + 24, 20, 4))
        pygame.draw.rect(self.screen, MARIO_BROWN, (mx - 1, my + 28, 10, 4))
        pygame.draw.rect(self.screen, MARIO_BROWN, (mx + 15, my + 28, 10, 4))

        # 开始提示（闪烁）
        if pygame.time.get_ticks() % 1000 < 700:
            start = self.font_medium.render('Press SPACE to Start', True, WHITE)
            start_rect = start.get_rect(center=(SCREEN_WIDTH // 2, 420))
            self.screen.blit(start, start_rect)

        # 操作说明
        controls = [
            '<- -> or A D : Move',
            'SPACE : Jump (hold for higher)',
        ]
        for i, text in enumerate(controls):
            ctrl = self.font_small.render(text, True, (200, 200, 200))
            ctrl_rect = ctrl.get_rect(center=(SCREEN_WIDTH // 2, 480 + i * 25))
            self.screen.blit(ctrl, ctrl_rect)

    def draw_playing(self):
        """绘制游戏画面"""
        self.screen.fill(SKY_BLUE)

        # 绘制远处的云朵装饰
        self._draw_clouds()

        cam_x = self.camera.x

        # ---- 绘制地面 ----
        for tile_rect, tile_type in self.solid_tiles:
            draw_x = tile_rect.x - cam_x
            draw_y = tile_rect.y
            # 跳过屏幕外的瓷砖
            if draw_x + TILE_SIZE < 0 or draw_x > SCREEN_WIDTH:
                continue

            if tile_type == 'ground':
                pygame.draw.rect(self.screen, GROUND_BROWN,
                               (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
                # 顶部草地
                pygame.draw.rect(self.screen, (80, 180, 60),
                               (draw_x, draw_y, TILE_SIZE, 4))
                pygame.draw.rect(self.screen, GROUND_DARK,
                               (draw_x, draw_y, TILE_SIZE, TILE_SIZE), 1)

            elif tile_type == 'pipe':
                pygame.draw.rect(self.screen, PIPE_GREEN,
                               (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
                # 水管高光
                pygame.draw.rect(self.screen, PIPE_LIGHT,
                               (draw_x + 2, draw_y, 6, TILE_SIZE))
                pygame.draw.rect(self.screen, PIPE_DARK,
                               (draw_x, draw_y, TILE_SIZE, TILE_SIZE), 1)
                # 水管顶部加厚边缘（检查上方是否为空）
                above_y = draw_y - TILE_SIZE
                has_pipe_above = False
                for tr, tt in self.solid_tiles:
                    if tt == 'pipe' and tr.x == tile_rect.x and tr.y == above_y:
                        has_pipe_above = True
                        break
                if not has_pipe_above:
                    pygame.draw.rect(self.screen, PIPE_GREEN,
                                   (draw_x - 2, draw_y, TILE_SIZE + 4, 6))
                    pygame.draw.rect(self.screen, PIPE_RIM,
                                   (draw_x - 2, draw_y, TILE_SIZE + 4, 6), 1)

        # ---- 绘制方块 ----
        for block in self.question_blocks:
            block.draw(self.screen, cam_x)
        for block in self.brick_blocks:
            block.draw(self.screen, cam_x)

        # ---- 绘制金币 ----
        for coin in self.coins:
            coin.draw(self.screen, cam_x)

        # ---- 绘制道具 ----
        for item in self.items:
            item.draw(self.screen, cam_x)

        # ---- 绘制敌人 ----
        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        # ---- 绘制终点旗帜 ----
        if self.flagpole:
            self.flagpole.draw(self.screen, cam_x)

        # ---- 绘制玩家 ----
        if self.player:
            self.player.draw(self.screen, cam_x)

        # ---- 绘制分数弹出 ----
        for popup in self.popups:
            popup.draw(self.screen, cam_x)

        # ---- HUD ----
        self.hud.draw(self.screen, self.player, self.time_left)

    def _draw_clouds(self):
        """绘制背景装饰云朵"""
        cloud_positions = [
            (100, 60), (350, 40), (600, 80), (900, 50),
            (1200, 70), (1500, 45), (1800, 65), (2200, 55),
            (2600, 40), (3000, 75), (3400, 50), (3800, 60),
            (4200, 45), (4600, 70), (5000, 55), (5400, 40),
            (5800, 65), (6200, 50),
        ]
        parallax = 0.3
        for cx, cy in cloud_positions:
            dx = cx - self.camera.x * parallax
            dx = dx % (SCREEN_WIDTH + 200) - 100
            pygame.draw.ellipse(self.screen, WHITE,
                              (int(dx), cy, 80, 30))
            pygame.draw.ellipse(self.screen, WHITE,
                              (int(dx) + 15, cy - 10, 50, 25))
            pygame.draw.ellipse(self.screen, WHITE,
                              (int(dx) + 40, cy + 5, 60, 25))

    def draw_level_complete(self):
        """绘制过关画面"""
        self.screen.fill(SKY_BLUE)
        self._draw_clouds()

        cam_x = self.camera.x
        for tile_rect, tile_type in self.solid_tiles:
            draw_x = tile_rect.x - cam_x
            if draw_x + TILE_SIZE < 0 or draw_x > SCREEN_WIDTH:
                continue
            if tile_type == 'ground':
                pygame.draw.rect(self.screen, GROUND_BROWN,
                               (draw_x, tile_rect.y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(self.screen, (80, 180, 60),
                               (draw_x, tile_rect.y, TILE_SIZE, 4))

        for block in self.question_blocks:
            block.draw(self.screen, cam_x)
        for block in self.brick_blocks:
            block.draw(self.screen, cam_x)
        if self.flagpole:
            self.flagpole.draw(self.screen, cam_x)
        if self.player:
            self.player.draw(self.screen, cam_x)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render('LEVEL CLEAR!', True, STAR_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)

        score = self.font_large.render(
            f'Score: {self.player.score:06d}', True, WHITE)
        self.screen.blit(score, score.get_rect(center=(SCREEN_WIDTH // 2, 280)))

        coins = self.font_large.render(
            f'Coins: {self.player.coins}', True, COIN_YELLOW)
        self.screen.blit(coins, coins.get_rect(center=(SCREEN_WIDTH // 2, 320)))

        time_bonus = self.font_large.render(
            f'Time Bonus: {int(self.time_left) * 50}', True, WHITE)
        self.screen.blit(time_bonus, time_bonus.get_rect(
            center=(SCREEN_WIDTH // 2, 360)))

        if pygame.time.get_ticks() % 1000 < 700:
            cont = self.font_medium.render(
                'Press SPACE to Continue', True, WHITE)
            self.screen.blit(cont, cont.get_rect(
                center=(SCREEN_WIDTH // 2, 450)))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        self.screen.fill(BLACK)

        title = self.font_title.render('GAME OVER', True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        score = self.font_large.render(
            f'Final Score: {self.player.score:06d}', True, WHITE)
        self.screen.blit(score, score.get_rect(center=(SCREEN_WIDTH // 2, 300)))

        if self.game_over_timer > 60:
            if pygame.time.get_ticks() % 1000 < 700:
                restart = self.font_medium.render(
                    'Press SPACE to Restart', True, WHITE)
                self.screen.blit(restart, restart.get_rect(
                    center=(SCREEN_WIDTH // 2, 400)))

        self.game_over_timer += 1

    # ============================================================
    #                       主循环
    # ============================================================
    def run(self):
        """游戏主循环"""
        running = True
        while running:
            # ---- 事件处理 ----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # 键盘按下事件：只处理全局退出和 UI 状态切换（单次触发逻辑）
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == 'playing':
                            self.state = 'menu'
                        else:
                            running = False

                    # 非游戏进行状态下，空格键用于界面跳转
                    if event.key == pygame.K_SPACE:
                        if self.state == 'menu':
                            self.start_level(self.current_level)

                        elif self.state == 'level_complete':
                            self.current_level += 1
                            if self.current_level > 1:
                                self.current_level = 1
                            self.start_level(self.current_level)

                        elif self.state == 'game_over':
                            if self.game_over_timer > 60:
                                self.current_level = 1
                                self.player.lives = INITIAL_LIVES
                                self.player.score = 0
                                self.player.coins = 0
                                self.start_level(self.current_level)

            # ---- 状态更新 ----
            if self.state == 'playing':
                self.update_playing()

            # ---- 绘制 ----
            if self.state == 'menu':
                self.draw_menu()
            elif self.state == 'playing':
                self.draw_playing()
            elif self.state == 'level_complete':
                self.draw_level_complete()
            elif self.state == 'game_over':
                self.draw_game_over()

            # ---- 刷新 ----
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ================================================================
#                           启动
# ================================================================
if __name__ == '__main__':
    game = Game()
    game.run()
