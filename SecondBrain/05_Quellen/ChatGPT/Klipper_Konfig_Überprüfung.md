---
title: "Klipper Konfig Überprüfung"
type: chatgpt_conversation
source: chatgpt
source_id: "67b83169-c9a4-8007-87cd-fecf77fc2132"
created: 2025-02-21
tags:
  - chatgpt
  - import
  - ki
  - sap
  - verein
---


# Klipper Konfig Überprüfung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67b83169-c9a4-8007-87cd-fecf77fc2132`
- Nachrichten: 8

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

überprüfe die konfig: # printer_size: 300x300x320
# version: 3.6
# This file contains pin mappings for the stock Creality Ender-3 Max Neo 
# To use this config, during "make menuconfig" select the
# STM32F103 with a "28KiB bootloader" and serial (on USART1 PA10/PA9)
# communication.

# If you prefer a direct serial connection, in "make menuconfig"
# select "Enable extra low-level configuration options" and select
# serial (on USART3 PB11/PB10), which is broken out on the 10 pin IDC
# cable used for the LCD module as follows:
# 3: Tx, 4: Rx, 9: GND, 10: VCC

# Flash this firmware by copying "out/klipper.bin" to a SD card and
# turning on the printer with the card inserted. The firmware
# filename must end in ".bin" and must not match the last filename
# that was flashed.

# See docs/Config_Reference.md for a description of parameters.

###fluidd set
[include cx_printer.cfg]

[display_status]

[pause_resume]

[gcode_macro PAUSE]
description: Pause the actual running print
rename_existing: PAUSE_BASE
# change this if you need more or less extrusion
variable_extrude: 1.0
gcode:
  
##### read E from pause macro #####
  {% set E = printer["gcode_macro PAUSE"].extrude|float %}
  
##### set park positon for x and y #####
  
# default is your max posion from your printer.cfg
  {% set x_park = printer.toolhead.axis_maximum.x|float - 5.0 %}
  {% set y_park = printer.toolhead.axis_maximum.y|float - 5.0 %}
  
##### calculate save lift position #####
  {% set max_z = printer.toolhead.axis_maximum.z|float %}
  {% set act_z = printer.toolhead.position.z|float %}
  {% if act_z < (max_z - 2.0) %}
      {% set z_safe = 2.0 %}
  {% else %}
      {% set z_safe = max_z - act_z %}
  {% endif %}
  
##### end of definitions #####
  PAUSE_BASE
  G91
  {% if printer.extruder.can_extrude|lower == 'true' %}
    G1 E-{E} F2100
  {% else %}
    {action_respond_info("Extruder not hot enough")}
  {% endif %}
  {% if "xyz" in printer.toolhead.homed_axes %}
    G1 Z{z_safe} F900
    G90
    G1 X{x_park} Y{y_park} F6000
  {% else %}
    {action_respond_info("Printer not homed")}
  {% endif %}


[gcode_macro RESUME]
description: Resume the actual running print
rename_existing: RESUME_BASE
gcode:
  
##### read E from pause macro #####
  {% set E = printer["gcode_macro PAUSE"].extrude|float %}
  
#### get VELOCITY parameter if specified ####
  {% if 'VELOCITY' in params|upper %}
    {% set get_params = ('VELOCITY=' + params.VELOCITY)  %}
  {%else %}
    {% set get_params = "" %}
  {% endif %}
  
##### end of definitions #####
  {% if printer.extruder.can_extrude|lower == 'true' %}
    G91
    G1 E{E} F2100
  {% else %}
    {action_respond_info("Extruder not hot enough")}
  {% endif %}
  RESUME_BASE {get_params}

[gcode_macro CANCEL_PRINT]
description: Cancel the actual running print
rename_existing: CANCEL_PRINT_BASE
gcode:
  TURN_OFF_HEATERS
  {% if "xyz" in printer.toolhead.homed_axes %}
    G91
    G1 Z4.5 F300
    G90
  {% else %}
    {action_respond_info("Printer not homed")}
  {% endif %}
    G28 X Y
  {% set y_park = printer.toolhead.axis_maximum.y|float - 5.0 %}
    G1 Y{y_park} F2000
    M84
  CANCEL_PRINT_BASE


[stepper_x]
step_pin: PB9
dir_pin: PC2
enable_pin: !PC3
microsteps: 16
rotation_distance: 40
endstop_pin: ^PA5
position_min: -17
position_endstop: -17
position_max: 300 
homing_speed: 50

[stepper_y]
step_pin: PB7
dir_pin: PB8
enable_pin: !PC3
microsteps: 16
rotation_distance: 40
endstop_pin: ^PA6
position_min: 0
position_endstop: 0
position_max: 300 
homing_speed: 50

[stepper_z]
step_pin: PB5
dir_pin: !PB6
enable_pin: !PC3
microsteps: 16
rotation_distance: 8
endstop_pin: probe:z_virtual_endstop  
#enable to use bltouch
# endstop_pin: ^PA7   #disable to use bltouch
# position_endstop: 0.0  #disable to use bltouch
position_max: 340
position_min: -5
homing_speed: 4
second_homing_speed: 1
homing_retract_dist: 2.0

[extruder]
max_extrude_only_distance: 100.0
step_pin: PB3
dir_pin: PB4
enable_pin: !PC3
microsteps: 16
rotation_distance: 31.901
nozzle_diameter: 0.400
filament_diameter: 1.750
heater_pin: PA1
sensor_type: EPCOS 100K B57560G104F
sensor_pin: PC5
control: pid
# tuned for stock hardware with 200 degree Celsius target
pid_Kp: 21.527
pid_Ki: 1.063
pid_Kd: 108.982
min_temp: 0
max_temp: 265

[idle_timeout]
timeout: 172800


[verify_heater extruder]
check_gain_time: 200
hysteresis: 5


[heater_bed]
heater_pin: PA2
sensor_type: EPCOS 100K B57560G104F
sensor_pin: PC4
control: pid
# tuned for stock hardware with 50 degree Celsius target
pid_Kp: 54.027
pid_Ki: .770
pid_Kd: 2948.182
min_temp: 0
max_temp: 130

