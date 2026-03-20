import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MoodSelector from '@/components/entries/mood-selector';

describe('MoodSelector', () => {
  const moods = ['great', 'good', 'neutral', 'bad', 'terrible'] as const;

  it('renders all five mood buttons', () => {
    render(<MoodSelector value={null} onChange={jest.fn()} />);
    for (const mood of moods) {
      expect(screen.getByTitle(mood)).toBeInTheDocument();
    }
  });

  it('highlights the selected mood', () => {
    render(<MoodSelector value="good" onChange={jest.fn()} />);
    const selected = screen.getByTitle('good');
    expect(selected.className).toContain('ring-2');
  });

  it('calls onChange when a mood is clicked', async () => {
    const user = userEvent.setup();
    const onChange = jest.fn();
    render(<MoodSelector value={null} onChange={onChange} />);
    await user.click(screen.getByTitle('great'));
    expect(onChange).toHaveBeenCalledWith('great');
  });

  it('deselects when clicking the already-selected mood', async () => {
    const user = userEvent.setup();
    const onChange = jest.fn();
    render(<MoodSelector value="neutral" onChange={onChange} />);
    await user.click(screen.getByTitle('neutral'));
    expect(onChange).toHaveBeenCalledWith(null);
  });
});
