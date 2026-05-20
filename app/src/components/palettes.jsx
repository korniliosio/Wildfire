import {
  interpolatePlasma,
  interpolateGreys,
  interpolateBrBG,
  interpolateViridis,
  interpolatePiYG,
  interpolatePuOr,
  interpolatePRGn,
  interpolatePuBuGn,
  interpolateInferno,
  interpolateBlues,
  interpolateRdPu,
  interpolateYlOrRd,
  interpolateGreens,
  interpolateOranges,
} from "d3-scale-chromatic";

export const paletteLookup = {
  Plasma: interpolatePlasma,
  Greys: interpolateGreys,
  BrBG: interpolateBrBG,
  Viridis: interpolateViridis,
  PiYG: interpolatePiYG,
  PuOr: interpolatePuOr,
  PRGn: interpolatePRGn,
  PuBuGn: interpolatePuBuGn,
  Inferno: interpolateInferno,
  Blues: interpolateBlues,
  RdPu: interpolateRdPu,
  YlOrRd: interpolateYlOrRd,
  Greens: interpolateGreens,
  Oranges: interpolateOranges,
};

export function getInterpolator(paletteName) {
  return paletteLookup[paletteName] || interpolateYlOrRd;
}