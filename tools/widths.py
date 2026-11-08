import re
src=open(__import__('os').path.join(__import__('mmtext').DEC,'src/code/z_message_nes.c')).read()
arr=re.search(r'f32 sNESFontWidths\[160\] = \{(.*?)\};',src,re.S).group(1)
W=[float(x.strip().rstrip('f')) for x in arr.split(',') if x.strip()]
def charpx(code,scale=0.75):
    if code==0x20: return 6
    return int(W[code-0x20]*scale)
