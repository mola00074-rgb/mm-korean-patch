#ifndef KR_UI_H
#define KR_UI_H
#include "PR/ultratypes.h"
typedef struct { u32 vrom; u32 offset; u32 size; u32 data; } KrUiPatch;
#define KR_UI_PATCH_COUNT 100
extern const KrUiPatch kr_ui_patches[KR_UI_PATCH_COUNT];
extern const u8 kr_ui_blob[];
extern const u8 kr_press_start_tex[];
#define KR_PRESS_START_W 128
#define KR_PRESS_START_H 16
#endif
