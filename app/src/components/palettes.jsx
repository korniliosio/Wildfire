import {
  interpolateBlues,
  interpolateGreens,
  interpolateOranges,
  interpolatePurples,
  interpolateReds,
  interpolateGreys,
  interpolateBuGn,
  interpolateBuPu,
  interpolateOrRd,
  interpolatePuRd,
  interpolateYlOrRd,
  interpolateYlGn,
  interpolateYlGnBu,
} from "d3-scale-chromatic";

export const paletteLookup = {
  Greys: interpolateGreys,
  Blues: interpolateBlues,
  Greens: interpolateGreens,
  Oranges: interpolateOranges,
  Reds: interpolateReds,
  Purples: interpolatePurples,
  BuGn: interpolateBuGn,
  BuPu: interpolateBuPu,
  OrRd: interpolateOrRd,
  PuRd: interpolatePuRd,
  YlOrRd: interpolateYlOrRd,
  YlGn: interpolateYlGn,
  YlGnBu: interpolateYlGnBu,
};

export function getInterpolator(paletteName) {
  return paletteLookup[paletteName] || interpolateGreys;
}