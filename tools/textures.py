# Renders Korean replacements for texture-based text and writes src/kr_tex.c / kr_tex.h.
#  * item_name_static : pause-screen item names, IA4 128x16, indexed by ItemId
#  * map_name_static  : pause-screen map point names, IA4 128x16
#  * daytelop_static  : "Dawn of the First Day" screen, I4 128x64 (left/right halves) and I4 144x32
import os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, 'fonts', 'NanumGothic-ExtraBold.ttf')
OUT = os.path.join(HERE, '..', 'src')

ITEM_NAMES = {
    0: '시간의 오카리나', 1: '용사의 활', 2: '불꽃의 화살', 3: '얼음의 화살', 4: '빛의 화살',
    6: '폭탄', 7: '봄추', 8: '데쿠 막대', 9: '데쿠 열매', 10: '마법 콩',
    12: '화약통', 13: '사진기', 14: '진실의 렌즈', 15: '훅샷', 16: '대요정의 검',
    18: '빈 병', 19: '빨간 약', 20: '초록 약', 21: '파란 약', 22: '요정', 23: '데쿠 공주',
    24: '우유', 25: '우유 (1/2)', 26: '물고기', 27: '벌레', 28: '파란 불꽃', 29: '포우',
    30: '빅 포우', 31: '샘물', 32: '온천수', 33: '조라의 알', 34: '금가루', 35: '마법 버섯',
    36: '해마', 37: '샤토 로마니', 40: '달의 눈물', 41: '토지 증서', 42: '늪 증서',
    43: '산 증서', 44: '바다 증서', 45: '방 열쇠', 46: '엄마에게 보내는 속달',
    47: '카페이에게 보내는 편지', 48: '추억의 펜던트',
    50: '데쿠 가면', 51: '고론 가면', 52: '조라 가면', 53: '귀신 가면', 54: '진실의 가면',
    55: '카페이의 가면', 56: '철야 가면', 57: '토끼 두건', 58: '키톤 가면', 59: '가로 가면',
    60: '로마니의 가면', 61: '단장의 가면', 62: '우체부 모자', 63: '부부의 가면',
    64: '대요정의 가면', 65: '깁도 가면', 66: '돈 게로의 가면', 67: '카마로의 가면',
    68: '대장의 모자', 69: '돌 가면', 70: '브레멘 가면', 71: '폭탄 가면', 72: '냄새의 가면',
    73: '거인의 가면',
    77: '코키리의 검', 78: '면도날 검', 79: '금빛 검', 81: '용사의 방패', 82: '거울 방패',
    83: '화살통 (30개)', 84: '화살통 (40개)', 85: '화살통 (50개)',
    86: '폭탄 가방 (20개)', 87: '폭탄 가방 (30개)', 88: '폭탄 가방 (40개)',
    93: '오도르와의 유해', 94: '고트의 유해', 95: '교르그의 유해', 96: '트윈몰드의 유해',
    97: '눈뜸의 소나타', 98: '고론의 자장가', 99: '뉴웨이브 보사노바', 100: '공허의 엘레지',
    101: '질서의 맹세', 103: '시간의 노래', 104: '치유의 노래', 105: '에포나의 노래',
    106: '비상의 노래', 107: '폭풍의 노래', 109: '봄버즈 수첩', 111: '하트 조각',
    115: '자장가의 서곡', 116: '보스 열쇠', 117: '나침반', 118: '던전 지도', 119: '길 잃은 요정',
}
ITEM_COUNT = 120

MAP_NAMES = [
    '그레이트 베이', '조라 홀', '로마니 목장', '데쿠 궁전', '우드폴', '클락 타운', '스노헤드',
    '이카나 묘지', '이카나 계곡', '고론 마을', '스톤 타워', '그레이트 베이 해안', '남쪽 늪',
    '산골 마을', '밀크 로드', '조라 곶',
]

