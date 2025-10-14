from Box2D import b2World, b2PolygonShape


def create_walls(
    world: b2World, wall_thickness: float, room_width: float, room_height: float
):

    left_wall = world.CreateStaticBody(
        position=(-room_width / 2 + wall_thickness / 2, 0),
        shapes=b2PolygonShape(box=(wall_thickness, room_height)),
    )
    right_wall = world.CreateStaticBody(
        position=(room_width / 2 - wall_thickness / 2, 0),
        shapes=b2PolygonShape(box=(wall_thickness, room_height)),
    )
    top_wall = world.CreateStaticBody(
        position=(0, room_height / 2 - wall_thickness / 2),
        shapes=b2PolygonShape(box=(room_width, wall_thickness)),
    )
    bottom_wall = world.CreateStaticBody(
        position=(0, -room_height / 2 + wall_thickness / 2),
        shapes=b2PolygonShape(box=(room_width, wall_thickness)),
    )

    left_wall.userData = "left_wall"
    right_wall.userData = "right_wall"
    top_wall.userData = "top_wall"
    bottom_wall.userData = "bottom_wall"
    return left_wall, right_wall, top_wall, bottom_wall


