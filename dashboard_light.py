import hid
import time
import psutil
import sys
import colorsys
import json
import os

# --- PATH CONFIGURATION (DYNAMIC) ---
# This finds the directory where this script is running
# and looks for 'config.json' inside that same folder.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

# HARDWARE CONSTANTS
VENDOR_ID = 0x0416
PRODUCT_ID = 0x8001
NUMBER_OF_LEDS = 84

# DEFAULT SETTINGS
settings = {
    "update_interval": 2.0,
    "wipe_speed": 0.01,
    "hue_step": 0.02,
    "brightness": 1.0
}

def load_config():
    global settings
    try:
        if os.path.exists(CONFIG_FILE):
            # Read Raw File for Debugging
            with open(CONFIG_FILE, 'r') as f:
                content = f.read()
            
            # Parse JSON
            if content.strip():
                new_settings = json.loads(content)
                settings.update(new_settings)
        else:
            # Print error to console if running manually
            sys.stdout.write(f"\n[ERROR] Config NOT found at: {CONFIG_FILE}\n")
            
    except Exception as e:
        sys.stdout.write(f"\n[ERROR] Config Load Failed: {e}\n")

def apply_brightness(hex_color, brightness):
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    r = int(r * brightness)
    g = int(g * brightness)
    b = int(b * brightness)
    
    return f"{min(r,255):02X}{min(g,255):02X}{min(b,255):02X}"

# --- MAPPING COORDINATES ---
led_pos_coords = [0.0] * NUMBER_OF_LEDS
def assign_coords(indices, start_pos, end_pos):
    count = len(indices)
    step = (end_pos - start_pos) / count if count > 1 else 0
    for i, led_idx in enumerate(indices):
        pos = start_pos + (i * step)
        if 0 <= led_idx < NUMBER_OF_LEDS: led_pos_coords[led_idx] = pos

# Zones
assign_coords([7, 6, 5, 4, 3, 2, 1], 0.00, 0.05) 
assign_coords([14, 13, 12, 11, 10, 9, 8], 0.06, 0.12)
assign_coords(list(range(36, 51)), 0.00, 0.15) 
led_pos_coords[0] = 0.05 # Percent

assign_coords([23, 22, 21, 20, 19, 18, 17], 0.35, 0.42)
assign_coords([30, 29, 28, 27, 26, 25, 24], 0.43, 0.50)
assign_coords([37, 36, 35, 34, 33, 32, 31], 0.51, 0.58)
assign_coords([44, 43, 42, 41, 40, 39, 38], 0.59, 0.66)
led_pos_coords[16] = 0.40 # MHz

assign_coords([65, 66, 67, 64, 61, 62, 63], 0.70, 0.78)
assign_coords([57, 58, 60, 56, 53, 54, 55], 0.79, 0.87)
assign_coords([49, 50, 52, 48, 45, 46, 47], 0.88, 0.96)
led_pos_coords[51] = 0.90 # CPU
led_pos_coords[69] = 0.80 # C

# Digits Indices
temp_digits_indices = [[49, 50, 52, 48, 45, 46, 47], [57, 58, 60, 56, 53, 54, 55], [65, 66, 67, 64, 61, 62, 63]]
usage_digits_indices = [[14, 13, 12, 11, 10, 9, 8], [7, 6, 5, 4, 3, 2, 1]]
speed_digits_indices = [[44, 43, 42, 41, 40, 39, 38], [37, 36, 35, 34, 33, 32, 31], [30, 29, 28, 27, 26, 25, 24], [23, 22, 21, 20, 19, 18, 17]]
bar_usage_indices = list(range(36, 51))
digit_shapes = {'0':[1,1,1,0,1,1,1],'1':[0,0,1,0,0,0,1],'2':[0,1,1,1,1,1,0],'3':[0,1,1,1,0,1,1],'4':[1,0,1,1,0,0,1],'5':[1,1,0,1,0,1,1],'6':[1,1,0,1,1,1,1],'7':[0,1,1,0,0,0,1],'8':[1,1,1,1,1,1,1],'9':[1,1,1,1,0,1,1],' ':[0,0,0,0,0,0,0]}

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp-isa-0000' in temps: return temps['coretemp-isa-0000'][0].current
        for key in ['coretemp', 'k10temp', 'cpu_thermal', 'acpitz']:
            if key in temps: return temps[key][0].current
    except: pass
    return 0

