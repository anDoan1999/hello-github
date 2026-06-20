"""
马里奥风格横版闯关游戏 - 关卡系统
包含关卡地图数据和加载逻辑
"""

from settings import *
from sprites import (Player, Goomba, PiranhaPlant, Coin, Mushroom, Star,
                     QuestionBlock, BrickBlock, Flagpole)


# ================================================================
#                    关卡1：草原冒险
# ================================================================
# 每个字符串代表一行，从上到下
# 宽度 = 200 个瓷砖（6400像素），高度 = 19 行（608像素）
#
# 图例：
#   .  = 空气        G  = 地面        B  = 砖块
#   ?  = 问号(金币)   M  = 问号(蘑菇)  T  = 问号(星星)
#   U  = 已使用方块   C  = 空中金币    F  = 终点旗杆
#   p  = 水管左上     q  = 水管右上    r  = 水管左下     s  = 水管右下
#   E  = 板栗仔       S  = 食人花

LEVEL_1_MAP = [
    # 行0（最顶部）- 基本全空
    '........................................................................................................................................................................................................',
    # 行1
    '........................................................................................................................................................................................................',
    # 行2
    '........................................................................................................................................................................................................',
    # 行3
    '........................................................................................................................................................................................................',
    # 行4
    '........................................................................................................................................................................................................',
    # 行5
    '........................................................................................................................................................................................................',
    # 行6 - 高空金币奖励
    '.................................................................................................................C.C.C....................................................................................',
    # 行7
    '..............................................................................................................C.C.C.C.C...................................................................................',
    # 行8 - 问号方块和砖块区域1
    '........................................................................................................................................................................................................',
    # 行9 - 第一组方块
    '.........................?............................................................?...........B?B..............................?.....................................?.................................',
    # 行10
    '........................................................................................................................................................................................................',
    # 行11 - 管道区域
    '..............................................................................................................................................................................F...............................',
    # 行12 - 管道顶部
    '......................pq..........pq...............pq.............................................pq........pq..............pq......................................pq..............pq...............',
    # 行13 - 管道主体
    '......................rs..........rs...............rs.............................................rs........rs..............rs......................................rs..............rs...............',
    # 行14 - 管道主体
    '......................rs..........rs...............rs.............................................rs........rs..............rs......................................rs..............rs...............',
    # 行15 - 管道底部到地面
    '........................................................................................................................................................................................................',
    # 行16 - 地面上方（跳跃平台）
    '................................................................................B.B.B.B.B.......................................................................................................B.B.B.....',
    # 行17 - 地面
    'GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG......GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG......GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG',
    # 行18 - 地下层（不可见，纯地面深度）
    'GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG......GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG......GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG',
]

# 敌人出生点列表 (类型, 列, 行)
LEVEL_1_ENEMIES = [
    ('goomba', 22, 16),    # 第一个板栗仔
    ('goomba', 40, 16),    # 管道附近
    ('goomba', 55, 16),    # 中间区域
    ('goomba', 60, 16),    # 中间区域
    ('goomba', 75, 16),    # 管道区域
    ('goomba', 90, 16),    # 后半段
    ('goomba', 95, 16),    # 后半段
    ('goomba', 110, 16),   # 后半段
    ('goomba', 125, 16),   # 跳跃平台前
    ('goomba', 135, 16),   # 陷阱区域
    ('goomba', 155, 16),   # 后段
    ('goomba', 165, 16),   # 终点前
    ('piranha', 22, 12),   # 第一个管道的食人花
    ('piranha', 86, 12),   # 中间管道
    ('piranha', 122, 12),  # 后段管道
]


def load_level(level_num=1):
    """
    加载关卡数据
    返回: player, tiles, enemies, items, blocks, flagpole, level_width, level_height
    """
    if level_num == 1:
        map_data = LEVEL_1_MAP
        enemy_data = LEVEL_1_ENEMIES
    else:
        map_data = LEVEL_1_MAP
        enemy_data = LEVEL_1_ENEMIES

    level_height = len(map_data)
    level_width = max(len(row) for row in map_data)

    # 收集所有需要创建的对象
    solid_tiles = []       # 不可穿越的瓷砖 [(rect, type), ...]
    question_blocks = []   # 问号方块
    brick_blocks = []      # 砖块
    coins = []             # 静态金币
    enemies = []           # 敌人
    flagpole = None
    player = None

    # 解析地图
    for row_idx, row in enumerate(map_data):
        for col_idx, char in enumerate(row):
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE

            if char == TILE_GROUND:
                solid_tiles.append((pygame.Rect(x, y, TILE_SIZE, TILE_SIZE), 'ground'))

            elif char == TILE_BRICK:
                block = BrickBlock(x, y)
                brick_blocks.append(block)
                solid_tiles.append((block.rect, 'brick'))

            elif char == TILE_QUESTION:
                block = QuestionBlock(x, y, contains='coin')
                question_blocks.append(block)
                solid_tiles.append((block.rect, 'question'))

            elif char == TILE_MUSHROOM:
                block = QuestionBlock(x, y, contains='mushroom')
                question_blocks.append(block)
                solid_tiles.append((block.rect, 'question'))

            elif char == TILE_STAR:
                block = QuestionBlock(x, y, contains='star')
                question_blocks.append(block)
                solid_tiles.append((block.rect, 'question'))

            elif char == TILE_PIPE_TL:
                solid_tiles.append((pygame.Rect(x, y, TILE_SIZE, TILE_SIZE), 'pipe'))
            elif char == TILE_PIPE_TR:
                solid_tiles.append((pygame.Rect(x, y, TILE_SIZE, TILE_SIZE), 'pipe'))
            elif char == TILE_PIPE_BL:
                solid_tiles.append((pygame.Rect(x, y, TILE_SIZE, TILE_SIZE), 'pipe'))
            elif char == TILE_PIPE_BR:
                solid_tiles.append((pygame.Rect(x, y, TILE_SIZE, TILE_SIZE), 'pipe'))

            elif char == TILE_COIN:
                coins.append(Coin(x, y))

            elif char == TILE_FLAGPOLE:
                flagpole = Flagpole(x, y)

    # 创建玩家（在地图左下角开始）
    player = Player(3 * TILE_SIZE, 16 * TILE_SIZE)

    # 创建敌人
    for enemy_type, col, row in enemy_data:
        x = col * TILE_SIZE
        y = row * TILE_SIZE
        if enemy_type == 'goomba':
            enemies.append(Goomba(x, y))
        elif enemy_type == 'piranha':
            # 食人花需要知道水管顶部位置
            pipe_top_y = 12 * TILE_SIZE  # 水管顶部行
            enemies.append(PiranhaPlant(x + 2, y, pipe_top_y))

    # 如果没有旗帜，放在默认位置
    if flagpole is None:
        flagpole = Flagpole(190 * TILE_SIZE, 7 * TILE_SIZE)

    return {
        'player': player,
        'solid_tiles': solid_tiles,
        'question_blocks': question_blocks,
        'brick_blocks': brick_blocks,
        'coins': coins,
        'enemies': enemies,
        'flagpole': flagpole,
        'level_width': level_width * TILE_SIZE,
        'level_height': level_height * TILE_SIZE,
    }


# 导入 pygame（在文件顶部已经通过 settings 间接导入，但 Rect 需要显式导入）
import pygame
