#!/usr/bin/env python3
"""
tdot_pi.py - TdoT-Demo, Teil am Raspberry Pi (Spulenteststand, Diplomarbeit HTL Hollabrunn)

Abgespeckte Version: NUR manuelles Anfahren + Demo-Dauerlauf.
  * KEINE Referenzfahrt (G28) - der Messarm ist montiert und wuerde ins Bett fahren.
  * KEIN Sensor, KEIN Netzteil - die angezeigten Messwerte sind erfunden.

Wird vom PC-Programm tdot_demo.py per SSH hochgeladen und gestartet.
Befehle kommen zeilenweise ueber stdin:
  MOVE dx dy dz                      relative Fahrt in mm
  POS                                Position abfragen
  DEMO x1 x2 y1 y2 schritt z         Dauerlauf im Rechteck (Ende nur mit Strg+C / SIGINT)
  QUIT                               beenden
Ausgaben: STATUS:<text>, POS:x,y,z, DATA:x,y,z,bx,by,bz,b
"""
import sys, os, re, time, glob, math, random, signal, subprocess
import serial

PORT = None
printer = None


def find_port():
    """Nur Drucker angesteckt -> meist /dev/ttyUSB0, mit Netzteil oft /dev/ttyUSB1."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    ports = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
    if not ports:
        raise RuntimeError("Kein Drucker-Port gefunden (USB-Kabel Drucker <-> Pi pruefen).")
    if len(ports) > 1:
        print(f"STATUS:Mehrere Ports {ports}, nehme den letzten.", flush=True)
    return ports[-1]


def send(cmd, timeout=35):
    printer.write((cmd + "\n").encode("ascii"))
    printer.flush()
    t0 = time.time()
    lines = []
    while time.time() - t0 < timeout:
        line = printer.readline().decode(errors="ignore").strip()
        if not line:
            continue
        if line.startswith("ok"):
            return lines
        lines.append(line)
    return lines


def position():
    for line in send("M114", timeout=5):
        m = re.search(r"X:\s*(-?[\d.]+)\s*Y:\s*(-?[\d.]+)\s*Z:\s*(-?[\d.]+)", line)
        if m:
            return [float(m.group(i)) for i in (1, 2, 3)]
    return None


def report():
    p = position()
    if p:
        print(f"POS:{p[0]:.2f},{p[1]:.2f},{p[2]:.2f}", flush=True)


def stop(sig=None, frame=None):
    """Abbruch: Duese 10 mm hoch, Port zu."""
    if printer and printer.is_open:
        try:
            printer.timeout = 2.0
            send("G91", 3); send("G1 Z10 F1000", 3); send("G90", 3); send("M400", 15)
            printer.close()
        except Exception:
            pass
    print("STATUS:Gestoppt, Duese 10 mm angehoben.", flush=True)
    os._exit(0)


def fake_field(x, y, cx, cy):
    r2 = (x - cx) ** 2 + (y - cy) ** 2
    bz = 3.0 * math.exp(-r2 / (2 * 22.0 ** 2)) + random.gauss(0, 0.03)
    bx = 0.05 * (x - cx) * math.exp(-r2 / (2 * 30.0 ** 2)) + random.gauss(0, 0.03)
    by = 0.05 * (y - cy) * math.exp(-r2 / (2 * 30.0 ** 2)) + random.gauss(0, 0.03)
    return bx, by, bz, math.sqrt(bx * bx + by * by + bz * bz)


def steps(a, b, d):
    a, b = min(a, b), max(a, b)
    vals, v = [], a
    while v <= b + 0.001:
        vals.append(round(v, 2))
        v += d
    return vals


def demo(x1, x2, y1, y2, step, z):
    xs, ys = steps(x1, x2, step), steps(y1, y2, step)
    path = []
    for i, y in enumerate(ys):
        path += [(x, y) for x in (xs if i % 2 == 0 else xs[::-1])]
    loop = path + path[-2:0:-1]          # hin und zurueck -> kein Sprung
    cx, cy = (xs[0] + xs[-1]) / 2, (ys[0] + ys[-1]) / 2
    print(f"STATUS:Demo laeuft: {len(xs)} x {len(ys)} Punkte, Hoehe Z={z:.1f} mm", flush=True)
    send(f"G1 Z{z:.2f} F600"); send("M400", 60)
    runde = 0
    while True:
        runde += 1
        print(f"STATUS:Demo-Runde {runde}", flush=True)
        for (x, y) in loop:
            send(f"G1 X{x:.2f} Y{y:.2f} F3500")
            send("M400", 60)
            time.sleep(0.6)               # "Messung"
            bx, by, bz, b = fake_field(x, y, cx, cy)
            print(f"DATA:{x:.2f},{y:.2f},{z:.2f},{bx:.3f},{by:.3f},{bz:.3f},{b:.3f}", flush=True)


def main():
    global printer, PORT
    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, stop)
    PORT = find_port()
    # Port oeffnen OHNE den Drucker neu zu starten (DTR aus)
    subprocess.run(["stty", "-F", PORT, "-hupcl"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    printer = serial.Serial()
    printer.port, printer.baudrate, printer.timeout = PORT, 115200, 0.5
    printer.dtr = False
    printer.rts = False
    printer.open()
    t0 = time.time()
    while time.time() - t0 < 3:           # Startmeldungen abwarten
        printer.readline()
    printer.timeout = 2.0
    printer.reset_input_buffer()
    send("G21"); send("G90"); send("M83")
    send("M211 S0")   # Software-Endschalter aus (ohne Referenzfahrt sonst evtl. keine Fahrt in Minus-Richtung)
    send("M84 S0")    # Motoren bleiben an, sonst gehen die Ecken verloren
    print(f"STATUS:Bereit (Port {PORT}). Keine Referenzfahrt!", flush=True)
    report()

    for line in iter(sys.stdin.readline, ""):
        p = line.split()
        if not p:
            continue
        c = p[0].upper()
        try:
            if c == "QUIT":
                break
            elif c == "POS":
                report()
            elif c == "MOVE" and len(p) == 4:
                dx, dy, dz = [max(-100.0, min(100.0, float(v))) for v in p[1:]]
                send("G91")
                if dz:
                    send(f"G1 Z{dz:.2f} F600")
                if dx or dy:
                    send(f"G1 X{dx:.2f} Y{dy:.2f} F3000")
                send("G90"); send("M400", 60)
                report()
            elif c == "DEMO" and len(p) == 7:
                demo(*[float(v) for v in p[1:]])
        except ValueError:
            print(f"STATUS:Befehl ungueltig: {line.strip()}", flush=True)
    printer.close()
    print("STATUS:Beendet.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"STATUS:FEHLER: {e}", flush=True)
        sys.exit(1)
