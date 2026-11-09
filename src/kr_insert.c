// Korean replacements for words the message decoder inserts from game code
// (they are not part of message_data_static, so the message swap in kr_patch.c cannot reach them):
//   * "Rupee(s)" after amounts         -> 루피
//   * ordinals "st/nd/rd/th"            -> 번째   (stray fairy / skulltula token count)
//   * " hour(s)"                        -> 시간   (hours until the moon falls)
//   * owl statue destination names      -> Korean place names
//   * Spider House mask code colours    -> 빨강/파랑/노랑/초록
//
// Hangul in the decoded buffer uses KR_PLACEHOLDER (full-width advance) and the glyph is written straight
// into the font character buffer. Letters that have no Korean counterpart are turned into KR_BLANK, a
// zero-width character with an empty glyph, so the character-buffer slots stay in step with the draw code.

#include "modding.h"
#include "global.h"
#include "message_data_fmt_nes.h"
#include "kr_data.h"

#define KR_BLANK 0x81

extern f32 sNESFontWidths[160];

static void kr_copy_glyph(Font* font, s32 offset, u16 glyph) {
    u8* dst = &font->charBuf[font->unk_11D88][offset];
    s32 i;

    if (glyph >= KR_GLYPH_COUNT) {
        for (i = 0; i < FONT_CHAR_TEX_SIZE; i++) {
            dst[i] = 0;
        }
        return;
    }
    for (i = 0; i < FONT_CHAR_TEX_SIZE; i++) {
        dst[i] = kr_glyphs[glyph][i];
    }
}

static u16 kr_ins_glyph(s32 word, s32 index) {
    return kr_ins_glyphs[kr_ins_words[word].start + index];
}

void kr_insert_set_widths(void) {
    sNESFontWidths[KR_PLACEHOLDER - ' '] = KR_ADVANCE;
    sNESFontWidths[KR_BLANK - ' '] = 0.0f;
}

// Writes a whole inserted word at decoded-buffer position *p (which is left on the last character written).
static void kr_write_word(PlayState* play, s32 word, s16* p, s32* o, f32* f) {
    MessageContext* msgCtx = &play->msgCtx;
    Font* font = &msgCtx->font;
    s32 i;
    s32 len = kr_ins_words[word].len;
    s16 pos = *p;
    s32 off = *o;
    f32 w = *f;

    for (i = 0; i < len; i++) {
        u16 g = kr_ins_glyph(word, i);

        if (g == 0xFFFF) {
            msgCtx->decodedBuffer.schar[pos] = ' ';
            w += 6.0f;
        } else {
            msgCtx->decodedBuffer.schar[pos] = KR_PLACEHOLDER;
            kr_copy_glyph(font, off, g);
            off += FONT_CHAR_TEX_SIZE;
            w += KR_ADVANCE * msgCtx->textCharScale;
        }
        pos++;
    }
    *p = pos - 1;
    *o = off;
    *f = w;
}

// "<amount> Rupees" (doggy race bet, held item price)
RECOMP_PATCH void Message_LoadPluralRupeesNES(PlayState* play, s16* decodedBufPos, s32* offset, f32* arg3) {
    kr_write_word(play, KR_INS_RUPEES, decodedBufPos, offset, arg3);
}

// "<amount> Rupee(s)" (bank deposit input)
RECOMP_PATCH void Message_LoadLocalizedRupeesNES(PlayState* play, s16* decodedBufPos, s32* offset, f32* arg3) {
    kr_write_word(play, KR_INS_RUPEES, decodedBufPos, offset, arg3);
}

// "<amount> Rupee/Rupees" (bank balance, amount selected)
RECOMP_PATCH void Message_LoadRupeesNES(PlayState* play, s16* decodedBufPos, s32* offset, f32* arg3, s16 singular) {
    kr_write_word(play, KR_INS_RUPEES, decodedBufPos, offset, arg3);
}

