"""
tdot_demo.py - TdoT-Demo Spulenteststand (PC-Programm)

Abgespeckte Version fuer den Tag der offenen Tuer:
  1. Mit dem Raspberry Pi verbinden (SSH)
  2. Zwei Ecken eines Rechtecks von Hand anfahren
  3. DEMO starten: Drucker faehrt das Rechteck im Dauerlauf ab, bis STOPP gedrueckt wird
Es gibt KEINE Referenzfahrt. Die Messwerte sind erfunden (Sensor nicht angeschlossen).

Benoetigt: Python 3 + paramiko  (pip install paramiko)
"""
import os
import threading
import tkinter as tk
from tkinter import ttk
import paramiko

PI_IP = "192.168.10.2"
PI_USER = "piben"
PI_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tdot_pi.py")


class Demo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spulenteststand – TdoT-Demo")
        self.geometry("900x620")
        self.client = None
        self.chan = None
        self.pos = None
        self.ecke = {1: None, 2: None}
        self.step = tk.StringVar(value="10")
        self._baue_gui()

    # ---------------- GUI ----------------
    def _baue_gui(self):
        big = ("Segoe UI", 28, "bold")
        f = ttk.LabelFrame(self, text="1. Verbinden")
        f.pack(fill="x", padx=10, pady=6)
        self.e_ip = ttk.Entry(f, width=16); self.e_ip.insert(0, PI_IP)
        self.e_user = ttk.Entry(f, width=10); self.e_user.insert(0, PI_USER)
        self.e_pw = ttk.Entry(f, width=14, show="*")
        for t, w in (("IP", self.e_ip), ("Benutzer", self.e_user), ("Passwort", self.e_pw)):
            ttk.Label(f, text=t).pack(side="left", padx=(8, 2)); w.pack(side="left")
        self.b_conn = ttk.Button(f, text="Verbinden", command=self.verbinden)
        self.b_conn.pack(side="left", padx=10, pady=6)

        mid = ttk.Frame(self); mid.pack(fill="x", padx=10)
        j = ttk.LabelFrame(mid, text="2. Ecken anfahren")
        j.pack(side="left", fill="y", padx=(0, 6), pady=6)
        self.l_pos = ttk.Label(j, text="Düse: –", font=("Segoe UI", 14, "bold"))
        self.l_pos.grid(row=0, column=0, columnspan=4, pady=6)
        ttk.Label(j, text="Schritt (mm):").grid(row=1, column=0, sticky="w", padx=6)
        sf = ttk.Frame(j); sf.grid(row=1, column=1, columnspan=3, sticky="w")
        for v in ("1", "10", "50"):
            ttk.Radiobutton(sf, text=v, value=v, variable=self.step).pack(side="left")
        def k(t, r, c, d):
            ttk.Button(j, text=t, width=7, command=lambda: self.fahren(*d)).grid(row=r, column=c, padx=3, pady=3, ipady=6)
        k("Y+", 2, 1, (0, 1, 0)); k("X−", 3, 0, (-1, 0, 0)); k("X+", 3, 2, (1, 0, 0)); k("Y−", 4, 1, (0, -1, 0))
        k("Z+ ↑", 2, 3, (0, 0, 1)); k("Z− ↓", 4, 3, (0, 0, -1))
        ttk.Button(j, text="📍 Ecke 1 übernehmen", command=lambda: self.ecke_setzen(1)).grid(row=5, column=0, columnspan=4, sticky="ew", padx=6, pady=(10, 2))
        ttk.Button(j, text="📍 Ecke 2 übernehmen", command=lambda: self.ecke_setzen(2)).grid(row=6, column=0, columnspan=4, sticky="ew", padx=6, pady=2)
        self.l_ecken = ttk.Label(j, text="Ecke 1: –\nEcke 2: –", justify="left")
        self.l_ecken.grid(row=7, column=0, columnspan=4, sticky="w", padx=6, pady=4)

        d = ttk.LabelFrame(mid, text="3. Demo")
        d.pack(side="left", fill="both", expand=True, pady=6)
        r = ttk.Frame(d); r.pack(pady=6)
        ttk.Label(r, text="Punktabstand (mm):").pack(side="left")
        self.e_delta = ttk.Entry(r, width=6); self.e_delta.insert(0, "10"); self.e_delta.pack(side="left", padx=4)
        tk.Button(d, text="▶ DEMO STARTEN", bg="#8E44AD", fg="white", font=("Segoe UI", 14, "bold"),
                  command=self.demo_start).pack(fill="x", padx=12, pady=4, ipady=6)
        tk.Button(d, text="⏹ STOPP", bg="#D13438", fg="white", font=("Segoe UI", 14, "bold"),
                  command=self.stopp).pack(fill="x", padx=12, pady=4, ipady=6)
        self.l_b = ttk.Label(d, text="0.00 mT", font=big, foreground="#2FA572")
        self.l_b.pack(pady=(12, 0))
        self.l_bxyz = ttk.Label(d, text="Bx –  By –  Bz –   (Demo-Werte)")
        self.l_bxyz.pack()

        self.log = tk.Text(self, height=10, font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, padx=10, pady=6)
        self.schreibe("Ablauf: Verbinden → Ecken anfahren → DEMO STARTEN. STOPP hebt die Düse 10 mm an.")

    def schreibe(self, t):
        self.log.insert("end", t + "\n"); self.log.see("end")

    def ui(self, f):
        self.after(0, f)

    # ---------------- SSH ----------------
    def verbinden(self):
        self.b_conn.configure(state="disabled")
        self.schreibe("Verbinde ...")
        threading.Thread(target=self._verbinden, daemon=True).start()

    def _verbinden(self):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(self.e_ip.get().strip(), username=self.e_user.get().strip(),
                      password=self.e_pw.get() or None, timeout=6)
            sftp = c.open_sftp(); sftp.put(PI_SCRIPT, "tdot_pi.py"); sftp.close()
            self.client = c
            self.ui(lambda: self.schreibe("Verbunden. Starte Anfahr-Modus am Pi ..."))
            self._starte_pi()
        except Exception as e:
            self.ui(lambda: (self.schreibe(f"FEHLER Verbindung: {e}"), self.b_conn.configure(state="normal")))

    def _starte_pi(self):
        # evtl. alte Instanz beenden
        self.client.exec_command("pkill -INT -f tdot_pi.py")
        ch = self.client.get_transport().open_session()
        ch.set_combine_stderr(True)
        ch.exec_command("sleep 1; python3 -u tdot_pi.py")
        self.chan = ch
        threading.Thread(target=self._lesen, args=(ch,), daemon=True).start()

    def _lesen(self, ch):
        for line in ch.makefile("r", -1):
            line = line.strip()
            if line:
                self.ui(lambda l=line: self.zeile(l))
        self.ui(lambda: (self.schreibe("Pi-Programm beendet. Zum Weitermachen erneut 'Verbinden'."),
                         self.b_conn.configure(state="normal")))
        self.chan = None

    def zeile(self, l):
        if l.startswith("POS:"):
            self.pos = [float(v) for v in l[4:].split(",")]
            self.l_pos.configure(text="Düse: X{:.1f}  Y{:.1f}  Z{:.1f}".format(*self.pos))
        elif l.startswith("DATA:"):
            x, y, z, bx, by, bz, b = [float(v) for v in l[5:].split(",")]
            self.l_pos.configure(text=f"Düse: X{x:.1f}  Y{y:.1f}  Z{z:.1f}")
            self.l_b.configure(text=f"{b:.2f} mT")
            self.l_bxyz.configure(text=f"Bx {bx:+.2f}  By {by:+.2f}  Bz {bz:+.2f} mT   (Demo-Werte)")
        elif l.startswith("STATUS:"):
            self.schreibe(l[7:])
        else:
            self.schreibe(l)

    def senden(self, t):
        if not self.chan or self.chan.closed:
            self.schreibe("Nicht verbunden – zuerst 'Verbinden'.")
            return False
        self.chan.send((t + "\n").encode())
        return True

    # ---------------- Aktionen ----------------
    def fahren(self, sx, sy, sz):
        s = float(self.step.get())
        self.senden(f"MOVE {sx * s} {sy * s} {sz * s}")

    def ecke_setzen(self, n):
        if not self.pos:
            self.schreibe("Position unbekannt – zuerst verbinden.")
            return
        self.ecke[n] = list(self.pos)
        t = [f"Ecke {i}: " + ("X{:.1f} Y{:.1f} Z{:.1f}".format(*self.ecke[i]) if self.ecke[i] else "–") for i in (1, 2)]
        self.l_ecken.configure(text="\n".join(t))

    def demo_start(self):
        e1, e2 = self.ecke[1], self.ecke[2]
        if not (e1 and e2):
            self.schreibe("Bitte zuerst beide Ecken übernehmen.")
            return
        try:
            delta = max(1.0, float(self.e_delta.get().replace(",", ".")))
        except ValueError:
            delta = 10.0
        z = max(e1[2], e2[2])   # hoehere der beiden Ecken = sicherer
        if self.senden(f"DEMO {e1[0]} {e2[0]} {e1[1]} {e2[1]} {delta} {z}"):
            self.schreibe(f"Demo gestartet (Δ={delta} mm, Z={z:.1f} mm).")

    def stopp(self):
        if not self.client:
            return
        self.schreibe("STOPP ...")
        threading.Thread(target=lambda: self.client.exec_command("pkill -INT -f tdot_pi.py"), daemon=True).start()


if __name__ == "__main__":
    Demo().mainloop()
