import { useState } from 'react';
import type { FormEvent } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import type { TodoItem } from './ItemDisplay';

interface AddItemFormProps {
    onNewItem: (item: TodoItem) => void;
}

export function AddItemForm({ onNewItem }: AddItemFormProps) {
    const [newItem, setNewItem] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const submitNewItem = (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const trimmed = newItem.trim();
        if (!trimmed || submitting) return;
        setSubmitting(true);

        const options = {
            method: 'POST',
            body: JSON.stringify({ name: trimmed }),
            headers: { 'Content-Type': 'application/json' },
        };

        fetch('/api/items', options)
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<TodoItem>;
            })
            .then((item) => {
                onNewItem(item);
                setSubmitting(false);
                setNewItem('');
            })
            .catch((err: unknown) => {
                console.error('Failed to add item:', err);
                setSubmitting(false);
            });
    };

    return (
        <Form onSubmit={submitNewItem}>
            <InputGroup className="mb-3">
                <Form.Control
                    value={newItem}
                    onChange={(e) => setNewItem(e.target.value)}
                    type="text"
                    placeholder="New Item"
                    aria-label="New item"
                />
                <Button
                    type="submit"
                    variant="success"
                    disabled={!newItem.trim().length || submitting}
                >
                    {submitting ? 'Adding...' : 'Add Item'}
                </Button>
            </InputGroup>
        </Form>
    );
}
