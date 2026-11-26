/**
 * A value stored as JSON, or the fallback when there is none or the browser refuses to read it,
 * which also covers a blocked or corrupt store. Each caller names its key, so the browser storage
 * catalogue can be checked against the code.
 */
export function parsedOr<T>(read: () => string | null, fallback: T): T {
    try {
        const raw = read()
        return raw ? JSON.parse(raw) as T : fallback
    } catch {
        return fallback
    }
}

/** Stores or removes a value; a browser that refuses to store anything simply forgets it. */
export function storeQuietly(write: () => void): void {
    try {
        write()
    } catch {
        return
    }
}

/** A value stored as plain text, or the fallback when there is none or the browser refuses to read it. */
export function storedOr(read: () => string | null, fallback: string): string {
    try {
        return read() ?? fallback
    } catch {
        return fallback
    }
}