[fan]
pin: PA0

[fan_generic extruder_partfan]
# pin: PB15
pin: PC6
#max_power:
#shutdown_speed:
#cycle_time:
#hardware_pwm:
#kick_start_time:
#off_below:
#tachometer_pin:
#tachometer_ppr:
#tachometer_poll_interval:
#   See the "fan" section for a description of the above parameters.
#heater: extruder
#   Name of the config section defining the heater that this fan is
#   associated with. If a comma separated list of heater names is
#   provided here, then the fan will be enabled when any of the given
#   heaters are enabled. The default is "extruder".
#heater_temp: 50.0
#   A temperature (in Celsius) that the heater must drop below before
#   the fan is disabled. The default is 50 Celsius.
#fan_speed: 1.0
#   The fan speed (expressed as a value from 0.0 to 1.0) that the fan
#   will be set to when its associated heater is enabled. The default
#   is 1.0


[heater_fan heater_partfan]
pin: PB14
#max_power:
#shutdown_speed:
#cycle_time:
#hardware_pwm:
#kick_start_time:
#off_below:
#tachometer_pin:
#tachometer_ppr:
#tachometer_poll_interval:
#   See the "fan" section for a description of the above parameters.
#heater: extruder
#   Name of the config section defining the heater that this fan is
#   associated with. If a comma separated list of heater names is
#   provided here, then the fan will be enabled when any of the given
#   heaters are enabled. The default is "extruder".
#heater_temp: 50.0
#   A temperature (in Celsius) that the heater must drop below before
#   the fan is disabled. The default is 50 Celsius.
#fan_speed: 1.0
#   The fan speed (expressed as a value from 0.0 to 1.0) that the fan
#   will be set to when its associated heater is enabled. The default
#   is 1.0

[mcu]
serial: /dev/serial/by-id/usb_serial_1
restart_method: command

[printer]
kinematics: cartesian
max_velocity: 300
max_accel: 3000
# max_accel_to_decel: 7000
max_z_velocity: 5
square_corner_velocity: 5.0
max_z_accel: 100



# [mcu rpi]
# serial: /tmp/klipper_host_mcu

# [adxl345]
# cs_pin: rpi:None
# spi_speed: 2000000
# spi_bus: spidev2.0

# [resonance_tester]
# accel_chip: adxl345
# accel_per_hz: 70
# probe_points:
#     117.5,117.5,10

[input_shaper]
shaper_type_x = mzv
shaper_freq_x = 89.8
shaper_type_y = mzv
shaper_freq_y = 35.2

[bltouch]
sensor_pin: ^PB1
control_pin: PB0
x_offset: 50.0
y_offset: -6.0
#z_offset: 0
speed: 10
samples: 3
sample_retract_dist: 5.0
stow_on_each_sample = false 
#high speed for bltoch

[safe_z_home]
home_xy_position: 150,150 
# Change coordinates to the center of your print bed
speed: 100
z_hop: 10               
# Move up 10mm
z_hop_speed: 5

[bed_mesh]
speed: 250
mesh_min: 100,20         
#need to handle head distance with bl_touch
mesh_max: 340,290      
#max probe range
probe_count: 5,5
mesh_pps: 3,3
fade_start: 1
fade_end: 10
fade_target: 0
algorithm: bicubic

[bed_screws]
screw1:30,30
screw1_name:1
screw2:270,30
screw2_name:2
screw3:270,275
screw3_name:3
screw4:30,275
screw4_name:4


[exclude_object]


[gcode_arcs]
#resolution: 1.0

[gcode_macro BED_LEVEL]
gcode:
    G28
    BED_MESH_CALIBRATE


[gcode_macro Z_AXI_CALIBRATE]
gcode:
    G28
    PROBE_CALIBRATE

[gcode_macro SHAPER]
gcode:
    G28
    SHAPER_CALIBRATE

[gcode_macro PID]
gcode:
    G28
    PID_CALIBRATE HEATER=extruder TARGET=200
    PID_CALIBRATE HEATER=heater_bed TARGET=60

[gcode_macro Press_Advance_short]
gcode:
    SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY=1 ACCEL=500
    TUNING_TOWER COMMAND=SET_PRESSURE_ADVANCE PARAMETER=ADVANCE START=0 FACTOR=.005

[gcode_macro Press_Advance_long]
gcode:
    SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY=1 ACCEL=500
    TUNING_TOWER COMMAND=SET_PRESSURE_ADVANCE PARAMETER=ADVANCE START=0 FACTOR=.020


[include timelapse.cfg]
[include cx_gmcro.cfg]

### 2. Assistent

Hier ist eine detaillierte Überprüfung deiner Klipper-Konfiguration:

---

### 1. Allgemeine Kommentare und Include-Befehle
- **Kommentarbereich und Hinweise:**  
  Die initialen Kommentare (z. B. Druckervolumen, Version, Flash-Hinweise) sehen korrekt aus. Sie geben hilfreiche Informationen für die Installation und Auswahl des Bootloaders an.

- **Includes:**  
  Mit `[include cx_printer.cfg]`, `[include timelapse.cfg]` und `[include cx_gmcro.cfg]` werden zusätzliche Konfigurationsdateien eingebunden. Stelle sicher, dass diese Dateien am richtigen Ort liegen und korrekt konfiguriert sind.

---

### 2. G-Code-Makros
- **PAUSE, RESUME, CANCEL_PRINT:**  
  - Die Makros definieren Variablen (z. B. die Extrusion \(E\)) und berechnen Park- sowie sichere Positionen für X, Y und Z.  
  - Die Verwendung von relativen Moves (`G91`) und anschließenden Rückwechseln in den absoluten Modus (`G90`) ist korrekt umgesetzt.  
  - Es werden Zustandsabfragen gemacht (z. B. ob der Extruder heiß genug ist oder ob die Achsen homed sind).  
  - **Hinweis:** Prüfe, ob der Extrusionswert und die Parkpositionen in deiner Druckumgebung wie gewünscht funktionieren – je nach Mechanik können hier Anpassungen nötig sein.

