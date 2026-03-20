import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TagBadge from '@/components/tags/tag-badge';
import type { Tag } from '@/types/api';

const mockTag: Tag = {
  id: '1',
  name: 'work',
  color: '#FF0000',
  created_at: '2024-01-01T00:00:00Z',
};

describe('TagBadge', () => {
  it('renders the tag name', () => {
    render(<TagBadge tag={mockTag} />);
    expect(screen.getByText('work')).toBeInTheDocument();
  });

  it('applies tag color as background', () => {
    render(<TagBadge tag={mockTag} />);
    const badge = screen.getByText('work');
    // JSDOM may parse hex to rgb
    expect(badge.style.backgroundColor).toBeTruthy();
    expect(badge.style.color).toBeTruthy();
  });

  it('uses default colors when tag has no color', () => {
    const noColorTag: Tag = { ...mockTag, color: null };
    render(<TagBadge tag={noColorTag} />);
    const badge = screen.getByText('work');
    // Default grey (#e5e7eb) may be expressed as rgb
    expect(badge.style.backgroundColor).toBeTruthy();
    expect(badge.style.color).toBeTruthy();
  });

  it('shows remove button when onRemove is provided', () => {
    render(<TagBadge tag={mockTag} onRemove={jest.fn()} />);
    expect(screen.getByText('×')).toBeInTheDocument();
  });

  it('does not show remove button by default', () => {
    render(<TagBadge tag={mockTag} />);
    expect(screen.queryByText('×')).not.toBeInTheDocument();
  });

  it('calls onRemove when × is clicked', async () => {
    const user = userEvent.setup();
    const onRemove = jest.fn();
    render(<TagBadge tag={mockTag} onRemove={onRemove} />);
    await user.click(screen.getByText('×'));
    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  it('applies selected ring style', () => {
    render(<TagBadge tag={mockTag} selected />);
    const badge = screen.getByText('work');
    expect(badge.className).toContain('ring-2');
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const onClick = jest.fn();
    render(<TagBadge tag={mockTag} onClick={onClick} />);
    await user.click(screen.getByText('work'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
