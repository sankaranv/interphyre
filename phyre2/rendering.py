from phyre2.objects import Ball, Basket, Platform
import pygame
from Box2D import b2PolygonShape, b2CircleShape
import cv2
import numpy as np

system_colors = {
    "green": (32, 201, 162),
    "red": (235, 82, 52),
    "blue": (32, 93, 214),
    "black": (0, 0, 0),
    "gray": (200, 200, 200),
    "purple": (81, 56, 150),
}


def transform_vertices_for_render(position, frame_width, frame_height, ppm=60):
    x, y = position
    x = int(x * ppm + frame_width / 2)  # Adjust the scaling factor as needed
    y = int(-y * ppm + frame_height / 2)  # Adjust the scaling factor as needed
    return x, y


def render_wall(wall, screen, mode="pygame"):
    if mode == "pygame":
        screen_width, screen_height = screen.get_size()
    elif mode == "opencv":
        screen_width, screen_height = screen.shape[0], screen.shape[1]
    else:
        raise Exception(f"Render mode {mode} not recognized")
    for fixture in wall.fixtures:
        shape = fixture.shape
        if isinstance(shape, b2PolygonShape):
            vertices = [
                transform_vertices_for_render(
                    wall.transform * v, screen_width, screen_height
                )
                for v in shape.vertices
            ]
            if mode == "pygame":
                pygame.draw.polygon(screen, (255, 0, 0), vertices)
            elif mode == "opencv":
                cv2.fillPoly(screen, np.array([vertices]), (0, 0, 255))


def render_basket(basket_body, color, screen, mode="pygame"):
    if mode == "pygame":
        screen_width, screen_height = screen.get_size()
    elif mode == "opencv":
        screen_width, screen_height = screen.shape[0], screen.shape[1]
    else:
        raise Exception(f"Render mode {mode} not recognized")
    for fixture in basket_body.fixtures:
        shape = fixture.shape
        if isinstance(shape, b2PolygonShape):
            vertices = [
                transform_vertices_for_render(
                    basket_body.transform * v, screen_width, screen_height
                )
                for v in shape.vertices
            ]
            if mode == "pygame":
                pygame.draw.polygon(screen, color, vertices)
            elif mode == "opencv":
                bgr_color = (color[2], color[1], color[0])
                cv2.fillPoly(screen, np.array([vertices]), bgr_color)


def render_ball(ball, screen, ppm, color, mode="pygame"):
    if mode == "pygame":
        screen_width, screen_height = screen.get_size()
    elif mode == "opencv":
        screen_width, screen_height = screen.shape[0], screen.shape[1]
    else:
        raise Exception(f"Render mode {mode} not recognized")
    for fixture in ball.fixtures:
        shape = fixture.shape
        if isinstance(shape, b2CircleShape):
            position = transform_vertices_for_render(
                ball.transform * shape.pos, screen_width, screen_height
            )
            if mode == "pygame":
                pygame.draw.circle(screen, color, position, int(shape.radius * ppm))
            elif mode == "opencv":
                bgr_color = (color[2], color[1], color[0])
                cv2.circle(screen, position, int(shape.radius * ppm), bgr_color, -1)


def render_platform(platform, color, screen, mode="pygame"):
    if mode == "pygame":
        screen_width, screen_height = screen.get_size()
    elif mode == "opencv":
        screen_width, screen_height = screen.shape[0], screen.shape[1]
    else:
        raise Exception(f"Render mode {mode} not recognized")
    for fixture in platform.fixtures:
        shape = fixture.shape
        if isinstance(shape, b2PolygonShape):
            vertices = [
                transform_vertices_for_render(
                    platform.transform * v, screen_width, screen_height
                )
                for v in shape.vertices
            ]
            if mode == "pygame":
                pygame.draw.polygon(screen, color, vertices)
            elif mode == "opencv":
                bgr_color = (color[2], color[1], color[0])
                cv2.fillPoly(screen, np.array([vertices]), bgr_color)


def render_scene(world, level, screen, ppm):
    if isinstance(screen, pygame.Surface):
        mode = "pygame"
    elif isinstance(screen, np.ndarray):
        mode = "opencv"
    for body in world.bodies:
        body_name = body.userData
        if "wall" in body_name:
            render_wall(body, screen, mode)
        elif body_name in level.objects:
            color = system_colors[level.objects[body_name].color]
            if isinstance(level.objects[body_name], Basket):
                render_basket(body, color, screen, mode)
            elif isinstance(level.objects[body_name], Platform):
                render_platform(body, color, screen, mode)
            elif isinstance(level.objects[body_name], Ball):
                render_ball(body, screen, ppm, color, mode)
        else:
            raise Exception(
                f"Cannot render body {body.userData}, is of unrecognized type"
            )
