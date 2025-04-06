from OpenGL.GL import *

class Uniform:
    def __init__(self, dataType, data):
        # int | bool | float | vec2 | vec3 | vec4
        self.dataType = dataType
        self.data = data

        # referencia para la ubicación de la variable
        self.variableRef = None

    # Obtener una referencia para la variable uniforme
    def locateVariable(self, programRef, variableName):
        # Con esto, obtengo la ubicación a la que enviar la información (?)
        self.variableRef = glGetUniformLocation(programRef, variableName)

    # Guardar la info en la variable uniforme
    def uploadData(self):
        if self.variableRef is None:  # Si no existe, no hagas nada
            return
        if self.dataType == "int":
            glUniform1i(self.variableRef, self.data)
        elif self.dataType == "bool":
            glUniform1i(self.variableRef, self.data)
        elif self.dataType == "float":
            glUniform1f(self.variableRef, self.data)
        elif self.dataType == "vec2":
            glUniform2f(self.variableRef, self.data[0], self.data[1])
        elif self.dataType == "vec3":
            glUniform3f(self.variableRef, self.data[0], self.data[1], self.data[2])
        elif self.dataType == "vec4":
            glUniform4f(self.variableRef, self.data[0], self.data[1], self.data[2], self.data[3])
        else:
            raise Exception("Tipo de Uniforme desconocida:" + self.dataType)