import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Robot Simulation")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
VIEW_COLOR = (200, 200, 200, 100)

ROBOT_SIZE = 20
SPEED = 2
TURN_SPEED = 0.1
VIEW_DISTANCE = 150
VIEW_ANGLE = 76

class Robot:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = SPEED
    
    def move(self):
        if self.speed > 0:
            self.x += self.speed * math.cos(self.angle)
            self.y += self.speed * math.sin(self.angle)
        
            if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
                self.angle += math.pi
            
            self.x = max(0, min(WIDTH, self.x))
            self.y = max(0, min(HEIGHT, self.y))
    
    def rotate_towards(self, target_x, target_y):
        target_angle = math.atan2(target_y - self.y, target_x - self.x)
        angle_diff = (target_angle - self.angle) % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        
        if angle_diff > 0:
            self.angle += min(angle_diff, TURN_SPEED)
        else:
            self.angle += max(angle_diff, -TURN_SPEED)

    def rotate_randomly(self):
        self.angle += random.uniform(-TURN_SPEED, TURN_SPEED)

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), ROBOT_SIZE // 2)
        self.draw_visibility_arc()

    def draw_visibility_arc(self):
        end_angle1 = self.angle - VIEW_ANGLE / 2
        end_angle2 = self.angle + VIEW_ANGLE / 2
        points = [(self.x, self.y)]
        for angle in [end_angle1, end_angle2]:
            dx = self.x + VIEW_DISTANCE * math.cos(angle)
            dy = self.y + VIEW_DISTANCE * math.sin(angle)
            points.append((dx, dy))
        pygame.draw.polygon(screen, VIEW_COLOR, points, 0)
        
    def is_on_target(self, target_x, target_y, target_size):
        return abs(self.x - (target_x + target_size // 2)) < target_size // 2 and abs(self.y - (target_y + target_size // 2)) < target_size // 2

    def can_see_target(self, target_x, target_y, target_size):
        distance = math.sqrt((self.x - (target_x + target_size / 2)) ** 2 + (self.y - (target_y + target_size / 2)) ** 2)
        if distance <= VIEW_DISTANCE:
            target_angle = math.atan2(target_y + target_size / 2 - self.y, target_x + target_size / 2 - self.x)
            angle_diff = (target_angle - self.angle) % (2 * math.pi)
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            return -VIEW_ANGLE / 2 <= angle_diff <= VIEW_ANGLE / 2
        return False

robots = [
    Robot(random.randint(0, WIDTH), random.randint(0, HEIGHT), RED),
    Robot(random.randint(0, WIDTH), random.randint(0, HEIGHT), BLUE)
]

TARGET_SIZE = 60 
target_x, target_y = WIDTH - TARGET_SIZE, 0

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)

    pygame.draw.rect(screen, GREEN, (target_x, target_y, TARGET_SIZE, TARGET_SIZE))
    
    all_robots_on_target = True
    for robot in robots:
        if not robot.is_on_target(target_x, target_y, TARGET_SIZE):
            if robot.can_see_target(target_x, target_y, TARGET_SIZE):
                robot.rotate_towards(target_x + TARGET_SIZE // 2, target_y + TARGET_SIZE // 2)
            else:
                robot.rotate_randomly()
            robot.move()
            all_robots_on_target = False
        else:
            robot.speed = 0
        robot.draw()

    if all_robots_on_target:
        print("All robots have found the target!")
        running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
