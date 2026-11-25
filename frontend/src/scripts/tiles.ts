/**
 * Where map tiles come from: the tool's own server, which fetches them from OpenStreetMap and
 * keeps them, so the browser never connects to a third party.
 */
export const TILE_URL = '/tiles/{z}/{x}/{y}.png'

/** The attribution OpenStreetMap's tiles require. */
export const TILE_ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

/** The zoom levels the tile server serves. */
export const TILE_MIN_ZOOM = 10
export const TILE_MAX_ZOOM = 18

/** The box around Berlin the tile server serves, as south-west and north-east corners. */
export const TILE_BOUNDS: [[number, number], [number, number]] = [[52.25, 12.9], [52.8, 13.95]]

/** Map options that keep a map inside the tiles the server serves. */
export const MAP_LIMITS = {
    minZoom: TILE_MIN_ZOOM,
    maxZoom: TILE_MAX_ZOOM,
    maxBounds: TILE_BOUNDS,
    maxBoundsViscosity: 1,
}

/** Tile layer options matching the tiles the server serves. */
export const TILE_LAYER_OPTIONS = {
    minZoom: TILE_MIN_ZOOM,
    maxZoom: TILE_MAX_ZOOM,
    bounds: TILE_BOUNDS,
    attribution: TILE_ATTRIBUTION,
}