---

### 3. Stepper- und Achseneinstellungen
- **X-Achse:**  
  - Pins, Microsteps und Rotation Distance (40) wirken passend.  
  - Die Endstop-Position (position_min und position_endstop: –17) deutet auf eine Verschiebung des Koordinatensystems hin.  
- **Y-Achse:**  
  - Auch hier sind die Pins und Parameter (position_min: 0, position_max: 300) konsistent.
- **Z-Achse:**  
  - Rotation Distance (8) und die homing Parameter (homing_speed, second_homing_speed, homing_retract_dist) passen zur erwarteten Genauigkeit.  
  - Der virtuelle Endstop (probe:z_virtual_endstop) ermöglicht den Einsatz von Sensoren wie dem BLTouch.
- **Extruder:**  
  - Die Parameter (Rotation Distance, Filament- und Nozzledurchmesser) und PID-Tuningwerte sind für die Stock-Hardware typisch.  
- **Wiederkehrender Enable-Pin:**  
  - Es fällt auf, dass alle Steppers (X, Y, Z und Extruder) denselben `enable_pin: !PC3` verwenden. Dies kann an der Boardkonfiguration liegen – stelle sicher, dass dies mit deinem Hardware-Setup übereinstimmt.

---

### 4. Heizungen, Lüfter und MCU
- **Heizungen:**  
  - Extruder und Heizbett sind mit PID-Regelung versehen. Die angegebenen PID-Werte und Temperaturgrenzen erscheinen im Rahmen des Erwartbaren.  
  - Die „verify_heater“-Sektion für den Extruder dient der Absicherung und ist sinnvoll konfiguriert.
- **Lüfter:**  
  - Der Hauptlüfter (Pin PA0) sowie der „heater_fan“ (Pin PB14) sind definiert.  
  - Es gibt auch eine kommentierte Sektion für einen zusätzlichen, generischen Lüfter – diese kann bei Bedarf aktiviert werden.
- **MCU:**  
  - Der serielle Port `/dev/serial/by-id/usb_serial_1` und der Restart-Method `command` sind richtig angegeben – sofern dein Board auch tatsächlich unter diesem Port erreichbar ist.

---

### 5. Druckereinstellungen und weitere Features
- **Druckerparameter:**  
  - Die kinematischen Einstellungen (Cartesian, max_velocity, max_accel etc.) sind typischerweise für einen Ender-3 Max Neo gewählt.  
- **Input Shaper:**  
  - Die konfigurierten Frequenzen (X: 89.8, Y: 35.2) erscheinen plausibel – hier solltest du jedoch nach Feinabstimmung fragen, falls Schwingungen beobachtet werden.
- **BLTouch und Safe Z Home:**  
  - Die BLTouch-Parameter (Offsets, Anzahl der Samples, Retract-Distanz) sind gesetzt.  
  - Der `safe_z_home`-Abschnitt stellt sicher, dass beim Home-Vorgang die Achse auf eine sichere Höhe gehoben wird.
- **Bed Mesh:**  
  - Die Mesh-Einstellungen (Geschwindigkeit, Probe-Bereich, Anzahl der Proben etc.) sind korrekt formuliert.  
  - **Auffällig:** Die definierten Werte für `mesh_min: 100,20` und `mesh_max: 340,290` weichen etwas von den Schrittgrenzen (z. B. X: –17 bis 300 und Y: 0 bis 300) ab. Dies könnte bedeuten, dass der aktive Druckbereich oder die Referenzkoordinaten verschoben sind. Prüfe, ob diese Werte den tatsächlichen Druckbereich deines Betts abbilden.

---

### 6. Zusammenfassung und Empfehlungen
- **Konfiguration insgesamt:**  
  Die Datei ist größtenteils konsistent und entspricht den typischen Einstellungen für einen Creality Ender-3 Max Neo unter Klipper.
- **Prüfpunkte:**  
  - **Koordinatensystem:** Verifiziere die Verschiebung bei der X-Achse (position_min –17) und ob dies mit den Bed Mesh-Koordinaten (mesh_min und mesh_max) harmoniert.  
  - **Enable-Pin:** Bestätige, dass der gemeinsame `!PC3`-Pin für alle Stepper in deinem Setup korrekt ist.  
  - **BLTouch-Z-Offset:** Falls noch nicht kalibriert, sollte der Z-Offset (derzeit auskommentiert) ermittelt und angepasst werden.
- **Testläufe:**  
  Nach dem Flashen empfiehlt sich ein Testdruck und eine gründliche Überprüfung aller Achsen, Endstops und Sensoren, um sicherzustellen, dass die Einstellungen im Zusammenspiel mit der Mechanik korrekt arbeiten.

---

Falls du weitere Anpassungen oder Fragen zu einzelnen Parametern hast, helfe ich gern weiter.

### 3. Benutzer

bekomme fehler key_335

### 4. Assistent

Der Fehler „key_335“ deutet meist darauf hin, dass Klipper beim Parsen eines Makros auf einen undefinierten oder falsch referenzierten Schlüssel stößt. In deinem Fall fällt besonders der [gcode_macro RESUME] auf, in dem folgender Ausdruck problematisch sein könnte:

```jinja
{% if 'VELOCITY' in params|upper %}
```

**Problematik:**

- **Falsche Anwendung des Filters:**  
  Der Filter `|upper` wird hier auf das ganze Dictionary `params` angewendet. Da `params` ein Dictionary und kein String ist, führt das zu einem Fehler, weil der Filter `upper` für Dictionaries nicht definiert ist.

**Lösungsvorschlag:**

Ändere die Bedingung, sodass du direkt prüfst, ob der Schlüssel `"VELOCITY"` in `params` enthalten ist. Beispielsweise so:

```jinja
{% if 'VELOCITY' in params %}
```

