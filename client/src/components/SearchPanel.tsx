import { useCallback, useEffect, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import Row from 'react-bootstrap/Row';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagnifyingGlass } from '@fortawesome/free-solid-svg-icons/faMagnifyingGlass';
import { faXmark } from '@fortawesome/free-solid-svg-icons/faXmark';
import { faCheck } from '@fortawesome/free-solid-svg-icons/faCheck';
import { faPen } from '@fortawesome/free-solid-svg-icons/faPen';
import { faTrash } from '@fortawesome/free-solid-svg-icons/faTrash';
import { useI18n } from '../i18nContext';
import { ItemTags } from './ItemTags';
import { ItemEditForm } from './ItemEditForm';
import { BulkBar } from './BulkBar';
import { useSelection } from './useSelection';
import { CATEGORIES, CATEGORY_COLORS } from './categories';
import type { Category, TodoItem } from './ItemDisplay';
import './ItemDisplay.scss';

type Mode = 'all' | 'category' | 'keyword';

const NO_RESULTS: TodoItem[] = [];

/** 검색 결과에서는 일정을 읽기 전용 배지로 보여준다 (수정은 '수정' 버튼) */
function DueBadge({ item }: { item: TodoItem }) {
    if (!item.due_date) return null;
    return (
        <Badge bg="secondary" className="due-badge-static">
            {item.due_date}
            {item.due_time ? ` ${item.due_time}` : ''}
        </Badge>
    );
}

interface CategoryCount {
    category: Category;
    count: number;
}

/**
 * 등록(Register)된 항목 검색
 *  1. 전체: DB 에 등록된 항목 전체
 *  2. 분류별: 분류 목록(개수 포함)에서 선택 후, 그 분류 안에서 키워드로 추가 검색
 *  3. 키워드: 이름에 키워드가 포함된 항목
 * 결과 항목에서 '확인' 은 화면에서만 숨기고, '삭제' 는 DB 에서 삭제한다.
 */
