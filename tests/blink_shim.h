// Minimal C++ stand-in for the Blink language, ONLY to compile-check and
// numerically test OF_Flare.blink outside Nuke. Not part of the plugin.
#pragma once
#include <cmath>
#include <cstdio>
#include <vector>
#include <algorithm>

#define kernel struct
#define param public
#define local public

struct float2 { float x, y; float2(): x(0), y(0) {} float2(float a, float b): x(a), y(b) {} };
struct float3 { float x, y, z; float3(): x(0), y(0), z(0) {} float3(float a, float b, float c): x(a), y(b), z(c) {}
  float3& operator+=(const float3& o){ x+=o.x; y+=o.y; z+=o.z; return *this; } };
struct float4 { float x, y, z, w; float4(): x(0), y(0), z(0), w(0) {} float4(float a, float b, float c, float d): x(a), y(b), z(c), w(d) {} };
struct int2 { int x, y; };
inline float4 operator*(float4 a, float s){ return float4(a.x*s,a.y*s,a.z*s,a.w*s); }
inline float4 operator+(float4 a, float4 b){ return float4(a.x+b.x,a.y+b.y,a.z+b.z,a.w+b.w); }
inline float2 operator+(float2 a, float2 b){ return float2(a.x+b.x, a.y+b.y); }
inline float2 operator-(float2 a, float2 b){ return float2(a.x-b.x, a.y-b.y); }
inline float2 operator*(float2 a, float s){ return float2(a.x*s, a.y*s); }
inline float3 operator*(float3 a, float s){ return float3(a.x*s, a.y*s, a.z*s); }
inline float3 operator+(float3 a, float3 b){ return float3(a.x+b.x, a.y+b.y, a.z+b.z); }
template <class T> inline T min(T a, T b){ return a < b ? a : b; }
template <class T> inline T max(T a, T b){ return a > b ? a : b; }

struct Rect { int x1, y1, x2, y2; };
enum { ePixelWise, eRead, eWrite, eAccessRandom, eAccessPoint, eEdgeClamped };
template <int M> struct ImageComputationKernel {};

template <int RW, int ACC, int EDGE = 0>
struct Image {
  Rect bounds = {0, 0, 0, 0}; int w = 0, h = 0; std::vector<float4> buf; int cx = 0, cy = 0;
  void alloc(int W, int H){ w = W; h = H; bounds = {0, 0, W, H}; buf.assign(W*H, float4()); }
  float4 operator()(int x, int y) const { x = std::min(std::max(x,0),w-1); y = std::min(std::max(y,0),h-1); return buf[y*w+x]; }
  float4& operator()() { return buf[cy*w+cx]; }
};
template <class T> void defineParam(T& p, const char*, T def){ p = def; }
