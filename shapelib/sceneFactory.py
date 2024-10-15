import xml.etree.cElementTree as ET
import random
import functional.FLfunctions as fl
import functional.decorators as dc
import functional.lambdas as la
import shapelib.animetionlib.move as mv
import shapelib.animetionlib.zoom as zm
import shapelib.shapes as sp

def scenes_processor(path:str) -> list[tuple[list, str, int]]:
    tree = ET.ElementTree(file=path)
    root = tree.getroot()
    xmlScenes = root.findall(path="scene")
    scenes = fl.map(genScene, xmlScenes)
    return scenes

def genScene(xmlScene:ET.Element) -> dict[str, any]:
    dic = {}
    xmlShapes = xmlScene.find("shapes")
    xmlTitle = xmlScene.find("title")
    xmlArrays = xmlScene.findall("array")

    dic["duration"] = int(xmlScene.findtext("duration", default=0))
    dic["inLoop"] = False
    dic["title"] = genTitle(xmlTitle)
    dic["arrays"] = genArrays(xmlArrays)

    shapeList = genShapes(xmlShapes, dic.copy())
    def takeLayer(pre:list[list], curr:sp.AbsShape, index):
        pre[curr.layer].append(curr)
        return pre
    layers = fl.reduce(takeLayer, shapeList, [[],[],[],[],[]])
    dic["layers"] = layers
    return dic

def genTitle(xmlTitle:ET.Element) -> dict[str, any]:
    title = {}
    title["name"] = xmlTitle.findtext("name", default="scene")
    title["color"] = xmlTitle.findtext("color", default="#FFFFFF")
    title["font-size"] = int(xmlTitle.findtext("font-size", default=32))
    return title

def genArrays(xmlArrays:list[ET.Element]) -> dict[str, list]:
    def inner(pre:dict, curr:ET.Element, index):
        name = curr.get("name")
        type = curr.get("type")
        def getText(valueXml:ET.Element):
            if type.lower() == "int":
                return int(valueXml.text)
            return valueXml.text
        values = fl.map(getText, curr.findall(path="value"))
        pre[name] = values
        return pre
    return fl.reduce(inner, xmlArrays, {})

# -------------------Shapes---------------------

def genShapes(shapes:ET.Element, sceneConfig={}) -> list[sp.AbsShape]:
    rdGenEllip = dc.globalConfigDecorater(genEllip, sceneConfig)
    rdGenRect = dc.globalConfigDecorater(genRect, sceneConfig)
    rdGenStar = dc.globalConfigDecorater(genStar, sceneConfig)
    rdGenLoop = dc.globalConfigDecorater(genLoopShapes, sceneConfig)

    ellipse = fl.map(rdGenEllip, shapes.findall(path="ellipse"))
    rects = fl.map(rdGenRect, shapes.findall(path="rect"))
    star = fl.map(rdGenStar, shapes.findall(path="star"))

    loopShapes = fl.concat(fl.map(rdGenLoop, shapes.findall(path="loop")))

    return rects + ellipse + star + loopShapes

def genLoopShapes(sceneConfig:dict, loopTag:ET.Element) -> list[sp.AbsShape]:
    contentTag = loopTag.find(path="loopContent")
    if contentTag == None: return []

    randomConfig = {}
    i = int(getTagAttr(loopTag, "i", default=0, sceneConfig=sceneConfig))
    step = int(getTagAttr(loopTag, "step", default=1, sceneConfig=sceneConfig))
    count = int(getTagAttr(loopTag, "count", default=-1, sceneConfig=sceneConfig))
    sceneConfig["inLoop"] = True

    shapes = []
    count = count * step + i
    while i <= count:
        randomConfig["i"] = i
        sceneConfig["loop"] = randomConfig
        
        shapes += genShapes(contentTag, sceneConfig)

        i+=step
    sceneConfig["inLoop"] = False

    return shapes

