import { useEffect, useRef, useState } from 'react';
import Button from 'react-bootstrap/Button';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons/faTrash';
import { useI18n } from '../i18nContext';

interface BulkBarProps {
    total: number;
    selectedIds: string[];
    allSelected: boolean;
    onSelectAll: (checked: boolean) => void;
    /** 서버에서 삭제가 끝난 뒤 호출된다 (화면 목록에서 제거하는 용도) */
    onDeleted: (ids: string[]) => void;
}

/** 목록 상단의 '전체 선택' 체크박스 + '선택 삭제' 버튼 */
export function BulkBar({
    total,
    selectedIds,
    allSelected,
    onSelectAll,
    onDeleted,
}: BulkBarProps) {
    const { t } = useI18n();
    const [deleting, setDeleting] = useState(false);
    const checkboxRef = useRef<HTMLInputElement>(null);
    const count = selectedIds.length;

    // 일부만 선택된 상태는 체크박스를 '부분 선택'(-)으로 표시
    useEffect(() => {
        if (checkboxRef.current) {
            checkboxRef.current.indeterminate = count > 0 && !allSelected;
        }
    }, [count, allSelected]);

    if (total === 0) return null;

    const deleteSelected = () => {
        if (count === 0 || deleting) return;
        if (!window.confirm(t('bulkDeleteConfirm', { n: count }))) return;
        setDeleting(true);
        fetch('/api/items/bulk-delete', {
            method: 'POST',
            body: JSON.stringify({ ids: selectedIds }),
            headers: { 'Content-Type': 'application/json' },
        })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP error ${r.status}`);
                onDeleted(selectedIds);
            })
            .catch((err: unknown) =>
                console.error('Failed to delete items:', err),
            )
            .finally(() => setDeleting(false));
    };

    return (
        <div className="bulk-bar">
            <label className="bulk-select-all">
                <input
                    ref={checkboxRef}
                    type="checkbox"
                    className="form-check-input"
                    checked={allSelected}
                    onChange={(e) => onSelectAll(e.target.checked)}
                />
                <span>
                    {t('selectAll')} ({count}/{total})
                </span>
            </label>
            <Button
                size="sm"
                variant="danger"
                disabled={count === 0 || deleting}
                onClick={deleteSelected}
            >
                <FontAwesomeIcon icon={faTrash} /> {t('deleteSelected')}
                {count > 0 ? ` (${count})` : ''}
            </Button>
        </div>
    );
}
