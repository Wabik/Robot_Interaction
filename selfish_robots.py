import pygame
import random
import math
import time
import pandas as pd

FILE_PATH = "j:\\Desktop\\Robot_Interaction\\selfish_time.csv"

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Robot Simulation")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)
VIEW_COLOR = (200, 200, 200, 100)
PURPLE = (128, 0, 128)

ROBOT_SIZE = 20
SPEED = 2
TURN_SPEED = 0.1
VIEW_DISTANCE = 150
VIEW_ANGLE = math.radians(76)

TARGET_SIZE = 100
target_x, target_y = WIDTH - TARGET_SIZE, 0

safe_areas = [
    pygame.Rect(target_x, 0, WIDTH - target_x, 5),
    pygame.Rect(795, 0, 5, 100)
]

class Robot:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = SPEED
        self.active = True

    def move(self):
        if self.active:
            self.x += self.speed * math.cos(self.angle)
            self.y += self.speed * math.sin(self.angle)

            if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
                self.angle = (self.angle + math.pi) % (2 * math.pi)

            self.x = max(0, min(WIDTH, self.x))
            self.y = max(0, min(HEIGHT, self.y))

    def rotate_towards(self, target_x, target_y):
        target_angle = math.atan2(target_y - self.y, target_x - self.x)
        angle_diff = (target_angle - self.angle) % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        
        if abs(angle_diff) < TURN_SPEED:
            self.angle = target_angle
        else:
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
        
    def is_in_safe_area(self):
        robot_rect = pygame.Rect(self.x - ROBOT_SIZE // 2, self.y - ROBOT_SIZE // 2, ROBOT_SIZE, ROBOT_SIZE)
        return any(robot_rect.colliderect(area) for area in safe_areas)
    
    def can_see_target(self, target_x, target_y, target_size):
        distance = math.hypot(self.x - (target_x + target_size / 2), self.y - (target_y + target_size / 2))
        if distance <= VIEW_DISTANCE:
            target_angle = math.atan2(target_y + target_size / 2 - self.y, target_x + target_size / 2 - self.x)
            angle_diff = (target_angle - self.angle) % (2 * math.pi)
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            return -VIEW_ANGLE / 2 <= angle_diff <= VIEW_ANGLE / 2
        return False
    
    def check_collision(self, other):
        distance = math.hypot(self.x - other.x, self.y - other.y)
        return distance < ROBOT_SIZE

    def avoid_collision(self, other):
        print("Collision!")
        self.angle = (self.angle + math.pi / 2) % (2 * math.pi)

def save_time_to_file(time_taken, file_path):
    try:
        df = pd.DataFrame({"selfish time": [time_taken]})
        df.to_csv(file_path, mode='a', header=False, index=False)
    except Exception as e:
        print(f"Error saving to file: {e}")

robots = [
    Robot(100, 100, RED),
    Robot(300, 300, BLUE),
    Robot(600, 600, YELLOW)
]

running = True
clock = pygame.time.Clock()

start_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)

    pygame.draw.rect(screen, GREEN, (target_x, target_y, TARGET_SIZE, TARGET_SIZE))
    
    for area in safe_areas:
        pygame.draw.rect(screen, PURPLE, area)

    all_robots_in_safe_area = True
    for robot in robots:
        if not robot.is_in_safe_area():
            if robot.can_see_target(target_x, target_y, TARGET_SIZE):
                robot.rotate_towards(target_x + TARGET_SIZE // 2, target_y + TARGET_SIZE // 2)
            else:
                robot.rotate_randomly()
            robot.move()
            all_robots_in_safe_area = False
        else:
            robot.speed = 0
            robot.active = False
        robot.draw()

    for i in range(len(robots)):
        for j in range(i + 1, len(robots)):
            if robots[i].active and robots[j].active and robots[i].check_collision(robots[j]):
                robots[i].avoid_collision(robots[j])
                robots[j].avoid_collision(robots[i])

    if all_robots_in_safe_area:
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"All robots have found the target in {time_taken:.2f} seconds!")
        save_time_to_file(time_taken, FILE_PATH)
        running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
