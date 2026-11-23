import { useEffect, useState } from 'react';

export function Greeting() {
    const [greeting, setGreeting] = useState<string | null>(null);

    useEffect(() => {
        fetch('/api/greeting')
            .then((res) => {
                if (!res.ok) throw new Error(`HTTP error ${res.status}`);
                return res.json() as Promise<{ greeting?: string }>;
            })
            .then((data) => setGreeting(data?.greeting || ''))
            .catch((err: unknown) =>
                console.error('Failed to load greeting:', err),
            );
    }, [setGreeting]);

    if (!greeting) return null;

    return <h1 className="text-center mb-5">{greeting}</h1>;
}
