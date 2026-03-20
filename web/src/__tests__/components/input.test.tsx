import { render, screen } from '@testing-library/react';
import Input from '@/components/ui/input';

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('renders without label', () => {
    render(<Input placeholder="Type here" />);
    expect(screen.getByPlaceholderText('Type here')).toBeInTheDocument();
  });

  it('shows error message', () => {
    render(<Input label="Name" error="Required field" />);
    expect(screen.getByText('Required field')).toBeInTheDocument();
  });

  it('applies error styling', () => {
    render(<Input label="Name" error="Oops" />);
    const input = screen.getByLabelText('Name');
    expect(input.className).toContain('border-red-300');
  });

  it('generates id from label', () => {
    render(<Input label="Full Name" />);
    const input = screen.getByLabelText('Full Name');
    expect(input.id).toBe('full-name');
  });

  it('uses provided id over generated', () => {
    render(<Input label="Email" id="custom-id" />);
    const input = screen.getByLabelText('Email');
    expect(input.id).toBe('custom-id');
  });

  it('passes through HTML attributes', () => {
    render(<Input label="Phone" type="tel" required />);
    const input = screen.getByLabelText('Phone');
    expect(input).toHaveAttribute('type', 'tel');
    expect(input).toBeRequired();
  });
});
