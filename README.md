# Thermalright Digital LCD Driver

A custom Python driver for Thermalright Digital CPU Coolers (e.g., Phantom Spirit 120 EVO Digital). This driver replaces the default software, offering smoother updates, lower resource usage, and a premium "Diagonal Wipe" color animation.

## Features
* **Real-time Monitoring:** Displays CPU Temperature, Usage, and Frequency.
* **Wipe Fill Animation:** Colors paint diagonally from bottom-right to top-left.
* **Live Configuration:** Adjust speed, brightness, and colors instantly without restarting.
* **Portable:** Can run from any directory.
* **Efficient:** Minimal system resource usage.

## Installation

1.  **Clone the repository:**
    (Requires root to write to /opt)
    
        sudo git clone https://github.com/Shajal525/thermalright-ps-120-digital.git /opt/thermalright_led

2.  **Navigate to the directory:**
    
        cd /opt/thermalright_led

3.  **Create a virtual environment:**
    
        sudo apt install python3.13-venv
        python3 -m venv .venv

4.  **Install dependencies:**
    
        sudo .venv/bin/pip install -r requirements.txt

## Manual Testing

Before setting up the background service, test that the driver works manually.

1.  **Run the script (requires sudo):**
    
        sudo .venv/bin/python3 dashboard.py

2.  **Verify the output:**
    * You should see "Connected" in the console.
    * The cooler display should light up and animate.

3.  **Stop the test:**
    * Press `Ctrl+C` to exit.

## Configuration

Customize the driver by editing `config.json` in the script directory. **Changes take effect immediately.**

    {
        "update_interval": 2.0,
        "wipe_speed": 0.01,
        "hue_step": 0.02,
        "brightness": 1.0
    }

### Configuration Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `update_interval` | `2.0` | Seconds between sensor readings. Higher = stable; Lower = responsive. |
| `wipe_speed` | `0.01` | How fast the new color fills the screen. Lower (`0.005`) is slower/smoother. |
| `hue_step` | `0.02` | Color difference for the next fill. Lower = subtle gradient; Higher = distinct colors. |
| `brightness` | `1.0` | Brightness multiplier from `0.0` (Off) to `1.0` (Max). |

## Auto-Start Service

Set up the driver to start automatically with the system.

1.  **Create the service file:**
    
        sudo nano /etc/systemd/system/thermalright-digital.service

2.  **Paste this content:**
    
        [Unit]
        Description=Thermalright Digital LCD Driver
        After=multi-user.target

        [Service]
        Type=simple
        User=root
        WorkingDirectory=/opt/thermalright_led
        ExecStart=/opt/thermalright_led/.venv/bin/python3 /opt/thermalright_led/dashboard.py
        Restart=always
        RestartSec=5

        [Install]
        WantedBy=multi-user.target

3.  **Enable and Start:**
    
        sudo systemctl daemon-reload
        sudo systemctl enable thermalright-digital
        sudo systemctl start thermalright-digital

4.  **Check Status:**
    
        sudo systemctl status thermalright-digital