def main():
    print(f"Starting Dashboard from {SCRIPT_DIR}...")
    load_config()
    
    last_data_time = 0
    last_config_check = 0
    cached_temp = 0
    cached_usage = 0
    cached_speed = 0
    leds_on_mask = [False] * NUMBER_OF_LEDS
    
    current_hue = 0.0         
    target_hue = settings["hue_step"]
    wipe_progress = 0.0       

    while True:
        try:
            dev = hid.Device(VENDOR_ID, PRODUCT_ID)
            print("\nConnected.")
            
            while True:
                now = time.time()
                
                # 1. CHECK CONFIG
                if now - last_config_check > 2.0:
                    load_config()
                    last_config_check = now

                # 2. DATA UPDATE
                if now - last_data_time > settings["update_interval"]:
                    cached_temp = get_cpu_temp()
                    cached_usage = psutil.cpu_percent()
                    try:
                        f = psutil.cpu_freq()
                        cached_speed = int(f.current) if f else 0
                    except: cached_speed = 0
                    last_data_time = now
                    
                    leds_on_mask = [False] * NUMBER_OF_LEDS
                    t_str = f"{min(int(cached_temp), 199): >3}"
                    for i, c in enumerate(t_str):
                        if c in digit_shapes:
                             for idx, on in enumerate(digit_shapes[c]): 
                                 if on: leds_on_mask[temp_digits_indices[i][idx]] = True
                    u_val = int(cached_usage)
                    if cached_usage > 0 and u_val == 0: u_val = 1
                    u_str = f"{min(u_val, 99):02}"
                    for i, c in enumerate(u_str):
                        if c in digit_shapes:
                            for idx, on in enumerate(digit_shapes[c]):
                                if on: leds_on_mask[usage_digits_indices[i][idx]] = True
                    s_str = f"{min(cached_speed, 9999): >4}"
                    for i, c in enumerate(s_str):
                         if c in digit_shapes:
                             for idx, on in enumerate(digit_shapes[c]):
                                 if on: leds_on_mask[speed_digits_indices[i][idx]] = True
                    u_lit = int((cached_usage / 100.0) * len(bar_usage_indices))
                    for i in range(u_lit): leds_on_mask[bar_usage_indices[i]] = True
                    leds_on_mask[0]=True; leds_on_mask[16]=True; leds_on_mask[51]=True; leds_on_mask[69]=True

                # 3. ANIMATION
                wipe_progress += settings["wipe_speed"]
                if wipe_progress >= 1.2: 
                    wipe_progress = 0.0
                    current_hue = target_hue
                    target_hue = (target_hue + settings["hue_step"]) % 1.0

                r1, g1, b1 = colorsys.hsv_to_rgb(current_hue, 1.0, 1.0)
                base_color_old = f"{int(r1*255):02X}{int(g1*255):02X}{int(b1*255):02X}"
                r2, g2, b2 = colorsys.hsv_to_rgb(target_hue, 1.0, 1.0)
                base_color_new = f"{int(r2*255):02X}{int(g2*255):02X}{int(b2*255):02X}"

                # 4. APPLY BRIGHTNESS
                dim_color_old = apply_brightness(base_color_old, settings["brightness"])
                dim_color_new = apply_brightness(base_color_new, settings["brightness"])

                # 5. ASSIGN
                colors = ["000000"] * NUMBER_OF_LEDS
                for i in range(NUMBER_OF_LEDS):
                    if leds_on_mask[i]:
                        if wipe_progress >= led_pos_coords[i]: colors[i] = dim_color_new
                        else: colors[i] = dim_color_old

                # LOGGING
                sys.stdout.write(f"\rBri: {settings['brightness']} | Color: #{dim_color_new}   ")
                sys.stdout.flush()

                # SEND
                header = 'dadbdcdd000000000000000000000000fc0000ff'
                message = "".join(colors)
                dev.write(bytes.fromhex(header + message[:128-len(header)]))
                payload = message[88:]
                for i in range(4):
                     if payload[i*128 : (i+1)*128]: dev.write(bytes.fromhex('00' + payload[i*128:(i+1)*128]))
                
                time.sleep(0.05)

        except Exception as e:
            print(f"\nWaiting... {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
