from phyre2.utils import b2_to_pygame, Ball, Basket, Platform
import pygame
from Box2D import b2PolygonShape, b2CircleShape


system_colors = {
    "green": (32, 201, 162),
    "red": (235, 82, 52),
    "blue": (32, 93, 214),
    "black": (0, 0, 0),
    "gray": (200, 200, 200),
    "purple": (81, 56, 150),
}


def render_wall(wall, screen):
    screen_width, screen_height = screen.get_size()
    for fixture in wall.fixtures:
        shape = fixture.shape
        if isinstance(shape, b2PolygonShape):
            vertices = [
                b2_to_pygame(wall.transform * v, screen_width, screen_height)
                for v in shape.vertices
            ]
            pygame.draw.polygon(screen, (255, 0, 0), vertices)


def render_basket(basket_body, color, screen):
    screen_width, screen_height = screen.get_size()
    for fixture in basket_body.fixtures:
        shape = fixture.shape
        if isinstance(shape, b2PolygonShape):
            vertices = [
                b2_to_pygame(basket_body.transform * v, screen_width, screen_height)
                for v in shape.vertices
            ]
            pygame.draw.polygon(screen, color, vertices)


def render_ball(ball, screen, ppm, color):
    screen_width, screen_height = screen.get_size()
    for fixture in ball.fixtures:
        shape = fixture.shape
        if isinstance(shape, b2CircleShape):
            position = b2_to_pygame(
                ball.transform * shape.pos, screen_width, screen_height
            )
            pygame.draw.circle(screen, color, position, int(shape.radius * ppm))


def render_platform(platform, color, screen):
    screen_width, screen_height = screen.get_size()
    for fixture in platform.fixtures:
        shape = fixture.shape
        if isinstance(shape, b2PolygonShape):
            vertices = [
                b2_to_pygame(platform.transform * v, screen_width, screen_height)
                for v in shape.vertices
            ]
            pygame.draw.polygon(screen, color, vertices)


def render_scene(world, level, screen, ppm):
    for body in world.bodies:
        body_name = body.userData
        if "wall" in body_name:
            render_wall(body, screen)
        elif body_name in level.objects:
            color = system_colors[level.objects[body_name].color]
            if isinstance(level.objects[body_name], Basket):
                render_basket(body, color, screen)
            elif isinstance(level.objects[body_name], Platform):
                render_platform(body, color, screen)
            elif isinstance(level.objects[body_name], Ball):
                render_ball(body, screen, ppm, color)
        else:
            raise Exception(
                f"Cannot render body {body.userData}, is of unrecognized type"
            )
