[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

# Refoss RPC

Integrate Refoss devices that support the `RPC` protocol into Home Assistant.

**Requirements**: Home Assistant 2025.2.5 or above.

## Installation

### Option A: Via HACS

1. Search for **"Refoss RPC"** in the HACS default repository.
2. Click **Install**.
3. Restart Home Assistant.
4. Proceed to [Configuration](#configuration).

### Option B: Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/Refoss/refoss_rpc/releases/latest).
2. Copy the `refoss_rpc` folder into the `custom_components` directory of your Home Assistant configuration directory (where `configuration.yaml` is located).

   ```
   ~/.homeassistant/
   ├── configuration.yaml
   ├── secrets.yaml
   └── custom_components/
       └── refoss_rpc/
           ├── __init__.py
           ├── entity.py
           ├── switch.py
           └── ...
   ```

3. Restart Home Assistant.
4. Proceed to [Configuration](#configuration).

## Configuration

1. Navigate to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **"Refoss RPC"** and select it from the list.
3. Follow the setup wizard.

Or click here: [![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=refoss_rpc)

## Supported Devices

| Model | Version |
|-------|---------|
| Refoss Smart Wi-Fi Switch, R11 | All |
| Refoss Smart Wi-Fi Plug, P11S | All |
| Refoss Smart Wi-Fi Switch, R21 | All |
| Refoss Smart Energy Monitor, EM06P | All |
| Refoss Smart Energy Monitor, EM16P | All |
| Refoss Smart Energy Monitor, EM01P | All |
