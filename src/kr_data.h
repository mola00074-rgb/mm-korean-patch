#ifndef KR_DATA_H
#define KR_DATA_H
#include "PR/ultratypes.h"
#define KR_PLACEHOLDER 0x80
#define KR_ADVANCE 15.0f
#define KR_MSG_COUNT 4477
#define KR_GLYPH_COUNT 998
typedef struct { u32 orig_off; u32 data_off; u16 len; u16 npos; u32 pos_off; } KrMsgEntry;
typedef struct { u16 pos; u16 glyph; } KrGlyphPos;
extern const KrMsgEntry kr_msg_table[KR_MSG_COUNT];
extern const u8 kr_msg_blob[];
extern const KrGlyphPos kr_glyph_pos[];
extern const u8 kr_glyphs[KR_GLYPH_COUNT][128];
typedef struct { u16 start; u16 len; } KrInsWord;
extern const u16 kr_ins_glyphs[];
extern const KrInsWord kr_ins_words[];
#define KR_INS_ORDINAL 0
#define KR_INS_HOURS 1
#define KR_INS_RUPEES 2
#define KR_INS_MASK_RED 3
#define KR_INS_MASK_BLUE 4
#define KR_INS_MASK_YELLOW 5
#define KR_INS_MASK_GREEN 6
#define KR_INS_OWL_GREAT_BAY_COAST 7
#define KR_INS_OWL_ZORA_CAPE 8
#define KR_INS_OWL_SNOWHEAD 9
#define KR_INS_OWL_MOUNTAIN_VILLAGE 10
#define KR_INS_OWL_CLOCK_TOWN 11
#define KR_INS_OWL_MILK_ROAD 12
#define KR_INS_OWL_WOODFALL 13
#define KR_INS_OWL_SOUTHERN_SWAMP 14
#define KR_INS_OWL_IKANA_CANYON 15
#define KR_INS_OWL_STONE_TOWER 16
#define KR_INS_OWL_ENTRANCE 17
#endif
