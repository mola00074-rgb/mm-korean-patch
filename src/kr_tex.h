#ifndef KR_TEX_H
#define KR_TEX_H
#include "PR/ultratypes.h"
#define KR_ITEM_NAME_COUNT 120
#define KR_MAP_NAME_COUNT 16
extern const s16 kr_item_name_idx[KR_ITEM_NAME_COUNT];
extern const u8 kr_item_name_tex[100][0x400];
extern const u8 kr_map_name_tex[KR_MAP_NAME_COUNT][0x400];
extern const u8 kr_day_tex[8][0x1000];
extern const u8 kr_hours_tex[3][0x900];
#endif