Damit vermeidest du den fehlerhaften Aufruf von `|upper` auf ein Dictionary. Falls du den Wert von `"VELOCITY"` unabhängig von der Groß-/Kleinschreibung prüfen möchtest, kannst du den Schlüssel gleich in der gewünschten Schreibweise übergeben oder den Vergleich anders gestalten.

**Zusätzlicher Hinweis:**  
Stelle sicher, dass alle anderen Makro-Zugriffe (wie das Abfragen von `printer["gcode_macro PAUSE"].extrude`) korrekt sind und auch immer den erwarteten Wert zurückliefern. Falls ein Schlüssel eventuell nicht definiert ist, kann es helfen, Standardwerte mit dem `default`-Filter zu setzen.

Nach dieser Anpassung sollte der Fehler „key_335“ nicht mehr auftreten. Falls er weiterhin besteht, empfiehlt es sich, im Klipper-Logfile nach weiteren Details zu suchen, um zu sehen, ob eventuell ein anderer Bereich der Konfiguration betroffen ist.

### 5. Benutzer

korrigiere den fehler und erstelle mir eine neue konfig

### 6. Assistent

Hier findest du die komplette, korrigierte Konfiguration. Ich habe in der Makro-Definition für **RESUME** den fehlerhaften Filter entfernt – statt  
```jinja
{% if 'VELOCITY' in params|upper %}
```
wird nun einfach geprüft, ob der Schlüssel vorhanden ist.