def genRect(sceneConfig, rectTag:ET.Element):
    x = int(getTagAttr(rectTag, "x", sceneConfig=sceneConfig, default=0))
    y = int(getTagAttr(rectTag, "y", sceneConfig=sceneConfig, default=0))
    w = int(getTagAttr(rectTag, "w", sceneConfig=sceneConfig, default=0))
    h = int(getTagAttr(rectTag, "h", sceneConfig=sceneConfig, default=0))
    color = getTagAttr(rectTag, "color", sceneConfig=sceneConfig, default="#FFFFFF")
    border = getTagAttr(rectTag, "border", sceneConfig=sceneConfig, default=None)
    layer = int(getTagAttr(rectTag, "layer", sceneConfig=sceneConfig, default=2))
    move = getMove(rectTag.find(path="move"))
    zoom = getZoom(rectTag.find(path="zoom"))

    rect = sp.Rect().setPosition(x, y).setSize(w, h).setColor(color).setLayer(layer).setBorder(border).setMove(move).setZoom(zoom)
    return rect

def genEllip(sceneConfig, ellipTag:ET.Element):
    x = int(getTagAttr(ellipTag, "x", sceneConfig=sceneConfig, default=0))
    y = int(getTagAttr(ellipTag, "y", sceneConfig=sceneConfig, default=0))
    w = int(getTagAttr(ellipTag, "w", sceneConfig=sceneConfig, default=0))
    h = int(getTagAttr(ellipTag, "h", sceneConfig=sceneConfig, default=0))
    layer = int(getTagAttr(ellipTag, "layer", sceneConfig=sceneConfig, default=2))
    color = getTagAttr(ellipTag, "color", sceneConfig=sceneConfig, default="#FFFFFF")
    border = getTagAttr(ellipTag, "border", sceneConfig=sceneConfig, default=None)
    move = getMove(ellipTag.find(path="move"))
    zoom = getZoom(ellipTag.find(path="zoom"))

    ellip = sp.Ellipse().setPosition(x, y).setSize(w, h).setColor(color).setLayer(layer).setBorder(border).setMove(move).setZoom(zoom)
    return ellip

def genStar(sceneConfig, starTag: ET.Element):
    x = int(getTagAttr(starTag, "x", sceneConfig=sceneConfig, default=0))
    y = int(getTagAttr(starTag, "y", sceneConfig=sceneConfig, default=0))
    w = float(getTagAttr(starTag, "w", sceneConfig=sceneConfig, default=0.5))
    c1 = getTagAttr(starTag, "c1", sceneConfig=sceneConfig, default="#0000aa")
    c2 = getTagAttr(starTag, "c2", sceneConfig=sceneConfig, default="#0000FF")
    layer = int(getTagAttr(starTag, "layer", sceneConfig=sceneConfig, default=2))
    border = getTagAttr(starTag, "border", sceneConfig=sceneConfig, default=None)
    move = getMove(starTag.find(path="move"))
    zoom = getZoom(starTag.find(path="zoom"))

    star = sp.Star().setPosition(x, y).setSize(w).setColor(c1, c2).setLayer(layer).setBorder(border).setMove(move).setZoom(zoom)
    return star

# -------------------- get ------------------------

def getTagAttr(tag:ET.Element, key, default=None, sceneConfig:dict={}):
    keyTag = tag.find(key)
    if keyTag == None: return default

    if keyTag.find(path="getI") != None:
        return sceneConfig["loop"]["i"]

    if keyTag.find(path="getArray") == None and keyTag.find(path="random") == None:
        text = tag.findtext(key, default=default)
        return text

    if keyTag.find(path="getArray") != None:
        getArray = keyTag.find("getArray") 
        arr = sceneConfig["arrays"][getArray.get("name")]
        index = int(getTagAttr(getArray, "index", default=0, sceneConfig=sceneConfig))
        return arr[index]
    
    if keyTag.find(path="random") != None:
        rd = keyTag.find("random")
        fr =  getTagAttr(rd, "from", default=0, sceneConfig=sceneConfig)
        to =  getTagAttr(rd, "to", default=0, sceneConfig=sceneConfig)

        if rd.get("type", default="int").lower() == "float":
            return random.uniform(float(fr), float(to))
        return random.randint(int(fr), int(to))
    
    return default

def getZoom(zoomTag:ET.Element):
    if zoomTag == None: return zm.defaultZoom
    name = zoomTag.text
    keys = fl.dict_map(la.intDict, zoomTag.attrib)
    return zm.zoom(name)(**keys)

def getMove(moveTag:ET.Element):
    if moveTag == None: return mv.defaultMove
    name = moveTag.text
    keys = fl.dict_map(la.intDict, moveTag.attrib)
    return mv.move(name)(**keys)