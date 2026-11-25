import { useCallback, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
    I18nContext,
    STORAGE_KEY_LANG,
    initialLang,
    translate,
} from './i18nContext';
import type { I18nValue, Lang } from './i18nContext';

export function I18nProvider({ children }: { children: ReactNode }) {
    const [lang, setLangState] = useState<Lang>(initialLang);

    const setLang = useCallback((next: Lang) => {
        setLangState(next);
        try {
            localStorage.setItem(STORAGE_KEY_LANG, next);
        } catch {
            // 무시
        }
        document.documentElement.lang = next;
    }, []);

    const t = useCallback<I18nValue['t']>(
        (key, params) => translate(lang, key, params),
        [lang],
    );

    const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
    return (
        <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
    );
}
