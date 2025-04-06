import math
import random
import numpy as np
from OpenGL.GL import *

import basic_shapes as bs
import transformations2 as tr
import easy_shaders as es
from uniform import Uniform

s = math.sqrt(3)  # voy a usar esto más adelante

# retorna una lista con 2tuplas que asocian la velocidad (en xy-coordenadas) a cada orientación entre 1 y 5.
vel = {
    0: [0, s],       # La orientación 0 es hacia arriba. Es la orientación que eleva a y fija b
    1: [1.5, s/2],   # La orientación 1 es en la diagonal positiva. Es la orientación que eleva a y b
    2: [1.5, -s/2],  # La orientación 2 es en la diagonal negativa. Es la orientación que fija a y eleva b
    3: [0, -s],      # La orientación 3 es opuesta a 0. Es la orientación que disminuye a y fija b
    4: [-1.5, -s/2], # La orientación 4 es la opuesta a 1. Es la orientación que disminuye b y a
    5: [-1.5, s/2]   # La orientación 5 es la opuesta a 2. Es la orientación que fija a y disminuye b
}

class Axis():

    def __init__(self, pipeline):
        self.model = es.toGPUShape(bs.createAxis(1))
        self.show = True
        self.translation = Uniform("vec3", [0, 0, 0])
        self.translation.locateVariable(pipeline.shaderProgram, 'translation')

    def toggle(self):
        self.show = not self.show

    def draw(self, pipeline, projection, view):
        if not self.show:
            return
        glUseProgram(pipeline.shaderProgram)
        self.translation.data = [0, 0, 0]
        self.translation.uploadData()
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'projection'), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'view'), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE, tr.identity())
        pipeline.drawShape(self.model, GL_LINES)

class BackGround():
    def __init__(self):
        self.model = es.toGPUShape(bs.createTextureCube("S1.png"), GL_REPEAT, GL_NEAREST)
        self.transform = tr.uniformScale(51)

    def draw(self, pipeline, projection, view):
        #self.alphaU.data = 1.0
        #self.alphaU.uploadData()
        glUseProgram(pipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'projection'), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'view'), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE, self.transform)
        pipeline.drawShape(self.model)

class Bestagon():
    # r, g, b son los fill colors
    def __init__(self, r, g, b, a, u, v, z, pipeline):
        # almaceno los colores porque van a ser usados por la luz
        self.red = r
        self.green = g
        self.blue = b
        #u, v, z van a representar posiciones en coordenadas hexagonales!!
        self.pos_u = u
        self.pos_v = v
        self.color = [r, g, b, a]  # quiero una lista?
        self.model1 = es.toGPUShape(bs.createBestagon())  # model1 es el borde
        self.model2 = es.toGPUShape(bs.createBestagonFill(r, g, b))
        self.show = True  # se muestra el grid
        self.fill = False  # Pero inicialmente no se muestra el relleno
        self.oscilating = False  # Solo va a oscilar en ocasiones específicas
        self.brightening = True  # esto ayuda a controlar la oscilación
        self.alphaU = Uniform('float', a)
        self.alphaU.locateVariable(pipeline.shaderProgram, 'alpha')
        x, y = coordinates2screen(u, v)
        self.transform = tr.translate(x, y, z)

    def activate(self, dt):  # duración: 1 seg
        if self.fill:  # Si ya tienes el fill activado, es porque está corriendo la animación
            self.color[3] = min([1.0, self.color[3] + dt])
            return
        # De lo contrario, la animación debe iniciar
        self.fill = True  # Se supone que en este punto el alpha es cero
        self.color[3] += dt

    def deactivate(self, dt):  # duración: 1 seg
        # esto no debería ser llamado si fill es falso
        if self.color[3] == 0:  # si alpha llegó a cero...
            self.fill = False  # entonces puedes desactivar el fill
            return
        # de lo contrario...
        self.color[3] = max([0, self.color[3] - dt])

    def oscilate(self, dt):
        if self.brightening:
            self.activate(dt)
            if self.color[3] == 1:
                self.brightening = False
            return
        self.deactivate(dt)
        if not self.fill:
            self.brightening = True
        return

    def toggle(self):
        self.show = not self.show

    def setAlpha(self, a):
        self.color[3] = a

    def draw(self, pipeline, projection, view):
        if not self.show:
            return
        if self.fill:
            glUseProgram(pipeline.shaderProgram)
            self.alphaU.data = self.color[3]
            self.alphaU.uploadData()
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'projection'), 1, GL_TRUE, projection)
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'view'), 1, GL_TRUE, view)
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE, self.transform)
            pipeline.drawShape(self.model2, GL_TRIANGLE_FAN)
        glUseProgram(pipeline.shaderProgram)
        self.alphaU.data = 1.0
        self.alphaU.uploadData()
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'projection'), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'view'), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE, self.transform)
        pipeline.drawShape(self.model1, GL_LINES)

