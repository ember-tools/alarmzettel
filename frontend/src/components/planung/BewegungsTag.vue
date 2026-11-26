<script setup lang="ts">
import {computed, onBeforeUnmount, onMounted, ref, watch} from 'vue'
import * as echarts from 'echarts/core'
import {CustomChart} from 'echarts/charts'
import {DataZoomComponent, GridComponent, TooltipComponent} from 'echarts/components'
import {SVGRenderer} from 'echarts/renderers'
import {getIcon} from '@iconify/vue'
import {useDark} from '@vueuse/core'
import {t} from '../../i18n'
import type {Balken, Bewegungsbild, Linie} from '../../scripts/bewegungen'

echarts.use([CustomChart, DataZoomComponent, GridComponent, TooltipComponent, SVGRenderer])

/**
 * Ein Tag als Bild: die Bänder sind die Orte, die Zeit läuft nach rechts. Gezeichnet wird nur,
 * was `bewegungsbild` schon angeordnet hat – Reihen, Bänder und Fenster stehen fest, damit der
 * Bildschirm und das PDF dasselbe zeigen.
 */
const {bild} = defineProps<{ bild: Bewegungsbild }>()
const gewaehlt = defineModel<string | null>('gewaehlt', {default: null})

const REIHE = 30

/**
 * The symbols come from the same bundled icon set the interface uses. A bar and a line are two
 * different things, and that should be visible without inferring it from the shape.
 */
const SYMBOLS = {
  stay: 'i-lucide-map-pin',
  vehicle: 'i-lucide-truck',
  onFoot: 'i-lucide-footprints',
}

const dark = useDark()

interface Koordinatensystem {
    x: number
    y: number
    width: number
    height: number
}

/**
 * Die Mitte des Stücks, das von einer Fahrt im Fenster liegt. Beim Hineinzoomen liegt die Mitte
 * der ganzen Strecke oft weit außerhalb – das Zeichen wäre dann weg, obwohl die Linie zu sehen
 * ist. Liegt gar nichts im Fenster, gibt es auch kein Zeichen.
 */
function sichtbareMitte(von: [number, number], nach: [number, number],
                        feld: Koordinatensystem): [number, number] | null {
    const links = feld.x, rechts = feld.x + feld.width
    const [a, b] = von[0] <= nach[0] ? [von, nach] : [nach, von]
    const anfang = Math.max(a[0], links)
    const ende = Math.min(b[0], rechts)
    if (ende < anfang) return null
    const x = (anfang + ende) / 2
    const strecke = b[0] - a[0]
    const anteil = strecke === 0 ? 0.5 : (x - a[0]) / strecke
    return [x, a[1] + (b[1] - a[1]) * anteil]
}

/**
 * A symbol as an image in a square of the given size, drawn in the given colour. The position
 * lives in the element's own offset, so the symbols move along with the bars when zooming.
 */
function symbol(name: string, x: number, y: number, size: number, color: string, opacity: number) {
  const icon = getIcon(name.replace(/^i-lucide-/, 'lucide:'))
  const svg = icon
      ? `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${icon.left} ${icon.top} ${icon.width} ${icon.height}" color="${color}">${icon.body}</svg>`
      : '<svg xmlns="http://www.w3.org/2000/svg"/>'
  return {
    type: 'image' as const,
    x, y,
    style: {image: `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`, width: size, height: size, opacity},
  }
}
const behaelter = ref<HTMLElement>()
let diagramm: echarts.ECharts | undefined
let beobachter: ResizeObserver | undefined

/** Die Farben kommen aus dem Stylesheet, damit das Bild dem Thema folgt statt es zu raten. */
function farbe(name: string): string {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#888'
}

/** Auch die Legende folgt dem Thema – sie hängt am Wechsel, nicht am Zufall des Neuzeichnens. */
const legendenfarben = computed(() => {
    void dark.value
    return {stehend: farbe('--ui-text-muted'), signal: farbe('--ui-signal')}
})

/** Jede Reihe eines Bandes ist eine Spur der Kategorieachse; beschriftet wird die mittlere. */
function spuren(): { beschriftung: string[], anfang: Map<string, number> } {
    const beschriftung: string[] = []
    const anfang = new Map<string, number>()
    for (const band of bild.baender) {
        anfang.set(band.ortId, beschriftung.length)
        for (let reihe = 0; reihe < band.reihen; reihe++) {
            beschriftung.push(reihe === Math.floor((band.reihen - 1) / 2) ? band.name : '')
        }
    }
    return {beschriftung, anfang}
}

function zeitpunkt(minute: number): number {
    return Date.parse(`${bild.datum}T00:00:00`) + minute * 60000
}

function uhr(minute: number): string {
    const innerhalb = ((minute % 1440) + 1440) % 1440
    return `${String(Math.floor(innerhalb / 60)).padStart(2, '0')}:` +
        String(innerhalb % 60).padStart(2, '0')
}

function beschriften(eintrag: Balken | Linie): string {
    const dazu = eintrag.begleitung.filter(Boolean)
    return dazu.length ? `${eintrag.name} · ${dazu.join(', ')}` : eintrag.name
}

