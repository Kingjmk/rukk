from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *
import pygame
import math
import socket
import struct

s = socket.socket()


def dist(a, b):
    return math.sqrt((a * a) + (b * b))


def get_y_rotation(x, y, z):
    radians = math.atan2(x, dist(y, z))
    return -math.degrees(radians)


def get_x_rotation(x, y, z):
    radians = math.atan2(y, dist(x, z))
    return math.degrees(radians)


def get_z_rotation(x, y, z):
    radians = math.atan2(z, dist(x, y))
    return math.degrees(radians)


def init_display(width=640, height=480):
    pygame.init()
    screen = pygame.display.set_mode((width, height), OPENGL | DOUBLEBUF)
    pygame.display.set_caption("Press Esc to quit")
    if height == 0:
        height = 1

    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.0 * width / height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)


def draw_text(position, text_string):
    font = pygame.font.SysFont("Courier", 18, True)
    text_surface = font.render(text_string, True, (255, 255, 255, 255), (0, 0, 0, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glRasterPos3d(*position)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)


def draw_frame(sensor_data):
    gx, gy, gz, ax, ay, az = sensor_data

    x_rotation = get_x_rotation(gx, gy, gz)
    y_rotation = get_y_rotation(gx, gy, gz)
    z_rotation = get_z_rotation(gx, gy, gz)

    global rquad
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glLoadIdentity()
    glTranslatef(0, 0.0, -7.0)

    osd_text = "pitch: " + str("{0:.2f}".format(y_rotation)) + ", roll: " + str("{0:.2f}".format(x_rotation))
    osd_text += ", yaw: " + str("{0:.2f}".format(az))

    draw_text((-2, -2, 2), osd_text)

    # the way I'm holding the IMU board, X and Y axis are switched
    # with respect to the OpenGL coordinate system
    glRotatef(z_rotation, 0.0, 1.0, 0.0)
    glRotatef(y_rotation, 1.0, 0.0, 0.0)  # Pitch, rotate around x-axis
    glRotatef(-1 * x_rotation, 0.0, 0.0, 1.0)  # Roll,  rotate around z-axis

    glBegin(GL_QUADS)
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(1.0, 0.2, -1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(1.0, 0.2, 1.0)

    glColor3f(1.0, 0.5, 0.0)
    glVertex3f(1.0, -0.2, 1.0)
    glVertex3f(-1.0, -0.2, 1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(1.0, -0.2, -1.0)

    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(1.0, 0.2, 1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(-1.0, -0.2, 1.0)
    glVertex3f(1.0, -0.2, 1.0)

    glColor3f(1.0, 1.0, 0.0)
    glVertex3f(1.0, -0.2, -1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(1.0, 0.2, -1.0)

    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(-1.0, 0.2, 1.0)
    glVertex3f(-1.0, 0.2, -1.0)
    glVertex3f(-1.0, -0.2, -1.0)
    glVertex3f(-1.0, -0.2, 1.0)

    glColor3f(1.0, 0.0, 1.0)
    glVertex3f(1.0, 0.2, -1.0)
    glVertex3f(1.0, 0.2, 1.0)
    glVertex3f(1.0, -0.2, 1.0)
    glVertex3f(1.0, -0.2, -1.0)
    glEnd()


def main():
    host = '192.168.1.19'  # ip of raspberry pi
    port = 12345
    s.connect((host, port))

    init_display()
    frames = 0
    ticks = pygame.time.get_ticks()

    while True:
        event = pygame.event.poll()
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            pygame.quit()  # * quit pygame properly
            break

        data = s.recv(48)
        if len(data) == 0:
            break
        try:
            sensor_data = struct.unpack('!dddddd', data)
        except Exception as e:
            print('---')
            break

        draw_frame(sensor_data)
        pygame.display.flip()
        frames = frames + 1

    print("fps:  %d" % ((frames*1000)/(pygame.time.get_ticks()-ticks)))
    s.close()


if __name__ == '__main__':
    main()