export function SearchPanel() {
    const { t } = useI18n();
    const [mode, setMode] = useState<Mode>('all');
    const [searchInput, setSearchInput] = useState('');
    const [query, setQuery] = useState('');
    const [category, setCategory] = useState<Category | null>(null);
    const [counts, setCounts] = useState<CategoryCount[]>([]);
    const [results, setResults] = useState<TodoItem[] | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const selection = useSelection(results ?? NO_RESULTS);
    const clearSelection = selection.clear;

    // 입력이 멈춘 뒤 300ms 후에 검색어를 확정
    useEffect(() => {
        const timer = setTimeout(() => setQuery(searchInput.trim()), 300);
        return () => clearTimeout(timer);
    }, [searchInput]);

    const loadCounts = useCallback(() => {
        fetch('/api/categories?registered=true')
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<CategoryCount[]>;
            })
            .then(setCounts)
            .catch((err: unknown) =>
                console.error('Failed to load categories:', err),
            );
    }, []);

    useEffect(loadCounts, [loadCounts]);

    // 모드별 검색 조건. null 이면 아직 검색할 수 없는 상태(안내 문구 표시)
    const buildUrl = (): string | null => {
        const params = new URLSearchParams({ registered: 'true' });
        if (mode === 'category') {
            if (!category) return null;
            params.set('category', category);
            if (query) params.set('q', query);
        } else if (mode === 'keyword') {
            if (!query) return null;
            params.set('q', query);
        }
        return `/api/items?${params.toString()}`;
    };
    const url = buildUrl();

    useEffect(() => {
        if (url === null) {
            setResults([]);
            return;
        }
        const controller = new AbortController();
        setResults(null);
        clearSelection();
        fetch(url, { signal: controller.signal })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                return r.json() as Promise<TodoItem[]>;
            })
            .then((data) => setResults(Array.isArray(data) ? data : []))
            .catch((err: unknown) => {
                if (err instanceof DOMException && err.name === 'AbortError')
                    return;
                console.error('Failed to search items:', err);
                setResults([]);
            });
        return () => controller.abort();
    }, [url, clearSelection]);

    const changeMode = (next: Mode) => {
        setMode(next);
        setSearchInput('');
        setQuery('');
        if (next === 'category') loadCounts();
    };

    // 확인: 화면에서만 숨김 (DB 유지)
    const dismiss = (item: TodoItem) =>
        setResults((prev) => (prev ?? []).filter((i) => i.id !== item.id));

    // 삭제: DB 에서 삭제하고 화면에서도 제거
    const remove = (item: TodoItem) => {
        if (!window.confirm(t('deleteConfirm'))) return;
        fetch(`/api/items/${item.id}`, { method: 'DELETE' })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                dismiss(item);
                loadCounts();
            })
            .catch((err: unknown) =>
                console.error('Failed to remove item:', err),
            );
    };

    const showKeywordBox = mode === 'keyword' || mode === 'category';

    let emptyMessage = t('noResults');
    if (mode === 'category' && !category) {
        emptyMessage =
            counts.length === 0 ? t('noCategories') : t('pickCategory');
    } else if (mode === 'keyword' && !query) {
        emptyMessage = t('enterKeyword');
    } else if (query) {
        emptyMessage = t('noResultsFor', { q: query });
    }

    return (
        <>
            <ButtonGroup className="w-100 mb-3" aria-label="Search mode">
                {(
                    [
                        ['all', t('modeAll')],
                        ['category', t('modeCategory')],
                        ['keyword', t('modeKeyword')],
                    ] as [Mode, string][]
                ).map(([value, label]) => (
                    <Button
                        key={value}
                        variant={mode === value ? 'primary' : 'outline-primary'}
                        onClick={() => changeMode(value)}
                    >
                        {label}
                    </Button>
                ))}
            </ButtonGroup>

            {mode === 'category' && (
                <div className="category-list mb-3">
                    {counts.length === 0 && (
                        <span className="text-muted">{t('noCategories')}</span>
                    )}
                    {CATEGORIES.filter((c) =>
                        counts.some((x) => x.category === c),
                    ).map((c) => {
                        const count =
                            counts.find((x) => x.category === c)?.count ?? 0;
                        return (
                            <Button
                                key={c}
                                size="sm"
                                variant={
                                    category === c
                                        ? CATEGORY_COLORS[c]
                                        : `outline-${CATEGORY_COLORS[c]}`
                                }
                                onClick={() =>
                                    setCategory(category === c ? null : c)
                                }
                            >
                                {t(`category.${c}`)} ({count})
                            </Button>
                        );
                    })}
                </div>
            )}

            {showKeywordBox && (mode === 'keyword' || category) && (
                <InputGroup className="mb-3">
                    <InputGroup.Text>
                        <FontAwesomeIcon icon={faMagnifyingGlass} />
                    </InputGroup.Text>
                    <Form.Control
                        type="text"
                        placeholder={
                            mode === 'category'
                                ? t('categoryKeywordPlaceholder')
                                : t('keywordPlaceholder')
                        }
                        aria-label="Search keyword"
                        value={searchInput}
                        onChange={(e) => setSearchInput(e.target.value)}
                    />
                    {searchInput && (
                        <Button
                            variant="outline-secondary"
                            aria-label={t('clearSearch')}
                            onClick={() => setSearchInput('')}
                        >
                            <FontAwesomeIcon icon={faXmark} />
                        </Button>
                    )}
                </InputGroup>
            )}

            {results === null && <p className="text-center">{t('loading')}</p>}
            {results !== null && results.length === 0 && (
                <p className="text-center text-muted">{emptyMessage}</p>
            )}
            {results !== null && results.length > 0 && (
                <p className="text-muted small">
                    {t('resultCount', { n: results.length })}
                </p>
            )}
            {results !== null && (
                <BulkBar
                    total={results.length}
                    selectedIds={selection.selectedIds}
                    allSelected={selection.allSelected}
                    onSelectAll={selection.setAll}
                    onDeleted={(ids) => {
                        setResults((prev) =>
                            (prev ?? []).filter((i) => !ids.includes(i.id)),
                        );
                        loadCounts();
                    }}
                />
            )}
            {results?.map((item) => (
                <Container fluid className="item" key={item.id}>
                    <Row>
                        <Col xs="auto" className="select-col">
                            <Form.Check
                                type="checkbox"
                                aria-label={t('selectItem')}
                                checked={selection.isSelected(item.id)}
                                onChange={(e) =>
                                    selection.setOne(item.id, e.target.checked)
                                }
                            />
                        </Col>
                        <Col className="name">
                            {editingId === item.id ? (
                                <ItemEditForm
                                    item={item}
                                    onCancel={() => setEditingId(null)}
                                    onSaved={(updated) => {
                                        setEditingId(null);
                                        setResults((prev) =>
                                            (prev ?? []).map((i) =>
                                                i.id === updated.id
                                                    ? updated
                                                    : i,
                                            ),
                                        );
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
                                        <DueBadge item={item} />
                                    </div>
                                </>
                            )}
                        </Col>
                        <Col xs="auto" className="result-actions">
                            <Button
                                size="sm"
                                variant="outline-primary"
                                onClick={() => dismiss(item)}
                                title={t('confirmTitle')}
                            >
                                <FontAwesomeIcon icon={faCheck} />{' '}
                                {t('confirm')}
                            </Button>
                            <Button
                                size="sm"
                                variant="outline-secondary"
                                onClick={() => setEditingId(item.id)}
                                disabled={editingId === item.id}
                                title={t('editTitle')}
                            >
                                <FontAwesomeIcon icon={faPen} /> {t('edit')}
                            </Button>
                            <Button
                                size="sm"
                                variant="outline-danger"
                                onClick={() => remove(item)}
                                title={t('deleteTitle')}
                            >
                                <FontAwesomeIcon icon={faTrash} /> {t('delete')}
                            </Button>
                        </Col>
                    </Row>
                </Container>
            ))}
            <p className="text-center text-muted small mt-4">
                {t('registeredOnly')}
            </p>
        </>
    );
}