class Scene():
    def __init__(self, pipeline, N=7):
        self.size = N
        self.bestagons = np.empty((2*N+1, 2*N+1), dtype=object)
        self.playing = True
        for i in range(2*N+1):
            for j in range(2*N+1):
                a, b = matrix2coordinates(i, j, 2*N+1)
                if a - b <= N and a - b >= -N:  # esta es la condición que arma el mapa hexagonal
                    self.bestagons[i, j] = Bestagon(random.random(), random.random(), random.random(), 0.0, a, b, 0, pipeline)
        self.activating = []  # Una lista de hexágonos activándose
        self.deactivating = []  # Los hexágonos descactivándose
        self.oscilating = []  # Los hexágonos oscilando

    def draw(self, pipeline, projection, view, dt):  # Ya que esto se va a correr a cada frame, voy a incluir acá el código de las animaciones
        # estacionarias de los hexágonos
        for h in self.activating:
            h.activate(dt)
            if h.color[3] == 1:  # si ya lo activé...
                self.activating.remove(h)  # entonces nada más que hacer aquí
        for h in self.deactivating:
            h.deactivate(dt)
            if not h.fill:  # si llegué al último paso de la desactivación en el que quité el fill...
                self.deactivating.remove(h)  # entonces nada más que hacer aquí
        for h in self.oscilating:  # esta lista no remueve elementos por su cuenta. Así que debo modificarla desde el objeto comida
            h.oscilate(dt)  # oscile mientras lo tenga en esta lista
        for r in self.bestagons:
            for b in r:
                if b is not None:
                    b.draw(pipeline, projection, view)

class SnakeBody():
    def __init__(self, a, b, scene, iniOrientation = 0):  # a,b son coordenadas hexagonales, todo va a ser hexagonal a este nivel
        self.pos_a = a  # estas son ubicaciones abstractas, que cambian con el orientation
        self.pos_b = b
        self.pos_x, self.pos_y = coordinates2screen(a, b)
        self.scene = scene
        self.containsApple = False  # un bool que nos indica si ese cuadrado ""contiene"" una manzana que la serpiente comió
        self.orientation = 0  # Número entre -1 y 1, esto es modificable en cada frame vía controlador (indica para dónde girar)
        self.key_orientation = 0  # Esta es la orientación que se actualiza en los keyframes y es la que determina el movimiento realmente
        if isinstance(self, SnakeHead):
            self.model = es.toGPUShape(shape = readOBJ2("cabeza.obj", (0.2, 0.6, 0.2)))
        else:
            self.model = es.toGPUShape(shape = readOBJ("cuerpo.obj", (0.2, 0.6, 0.2)))
        self.Scale = tr.scale(1, 1, 1)  # esto es fijo!
        self.Rotate = tr.rotationZ(np.pi/2)  # esto se actualiza con los updateOrientation
        if iniOrientation == 0:
            self.Rotate = tr.rotationZ(np.pi/2)
        elif iniOrientation == 1:
            self.Rotate = tr.rotationZ(np.pi/6)  # -30°
        elif iniOrientation == 2:
            self.Rotate = tr.rotationZ(-np.pi/6)  # -120°
        elif iniOrientation == 3:
            self.Rotate = tr.rotationZ(-np.pi/2)  # 180°
        elif iniOrientation == 4:
            self.Rotate = tr.rotationZ(-5*np.pi/6)
        elif iniOrientation == 5:
            self.Rotate = tr.rotationZ(5*np.pi/6)
        self.Trans = tr.translate(self.pos_x, self.pos_y, 0.3)  # esto se actualiza a cada rato
        self.transform = tr.matmul([self.Trans, self.Rotate, self.Scale])


    def move(self, dt, movetime):  # Esto es movimiento continuo, no en el mapa abstracto
        v = vel[self.key_orientation]  # esta es la velocidad asociada a la orientación que el SnakeBody tiene en este momento
        self.pos_x += dt*v[0] / movetime
        self.pos_y += dt*v[1] / movetime
        self.Trans = tr.translate(self.pos_x, self.pos_y, 0.3)
        self.transform = tr.matmul([self.Trans, self.Rotate, self.Scale])

    def draw(self, pipeline, projection, view):
        glUseProgram(pipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'projection'), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'view'), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE, self.transform)
        pipeline.drawShape(self.model, mode=GL_TRIANGLES)

    def updateOrientation(self, b):  # esto corre en cada keyframe. b es un bool relacionado a shouldModeTail
        self.key_orientation += self.orientation  # pásale la actual a la key
        self.key_orientation %= 6
        self.orientation = 0  # porque este es el paso el nuevo frame
        if not b:  # si esto se cumple, es porque b es falso, osea que shouldMoveTail ha sido desactivado
            return  # así que detenemos la función cuando corre para la cola
        if self.key_orientation == 0:
            self.pos_a += 1
            self.Rotate = tr.rotationZ(np.pi/2)
        elif self.key_orientation == 1:
            self.pos_a += 1
            self.pos_b += 1
            self.Rotate = tr.rotationZ(np.pi/6)  # -30°
        elif self.key_orientation == 2:
            self.pos_b += 1
            self.Rotate = tr.rotationZ(-np.pi/6)  # -120°
        elif self.key_orientation == 3:
            self.pos_a -= 1
            self.Rotate = tr.rotationZ(-np.pi/2)  # 180°
        elif self.key_orientation == 4:
            self.pos_a -= 1
            self.pos_b -= 1
            self.Rotate = tr.rotationZ(-5*np.pi/6)
        elif self.key_orientation == 5:
            self.pos_b -= 1
            self.Rotate = tr.rotationZ(5*np.pi/6)

