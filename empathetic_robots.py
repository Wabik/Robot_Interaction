import pygame
import random
import math
import time
import pandas as pd
import numpy as np

FILE_PATH = "j:\\Desktop\\Robot_Interaction\\empathetic_time.csv"

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Robot Simulation")

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (169, 169, 169) 
YELLOW = (255, 255, 0)
VIEW_COLOR = (200, 200, 200, 100)

ROBOT_SIZE = 20
SPEED = 2
BATTERY = 1.0
TURN_SPEED = 0.1
VIEW_DISTANCE = 150
VIEW_ANGLE = math.radians(76)

TARGET_SIZE = 100
target_x, target_y = WIDTH - TARGET_SIZE, 0

safe_areas = [
    pygame.Rect(target_x, 0, WIDTH - target_x, 5),
    pygame.Rect(795, 0, 5, 100)
]

# Wzór 2.1 - funkcja obliczająca podobieństwo między dwoma zbiorami rozmytymi
def similarity(Aj, Ai):
    n = len(Aj)
    distance = np.sqrt(np.sum((np.array(Aj) - np.array(Ai))**2) / n)
    return 1 - distance

# Wzór 2.2 - funkcja obliczająca ocenę stanu na podstawie podobieństwa do innych stanów
def calculate_reward(Ai, A_list, r_list):
    m = len(A_list)
    weighted_sum = 0
    for j in range(m):
        s_ij = similarity(A_list[j], Ai)
        weighted_sum += s_ij * r_list[j]
    return weighted_sum / m


