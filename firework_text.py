import colorsys
import time
import pygame
from random import randint, uniform, choice
import math
from PIL import Image, ImageDraw, ImageFont

vector2 = pygame.math.Vector2
trails = []
fade_p = []

# general
# 上升阶段所受的重力加速度
GRAVITY_FIREWORK = vector2(0, 0.3)
# 爆炸后粒子所受的重力加速度
GRAVITY_PARTICLE = vector2(0, 0.07)
# 显示窗口的宽度和高度
DISPLAY_WIDTH = 1500
DISPLAY_HEIGHT = 1000
# 窗口的背景颜色
BACKGROUND_COLOR = (20, 20, 30) 

# firework
# 烟花上升的速度
FIREWORK_SPEED_MIN = 17
FIREWORK_SPEED_MAX = 19
# 烟花的大小
FIREWORK_SIZE =4

# particle
# 粒子的生命周期，以帧数为单位
PARTICLE_LIFESPAN = 120
# 粒子在x轴方向上的扩散系数
X_SPREAD = 0.92
Y_SPREAD = 0.92
# 粒子的大小
PARTICLE_SIZE = 2
# 烟花爆炸时产生的粒子数量
MIN_PARTICLES = 250
MAX_PARTICLES = 300
# 摆动缩放因子
X_WIGGLE_SCALE = 20  
Y_WIGGLE_SCALE = 10
# 爆炸半径
EXPLOSION_RADIUS_MIN = 40
EXPLOSION_RADIUS_MAX = 45
# 是否启用彩色效果
COLORFUL = True

# trail
# 粒子轨迹的生命周期
TRAIL_LIFESPAN = PARTICLE_LIFESPAN / 3
# 粒子轨迹的生成频率
TRAIL_FREQUENCY = 10  
# 是否启用粒子轨迹效果
TRAILS = True

# 字体路径和字符
FONT_PATH = "msyhl.ttc"
CHARACTER = " Happy New Year!"
places=[i for i in range(100,1400,250)]
place=0

def get_char_contour_points(font_path, char, size):
    """
    获取字符的轮廓点
    :param font_path: TTF 字体文件路径
    :param char: 要渲染的字符
    :param size: 字符的大小
    :return: 字符的轮廓点列表
    """
    font = ImageFont.truetype(font_path, size)
    image = Image.new("L", (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), char, font=font, fill=255)
    points = []
    for y in range(image.height):
        for x in range(image.width):
            if image.getpixel((x, y)) > 128:
                points.append((x, y))
    return [(x-0.25*size, y-0.85*size) for x, y in points]

def generate_vivid_color():
    """生成高饱和度、高明度的颜色（HSV转RGB）"""
    hue = uniform(0, 0.6)          # 随机色相（0~1）
    saturation = 0.8 + uniform(0, 0.1)  # 饱和度 90%~100%
    value = 0.8 + uniform(0, 0.2)       # 明度 80%~100%
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return (int(r * 255), int(g * 255), int(b * 255))

