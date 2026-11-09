# Renders Korean replacements for interface textures (pause menu, HUD button labels, title/file select screens)
# and writes src/kr_ui.c: a table of (segment VROM, offset, size, data) patches applied after the segment is DMA'd.
#
# The original ROM data is needed (mm-decomp/extracted/n64-us/baserom) because some textures keep their
# background (pause page banners, file select buttons) and only the lettering is replaced.
import os, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import mmtext

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, 'fonts', 'NanumGothic-ExtraBold.ttf')
OUT = os.path.join(HERE, '..', 'src')
BASEROM = os.path.join(mmtext.DEC, 'extracted', 'n64-us', 'baserom')
XML = os.path.join(mmtext.DEC, 'assets', 'xml')

SEGMENTS = {
    # name: (vrom, xml)
    'icon_item_jpn_static': (0x00A13000, 'interface/icon_item_jpn_static.xml'),
    'do_action_static': (0x00AC0000, 'interface/do_action_static.xml'),
    'parameter_static': (0x01EBD000, 'interface/parameter_static.xml'),
    'title_static': (0x01E88000, 'misc/title_static.xml'),
    'week_static': (0x01EC9000, 'interface/week_static.xml'),
    'icon_item_gameover_static': (0x00A0F000, 'interface/icon_item_gameover_static.xml'),
}

