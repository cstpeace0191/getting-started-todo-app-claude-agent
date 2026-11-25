import { useState } from 'react';
import type { FormEvent } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { useI18n } from '../i18nContext';
import type { TodoItem } from './ItemDisplay';

interface ItemEditFormProps {
    item: TodoItem;
    onSaved: (item: TodoItem) => void;
    onCancel: () => void;
}

/** 할 일 내용과 일정(날짜·시간)을 한 번에 수정하는 인라인 폼 */
export function ItemEditForm({ item, onSaved, onCancel }: ItemEditFormProps) {
    const { t } = useI18n();
    const [name, setName] = useState(item.name);
    const [date, setDate] = useState(item.due_date ?? '');
    const [time, setTime] = useState(item.due_time ?? '');
    const [saving, setSaving] = useState(false);

    const trimmed = name.trim();
    const canSave = trimmed.length > 0 && !saving;

    const submit = (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!canSave) return;
        setSaving(true);
        // 서버 규칙: due_date "" 는 일정 삭제(시간도 함께 삭제), due_time "" 는 시간만 삭제
        fetch(`/api/items/${item.id}`, {
            method: 'PUT',
            body: JSON.stringify({
                name: trimmed,
                due_date: date,
                due_time: date ? time : '',
            }),
            headers: { 'Content-Type': 'application/json' },
        })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<TodoItem>;
            })
            .then(onSaved)
            .catch((err: unknown) => {
                console.error('Failed to edit item:', err);
                setSaving(false);
            });
    };

    return (
        <Form className="edit-form" onSubmit={submit}>
            <Form.Control
                size="sm"
                type="text"
                autoFocus
                maxLength={255}
                aria-label={t('editNameLabel')}
                value={name}
                onChange={(e) => setName(e.target.value)}
            />
            <div className="edit-form-row">
                <Form.Control
                    size="sm"
                    type="date"
                    aria-label={t('dueDate')}
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                />
                <Form.Control
                    size="sm"
                    type="time"
                    aria-label={t('dueTime')}
                    value={time}
                    disabled={!date}
                    onChange={(e) => setTime(e.target.value)}
                />
                <Button
                    size="sm"
                    type="submit"
                    variant="primary"
                    disabled={!canSave}
                >
                    {saving ? t('saving') : t('editDone')}
                </Button>
                <Button
                    size="sm"
                    type="button"
                    variant="outline-secondary"
                    onClick={onCancel}
                >
                    {t('cancel')}
                </Button>
            </div>
        </Form>
    );
}
