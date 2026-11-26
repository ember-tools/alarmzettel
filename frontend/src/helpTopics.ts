/**
 * The topics of the help center in reading order: the slug of each page and the catalogue key below
 * `help.topics` that holds its title and description. `vite.config.ts` prerenders a page per slug.
 */
export const HELP_TOPICS = [
    {slug: 'alarme-anlegen', key: 'alarms'},
    {slug: 'adressen', key: 'addresses'},
    {slug: 'einsatzmittel', key: 'vehicles'},
    {slug: 'drucken', key: 'printing'},
    {slug: 'kataloge', key: 'catalogues'},
    {slug: 'ablauf', key: 'schedule'},
    {slug: 'gemeinsam-arbeiten', key: 'together'},
    {slug: 'arbeitsmappe', key: 'workbook'},
] as const

/** The slug of a help topic. */
export type HelpSlug = (typeof HELP_TOPICS)[number]['slug']
