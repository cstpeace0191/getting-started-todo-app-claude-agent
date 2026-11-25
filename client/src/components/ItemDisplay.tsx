import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPen } from '@fortawesome/free-solid-svg-icons/faPen';
import { faBoxArchive } from '@fortawesome/free-solid-svg-icons/faBoxArchive';
import { faWandMagicSparkles } from '@fortawesome/free-solid-svg-icons/faWandMagicSparkles';
import { useI18n } from '../i18nContext';
import { ItemTags } from './ItemTags';
import { DueEditor } from './DueEditor';
import { ItemEditForm } from './ItemEditForm';
import { localToday } from '../dates';
import './ItemDisplay.scss';

export type Category = 'study' | 'work' | 'personal';
export type Priority = 'high' | 'medium' | 'low';

export interface TodoItem {
    id: string;
    name: string;
    completed: boolean;
    category?: Category | null;
    priority?: Priority | null;
    registered?: boolean;
    due_date?: string | null;
    due_time?: string | null;
}

interface ItemDisplayProps {
    item: TodoItem;
    aiEnabled: boolean;
    onItemUpdate: (item: TodoItem) => void;
    /** 오늘 일정 탭처럼 '등록' 버튼이 필요 없는 곳에서 숨긴다 */
    hideRegister?: boolean;
    /** 일괄 삭제용 선택 체크박스 (onSelectChange 를 넘기면 표시) */
    selected?: boolean;
    onSelectChange?: (checked: boolean) => void;
}

export function ItemDisplay({
    item,
    aiEnabled,
    onItemUpdate,
    hideRegister = false,
    selected = false,
    onSelectChange,
}: ItemDisplayProps) {
    const { t } = useI18n();
    const [classifying, setClassifying] = useState(false);
    const [registering, setRegistering] = useState(false);
    const [editing, setEditing] = useState(false);

    const reclassify = () => {
        if (classifying) return;
        setClassifying(true);
        fetch(`/api/items/${item.id}/classify?today=${localToday()}`, {
            method: 'POST',
        })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<TodoItem>;
            })
            .then(onItemUpdate)
            .catch((err: unknown) =>
                console.error('Failed to classify item:', err),
            )
            .finally(() => setClassifying(false));
    };

    const toggleCompletion = () => {
        fetch(`/api/items/${item.id}`, {
            method: 'PUT',
            body: JSON.stringify({
                name: item.name,
                completed: !item.completed,
            }),
            headers: { 'Content-Type': 'application/json' },
        })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<TodoItem>;
            })
            .then(onItemUpdate)
            .catch((err: unknown) =>
                console.error('Failed to update item:', err),
            );
    };

    // 등록: DB 에 registered=true 로 저장한다. 등록 후에야 완료/해야됨 토글과 수정 버튼이 나타난다
    const registerItem = () => {
        if (registering) return;
        setRegistering(true);
        fetch(`/api/items/${item.id}`, {
            method: 'PUT',
            body: JSON.stringify({ registered: true }),
            headers: { 'Content-Type': 'application/json' },
        })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<TodoItem>;
            })
            .then((saved) => {
                onItemUpdate(saved);
                setRegistering(false);
            })
            .catch((err: unknown) => {
                console.error('Failed to register item:', err);
                setRegistering(false);
            });
    };

    // 등록 전에는 '등록' 버튼만, 등록 후(또는 등록이 필요 없는 화면)에는 토글+수정 버튼
    const showActions = hideRegister || Boolean(item.registered);

    return (
        <Container fluid className={`item ${item.completed && 'completed'}`}>
            <Row>
                {onSelectChange && (
                    <Col xs="auto" className="select-col">
                        <Form.Check
                            type="checkbox"
                            aria-label={t('selectItem')}
                            checked={selected}
                            onChange={(e) => onSelectChange(e.target.checked)}
                        />
                    </Col>
                )}
                <Col className="name">
                    {editing ? (
                        <ItemEditForm
                            item={item}
                            onCancel={() => setEditing(false)}
                            onSaved={(updated) => {
                                setEditing(false);
                                onItemUpdate(updated);
                            }}
                        />
                    ) : (
                        <>
                            <div>{item.name}</div>
                            <div className="tags">
                                <ItemTags
                                    category={item.category}
                                    priority={item.priority}
                                />
                                <DueEditor
                                    item={item}
                                    onItemUpdate={onItemUpdate}
                                />
                                {aiEnabled && (
                                    <Button
                                        className="classify"
                                        size="sm"
                                        variant="link"
                                        onClick={reclassify}
                                        disabled={classifying}
                                        aria-label="Classify item with AI"
                                        title={t('reclassifyTitle')}
                                    >
                                        <FontAwesomeIcon
                                            icon={faWandMagicSparkles}
                                        />{' '}
                                        {classifying
                                            ? t('classifying')
                                            : item.category
                                              ? t('reclassify')
                                              : t('aiClassify')}
                                    </Button>
                                )}
                            </div>
                        </>
                    )}
                </Col>
                <Col xs="auto" className="actions">
                    {!showActions && (
                        <Button
                            size="sm"
                            variant="outline-success"
                            onClick={registerItem}
                            disabled={registering}
                            title={t('registerTitle')}
                            aria-label="Register item"
                        >
                            <FontAwesomeIcon icon={faBoxArchive} />{' '}
                            {t('register')}
                        </Button>
                    )}
                    {showActions && (
                        <>
                            <Button
                                size="sm"
                                className={`status-toggle ${item.completed ? 'is-done' : 'is-todo'}`}
                                onClick={toggleCompletion}
                                aria-pressed={item.completed}
                                title={t('statusTitle')}
                                aria-label={
                                    item.completed
                                        ? 'Mark item as incomplete'
                                        : 'Mark item as complete'
                                }
                            >
                                {item.completed
                                    ? t('statusDone')
                                    : t('statusTodo')}
                            </Button>
                            <Button
                                size="sm"
                                variant="outline-secondary"
                                onClick={() => setEditing(true)}
                                disabled={editing}
                                title={t('editTitle')}
                                aria-label="Edit item"
                            >
                                <FontAwesomeIcon icon={faPen} /> {t('edit')}
                            </Button>
                        </>
                    )}
                </Col>
            </Row>
        </Container>
    );
}