/** Material und Notiz stehen im Hinweis: auf dem Balken wäre dafür kein Platz. */
function beiwerk(eintrag: Balken | Linie): string {
    const teile = [eintrag.material.join(', '), eintrag.notiz].filter(Boolean)
    return teile.length ? `<br><span style="opacity:.7">${teile.join(' · ')}</span>` : ''
}

function blass(spurId: string): number {
    return gewaehlt.value === null || gewaehlt.value === spurId ? 1 : 0.18
}

/**
 * The chart's options. A stay stands quietly in ink and a drive runs in the signal colour, so the
 * two differ at first glance and not only by their shape. `weakFilter` keeps what reaches into the
 * window, so a bar that begins before it is cut at the edge instead of vanishing. A corner is round
 * where the stay really begins or ends and square where the window only cuts it off, which shows
 * that it goes on without adding anything to it.
 */
function optionen() {
    const {beschriftung, anfang} = spuren()
    const ink = farbe('--ui-text-highlighted')
    const muted = farbe('--ui-text-muted')
    const rule = farbe('--ui-border')
    const signal = farbe('--ui-signal')
    const stehend = farbe('--ui-text-muted')
    const spur = (ortId: string, reihe: number) => (anfang.get(ortId) ?? 0) + reihe

    return {
        animation: false,
        backgroundColor: 'transparent',
        grid: {left: 130, right: 24, top: 16, bottom: 54},
        tooltip: {
            confine: true,
            formatter: (stelle: {data: {hinweis: string}}) => stelle.data.hinweis,
        },
        xAxis: {
            type: 'time',
            min: zeitpunkt(bild.von), max: zeitpunkt(bild.bis),
            axisLine: {lineStyle: {color: rule}},
            axisLabel: {color: muted, hideOverlap: true},
            splitLine: {show: true, lineStyle: {color: rule, opacity: 0.5}},
        },
        yAxis: {
            type: 'category', data: beschriftung, inverse: true,
            axisTick: {show: false},
            axisLine: {show: false},
            splitLine: {show: false},
            axisLabel: {color: ink, fontWeight: 'bold', width: 120, overflow: 'truncate'},
        },
        dataZoom: [
            {type: 'inside', xAxisIndex: 0, filterMode: 'weakFilter'},
            {type: 'slider', xAxisIndex: 0, height: 20, bottom: 12, filterMode: 'weakFilter',
             borderColor: rule, fillerColor: `${signal}22`, handleStyle: {color: signal},
             textStyle: {color: muted}},
        ],
        series: [
            {
                type: 'custom', name: 'fahrten', clip: true,
                renderItem: (parameter: {coordSys: Koordinatensystem}, api: {
                    value: (stelle: number) => number
                    coord: (werte: number[]) => [number, number]
                }) => {
                    const von = api.coord([api.value(0), api.value(2)])
                    const nach = api.coord([api.value(1), api.value(3)])
                    const mitFahrzeug = api.value(4) === 1
                    const deckung = api.value(5)
                    const winkel = Math.atan2(nach[1] - von[1], nach[0] - von[0])
                    const spitze = 6
                    const mitte = sichtbareMitte(von, nach, parameter.coordSys)
                    return {
                        type: 'group',
                        children: [
                            {
                                type: 'line',
                                shape: {x1: von[0], y1: von[1], x2: nach[0], y2: nach[1]},
                                style: {
                                    stroke: signal, lineWidth: 2,
                                    lineDash: mitFahrzeug ? undefined : [5, 4],
                                    opacity: deckung,
                                },
                            },
                            {
                                type: 'polygon',
                                shape: {points: [
                                    [nach[0], nach[1]],
                                    [nach[0] - spitze * Math.cos(winkel - 0.4),
                                     nach[1] - spitze * Math.sin(winkel - 0.4)],
                                    [nach[0] - spitze * Math.cos(winkel + 0.4),
                                     nach[1] - spitze * Math.sin(winkel + 0.4)],
                                ]},
                                style: {fill: signal, opacity: deckung},
                            },
                            ...(mitte ? [symbol(mitFahrzeug ? SYMBOLS.vehicle : SYMBOLS.onFoot,
                                                mitte[0] - 6, mitte[1] - 12, 11, signal, deckung)] : []),
                        ],
                    }
                },
                encode: {x: [0, 1], y: [2, 3]},
                data: bild.linien.map(linie => ({
                    value: [
                        zeitpunkt(linie.von), zeitpunkt(linie.bis),
                        spur(linie.vonOrtId, linie.vonReihe), spur(linie.nachOrtId, linie.nachReihe),
                        linie.mittel === 'fahrzeug' ? 1 : 0, blass(linie.spurId),
                    ],
                    spurId: linie.spurId,
                    hinweis: `${beschriften(linie)}<br>${uhr(linie.von)}–${uhr(linie.bis)}` +
                        beiwerk(linie),
                })),
            },
            {
                type: 'custom', name: 'aufenthalte', clip: true,
                renderItem: (parameter: {coordSys: Koordinatensystem},
                             api: {
                                 value: (stelle: number) => number
                                 coord: (werte: number[]) => [number, number]
                                 size: (werte: number[]) => [number, number]
                             }) => {
                    const anfangs = api.coord([api.value(0), api.value(2)])
                    const endes = api.coord([api.value(1), api.value(2)])
                    const hoehe = Math.min(api.size([0, 1])[1] * 0.62, REIHE * 0.7)
                    const breite = Math.max(endes[0] - anfangs[0], 2)
                    const kasten = echarts.graphic.clipRectByRect(
                        {x: anfangs[0], y: anfangs[1] - hoehe / 2, width: breite, height: hoehe},
                        {x: parameter.coordSys.x, y: parameter.coordSys.y,
                         width: parameter.coordSys.width, height: parameter.coordSys.height})
                    if (!kasten) return null
                    const deckung = api.value(4)
                    const platzFuerZeichen = kasten.width > 22
                    const einzug = platzFuerZeichen ? 20 : 5
                    const linksAb = kasten.x > anfangs[0] + 0.5
                    const rechtsAb = kasten.x + kasten.width < endes[0] - 0.5
                    const ecken = [linksAb ? 0 : 3, rechtsAb ? 0 : 3,
                                   rechtsAb ? 0 : 3, linksAb ? 0 : 3]
                    return {
                        type: 'group',
                        children: [
                            {
                                type: 'rect',
                                shape: {...kasten, r: ecken},
                                style: {fill: `${stehend}33`, stroke: stehend, lineWidth: 1,
                                        opacity: deckung},
                            },
                            ...(platzFuerZeichen ? [symbol(SYMBOLS.stay, kasten.x + 6,
                                                           kasten.y + kasten.height / 2 - 5, 10, ink, deckung)] : []),
                            {
                                type: 'text',
                                style: {
                                    x: kasten.x + einzug, y: kasten.y + kasten.height / 2,
                                    text: String(api.value(3)), fill: ink, fontSize: 11,
                                    verticalAlign: 'middle',
                                    width: Math.max(kasten.width - einzug - 5, 0),
                                    overflow: 'truncate', opacity: deckung,
                                },
                            },
                        ],
                    }
                },
                encode: {x: [0, 1], y: 2},
                data: bild.balken.map(balken => ({
                    value: [
                        zeitpunkt(balken.von), zeitpunkt(balken.bis),
                        spur(balken.ortId, balken.reihe),
                        beschriften(balken) + (balken.lage ? ` · ${balken.lage}` : ''),
                        blass(balken.spurId),
                    ],
                    spurId: balken.spurId,
                    hinweis: `${beschriften(balken)}<br>${uhr(balken.von)}–${uhr(balken.bis)}` +
                        (balken.lage ? `<br>${balken.lage}` : '') + beiwerk(balken),
                })),
            },
        ],
    }
}

