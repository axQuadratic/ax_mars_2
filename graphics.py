# This library handles primarily the displaying of core data

from PIL import Image
import math
import options as o

tile_size = 20
border_width = 1
max_field_width = 100

tiles = {}

def main():
    for color in o.tile_colors:
        tiles[o.tile_colors(color).name] = pregenerate_tile(tile_size, border_width, color, False, False)    
        tiles["cross_" + o.tile_colors(color).name] = pregenerate_tile(tile_size, border_width, color, True, False)
        tiles["highlight_" + o.tile_colors(color).name] = pregenerate_tile(tile_size, border_width * 3, color, False, True)    
        tiles["highlight_cross_" + o.tile_colors(color).name] = pregenerate_tile(tile_size, border_width, color, True, True)
        

def pregenerate_tile(tile_size, border_width, fill_color, cross, highlight):
    data = []
    
    for j in range(border_width):
        for i in range(tile_size):
            data.append((0, 0, 0) if not highlight else (31, 83, 141)) # Highlighted tiles are given a thicker border in Tailwind Blue(TM)

    if cross:
        # This cross-drawing algorithm was developed by hand and is unbelievably janky
        for k in range(math.floor((tile_size - border_width * 2) / 2)):
            for i in range(border_width):
                data.append((0, 0, 0))

            for i in range(k if k < 8 else 7):
                data.append(o.tile_colors.black.value)

            for i in range(border_width * 2):
                data.append(o.tile_colors(fill_color).value)

            for i in range(tile_size - border_width * 2 - border_width * 4 - k * 2):
                data.append(o.tile_colors.black.value)

            for i in range(border_width * 2):
                data.append(o.tile_colors(fill_color).value)
            
            for i in range(k if k < 8 else 7):
                data.append(o.tile_colors.black.value)

            for i in range(border_width):
                data.append((0, 0, 0))
        
        for k in reversed(range(math.floor((tile_size - border_width * 2) / 2))):
            for i in range(border_width):
                data.append((0, 0, 0))

            for i in range(k if k < 8 else 7):
                data.append(o.tile_colors.black.value)

            for i in range(border_width * 2):
                data.append(o.tile_colors(fill_color).value)

            for i in range(tile_size - border_width * 2 - border_width * 4 - k * 2):
                data.append(o.tile_colors.black.value)

            for i in range(border_width * 2):
                data.append(o.tile_colors(fill_color).value)
            
            for i in range(k if k < 8 else 7):
                data.append(o.tile_colors.black.value)

            for i in range(border_width):
                data.append((0, 0, 0))

    else:
        for k in range(tile_size - border_width * 2):
            for i in range(border_width):
                data.append((0, 0, 0))

            for i in range(tile_size - border_width * 2):
                data.append(o.tile_colors(fill_color).value)

            for i in range(border_width):
                data.append((0, 0, 0))

    for j in range(border_width):
        for i in range(tile_size):
            data.append((0, 0, 0) if not highlight else (31, 83, 141))

    return data

# The main graphics handler
def create_image_from_state_data(state : list, prev_state : list, field_size : int, prev_image : Image):
    # In cases of very large cores, more tiles are fit into each row to prevent excessively large windows
    if field_size > 10000:
        a_max_field_width = math.ceil(math.sqrt(field_size))
    else:
        a_max_field_width = max_field_width

    row_count = math.ceil(field_size / a_max_field_width)
    if prev_image is None or prev_image.size != (a_max_field_width * tile_size, row_count * tile_size): # The previous image can only be used as a base if their dimensions match
        new_image = Image.new("RGB", (a_max_field_width * tile_size, row_count * tile_size))
    else:
        new_image = prev_image
    if state == []: return new_image # No core is initialized

    # Draw the image by placing pregenerated tiles as needed
    img_data = new_image.load()
    current_tile = 0
    for y in range(row_count):
        for x in range(a_max_field_width):
            # Determine the tile's colour
            if state[current_tile].read_marked:
                render_color = "white"
            else:
                render_color = state[current_tile].color
            if state[current_tile].highlighted:
                render_color = "highlight_" + render_color

            if prev_state == []:
                # If no core was previously loaded, each tile must obviously be created from scratch
                img_data = draw_tile(img_data, x * tile_size, y * tile_size, render_color)
            elif state[current_tile] != prev_state[current_tile]:
                # This step takes up quite a bit of CPU time, hence why it is skipped if the image would be unchanged
                img_data = draw_tile(img_data, x * tile_size, y * tile_size, render_color)

            current_tile += 1
            if current_tile >= field_size: break

        # Clever way to break out of nested loops all at once; see http://psung.blogspot.com/2007/12/for-else-in-python.html
        else: continue
        break

    return new_image

# Places pixel data created in pregenerate_tile on image data
def draw_tile(data, start_x, start_y, tile):
    for y in range(tile_size):
        for x in range(tile_size):
            data[start_x + x, start_y + y] = tiles[tile][tile_size * y + x]

    return data

main()