```ini
# printer_size: 300x300x320
# version: 3.6
# This file contains pin mappings for the stock Creality Ender-3 Max Neo 
# To use this config, during "make menuconfig" select the
# STM32F103 with a "28KiB bootloader" and serial (on USART1 PA10/PA9)
# communication.

# If you prefer a direct serial connection, in "make menuconfig"
# select "Enable extra low-level configuration options" and select
# serial (on USART3 PB11/PB10), which is broken out on the 10 pin IDC
# cable used for the LCD module as follows:
# 3: Tx, 4: Rx, 9: GND, 10: VCC

# Flash this firmware by copying "out/klipper.bin" to a SD card and
# turning on the printer with the card inserted. The firmware
# filename must end in ".bin" and must not match the last filename
# that was flashed.

# See docs/Config_Reference.md for a description of parameters.

###fluidd set
[include cx_printer.cfg]

[display_status]

[pause_resume]

[gcode_macro PAUSE]
description: Pause the actual running print
rename_existing: PAUSE_BASE
# change this if you need more or less extrusion
variable_extrude: 1.0
gcode:
  
##### read E from pause macro #####
  {% set E = printer["gcode_macro PAUSE"].extrude|float %}
  
##### set park positon for x and y #####
  {% set x_park = printer.toolhead.axis_maximum.x|float - 5.0 %}
  {% set y_park = printer.toolhead.axis_maximum.y|float - 5.0 %}
  
##### calculate save lift position #####
  {% set max_z = printer.toolhead.axis_maximum.z|float %}
  {% set act_z = printer.toolhead.position.z|float %}
  {% if act_z < (max_z - 2.0) %}
      {% set z_safe = 2.0 %}
  {% else %}
      {% set z_safe = max_z - act_z %}
  {% endif %}
  
##### end of definitions #####
  PAUSE_BASE
  G91
  {% if printer.extruder.can_extrude|lower == 'true' %}
    G1 E-{E} F2100
  {% else %}
    {action_respond_info("Extruder not hot enough")}
  {% endif %}
  {% if "xyz" in printer.toolhead.homed_axes %}
    G1 Z{z_safe} F900
    G90
    G1 X{x_park} Y{y_park} F6000
  {% else %}
    {action_respond_info("Printer not homed")}
  {% endif %}


[gcode_macro RESUME]
description: Resume the actual running print
rename_existing: RESUME_BASE
gcode:
  
##### read E from pause macro #####
  {% set E = printer["gcode_macro PAUSE"].extrude|float %}
  
#### get VELOCITY parameter if specified ####
  {% if 'VELOCITY' in params %}
    {% set get_params = ('VELOCITY=' + params.VELOCITY)  %}
  {% else %}
    {% set get_params = "" %}
  {% endif %}
  
##### end of definitions #####
  {% if printer.extruder.can_extrude|lower == 'true' %}
    G91
    G1 E{E} F2100
  {% else %}
    {action_respond_info("Extruder not hot enough")}
  {% endif %}
  RESUME_BASE {get_params}

[gcode_macro CANCEL_PRINT]
description: Cancel the actual running print
rename_existing: CANCEL_PRINT_BASE
gcode:
  TURN_OFF_HEATERS
  {% if "xyz" in printer.toolhead.homed_axes %}
    G91
    G1 Z4.5 F300
    G90
  {% else %}
    {action_respond_info("Printer not homed")}
  {% endif %}
    G28 X Y
  {% set y_park = printer.toolhead.axis_maximum.y|float - 5.0 %}
    G1 Y{y_park} F2000
    M84
  CANCEL_PRINT_BASE


[stepper_x]
step_pin: PB9
dir_pin: PC2
enable_pin: !PC3
microsteps: 16
rotation_distance: 40
endstop_pin: ^PA5
position_min: -17
position_endstop: -17
position_max: 300 
homing_speed: 50

[stepper_y]
step_pin: PB7
dir_pin: PB8
enable_pin: !PC3
microsteps: 16
rotation_distance: 40
endstop_pin: ^PA6
position_min: 0
position_endstop: 0
position_max: 300 
homing_speed: 50

[stepper_z]
step_pin: PB5
dir_pin: !PB6
enable_pin: !PC3
microsteps: 16
rotation_distance: 8
endstop_pin: probe:z_virtual_endstop  
#enable to use bltouch
# endstop_pin: ^PA7   #disable to use bltouch
# position_endstop: 0.0  #disable to use bltouch
position_max: 340
position_min: -5
homing_speed: 4
second_homing_speed: 1
homing_retract_dist: 2.0

[extruder]
max_extrude_only_distance: 100.0
step_pin: PB3
dir_pin: PB4
enable_pin: !PC3
microsteps: 16
rotation_distance: 31.901
nozzle_diameter: 0.400
filament_diameter: 1.750
heater_pin: PA1
sensor_type: EPCOS 100K B57560G104F
sensor_pin: PC5
control: pid
# tuned for stock hardware with 200 degree Celsius target
pid_Kp: 21.527
pid_Ki: 1.063
pid_Kd: 108.982
min_temp: 0
max_temp: 265

[idle_timeout]
timeout: 172800


[verify_heater extruder]
check_gain_time: 200
hysteresis: 5


[heater_bed]
heater_pin: PA2
sensor_type: EPCOS 100K B57560G104F
sensor_pin: PC4
control: pid
# tuned for stock hardware with 50 degree Celsius target
pid_Kp: 54.027
pid_Ki: .770
pid_Kd: 2948.182
min_temp: 0
max_temp: 130

[fan]
pin: PA0

[fan_generic extruder_partfan]
# pin: PB15
pin: PC6
#max_power:
#shutdown_speed:
#cycle_time:
#hardware_pwm:
#kick_start_time:
#off_below:
#tachometer_pin:
#tachometer_ppr:
#tachometer_poll_interval:
#   See the "fan" section for a description of the above parameters.
#heater: extruder
#   Name of the config section defining the heater that this fan is
#   associated with. If a comma separated list of heater names is
#   provided here, then the fan will be enabled when any of the given
#   heaters are enabled. The default is "extruder".
#heater_temp: 50.0
#   A temperature (in Celsius) that the heater must drop below before
#   the fan is disabled. The default is 50 Celsius.
#fan_speed: 1.0
#   The fan speed (expressed as a value from 0.0 to 1.0) that the fan
#   will be set to when its associated heater is enabled. The default
#   is 1.0


[heater_fan heater_partfan]
pin: PB14
#max_power:
#shutdown_speed:
#cycle_time:
#hardware_pwm:
#kick_start_time:
#off_below:
#tachometer_pin:
#tachometer_ppr:
#tachometer_poll_interval:
#   See the "fan" section for a description of the above parameters.
#heater: extruder
#   Name of the config section defining the heater that this fan is
#   associated with. If a comma separated list of heater names is
#   provided here, then the fan will be enabled when any of the given
#   heaters are enabled. The default is "extruder".
#heater_temp: 50.0
#   A temperature (in Celsius) that the heater must drop below before
#   the fan is disabled. The default is 50 Celsius.
#fan_speed: 1.0
#   The fan speed (expressed as a value from 0.0 to 1.0) that the fan
#   will be set to when its associated heater is enabled. The default
#   is 1.0

[mcu]
serial: /dev/serial/by-id/usb_serial_1
restart_method: command

[printer]
kinematics: cartesian
max_velocity: 300
max_accel: 3000
# max_accel_to_decel: 7000
max_z_velocity: 5
square_corner_velocity: 5.0
max_z_accel: 100

# [mcu rpi]
# serial: /tmp/klipper_host_mcu

# [adxl345]
# cs_pin: rpi:None
# spi_speed: 2000000
# spi_bus: spidev2.0

# [resonance_tester]
# accel_chip: adxl345
# accel_per_hz: 70
# probe_points:
#     117.5,117.5,10

[input_shaper]
shaper_type_x = mzv
shaper_freq_x = 89.8
shaper_type_y = mzv
shaper_freq_y = 35.2

[bltouch]
sensor_pin: ^PB1
control_pin: PB0
x_offset: 50.0
y_offset: -6.0
#z_offset: 0
speed: 10
samples: 3
sample_retract_dist: 5.0
stow_on_each_sample = false 
#high speed for bltoch

[safe_z_home]
home_xy_position: 150,150 
# Change coordinates to the center of your print bed
speed: 100
z_hop: 10               
# Move up 10mm
z_hop_speed: 5

[bed_mesh]
speed: 250
mesh_min: 100,20         
#need to handle head distance with bl_touch
mesh_max: 340,290      
#max probe range
probe_count: 5,5
mesh_pps: 3,3
fade_start: 1
fade_end: 10
fade_target: 0
algorithm: bicubic

[bed_screws]
screw1:30,30
screw1_name:1
screw2:270,30
screw2_name:2
screw3:270,275
screw3_name:3
screw4:30,275
screw4_name:4

[exclude_object]

[gcode_arcs]
#resolution: 1.0

[gcode_macro BED_LEVEL]
gcode:
    G28
    BED_MESH_CALIBRATE

[gcode_macro Z_AXI_CALIBRATE]
gcode:
    G28
    PROBE_CALIBRATE

[gcode_macro SHAPER]
gcode:
    G28
    SHAPER_CALIBRATE

[gcode_macro PID]
gcode:
    G28
    PID_CALIBRATE HEATER=extruder TARGET=200
    PID_CALIBRATE HEATER=heater_bed TARGET=60

[gcode_macro Press_Advance_short]
gcode:
    SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY=1 ACCEL=500
    TUNING_TOWER COMMAND=SET_PRESSURE_ADVANCE PARAMETER=ADVANCE START=0 FACTOR=.005

[gcode_macro Press_Advance_long]
gcode:
    SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY=1 ACCEL=500
    TUNING_TOWER COMMAND=SET_PRESSURE_ADVANCE PARAMETER=ADVANCE START=0 FACTOR=.020

[include timelapse.cfg]
[include cx_gmcro.cfg]
```

---

**Hinweis:**  
Bitte stelle sicher, dass alle referenzierten Dateien (z. B. `cx_printer.cfg`, `timelapse.cfg` und `cx_gmcro.cfg`) vorhanden und korrekt konfiguriert sind. Teste die Konfiguration vor dem Druck, um sicherzustellen, dass alle Funktionen wie erwartet arbeiten.

### 7. Benutzer

