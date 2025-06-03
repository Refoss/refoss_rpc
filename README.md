# refoss_rpc
- Home Assistant version: 2025.2.5 or above.
- Integrate Refoss devices that support `RPC` protocol into Home Assistant.

## Installation

### Custom Repositories in HACS (recommended)
- Make sure the [HACS integration](https://hacs.xyz/) is properly installed for your instance of home assistant.
- Reference [Custom Repositories](https://hacs.xyz/docs/faq/custom_repositories),In the HACS UI go to "Integrations", click on "+" in the lower right corner".
- Paste https://github.com/Refoss/refoss_rpc into the field that says "Add custom repository URL", select "Integration" from "Category" dropdown and click "Add".
- You should now see a card with the Refoss RPC integration in the HACS -> "Integrations" section. Click "Install".
- Select the latest version from the dropdown and click "Install".
- Restart Home Assistant.

### Manual installation
- Using the tool of choice open the directory for your HA configuration (where you find configuration.yaml).
- If you do not have a custom_components directory there, you need to create it.
- In releases(https://github.com/Refoss/refoss_rpc/releases), download the version you need.
- In the downloaded file, locate the refoss_rpc directory and copy it to the custom_components directory.
- Restart Home Assistant.

## Configuration
- In the HA UI go to "Configuration" -> "Integrations", click "+", search for "Refoss RPC", and select the "Refoss RPC" integration from the list.
  Or click here: [![Start Config Flow](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=refoss_rpc)

## Supported device models

| Model                            | Version            |             
|----------------------------------|--------------------|
| `Refoss Smart Wi-Fi Switch, R11` | `all`              |
| `Refoss Smart Wi-Fi Plug, P11S`  | `all`              |

## Binary input sensors

It's possible to select if a device's input is connected to a button or a switch. Binary sensors are created only if the input mode is set to `switch`. When the input mode is set to `button` you can use events for your automations.

## Events

If device's input mode is set to `button`, integration fires events under the type `refoss.click` when the switch is used. You can use these events in your automations.

### Automations

The simplest way to create automations is to use the Home Assistant automation editor. For example, to set an automation triggered by a double press of a particular R11 Button1:

1. In the Triggers section of the automation, set Trigger Type to `Device`.
2. In the Device dropdown menu. find the R11.
3. In the Trigger dropdown menu, select `Button1 double push`.
4. Set any conditions and actions to complete your automation.

### Possible values for `click_type`

Devices use the values `btn_down`, `btn_up`, `single_push`, `double_push`, `triple_push` and `long_push` as `click_type`.

## Device actions

The integration offers device actions which can be triggered by a configuration button.

### Firmware update

Trigger device firmware update.

### Check latest firmware

Trigger check latest firmware of device.

### Reboot

Trigger reboot of device.