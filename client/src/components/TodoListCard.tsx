import { useCallback, useEffect, useState } from 'react';
import { AddItemForm } from './AddNewItemForm';
import { ItemDisplay } from './ItemDisplay';
import type { TodoItem } from './ItemDisplay';

export function TodoListCard() {
    const [items, setItems] = useState<TodoItem[] | null>(null);

    useEffect(() => {
        fetch('/api/items')
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<TodoItem[]>;
            })
            .then((data) => setItems(Array.isArray(data) ? data : []))
            .catch((err: unknown) => {
                console.error('Failed to load items:', err);
                setItems([]);
            });
    }, []);

    const onNewItem = useCallback((newItem: TodoItem) => {
        setItems((prev) => [...(prev ?? []), newItem]);
    }, []);

    const onItemUpdate = useCallback((item: TodoItem) => {
        setItems((prev) => {
            const list = prev ?? [];
            const index = list.findIndex((i) => i.id === item.id);
            if (index === -1) return list;
            return [...list.slice(0, index), item, ...list.slice(index + 1)];
        });
    }, []);

    const onItemRemoval = useCallback((item: TodoItem) => {
        setItems((prev) => {
            const list = prev ?? [];
            const index = list.findIndex((i) => i.id === item.id);
            if (index === -1) return list;
            return [...list.slice(0, index), ...list.slice(index + 1)];
        });
    }, []);

    if (items === null) return 'Loading...';

    return (
        <>
            <AddItemForm onNewItem={onNewItem} />
            {items.length === 0 && (
                <p className="text-center">No items yet! Add one above!</p>
            )}
            {items.map((item) => (
                <ItemDisplay
                    key={item.id}
                    item={item}
                    onItemUpdate={onItemUpdate}
                    onItemRemoval={onItemRemoval}
                />
            ))}
        </>
    );
}
