# Library imports
import sys
from OpenGL.GL import *
import glfw

import numpy as np
from mathlib import Point3
# import basic_shapes_extended as bs_ext
import camera as cam
import easy_shaders as es
import transformations2 as tr2
import lights as light

from model import *


# A class to store the application control
class Controller:
    def __init__(self):
        self.fillPolygon = True


# Global controller as communication with the callback function
controller = Controller()

# Create camera
cameramode = [2]  # 0: FPS // 1: Vertical // 2: Diagonal
x, y = coordinates2screen(-1, 0)
camera0 = cam.CameraXYZ(Point3(x, y, 2.0), center=Point3(0, 0, 1.2))
camera1 = cam.CameraXYZ(Point3(0, -0.1, 25), center=Point3())
camera2 = cam.CameraXYZ(Point3(-15, 13, 15), center=Point3())

def on_key(window_obj, key, scancode, action, mods):
    global controller
    global obj_light

    if action in (glfw.REPEAT, glfw.PRESS):
        # Controles de cámara
        if key == glfw.KEY_E:
            cameramode[0] = 1
        elif key == glfw.KEY_T:
            cameramode[0] = 2
        elif key == glfw.KEY_R:
            cameramode[0] = 0
        # Controles de movimiento
        elif key in (glfw.KEY_A, glfw.KEY_LEFT):
            S.body[0].orientation = -1
        elif key in (glfw.KEY_D, glfw.KEY_RIGHT):
            S.body[0].orientation = 1
        elif key in (glfw.KEY_W, glfw.KEY_UP):
            S.body[0].orientation = 0

    if action != glfw.PRESS:
        return

    if key == glfw.KEY_SPACE:
        controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_ESCAPE:
        sys.exit()