DAYS = ['첫째 날', '둘째 날', '마지막 날', '새로운 날']
DAY_SMALL = '새벽'
HOURS = ['- 남은 시간 72시간 -', '- 남은 시간 48시간 -', '- 남은 시간 24시간 -']

SS = 4


def text_mask(text, w, h, size, max_w, cy, squeeze_ok=True):
    """White-on-black coverage mask (float 0..1 list) of text centred at x, vertical centre cy."""
    f = ImageFont.truetype(FONT, int(size * SS))
    bb = f.getbbox(text)
    ref = f.getbbox('한')
    tw = bb[2] - bb[0]
    sx = 1.0
    if tw > max_w * SS:
        sx = (max_w * SS) / tw
    big = Image.new('L', (int(tw + 8 * SS), h * SS), 0)
    d = ImageDraw.Draw(big)
    gh = ref[3] - ref[1]
    d.text((4 * SS - bb[0], cy * SS - gh / 2 - ref[1]), text, font=f, fill=255)
    if sx < 1.0:
        big = big.resize((max(1, int(big.width * sx)), big.height), Image.LANCZOS)
    canvas = Image.new('L', (w * SS, h * SS), 0)
    canvas.paste(big, ((w * SS - big.width) // 2, 0))
    small = canvas.resize((w, h), Image.BOX)
    return [v / 255.0 for v in small.getdata()], sx


def fit_size(text, sizes, max_w):
    for s in sizes:
        f = ImageFont.truetype(FONT, int(s * SS))
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= max_w * SS:
            return s
    return sizes[-1]


def render_ia4(text, w=128, h=16):
    size = fit_size(text, [13, 12.5, 12, 11.5, 11], w - 6)
    t, sx = text_mask(text, w, h, size, w - 6, 7.6)
    out_px = []
    for y in range(h):
        for x in range(w):
            v = t[y * w + x]
            sh = 0.0
            for dx, dy in ((1, 1), (1, 0), (0, 1)):
                xx, yy = x - dx, y - dy
                if 0 <= xx < w and 0 <= yy < h:
                    sh = max(sh, t[yy * w + xx])
            if v > 0.12:
                i = min(7, max(1, round(v * 7 * 1.1)))
                out_px.append((i << 1) | 1)
            elif sh > 0.35:
                out_px.append(1)  # opaque black shadow
            else:
                out_px.append(0)
    data = bytearray()
    for k in range(0, len(out_px), 2):
        data.append((out_px[k] << 4) | out_px[k + 1])
    return bytes(data), out_px


def render_i4(lines, w, h):
    """lines: list of (text, size, cy). Returns I4 bytes and pixel list."""
    acc = [0.0] * (w * h)
    for text, size, cy in lines:
        t, _ = text_mask(text, w, h, size, w - 8, cy)
        acc = [max(a, b) for a, b in zip(acc, t)]
    px = [min(15, round(v * 15 * 1.05)) for v in acc]
    data = bytearray()
    for k in range(0, len(px), 2):
        data.append((px[k] << 4) | px[k + 1])
    return bytes(data), px


def day_textures(day):
    W, H = 256, 64
    data, px = render_i4([(DAY_SMALL, 19, 12), (day, 38, 42)], W, H)
    left = bytearray(); right = bytearray()
    for y in range(H):
        row = px[y * W:(y + 1) * W]
        for half, out in ((row[:128], left), (row[128:], right)):
            for k in range(0, 128, 2):
                out.append((half[k] << 4) | half[k + 1])
    return bytes(left), bytes(right), px


def c_array(f, name, blobs, size):
    f.write('__attribute__((aligned(8))) const u8 %s[%d][0x%X] = {\n' % (name, len(blobs), size))
    for b in blobs:
        assert len(b) == size, (name, len(b), size)
        f.write('    {')
        f.write(','.join('0x%02X' % x for x in b))
        f.write('},\n')
    f.write('};\n\n')


def preview(item_px, map_px, day_px, hours_px, path):
    sc = 2
    img = Image.new('RGB', (128 * 2 * sc + 20, 16 * 16 * sc + 300), (30, 30, 90))
    def put_ia4(px, ox, oy):
        for y in range(16):
            for x in range(128):
                v = px[y * 128 + x]
                if v & 1:
                    i = (v >> 1) * 255 // 7
                    for a in range(sc):
                        for b in range(sc):
                            img.putpixel((ox + x * sc + a, oy + y * sc + b), (i, i, i))
    keys = sorted(ITEM_NAMES)
    for n, k in enumerate([1, 13, 46, 47, 53, 61, 83, 86, 99, 100, 115, 119, 25, 0, 66, 104]):
        put_ia4(item_px[k], 0, n * 16 * sc)
    for n, p in enumerate(map_px):
        put_ia4(p, 128 * sc + 20, n * 16 * sc)
    oy = 16 * 16 * sc + 10
    d = Image.new('L', (256, 64)); d.putdata([v * 17 for v in day_px])
    img.paste(Image.merge('RGB', [d.resize((512, 128))] * 3), (0, oy))
    hh = Image.new('L', (144, 32)); hh.putdata([v * 17 for v in hours_px])
    img.paste(Image.merge('RGB', [hh.resize((288, 64))] * 3), (112, oy + 140))
    img.save(path)


def main():
    item_blobs = []; item_idx = [-1] * ITEM_COUNT; item_px = {}
    for k in sorted(ITEM_NAMES):
        b, px = render_ia4(ITEM_NAMES[k])
        item_idx[k] = len(item_blobs); item_blobs.append(b); item_px[k] = px
    map_blobs = []; map_px = []
    for n in MAP_NAMES:
        b, px = render_ia4(n); map_blobs.append(b); map_px.append(px)
    day_blobs = []; first_day_px = None
    for d in DAYS:
        l, r, px = day_textures(d)
        day_blobs += [l, r]
        if first_day_px is None:
            first_day_px = px
    hour_blobs = []; first_hours_px = None
    for t in HOURS:
        b, px = render_i4([(t, 17, 16)], 144, 32)
        hour_blobs.append(b)
        if first_hours_px is None:
            first_hours_px = px

    with open(os.path.join(OUT, 'kr_tex.h'), 'w') as f:
        f.write('#ifndef KR_TEX_H\n#define KR_TEX_H\n#include "PR/ultratypes.h"\n')
        f.write('#define KR_ITEM_NAME_COUNT %d\n#define KR_MAP_NAME_COUNT %d\n' % (ITEM_COUNT, len(MAP_NAMES)))
        f.write('extern const s16 kr_item_name_idx[KR_ITEM_NAME_COUNT];\n')
        f.write('extern const u8 kr_item_name_tex[%d][0x400];\n' % len(item_blobs))
        f.write('extern const u8 kr_map_name_tex[KR_MAP_NAME_COUNT][0x400];\n')
        f.write('extern const u8 kr_day_tex[8][0x1000];\n')
        f.write('extern const u8 kr_hours_tex[3][0x900];\n#endif\n')
    with open(os.path.join(OUT, 'kr_tex.c'), 'w') as f:
        f.write('// Generated by tools/textures.py\n#include "kr_tex.h"\n\n')
        f.write('const s16 kr_item_name_idx[KR_ITEM_NAME_COUNT] = {\n    ')
        f.write(', '.join(str(x) for x in item_idx))
        f.write('\n};\n\n')
        c_array(f, 'kr_item_name_tex', item_blobs, 0x400)
        c_array(f, 'kr_map_name_tex', map_blobs, 0x400)
        c_array(f, 'kr_day_tex', day_blobs, 0x1000)
        c_array(f, 'kr_hours_tex', hour_blobs, 0x900)
    preview(item_px, map_px, first_day_px, first_hours_px, os.path.join(HERE, '..', 'docs', 'textures_preview.png'))
    print('textures: %d item names, %d map names, %d day, %d hours' % (len(item_blobs), len(map_blobs), len(day_blobs), len(hour_blobs)))


if __name__ == '__main__':
    main()
