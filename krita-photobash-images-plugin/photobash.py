from krita import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import math

class PhotobashDocker(DockWidget):
    directoryPath = ""
    applicationName = "Photobash"
    referencesSetting = "referencesDirectory"
    
    foundImages = []
    
    filterTextEdit = None
    mainWidget = None
    imagesButtons = []

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photobash Images")

        # Read settings 
        self.directoryPath = Application.readSetting(self.applicationName, self.referencesSetting, "")

        self.setLayout()

    def canvasChanged(self, canvas):
        pass

    def setLayout(self):
        self.mainWidget = QWidget(self)
        self.setWidget(self.mainWidget)

        # Filtering text
        self.filterTextEdit = QLineEdit(self.mainWidget)
        self.filterTextEdit.setPlaceholderText("Filter image name...")
        self.filterTextEdit.textChanged.connect(self.updateFilters)

        changePathButton = QPushButton("Change Path", self.mainWidget)
        changePathButton.clicked.connect(self.changePath)

        mainLayout = QVBoxLayout()
        
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.filterTextEdit)
        topLayout.addWidget(changePathButton)

        imagesLayout = QVBoxLayout()

        
        for i in range(0,3):
            rowLayout = QHBoxLayout()
            
            for j in range(0,3):
                button = QToolButton(self.mainWidget)
                button.setMaximumHeight(3000)
                button.setMaximumWidth(3000)
                button.setMinimumHeight(self.mainWidget.height() / 3)
                button.setMinimumWidth(self.mainWidget.width() / 3)
                
                self.imagesButtons.append(button)
                
                rowLayout.addWidget(button)

            imagesLayout.addLayout(rowLayout)
        
        self.imagesButtons[0].clicked.connect(lambda: self.buttonClick(0))
        self.imagesButtons[1].clicked.connect(lambda: self.buttonClick(1))
        self.imagesButtons[2].clicked.connect(lambda: self.buttonClick(2))
        self.imagesButtons[3].clicked.connect(lambda: self.buttonClick(3))
        self.imagesButtons[4].clicked.connect(lambda: self.buttonClick(4))
        self.imagesButtons[5].clicked.connect(lambda: self.buttonClick(5))
        self.imagesButtons[6].clicked.connect(lambda: self.buttonClick(6))
        self.imagesButtons[7].clicked.connect(lambda: self.buttonClick(7))
        self.imagesButtons[8].clicked.connect(lambda: self.buttonClick(8))

        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(imagesLayout)

        self.mainWidget.setLayout(mainLayout)


    def updateFilters(self):
        self.foundImages = []

        if self.directoryPath != "":
            it = QDirIterator(self.directoryPath, QDirIterator.Subdirectories)

            while(it.hasNext()): 
                if self.filterTextEdit.text().lower() in it.filePath().lower() and (".png" in it.filePath() or ".jpg" in it.filePath() or ".jpeg" in it.filePath()):
                    #print(it.filePath())
                    self.foundImages.append(it.filePath())
                    
                it.next()
                
        self.updateImages()

    def buttonClick(self, position):
        if position < len(self.foundImages):
            self.addPhoto(self.foundImages[position])
        
    def updateImages(self):
        maxWidth = self.imagesButtons[0].width()
        maxHeight = self.imagesButtons[0].height()

        maxRange = min(len(self.foundImages), len(self.imagesButtons))
        for i in range(0, len(self.imagesButtons)):
            if i < maxRange:
                print(self.foundImages[i])
                pixmap = QPixmap(self.foundImages[i])
                icon = QIcon(pixmap)

                self.imagesButtons[i].setIcon(icon)
                self.imagesButtons[i].setIconSize(QSize(int(maxWidth), int(maxHeight)))
            else: 
                self.imagesButtons[i].setIconSize(QSize(0,0))

    def changePath(self):
        fileDialog = QFileDialog(QWidget(self));
        fileDialog.setFileMode(QFileDialog.DirectoryOnly);
        
        print(self.directoryPath)

        if self.directoryPath == "":
            self.directoryPath = fileDialog.getExistingDirectory()
            Application.writeSetting(self.applicationName, self.referencesSetting, self.directoryPath)
        else: 
            self.directoryPath = fileDialog.getExistingDirectory(self.mainWidget, "Change Directory for Images", self.directoryPath)
            Application.writeSetting(self.applicationName, self.referencesSetting, self.directoryPath)
                
    
    def addPhoto(self, photoPath):
        # Get the document:
        doc = Krita.instance().activeDocument()
        
        # Saving a non-existent document causes crashes, so lets check for that first.
        if doc is not None:
            root = doc.activeNode().parentNode();
            
            layerName = photoPath.split("/")[len(photoPath.split("/")) - 1]

            newLayer = doc.createNode(layerName, "paintLayer")
            newLayer2 = doc.createFileLayer(layerName, photoPath, "ImageToPPI")
            
            root.addChildNode(newLayer2, None)
            root.addChildNode(newLayer, None)

            activeNode = doc.activeNode();
            
            activeNode.mergeDown()

            Krita.instance().activeDocument().refreshProjection()
            

Krita.instance().addDockWidgetFactory(DockWidgetFactory("PhotobashDocker", DockWidgetFactoryBase.DockRight, PhotobashDocker))

