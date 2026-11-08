from PIL import Image, ImageDraw, ImageFont
import os
FONT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'fonts','NanumGothic-ExtraBold.ttf')
SS=8
def render(ch, size=13.6, xoff=0.3, top=0.2, font=FONT):
    f=ImageFont.truetype(font, int(size*SS))
    im=Image.new('L',(16*SS,16*SS),0); d=ImageDraw.Draw(im)
    bb=f.getbbox('한')  # reference box for vertical alignment
    d.text((xoff*SS - 0, top*SS - bb[1]), ch, font=f, fill=255)
    im=im.resize((16,16),Image.LANCZOS)
    px=[min(15,round(v/255*15*1.15)) for v in im.getdata()]
    out=bytearray()
    for y in range(16):
        for x in range(0,16,2): out.append((px[y*16+x]<<4)|px[y*16+x+1])
    return bytes(out)