static const u8 sKrOwlWords[OWL_WARP_MAX] = {
    KR_INS_OWL_GREAT_BAY_COAST, KR_INS_OWL_ZORA_CAPE,   KR_INS_OWL_SNOWHEAD,       KR_INS_OWL_MOUNTAIN_VILLAGE,
    KR_INS_OWL_CLOCK_TOWN,      KR_INS_OWL_MILK_ROAD,   KR_INS_OWL_WOODFALL,       KR_INS_OWL_SOUTHERN_SWAMP,
    KR_INS_OWL_IKANA_CANYON,    KR_INS_OWL_STONE_TOWER, KR_INS_OWL_ENTRANCE,
};

RECOMP_PATCH void Message_LoadOwlWarpTextNES(PlayState* play, s32* offset, f32* arg2, s16* decodedBufPos) {
    s16 owlWarpId;

    if (Map_CurRoomHasMapI(play) || (play->sceneId == SCENE_SECOM)) {
        owlWarpId = OWL_WARP_ENTRANCE;
    } else {
        owlWarpId = play->pauseCtx.cursorPoint[PAUSE_WORLD_MAP];
    }
    if ((owlWarpId < 0) || (owlWarpId >= OWL_WARP_MAX)) {
        owlWarpId = OWL_WARP_ENTRANCE;
    }
    kr_write_word(play, sKrOwlWords[owlWarpId], decodedBufPos, offset, arg2);
}

// Message_LoadCharNES is used by the decoder to append single letters for ordinals, "hours" and the
// mask code colour names. The control code being decoded tells which word the letters belong to.
static PlayState* sLcPlay;
static s32 sLcOffset;
static s16 sLcPos;
static u8 sLcChar;
static s32 sLcCount;
static u16 sLcMsgPos = 0xFFFF;

void kr_insert_reset(void) {
    sLcMsgPos = 0xFFFF;
    sLcCount = 0;
}

RECOMP_HOOK("Message_LoadCharNES")
void kr_lc_pre(PlayState* play, u8 codePointIndex, s32* offset, f32* arg3, s16 decodedBufPos) {
    sLcPlay = play;
    sLcOffset = *offset;
    sLcPos = decodedBufPos;
    sLcChar = codePointIndex;
}

RECOMP_HOOK_RETURN("Message_LoadCharNES") void kr_lc_post(void) {
    MessageContext* msgCtx;
    Font* font;
    u8 code;
    s32 word;
    s32 k;
    u16 g;

    if (sLcPlay == NULL) {
        return;
    }
    // Digits and punctuation are left alone.
    if (!(((sLcChar >= 'a') && (sLcChar <= 'z')) || ((sLcChar >= 'A') && (sLcChar <= 'Z')))) {
        return;
    }

    msgCtx = &sLcPlay->msgCtx;
    font = &msgCtx->font;
    code = (u8)font->msgBuf.schar[msgCtx->msgBufPos];

    if ((code == MESSAGE_STRAY_FAIRIES) || (code == MESSAGE_TOKENS)) {
        word = KR_INS_ORDINAL;
    } else if (code == MESSAGE_HOURS_UNTIL_MOON_CRASH) {
        word = KR_INS_HOURS;
    } else if ((code >= MESSAGE_SPIDER_HOUSE_MASK_CODE_1) && (code <= MESSAGE_SPIDER_HOUSE_MASK_CODE_6)) {
        u8 color = gSaveContext.save.saveInfo.spiderHouseMaskOrder[code - MESSAGE_SPIDER_HOUSE_MASK_CODE_1];
        if (color > 3) {
            return;
        }
        word = KR_INS_MASK_RED + color;
    } else {
        return;
    }

    if (sLcMsgPos != msgCtx->msgBufPos) {
        sLcMsgPos = msgCtx->msgBufPos;
        sLcCount = 0;
    }
    k = sLcCount++;

    if (k < kr_ins_words[word].len) {
        g = kr_ins_glyph(word, k);
    } else {
        g = 0xFFFF;
    }
    if (g == 0xFFFF) {
        msgCtx->decodedBuffer.schar[sLcPos] = KR_BLANK;
        kr_copy_glyph(font, sLcOffset, 0xFFFF);
    } else {
        msgCtx->decodedBuffer.schar[sLcPos] = KR_PLACEHOLDER;
        kr_copy_glyph(font, sLcOffset, g);
    }
}
