//---------------------------------------------------------
// Legacy GPU_* helpers from libctru 1.1.0 (gpu-old.c), which
// were removed from libctru in 1.2.0. The 3DS GPU code was
// written against these, so they are kept here verbatim
// (apart from const-correctness) on top of the GPUCMD_*
// functions that current libctru still provides.
//---------------------------------------------------------

#ifndef _3DSGPULEGACY_H_
#define _3DSGPULEGACY_H_

#include <3ds.h>

#ifdef __cplusplus
extern "C" {
#endif

void GPU_Init(Handle *gsphandle);
void GPU_Reset(u32* gxbuf, u32* gpuBuf, u32 gpuBufSize);

void GPU_SetFloatUniform(GPU_SHADER_TYPE type, u32 startreg, u32* data, u32 numreg);

void GPU_SetViewport(u32* depthBuffer, u32* colorBuffer, u32 x, u32 y, u32 w, u32 h);
void GPU_SetScissorTest(GPU_SCISSORMODE mode, u32 left, u32 bottom, u32 right, u32 top);
void GPU_DepthMap(float zScale, float zOffset);
void GPU_SetAlphaTest(bool enable, GPU_TESTFUNC function, u8 ref);
void GPU_SetDepthTestAndWriteMask(bool enable, GPU_TESTFUNC function, GPU_WRITEMASK writemask);
void GPU_SetStencilTest(bool enable, GPU_TESTFUNC function, u8 ref, u8 input_mask, u8 write_mask);
void GPU_SetStencilOp(GPU_STENCILOP sfail, GPU_STENCILOP dfail, GPU_STENCILOP pass);
void GPU_SetFaceCulling(GPU_CULLMODE mode);
void GPU_SetAlphaBlending(GPU_BLENDEQUATION colorEquation, GPU_BLENDEQUATION alphaEquation,
	GPU_BLENDFACTOR colorSrc, GPU_BLENDFACTOR colorDst,
	GPU_BLENDFACTOR alphaSrc, GPU_BLENDFACTOR alphaDst);
void GPU_SetBlendingColor(u8 r, u8 g, u8 b, u8 a);

void GPU_SetAttributeBuffers(u8 totalAttributes, u32* baseAddress, u64 attributeFormats, u16 attributeMask, u64 attributePermutation, u8 numBuffers, u32 bufferOffsets[], u64 bufferPermutations[], u8 bufferNumAttributes[]);

void GPU_SetTextureEnable(GPU_TEXUNIT units);
void GPU_SetTexture(GPU_TEXUNIT unit, u32* data, u16 width, u16 height, u32 param, GPU_TEXCOLOR colorType);
void GPU_SetTextureBorderColor(GPU_TEXUNIT unit, u32 borderColor);
void GPU_SetTexEnv(u8 id, u16 rgbSources, u16 alphaSources, u16 rgbOperands, u16 alphaOperands, GPU_COMBINEFUNC rgbCombine, GPU_COMBINEFUNC alphaCombine, u32 constantColor);

void GPU_DrawArray(GPU_Primitive_t primitive, u32 first, u32 count);

void GPUCMD_Finalize(void);
void GPUCMD_FlushAndRun(void);

#ifdef __cplusplus
}
#endif

#endif