class SnakeHead(SnakeBody): # SnakeHead es un tipo especial de SnakeBody, con su propio método de movimiento, el cual involucra a la cámara
    def move(self, dt, movetime, ca):
        v = vel[self.key_orientation]  # esta es la velocidad asociada a la orientación que el SnakeBody tiene en este momento
        dx = dt*v[0] / movetime
        dy = dt*v[1] / movetime
        self.pos_x += dx
        self.pos_y += dy
        self.Trans = tr.translate(self.pos_x, self.pos_y, 0.3)
        self.transform = tr.matmul([self.Trans, self.Rotate, self.Scale])  # esa primera rotación corrige el modelo solamente
        ca.move_center_x(dx)
        ca.move_center_y(dy)

class SnakeNeck(SnakeBody): # SnakNeck es un tipo especial de SnakeBody, con su propio método de movimiento, el cual involucra a la cámara
    def move(self, dt, movetime, ca):
        v = vel[self.key_orientation]  # esta es la velocidad asociada a la orientación que el SnakeBody tiene en este momento
        dx = dt*v[0] / movetime
        dy = dt*v[1] / movetime
        self.pos_x += dx
        self.pos_y += dy
        self.Trans = tr.translate(self.pos_x, self.pos_y, 0.3)
        self.transform = tr.matmul([self.Trans, self.Rotate, self.Scale])
        ca.move_x(dx)
        ca.move_y(dy)

class Food():
    def __init__(self, scene, light):
        self.scene = scene
        self.light = light  # almaceno la luz
        self.model = es.toGPUShape(shape = readOBJ2("champi.obj", (0.75, 0.2, 0.2)))
        # una iteración de pick()
        N = 2*scene.size + 1
        i = random.randint(1, N-1)
        j = random.randint(1, N-1)
        b = scene.bestagons[i, j]
        while b is None or b.fill:
            i = random.randint(1, N-1)
            j = random.randint(1, N-1)
            b = scene.bestagons[i, j]
        self.pos_a, self.pos_b = matrix2coordinates(i, j, N)
        scene.oscilating.append(b)
        self.transform = tr.identity()

    def pick(self):
        N = 2*self.scene.size + 1
        i = random.randint(1, N-1)
        j = random.randint(1, N-1)
        b = self.scene.bestagons[i, j]
        while b is None or b.fill:  # me pongo a elegir un bestagon que no esté ocupado por la serpiente
            i = random.randint(1, N-1)
            j = random.randint(1, N-1)
            b = self.scene.bestagons[i, j]
        self.pos_a, self.pos_b = matrix2coordinates(i, j, N)
        x, y = coordinates2screen(self.pos_a, self.pos_b)
        self.light.set_position(x, y, 5)  # movemos la luz sobre la nueva ubicación
        self.light.change_color(b.red, b.green, b.blue)
        self.scene.oscilating.append(b)

    def draw(self, pipeline, projection, view):
        x, y = coordinates2screen(self.pos_a, self.pos_b)
        self.transform = tr.translate(x, y, 0.3)
        glUseProgram(pipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'projection'), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'view'), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE, self.transform)
        pipeline.drawShape(self.model, mode=GL_TRIANGLES)

