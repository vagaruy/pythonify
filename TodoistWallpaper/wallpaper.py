#!/usr/bin/env python3
import todoist as td
import subprocess
import os
import time
from uritools import urisplit
from gi.repository import Gdk
import argparse

curr_dir = os.path.dirname(os.path.realpath(__file__))

PROJECT = ""
WALLPAPER = ""
# --
text_color = "white"  # text color
size = "20"  # text size (real size depends on the scale factor of your wallpaper)
border = 120  # space around your text blocks
columns = 2  # (max) number of columns
n_lines = 40  # (max) number of lines per column
gravity = "NorthEast"


# --

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--project", required=True, help="Todoist Project to display", type=str)
    parser.add_argument("-w", "--wallpaper", required=True, help="Current Wallpaper", type=str)
    args = parser.parse_args()

    global PROJECT
    PROJECT = args.project
    global WALLPAPER
    WALLPAPER = args.wallpaper


def run_command(cmd):
    subprocess.call(["/bin/bash", "-c", cmd])


def get_value(cmd):
    return subprocess.check_output(["/bin/bash", "-c", cmd]).decode("utf-8").strip()


def read_text(file):
    with open(file) as src:
        return [l.strip() for l in src.readlines()]


def slice_lines(lines, n_lines, columns):
    markers = [i for i in range(len(lines)) if i % n_lines == 0]
    last = len(lines);
    markers = markers + [last] if markers[-1] != last else markers
    textblocks = [lines[markers[i]:markers[i + 1]] for i in range(len(markers) - 1)]
    filled_blocks = len(textblocks)
    if filled_blocks < columns:
        for n in range(columns - filled_blocks):
            textblocks.insert(len(textblocks), [])
    for i in range(columns):
        textblocks[i] = ("\n").join(textblocks[i])
    return textblocks[:columns]


def create_section(psize, text, layer):
    section_command = "convert -background none -fill " + text_color + " -border " + str(border) + \
                " -bordercolor none -pointsize " + size + " -size " + psize + \
                " caption:" + '"' + text + '" ' + layer
    print(section_command)
    run_command(section_command)


def combine_sections(layers):
    run_command("convert " + image_1 + " " + image_2 + " " + "+append " + span_image)
    pass


def set_overlay():
    boxes = slice_lines(getallitemsforproject(PROJECT), n_lines, columns)
    print(boxes)
    # curr_wall = getCurrentWallpaper()
    # dim = getCurrentScreenDimensions()
    # curr_wall = resizeImage(curr_wall, dim)
    resolution = get_value('identify -format "%wx%h" ' + WALLPAPER).split("x")
    w = str(int(int(resolution[0]) / columns) - 2 * border)
    h = str(int(resolution[1]) - 2 * border)
    layers = []
    for i in range(len(boxes)):
        layer = curr_dir + "/" + "layer_" + str(i + 1) + ".png"
        create_section(w + "x" + h, boxes[i], layer)
        layers.append(layer)
    wall_img = curr_dir + "/" + "walltext.jpg"

    layer_append_command = "convert " + (" ").join(layers) + " " + " -gravity " + gravity + " +append " + curr_dir + "/" + "layer_span.png"
    print(layer_append_command)
    run_command(layer_append_command)

    new_wallpaper_command = "convert " + " -gravity " + gravity + " " + WALLPAPER + " " + curr_dir + "/" + "layer_span.png" + " -background None -layers merge " + wall_img
    print(new_wallpaper_command)
    run_command(new_wallpaper_command)

    run_command("gsettings set org.gnome.desktop.background picture-uri file:///" + wall_img)
    for img in [img for img in os.listdir(curr_dir) if img.startswith("layer_")]:
        os.remove(curr_dir + "/" + img)


def getallitemsforproject(project_name):
    """Retrieve all completed and remaining tasks for a project"""
    api = td.TodoistAPI()
    user = api.user.login('vipul.agarwal89@gmail.com', 'nealcaffrey')
    print(user)
    response = api.sync()
    items = []
    project_id = -1
    if 'projects' in response:
        for project in response['projects']:
            if project['name'] == project_name:
                project_id = project['id']
                break


        if project_id != -1:
            for item in response['items']:
                if item['project_id'] == project_id:
                    items.append(item['content'])
        else:
            print("Project Name cannot be found in the account")
    else:
        print("Projects data not returned in the API call")
    return items


def getCurrentWallpaper():
    curr_wall = get_value("gsettings get org.gnome.desktop.background picture-uri")
    parts = urisplit(curr_wall)
    curr_wall = parts.getpath()
    curr_wall = curr_wall[:-1]
    print(curr_wall)
    return curr_wall


def getCurrentScreenDimensions():
    screen = Gdk.Screen.get_default()
    geo = screen.get_monitor_geometry(screen.get_primary_monitor())
    return {'width': geo.width, 'height': geo.height}


def resizeImage(image, dimensions):
    resized_image = image + "_resized";
    run_command("convert " + image + " -resize " + str(dimensions['width']) + "x" + str(
        dimensions['height']) + " " + resized_image)
    return resized_image

def readFromExistingFile():
    try:
        file = open("notes.txt")
        data = file.read()
        file.close()
    except Exception:
        data = ""
    return data

def writeDataToFile(data):
    print("Writing to file " , data)
    file = open("notes.txt")
    file.write(data)
    file.close()

parse_arguments()
set_overlay()
while True:
    try:
        # Grab and save data in current folder and then later try to match with it. More failsafe than other methods.
        text_1 = getallitemsforproject(PROJECT)
        time.sleep(60)
        text_2 = getallitemsforproject(PROJECT)
        if text_2 != text_1:
            print("setting overlay..")
            set_overlay()
            writeDataToFile(text_2)
    except Exception:
        pass
