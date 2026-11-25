import Badge from 'react-bootstrap/Badge';
import { useI18n } from '../i18nContext';
import { CATEGORY_COLORS } from './categories';
import type { Category, Priority } from './ItemDisplay';

const PRIORITY_COLORS: Record<Priority, string> = {
    high: 'danger',
    medium: 'warning',
    low: 'success',
};

/** 분류/우선순위 배지 (현재 언어로 표시) */
export function ItemTags({
    category,
    priority,
}: {
    category?: Category | null;
    priority?: Priority | null;
}) {
    const { t } = useI18n();
    return (
        <>
            {category && (
                <Badge bg={CATEGORY_COLORS[category]}>
                    {t(`category.${category}`)}
                </Badge>
            )}
            {priority && (
                <Badge
                    bg={PRIORITY_COLORS[priority]}
                    text={priority === 'medium' ? 'dark' : undefined}
                >
                    {t('priorityPrefix')} {t(`priority.${priority}`)}
                </Badge>
            )}
        </>
    );
}