optimiere folgende konfig: # !Ender-3 Max Neo
# printer_size: 300x300x340
# version: 3.6
# This file contains pin mappings for the stock 2020 Creality Ender 3
# MAX. To use this config, during "make menuconfig" select the
# STM32F103 with a "28KiB bootloader" and serial (on USART1 PA10/PA9)
# communication.

# Because this printer has factory wiring, mounts, and firmware for
# a BLTouch, but does not ship with one at this time, default values
# for the sensor have been specified, but disabled, in anticipation of
# future revisions or user modification. User should take care to
# customize the offsets, particularly z-offset, for their specific unit.

# Flash this firmware by copying "out/klipper.bin" to a SD card and
# turning on the printer with the card inserted. The firmware
# filename must end in ".bin" and must not match the last filename
# that was flashed.

# See docs/Config_Reference.md for a description of parameters.

###fluidd set
[include cx_printer.cfg]


[display_status]

[pause_resume]

[gcode_macro PAUSE]
description: Pause the actual running print
rename_existing: PAUSE_BASE
# change this if you need more or less extrusion
variable_extrude: 1.0
gcode:
  ##### read E from pause macro #####
  {% set E = printer["gcode_macro PAUSE"].extrude|float %}
  ##### set park positon for x and y #####
  # default is your max posion from your printer.cfg
  {% set x_park = printer.toolhead.axis_maximum.x|float - 5.0 %}
  {% set y_park = printer.toolhead.axis_maximum.y|float - 5.0 %}
  ##### calculate save lift position #####
  {% set max_z = printer.toolhead.axis_maximum.z|float %}
  {% set act_z = printer.toolhead.position.z|float %}
  {% if act_z < (max_z - 2.0) %}
      {% set z_safe = 2.0 %}
  {% else %}
      {% set z_safe = max_z - act_z %}
  {% endif %}
  ##### end of definitions #####
  PAUSE_BASE
  G91
  {% if printer.extruder.can_extrude|lower == 'true' %}
    G1 E-{E} F2100
  {% else %}
    {action_respond_info("Extruder not hot enough")}
  {% endif %}
  {% if "xyz" in printer.toolhead.homed_axes %}
    G1 Z{z_safe} F900
    G90
    G1 X{x_park} Y{y_park} F6000
  {% else %}
    {action_respond_info("Printer not homed")}
  {% endif %} 

[gcode_macro RESUME]
description: Resume the actual running print
rename_existing: RESUME_BASE
gcode:
  ##### read E from pause macro #####
  {% set E = printer["gcode_macro PAUSE"].extrude|float %}
  #### get VELOCITY parameter if specified ####
  {% if 'VELOCITY' in params|upper %}
    {% set get_params = ('VELOCITY=' + params.VELOCITY)  %}
  {%else %}
    {% set get_params = "" %}
  {% endif %}
  ##### end of definitions #####
  {% if printer.extruder.can_extrude|lower == 'true' %}
    G91
    G1 E{E} F2100
  {% else %}
    {action_respond_info("Extruder not hot enough")}
  {% endif %}  
  RESUME_BASE {get_params}

[gcode_macro CANCEL_PRINT]
description: Cancel the actual running print
rename_existing: CANCEL_PRINT_BASE
gcode:
  TURN_OFF_HEATERS
  {% if "xyz" in printer.toolhead.homed_axes %}
    G91
    G1 Z4.5 F300
    G90
  {% else %}
    {action_respond_info("Printer not homed")}
  {% endif %}
    G28 X Y
  {% set y_park = printer.toolhead.axis_maximum.y|float - 5.0 %}
    G1 Y{y_park} F2000
    M84
  CANCEL_PRINT_BASE

[stepper_x]
step_pin: PC2
dir_pin: PB9
enable_pin: !PC3
microsteps: 16
rotation_distance: 40
endstop_pin: ^PA5
position_endstop: -25
position_max: 300
position_min: -25
homing_speed: 80

[stepper_y]
step_pin: PB8
dir_pin: PB7
enable_pin: !PC3
microsteps: 16
rotation_distance: 40
endstop_pin: ^PA6
position_endstop: 0
position_max: 300
homing_speed: 80

[stepper_z]
step_pin: PB6
dir_pin: !PB5
enable_pin: !PC3
microsteps: 16
rotation_distance: 8
# position_endstop: 0.0                     # disable to use BLTouch
# endstop_pin: ^PA7                         # disable to use BLTouch
endstop_pin: probe:z_virtual_endstop    # enable to use BLTouch
position_min: -5                        # enable to use BLTouch
position_max: 345

[safe_z_home]                         # enable for BLTouch
home_xy_position: 182, 167
speed: 200
z_hop: 5
z_hop_speed: 5

[bltouch]                             # enable for BLTouch - fast-mode
sensor_pin: ^PB1
control_pin: PB0
x_offset: -32                          # modify as needed for bltouch location
y_offset: -12                          # modify as needed for bltouch location
#z_offset: 0.0                          # modify as needed for bltouch or run PROBE_CALIBRATE
speed: 20
pin_up_touch_mode_reports_triggered: False

[bed_mesh]                            # enable for BLTouch
speed: 150
mesh_min: 23, 25
mesh_max: 268, 288
algorithm: bicubic
probe_count: 5,5                     
horizontal_move_z: 5

[idle_timeout]
timeout: 172800

[bed_screws]
screw1:30,25
screw1_name:1
screw2:270,25
screw2_name:2
screw3:270,270
screw3_name:3
screw4:30,270
screw4_name:4

[extruder]
max_extrude_only_distance: 1000.0
step_pin: PB4
dir_pin: PB3
enable_pin: !PC3
microsteps: 16
rotation_distance: 31.901           
nozzle_diameter: 0.400
filament_diameter: 1.750
heater_pin: PA1
sensor_type: EPCOS 100K B57560G104F
sensor_pin: PC5
control: pid
pid_Kp: 21.527
pid_Ki: 1.063
pid_Kd: 108.982
min_temp: 0
max_temp: 265
pressure_advance: 0.0               

