// Majora's Mask: Recompiled - Korean translation mod
//
// How it works:
//  * Every time the game DMAs a message from message_data_static into the message buffer,
//    the translated (Korean) version of that message is copied over it.
//  * In the translated byte stream every Hangul syllable is a single placeholder byte (KR_PLACEHOLDER).
//    A side table maps each placeholder's buffer position to a glyph index in kr_glyphs.
//  * When the decoder loads the glyph for a placeholder (Font_LoadCharNES), the Hangul glyph
//    is written into the character buffer instead of the original font glyph.
//  * The placeholder's advance width is set to a fixed full-width value.

#include "modding.h"
#include "global.h"
#include "recomputils.h"
#include "kr_data.h"

extern f32 sNESFontWidths[160];

#define MSG_ROM_START 0x00AD1000
#define MSG_ROM_END 0x00B3A9F0
#define MSG_BUF_SIZE 1280

static void* sPendRam = NULL;
static u32 sPendVrom = 0;
static s32 sPending = false;

static u16 sKrMap[MSG_BUF_SIZE];
static void* sKrBuf = NULL;
static s32 sKrActive = false;

static void kr_copy(u8* dst, const u8* src, u32 len) {
    u32 i;
    for (i = 0; i < len; i++) {
        dst[i] = src[i];
    }
}

static const KrMsgEntry* kr_find(u32 off) {
    s32 lo = 0;
    s32 hi = KR_MSG_COUNT - 1;

    while (lo <= hi) {
        s32 mid = (lo + hi) / 2;
        u32 v = kr_msg_table[mid].orig_off;
        if (v == off) {
            return &kr_msg_table[mid];
        }
        if (v < off) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return NULL;
}

RECOMP_HOOK("DmaMgr_RequestSync") void kr_dma_pre(void* ram, uintptr_t vrom, size_t size) {
    if ((vrom >= MSG_ROM_START) && (vrom < MSG_ROM_END)) {
        sPending = true;
        sPendRam = ram;
        sPendVrom = vrom;
    } else {
        sPending = false;
        if (ram == sKrBuf) {
            // Something else (e.g. the credits text) was loaded into the message buffer.
            sKrActive = false;
        }
    }
}

RECOMP_HOOK_RETURN("DmaMgr_RequestSync") void kr_dma_post(void) {
    const KrMsgEntry* e;
    u32 i;

    if (!sPending) {
        return;
    }
    sPending = false;

    e = kr_find(sPendVrom - MSG_ROM_START);
    if (e == NULL) {
        if (sPendRam == sKrBuf) {
            sKrActive = false;
        }
        return;
    }

    kr_copy(sPendRam, &kr_msg_blob[e->data_off], e->len);

    for (i = 0; i < MSG_BUF_SIZE; i++) {
        sKrMap[i] = 0xFFFF;
    }
    for (i = 0; i < e->npos; i++) {
        const KrGlyphPos* p = &kr_glyph_pos[e->pos_off + i];
        if (p->pos < MSG_BUF_SIZE) {
            sKrMap[p->pos] = p->glyph;
        }
    }
    sKrBuf = sPendRam;
    sKrActive = true;
}

// Fixed advance for Hangul syllables.
RECOMP_HOOK("Message_DecodeNES") void kr_decode_pre(PlayState* play) {
    sNESFontWidths[KR_PLACEHOLDER - ' '] = KR_ADVANCE;
}

static PlayState* sFontPlay;
static s32 sFontOffset;
static u8 sFontCodePoint;

RECOMP_HOOK("Font_LoadCharNES") void kr_loadchar_pre(PlayState* play, u8 codePointIndex, s32 offset) {
    sFontPlay = play;
    sFontCodePoint = codePointIndex;
    sFontOffset = offset;
}

RECOMP_HOOK_RETURN("Font_LoadCharNES") void kr_loadchar_post(void) {
    MessageContext* msgCtx;
    Font* font;
    u16 pos;
    u16 glyph;

    if (!sKrActive || (sFontCodePoint != KR_PLACEHOLDER) || (sFontPlay == NULL)) {
        return;
    }

    msgCtx = &sFontPlay->msgCtx;
    font = &msgCtx->font;

    if ((void*)&font->msgBuf != sKrBuf) {
        return;
    }

    pos = msgCtx->msgBufPos;
    if (pos >= MSG_BUF_SIZE) {
        return;
    }
    if ((u8)font->msgBuf.schar[pos] != KR_PLACEHOLDER) {
        return;
    }

    glyph = sKrMap[pos];
    if ((glyph == 0xFFFF) || (glyph >= KR_GLYPH_COUNT)) {
        return;
    }

    kr_copy(&font->charBuf[font->unk_11D88][sFontOffset], kr_glyphs[glyph], FONT_CHAR_TEX_SIZE);
}
