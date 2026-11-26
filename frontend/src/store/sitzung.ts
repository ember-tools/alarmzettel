/**
 * Die laufende Sitzung dieses Browsers und die, die er sonst noch kennt.
 *
 * Das Token der laufenden steht im Cookie, das der Server setzt – deshalb steht hier keines. Die
 * Liste der bekannten gehört dem Browser und nicht der Arbeitsmappe, also liegt sie im
 * `localStorage`; eine Sitzung, die der Server nicht mehr kennt, fliegt beim Öffnen heraus.
 */
import {reactive} from 'vue'
import {laufendeSitzung, sitzungAnlegen, sitzungUebernehmen, type Sitzungskopf} from '../api/sitzung'
import {arbeitsmappe, ersetzen, uebernehmen} from './arbeitsmappe'
import {beitreten, verbindung, verlassen} from './sync'
import type {Arbeitsmappe} from '../interfaces/Alarm'

const BEKANNT = 'alarmzettel_sitzungen'
const NAME = 'alarmzettel_name'

export interface BekannteSitzung {
    token: string
    beschriftung: string
    zuletzt: string
}

export const sitzung = reactive({
    token: null as string | null,
    laeuftAb: null as string | null,
    /** Diese Sitzung ist über einen Lesen-Link geöffnet: sehen ja, mitschreiben nein. */
    nurLesen: false,
    bekannt: [] as BekannteSitzung[],
})

/**
 * A value stored as JSON, or the fallback when there is none or the browser refuses to read it.
 * Each caller names its key, so the browser storage catalogue can be checked against the code.
 */
function parsedOr<T>(read: () => string | null, fallback: T): T {
    try {
        const raw = read()
        return raw ? JSON.parse(raw) as T : fallback
    } catch {
        return fallback
    }
}

/** Stores a value; a browser that refuses to store anything simply forgets it. */
function storeQuietly(write: () => void): void {
    try {
        write()
    } catch {
        return
    }
}

/** Woran man eine Sitzung wiedererkennt: erstes Stichwort und wie viele Alarme darin stehen. */
function beschriftung(mappe: Arbeitsmappe): string {
    const erste = mappe.alarme[0]?.stichwort?.trim()
    const anzahl = mappe.alarme.length
    if (!anzahl) return 'leer'
    return erste ? `${erste} (${anzahl})` : `${anzahl} Alarme`
}

function merken(token: string) {
    const ohne = sitzung.bekannt.filter(eintrag => eintrag.token !== token)
    sitzung.bekannt = [{token, beschriftung: beschriftung(arbeitsmappe),
                        zuletzt: new Date().toISOString()}, ...ohne].slice(0, 20)
    storeQuietly(() => localStorage.setItem(BEKANNT, JSON.stringify(sitzung.bekannt)))
}

export function sitzungVergessen(token: string) {
    sitzung.bekannt = sitzung.bekannt.filter(eintrag => eintrag.token !== token)
    storeQuietly(() => localStorage.setItem(BEKANNT, JSON.stringify(sitzung.bekannt)))
}

/** The name this browser last worked under, empty when it has none yet. */
export function rememberedName(): string {
    return parsedOr<string>(() => localStorage.getItem(NAME), '')
}

export function name(): string {
    return rememberedName() || 'Ich'
}

export function nameSetzen(wert: string) {
    storeQuietly(() => localStorage.setItem(NAME, JSON.stringify(wert.trim())))
    verbindung.wer = wert.trim() || 'Ich'
}

function uebernehmenIn(kopf: Sitzungskopf) {
    sitzung.token = kopf.token
    sitzung.laeuftAb = kopf.laeuftAb
    sitzung.nurLesen = kopf.nurLesen
    merken(kopf.token)
}

/**
 * Beim Start: die Sitzung aus dem Cookie aufnehmen. Gibt es keine, wird eine angelegt – mit dem,
 * was noch im `localStorage` liegt, damit die Umstellung niemandem seine Arbeit nimmt.
 */
export async function sitzungStarten() {
    sitzung.bekannt = parsedOr<BekannteSitzung[]>(() => localStorage.getItem(BEKANNT), [])
    const laufend = await laufendeSitzung()
    if (laufend) {
        await beitreten(laufend.token, name(), laufend.nurLesen)
        uebernehmenIn(laufend)
        return
    }
    const kopf = await sitzungAnlegen(arbeitsmappe)
    await beitreten(kopf.token, name())
    uebernehmenIn(kopf)
}

/** Eine leere Sitzung. Die alte bleibt liegen, sie ist ja nicht gelöscht. */
export async function neueSitzung() {
    const leer = uebernehmen({version: 1, alarme: []} as unknown as Arbeitsmappe)
    const kopf = await sitzungAnlegen(leer)
    verlassen()
    ersetzen(leer)
    await beitreten(kopf.token, name())
    uebernehmenIn(kopf)
}

/** In eine bekannte oder geteilte Sitzung wechseln. */
export async function sitzungWechseln(token: string) {
    const kopf = await sitzungUebernehmen(token)
    await beitreten(token, name(), kopf.nurLesen)
    uebernehmenIn(kopf)
}