function zeichnen() {
    diagramm?.setOption(optionen(), true)
}

onMounted(() => {
    if (!behaelter.value) return
    diagramm = echarts.init(behaelter.value, undefined, {renderer: 'svg'})
    diagramm.on('click', stelle => {
        const spurId = (stelle.data as {spurId?: string} | undefined)?.spurId
        gewaehlt.value = spurId && gewaehlt.value !== spurId ? spurId : null
    })
    zeichnen()
    beobachter = new ResizeObserver(() => diagramm?.resize())
    beobachter.observe(behaelter.value)
})

onBeforeUnmount(() => {
    beobachter?.disconnect()
    diagramm?.dispose()
})

watch(() => [bild, gewaehlt.value, dark.value], () => zeichnen(), {deep: true})
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-x-5 gap-y-1 mb-2 text-[13px]">
      <span class="flex items-center gap-2">
        <span class="inline-block w-6 h-3 rounded-sm border"
              :style="{background: `${legendenfarben.stehend}33`, borderColor: legendenfarben.stehend}" />
        <UIcon name="i-lucide-map-pin" class="text-muted"/>
        {{ t('ablauf.legende.aufenthalt') }}
      </span>
      <span class="flex items-center gap-2">
        <span class="inline-block w-6 h-0 border-t-2"
              :style="{borderColor: legendenfarben.signal}" />
        <UIcon name="i-lucide-truck" :style="{color: legendenfarben.signal}"/>
        {{ t('ablauf.legende.fahrt') }}
      </span>
      <span class="flex items-center gap-2">
        <span class="inline-block w-6 h-0 border-t-2 border-dashed"
              :style="{borderColor: legendenfarben.signal}" />
        <UIcon name="i-lucide-footprints"
                           :style="{color: legendenfarben.signal}"/>
        {{ t('ablauf.legende.fussweg') }}
      </span>
    </div>

    <div ref="behaelter"
         :style="{height: `${bild.baender.reduce((summe, band) => summe + band.reihen, 0) * REIHE + 90}px`}"
         class="w-full" />
    <p class="text-muted text-[13px] mt-1">{{ t('ablauf.bewegungHinweis') }}</p>
  </div>
</template>