class Firework:
    def __init__(self, character: str):
        # 烟花的颜色、爆炸后的粒子颜色
        self.colour = generate_vivid_color()
        self.colours = (generate_vivid_color(), generate_vivid_color())
        # 一个烟花粒子对象
        if place==0:
            self.firework = Particle(randint(0, DISPLAY_WIDTH), DISPLAY_HEIGHT, 0, 0, 0, True, self.colour)
        else:
            self.firework = Particle(places[place], DISPLAY_HEIGHT, 0, 0, 0, True, self.colour)
        self.exploded = False
        self.particles = []
        if character == "":
            self.points = []
            self.char=False
        else:
            self.char=True
            self.points = get_char_contour_points(FONT_PATH, character, 45)

    def update(self, win: pygame.Surface) -> None:
        """
        每帧调用的方法，用于更新烟花的状态和显示。
        """
        if not self.exploded:
            # 对烟花施加重力
            self.firework.apply_force(GRAVITY_FIREWORK)
            self.firework.move()
            self.show(win)
            # 如果烟花的垂直速度大于等于0，表示烟花已经到达最高点，开始爆炸
            if self.firework.vel.y >= 0:
                self.exploded = True
                self.explode()
        else:
            for particle in self.particles:
                particle.update()
                particle.show(win)

    def explode(self):
        """
        当烟花达到最高点时，生成爆炸粒子。
        该方法在烟花达到最高点时被调用，用于生成爆炸粒子。粒子的数量是随机的，介于MIN_PARTICLES和MAX_PARTICLES之间。
        如果启用了彩色效果（COLORFUL为True），则粒子的颜色是从self.colours中随机选择的；否则，粒子的颜色与烟花的颜色相同。
        """
        if self.char:
            for dx,dy in self.points:
                colour = choice(self.colours) if COLORFUL else self.colour
                r=math.sqrt(dx**2+dy**2)
                particle = Particle(self.firework.pos.x, self.firework.pos.y, dx, dy, r, False, colour)
                self.particles.append(particle)
        else:
            for i in range(randint(MIN_PARTICLES, MAX_PARTICLES)):
                colour = choice(self.colours) if COLORFUL else self.colour
                particle = Particle(self.firework.pos.x, self.firework.pos.y, 0, 0, 0, False, colour)
                self.particles.append(particle)

    def show(self, win: pygame.Surface) -> None:
        """
        绘制烟花。
        """
        x = int(self.firework.pos.x)
        y = int(self.firework.pos.y)
        pygame.draw.circle(win, self.colour, (x, y), self.firework.size)

    def remove(self) -> bool:
        """
        检查烟花是否应该被移除。
        如果烟花还没有爆炸，则返回False。如果烟花已经爆炸，并且所有的粒子都已经被移除，则返回True。
        """
        if not self.exploded:
            return False
        for p in self.particles:
            if p.remove:
                self.particles.remove(p)
        return len(self.particles) == 0

class Particle(object):
    def __init__(self, x, y, dx, dy, r, firework, colour):
        self.firework = firework
        # 粒子的位置
        self.pos = vector2(x, y)
        # 粒子的初始位置
        self.origin = vector2(x, y)
        # 粒子的加速度
        self.acc = vector2(0, 0)
        # 粒子是否需要被移除
        self.remove = False
        # 粒子的爆炸半径
        if r==0:
            self.explosion_radius =  randint(EXPLOSION_RADIUS_MIN, EXPLOSION_RADIUS_MAX)
        else:
            self.explosion_radius = r 
        # 粒子的生命周期
        self.life = 0
        # 粒子的颜色
        self.colour = colour
        # 粒子轨迹的生成频率
        self.trail_frequency = TRAIL_FREQUENCY + randint(-3, 3)

        if self.firework:
            self.vel = vector2(0, -randint(FIREWORK_SPEED_MIN, FIREWORK_SPEED_MAX))
            self.size = FIREWORK_SIZE
        else:
            if dx==0 and dy==0:
                self.vel = vector2(uniform(-0.5, 0.5), uniform(-0.5, 0.5))
                self.vel.x *= randint(7, self.explosion_radius + 2)
                self.vel.y *= randint(7, self.explosion_radius + 2)
            else:
                self.vel = vector2(0.7*dx, 0.7*dy)
            self.size = randint(PARTICLE_SIZE - 1, PARTICLE_SIZE + 1)
            # 更新粒子的位置并移除粒子，如果粒子在半径之外
            self.move()
            self.outside_spawn_radius()

    def update(self) -> None:
        """
        更新粒子的状态。
        该方法在每一帧被调用，用于更新粒子的生命周期、生成粒子轨迹、施加力并移动粒子。
        """
        self.life += 1
        # 如果粒子的生命周期是轨迹生成频率的倍数，则生成一个新的轨迹
        if self.life % self.trail_frequency == 0:
            trails.append(Trail(self.pos.x, self.pos.y, False, self.colour, self.size))
        # 对粒子施加一个随机的力，使其产生摆动效果
        self.apply_force(vector2(uniform(-1, 1) / X_WIGGLE_SCALE, GRAVITY_PARTICLE.y + uniform(-1, 1) / Y_WIGGLE_SCALE))
        # 移动粒子
        self.move()

    def apply_force(self, force: pygame.math.Vector2) -> None:
        # 改变粒子的加速度
        self.acc += force

    def outside_spawn_radius(self) -> bool:
        """
        检查粒子是否在生成半径之外。
        """
        distance = math.sqrt((self.pos.x - self.origin.x) ** 2 + (self.pos.y - self.origin.y) ** 2)
        return distance > self.explosion_radius
    def move(self) -> None:
        # 如果粒子不是烟花，则在x和y方向上应用扩散系数
        if not self.firework:
            self.vel.x *= X_SPREAD
            self.vel.y *= Y_SPREAD
        # 更新粒子的速度和位置，并重置加速度
        self.vel += self.acc
        self.pos += self.vel
        self.acc *= 0
        self.decay()

    def show(self, win: pygame.Surface) -> None:
        x = int(self.pos.x)
        y = int(self.pos.y)
        pygame.draw.circle(win, self.colour, (x, y), self.size)

    def decay(self) -> None:
        if self.life > PARTICLE_LIFESPAN:
            if randint(0, 15) == 0:
                self.remove = True
        if not self.remove and self.life > PARTICLE_LIFESPAN * 1.5:
            self.remove = True


