# Krita Tilebooru Plugin

## Installation

To download this plugin, download a zip from the [releases](https://github.com/webbster64/Krita-Tilebooru-Parallax-mapping-Plugin/releases). After extracting, place the it's contents in the correct folder:

- **Linux**: Place the folder inside "~/.local/share/krita/pykrita". 
- **Windows**: Place the folder inside "C:\Users\username\AppData\Roaming\krita\pykrita".

All that's left is to activate the plugin inside Krita! To do this, start Krita, and on the top bar go to Settings > Configure Krita > Python Plugin Manager. On the list, if the plugin was placed correctly, there should be a new entry named `Tilebooru Images`. Check it, click `OK`, and restart Krita. There is now a new docker named "Tilebooru Images"! Place wherever you prefer. 

The plugin is now correctly installed! Click on "Set Tiles Folder", and set the folder that contains all your references. After that, you're good to go! The plugin will recursively look inside your folder, so all the photos, even those that are stored inside different folders will show up! To know more about how to use the plugin to it's full potential, read the next chapter.

## Using the Plugin (really well)

After setting the Tiles folder, you now have a list of 9 images in the docker. If your folder has more than 9 images in total, there are now multiple pages. There are different ways to scroll the list, such as:
- Clicking on the "next" and "previous" buttons on the bottom row of the docker;
- Scrolling the slider next to the pages indicator;
- Mouse Wheel Up and Down;
- Alt + Drag Left or Right, in case you're using a stylus. 

If the images in the folders are of large size, there may be some slowdown when scrolling quickly. However, the plugin is caching the previews, and stores up to 90 images, so you can scroll through them back more easily later. 

To add an image to the document, all you'll have to do is click on the image. That's it!, After adding, you'll notice that the image might be scaled. To reduce needing to always transform to the correct size, there are two elements to assist you:

To use the Tiles hosted with tags for filter tick the Use Tilebooru Tiles, tipe in the search bar the tags you want to use, and click on the "Search" button. That's it! The plugin will now list the tiles with that tag, to add the the tile to the map click on it and move and scale as needed.

- The "Tile Scale" slider controls how large the Tile will be when it's placed. If the scale is 50%, the Tile scale will be respect the original resolutions of the Tile. If it's 100%, it will add the image in full resolution, if it's 50% it will add the image at half the original resolution. 

Dragging the image presents the same behaviour as clicking, with the only difference being that the image will be added in the position you specify! It will always preserve aspect ratio, so there's no need to worry with distortion.

If you want to filter the Tiles, you can add words to the text prompt on top of the widget. This filter will work on the full path of the image, so if you have images with random names, but are inside a folder called "rocks", if you input "rocks", those images will still appear. There's also an extra feature, in which mulitple word search adds to the selection. For example, if you input "rocks marble", the images that contain either "rocks" or "marble" will appear!

I found that naming your tiles like this 

`size quantity name orentation type`

`medium bundle scroll vertical prop.png`

`medium single scroll vertical prop.png`

works the best for filtering 

## Context Menu

You can also have some extra features by right-clicking on an image. This will open up a small menu, with several options: 
- **Preview in Docker**: This will maximize the selected image on the docker, to do a quick preview. You can close the preview by left-clicking the preview;
- **Pin to Beginning / Unpin**: You can add "favourites" to an image, by pinning them to the beginning. This is useful if you have a select few images that you like to re-use, but are on different pages. This way you can have an easy way to access them, which will persist across restarts. It will only forget the favourite images if you decide to change the references folder. You can also unpin the images to send them to their original placement. A favourite will have a triangle in the top-left corner.
- **Open as New Document**: Opens the image as a new document, but keep in mind that this is the original image. If you save it, it will override the one you have on your references folder. 
- **Place as Reference**: You can add an image as reference, and place it wherever you want! If you want to remove a reference, you need to press the "Pushpin Icon" on your toolbox, and remove it using that tool.
