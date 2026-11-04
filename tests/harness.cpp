#include "blink_shim.h"
#include "../Kernels/OF_Flare.blink"
#include <string>
int main(int argc, char** argv) {
  const int W = 1280, H = 720;
  OF_Flare k;
  k.define();
#include "assign.inc"
  k.src.alloc(W, H); k.dst.alloc(W, H);
  for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
    k.dst.cx = x; k.dst.cy = y;
    int2 p; p.x = x; p.y = y;
    k.process(p);
  }
  FILE* f = fopen(argv[1], "wb");
  fwrite(&W, 4, 1, f); fwrite(&H, 4, 1, f);
  for (auto& c : k.dst.buf) { float v[3] = {c.x, c.y, c.z}; fwrite(v, 4, 3, f); }
  fclose(f);
  return 0;
}
