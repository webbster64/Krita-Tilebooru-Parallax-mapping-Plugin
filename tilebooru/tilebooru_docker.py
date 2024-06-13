# Tilebooru Images is a Krita plugin to get CC0 images based on a search,
# straight from the Krita Interface. Useful for textures and concept art!
# Copyright (C) 2020  Pedro Reis.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from krita import *
from enum import Enum
from operator import itemgetter
import copy
import math
from PyQt5 import QtWidgets, QtCore, uic
from .tilebooru_modulo import (
    Tilebooru_Display,
    Tilebooru_Button,
)
import os.path
import sys

# Add the 'libs' folder to the Python path
plugin_dir = os.path.dirname(os.path.realpath(__file__))
libs_dir = os.path.join(plugin_dir, 'libs')
sys.path.append(libs_dir)
import tempfile
import requests

class TransparencyType(Enum):
    NONE = 0
    LAYER = 1
    BLEND = 2

class TilebooruDocker(DockWidget):
    def __init__(self):
        super().__init__()

        # Construct
        self.setupVariables()
        self.setupInterface()
        self.setupModules()
        self.setStyle()
        self.initialize()

    def setupVariables(self):
        self.mainWidget = QWidget(self)

        self.applicationName = "Tilebooru_Display"
        self.referencesSetting = "referencesDirectory"
        self.foundFavouritesSetting = "currentFavourites"

        # Tilebooru Images is a Krita plugin to get CC0 images based on a search,
        self.useHostedImagesSetting = "useHostedImages"
        self.useHostedImages = False
        self.full_image_urls = []  # Add this line to initialize full_image_urls

        self.currImageScale = 100
        # self.fitCanvasChecked = bool(Application.readSetting(self.applicationName, self.fitCanvasSetting, "True"))
        self.imagesButtons = []
        self.foundImages = []
        self.favouriteImages = []

        # maps path to image
        self.cachedImages = {}
        self.cachedSearchKeywords = {}
        # self.cachedDatePaths = []
        self.order = []
        # store order of push
        self.cachedPathImages = []
        self.maxCachedImages = 90
        self.maxCachedSearchKeyword = 2000
        self.maxNumPages = 9999

        self.currPage = 0
        self.directoryPath = Application.readSetting(self.applicationName, self.referencesSetting, "")
        favouriteImagesValues = Application.readSetting(self.applicationName, self.foundFavouritesSetting, "").split("'")
        
        for value in favouriteImagesValues:
            if value not in ["[", ", ", "]", "", "[]"]:
                self.favouriteImages.append(value)
        
        self.bg_alpha = "background-color: rgba(0, 0, 0, 50); "
        self.bg_hover = "background-color: rgba(0, 0, 0, 100); "

    def setupInterface(self):
        # Window
        self.setWindowTitle("Tilebooru Images")

        # Path Name
        self.directoryPlugin = os.path.dirname(os.path.realpath(__file__))

        # Tilebooru Docker
        self.mainWidget = QWidget(self)
        self.setWidget(self.mainWidget)

        # self.layout = uic.loadUi(os.path.join(self.directoryPlugin, 'tilebooru_docker.ui'), self.mainWidget)
        self.layout = uic.loadUi(self.directoryPlugin + '/tilebooru_docker.ui', self.mainWidget)

        

        self.layout.useHostedImagesCheckBox.stateChanged.connect(self.toggleHostedImages)

        self.layoutButtons = [
            self.layout.imagesButtons0,
            self.layout.imagesButtons1,
            self.layout.imagesButtons2,
            self.layout.imagesButtons3,
            self.layout.imagesButtons4,
            self.layout.imagesButtons5,
            self.layout.imagesButtons6,
            self.layout.imagesButtons7,
            self.layout.imagesButtons8,
        ]


        # Adjust Layouts
        self.layout.imageWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.layout.middleWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # setup connections for top elements
        self.layout.filterTextEdit.textChanged.connect(self.textFilterChanged)
        self.layout.changePathButton.clicked.connect(self.changePath)

        # setup connections for bottom elements
        self.layout.previousButton.clicked.connect(lambda: self.updateCurrentPage(-1))
        self.layout.nextButton.clicked.connect(lambda: self.updateCurrentPage(1))
        self.layout.refresh.clicked.connect(self.refresh_cache)

        self.layout.scaleSlider.valueChanged.connect(self.updateScale)
        self.layout.paginationSlider.setMinimum(0)
        self.layout.paginationSlider.valueChanged.connect(self.updatePage)


    def refresh_cache(self):
        self.favouriteImages = []
        self.foundImages = []
        self.cachedSearchKeywords = {}
        self.getImagesFromDirectory()

    def setupModules(self):
        # Display Single
        self.imageWidget = Tilebooru_Display(self.layout.imageWidget)
        self.imageWidget.SIGNAL_HOVER.connect(self.cursorHover)
        self.imageWidget.SIGNAL_CLOSE.connect(self.closePreview)

        # Display Grid
        self.imagesButtons = []
        for i, layoutButton in enumerate(self.layoutButtons):
            imageButton = Tilebooru_Button(layoutButton)
            imageButton.setNumber(i)
            imageButton.SIGNAL_HOVER.connect(self.cursorHover)
            imageButton.SIGNAL_LMB.connect(self.buttonClick)
            imageButton.SIGNAL_WUP.connect(lambda: self.updateCurrentPage(-1))
            imageButton.SIGNAL_WDN.connect(lambda: self.updateCurrentPage(1))
            imageButton.SIGNAL_PREVIEW.connect(self.openPreview)
            imageButton.SIGNAL_FAVOURITE.connect(self.pinToFavourites)
            imageButton.SIGNAL_UN_FAVOURITE.connect(self.unpinFromFavourites)
            imageButton.SIGNAL_OPEN_NEW.connect(self.openNewDocument)
            imageButton.SIGNAL_REFERENCE.connect(self.placeReference)
            imageButton.SIGNAL_ADD_WITH_TRANS_LAYER.connect(self.add_with_layer)
            imageButton.SIGNAL_ADD_WITH_ERASE_GROUP.connect(self.add_with_blend)
            imageButton.SIGNAL_MMD.connect(self.add_image_with_layer)
            imageButton.SIGNAL_CTRL_LEFT.connect(self.add_image_with_group)
            self.imagesButtons.append(imageButton)

    def setStyle(self):
        # Displays
        self.cursorHover(None)

    def initialize(self):
        # initialize based on what was setup
        if self.directoryPath:
            self.layout.changePathButton.setText("Change Tiles Folder")
            self.getImagesFromDirectory()
        # initial organization of images with favourites
        self.reorganizeImages()
        self.layout.scaleSliderLabel.setText("Tile Scale : 100%")

        self.updateImages()
        self.getImagesFromDirectory()

    def reorganizeImages(self):
        qDebug("Reorganizing images...")
        # organize images, taking into account favourites
        # and their respective order
        favouriteFoundImages = []
        for image in self.favouriteImages:
            if image in self.foundImages:
                self.foundImages.remove(image)
                favouriteFoundImages.append(image)

            qDebug(f"Favourite found images: {favouriteFoundImages}")
            qDebug(f"Remaining found images: {self.foundImages}")

    def textFilterChanged(self):
        if self.useHostedImages:
            # Skip filtering if "use Tilebooru Tiles" option is checked
            return

        search_text = self.layout.filterTextEdit.text().lower()
        search_words = search_text.split(" ")

        stringsInText = self.layout.filterTextEdit.text().lower().split(" ")

        QtCore.qDebug(f"Tilebooru stringsInText before filtering: {stringsInText}")

        if self.layout.filterTextEdit.text().lower() == "":
            self.foundImages = copy.deepcopy(self.allImages)
            self.reorganizeImages()
            self.updateImages()
            return

        newImages = []
        for word in stringsInText:
            for path in self.allImages:
                if word in path.replace(self.directoryPath, "").lower() and not path in newImages and word != "" and word != " ":
                    newImages.append(path)
                elif path in self.cachedSearchKeywords:
                    searchString = ",".join(self.cachedSearchKeywords[path]).lower()
                    if word in searchString and not path in newImages and word != "" and word != " ":
                        newImages.append(path)

        QtCore.qDebug(f"Tilebooru newImages after filtering: {newImages}")

        self.foundImages = newImages
        self.order = copy.deepcopy(self.foundImages)
        self.reorganizeImages()
        self.updateImages()
        
    def getImagesFromDirectory(self):
        self.currPage = 0
        newImages = []

        if self.useHostedImages:
            newImages = self.fetch_and_populate_images(self.layout.filterTextEdit.text())
        else:
            if self.directoryPath == "":
                self.foundImages = []
                self.favouriteImages = []
                self.updateImages()
                return

            it = QDirIterator(self.directoryPath, QDirIterator.Subdirectories)
            while it.hasNext():
                filePath = it.next()
                if filePath.lower().endswith(('.webp', '.png', '.jpg', '.jpeg')) and not filePath.endswith(('~')):
                    newImages.append(filePath)

        self.foundImages = copy.deepcopy(newImages)
        self.allImages = copy.deepcopy(newImages)
        self.reorganizeImages()
        self.updateImages()

    def updateCurrentPage(self, increment):
        if (self.currPage == 0 and increment == -1) or \
            ((self.currPage + 1) * len(self.imagesButtons) > len(self.foundImages) and increment == 1) or \
            len(self.foundImages) == 0:
            return
        
        self.currPage += increment
        maxNumPage = math.ceil(len(self.foundImages) / len(self.layoutButtons))
        self.currPage = max(0, min(self.currPage, maxNumPage - 1))
        self.updateImages()

    def updateScale(self, value):
        self.currImageScale = value
        self.layout.scaleSliderLabel.setText(f"Tile Scale : {self.currImageScale}%")

        # update layout buttons, needed when dragging
        self.imageWidget.setImageScale(self.currImageScale)

        # normal images
        for i in range(0, len(self.imagesButtons)):
            self.imagesButtons[i].setImageScale(self.currImageScale)

    def updatePage(self, value):
        maxNumPage = math.ceil(len(self.foundImages) / len(self.layoutButtons))
        self.currPage = max(0, min(value, maxNumPage - 1))
        self.updateImages()

    def cursorHover(self, SIGNAL_HOVER):
        qDebug("Cursor hover event detected.")
        # Display Image
        qDebug("Setting image widget style sheet to background alpha.")
        self.layout.imageWidget.setStyleSheet(self.bg_alpha)
        if SIGNAL_HOVER == "D":
            qDebug("Detected signal hover 'D'. Setting image widget style sheet to background hover.")
            self.layout.imageWidget.setStyleSheet(self.bg_hover)

        # normal images
        for i in range(0, len(self.layoutButtons)):
            qDebug(f"Setting layout button {i} style sheet to background alpha.")
            self.layoutButtons[i].setStyleSheet(self.bg_alpha)

            if SIGNAL_HOVER == str(i):
                self.layoutButtons[i].setStyleSheet(self.bg_hover)

    # checks if image is cached, and if it isn't, create it and cache it
    def getImage(self, path):
        if path in self.cachedPathImages:
            return self.cachedImages[path]

        # need to remove from cache
        if len(self.cachedImages) > self.maxCachedImages: 
            removedPath = self.cachedPathImages.pop()
            self.cachedImages.pop(removedPath)
            if removedPath in self.cachedSearchKeywords:
                self.cachedSearchKeywords.pop(removedPath)
            for i in self.cachedDatePaths[:]:
                if i['value'] == removedPath:
                    self.cachedDatePaths.remove(i)
                    break
        self.cachedPathImages = [path] + self.cachedPathImages
        self.cachedImages[path] = QImage(path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return self.cachedImages[path]

    # makes sure the first 9 found images exist
    def checkValidImages(self):
        found = 0
        for path in self.foundImages:
            if found == 9:
                return

            if self.checkPath(path):
                found = found + 1

    def updateImages(self):
        qDebug("Tilebooru Updating images...")

        self.checkValidImages()
        buttonsSize = len(self.imagesButtons)

        # don't try to access image that isn't there
        maxRange = min(len(self.foundImages) - self.currPage * buttonsSize, buttonsSize)

        qDebug(f"Tilebooru maxRange: {maxRange}")
        qDebug(f"Tilebooru self.foundImages: {self.foundImages}")

        for i in range(0, len(self.imagesButtons)):
            if i < maxRange:
                # image is within valid range, apply it
                path = self.foundImages[i + buttonsSize * self.currPage]
                qDebug(f"Tilebooru Setting image for index {i} to path: {path}")
                self.imagesButtons[i].setFavourite(path in self.favouriteImages)
                self.imagesButtons[i].setImage(path, self.getImage(path))
            else:
                # image is outside the range
                qDebug(f"Tilebooru Clearing image for index {i}")
                self.imagesButtons[i].setFavourite(False)
                self.imagesButtons[i].setImage("",None)

        qDebug("Tilebooru Images updated.")

        # update text for pagination
        maxNumPage = math.ceil(len(self.foundImages) / len(self.layoutButtons))
        currPage = self.currPage + 1

        if maxNumPage == 0:
            currPage = 0

        # normalize string length
        if currPage < 10:
            currPage = "   " + str(currPage)
        elif currPage < 100:
            currPage = "  " + str(currPage)
        elif currPage < 1000:
            currPage = " " + str(currPage)

        # currPage is the index, but we want to present it in a user friendly way,
        # so it starts at 1
        self.layout.paginationLabel.setText(f"Page: {currPage}/{str(maxNumPage)}")
        # correction since array begins at 0
        self.layout.paginationSlider.setRange(0, maxNumPage - 1)
        self.layout.paginationSlider.setSliderPosition(self.currPage)


    def add_image_with_layer(self,position):
        if position < len(self.foundImages) - len(self.imagesButtons) * self.currPage:
            self.addImageLayer(self.foundImages[position + len(self.imagesButtons) * self.currPage],TransparencyType.LAYER)

    def add_image_with_group(self,position):
        if position < len(self.foundImages) - len(self.imagesButtons) * self.currPage:
            self.addImageLayer(self.foundImages[position + len(self.imagesButtons) * self.currPage],TransparencyType.BLEND)
    def add_with_layer(self,photoPath):
        self.addImageLayer(photoPath,TransparencyType.LAYER)

    def add_with_blend(self,photoPath):
        self.addImageLayer(photoPath,TransparencyType.BLEND)

    def addImageLayer(self, photoPath):
        # file no longer exists, remove from all structures
        if not self.checkPath(photoPath):
            self.updateImages()
            return
            
        QtCore.qDebug(f"Adding image layer: {photoPath}")

        # Get the document:
        doc = Krita.instance().activeDocument()

        # Saving a non-existent document causes crashes, so let's check for that first.
        if doc is None:
            QtCore.qDebug("No active document found.")
            return 

        # Check if there is a valid Canvas to place the Image
        if self.canvas() is None or self.canvas().view() is None:
            QtCore.qDebug("No valid canvas found.")
            return 

        scale = self.currImageScale / 100
        image = QImage(photoPath)
        # scale image
        image = image.scaled(int(image.width() * scale), int(image.height() * scale), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # MimeData
        mimedata = QMimeData()
        url = QUrl().fromLocalFile(photoPath)
        mimedata.setUrls([url])
        mimedata.setImageData(image)

        # Set image in clipboard
        QApplication.clipboard().setImage(image)

        # Place Image and Refresh Canvas
        try:
            Krita.instance().action('edit_paste').trigger()
            Krita.instance().activeDocument().refreshProjection()
            QtCore.qDebug("Image layer added successfully.")
        except Exception as e:
            QtCore.qDebug(f"Error adding image layer: {e}")

    def checkPath(self, path):
        if not os.path.isfile(path):
            if path in self.foundImages:
                self.foundImages.remove(path)
            if path in self.allImages:
                self.allImages.remove(path)
            if path in self.favouriteImages:
                self.favouriteImages.remove(path)
            if path in self.cachedSearchKeywords:
                self.cachedSearchKeywords.remove(path)
            for i in self.cachedDatePaths[:]:
                if i['value'] == path:
                    self.cachedDatePaths.remove(i)
                    break
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Missing Image!")
            dlg.setText("This image you tried to open was not found. Removing from the list.")
            dlg.exec()

            return False

        return True

    def openNewDocument(self, path):
        if not self.checkPath(path):
            self.updateImages()
            return 

        document = Krita.instance().openDocument(path)
        Application.activeWindow().addView(document)

    def placeReference(self, path):
        if not self.checkPath(path):
            self.updateImages()
            return

        # MimeData
        mimedata = QMimeData()
        url = QUrl().fromLocalFile(path)
        mimedata.setUrls([url])
        image = QImage(path)
        mimedata.setImageData(image)

        QApplication.clipboard().setImage(image)
        Krita.instance().action('paste_as_reference').trigger()

    def openPreview(self, path):
        self.imageWidget.setImage(path, self.getImage(path))
        self.layout.imageWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.middleWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)

    def closePreview(self):
        self.layout.imageWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.layout.middleWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def pinToFavourites(self, path):
        self.currPage = 0
        self.favouriteImages = [path] + self.favouriteImages

        # save setting for next restart
        Application.writeSetting(self.applicationName, self.foundFavouritesSetting, str(self.favouriteImages))
        self.reorganizeImages()
        self.updateImages()

    def unpinFromFavourites(self, path):
        if path in self.favouriteImages:
            self.favouriteImages.remove(path)

        Application.writeSetting(self.applicationName, self.foundFavouritesSetting, str(self.favouriteImages))

        # resets order to the default, but checks if foundImages is only a subset
        # in case it is searching
        orderedImages = []
        for image in self.allImages:
            if image in self.foundImages:
                orderedImages.append(image)

        self.foundImages = orderedImages
        self.reorganizeImages()
        self.updateImages()

    def leaveEvent(self, event):
        self.layout.filterTextEdit.clearFocus()

    def canvasChanged(self, canvas):
        pass

    def buttonClick(self, position):
        if position < len(self.foundImages) - len(self.imagesButtons) * self.currPage:
            self.onImageSelected(position + len(self.imagesButtons) * self.currPage)


    def searchButtonClicked(self):
        search_text = self.layout.filterTextEdit.text()
        if self.useHostedImages:
            self.foundImages = self.fetch_and_populate_images(search_text)
        else:
            self.getImagesFromDirectory()
        self.reorganizeImages()
        self.updateImages()

    def checkPath(self, path):
        return os.path.exists(path)

    # Opens a window to choose the directory path
    def changePath(self):
        if self.useHostedImages:
            self.getImagesFromDirectory()
            return

        fileDialog = QFileDialog(QWidget(self))
        fileDialog.setFileMode(QFileDialog.DirectoryOnly)

        if self.directoryPath == "":
            path = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        else:
            path = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        
        title = "Change Directory for Images"
        dialogOptions = QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog
        new_path = fileDialog.getExistingDirectory(self.mainWidget, title, path, dialogOptions)
        if self.directoryPath != "" and new_path == "":
            return
        self.directoryPath = new_path
        Application.writeSetting(self.applicationName, self.referencesSetting, self.directoryPath)

        self.favouriteImages = []
        self.foundImages = []
        self.cachedSearchKeywords = {}
        self.cachedDatePaths = []
        Application.writeSetting(self.applicationName, self.foundFavouritesSetting, "")

        if self.directoryPath == "":
            self.layout.changePathButton.setText("Set Tiles Folder")
        else:
            self.layout.changePathButton.setText("Change Tiles Folder")

        self.getImagesFromDirectory()



    def fetch_images_from_tilebooru(self, search_query):
        url = "http://192.168.20.91:3000/posts.json"
        params = {
            "login": "test",
            "api_key": "fN9gp4Uvy6dfg4ZGdqbqBrBZ",
            "tags": search_query,
            "limit": 100,
        }
        QtCore.qDebug("Fetching images from Tilebooru...")
        response = requests.get(url, params=params)
        QtCore.qDebug("Tilebooru API request completed.")
        if response.status_code == 200:
            data = response.json()
            image_data = []
            for post in data:
                if "preview_file_url" in post and "file_url" in post:
                    image_data.append({
                        "preview_url": post["preview_file_url"],
                        "full_url": post["file_url"]
                    })
                else:
                    QtCore.qDebug(f"Missing 'preview_file_url' or 'file_url' in post: {post.keys()}")
            return image_data
        else:
            QtCore.qDebug(f"Error fetching images from Tilebooru: {response.status_code}")
            return []

    def toggleHostedImages(self, state):
        if state == Qt.Checked:
            self.useHostedImages = True
            Application.writeSetting(self.applicationName, self.useHostedImagesSetting, "true")
            self.layout.changePathButton.setText("Search")
            QtCore.qDebug("Switching to Hosted Images")
        else:
            self.useHostedImages = False
            Application.writeSetting(self.applicationName, self.useHostedImagesSetting, "false")
            self.layout.changePathButton.setText("Select References Folder")
            QtCore.qDebug("switching to Local Images")
        self.getImagesFromDirectory()


    def fetch_and_populate_images(self, search_query):
        image_data_list = self.fetch_images_from_tilebooru(search_query)
        preview_images = []
        self.full_image_urls = []

        for image_data in image_data_list:
            preview_url = image_data["preview_url"]
            full_url = image_data["full_url"]
            response = requests.get(preview_url)
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_file.write(response.content)
                temp_file.close()
                preview_images.append(temp_file.name)
                self.full_image_urls.append(full_url)
            else:
                QtCore.qDebug(f"Error fetching preview image from URL: {preview_url}")

        return preview_images


    def onImageSelected(self, index):
        if index >= 0 and index < len(self.full_image_urls):
            full_image_url = self.full_image_urls[index]
            QtCore.qDebug(f"Selected image index: {index}")
            QtCore.qDebug(f"Full image URL: {full_image_url}")
            response = requests.get(full_image_url)
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_file.write(response.content)
                temp_file.close()
                QtCore.qDebug(f"Full image saved to: {temp_file.name}")
                self.addImageLayer(temp_file.name)
            else:
                QtCore.qDebug(f"Error fetching full image from URL: {full_image_url}")
        elif index >= 0 and index < len(self.foundImages):
            selected_image = self.foundImages[index]
            QtCore.qDebug(f"Selected local image index: {index}")
            QtCore.qDebug(f"Selected local image path: {selected_image}")
            self.addImageLayer(selected_image)
        else:
            QtCore.qDebug(f"Invalid image index: {index}")

