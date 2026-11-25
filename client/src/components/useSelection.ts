import { useCallback, useMemo, useState } from 'react';

/**
 * 목록의 체크박스 선택 상태.
 * 화면에 표시 중인 항목(items) 기준으로 계산하므로, 목록에서 사라진 항목은 자동으로 선택에서 빠진다.
 */
export function useSelection(items: { id: string }[]) {
    const [selected, setSelected] = useState<Set<string>>(() => new Set());

    const selectedIds = useMemo(
        () => items.filter((i) => selected.has(i.id)).map((i) => i.id),
        [items, selected],
    );

    const isSelected = useCallback(
        (id: string) => selected.has(id),
        [selected],
    );

    const setOne = useCallback((id: string, checked: boolean) => {
        setSelected((prev) => {
            const next = new Set(prev);
            if (checked) next.add(id);
            else next.delete(id);
            return next;
        });
    }, []);

    // 전체 선택/해제: 현재 화면에 표시된 모든 항목이 대상
    const setAll = useCallback(
        (checked: boolean) =>
            setSelected(checked ? new Set(items.map((i) => i.id)) : new Set()),
        [items],
    );

    const clear = useCallback(() => setSelected(new Set()), []);

    return {
        selectedIds,
        isSelected,
        setOne,
        setAll,
        clear,
        allSelected: items.length > 0 && selectedIds.length === items.length,
    };
}
