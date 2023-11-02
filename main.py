import fitz
import pprint

doc = fitz.open("ESP8266EX.pdf") # open a document
#doc = fitz.open("2N3904_BJT.pdf")
page =doc[24]
xref=page.get_images(1)
print (xref)
pix = fitz.Pixmap(doc, 93)
pix.save("test1.png")
