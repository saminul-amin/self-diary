# Maestro E2E Tests for SelfDiary Mobile

These YAML flow definitions are designed for [Maestro](https://maestro.mobile.dev/)
— a declarative mobile UI testing framework.

## Prerequisites

1. Install Maestro: `curl -Ls https://get.maestro.mobile.dev | bash`
2. Start the backend: `cd backend && make run`
3. Run the Expo dev server: `cd mobile && npx expo start`
4. Launch on a simulator/emulator

## Running Tests

```bash
# Run a single flow
maestro test maestro/01-register.yaml

# Run the full suite in order
maestro test maestro/
```

## Flow Order

The flows are numbered and designed to run sequentially:

| #   | Flow         | Description                         |
| --- | ------------ | ----------------------------------- |
| 01  | Register     | Create a new account                |
| 02  | Login        | Sign in with registered credentials |
| 03  | Create Entry | Create a diary entry with mood      |
| 04  | Search Entry | Search and find the created entry   |
| 05  | Edit Entry   | Update the entry title and body     |
| 06  | Delete Entry | Delete the entry                    |
| 07  | Sign Out     | Log out from settings               |
