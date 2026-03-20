module.exports = {
  AppState: {
    addEventListener: jest.fn(() => ({ remove: jest.fn() })),
    currentState: 'active',
  },
  Platform: { OS: 'ios', select: jest.fn((obj) => obj.ios) },
};
