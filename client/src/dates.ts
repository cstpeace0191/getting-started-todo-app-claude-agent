/** 로컬 시간대 기준 Date → YYYY-MM-DD (UTC 변환 없이) */
export function toYmd(d: Date): string {
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${mm}-${dd}`;
}

/** YYYY-MM-DD → 로컬 자정의 Date */
export function parseYmd(value: string): Date {
    const [y, m, d] = value.split('-').map(Number);
    return new Date(y, m - 1, d);
}

/** 브라우저(사용자) 기준 오늘 날짜 YYYY-MM-DD (UTC 가 아닌 로컬 날짜) */
export function localToday(): string {
    return toYmd(new Date());
}

export type DateRange = [start: string, end: string];

/** day 가 속한 주의 월요일~일요일 */
export function weekRange(day: string): DateRange {
    const d = parseYmd(day);
    const sinceMonday = (d.getDay() + 6) % 7; // 월=0 ... 일=6
    const start = new Date(
        d.getFullYear(),
        d.getMonth(),
        d.getDate() - sinceMonday,
    );
    const end = new Date(
        start.getFullYear(),
        start.getMonth(),
        start.getDate() + 6,
    );
    return [toYmd(start), toYmd(end)];
}

/** day 가 속한 달의 1일~말일 */
export function monthRange(day: string): DateRange {
    const d = parseYmd(day);
    return [
        toYmd(new Date(d.getFullYear(), d.getMonth(), 1)),
        toYmd(new Date(d.getFullYear(), d.getMonth() + 1, 0)),
    ];
}

/** day 가 속한 해의 1월 1일~12월 31일 */
export function yearRange(day: string): DateRange {
    const y = parseYmd(day).getFullYear();
    return [toYmd(new Date(y, 0, 1)), toYmd(new Date(y, 11, 31))];
}
