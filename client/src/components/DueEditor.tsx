import { useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalendarDay } from '@fortawesome/free-solid-svg-icons/faCalendarDay';
import { useI18n } from '../i18nContext';
import { localToday } from '../dates';
import type { TodoItem } from './ItemDisplay';

interface DueEditorProps {
    item: TodoItem;
    onItemUpdate: (item: TodoItem) => void;
}

/** 일정(날짜/시간) 표시 배지. 누르면 그 자리에서 날짜·시간을 수정/삭제할 수 있다 */
export function DueEditor({ item, onItemUpdate }: DueEditorProps) {
    const { t } = useI18n();
    const [editing, setEditing] = useState(false);
    const [date, setDate] = useState(item.due_date ?? '');
    const [time, setTime] = useState(item.due_time ?? '');
    const [saving, setSaving] = useState(false);

    const open = () => {
        setDate(item.due_date ?? '');
        setTime(item.due_time ?? '');
        setEditing(true);
    };

    // 서버 규칙: due_date "" 는 일정 삭제(시간도 함께 삭제), due_time "" 는 시간만 삭제
    const save = (nextDate: string, nextTime: string) => {
        if (saving) return;
        setSaving(true);
        fetch(`/api/items/${item.id}`, {
            method: 'PUT',
            body: JSON.stringify({ due_date: nextDate, due_time: nextTime }),
            headers: { 'Content-Type': 'application/json' },
        })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<TodoItem>;
            })
            .then((updated) => {
                setEditing(false);
                onItemUpdate(updated);
            })
            .catch((err: unknown) =>
                console.error('Failed to update schedule:', err),
            )
            .finally(() => setSaving(false));
    };

    if (editing) {
        return (
            <span className="due-editor">
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
                    onChange={(e) => setTime(e.target.value)}
                />
                <Button
                    size="sm"
                    variant="primary"
                    disabled={!date || saving}
                    onClick={() => save(date, time)}
                >
                    {t('save')}
                </Button>
                <Button
                    size="sm"
                    variant="outline-secondary"
                    onClick={() => setEditing(false)}
                >
                    {t('cancel')}
                </Button>
                {item.due_date && (
                    <Button
                        size="sm"
                        variant="outline-danger"
                        disabled={saving}
                        onClick={() => save('', '')}
                    >
                        {t('clearDue')}
                    </Button>
                )}
            </span>
        );
    }

    if (!item.due_date) {
        return (
            <Button
                className="classify"
                size="sm"
                variant="link"
                onClick={open}
            >
                <FontAwesomeIcon icon={faCalendarDay} /> {t('setDue')}
            </Button>
        );
    }

    const today = localToday();
    const overdue = item.due_date < today && !item.completed;
    const bg = overdue
        ? 'danger'
        : item.due_date === today
          ? 'success'
          : 'secondary';

    return (
        <Badge
            as="button"
            type="button"
            bg={bg}
            className="due-badge"
            title={t('editDueTitle')}
            onClick={open}
        >
            <FontAwesomeIcon icon={faCalendarDay} /> {item.due_date}
            {item.due_time ? ` ${item.due_time}` : ''}
            {overdue ? ` (${t('overdueBadge')})` : ''}
        </Badge>
    );
}
