---
title: "Ender 3 Max Neo Optimierung"
type: chatgpt_conversation
source: chatgpt
source_id: "67bc1988-de84-8007-87e0-23f2a43df893"
created: 2025-02-24
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# Ender 3 Max Neo Optimierung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67bc1988-de84-8007-87e0-23f2a43df893`
- Nachrichten: 4

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich besitze einen ender 3 max neo. welche Optimierung würdest du bei nachfolgender config vorschlagen. Config: # !Ender-3 Max Neo
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

### 2. Assistent

Hier ein paar Optimierungsvorschläge, die du bei deiner Klipper-Konfiguration für den Ender 3 Max Neo in Betracht ziehen könntest:

1. **BLTouch & Bed Mesh**  
   - **Z-Offset präzise einstellen:** Zwar zeigt der "SAVE_CONFIG"-Block einen z_offset von 2.750 an, jedoch ist es wichtig, diesen Wert mit einem Probe-Kalibrierungsvorgang (z. B. PROBE_CALIBRATE) genau abzustimmen – insbesondere, da die BLTouch-Offsets (x: -32, y: -12) individuell angepasst werden müssen.  
   - **Bed Mesh Bereich überprüfen:** Die definierten Grenzen (mesh_min: 23,25 und mesh_max: 268,288) sollten den tatsächlichen Druckbereich abdecken. Je nach Bettbeschaffenheit kann es hilfreich sein, entweder die Anzahl der Probe-Punkte (aktuell 5x5) oder die Algorithmen-Einstellungen (bicubic) anzupassen.

2. **Input Shaper Einstellungen**  
   - Die aktuell gesetzten Shaper-Parameter (X: ei bei 136.8 Hz, Y: mzv bei 28.6 Hz) sind ein guter Startpunkt, jedoch empfiehlt es sich, einen Resonanztest durchzuführen. Mit dem Ergebnis dieses Tests kannst du die Frequenzen und ggf. den Shaper-Typ für beide Achsen weiter optimieren, um Vibrationen und Ringing zu minimieren.

3. **Extruder & Druckqualität**  
   - **Pressure Advance:** Momentan ist der Wert auf 0.0 gesetzt. Eine gezielte Kalibrierung der Pressure Advance (oder Linear Advance) kann dazu beitragen, Überschüsse und Unterextrusion an Beschleunigungswechseln zu minimieren und so die Druckqualität zu verbessern.  
   - **PID-Tuning:** Auch wenn die PID-Werte für Extruder und Heizbett bereits definiert sind, lohnt sich ein erneutes Autotune – insbesondere, wenn du unterschiedliche Filamenttypen oder Umgebungsbedingungen nutzt.

4. **Makros (PAUSE, RESUME, CANCEL_PRINT)**  
   - Die Makros arbeiten bereits gut mit Parkpositionen und Extrusionsanpassungen. Es könnte sich lohnen, zusätzliche Sicherheitsabfragen oder ein kurzes „Prime“-Kommando nach dem RESUME einzubauen, um sicherzustellen, dass der Filamentfluss wieder optimal ist.  
   - Beim CANCEL_PRINT könnte man über eine kurze Abkühlphase oder ein akustisches Signal nachdenken, falls das sofortige Abschalten der Heizungen für dich von Vorteil ist.

5. **Allgemeine Bewegungs- und Beschleunigungswerte**  
   - Die Einstellungen für max_velocity (300), max_accel (5000) und square_corner_velocity (5.0) sind ambitioniert und orientieren sich am Maximum. Falls du Unregelmäßigkeiten oder Ruckeln bemerkst, könntest du hier experimentell die Beschleunigungswerte etwas reduzieren.  
   - Ebenso könnte es sinnvoll sein, die Homing-Geschwindigkeit (aktuell 80 mm/s für X und Y) im Verhältnis zur mechanischen Stabilität noch einmal zu überprüfen.

6. **Filament-Sensor und weitere Features**  
   - Du hast bereits einen Filament-Sensor definiert (switch_pin: PA4). Es bietet sich an, diesen in ein Runout-Makro zu integrieren, um bei einem Filamentstopp automatisch den Druck zu pausieren und Filamentwechsel zu ermöglichen.

7. **Weitere Einbindung von Konfigurations-Includes**  
   - Da du zusätzliche Konfigurationsdateien (cx_printer.cfg, timelapse.cfg, cx_gmcro.cfg) einbindest, solltest du sicherstellen, dass alle Einstellungen harmonisch zusammenspielen. Insbesondere können dort noch weitere Optimierungsmöglichkeiten oder Sicherheitsfeatures versteckt sein.

Zusammengefasst empfehlen sich also Feintuning-Maßnahmen an den BLTouch- und Mesh-Werten, eine erneute Überprüfung der Input Shaper Parameter, eine Optimierung der Pressure Advance- und PID-Einstellungen sowie Anpassungen bei den Bewegungsparametern. Eine iterative Testphase nach jeder Änderung ist hierbei unerlässlich, um die optimale Druckqualität und Zuverlässigkeit zu gewährleisten.

### 3. Benutzer

extruder auf 215 grad und bed auf 60 grad  festlegen

### 4. Assistent

Um den Extruder auf 215 °C und das Heizbett auf 60 °C einzustellen, kannst du diese Befehle entweder in deinen Start-G-Code in deinem Slicer einfügen oder ein entsprechendes G-Code-Makro in deiner Klipper-Konfiguration definieren. Ein Beispiel für ein Makro könnte folgendermaßen aussehen:

```
[gcode_macro SET_TEMPS]
description: Setze Standardtemperaturen für Extruder und Heizbett
gcode:
  M104 S215   ; Setze Extrudertemperatur auf 215°C
  M140 S60    ; Setze Heizbett auf 60°C
  M109 S215   ; Warte, bis Extrudertemperatur erreicht ist
  M190 S60    ; Warte, bis Heizbetttemperatur erreicht ist
```

Wenn du dieses Makro in deiner Konfiguration einfügst, kannst du es am Anfang eines Drucks einfach mit dem Befehl `SET_TEMPS` aufrufen. Beachte, dass M109 und M190 dafür sorgen, dass der Druck erst startet, wenn die Zieltemperaturen erreicht sind. Alternativ kannst du die entsprechenden Befehle auch direkt in deinem Slicer-Start-G-Code verwenden.
