import { useEffect, useState } from 'react';
import { useI18n } from '../i18nContext';

export function Greeting() {
    const { lang } = useI18n();
    const [greeting, setGreeting] = useState<string | null>(null);

    // 선택한 언어가 바뀌면 해당 언어의 인사말을 서버에서 다시 받는다
    useEffect(() => {
        fetch(`/api/greeting?lang=${lang}`)
            .then((res) => {
                if (!res.ok) throw new Error(`HTTP error ${res.status}`);
                return res.json() as Promise<{ greeting?: string }>;
            })
            .then((data) => setGreeting(data?.greeting || ''))
            .catch((err: unknown) =>
                console.error('Failed to load greeting:', err),
            );
    }, [lang]);

    if (!greeting) return null;

    return <h1 className="text-center mb-5">{greeting}</h1>;
}
