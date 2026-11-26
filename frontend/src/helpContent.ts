import type {HelpTopicInfo} from '@emberbox/ui'
import {HELP_TOPICS, type HelpSlug} from './helpTopics'
import {t} from './i18n'

/** One block of a help page: the numbered paragraphs of a catalogue entry. */
export interface HelpBlock {
    /** The catalogue key below `help` whose paragraphs `1`, `2`, … the block shows. */
    topic: string
    /** How many paragraphs the entry has. */
    count: number
}

/** What each help page shows, by slug. */
export const HELP_CONTENT: Record<HelpSlug, HelpBlock[]> = {
    'alarme-anlegen': [{topic: 'alarms.create', count: 2}],
    'adressen': [{topic: 'alarms.addresses', count: 3}],
    'einsatzmittel': [{topic: 'alarms.vehicles', count: 2}],
    'drucken': [{topic: 'alarms.printing', count: 2}],
    'kataloge': [{topic: 'catalogues', count: 2}],
    'ablauf': [{topic: 'schedule', count: 4}],
    'gemeinsam-arbeiten': [{topic: 'together', count: 3}],
    'arbeitsmappe': [{topic: 'workbook', count: 3}],
}

/**
 * The numbered paragraphs of a help entry.
 *
 * @param topic the entry's key below `help`, such as `alarms.create`
 * @param count how many paragraphs it has
 * @returns the paragraphs
 */
export function paragraphs(topic: string, count: number): string[] {
    return Array.from({length: count}, (_, index) => t(`help.${topic}.${index + 1}`))
}

/**
 * The help topics with their titles and descriptions from the catalogue.
 *
 * @returns the topics in reading order
 */
export function helpTopicInfos(): HelpTopicInfo[] {
    return HELP_TOPICS.map(topic => ({
        slug: topic.slug,
        title: t(`help.topics.${topic.key}.title`),
        description: t(`help.topics.${topic.key}.description`),
    }))
}