[heater_bed]
heater_pin: PA2
sensor_type: EPCOS 100K B57560G104F
sensor_pin: PC4
control: pid
pid_Kp: 54.027
pid_Ki: 0.770
pid_Kd: 948.182
min_temp: 0
max_temp: 130

[fan]
pin: PA0

[fan_generic extruder_partfan]
pin: PC6

# [mcu rpi]
# serial: /tmp/klipper_host_mcu

# [adxl345]
# cs_pin: rpi:None
# spi_speed: 2000000
# spi_bus: spidev2.0

# [resonance_tester]
# accel_chip: adxl345
# accel_per_hz: 70
# probe_points:
#      150,150,10

[input_shaper]
shaper_type_x = ei
shaper_freq_x = 136.8
shaper_type_y = mzv
shaper_freq_y = 28.6

[filament_switch_sensor filament_sensor]
switch_pin: PA4

[mcu]
serial: /dev/serial/by-id/usb_serial_1
restart_method: command

[printer]
kinematics: cartesian
max_velocity: 300
max_accel: 5000
max_z_velocity: 10
max_z_accel: 1000
square_corner_velocity: 5.0

[exclude_object]


[gcode_arcs]
#resolution: 1.0


[include timelapse.cfg]
[include cx_gmcro.cfg]

#*# <---------------------- SAVE_CONFIG ---------------------->
#*# DO NOT EDIT THIS BLOCK OR BELOW. The contents are auto-generated.
#*#
#*# [bltouch]
#*# z_offset = 2.750
#*#
#*# [bed_mesh default]
#*# version = 1
#*# points =
#*# 	-0.275000, -0.037500, 0.137500, 0.325000, 0.520000
#*# 	-0.067500, 0.000000, 0.055000, 0.147500, 0.277500
#*# 	-0.092500, -0.020000, -0.007500, 0.047500, 0.147500
#*# 	0.102500, 0.065000, 0.025000, 0.047500, 0.097500
#*# 	0.450000, 0.292500, 0.162500, 0.110000, 0.067500
#*# x_count = 5
#*# y_count = 5
#*# mesh_x_pps = 2
#*# mesh_y_pps = 2
#*# algo = bicubic
#*# tension = 0.2
#*# min_x = 23.0
#*# max_x = 268.0
#*# min_y = 25.0
#*# max_y = 288.0

### 8. Assistent

Hier folgt eine optimierte Version deiner Konfiguration. Dabei wurden folgende Verbesserungen vorgenommen:

- **Fehler im RESUME-Makro behoben:**  
  Es wurde der Aufruf `params|upper` entfernt – nun wird direkt geprüft, ob der Schlüssel `'VELOCITY'` in `params` vorhanden ist.

- **Konsistente Formatierung und Kommentare:**  
  Einige Kommentare und Abstände wurden vereinheitlicht, sodass die Datei leichter lesbar und übersichtlich ist.

- **Gruppierung der Einstellungen:**  
  Die Bereiche (Makros, Achsen, BLTouch, Heizungen etc.) sind logisch gegliedert, um spätere Anpassungen zu erleichtern.

---

Hier die optimierte Konfiguration:

