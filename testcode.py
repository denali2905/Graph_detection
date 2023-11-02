import cv2
import numpy as np
import fitz
import pprint

doc = fitz.open("ESP8266EX.pdf") # open a document
#doc = fitz.open("Digilent_Basys_3_Artix-7_FPGA_Board.pdf") 
#doc = fitz.open("2N3904_BJT.pdf")
page =doc[24]
#page_area = page.bound().get_area()
paths = page.get_drawings()
if len(paths) < 30:
    print ("no diagrams")
    exit()
draws=0
#for page_index in range(len(doc)): # iterate over pdf pages
outpdf = fitz.open()
outpage = outpdf.new_page(width=page.rect.width, height=page.rect.height)
shape = outpage.new_shape()  # make a drawing canvas for the output page

# --------------------------------------
# loop through the paths and draw them
# --------------------------------------
for path in paths:
    # ------------------------------------
    # draw each entry of the 'items' list
    # ------------------------------------
    for item in path["items"]:  # these are the draw commands
        if item[0] == "l":  # line
            shape.draw_line(item[1], item[2])
        elif item[0] == "re":  # rectangle
            draws+=1
            shape.draw_rect(item[1])
        elif item[0] == "qu":  # quad
            draws+=1
            shape.draw_quad(item[1])
        elif item[0] == "c":  # curve
            draws+=1
            shape.draw_bezier(item[1], item[2], item[3], item[4])
        else:
            raise ValueError("unhandled drawing", item)
    # ------------------------------------------------------
    # all items are drawn, now apply the common properties
    # to finish the path
    # ------------------------------------------------------
    
    shape.finish(
        fill=path["fill"],  # fill color
        color=path["color"],  # line color
        dashes=path["dashes"],  # line dashing
        even_odd=path.get("even_odd", True),  # control color of overlaps
        closePath=path["closePath"],  # whether to connect last and first point
        lineJoin=1,  # how line joins should look like
        lineCap=1,  # how line ends should look like
        width=path["width"],  # line width
        stroke_opacity=1,  # same value for both
        fill_opacity=1,  # opacity parameters
        )
# all paths processed - commit the shape to its page
if draws < 20:
    print ("no diagrams")
    exit()
shape.commit()
outpdf.save("drawings-page-0.pdf")
doc = fitz.open("drawings-page-0.pdf")
page2 =doc[0]
pix = page2.get_pixmap()
pix.save("test1.png")

# Load image, grayscale, Otsu's threshold
image = cv2.imread('test1.png')
original = image.copy()
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

# Dilate with horizontal kernel
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20,20))
dilate = cv2.dilate(thresh, kernel, iterations=1)

# Find contours and remove non-diagram contours
cnts = cv2.findContours(dilate, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if len(cnts) == 2 else cnts[1]
for c in cnts:
    x,y,w,h = cv2.boundingRect(c)
    area = cv2.contourArea(c)
    if w/h > 3:
        cv2.drawContours(dilate, [c], -1, (0,0,0), -1)

# Iterate through diagram contours and form single bounding box
boxes = []
fboxes = []
cnts,heir = cv2.findContours(dilate, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
height,width,chan=image.shape
page_area=height*width
for c in range(len(cnts)):
    #if heir[0][c][2]==-1:
        x, y, w, h = cv2.boundingRect(cnts[c])
        area = cv2.contourArea(cnts[c])
        rarea=(w)*(h)
        if heir[0][c][2]==-1 and 200<rarea<page_area*0.5: 
                fboxes.append(fitz.Rect(x,y,x+w,y+h))
                boxes.append([x,y, x+w,y+h])
        elif rarea<page_area*0.5:
            fboxes.append(fitz.Rect(x,y,x+w,y+h))
            #v=fboxes[c].get_area()

            

for f in range (len(fboxes)):
    for f2 in range(f+1,len(fboxes)):
        if fboxes[f] in (fboxes[f2]):
            #fboxes[f2]=fitz.Rect(min(fboxes[f2].x0,fboxes[f].x0),
            #                    min(fboxes[f2].y0,fboxes[f].y0),
            #                     max(fboxes[f2].x1,fboxes[f].x1),
            #                    max(fboxes[f2].y1,fboxes[f].y1),)
            fboxes[f]=fitz.Rect()
        elif fboxes[f2] in fboxes[f]:
            fboxes[f2]=fitz.Rect()

boxes = np.asarray(boxes)
#x = np.min(boxes[:,0])
#y = np.min(boxes[:,1])
#w = np.max(boxes[:,2]) - x
#h = np.max(boxes[:,3]) - y

# Extract ROI
#cv2.rectangle(image, (x,y), (x + w,y + h), (36,255,12), 3)
val= True 
mt=0
#doc = fitz.open("2N3904_BJT.pdf")
doc = fitz.open("ESP8266EX.pdf")
#doc = fitz.open("Digilent_Basys_3_Artix-7_FPGA_Board.pdf")
page =doc[24]
tables = page.find_tables(vertical_strategy='lines', horizontal_strategy='lines',min_words_vertical=10, text_tolerance=None,edge_min_length=10)
for b in fboxes:
    if not b.is_empty:
        clip=fitz.Rect(b[0]-30,b[1]-30,b[2]+30,b[3]+30)
        for t in tables:
            data=t.extract()
            for d in data:
                for e in d:
                    if e=='' or e==None:
                        mt+=1
            if mt/t.col_count/t.row_count<.5 and t.col_count>1 and t.row_count>1:
                if clip.intersects(t.bbox):
                    val=False
                    break
        if val:
            pix = page.get_pixmap(clip=clip)
            pix.save("test2.png")

    #ROI = original[b[0]:b[2],b[1]:b[3]]
    #if ROI.__array__:
        #cv2.imshow('ROI%i'%i, ROI)

cv2.imshow('image', image)
cv2.imshow('thresh', thresh)
cv2.imshow('dilate', dilate)
#cv2.imshow('ROI', ROI)
#clip=fitz.Rect(b[0]-30,b[1]-30,b[2]+30,b[3]+30)
 # open a document

#page =doc[10]
#pix = page.get_pixmap()
#pix.save("test2.png")
cv2.waitKey()