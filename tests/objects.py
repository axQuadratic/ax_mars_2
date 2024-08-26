from enum import Enum

tile_size = 20
border_width = 1

class tile_colors(Enum):
    blue_tile = (0, 200, 200)
    red_tile = (200, 0, 0)
    green_tile = (0, 200, 0)
    yellow_tile = (200, 200, 0)
    white_tile = (255, 255, 255)
    black_tile = (5, 5, 5)

def pregenerate_tile(tile_size, border_width, fill_color, cross, selected):
    data = []
    
    for j in range(border_width):
        for i in range(tile_size):
            data.append((255, 0, 0) if selected else (0, 0, 0))

    for k in range(tile_size - border_width * 2):
        for i in range(border_width):
            data.append((255, 0, 0) if selected else (0, 0, 0))

        if cross:
            for j in range(int((tile_size - border_width * 2) / 2)):
                for i in range(j):
                    data.append((5, 5, 5))

                for i in range(border_width * 2):
                    data.append(tile_colors(fill_color).value)

                for i in range(tile_size - (border_width * 2 + j) * 2):
                    data.append((5, 5, 5))

                for i in range(border_width * 2):
                    data.append(tile_colors(fill_color).value)
                
                for i in range(j):
                    data.append((5, 5, 5))

            for j in range(int((tile_size - border_width * 2) / 2), 0, -1):
                for i in range(j):
                    data.append((5, 5, 5))

                for i in range(border_width * 2):
                    data.append(tile_colors(fill_color).value)

                for i in range(tile_size - (border_width * 2 + j) * 2):
                    data.append((5, 5, 5))

                for i in range(border_width * 2):
                    data.append(tile_colors(fill_color).value)
                
                for i in range(j):
                    data.append((255, 0, 0) if selected else (0, 0, 0))

        else:
            for i in range(tile_size - border_width * 2):
                data.append(tile_colors(fill_color).value)

        for i in range(border_width):
            data.append((255, 0, 0) if selected else (0, 0, 0))

    for j in range(border_width):
        for i in range(tile_size):
            data.append((255, 0, 0) if selected else (0, 0, 0))

    return data

tiles = {}
sel_tiles = {}

for color in tile_colors:
    tiles[tile_colors(color).name] = pregenerate_tile(tile_size, border_width, color, False, False)    
    tiles["cross_" + tile_colors(color).name] = pregenerate_tile(tile_size, border_width, color, True, False)
    sel_tiles[tile_colors(color).name] = pregenerate_tile(tile_size, border_width, color, False, True)    
    sel_tiles["cross_" + tile_colors(color).name] = pregenerate_tile(tile_size, border_width, color, True, True)