class Trail(Particle):
    def __init__(self, x, y, is_firework, colour, parent_size):
        """
        初始化粒子对象。
        x (int): 粒子的初始x坐标。
        y (int): 粒子的初始y坐标。
        is_firework (bool): 粒子是否为烟花。
        colour (tuple): 粒子的颜色。
        parent_size (int): 父粒子的大小。
        """
        Particle.__init__(self, x, y, 0, 0, 0, is_firework, colour)
        self.size = parent_size - 1

    def decay(self) -> bool:
        """
        更新粒子轨迹的状态。
        该方法在每一帧被调用，用于更新粒子轨迹的生命周期、大小和颜色。如果粒子轨迹的生命周期超过了TRAIL_LIFESPAN，则有一定的概率将其标记为移除。
        如果粒子轨迹的生命周期超过了TRAIL_LIFESPAN的1.5倍，则将其标记为移除。
        """
        # 增加粒子轨迹的生命周期
        self.life += 1
        if self.life % 100 == 0:
            self.size -= 1

        self.size = max(0, self.size)
        self.colour = (min(self.colour[0] + 5, 255), min(self.colour[1] + 5, 255), min(self.colour[2] + 5, 255))

        if self.life > TRAIL_LIFESPAN:
            ran = randint(0, 15)
            if ran == 0:
                return True
        if not self.remove and self.life > TRAIL_LIFESPAN * 1.2:
            return True
        
        return False


def update(win: pygame.Surface, fireworks: list, trails: list) -> None:
    """
    更新烟花和粒子轨迹的状态，并在窗口上显示它们。
    """
    if TRAILS:
        for t in trails:
            t.show(win)
            if t.decay():
                trails.remove(t)
    for fw in fireworks:
        fw.update(win)
        if fw.remove():
            fireworks.remove(fw)
    pygame.display.update()


def go():
    pygame.init()
    pygame.display.set_caption("HAPPY")
    win = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    clock = pygame.time.Clock()
    clock.tick(60)
    global place
    fireworks = []
    index = 0
    running = True
    is_paused = False  
    pause_start_time = 0 

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        clock.tick(6000000)
        win.fill(BACKGROUND_COLOR)
        # 仅在非暂停状态下生成烟花
        if not is_paused:
            if index < len(CHARACTER):
                current_char = CHARACTER[index]
                if current_char == " ":
                    # 触发1秒暂停
                    is_paused = True
                    pause_start_time = pygame.time.get_ticks()
                    place = 0
                else:
                    place += 1
                fireworks.append(Firework(current_char))
                index += 1
            else:   
                if randint(0, 70) == 1: 
                    place = 0
                    fireworks.append(Firework(""))
        else:
            # 检查是否已暂停1秒
            current_time = pygame.time.get_ticks()
            if current_time - pause_start_time >= 3000:
                is_paused = False  # 恢复生成
        update(win, fireworks, trails)

    pygame.quit()
    quit()

if __name__ == "__main__":
    go()