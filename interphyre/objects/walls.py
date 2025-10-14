from Box2D import b2World, b2PolygonShape


def create_walls(
    world: b2World, wall_thickness: float, room_width: float, room_height: float
):
    """Create boundary walls for the physics simulation.
    
    Creates four static walls (left, right, top, bottom) that form the
    boundaries of the simulation area.
    
    Args:
        world (b2World): The Box2D physics world to create walls in
        wall_thickness (float): Thickness of the wall bodies
        room_width (float): Total width of the room
        room_height (float): Total height of the room
        
    Returns:
        tuple: (left_wall, right_wall, top_wall, bottom_wall) Box2D bodies
        
    Note:
        Walls are created as static bodies that cannot be moved by physics forces.
        Each wall has userData set to "left_wall", "right_wall", "top_wall", or "bottom_wall".
    """
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