# texture name -> (Korean text, style[, options])
#   style: 'shadow' white text + dark drop shadow, 'outline' white text + dark outline,
#          'plain' white text only (I formats), 'button' file select button, 'banner' pause page banner
TEXTS = {
    'icon_item_jpn_static': {
        'gPauseWoodfallTitleENGTex': ('우드폴 신전', 'shadow'),
        'gPauseSnowheadTitleENGTex': ('스노헤드 신전', 'shadow'),
        'gPauseGreatBayTitleENGTex': ('그레이트 베이 신전', 'shadow'),
        'gPauseStoneTowerTitleENGTex': ('스톤 타워 신전', 'shadow'),
        'gPauseToEquipENGTex': ('장비하기', 'shadow'),
        'gPauseToDecideENGTex': ('결정', 'shadow'),
        'gPauseToPlayMelodyENGTex': ('멜로디 연주', 'shadow'),
        'gPauseToSelectItemENGTex': ('아이템 선택으로', 'shadow'),
        'gPauseToMapENGTex': ('지도로', 'shadow'),
        'gPauseToQuestStatusENGTex': ('퀘스트 상태로', 'shadow'),
        'gPauseToMasksENGTex': ('가면으로', 'shadow'),
        'gPauseToViewNotebookENGTex': ('수첩 보기', 'shadow'),
    },
    'do_action_static': {
        'gDoActionAttackENGTex': ('공격', 'outline'), 'gDoActionCheckENGTex': ('보기', 'outline'),
        'gDoActionEnterENGTex': ('들어가기', 'outline'), 'gDoActionReturnENGTex': ('돌아가기', 'outline'),
        'gDoActionOpenENGTex': ('열기', 'outline'), 'gDoActionJumpENGTex': ('점프', 'outline'),
        'gDoActionDecideENGTex': ('결정', 'outline'), 'gDoActionDiveENGTex': ('잠수', 'outline'),
        'gDoActionFasterENGTex': ('빨리', 'outline'), 'gDoActionThrowENGTex': ('던지기', 'outline'),
        'gDoActionNaviENGTex': ('타틀', 'outline'), 'gDoActionClimbENGTex': ('오르기', 'outline'),
        'gDoActionDropENGTex': ('놓기', 'outline'), 'gDoActionDownENGTex': ('내리기', 'outline'),
        'gDoActionQuitENGTex': ('그만두기', 'outline'), 'gDoActionSpeakENGTex': ('말하기', 'outline'),
        'gDoActionNextENGTex': ('다음', 'outline'), 'gDoActionGrabENGTex': ('잡기', 'outline'),
        'gDoActionStopENGTex': ('멈추기', 'outline'), 'gDoActionPutAwayENGTex': ('넣기', 'outline'),
        'gDoActionReelENGTex': ('감기', 'outline'), 'gDoActionInfoENGTex': ('설명', 'outline'),
        'gDoActionWarpENGTex': ('워프', 'outline'), 'gDoActionSnapENGTex': ('촬영', 'outline'),
        'gDoActionExplodeENGTex': ('폭발', 'outline'), 'gDoActionDanceENGTex': ('춤추기', 'outline'),
        'gDoActionMarchENGTex': ('행진', 'outline'), 'gDoActionCurlENGTex': ('웅크리기', 'outline'),
        'gDoActionSurfaceENGTex': ('떠오르기', 'outline'), 'gDoActionSwimENGTex': ('수영', 'outline'),
        'gDoActionPunchENGTex': ('펀치', 'outline'), 'gDoActionPoundENGTex': ('내려찍기', 'outline'),
        'gDoActionHookENGTex': ('훅샷', 'outline'), 'gDoActionShootENGTex': ('쏘기', 'outline'),
    },
    'parameter_static': {
        'gTatlCUpENGTex': ('타틀', 'outline'),
    },
    'week_static': {
        'gClockDay1stTex': ('첫째 날', 'plain'),
        'gClockDay2ndTex': ('둘째 날', 'plain'),
        'gClockDayFinalTex': ('마지막 날', 'plain'),
    },
    'icon_item_gameover_static': {
        'gContinuePlayingNESTex': ('계속하시겠습니까?', 'shadow'),
    },
    'title_static': {
        'gFileSelNoFileToCopyENGTex': ('복사할 파일이 없습니다.', 'shadow'),
        'gFileSelNoFileToEraseENGTex': ('지울 파일이 없습니다.', 'shadow'),
        'gFileSelNoEmptyFileENGTex': ('빈 파일이 없습니다.', 'shadow'),
        'gFileSelFileEmptyENGTex': ('빈 파일입니다.', 'shadow'),
        'gFileSelFileInUseENGTex': ('사용 중인 파일입니다.', 'shadow'),
        'gFileSelCopyWhichFileENGTex': ('어느 파일을 복사할까요?', 'shadow'),
        'gFileSelCopyToWhichFileENGTex': ('어느 파일에 복사할까요?', 'shadow'),
        'gFileSelAreYouSureCopyENGTex': ('정말 복사할까요?', 'shadow'),
        'gFileSelFileCopiedENGTex': ('파일을 복사했습니다.', 'shadow'),
        'gFileSelPleaseSelectAFileENGTex': ('파일을 선택해 주세요.', 'shadow'),
        'gFileSelOpenThisFileENGTex': ('이 파일을 열까요?', 'shadow'),
        'gFileSelEraseWhichFileENGTex': ('어느 파일을 지울까요?', 'shadow'),
        'gFileSelAreYouSureEraseENGTex': ('정말 지울까요?', 'shadow'),
        'gFileSelFileErasedENGTex': ('파일을 지웠습니다.', 'shadow'),
        'gFileSelOptionsENGTex': ('옵션', 'shadow'),
        'gFileSelNameENGTex': ('이름?', 'shadow'),
        'gFileSelSurroundENGTex': ('서라운드', 'shadow'),
        'gFileSelHeadsetENGTex': ('헤드셋', 'shadow'),
        'gFileSelMonoENGTex': ('모노', 'shadow'),
        'gFileSelSoundENGTex': ('사운드', 'shadow'),
        'gFileSelStereoENGTex': ('스테레오', 'shadow'),
        'gFileSelTargetingENGTex': ('Z 주목', 'shadow'),
        'gFileSelSwitchENGTex': ('전환', 'shadow'),
        'gFileSelHoldENGTex': ('유지', 'shadow'),
        'gFileSelCheckBrightnessENGTex': ('밝기 확인', 'shadow'),
        'gFileSelDecideCancelENGTex': ('A-결정 · B-취소', 'shadow'),
        'gFileSelDecideSaveENGTex': ('A-결정 · B-저장', 'shadow'),
        'gFileSelPleaseWaitENGTex': ('잠시 기다려 주세요...', 'shadow'),
        'gFileSelCopyButtonENGTex': ('복사', 'button'),
        'gFileSelFile1ButtonENGTex': ('파일 1', 'button', {'right_keep': 12}),
        'gFileSelFile2ButtonENGTex': ('파일 2', 'button', {'right_keep': 12}),
        'gFileSelFile3ButtonENGTex': ('파일 3', 'button', {'right_keep': 12}),
        'gFileSelYesButtonENGTex': ('예', 'button'),
        'gFileSelEraseButtonENGTex': ('지우기', 'button'),
        'gFileSelENDButtonENGTex': ('끝', 'button'),
        'gFileSelOptionsButtonENGTex': ('옵션', 'button'),
        'gFileSelQuitButtonENGTex': ('나가기', 'button'),
        'gFileSelFirstDayENGTex': ('첫째 날', 'plain'),
        'gFileSelSecondDayENGTex': ('둘째 날', 'plain'),
        'gFileSelFinalDayENGTex': ('마지막 날', 'plain'),
        'gFileSelMASKSENGTex': ('가면', 'plain'),
    },
}

