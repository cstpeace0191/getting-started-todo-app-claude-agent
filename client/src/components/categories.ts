import type { Category } from './ItemDisplay';

export const CATEGORIES: Category[] = ['study', 'work', 'personal'];

export const CATEGORY_COLORS: Record<Category, string> = {
    study: 'primary',
    work: 'info',
    personal: 'secondary',
};