if __name__ == '__main__':

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 900
    height = 900
    window = glfw.create_window(width, height, 'HexSnake', None, None)

    if not window:
        glfw.terminate()
        sys.exit()

    glfw.make_context_current(window)
    # Connecting the callback function 'on_key' to handle keyboard events
    glfw.set_key_callback(window, on_key)
    # A diferencia del caso sin luces, ahora cambian los shaders.
    # Creating shader programs for textures and for colores
    colorShaderProgram = es.SimpleModelViewProjectionShaderProgram()
    lightShaderProgram = es.SimplePhongShaderProgram()
    textureShaderProgram = es.SimpleTextureModelViewProjectionShaderProgram()
    # Setting up the clear screen color
    glClearColor(0.15, 0.15, 0.15, 1.0)
    # As we work in 3D, we need to check which part is in front,
    # and which one is at the back
    glEnable(GL_DEPTH_TEST)
    # Transparencias!!
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Create models
    scene = Scene(colorShaderProgram, 5)
    S = Snake(5, scene)
    bg = BackGround()
    for r in scene.bestagons:
        for b in r:
            if b is not None and (b.pos_u + b.pos_v)%3 == 0:
                scene.oscilating.append(b)
    # Create light
    obj_light = light.Light(shader=lightShaderProgram, position=[0, 0, 5], color=[1, 1, 1])
    # Place light
    obj_light.place()
    # Create projection
    projection = tr2.perspective(45, float(width) / float(height), 0.1, 100)
    view1 = camera1.get_view()
    view2 = camera2.get_view()

    # loop de introducción con una breve animación
    ready = False
    t0 = glfw.get_time()
    introtime = 0
    while not ready:
        ti = glfw.get_time()
        dt = ti - t0
        introtime += dt
        t0 = ti
        glfw.poll_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # las instrucciones para dibujar con cámara diagonal, pero sin mover nada
        bg.draw(textureShaderProgram, projection, view2)
        glUseProgram(lightShaderProgram.shaderProgram)
        glUniform3f(glGetUniformLocation(lightShaderProgram.shaderProgram, "viewPos"), camera2.get_pos_x(), camera2.get_pos_y(), camera2.get_pos_z())
        scene.draw(colorShaderProgram, projection, view2, dt)
        S.draw(lightShaderProgram, projection, view2)
        if introtime >= 5:
            ready = True
        glfw.swap_buffers(window)

    for r in scene.bestagons:  # que se vayan apagando de a poco
        for b in r:
            if b is not None and (b.pos_u + b.pos_v)%3 == 0:
                #b.fill = False
                scene.deactivating.append(b)
    scene.oscilating = [] # que ya no oscilen
    for k in range(len(S.body)-1):  # ponemos a activar los hexágonos que integran a la serpiente
        i, j = coordinates2matrix(-k, 0, 11)
        scene.activating.append(scene.bestagons[int(i), int(j)])
    t0 = ti
    movetime = 1.8  # tiempo (en segundos) entre ubicaciones clave (keyframes les voy a llamar)
    isKeyFrame = True
    elapsed = 0  # tiempo que ha pasado entre keyframes
    cameramode = [0]
    food = Food(scene, obj_light)  # creamos la primera comida (le paso la luz porque la voy a mover en los métodos de esto)
    # loop principal
    while scene.playing and not glfw.window_should_close(window):  # loop del juego
        # Calculamos el dt
        ti = glfw.get_time()
        dt = ti - t0
        t0 = ti
        elapsed += dt  # cada vez estoy un poquito más cerca de un keyframe
        obj_light.place()
        # Chequeamos si debemos realizar un keyframe
        if elapsed >= movetime:  # y cuando me pasé...
            elapsed = 0  # reseteo la cuenta
            isKeyFrame = True  # y hacemos un keyframe

        # Using GLFW to check for input events
        glfw.poll_events()
        # Filling or not the shapes depending on the controller state
        if controller.fillPolygon:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Draw objects
        if cameramode[0] == 0:
            view0 = camera0.get_view()
            bg.draw(textureShaderProgram, projection, view0)
            glUseProgram(lightShaderProgram.shaderProgram)
            glUniform3f(glGetUniformLocation(lightShaderProgram.shaderProgram, "viewPos"), camera0.get_pos_x(), camera0.get_pos_y(), camera0.get_pos_z())
            try:
                scene.draw(colorShaderProgram, projection, view0, dt)
            except AttributeError:
                scene.playing = False
            S.draw(lightShaderProgram, projection, view0)
            food.draw(lightShaderProgram, projection, view0)
        elif cameramode[0] == 1:
            bg.draw(textureShaderProgram, projection, view1)
            glUseProgram(lightShaderProgram.shaderProgram)
            glUniform3f(glGetUniformLocation(lightShaderProgram.shaderProgram, "viewPos"), camera1.get_pos_x(), camera1.get_pos_y(), camera1.get_pos_z())
            try:
                scene.draw(colorShaderProgram, projection, view1, dt)
            except AttributeError:
                scene.playing = False
            S.draw(lightShaderProgram, projection, view1)
            food.draw(lightShaderProgram, projection, view1)
        elif cameramode[0] == 2:
            bg.draw(textureShaderProgram, projection, view2)
            glUseProgram(lightShaderProgram.shaderProgram)
            glUniform3f(glGetUniformLocation(lightShaderProgram.shaderProgram, "viewPos"), camera2.get_pos_x(), camera2.get_pos_y(), camera2.get_pos_z())
            try:
                scene.draw(colorShaderProgram, projection, view2, dt)
            except AttributeError:
                scene.playing = False
            S.draw(lightShaderProgram, projection, view2)
            food.draw(lightShaderProgram, projection, view2)

        S.move(dt, movetime, camera0)
        if isKeyFrame:
            S.shouldMoveTail = True
            S.moveApples()
            H = S.body[0]  # obtenemos cabeza y cola de la serpiente antes de actualizar las posiciones
            T = S.body[-1]
            i, j = coordinates2matrix(H.pos_a, H.pos_b, 2*scene.size + 1)  # obtenemos las coordenadas actuales de la cabeza
            a, b = food.pos_a, food.pos_b  # copio las coordenadas actuales de la comida antes de cambiar su ubicación
            HBestagon = scene.bestagons[int(i), int(j)]  # obtenemos el bestagon sobre el que la cabeza se encuentra ahora
            if S.isEating(food):  # si estoy comiendo (mi posición actual coincide con el lugar de la manzana)
                S.eat()
                food.pick()  # cambiamos la ubicación de la comida

            # desactivamos las coordenadas presentes de la cola
            i, j = coordinates2matrix(T.pos_a, T.pos_b, 2*scene.size + 1)
            scene.deactivating.append(scene.bestagons[int(i), int(j)])

            if S.isColliding():
                scene.playing = False
            # se actualizan las ubicaciones
            S.updateOrientation()
            H.updateOrientation(True)

            # que brille la posición futura
            i, j = coordinates2matrix(H.pos_a, H.pos_b, 2*scene.size + 1)
            try:
                HBestagon = scene.bestagons[int(i), int(j)]
            except IndexError:  # esto se activa si hay un out of bounds, es decir, la serpiente se sale de la escena
                scene.playing = False
            if a == H.pos_a and b == H.pos_b:
                scene.oscilating.remove(HBestagon)  # que ya no oscile el hexágono de la comida, para que se pueda activar
            scene.activating.append(HBestagon)

        # Once the drawing is rendered, buffers are swap so an uncomplete drawing is never seen
        glfw.swap_buffers(window)
        isKeyFrame = False  # terminado el frame, reseteo esto a False y se repite el ciclo

    cameramode = [1]
    scene.activating = []
    scene.oscilating = []
    for r in scene.bestagons:  # que se vayan apagando de a poco
        for b in r:
            if b is not None:
                scene.deactivating.append (b)  # desactiva todo
    # Lista para escribir "GO" (Game Over) de una manera dramática
    GO = [(1,-1), (1,-2), (0,-3), (-1,-3), (-2,-3), (-3,-3), (-3,-2), (-2,-1), (-1,-1), (0,1), (-1,1), (-1,2), (0,3), (1,3), (2,3), (3,3), (3,2), (2,1), (1,1)]
    endtime = 0
    obj_light.set_position(0, 0, 5)  # de vuelta a la posición inicial
    obj_light.change_color(1, 1, 1)  # y al color inicial
    j=0
    # loop final
    while not glfw.window_should_close(window):
        ti = glfw.get_time()
        dt = ti - t0
        t0 = ti
        endtime += dt
        glfw.poll_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        obj_light.place()
        bg.draw(textureShaderProgram, projection, view1)
        glUseProgram(lightShaderProgram.shaderProgram)
        glUniform3f(glGetUniformLocation(lightShaderProgram.shaderProgram, "viewPos"), camera1.get_pos_x(), camera1.get_pos_y(), camera1.get_pos_z())
        scene.draw(colorShaderProgram, projection, view1, dt)
        S.draw(lightShaderProgram, projection, view1)  # dibujamos las cosas con view1
        if endtime >= 1.2: # ya se desactivaron las cosas
            if len(GO) > 0 and j%2 == 0:
                a, b = GO.pop()
                i, j = coordinates2matrix(a, b, 2*scene.size+1)
                scene.oscilating.append(scene.bestagons[int(i), int(j)])
        glfw.swap_buffers(window)
        j+=1
    glfw.terminate()
