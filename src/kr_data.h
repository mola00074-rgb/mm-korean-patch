#ifndef KR_DATA_H
#define KR_DATA_H
#include "PR/ultratypes.h"
#define KR_PLACEHOLDER 0x80
#define KR_ADVANCE 15.0f
#define KR_MSG_COUNT 4477
#define KR_GLYPH_COUNT 997
typedef struct { u32 orig_off; u32 data_off; u16 len; u16 npos; u32 pos_off; } KrMsgEntry;
typedef struct { u16 pos; u16 glyph; } KrGlyphPos;
extern const KrMsgEntry kr_msg_table[KR_MSG_COUNT];
extern const u8 kr_msg_blob[];
extern const KrGlyphPos kr_glyph_pos[];
extern const u8 kr_glyphs[KR_GLYPH_COUNT][128];
#endif
