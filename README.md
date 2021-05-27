# Anamorphic Projection Addon for Blender


![Example of anamorphic projection effect on default cube](https://github.com/mcullan/blender-anamorphic-projection/raw/main/static/anamorphic-gif.gif)


## Requirements

* Blender 2.9 (Possibly)

## Installation

1. Clone this repository, or just download `anamorphic-projection-addon.py`
2. In Blender, open the Preferences menu and click the Addons tab. 
3. In the upper right corner of the pop up window, click the button that says "Install", which will bring up a file browser. Navigate to `anamorphic-projection-addon.py` and click ok.



## Quickstart

1. Install the addon as noted above.
2. Open a new .blend file and create a mesh object if the default cube isn't already there.
3. Create a copy of the default camera, and change its focal length to 25.
4. Ensure that you're in object mode. Select the default cube in the 3D view, then press `n` to pull up the tab menu if it isn't there already.
5. Select Anamorphic Projection.
6. Change "To:" to your new camera with the modified focal length.
7. Press "Modify Copy". You should now see a new, larger mesh that looks like the orignal cube. If you change the active camera to your new camera, you can see that it matches the original visual image of the starting cube. Try rotating this object, and you will see that it is no longer a cube, just a shape that was made to match the original view from "From Camera".



## Usage

1. For the addon menu to appear, you must be in 3D view and Object Mode, with a Mesh object currently set as the active object.
2. While in the 3D view, if it isn't already open, press `n` to open a tab menu on the right hand side of the view. There should be a tab at the bottom of this menu that says "Anamorphic Projection". If not, ensure that you have installed the addon (and saved your preferences!), and that you have a mesh object (e.g. a Cube) selected.
3. In the Anamorphic projection menu, select a "From Camera" and a "To Camera". Your "From Camera" must be in Perspective mode, currently.
4. If your "To Camera" is in Perspective mode, you can use the "X translate" and "Y translate" parameters, which move the projected object in screen space. Screen space is normalized to be bounded by (-1, 1) in the X and Y axes.
5. If your "To Camera" is in Orthographic mode, you can use the "Depth Multiplier" parameter. If this value is zero, the projection will be planar. As this value gets larger, the projected object gets more elongated in the view Z axis (distance from the camera).
6. Press "Modify Active" or "Modify Copy", depending if you want to keep the current object as it is.
7. By switching the active camera between "From Camera" and "To Camera", you can see that the projected object visually matches the original object, but their 3D shapes will be generally very different.