class Snake():
    def __init__(self, n, scene):  # los squares se inicializarán con orientación cero
        k = 0
        self.body = [SnakeHead(-k, 0, scene)]
        self.scene = scene
        self.shouldMoveTail = True  # switch que indica si dejar quieta la cola o no 
        k += 1
        self.body.append(SnakeNeck(-k, 0, scene))
        k += 1
        while k < n:  # verificar que esto corra la cantidad de veces que debería
            self.body.append(SnakeBody(-k, 0, scene))
            k += 1

    def move(self, dt, movetime, ca):
        L = len(self.body)
        self.body[0].move(dt, movetime, ca)  # primero que nada, movamos la cabeza
        i = 1  # ahora... todo el resto
        while i < L-1:
            dx = self.body[i-1].pos_x - self.body[i+1].pos_x
            dy = self.body[i-1].pos_y - self.body[i+1].pos_y
            # Ahora... va a ser la única vez en mi vida que voy a usar esta nemotecnia
            if dx == 0:  # primero... evitemos la división por cero
                if dy > 0:
                    ang = np.pi/2
                else:
                    ang = -np.pi/2
            elif dx > 0:  # mitad derecha
                ang = math.atan(dy/dx)
            else:  # dx < 0  mitad izquierda
                ang = np.pi + math.atan(dy/dx)
            # he encontrado el ángulo, ahora a usarlo
            self.body[i].Rotate = tr.rotationZ(ang)  # ya, lo giré
            if i == 1:  # estamos en el snakeNeck...
                self.body[i].move(dt, movetime, ca)
            else:  # falta lidiar con la cola
                self.body[i].move(dt, movetime)  # de lo contrario, adelante
            i += 1  # casi se me olvida!
        # y luego de mover las orientaciones para todo el cuerpo de entremedio, las movemos para la cola. Con i = L-1
        if not self.shouldMoveTail:  # pero solo si deberíamos mover la cola
            return
        dx = self.body[i-1].pos_x - self.body[i].pos_x
        dy = self.body[i-1].pos_y - self.body[i].pos_y
        # Ahora... va a ser la única vez en mi vida que voy a usar esta nemotecnia
        if dx == 0:  # primero... evitemos la división por cero
            if dy > 0:
                ang = np.pi/2
            else:
                ang = -np.pi/2
        elif dx > 0:  # mitad derecha
            ang = math.atan(dy/dx)
        else:  # dx < 0  mitad izquierda
            ang = np.pi + math.atan(dy/dx)
        # he encontrado el ángulo, ahora a usarlo
        self.body[i].Rotate = tr.rotationZ(ang)  # ya, lo giré
        self.body[i].move(dt, movetime)
        #for b in self.body:  # legacy code de cuando no giraba las cosas cada frame
        #    if isinstance(b, (SnakeHead, SnakeNeck)):
        #        b.move(dt, movetime, ca)
        #    else:
        #        if not self.shouldMoveTail and b == self.body[-1]:  # si llegué a mover la cola, pero no debería
        #            return  # no seguir con la función.
        #        b.move(dt, movetime)  # VSCode me da advertencias por esto, pero es porque los argumentos para los distintos métodos move son distintos

    def draw(self, pipeline, projection, view):
        for b in self.body:
            b.draw(pipeline, projection, view)

    def updateOrientation(self):
        k = 0
        L = len(self.body)-1
        self.body[L-k].key_orientation = self.body[L-(k+1)].key_orientation
        self.body[L-k].updateOrientation(self.shouldMoveTail)
        k += 1
        while k < L:
            self.body[L-k].key_orientation = self.body[L-(k+1)].key_orientation
            self.body[L-k].updateOrientation(True)
            k += 1

    def moveApples(self):
        k = 0
        L = len(self.body)-1
        while k < L:
            self.body[L-k].containsApple = self.body[L-(k+1)].containsApple
            self.body[L-(k+1)].containsApple = False  # para que no haya una manzana en la cabeza generándose infinitamente
            k += 1
        tail = self.body[-1]
        if tail.containsApple:
            tail.containsApple = False
            self.body.append(SnakeBody(tail.pos_a, tail.pos_b, self.scene, iniOrientation=tail.key_orientation))
            self.shouldMoveTail = False  # congela la cola
            self.body[-1].key_orientation = self.body[-2].key_orientation  # debe moverse igual a aquella de la que proviene,
            # no partir con orientación cero

    def isEating(self, food):
        Hpos_a = self.body[0].pos_a
        Hpos_b = self.body[0].pos_b
        return Hpos_a == food.pos_a and Hpos_b == food.pos_b

    def eat(self):
        self.body[0].containsApple = True
    
    def isColliding(self):  # retorna True cuando la serpiente choca consigo misma
        head = self.body[0]  # la única cosa que puede chocar es la cabeza
        for b in self.body[1:]:
            if b.pos_a == head.pos_a and b.pos_b == head.pos_b:
                return True
        return False

