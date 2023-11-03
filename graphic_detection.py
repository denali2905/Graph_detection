import cv2
import numpy as np
import fitz
import pprint

file_name="Digilent_Basys_3_Artix-7_FPGA_Board.pdf"
doc = fitz.open(file_name)

for page in doc:
    paths = page.get_drawings()
    if len(paths) < 30:
        print ("no diagrams")
    else:
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
        else:
            shape.commit()
            #doc = fitz.open("drawings-page-0.pdf")

            pix = outpdf[0].get_pixmap()
            pix.save("Drawing_Output.png")

            # Load image, grayscale, Otsu's threshold
            image = cv2.imread("Drawing_Output.png")
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
                if w/h > 3 or h/w>2:
                    cv2.drawContours(dilate, [c], -1, (0,0,0), -1)

            # Iterate through diagram contours and form single bounding box
            fboxes = []
            cnts,heir = cv2.findContours(dilate, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            height,width,chan=image.shape
            page_area=height*width
            for c in range(len(cnts)):
                #if heir[0][c][2]==-1:
                    x, y, w, h = cv2.boundingRect(cnts[c])
                    area=(w)*(h)
                    if heir[0][c][2]==-1 and 200<area<page_area*0.5: 
                            fboxes.append(fitz.Rect(x,y,x+w,y+h))
                    elif area<page_area*0.5:
                        fboxes.append(fitz.Rect(x,y,x+w,y+h))

                        

            for f in range (len(fboxes)):
                for f2 in range(f+1,len(fboxes)):
                    if fboxes[f] in (fboxes[f2]):
                        fboxes[f]=fitz.Rect()
                    elif fboxes[f2] in fboxes[f]:
                        fboxes[f2]=fitz.Rect()


            val= True 
            mt=0
            id=0
            tables = page.find_tables(vertical_strategy='text', horizontal_strategy='lines')
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
                        id+=1
                        pix.save("Page-%i Diagram-%i.png" %(page.number,id))