```ini
# !Ender-3 Max Neo
# printer_size: 300x300x340
# version: 3.6
# Diese Konfiguration enthält die Pin-Mappings für den stock 2020 Creality Ender 3 MAX.
# Für die Nutzung wähle in "make menuconfig" den STM32F103 mit "28KiB bootloader" und serielle Kommunikation (USART1 PA10/PA9).
#
# Hinweis: Da der Drucker werkseitig für einen BLTouch ausgelegt ist, sind Standardwerte
# für den Sensor angegeben – diese müssen ggf. an deine Einheit angepasst werden.
#
# Flashen: Kopiere "out/klipper.bin" auf eine SD-Karte, stecke diese ein und starte den Drucker.
# Die Firmware-Datei muss auf ".bin" enden und darf nicht den zuletzt verwendeten Dateinamen tragen.
#
# Siehe docs/Config_Reference.md für Parameterbeschreibungen.

###fluidd set
[include cx_printer.cfg]

[display_status]
[pause_resume]

#########################################################################
# G-Code-Makros
#########################################################################

[gcode_macro PAUSE]
description: Pausiert den aktuell laufenden Druck
rename_existing: PAUSE_BASE
variable_extrude: 1.0   # Passe diesen Wert ggf. an, wenn mehr/ weniger Extrusion nötig ist
gcode:
  ##### Lese den Extrusionswert aus dem PAUSE-Makro #####
  {% set E = printer["gcode_macro PAUSE"].extrude|float %}
  ##### Berechne Parkposition für X und Y (Standard: max. Position - 5mm) #####
  {% set x_park = printer.toolhead.axis_maximum.x|float - 5.0 %}
  {% set y_park = printer.toolhead.axis_maximum.y|float - 5.0 %}
  ##### Berechne sichere Hubposition für Z #####
  {% set max_z = printer.toolhead.axis_maximum.z|float %}
  {% set act_z = printer.toolhead.position.z|float %}
  {% if act_z < (max_z - 2.0) %}
      {% set z_safe = 2.0 %}
  {% else %}
      {% set z_safe = max_z - act_z %}
  {% endif %}
  ##### Ausführung des Pause-Befehls #####
  PAUSE_BASE
  G91
  {% if printer.extruder.can_extrude|lower == 'true' %}
    G1 E-{E} F2100
  {% else %}
    {action_respond_info("Extruder not hot enough")}
  {% endif %}
  {% if "xyz" in printer.toolhead.homed_axes %}
    G1 Z{z_safe} F900
    G90
    G1 X{x_park} Y{y_park} F6000
  {% else %}
    {action_respond_info("Printer not homed")}
  {% endif %}

[gcode_macro RESUME]
description: Setzt den pausierten Druck fort
rename_existing: RESUME_BASE
gcode:
  ##### Lese den Extrusionswert aus dem PAUSE-Makro #####
  {% set E = printer["gcode_macro PAUSE"].extrude|float %}
  ##### Prüfe, ob der VELOCITY-Parameter angegeben wurde #####
  {% if 'VELOCITY' in params %}
    {% set get_params = ('VELOCITY=' + params.VELOCITY) %}
  {% else %}
    {% set get_params = "" %}
  {% endif %}
  ##### Fortsetzung des Drucks #####
  {% if printer.extruder.can_extrude|lower == 'true' %}
    G91
    G1 E{E} F2100
  {% else %}
    {action_respond_info("Extruder not hot enough")}
  {% endif %}
  RESUME_BASE {get_params}

[gcode_macro CANCEL_PRINT]
description: Bricht den laufenden Druck ab
rename_existing: CANCEL_PRINT_BASE
gcode:
  TURN_OFF_HEATERS
  {% if "xyz" in printer.toolhead.homed_axes %}
    G91
    G1 Z4.5 F300
    G90
  {% else %}
    {action_respond_info("Printer not homed")}
  {% endif %}
  G28 X Y
  {% set y_park = printer.toolhead.axis_maximum.y|float - 5.0 %}
  G1 Y{y_park} F2000
  M84
  CANCEL_PRINT_BASE

#########################################################################
# Achsen und Stepper-Einstellungen
#########################################################################

[stepper_x]
step_pin: PC2
dir_pin: PB9
enable_pin: !PC3
microsteps: 16
rotation_distance: 40
endstop_pin: ^PA5
position_endstop: -25
position_min: -25
position_max: 300
homing_speed: 80

[stepper_y]
step_pin: PB8
dir_pin: PB7
enable_pin: !PC3
microsteps: 16
rotation_distance: 40
endstop_pin: ^PA6
position_endstop: 0
position_max: 300
homing_speed: 80

[stepper_z]
step_pin: PB6
dir_pin: !PB5
enable_pin: !PC3
microsteps: 16
rotation_distance: 8
# Für BLTouch: Verwende den virtuellen Endstop
endstop_pin: probe:z_virtual_endstop
position_min: -5
position_max: 345

#########################################################################
# BLTouch, Safe Z Home & Bed Mesh
#########################################################################

[safe_z_home]
home_xy_position: 182,167   # Anpassen, falls der tatsächliche Druckbereich abweicht
speed: 200
z_hop: 5
z_hop_speed: 5

[bltouch]
sensor_pin: ^PB1
control_pin: PB0
x_offset: -32        # Anpassen je nach Montage
y_offset: -12        # Anpassen je nach Montage
# z_offset: 0.0      # Nach Bedarf kalibrieren oder per PROBE_CALIBRATE ermitteln
speed: 20
pin_up_touch_mode_reports_triggered: False

[bed_mesh]
speed: 150
mesh_min: 23,25
mesh_max: 268,288
algorithm: bicubic
probe_count: 5,5
horizontal_move_z: 5

#########################################################################
# Extruder, Heizungen und Lüfter
#########################################################################

[extruder]
max_extrude_only_distance: 1000.0
step_pin: PB4
dir_pin: PB3
enable_pin: !PC3
microsteps: 16
rotation_distance: 31.901
nozzle_diameter: 0.400
filament_diameter: 1.750
heater_pin: PA1
sensor_type: EPCOS 100K B57560G104F
sensor_pin: PC5
control: pid
pid_Kp: 21.527
pid_Ki: 1.063
pid_Kd: 108.982
min_temp: 0
max_temp: 265
pressure_advance: 0.0

[heater_bed]
heater_pin: PA2
sensor_type: EPCOS 100K B57560G104F
sensor_pin: PC4
control: pid
pid_Kp: 54.027
pid_Ki: 0.770
pid_Kd: 948.182
min_temp: 0
max_temp: 130

[fan]
pin: PA0

[fan_generic extruder_partfan]
pin: PC6

#########################################################################
# Weitere Einstellungen
#########################################################################

[input_shaper]
shaper_type_x = ei
shaper_freq_x = 136.8
shaper_type_y = mzv
shaper_freq_y = 28.6

[filament_switch_sensor filament_sensor]
switch_pin: PA4

[mcu]
serial: /dev/serial/by-id/usb_serial_1
restart_method: command

[printer]
kinematics: cartesian
max_velocity: 300
max_accel: 5000
max_z_velocity: 10
max_z_accel: 1000
square_corner_velocity: 5.0

[exclude_object]

[gcode_arcs]
#resolution: 1.0

[include timelapse.cfg]
[include cx_gmcro.cfg]

#*# <---------------------- SAVE_CONFIG ---------------------->
#*# DO NOT EDIT THIS BLOCK OR BELOW. The contents are auto-generated.
#*#
#*# [bltouch]
#*# z_offset = 2.750
#*#
#*# [bed_mesh default]
#*# version = 1
#*# points =
#*#   -0.275000, -0.037500, 0.137500, 0.325000, 0.520000
#*#   -0.067500, 0.000000, 0.055000, 0.147500, 0.277500
#*#   -0.092500, -0.020000, -0.007500, 0.047500, 0.147500
#*#   0.102500, 0.065000, 0.025000, 0.047500, 0.097500
#*#   0.450000, 0.292500, 0.162500, 0.110000, 0.067500
#*# x_count = 5
#*# y_count = 5
#*# mesh_x_pps = 2
#*# mesh_y_pps = 2
#*# algo = bicubic
#*# tension = 0.2
#*# min_x = 23.0
#*# max_x = 268.0
#*# min_y = 25.0
#*# max_y = 288.0
```

---

**Anmerkungen:**  
- Passe die BLTouch-Offsets (x_offset, y_offset, ggf. z_offset) exakt an deine Hardware an.  
- Überprüfe insbesondere die Koordinaten im Bereich „safe_z_home“ und „bed_mesh“, um sicherzustellen, dass diese zu deinem tatsächlichen Druckbett passen.  
- Teste die Änderungen nach Möglichkeit zuerst in einer sicheren Umgebung (z. B. mit nur manuellen Bewegungen), bevor du einen Druck startest.

Falls weitere Anpassungen oder Fragen auftreten, helfe ich gern weiter.