def matrix2coordinates(i, j, N):
    # i,j recorren de 1 a N con N impar
    # retorna a,b, que representan las coordenadas hexagonales
    return i - (N+1)/2 +1, j - (N+1)/2 + 1

def coordinates2screen(a, b):
    # a: horizontal hacia la derecha
    # b: vertical hacia arriba
    # Asumo lado del hexágono = 1
    x = b*3/2
    y = a*s - b*s/2
    return x, y

def coordinates2matrix(a, b, N):
    return a + (N+1)/2 - 1, b + (N+1)/2 - 1

def readFaceVertex(faceDescription):

    aux = faceDescription.split('/')

    assert len(aux[0]), "Vertex index has not been defined."

    faceVertex = [int(aux[0]), None, None]

    assert len(aux) == 3, "Only faces where its vertices require 3 indices are defined."

    if len(aux[1]) != 0:
        faceVertex[1] = int(aux[1])

    if len(aux[2]) != 0:
        faceVertex[2] = int(aux[2])

    return faceVertex

def readOBJ(filename, color):
    vertices = []
    normals = []
    textCoords= []
    faces = []

    with open(filename, 'r') as file:
        for line in file.readlines():
            aux = line.strip().split(' ')

            if aux[0] == 'v':
                vertices += [[float(coord) for coord in aux[1:]]]

            elif aux[0] == 'vn':
                normals += [[float(coord) for coord in aux[1:]]]

            elif aux[0] == 'vt':
                assert len(aux[1:]) == 2, "Texture coordinates with different than 2 dimensions are not supported"
                textCoords += [[float(coord) for coord in aux[1:]]]

            elif aux[0] == 'f':
                N = len(aux)
                faces += [[readFaceVertex(faceVertex) for faceVertex in aux[1:4]]]
                for i in range(3, N-1):
                    faces += [[readFaceVertex(faceVertex) for faceVertex in [aux[i], aux[i+1], aux[1]]]]

        vertexData = []
        indices = []
        index = 0

        # Per previous construction, each face is a triangle
        for face in faces:

            # Checking each of the triangle vertices
            for i in range(0,3):
                vertex = vertices[face[i][0]-1]
                normal = normals[face[i][2]-1]

                vertexData += [
                    vertex[0], vertex[1], vertex[2],
                    color[0], color[1], color[2],
                    normal[0], normal[1], normal[2]
                ]

            # Connecting the 3 vertices to create a triangle
            indices += [index, index + 1, index + 2]
            index += 3

        return bs.Shape(vertexData, indices)

# esta aplica una corrección de coordenadas que tiene que ver con cómo venían los modelos de la cabeza y comida
def readOBJ2(filename, color):
    vertices = []
    normals = []
    textCoords= []
    faces = []

    with open(filename, 'r') as file:
        for line in file.readlines():
            aux = line.strip().split(' ')

            if aux[0] == 'v':
                arr = [[float(coord) for coord in aux[1:]]]
                if filename == "cabeza.obj":
                    arr[0][1] -= 0.58
                elif filename == "champi.obj":
                    arr[0][1] -= 0.36
                else:
                    raise Exception("cuidado con los nombres de los archivos!")
                vertices += arr

            elif aux[0] == 'vn':
                normals += [[float(coord) for coord in aux[1:]]]

            elif aux[0] == 'vt':
                assert len(aux[1:]) == 2, "Texture coordinates with different than 2 dimensions are not supported"
                textCoords += [[float(coord) for coord in aux[1:]]]

            elif aux[0] == 'f':
                N = len(aux)
                faces += [[readFaceVertex(faceVertex) for faceVertex in aux[1:4]]]
                for i in range(3, N-1):
                    faces += [[readFaceVertex(faceVertex) for faceVertex in [aux[i], aux[i+1], aux[1]]]]

        vertexData = []
        indices = []
        index = 0

        # Per previous construction, each face is a triangle
        for face in faces:

            # Checking each of the triangle vertices
            for i in range(0,3):
                vertex = vertices[face[i][0]-1]
                normal = normals[face[i][2]-1]

                vertexData += [
                    vertex[0], vertex[1], vertex[2],
                    color[0], color[1], color[2],
                    normal[0], normal[1], normal[2]
                ]

            # Connecting the 3 vertices to create a triangle
            indices += [index, index + 1, index + 2]
            index += 3

        return bs.Shape(vertexData, indices)