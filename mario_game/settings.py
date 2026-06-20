"""
马里奥风格横版闯关游戏 - 全局配置
所有游戏常量集中管理，方便调整游戏手感
"""

# ==================== 窗口设置 ====================
SCREEN_WIDTH = 800          # 窗口宽度（像素）
SCREEN_HEIGHT = 600         # 窗口高度（像素）
FPS = 60                    # 帧率
TITLE = "超级马里奥 - MVP"  # 窗口标题

# ==================== 瓷砖系统 ====================
TILE_SIZE = 32              # 每个瓷砖的像素尺寸

# ==================== 颜色定义 (R, G, B) ====================
# 背景与环境
SKY_BLUE = (107, 140, 255)       # 天空蓝
DARK_SKY = (50, 80, 180)         # 深色天空（备用）
GROUND_BROWN = (139, 90, 43)     # 地面泥土色
GROUND_DARK = (101, 67, 33)      # 深色地面

# 玩家
MARIO_RED = (255, 0, 0)          # 马里奥红色
MARIO_DARK = (200, 0, 0)         # 深红色（帽子）
MARIO_SKIN = (255, 200, 150)     # 肤色
MARIO_BROWN = (139, 69, 19)      # 棕色（头发/胡子）
MARIO_GREEN = (0, 180, 0)        # 路易吉绿（备用）

# 方块
BRICK_COLOR = (185, 122, 50)     # 砖块主色
BRICK_DARK = (139, 90, 43)       # 砖块深色纹路
BRICK_LIGHT = (210, 160, 80)     # 砖块高光
QUESTION_YELLOW = (255, 200, 0)  # 问号方块主色
QUESTION_DARK = (200, 150, 0)    # 问号方块深色
QUESTION_LIGHT = (255, 230, 100) # 问号方块高光
USED_BLOCK = (150, 120, 80)      # 已使用方块颜色

# 敌人
GOOMBA_BROWN = (160, 82, 45)     # 板栗仔棕色
GOOMBA_DARK = (100, 50, 25)      # 板栗仔深色
GOOMBA_LIGHT = (210, 150, 90)    # 板栗仔浅色
PIRANHA_GREEN = (0, 160, 0)      # 食人花绿色
PIRANHA_RED = (220, 30, 30)      # 食人花红色
PIRANHA_WHITE = (255, 255, 220)  # 食人花白色

# 道具
COIN_YELLOW = (255, 215, 0)      # 金币金色
COIN_LIGHT = (255, 240, 100)     # 金币高光
MUSHROOM_RED = (220, 30, 30)     # 蘑菇红色
MUSHROOM_TAN = (210, 180, 140)   # 蘑菇肤色
STAR_YELLOW = (255, 255, 0)      # 无敌星黄色
STAR_ORANGE = (255, 165, 0)      # 无敌星橙色

# 水管
PIPE_GREEN = (0, 180, 0)         # 水管绿色
PIPE_DARK = (0, 130, 0)          # 水管深色
PIPE_LIGHT = (80, 220, 80)       # 水管高光
PIPE_RIM = (0, 100, 0)           # 水管边缘

# UI
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 100, 0)
FLAGPOLE_GRAY = (160, 160, 160)
FLAG_GREEN = (0, 200, 0)

# ==================== 物理参数 ====================
GRAVITY = 0.6               # 重力加速度（像素/帧²）
PLAYER_ACC = 0.5            # 玩家水平加速度
PLAYER_FRICTION = -0.12     # 地面摩擦力
PLAYER_MAX_SPEED_X = 5      # 最大水平速度
PLAYER_JUMP_FORCE = -12     # 跳跃初速度（负值向上）
PLAYER_JUMP_FORCE_BIG = -13 # 大状态跳跃初速度
MAX_FALL_SPEED = 10         # 最大下落速度

# 敌人物理
ENEMY_SPEED = 1             # 敌人移动速度

# 道具物理
ITEM_RISE_SPEED = -2        # 道具从方块弹出的速度
ITEM_MOVE_SPEED = 2         # 蘑菇/星星移动速度
ITEM_BOUNCE = -8            # 道具弹跳力

# ==================== 游戏规则 ====================
INITIAL_LIVES = 3           # 初始生命数
MAX_LIVES = 99              # 最大生命数
COINS_FOR_LIFE = 100        # 多少金币换1命
LEVEL_TIME = 300            # 关卡时间限制（秒）
INVINCIBLE_TIME = 120       # 受伤无敌帧数（2秒 @ 60fps）
STAR_DURATION = 480         # 无敌星持续帧数（8秒 @ 60fps）
GROW_ANIMATION_TIME = 30    # 变大动画帧数

# ==================== 地图字符定义 ====================
# 用于 levels.py 中的关卡地图
TILE_EMPTY = '.'        # 空气
TILE_GROUND = 'G'       # 地面（不可破坏）
TILE_BRICK = 'B'        # 砖块（大状态可击碎）
TILE_QUESTION = '?'     # 问号方块（含金币）
TILE_MUSHROOM = 'M'     # 问号方块（含蘑菇）
TILE_STAR = 'T'         # 问号方块（含无敌星）
TILE_USED = 'U'         # 已使用的方块
TILE_PIPE_TL = 'p'      # 水管左上角
TILE_PIPE_TR = 'q'      # 水管右上角
TILE_PIPE_BL = 'r'      # 水管左下角
TILE_PIPE_BR = 's'      # 水管右下角
TILE_COIN = 'C'         # 金币（空中）
TILE_FLAGPOLE = 'F'     # 终点旗杆

# 实体标记（不占瓷砖，仅标记出生点）
ENTITY_GOOMBA = 'E'     # 板栗仔
ENTITY_PIRANHA = 'S'    # 食人花

# ==================== 碰撞边距 ====================
# 微调碰撞框，让手感更好
COLLISION_TOLERANCE = 2  # 碰撞容差像素

# ==================== 动画速度 ====================
PLAYER_ANIM_SPEED = 6    # 玩家动画切换间隔（帧）
COIN_ANIM_SPEED = 8      # 金币旋转速度
STAR_BLINK_SPEED = 4     # 无敌星闪烁速度
