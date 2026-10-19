#!/usr/bin/env python3
"""Generate the SVG figures used by the FPGA showcase theory pages.

The coefficient data lives in assets/data/ and is copied from the fpga-lab
repository (s03_fir/lut/coef.mem, s04_resample/lut/hb_odd.mem).  Run from the
repository root:

    python3 tools/make_figs.py

No third-party plotting library is used; the SVGs are emitted directly so the
pages stay dependency-free and crisp at any zoom.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "img"
DATA = ROOT / "assets" / "data"

# palette ------------------------------------------------------------------
BG = "#071417"
GRID = "rgba(133,184,178,.12)"
AXIS = "rgba(133,184,178,.38)"
TEXT = "#b6cbc5"
MUTED = "#8ea7a2"
FAINT = "#5d7774"
GREEN = "#6cf0b0"
AMBER = "#ffc768"
BLUE = "#7bc8ff"
VIOLET = "#c8a8ff"
RED = "#ff8a80"
PANEL = "rgba(8,20,23,.55)"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

W = 780


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def read_mem(name: str) -> np.ndarray:
    vals = []
    for line in (DATA / name).read_text().splitlines():
        line = line.split("//")[0].strip()
        if not line:
            continue
        v = int(line, 16)
        if v >= 0x8000:
            v -= 0x10000
        vals.append(v)
    return np.array(vals, dtype=float)


class Ax:
    def __init__(self, w=W, h=330, l=64, r=26, t=28, b=48):
        self.w, self.h, self.l, self.r, self.t, self.b = w, h, l, r, t, b
        self.pw, self.ph = w - l - r, h - t - b

    def x(self, v):
        lo, hi = self.xlim
        return self.l + (v - lo) / (hi - lo) * self.pw

    def y(self, v):
        lo, hi = self.ylim
        return self.t + (hi - v) / (hi - lo) * self.ph

    def frame(self, xlim, ylim, xticks, yticks, xfmt=str, yfmt=str,
              xlabel="", ylabel="", xunit="", yunit=""):
        self.xlim, self.ylim = xlim, ylim
        out = [f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{BG}"/>']
        out.append(f'<rect x="{self.l}" y="{self.t}" width="{self.pw}" height="{self.ph}" fill="{PANEL}" stroke="{GRID}"/>')
        for v in yticks:
            yy = self.y(v)
            out.append(f'<line x1="{self.l}" y1="{yy:.1f}" x2="{self.l+self.pw}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="1"/>')
            out.append(f'<text x="{self.l-10}" y="{yy+3.5:.1f}" text-anchor="end" fill="{FAINT}" font-family="{MONO}" font-size="9.5">{esc(yfmt(v))}</text>')
        for v in xticks:
            xx = self.x(v)
            out.append(f'<line x1="{xx:.1f}" y1="{self.t}" x2="{xx:.1f}" y2="{self.t+self.ph}" stroke="{GRID}" stroke-width="1"/>')
            out.append(f'<text x="{xx:.1f}" y="{self.t+self.ph+18}" text-anchor="middle" fill="{FAINT}" font-family="{MONO}" font-size="9.5">{esc(xfmt(v))}</text>')
        out.append(f'<line x1="{self.l}" y1="{self.t+self.ph}" x2="{self.l+self.pw}" y2="{self.t+self.ph}" stroke="{AXIS}"/>')
        out.append(f'<line x1="{self.l}" y1="{self.t}" x2="{self.l}" y2="{self.t+self.ph}" stroke="{AXIS}"/>')
        if xlabel:
            out.append(f'<text x="{self.l+self.pw/2:.1f}" y="{self.h-12}" text-anchor="middle" fill="{MUTED}" font-family="{MONO}" font-size="10">{esc(xlabel)}</text>')
        if ylabel:
            out.append(f'<text x="15" y="{self.t+self.ph/2:.1f}" text-anchor="middle" fill="{MUTED}" font-family="{MONO}" font-size="10" transform="rotate(-90 15 {self.t+self.ph/2:.1f})">{esc(ylabel)}</text>')
        if xunit:
            out.append(f'<text x="{self.l+self.pw:.0f}" y="{self.t+self.ph+18}" text-anchor="end" fill="{FAINT}" font-family="{MONO}" font-size="9">{esc(xunit)}</text>')
        if yunit:
            out.append(f'<text x="{self.l-10}" y="{self.t-9}" text-anchor="end" fill="{FAINT}" font-family="{MONO}" font-size="9">{esc(yunit)}</text>')
        return out

    def polyline(self, xs, ys, color=GREEN, width=1.8, dash=None, opacity=1.0):
        pts = " ".join(f"{self.x(x):.1f},{self.y(y):.1f}" for x, y in zip(xs, ys))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" opacity="{opacity}"{d}/>'

    def hline(self, v, color=FAINT, dash="4 4", width=1):
        yy = self.y(v)
        return f'<line x1="{self.l}" y1="{yy:.1f}" x2="{self.l+self.pw}" y2="{yy:.1f}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}" opacity=".75"/>'

    def vline(self, v, color=FAINT, dash="4 4", width=1):
        xx = self.x(v)
        return f'<line x1="{xx:.1f}" y1="{self.t}" x2="{xx:.1f}" y2="{self.t+self.ph}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}" opacity=".75"/>'

    def label(self, xv, yv, text, color=MUTED, anchor="start", size=9.5, dy=0):
        return (f'<text x="{self.x(xv):.1f}" y="{self.y(yv)+dy:.1f}" text-anchor="{anchor}" '
                f'fill="{color}" font-family="{MONO}" font-size="{size}">{esc(text)}</text>')

    def legend(self, items, x=None, y=None):
        x = self.l + 14 if x is None else x
        y = self.t + 16 if y is None else y
        out = []
        for i, (color, name) in enumerate(items):
            yy = y + i * 16
            out.append(f'<line x1="{x}" y1="{yy}" x2="{x+16}" y2="{yy}" stroke="{color}" stroke-width="2.4"/>')
            out.append(f'<text x="{x+22}" y="{yy+3.5}" fill="{MUTED}" font-family="{MONO}" font-size="9.5">{esc(name)}</text>')
        return out


def stems(ax: Ax, xs, ys, color=GREEN, base=0.0, r=2.2, zero="#5d7774", hollow_gray=True):
    out = []
    for x, y in zip(xs, ys):
        if abs(y) < 1e-12:
            if hollow_gray:
                out.append(f'<circle cx="{ax.x(x):.1f}" cy="{ax.y(base):.1f}" r="1.8" fill="none" stroke="{FAINT}" stroke-width="1"/>')
            continue
        out.append(f'<line x1="{ax.x(x):.1f}" y1="{ax.y(base):.1f}" x2="{ax.x(x):.1f}" y2="{ax.y(y):.1f}" stroke="{color}" stroke-width="1.25" opacity=".85"/>')
        out.append(f'<circle cx="{ax.x(x):.1f}" cy="{ax.y(y):.1f}" r="{r}" fill="{color}"/>')
    return out


def wrap(ax: Ax, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ax.w} {ax.h}" '
            f'role="img" aria-label="{esc(label)}">' + "".join(body) + "</svg>")


def write(name: str, svg: str):
    (OUT / name).write_text(svg + "\n")
    print("wrote", name, len(svg))


# ============================================================ s01
def s01_wave():
    fs, f = 50e6, 100e3
    n = np.arange(1000)
    t = n / fs * 1e6
    s = np.round(2047 * np.sin(2 * math.pi * f * n / fs))
    c = np.round(2047 * np.cos(2 * math.pi * f * n / fs))
    ax = Ax(h=330)
    body = ax.frame((0, 20), (-2200, 2200), [0, 5, 10, 15, 20], [-2048, -1024, 0, 1024, 2047],
                    xlabel="时间 / µs", ylabel="12 位补码样本", xunit="", yunit="")
    body += [ax.hline(0, AXIS, "1 1", 1)]
    body += [ax.polyline(t, s, GREEN, 1.8), ax.polyline(t, c, AMBER, 1.5, dash="5 4")]
    body += ax.legend([(GREEN, "sin (I)"), (AMBER, "cos (Q) 虚线")], x=ax.l + 14, y=ax.t + 16)
    write("s01-wave.svg", wrap(ax, body, "100 kHz 正弦与余弦，20 微秒两周期"))


def s01_phase():
    step = 100e3 * 2**32 / 50e6
    addr_step = step / 2**20
    n = np.arange(0, 1005)
    addr = (n * addr_step) % 4096
    ax = Ax(h=320)
    body = ax.frame((0, 1000), (0, 4900), [0, 200, 400, 600, 800, 1000], [0, 1024, 2048, 3072, 4096],
                    xlabel="时钟拍数 n", ylabel="查表地址 / 0…4095", yunit="")
    body += [ax.hline(4096, FAINT, "4 4", 1)]
    # draw as staircase-ish line; wrap creates a jump, split into segments
    xs, ys = [], []
    prev = None
    for i, a in enumerate(addr):
        if prev is not None and a < prev - 1000:
            body.append(ax.polyline(xs, ys, GREEN, 1.6))
            xs, ys = [i - 1, i], [prev, 4096]
            body.append(ax.polyline(xs, ys, GREEN, 1.6, opacity=.35))
            xs, ys = [i], [a]
        else:
            xs.append(i); ys.append(a)
        prev = a
    body.append(ax.polyline(xs, ys, GREEN, 1.6))
    body += [ax.label(18, 4740, f"每拍 +{addr_step:.3f} 个表地址 → 约 500 拍绕一圈", GREEN, "start", 9.5)]
    body += [ax.label(18, 4430, "溢出 = 相位绕回 0，不需要比较器", FAINT, "start", 9)]
    write("s01-phase.svg", wrap(ax, body, "相位累加器查表地址随拍数锯齿上升"))


# ============================================================ s02
def s02_spectrum():
    w, h = 780, 430
    parts = []
    # panel headers
    def panel(y0, title, out_f, out_label, out_color, note):
        ax = Ax(h=180, t=26, b=36, l=58, r=24)
        # local coordinate system by translating: easier to create a standalone body and shift
        ax.h = 180
        ax.pw, ax.ph = ax.w - ax.l - ax.r, ax.h - ax.t - ax.b
        body = ax.frame((0, 600), (0, 1.2), [0, 100, 200, 250, 300, 400, 450, 500, 600], [],
                        xlabel="", ylabel="", yunit="")
        # stems
        for freq, name, col, ht in [(250, "输入 250k", BLUE, .62), (200, "本振 200k", AMBER, .48), (out_f, out_label, out_color, .92)]:
            xx = ax.x(freq)
            body.append(f'<line x1="{xx:.1f}" y1="{ax.y(0):.1f}" x2="{xx:.1f}" y2="{ax.y(ht):.1f}" stroke="{col}" stroke-width="2"/>')
            body.append(f'<circle cx="{xx:.1f}" cy="{ax.y(ht):.1f}" r="3.2" fill="{col}"/>')
            body.append(f'<text x="{xx:.1f}" y="{ax.y(ht)-8:.1f}" text-anchor="middle" fill="{col}" font-family="{MONO}" font-size="9.5">{esc(name)}</text>')
        body.append(f'<text x="{ax.l}" y="14" fill="{GREEN}" font-family="{MONO}" font-size="10" letter-spacing="1.2">{esc(title)}</text>')
        body.append(f'<text x="{ax.w-24}" y="14" text-anchor="end" fill="{FAINT}" font-family="{MONO}" font-size="9">{esc(note)}</text>')
        return f'<g transform="translate(0,{y0})">' + "".join(body) + "</g>"
    parts.append(panel(0, "① 上变频：输出 = 250k + 200k", 450, "和频 450k", GREEN, "和频"))
    parts.append(panel(215, "② 下变频：输出 = |250k − 200k|", 50, "差频 50k", GREEN, "差频"))
    # axis label at bottom
    parts.append(f'<text x="{W/2:.0f}" y="{h-8}" text-anchor="middle" fill="{MUTED}" font-family="{MONO}" font-size="10">频率 / kHz　（只画正频率分量）</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="复数混频的上变频与下变频频谱">' + "".join(parts) + "</svg>"
    write("s02-spectrum.svg", svg)


def s02_wave():
    fs = 50e6
    n = np.arange(2000)
    t = n / fs * 1e6
    xin = np.cos(2 * math.pi * 250e3 * n / fs)
    yout = np.cos(2 * math.pi * 50e3 * n / fs)
    ax = Ax(h=330)
    body = ax.frame((0, 40), (-1.25, 1.25), [0, 10, 20, 30, 40], [-1, 0, 1],
                    xlabel="时间 / µs", ylabel="归一化幅度", xfmt=lambda v: f"{v:g}", yfmt=lambda v: f"{v:g}")
    body += [ax.hline(0, AXIS, "1 1", 1)]
    body += [ax.polyline(t, xin, BLUE, 1.2, opacity=.8), ax.polyline(t, yout, GREEN, 2.2)]
    body += ax.legend([(BLUE, "输入 250 kHz"), (GREEN, "下变频输出 50 kHz")], x=ax.l + 14, y=ax.t + 14)
    body += [ax.label(20, .92, "5 : 1", AMBER, "middle", 12)]
    write("s02-wave.svg", wrap(ax, body, "输入 250 kHz 与下变频输出 50 kHz 的时域波形"))


# ============================================================ s03
def s03_coef():
    c = read_mem("fir_coef.mem")
    k = np.arange(len(c))
    ax = Ax(h=350)
    body = ax.frame((0, 46), (-2600, 10600), [0, 10, 20, 23, 30, 40, 46], [-2000, 0, 4000, 8000, 10000],
                    xlabel="抽头下标 k", ylabel="Q1.15 整数", yunit="")
    body += [ax.hline(0, AXIS, "1 1", 1)]
    body += stems(ax, k, c, GREEN)
    body += [ax.label(23, 9810, "c[23] = 9810", AMBER, "middle", 9.5, -10)]
    body += [ax.label(18, -1867, "c[18] = −1867", RED, "middle", 9, 14)]
    body += [ax.label(1.2, 7200, "两端 c[0]=c[46]=11", FAINT, "start", 9)]
    # symmetry bracket
    y = ax.y(10800)
    body.append(f'<path d="M{ax.x(0):.1f},{y:.1f} L{ax.x(0):.1f},{y-9:.1f} L{ax.x(46):.1f},{y-9:.1f} L{ax.x(46):.1f},{y:.1f}" fill="none" stroke="{FAINT}" stroke-width="1"/>')
    body += [ax.label(23, 11250, "c[k] = c[46−k] → 线性相位", FAINT, "middle", 9)]
    write("s03-coef.svg", wrap(ax, body, "47 个 FIR 系数，关于中心对称"))


def s03_response():
    c = read_mem("fir_coef.mem")
    nfft = 8192
    H = np.fft.rfft(c, nfft)
    f = np.fft.rfftfreq(nfft)
    mag = 20 * np.log10(np.maximum(np.abs(H) / c.sum(), 1e-9))
    f, mag = f[::4], mag[::4]
    stop = mag[(f >= .2) & (f <= .5)].max()
    ax = Ax(h=350)
    body = ax.frame((0, .5), (-90, 8), [0, .1, .2, .3, .4, .5], [-80, -60, -40, -20, 0],
                    xlabel="归一化频率 f / Fs", ylabel="|H(f)| / dB", yunit="")
    body += [ax.vline(.10, AMBER, "5 4"), ax.vline(.20, RED, "5 4")]
    body += [ax.hline(stop, RED, "2 5", 1)]
    body += [ax.polyline(f, np.clip(mag, -90, 8), GREEN, 1.9)]
    body += [ax.label(.103, 2.6, "通带边 0.10", AMBER, "start", 9)]
    body += [ax.label(.203, -8, "阻带边 0.20", RED, "start", 9)]
    body += [ax.label(.34, stop - 5, f"实测阻带 {abs(stop):.1f} dB", RED, "middle", 9.5)]
    body += [ax.label(.012, -7, "0 dB", FAINT, "start", 9)]
    body += [ax.label(.25, -30, "Hamming 窗：过渡带宽，但旁瓣低", FAINT, "middle", 9)]
    write("s03-response.svg", wrap(ax, body, "47 抽头 FIR 的幅频响应"))


def s03_phase():
    c = read_mem("fir_coef.mem")
    f = np.linspace(0, .2, 400)
    H = np.array([np.sum(c * np.exp(-2j * math.pi * fi * np.arange(len(c)))) for fi in f])
    ph = np.unwrap(np.angle(H))
    ax = Ax(h=330)
    body = ax.frame((0, .2), (-16, 0), [0, .05, .1, .15, .2], [-15, -10, -5, 0],
                    xlabel="归一化频率 f / Fs", ylabel="相位 / rad", yunit="")
    body += [ax.polyline(f, ph, VIOLET, 2.0)]
    body += [ax.label(.015, -2.0, "φ(f) = −2π·23·f", VIOLET, "start", 10)]
    body += [ax.label(.015, -4.2, "一条过原点的直线 → 群延迟恒为 23 拍", FAINT, "start", 9)]
    body += [ax.label(.15, -2.0, "斜率 = −2π·23", AMBER, "middle", 9)]
    write("s03-phase.svg", wrap(ax, body, "线性相位：相位随频率线性下降，斜率对应 23 拍群延迟"))


def s03_impulse():
    c = read_mem("fir_coef.mem")
    h = np.floor((c * 2047 + 2**14) / 2**15)
    n = np.arange(4, 4 + len(h))
    ax = Ax(h=340)
    body = ax.frame((0, 52), (-180, 700), [0, 4, 10, 20, 27, 35, 45, 51], [-100, 0, 200, 400, 600],
                    xlabel="输出拍数 n（冲激在 n=0 输入）", ylabel="y[n] / LSB", yunit="")
    body += [ax.hline(0, AXIS, "1 1", 1)]
    body += stems(ax, n, h, GREEN, base=0)
    body += [ax.vline(4, AMBER, "3 4"), ax.vline(27, AMBER, "3 4")]
    body += [ax.label(4, -150, "n=4", AMBER, "middle", 9), ax.label(27, -150, "n=27", AMBER, "middle", 9)]
    body += [ax.label(8, 420, "h[0] = 1", FAINT, "start", 9)]
    body += [ax.label(27, 613, "中心 613", GREEN, "middle", 9.5, -10)]
    body += [ax.label(40, 260, "4 拍流水 + 23 拍群延迟", FAINT, "middle", 9)]
    write("s03-impulse.svg", wrap(ax, body, "冲激响应：第 4 拍出现首抽头，第 27 拍到达中心峰"))


# ============================================================ s04
def s04_taps():
    o = read_mem("hb_odd.mem")
    h = np.zeros(61)
    h[30] = 16384
    h[1:60:2] = o
    h = h / 32768
    k = np.arange(61)
    ax = Ax(h=340)
    body = ax.frame((0, 60), (-.09, .55), [0, 10, 20, 30, 40, 50, 60], [-.05, 0, .2, .4],
                    xlabel="抽头下标 k", ylabel="归一化系数 h[k]", xfmt=lambda v: f"{v:g}", yfmt=lambda v: f"{v:g}")
    body += [ax.hline(0, AXIS, "1 1", 1)]
    body += stems(ax, k, h, GREEN, r=2.0)
    # zero markers are already hollow; mark center
    body += [ax.label(30, .5, "中心 0.5", AMBER, "middle", 9.5, -10)]
    body += [ax.label(3, .3, "偶数下标除中心外全为 0", FAINT, "start", 9)]
    body += [ax.label(44, .3, "30 个奇数抽头 → 15 对", GREEN, "start", 9)]
    write("s04-taps.svg", wrap(ax, body, "61 个半带抽头：中心 0.5，偶数下标为零，30 个奇数抽头"))


def s04_halfband():
    o = read_mem("hb_odd.mem")
    h = np.zeros(61)
    h[30] = 16384
    h[1:60:2] = o
    nfft = 16384
    H = np.fft.rfft(h, nfft)
    f = np.fft.rfftfreq(nfft)
    mag = 20 * np.log10(np.maximum(np.abs(H) / h.sum(), 1e-9))
    f, mag = f[::4], mag[::4]
    stop = mag[(f >= .3) & (f <= .5)].max()
    ax = Ax(h=350)
    body = ax.frame((0, .5), (-90, 5), [0, .1, .2, .25, .3, .4, .5], [-80, -60, -40, -20, 0],
                    xlabel="归一化频率 f / Fs", ylabel="|H(f)| / dB", yunit="")
    body += [ax.vline(.25, AMBER, "5 4"), ax.vline(.3, RED, "5 4"), ax.hline(stop, RED, "2 5", 1)]
    body += [ax.polyline(f, np.clip(mag, -90, 5), GREEN, 1.9)]
    body += [ax.label(.252, -3, "Fs/4 = −6 dB", AMBER, "start", 9)]
    body += [ax.label(.302, -11, "阻带起点 0.30", RED, "start", 9)]
    body += [ax.label(.36, stop - 5, f"实测阻带 {abs(stop):.1f} dB", RED, "middle", 9.5)]
    body += [ax.label(.03, -16, "通带与阻带关于 Fs/4 镜像对称", FAINT, "start", 9)]
    write("s04-halfband.svg", wrap(ax, body, "61 抽头半带滤波器的幅频响应，Fs/4 处为 -6 dB"))


def s04_images():
    w, h = 780, 400
    out = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="{BG}"/>']

    def tri(x0, width, base_y, height, color, alpha, label=None, dash=False, hollow=False):
        x1 = x0 + width / 2
        pts = f"{x0:.1f},{base_y:.1f} {x1:.1f},{base_y-height:.1f} {x0+width:.1f},{base_y:.1f}"
        stroke = color
        fill = "none" if hollow else color
        d = ' stroke-dasharray="4 4"' if dash else ""
        s = f'<polygon points="{pts}" fill="{fill}" opacity="{alpha}" stroke="{stroke}" stroke-width="1.2"{d}/>'
        if label:
            s += f'<text x="{x1:.1f}" y="{base_y-height-7:.1f}" text-anchor="middle" fill="{stroke}" font-family="{MONO}" font-size="9">{esc(label)}</text>'
        return s

    # top panel: original
    for i in range(2):
        out.append(f'<text x="26" y="{38+i*188}" fill="{GREEN}" font-family="{MONO}" font-size="10" letter-spacing="1">{esc(["① 原始基带","② 零插值之后"][i])}</text>')
    # axes
    for y0 in (70, 258):
        out.append(f'<line x1="42" y1="{y0+92}" x2="{w-24}" y2="{y0+92}" stroke="{AXIS}"/>')
        for f in (0, .5, 1, 1.5, 2):
            xx = 42 + f / 2 * (w - 70)
            out.append(f'<line x1="{xx:.1f}" y1="{y0+92}" x2="{xx:.1f}" y2="{y0+98}" stroke="{AXIS}"/>')
            out.append(f'<text x="{xx:.1f}" y="{y0+112}" text-anchor="middle" fill="{FAINT}" font-family="{MONO}" font-size="9">{f:g}·Fs</text>')
    # original spectrum
    base = 70 + 92
    out.append(tri(42, .2 / 2 * (w - 70), base, 58, BLUE, .35, "基带 [0, B]"))
    # zero-stuffed spectrum
    base2 = 258 + 92
    out.append(tri(42, .2 / 2 * (w - 70), base2, 58, BLUE, .35, "原谱"))
    out.append(tri(42 + .8 / 2 * (w - 70), .4 / 2 * (w - 70), base2, 58, RED, .3, "镜像 @ Fs−B", dash=True))
    out.append(tri(42 + (1.0) / 2 * (w - 70), .4 / 2 * (w - 70), base2, 58, RED, .18, "镜像 @ Fs+B", dash=True, hollow=True))
    out.append(tri(42 + (1.8) / 2 * (w - 70), .4 / 2 * (w - 70), base2, 58, RED, .12, "", dash=True, hollow=True))
    # transition band bracket
    x0 = 42 + .2 / 2 * (w - 70); x1 = 42 + .8 / 2 * (w - 70)
    yy = base2 + 24
    out.append(f'<path d="M{x0:.1f},{yy} L{x0:.1f},{yy+7} L{x1:.1f},{yy+7} L{x1:.1f},{yy}" fill="none" stroke="{AMBER}" stroke-width="1"/>')
    out.append(f'<text x="{(x0+x1)/2:.1f}" y="{yy+20}" text-anchor="middle" fill="{AMBER}" font-family="{MONO}" font-size="9">过渡带 = Fs − 2B</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="零插值前后的频谱与镜像">' + "".join(out) + "</svg>"
    write("s04-images.svg", svg)


def s04_alias():
    w, h = 780, 360
    out = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="{BG}"/>']
    panels = [("① 2:1 抽取前：Nyquist = 50 Hz", 50, 96, [10, 40], "10 Hz 有用", "40 Hz 干扰"),
              ("② 2:1 抽取后：Nyquist = 25 Hz，40 → 10 Hz", 25, 250, [10], "10 Hz", None)]
    for title, nyq, y0, tones, l1, l2 in panels:
        out.append(f'<text x="26" y="{y0-18}" fill="{GREEN}" font-family="{MONO}" font-size="10" letter-spacing="1">{esc(title)}</text>')
        base = y0 + 74
        out.append(f'<line x1="50" y1="{base}" x2="{w-28}" y2="{base}" stroke="{AXIS}"/>')
        for f in (0, 10, 25, 40, 50):
            xx = 50 + f / 55 * (w - 78)
            out.append(f'<line x1="{xx:.1f}" y1="{base}" x2="{xx:.1f}" y2="{base+6}" stroke="{AXIS}"/>')
            out.append(f'<text x="{xx:.1f}" y="{base+20}" text-anchor="middle" fill="{FAINT}" font-family="{MONO}" font-size="9">{f}</text>')
        # Nyquist line
        xn = 50 + nyq / 55 * (w - 78)
        out.append(f'<line x1="{xn:.1f}" y1="{y0-6}" x2="{xn:.1f}" y2="{base}" stroke="{AMBER}" stroke-dasharray="4 4"/>')
        out.append(f'<text x="{xn:.1f}" y="{base+34}" text-anchor="middle" fill="{AMBER}" font-family="{MONO}" font-size="9">Nyquist {nyq}</text>')
        hh = 52
        for f in tones:
            xx = 50 + f / 55 * (w - 78)
            out.append(f'<line x1="{xx:.1f}" y1="{base}" x2="{xx:.1f}" y2="{base-hh:.1f}" stroke="{BLUE}" stroke-width="2"/>')
            out.append(f'<circle cx="{xx:.1f}" cy="{base-hh:.1f}" r="3" fill="{BLUE}"/>')
        # labels
        if l2:
            out.append(f'<text x="{50+10/55*(w-78):.1f}" y="{base-hh-10}" text-anchor="middle" fill="{BLUE}" font-family="{MONO}" font-size="9">10</text>')
            out.append(f'<text x="{50+40/55*(w-78):.1f}" y="{base-hh-10}" text-anchor="middle" fill="{BLUE}" font-family="{MONO}" font-size="9">40</text>')
        else:
            # folded component at 10
            out.append(f'<line x1="{50+10/55*(w-78):.1f}" y1="{base}" x2="{50+10/55*(w-78):.1f}" y2="{base-hh-16:.1f}" stroke="{RED}" stroke-width="2" opacity=".8"/>')
            out.append(f'<text x="{50+10/55*(w-78)+8:.1f}" y="{base-hh-20}" fill="{RED}" font-family="{MONO}" font-size="9">40→10 折叠，压住有用信号</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="抽取前不滤波导致 40 Hz 干扰折叠到 10 Hz">' + "".join(out) + "</svg>"
    write("s04-alias.svg", svg)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s01_wave()
    s01_phase()
    s02_spectrum()
    s02_wave()
    s03_coef()
    s03_response()
    s03_phase()
    s03_impulse()
    s04_taps()
    s04_halfband()
    s04_images()
    s04_alias()


if __name__ == "__main__":
    main()