# Pause page banners: (Korean, [slice texture names left to right])
BANNERS = [
    ('아이템 선택', ['gPauseSelectItem00ENGTex', 'gPauseSelectItem10ENGTex', 'gPauseSelectItem20ENGTex']),
    ('지도', ['gPauseMap10ENGTex']),
    ('퀘스트 상태', ['gPauseQuestStatus00ENGTex', 'gPauseQuestStatus10ENGTex', 'gPauseQuestStatus20ENGTex']),
    ('가면', ['gPauseMasks10ENGTex']),
]

SS = 4
BPP = {'ia4': 4, 'i4': 4, 'ia8': 8, 'i8': 8, 'ia16': 16}


def tex_table(xml):
    t = open(os.path.join(XML, xml)).read()
    out = {}
    for m in re.finditer(r'Name="(\w+)"[^>]*?Format="(\w+)" Width="(\d+)" Height="(\d+)" Offset="(0x[0-9A-Fa-f]+)"', t):
        out[m.group(1)] = (m.group(2), int(m.group(3)), int(m.group(4)), int(m.group(5), 16))
    return out


def tex_size(fmt, w, h):
    return w * h * BPP[fmt] // 8


# ---- pixel codecs (lists of (intensity 0..255, alpha 0..255)) ----
def decode(buf, fmt, w, h):
    n = w * h
    px = []
    if fmt == 'ia8':
        px = [((b >> 4) * 17, (b & 15) * 17) for b in buf[:n]]
    elif fmt == 'ia16':
        px = [(buf[2 * i], buf[2 * i + 1]) for i in range(n)]
    elif fmt == 'i8':
        px = [(b, 255) for b in buf[:n]]
    elif fmt == 'i4':
        for b in buf[:n // 2]:
            px += [((b >> 4) * 17, 255), ((b & 15) * 17, 255)]
    elif fmt == 'ia4':
        for b in buf[:n // 2]:
            for v in (b >> 4, b & 15):
                px.append(((v >> 1) * 255 // 7, 255 if v & 1 else 0))
    return px


def encode(px, fmt):
    out = bytearray()
    q = lambda v, m: max(0, min(m, int(round(v * m / 255.0))))
    if fmt == 'ia8':
        for i, a in px:
            out.append((q(i, 15) << 4) | q(a, 15))
    elif fmt == 'ia16':
        for i, a in px:
            out += bytes((q(i, 255), q(a, 255)))
    elif fmt == 'i8':
        for i, a in px:
            out.append(q(i, 255))
    elif fmt == 'i4':
        for k in range(0, len(px), 2):
            out.append((q(px[k][0], 15) << 4) | q(px[k + 1][0], 15))
    elif fmt == 'ia4':
        vals = []
        for i, a in px:
            vals.append((q(i, 7) << 1) | (1 if a >= 128 else 0))
        for k in range(0, len(vals), 2):
            out.append((vals[k] << 4) | vals[k + 1])
    return bytes(out)


# ---- text rendering ----
def fit_font(text, max_w, max_h, start):
    s = start
    while s > 7:
        f = ImageFont.truetype(FONT, int(s * SS))
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= max_w * SS:
            return s, f
        s -= 0.5
    return s, ImageFont.truetype(FONT, int(s * SS))


def text_mask(text, w, h, size, align='center', margin=1, cy=None, maxw=None):
    """Returns coverage list (0..1) of text in a w x h box."""
    maxw = maxw or (w - 2 * margin)
    s, f = fit_font(text, maxw, h, size)
    bb = f.getbbox(text)
    ref = f.getbbox('한')
    tw = bb[2] - bb[0]
    sx = min(1.0, (maxw * SS) / tw) if tw else 1.0
    big = Image.new('L', (tw + 8 * SS, h * SS), 0)
    d = ImageDraw.Draw(big)
    gh = ref[3] - ref[1]
    if cy is None:
        cy = h / 2.0
    d.text((4 * SS - bb[0], cy * SS - gh / 2 - ref[1]), text, font=f, fill=255)
    if sx < 1.0:
        big = big.resize((max(1, int(big.width * sx)), big.height), Image.LANCZOS)
    canvas = Image.new('L', (w * SS, h * SS), 0)
    if align == 'left':
        x = margin * SS - 4 * SS
    elif align == 'right':
        x = w * SS - margin * SS - big.width + 4 * SS
    else:
        x = (w * SS - big.width) // 2
    canvas.paste(big, (x, 0))
    small = canvas.resize((w, h), Image.BOX)
    return [v / 255.0 for v in small.getdata()]


def shifted(m, w, h, dx, dy):
    out = [0.0] * (w * h)
    for y in range(h):
        for x in range(w):
            xx, yy = x - dx, y - dy
            if 0 <= xx < w and 0 <= yy < h:
                out[y * w + x] = m[yy * w + xx]
    return out


def dilate(m, w, h):
    out = list(m)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        s = shifted(m, w, h, dx, dy)
        out = [max(a, b) for a, b in zip(out, s)]
    return out


def detect_align(px, w, h):
    cols = [x for x in range(w) if any(px[y * w + x][1] > 100 and px[y * w + x][0] > 100 for y in range(h))]
    if not cols:
        return 'center'
    l, r = cols[0], w - 1 - cols[-1]
    if l <= 3 and r > 8:
        return 'left'
    if r <= 3 and l > 8:
        return 'right'
    return 'center'


def font_size_for(h, style):
    if h <= 12:
        return 10.5
    if style == 'outline':
        return 11.5
    if h >= 24:
        return min(15, h * 0.55)
    return 13


def render_simple(text, style, fmt, w, h, orig):
    align = detect_align(orig, w, h)
    if style == 'plain':
        lines = [text]
        size = font_size_for(h, style)
        m = text_mask(text, w, h, size, align='center', margin=1)
        return [(int(v * 255), 255) for v in m]
    size = font_size_for(h, style)
    margin = 2 if style == 'outline' else 1
    m = text_mask(text, w, h, size, align=align, margin=margin, cy=h / 2.0 - 0.5)
    if style == 'outline':
        sh = dilate(m, w, h)
    else:
        sh = [max(a, b) for a, b in zip(shifted(m, w, h, 1, 1), shifted(m, w, h, 1, 0))]
        sh = [max(a, b) for a, b in zip(sh, shifted(m, w, h, 0, 1))]
    px = []
    for t, s in zip(m, sh):
        a = max(t, min(1.0, s * 1.4) * 0.85)
        i = 255 * t / a if a > 0 else 0
        px.append((int(min(255, i)), int(a * 255)))
    return px


def render_button(text, w, h, orig, opts):
    px = list(orig)
    right_keep = opts.get('right_keep', 4)
    x0, x1 = 4, w - right_keep
    # interior is a horizontal gradient: every column is constant from row 2 to row 13
    for x in range(x0, x1):
        ref = orig[2 * w + x]
        for y in range(3, 13):
            px[y * w + x] = ref
    m = text_mask(text, x1 - x0, h, 11.5, align='center', margin=1, cy=7.5)
    full = [0.0] * (w * h)
    for y in range(h):
        for x in range(x1 - x0):
            full[y * w + x0 + x] = m[y * (x1 - x0) + x]
    ol = dilate(full, w, h)
    for k in range(w * h):
        i, a = px[k]
        if a == 0:
            continue
        o = min(1.0, ol[k] * 1.3)
        i = i * (1 - o) + 255 * o
        t = full[k]
        i = i * (1 - t) + 0 * t
        px[k] = (int(i), a)
    return px


def render_banner(text, slices, data, table):
    infos = [table[n] for n in slices]
    fmt, w, h = infos[0][0], infos[0][1], infos[0][2]
    W = w * len(slices)
    img = [None] * (W * h)
    for k, n in enumerate(slices):
        f, ww, hh, off = table[n]
        p = decode(data[off:off + tex_size(f, ww, hh)], f, ww, hh)
        for y in range(h):
            for x in range(w):
                img[y * W + k * w + x] = p[y * w + x]
    # The lettering sits in rows ~5..18 of the stone band. Columns with dark pixels there are text;
    # they are rebuilt by tiling clean stone columns from beside the text.
    R0, R1 = 4, 20
    def col_stats(x):
        v = [img[y * W + x] for y in range(R0, R1)]
        return min(i for i, a in v), sum(i for i, a in v) / len(v), min(a for i, a in v)
    stats = [col_stats(x) for x in range(W)]
    textcols = [x for x in range(W) if stats[x][2] > 200 and stats[x][0] < stats[x][1] * 0.5]
    if textcols:
        lo, hi = max(0, min(textcols) - 3), min(W - 1, max(textcols) + 3)
        clean = [x for x in range(W) if (x < lo - 1 or x > hi + 1) and stats[x][2] > 200
                 and stats[x][0] >= stats[x][1] * 0.6 and stats[x][1] < 250]
        left = [x for x in clean if x < lo] or [x for x in clean if x > hi]
        right = [x for x in clean if x > hi] or left
        ml = stats[left[-1]][1] if left else 180
        mr = stats[right[0]][1] if right else ml
        for x in range(max(0, lo), min(W, hi + 1)):
            if (x - lo) < (hi - x):
                src = left[-1 - ((x - lo) % len(left))]
            else:
                src = right[(hi - x) % len(right)]
            target = ml + (mr - ml) * (x - lo) / max(1, hi - lo)
            k = target / max(1.0, stats[src][1])
            for y in range(R0, R1):
                i, a = img[y * W + src]
                img[y * W + x] = (int(min(255, i * k)), a)
    m = text_mask(text, W, h, 13.5, align='center', margin=4, cy=11.0, maxw=min(W - 8, 150))
    for k in range(W * h):
        t = m[k]
        if t > 0:
            i, a = img[k]
            img[k] = (int(i * (1 - t) + 20 * t), a)
    out = []
    for k, n in enumerate(slices):
        f, ww, hh, off = table[n]
        p = [img[y * W + k * w + x] for y in range(h) for x in range(w)]
        out.append((n, off, encode(p, f), p))
    return out


def main():
    patches = []  # (segment, name, vrom, offset, bytes, preview px, fmt, w, h)
    for seg, (vrom, xml) in SEGMENTS.items():
        table = tex_table(xml)
        data = open(os.path.join(BASEROM, seg), 'rb').read()
        for name, spec in TEXTS.get(seg, {}).items():
            text, style = spec[0], spec[1]
            opts = spec[2] if len(spec) > 2 else {}
            fmt, w, h, off = table[name]
            orig = decode(data[off:off + tex_size(fmt, w, h)], fmt, w, h)
            if style == 'button':
                px = render_button(text, w, h, orig, opts)
            else:
                px = render_simple(text, style, fmt, w, h, orig)
            b = encode(px, fmt)
            assert len(b) == tex_size(fmt, w, h), name
            patches.append((seg, name, vrom, off, b, px, fmt, w, h))
        if seg == 'icon_item_jpn_static':
            for text, slices in BANNERS:
                for n, off, b, p in render_banner(text, slices, data, table):
                    fmt, w, h, _ = table[n]
                    patches.append((seg, n, vrom, off, b, p, fmt, w, h))

    blob = bytearray()
    entries = []
    for seg, name, vrom, off, b, px, fmt, w, h in patches:
        while len(blob) % 8:
            blob.append(0)
        entries.append((vrom, off, len(b), len(blob), name))
        blob += b

    with open(os.path.join(OUT, 'kr_ui.h'), 'w') as f:
        f.write('#ifndef KR_UI_H\n#define KR_UI_H\n#include "PR/ultratypes.h"\n')
        f.write('typedef struct { u32 vrom; u32 offset; u32 size; u32 data; } KrUiPatch;\n')
        f.write('#define KR_UI_PATCH_COUNT %d\n' % len(entries))
        f.write('extern const KrUiPatch kr_ui_patches[KR_UI_PATCH_COUNT];\n')
        f.write('extern const u8 kr_ui_blob[];\n')
        f.write('extern const u8 kr_press_start_tex[];\n')
        f.write('#define KR_PRESS_START_W 128\n#define KR_PRESS_START_H 16\n#endif\n')
    with open(os.path.join(OUT, 'kr_ui.c'), 'w') as f:
        f.write('// Generated by tools/ui_textures.py\n#include "kr_ui.h"\n\n')
        f.write('const KrUiPatch kr_ui_patches[KR_UI_PATCH_COUNT] = {\n')
        for e in entries:
            f.write('    { 0x%08X, 0x%X, 0x%X, 0x%X }, // %s\n' % e)
        f.write('};\n\n__attribute__((aligned(8))) const u8 kr_ui_blob[%d] = {\n' % len(blob))
        for i in range(0, len(blob), 32):
            f.write('    ' + ','.join('0x%02X' % x for x in blob[i:i + 32]) + ',\n')
        f.write('};\n\n')
        # Title screen "PRESS START" replacement (I4 128x16, drawn with the original colours)
        m = text_mask('START를 누르세요', 128, 16, 11.5, align='center', margin=1, cy=7.5)
        ps = encode([(int(v * 255), 255) for v in m], 'i4')
        f.write('__attribute__((aligned(8))) const u8 kr_press_start_tex[%d] = {\n' % len(ps))
        for i in range(0, len(ps), 32):
            f.write('    ' + ','.join('0x%02X' % x for x in ps[i:i + 32]) + ',\n')
        f.write('};\n')
        press_px = [(int(v * 255), 255) for v in m]

    # preview sheet
    sc = 2
    rows = patches + [('title', 'PRESS START', 0, 0, b'', press_px, 'i4', 128, 16)]
    H = sum(p[8] * sc + 6 for p in rows)
    sheet = Image.new('RGB', (2 * 160 * sc + 10, H // 2 + 40), (40, 40, 110))
    y = [0, 0]
    for k, (seg, name, vrom, off, b, px, fmt, w, h) in enumerate(rows):
        col = 0 if y[0] <= y[1] else 1
        im = Image.new('RGBA', (w, h))
        im.putdata([(i, i, i, a) for i, a in px])
        im = im.resize((w * sc, h * sc), Image.NEAREST)
        sheet.paste(im, (col * (160 * sc + 10), y[col]), im)
        y[col] += h * sc + 6
    sheet = sheet.crop((0, 0, sheet.width, max(y) + 4))
    sheet.save(os.path.join(HERE, '..', 'docs', 'ui_preview.png'))
    print('ui textures: %d patches, %d bytes' % (len(entries), len(blob)))


if __name__ == '__main__':
    main()