class Robot:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.base_color = color
        self.color = self.base_color
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = SPEED
        self.active = True
        self.battery_level = BATTERY
        self.knowledge = [[0.9,0.7,0.5,0,0,0], 
                          [0.5,0,0,0,0,0], 
                          [0.6,0.9,0.1,0,0,0], 
                          [0.8,0.2,0,0.5,0.3,0], 
                          [0.9,0.8,0.8,0,0,0], 
                          [0.1,0,0,0,0,0], 
                          [0.3,0,0,0.5,0.9,0],
                          [0.7,0.5,0.5,1,0.6,0.3]]
        self.rewards =[0.9,0.3,0.6,0.7,1,0.1,0.5, 0.8]
        self.current_stage = 0
        self.current_reward = 0
        self.last_battery_update = time.time()

    def battery(self):
        current_time = time.time()
        if current_time - self.last_battery_update >= 10:
            self.battery_level = max(0, self.battery_level - 0.01)
            self.last_battery_update = current_time
            print(f"Battery level of {self.color} robot: {self.battery_level:.2f}")
            vector_battery = round(self.battery_level, 2)

    def move(self, robots):
        if self.active:
            self.battery()
            if self.battery_level <= 0:
                self.speed = 0
                self.active = False
                self.color = GRAY
            else:
                if self.can_see_target(target_x, target_y, TARGET_SIZE):
                    self.color = GREEN
                    self.rotate_towards(target_x + TARGET_SIZE // 2, target_y + TARGET_SIZE // 2)
                elif self.can_see_green_robot(robots):
                    self.color = BLUE
                else:
                    self.color = self.base_color
                    self.rotate_randomly()

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
        self.vector_to_edges()
        self.vector_to_target()

    def draw_visibility_arc(self):
        end_angle1 = self.angle - VIEW_ANGLE / 2
        end_angle2 = self.angle + VIEW_ANGLE / 2
        points = [(self.x, self.y)]
        for angle in [end_angle1, end_angle2]:
            dx = self.x + VIEW_DISTANCE * math.cos(angle)
            dy = self.y + VIEW_DISTANCE * math.sin(angle)
            points.append((dx, dy))
        pygame.draw.polygon(screen, VIEW_COLOR, points, 0)

    def calculate_distances_to_edges(self):
        distances = []
        for angle_offset in [-VIEW_ANGLE / 2, 0, VIEW_ANGLE / 2]:
            angle = self.angle + angle_offset
            angle = angle % (2 * math.pi)
            
            if 0 <= angle < math.pi / 2:  # Right and Bottom edges
                distance_to_right = (WIDTH - self.x) / math.cos(angle)
                distance_to_bottom = (HEIGHT - self.y) / math.sin(angle)
                distance = min(distance_to_right, distance_to_bottom)
            elif math.pi / 2 <= angle < math.pi:  # Bottom and Left edges
                distance_to_bottom = (HEIGHT - self.y) / math.sin(angle)
                distance_to_left = self.x / math.cos(angle - math.pi)
                distance = min(distance_to_bottom, distance_to_left)
            elif math.pi <= angle < 3 * math.pi / 2:  # Left and Top edges
                distance_to_left = self.x / math.cos(angle - math.pi)
                distance_to_top = self.y / math.sin(angle - math.pi)
                distance = min(distance_to_left, distance_to_top)
            elif 3 * math.pi / 2 <= angle < 2 * math.pi:  # Top and Right edges
                distance_to_top = self.y / math.sin(angle - math.pi)
                distance_to_right = (WIDTH - self.x) / math.cos(angle)
                distance = min(distance_to_top, distance_to_right)

            distances.append((distance, angle))
        return distances    

    def vector_to_edges(self):
        distances = self.calculate_distances_to_edges()
        for distance, angle in distances:
            if distance < VIEW_DISTANCE:
                end_x = self.x + distance * math.cos(angle)
                end_y = self.y + distance * math.sin(angle)
                pygame.draw.line(screen, BLUE, (self.x, self.y), (end_x, end_y), 1)
                vector_from_wall = 1 - (distance / 150)
                return round(vector_from_wall, 2)
                # print("Vector", round(vector_from_wall,2 ))
                # print(f"Distance to edge: {distance:.0f}")
            else: 
                return 0

    def calculate_distance_to_target(self):
        nearest_x = max(target_x + 5, min(self.x, target_x + TARGET_SIZE - 5))
        nearest_y = max(target_y + 5, min(self.y, target_y + TARGET_SIZE - 5))

        distance = math.sqrt((self.x - nearest_x) ** 2 + (self.y - nearest_y) ** 2)
        return distance

    def vector_to_target(self):
        distance = self.calculate_distance_to_target()
        # if self.is_in_safe_area():
        #     return None

        if distance < VIEW_DISTANCE:
            vector_to_target = 1 - (distance / VIEW_DISTANCE)
        else:
            vector_to_target = 0  # Target is out of the visibility range
        # print("Vector to target:", round(vector_to_target, 2))
        return round(vector_to_target, 2)

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

    def can_see_green_robot(self, robots):
        for other in robots:
            if other != self and other.color == GREEN:
                distance = math.hypot(self.x - other.x, self.y - other.y)
                if distance <= VIEW_DISTANCE:
                    angle_to_other = math.atan2(other.y - self.y, other.x - self.x)
                    angle_diff = (angle_to_other - self.angle) % (2 * math.pi)
                    if angle_diff > math.pi:
                        angle_diff -= 2 * math.pi
                    if -VIEW_ANGLE / 2 <= angle_diff <= VIEW_ANGLE / 2:
                        return True
        return False

    def can_see_blue_robot(self, robots):
        for other in robots:
            if other != self and other.color == BLUE:
                distance = math.hypot(self.x - other.x, self.y - other.y)
                if distance <= VIEW_DISTANCE:
                    angle_to_other = math.atan2(other.y - self.y, other.x - self.x)
                    angle_diff = (angle_to_other - self.angle) % (2 * math.pi)
                    if angle_diff > math.pi:
                        angle_diff -= 2 * math.pi
                    if -VIEW_ANGLE / 2 <= angle_diff <= VIEW_ANGLE / 2:
                        return True
        return False

    def can_see_any_robot(self, robots):
        for other in robots:
            if other != self:
                distance = math.hypot(self.x - other.x, self.y - other.y)
                if distance <= VIEW_DISTANCE:
                    angle_to_other = math.atan2(other.y - self.y, other.x - self.x)
                    angle_diff = (angle_to_other - self.angle) % (2 * math.pi)
                    if angle_diff > math.pi:
                        angle_diff -= 2 * math.pi
                    if -VIEW_ANGLE / 2 <= angle_diff <= VIEW_ANGLE / 2:
                        return True
        return False

    def count_visible_robots(self, robots):
        total_robots = len(robots) - 1
        if total_robots <= 0:
            return 0
        
        visible_count = 0
        for other in robots:
            if other != self:
                distance = math.hypot(self.x - other.x, self.y - other.y)
                if distance <= VIEW_DISTANCE:
                    angle_to_other = math.atan2(other.y - self.y, other.x - self.x)
                    angle_diff = (angle_to_other - self.angle) % (2 * math.pi)
                    if angle_diff > math.pi:
                        angle_diff -= 2 * math.pi
                    if -VIEW_ANGLE / 2 <= angle_diff <= VIEW_ANGLE / 2:
                        visible_count += 1
        vector_see_robots = round(visible_count / total_robots,2)
        # print(vector_see_robots)
        return vector_see_robots
    
    def find_nearest_robot_of_color(self, robots, color):
        min_distance = VIEW_DISTANCE  # Only consider distances within view distance
        nearest_robot = None
        for other in robots:
            if other != self and other.color == color:
                distance = math.hypot(self.x - other.x, self.y - other.y)
                if distance <= VIEW_DISTANCE:
                    angle_to_other = math.atan2(other.y - self.y, other.x - self.x)
                    angle_diff = (angle_to_other - self.angle) % (2 * math.pi)
                    if angle_diff > math.pi:
                        angle_diff -= 2 * math.pi
                    if -VIEW_ANGLE / 2 <= angle_diff <= VIEW_ANGLE / 2 and distance < min_distance:
                        min_distance = distance
                        nearest_robot = other
        return nearest_robot, min_distance

    def vector_blue_robot(self, robots):
        nearest_blue_robot, distance = self.find_nearest_robot_of_color(robots, BLUE)
        if nearest_blue_robot:
            return 1 - (distance / VIEW_DISTANCE)
        return 0   
    def vector_green_robot(self, robots):
        nearest_green_robot, distance = self.find_nearest_robot_of_color(robots, GREEN)
        if nearest_green_robot:
            return 1 - (distance / VIEW_DISTANCE)
        return 0  # 


    def current_knowledge(self, robots):
        current_vectors = {
            'battery': self.battery_level,
            'to_edge': self.vector_to_edges(),
            'to_target': self.vector_to_target(),
            'count_robots': self.count_visible_robots(robots),
            'to_green_robot': self.vector_green_robot(robots),
            'to_blue_robot': self.vector_blue_robot(robots)
        }
        print("Wiedza", current_vectors)
        self.current_stage = list(current_vectors.values())
        print("Obecny stan", self.current_stage)
        reward = calculate_reward(self.current_stage, self.knowledge, self.rewards)
        self.current_reward = reward
        print("Obecna nagroda", round(self.current_reward,2))

    # def current_rewards(self,robots):
    #     reward = calculate_reward(self.current_stage, self.knowledge, self.rewards)
    #     self.current_reward = reward
    #     print("Obecna nagroda", self.current_reward)
   


    def check_collision(self, other):
        distance = math.hypot(self.x - other.x, self.y - other.y)
        return distance < ROBOT_SIZE

    def avoid_collision(self, other):
        print("Collision!")
        self.angle = (self.angle + math.pi / 2) % (2 * math.pi)

def vector_green_robot_vision(robot, robots):
    if robot.can_see_green_robot(robots):
        return 1
    else:
        return 0

def vector_blue_robot_vision(robot, robots):
    if robot.can_see_blue_robot(robots):
        return 1
    else:
        return 0

def save_time_to_file(time_taken, file_path):
    try:
        df = pd.DataFrame({"selfish time": [time_taken]})
        df.to_csv(file_path, mode='a', header=False, index=False)
    except Exception as e:
        print(f"Error saving to file: {e}")

robots = [
    Robot(100, 100, RED),
    Robot(300, 300, RED),
    Robot(600, 600, RED),
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
        pygame.draw.rect(screen, GREEN, area)

    all_robots_in_safe_area = True
    for robot in robots:
        
        if not robot.is_in_safe_area():
            robot.move(robots)
            robot.current_knowledge(robots)
            # robot.current_reward()

            all_robots_in_safe_area = False
        else:
            robot.speed = 0
            robot.active = False
            robot.color = GRAY
        robot.draw()
        
        visibility_ratio = robot.count_visible_robots(robots)
        blue_ratio = robot.vector_blue_robot(robots)
        green_ratio = robot.vector_green_robot(robots)

        # sees_green = vector_green_robot_vision(robot, robots)
        # print(f"Robot at ({robot.x}, {robot.y}) sees a green robot: {sees_green}")
        
        # sees_blue = vector_blue_robot_vision(robot, robots)
        # print(sees_blue)
        # print(f"Robot at ({robot.x}, {robot.y}) sees a blue robot: {sees_blue}")

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

# def print_knowledge_summary(robots):
#     print("Knowledge Summary for Each Robot:")
#     for index, robot in enumerate(robots):
#         knowledge_count = len(robot.knowledge)
#         print(f"Robot {index + 1}): {knowledge_count} knowledge points")

pygame.quit()
# print_knowledge_summary(robots)
