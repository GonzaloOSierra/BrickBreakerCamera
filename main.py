import cv2
import mediapipe as mp
import math
import time
import random

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

projectiles = []
last_shot_time = {}
shot_delay = 0.2
projectile_colors = [(255, 255, 0), (255, 0, 0), (0, 255, 0)]

rect_width = int(90 * 0.7)
rect_height = int(35 * 0.7)
rect_colors_left = [random.choice(projectile_colors) for _ in range(3)]
rect_colors_right = [random.choice(projectile_colors) for _ in range(3)]

block_rows = 1
block_cols = 16
block_width = 40
block_height = 15

# Variables de estado del juego
game_started = False
start_time = None
completed = False
elapsed_time_final = None

def point_to_line_distance(p1, p2, p3):
    return abs((p2[1] - p1[1]) * p3[0] - (p2[0] - p1[0]) * p3[1] + p2[0] * p1[1] - p2[1] * p1[0]) / \
           math.sqrt((p2[1] - p1[1])**2 + (p2[0] - p1[0])**2)

class Projectile:
    def __init__(self, start_position, direction_vector, color):
        self.position = list(start_position)
        self.direction = direction_vector
        self.speed = 10
        self.color = color

    def move(self):
        self.position[0] += self.direction[0] * self.speed
        self.position[1] += self.direction[1] * self.speed

    def is_out_of_bounds(self, width, height):
        return (
            self.position[0] < 0 or self.position[0] > width or
            self.position[1] < 0 or self.position[1] > height
        )

def reset_game():
    global blocks, projectiles, rect_colors_left, rect_colors_right, start_time, game_started, completed, elapsed_time_final
    blocks = []
    for row in range(block_rows):
        block_row = []
        for col in range(block_cols):
            color = random.choice(projectile_colors)
            block_row.append(color)
        blocks.append(block_row)
    projectiles = []
    rect_colors_left = [random.choice(projectile_colors) for _ in range(3)]
    rect_colors_right = [random.choice(projectile_colors) for _ in range(3)]
    start_time = time.time()
    game_started = True
    completed = False
    elapsed_time_final = None

# Inicializar bloques al empezar
reset_game()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # Voltear horizontalmente

    height, width, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Dibujar rectángulos de las manos
    for i in range(3):
        y_bottom = height - 10 - (i * int(rect_height * 1.3))
        y_top = y_bottom - rect_height
        cv2.rectangle(frame, (10, y_top), (10 + rect_width, y_bottom), rect_colors_left[i], -1)
        x_left = width - 10 - rect_width
        cv2.rectangle(frame, (x_left, y_top), (x_left + rect_width, y_bottom), rect_colors_right[i], -1)

    # Procesar detección de manos y disparos solo si no está completado
    if not completed and results.multi_hand_landmarks:
        for hand_idx, landmarks in enumerate(results.multi_hand_landmarks[:2]):

            wrist = None
            index_finger = None
            thumb = None

            for id, landmark in enumerate(landmarks.landmark):
                px, py = int(landmark.x * width), int(landmark.y * height)
                if id == 1:
                    wrist = (px, py)
                    cv2.circle(frame, wrist, 5, (255, 0, 0), -1)
                elif id == 8:
                    index_finger = (px, py)
                    cv2.circle(frame, index_finger, 5, (0, 0, 255), -1)
                elif id == 4:
                    thumb = (px, py)
                    cv2.circle(frame, thumb, 5, (0, 255, 0), -1)

            if wrist and index_finger:
                cv2.line(frame, wrist, index_finger, (0, 255, 0), 2)

                if thumb:
                    distance = point_to_line_distance(wrist, index_finger, thumb)
                    current_time = time.time()

                    if distance <= 10 and (current_time - last_shot_time.get(hand_idx, 0)) > shot_delay:
                        last_shot_time[hand_idx] = current_time
                        dx = index_finger[0] - wrist[0]
                        dy = index_finger[1] - wrist[1]
                        magnitude = math.hypot(dx, dy)
                        if magnitude != 0:
                            direction = (dx / magnitude, dy / magnitude)

                            if hand_idx == 0:
                                color = rect_colors_left[-1]
                                rect_colors_left.insert(0, random.choice(projectile_colors))
                                rect_colors_left = rect_colors_left[:3]
                            else:
                                color = rect_colors_right[-1]
                                rect_colors_right.insert(0, random.choice(projectile_colors))
                                rect_colors_right = rect_colors_right[:3]

                            new_projectile = Projectile(index_finger, direction, color)
                            projectiles.append(new_projectile)

    # Mover y dibujar proyectiles
    for p in projectiles[:]:
        p.move()
        x, y = int(p.position[0]), int(p.position[1])
        cv2.circle(frame, (x, y), 5, p.color, -1)

        col = x // block_width
        row = y // block_height
        if 0 <= row < block_rows and 0 <= col < block_cols:
            block_color = blocks[row][col]
            if block_color:
                if block_color == p.color:
                    blocks[row][col] = None
                    projectiles.remove(p)
                    continue
                else:
                    # Si no es mismo color, desaparecer proyectil
                    projectiles.remove(p)
                    continue

        if p.is_out_of_bounds(width, height):
            projectiles.remove(p)

    if not completed:
        all_none = all(all(block is None for block in row) for row in blocks)
        if all_none:
            completed = True
            elapsed_time_final = time.time() - start_time

    # Dibujar bloques
    for row in range(block_rows):
        for col in range(block_cols):
            color = blocks[row][col]
            if color:
                x1 = col * block_width
                y1 = row * block_height
                x2 = x1 + block_width
                y2 = y1 + block_height
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)

    if completed:
        # Sólo cubrimos con negro el 30% superior de la pantalla
        max_height = int(height * 0.3)
        cv2.rectangle(frame, (0, 0), (width, max_height), (0, 0, 0), -1)
        
        # Escribir "COMPLETADO" centrado en la parte superior (dentro del rectángulo)
        texto = "COMPLETADO"
        font = cv2.FONT_HERSHEY_SIMPLEX
        escala = 3
        grosor = 5
        color = (255, 255, 255)
        (text_width, text_height), _ = cv2.getTextSize(texto, font, escala, grosor)
        x_text = (width - text_width) // 2
        y_text = (max_height + text_height) // 2
        cv2.putText(frame, texto, (x_text, y_text), font, escala, color, grosor)
        
        # Mostrar temporizador pausado (tiempo final) en la parte inferior central
        elapsed_text = f"Tiempo: {elapsed_time_final:.1f} s"
        (et_width, et_height), _ = cv2.getTextSize(elapsed_text, font, 1, 2)
        x_et = (width - et_width) // 2
        y_et = height - 20
        cv2.putText(frame, elapsed_text, (x_et, y_et), font, 1, color, 2)
    else:
        # Mientras el juego no esté completado mostramos el temporizador en tiempo real abajo
        elapsed_time = time.time() - start_time
        elapsed_text = f"Tiempo: {elapsed_time:.1f} s"
        font = cv2.FONT_HERSHEY_SIMPLEX
        (et_width, et_height), _ = cv2.getTextSize(elapsed_text, font, 1, 2)
        x_et = (width - et_width) // 2
        y_et = height - 20
        cv2.putText(frame, elapsed_text, (x_et, y_et), font, 1, (255, 255, 255), 2)

    cv2.imshow("Juego", frame)
    key = cv2.waitKey(1)
    if key == ord("q"):
        break
    elif key == ord("r"):
        reset_game()

cap.release()
cv2.destroyAllWindows()
