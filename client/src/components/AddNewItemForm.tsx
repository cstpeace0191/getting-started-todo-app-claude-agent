import { useState } from 'react';
import type { FormEvent } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import { useI18n } from '../i18nContext';
import { localToday } from '../dates';
import type { TodoItem } from './ItemDisplay';

interface AddItemFormProps {
    onNewItem: (item: TodoItem) => void;
    aiEnabled?: boolean;
}

export function AddItemForm({
    onNewItem,
    aiEnabled = false,
}: AddItemFormProps) {
    const { t } = useI18n();
    const [newItem, setNewItem] = useState('');
    const [dueDate, setDueDate] = useState('');
    const [dueTime, setDueTime] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const submitNewItem = (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const trimmed = newItem.trim();
        if (!trimmed || submitting) return;
        setSubmitting(true);

        const options = {
            method: 'POST',
            body: JSON.stringify({
                name: trimmed,
                today: localToday(),
                // 날짜를 직접 지정하면 AI 가 추출한 날짜보다 우선한다
                ...(dueDate
                    ? {
                          due_date: dueDate,
                          ...(dueTime && { due_time: dueTime }),
                      }
                    : {}),
            }),
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
                setDueDate('');
                setDueTime('');
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
                    placeholder={t('newItemPlaceholder')}
                    aria-label="New item"
                />
                <Button
                    type="submit"
                    variant="success"
                    disabled={!newItem.trim().length || submitting}
                >
                    {submitting
                        ? aiEnabled
                            ? t('aiClassifyingAdd')
                            : t('adding')
                        : t('addItem')}
                </Button>
            </InputGroup>
            <div className="due-input mb-3">
                <span className="text-muted small">{t('dueOptional')}</span>
                <Form.Control
                    size="sm"
                    type="date"
                    aria-label={t('dueDate')}
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                />
                <Form.Control
                    size="sm"
                    type="time"
                    aria-label={t('dueTime')}
                    value={dueTime}
                    disabled={!dueDate}
                    onChange={(e) => setDueTime(e.target.value)}
                />
            </div>
        </Form>
    );
}
