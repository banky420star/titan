from flask import Flask, jsonify, render_template_string, request, send_from_directory
from pathlib import Path
from datetime import datetime
import json
import os
import subprocess
import sys
import traceback

BASE = Path("/Volumes/AI_DRIVE/TitanAgent")
sys.path.insert(0, str(BASE))

JOBS = BASE / "jobs"
RUNNING = JOBS / "running"
DONE = JOBS / "done"
CANCELLED = JOBS / "cancelled"
LOGS = JOBS / "logs"
TRACES = JOBS / "traces"
PRODUCTS = BASE / "products"

for folder in [RUNNING, DONE, CANCELLED, LOGS, TRACES, PRODUCTS]:
    folder.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)


HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Titan</title>
  <link rel="icon" href="/assets/favicon.ico">
  <link rel="alternate icon" href="/assets/titan_favicon.svg">\n  <link rel="icon" href="/assets/titan_favicon.svg">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      --bg: #111214;
      --bg2: #18191c;
      --panel: rgba(255,255,255,.045);
      --panel2: rgba(255,255,255,.075);
      --line: rgba(255,255,255,.09);
      --text: #f4f4f5;
      --muted: #a1a1aa;
      --yellow: #e8dd69;
      --orange: #e8ab43;
      --coral: #dd867b;
      --eye: #0f172a;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      height: 100%;
      overflow: hidden;
      background:
        radial-gradient(circle at 45% -20%, rgba(232,171,67,.14), transparent 34%),
        linear-gradient(180deg, var(--bg), var(--bg2));
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .app {
      height: 100vh;
      display: grid;
      grid-template-columns: 285px 1fr;
      overflow: hidden;
    }

    aside {
      height: 100vh;
      overflow-y: auto;
      background: #101113;
      border-right: 1px solid var(--line);
      padding: 20px 14px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 8px;
      font-size: 22px;
      font-weight: 850;
      letter-spacing: -.04em;
    }

    .mini {
      display: grid;
      grid-template-columns: repeat(3, 10px);
      align-items: end;
      gap: 0;
      height: 34px;
      filter: drop-shadow(0 8px 12px rgba(0,0,0,.25));
    }

    .bar {
      width: 10px;
      border-radius: 5px 5px 3px 3px;
      position: relative;
    }

    .bar.y { height: 22px; background: var(--yellow); }
    .bar.o { height: 34px; background: var(--orange); }
    .bar.r { height: 26px; background: var(--coral); }

    .bar.o::after,
    .bar.r::after {
      content: "";
      position: absolute;
      left: 2px;
      top: 11px;
      width: 6px;
      height: 8px;
      border-radius: 50%;
      background: var(--eye);
      box-shadow: 2px -1px 0 -1px white;
    }

    nav {
      display: grid;
      gap: 6px;
    }

    nav button {
      border: 0;
      color: #d4d4d8;
      background: transparent;
      text-align: left;
      border-radius: 14px;
      padding: 12px 13px;
      cursor: pointer;
      font-size: 15px;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: background .14s ease, color .14s ease, transform .14s ease;
    }

    nav button:hover {
      background: rgba(255,255,255,.06);
      color: white;
    }

    nav button.active {
      background: rgba(255,255,255,.09);
      color: white;
    }

    nav button:active,
    .btn:active,
    .card:active {
      transform: scale(.985);
    }

    .side-footer {
      margin-top: auto;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 18px;
      padding: 12px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }

    main {
      height: 100vh;
      overflow-y: auto;
      padding: 34px;
    }

    .shell {
      max-width: 1120px;
      margin: 0 auto;
    }

    .hero {
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 26px;
      align-items: center;
      margin-bottom: 22px;
    }

    .mascot-wrap {
      height: 150px;
      display: grid;
      place-items: center;
      position: relative;
    }

    .mascot-glow {
      position: absolute;
      width: 112px;
      height: 40px;
      bottom: 18px;
      background: rgba(232,171,67,.24);
      filter: blur(14px);
      border-radius: 50%;
    }

    .mascot {
      position: relative;
      width: 118px;
      height: 126px;
      image-rendering: pixelated;
      display: grid;
      place-items: center;
      animation: floaty 3.4s ease-in-out infinite;
      filter: drop-shadow(0 14px 24px rgba(0,0,0,.28));
    }

    @keyframes floaty {
      50% { transform: translateY(-7px); }
    }

    .sprite {
      display: grid;
      grid-template-columns: repeat(13, 8px);
      grid-auto-rows: 8px;
      gap: 0;
    }

    .px { width: 8px; height: 8px; }
    .Y { background: var(--yellow); }
    .O { background: var(--orange); }
    .R { background: var(--coral); }
    .B { background: var(--eye); }
    .W { background: white; }

    h1 {
      margin: 0;
      font-size: 58px;
      letter-spacing: -.06em;
      line-height: 1;
    }

    .subtitle {
      margin-top: 10px;
      color: var(--muted);
      font-size: 18px;
    }

    .composer {
      display: flex;
      gap: 10px;
      height: 62px;
      padding: 8px;
      background: rgba(255,255,255,.055);
      border: 1px solid var(--line);
      border-radius: 999px;
      margin-bottom: 16px;
      position: sticky;
      top: 16px;
      z-index: 10;
      backdrop-filter: blur(14px);
    }

    .composer input {
      flex: 1;
      min-width: 0;
      border: 0;
      outline: 0;
      background: transparent;
      color: white;
      padding: 0 14px;
      font-size: 16px;
    }

    .btn {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.075);
      color: white;
      border-radius: 999px;
      padding: 10px 14px;
      cursor: pointer;
      transition: background .14s ease, transform .14s ease;
    }

    .btn:hover {
      background: rgba(255,255,255,.11);
    }

    .btn.primary {
      min-width: 48px;
      background: rgba(232,171,67,.24);
      border-color: rgba(232,171,67,.26);
    }

    .view {
      display: none;
    }

    .view.active {
      display: block;
    }

    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 24px;
      overflow: hidden;
      margin-bottom: 18px;
    }

    .panel-head {
      padding: 15px 18px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    .panel-body {
      padding: 18px;
    }

    .messages {
      height: 390px;
      overflow-y: auto;
      display: grid;
      gap: 12px;
      padding: 18px;
    }

    .msg {
      max-width: 84%;
      padding: 13px 15px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.055);
      border-radius: 20px;
      white-space: pre-wrap;
      line-height: 1.45;
      word-break: break-word;
      animation: msgIn .16s ease both;
    }

    @keyframes msgIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .msg.user {
      justify-self: end;
      background: rgba(79,70,229,.18);
      border-color: rgba(124,140,255,.24);
    }

    .msg small {
      display: block;
      color: var(--muted);
      margin-bottom: 5px;
      font-weight: 700;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }

    .card {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 20px;
      padding: 16px;
      cursor: pointer;
      min-height: 118px;
      transition: background .14s ease, transform .14s ease;
    }

    .card:hover {
      background: var(--panel2);
      transform: translateY(-2px);
    }

    .card h3 {
      margin: 8px 0 6px;
      font-size: 16px;
    }

    .card p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.38;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      line-height: 1.45;
      color: #e5e7eb;
    }

    .row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }

    .field {
      flex: 1;
      min-width: 240px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.06);
      border-radius: 14px;
      color: white;
      padding: 12px;
      outline: 0;
    }

    @media (max-width: 900px) {
      html, body { overflow: auto; }
      .app { display: block; height: auto; }
      aside { height: auto; }
      main { height: auto; padding: 20px; }
      .hero { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
      .composer { position: static; }
    }
  
    /* TITAN_CHARACTER_FIX */
    .titan-logo {
      display: flex;
      align-items: flex-end;
      justify-content: center;
      position: relative;
      filter: drop-shadow(0 14px 24px rgba(0,0,0,.28));
    }

    .titan-logo .chunk {
      position: relative;
      display: block;
      box-shadow:
        inset 7px 9px 12px rgba(255,255,255,.22),
        inset -7px -10px 14px rgba(0,0,0,.16);
      transition: transform .16s ease;
    }

    .titan-logo .chunk.y {
      background: linear-gradient(145deg, #fff06a, #e8dd69);
    }

    .titan-logo .chunk.o {
      background: linear-gradient(145deg, #ffc46b, #e8ab43);
      z-index: 2;
    }

    .titan-logo .chunk.r {
      background: linear-gradient(145deg, #ff7b7d, #dd867b);
      z-index: 1;
    }

    .hero-logo {
      width: 142px;
      height: 142px;
      animation: titanFloat 3.4s ease-in-out infinite;
    }

    .hero-logo .chunk.y {
      width: 44px;
      height: 70px;
      border-radius: 17px;
      margin-right: -7px;
    }

    .hero-logo .chunk.o {
      width: 48px;
      height: 112px;
      border-radius: 18px;
    }

    .hero-logo .chunk.r {
      width: 44px;
      height: 78px;
      border-radius: 17px;
      margin-left: -7px;
    }

    .mini-logo {
      width: 38px;
      height: 38px;
      gap: 0;
      filter: drop-shadow(0 8px 12px rgba(0,0,0,.22));
    }

    .mini-logo .chunk.y {
      width: 12px;
      height: 24px;
      border-radius: 6px;
      margin-right: -2px;
    }

    .mini-logo .chunk.o {
      width: 14px;
      height: 36px;
      border-radius: 7px;
    }

    .mini-logo .chunk.r {
      width: 12px;
      height: 27px;
      border-radius: 6px;
      margin-left: -2px;
    }

    .titan-logo .eye {
      position: absolute;
      display: block;
      background: #0f172a;
      border-radius: 999px;
      transform-origin: center;
      transition: transform .1s ease;
    }

    .hero-logo .eye {
      width: 13px;
      height: 19px;
      top: 49px;
      box-shadow: inset -2px -3px 4px rgba(0,0,0,.2);
    }

    .hero-logo .chunk.o .eye {
      right: 9px;
    }

    .hero-logo .chunk.r .eye {
      left: 9px;
      top: 31px;
    }

    .mini-logo .eye {
      width: 5px;
      height: 8px;
      top: 13px;
    }

    .mini-logo .chunk.o .eye {
      right: 3px;
    }

    .mini-logo .chunk.r .eye {
      left: 3px;
      top: 10px;
    }

    .titan-logo .eye::after {
      content: "";
      position: absolute;
      width: 28%;
      height: 28%;
      border-radius: 50%;
      background: white;
      left: 28%;
      top: 18%;
      opacity: .95;
    }

    .titan-logo.blink .eye {
      transform: scaleY(.12);
    }

    .titan-logo:hover .chunk.o {
      transform: translateY(-3px);
    }

    @keyframes titanFloat {
      50% { transform: translateY(-7px); }
    }

    /* Hide old pixel sprite pieces if any remain */
    .sprite,
    .px {
      display: none !important;
    }

  
    /* TITAN_MASCOT_FINAL */
    .titan-mascot {
      position: relative;
      display: inline-block;
      filter: drop-shadow(0 12px 24px rgba(0,0,0,.28));
      user-select: none;
    }

    .titan-mascot .seg {
      position: absolute;
      bottom: 0;
      box-shadow:
        inset 0 5px 8px rgba(255,255,255,.20),
        inset 0 -8px 10px rgba(0,0,0,.10);
    }

    .titan-mascot .seg-y {
      background: linear-gradient(180deg, #fff17a 0%, #e7dc67 100%);
    }

    .titan-mascot .seg-o {
      background: linear-gradient(180deg, #ffd083 0%, #e8ab43 100%);
    }

    .titan-mascot .seg-r {
      background: linear-gradient(180deg, #f5a39e 0%, #dd867b 100%);
    }

    .titan-mascot-lg {
      width: 92px;
      height: 96px;
    }

    .titan-mascot-lg .seg-y {
      left: 6px;
      width: 26px;
      height: 44px;
      border-radius: 9px;
    }

    .titan-mascot-lg .seg-o {
      left: 28px;
      width: 30px;
      height: 68px;
      border-radius: 10px;
      z-index: 2;
    }

    .titan-mascot-lg .seg-r {
      left: 52px;
      width: 26px;
      height: 50px;
      border-radius: 9px;
      z-index: 1;
    }

    .titan-mascot-sm {
      width: 42px;
      height: 44px;
      margin-right: 10px;
      vertical-align: middle;
    }

    .titan-mascot-sm .seg-y {
      left: 2px;
      width: 12px;
      height: 22px;
      border-radius: 5px;
    }

    .titan-mascot-sm .seg-o {
      left: 11px;
      width: 14px;
      height: 34px;
      border-radius: 6px;
      z-index: 2;
    }

    .titan-mascot-sm .seg-r {
      left: 22px;
      width: 12px;
      height: 26px;
      border-radius: 5px;
      z-index: 1;
    }

    .titan-face .eye-wrap {
      position: absolute;
      overflow: hidden;
      border-radius: 999px;
      transform-origin: center center;
      transition: transform .12s ease;
      z-index: 5;
      background: transparent;
    }

    .titan-mascot-lg .eye-wrap {
      width: 11px;
      height: 18px;
      top: 34px;
    }

    .titan-mascot-lg .eye-left { left: 34px; }
    .titan-mascot-lg .eye-right { left: 49px; }

    .titan-mascot-sm .eye-wrap {
      width: 5px;
      height: 9px;
      top: 18px;
    }

    .titan-mascot-sm .eye-left { left: 16px; }
    .titan-mascot-sm .eye-right { left: 24px; }

    .titan-face .eye-core {
      position: absolute;
      inset: 0;
      border-radius: 999px;
      background: #101735;
      box-shadow: inset -1px -2px 2px rgba(0,0,0,.20);
      transform: translate(0px, 0px);
      transition: transform .08s linear;
    }

    .titan-face .eye-core::after {
      content: "";
      position: absolute;
      width: 26%;
      height: 26%;
      left: 30%;
      top: 17%;
      border-radius: 50%;
      background: rgba(255,255,255,.96);
    }

    .titan-face.blink .eye-wrap {
      transform: scaleY(0.08);
    }

    .floating {
      animation: titanFloat 3.2s ease-in-out infinite;
    }

    @keyframes titanFloat {
      0%   { transform: translateY(0px); }
      50%  { transform: translateY(-6px); }
      100% { transform: translateY(0px); }
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 22px;
      font-weight: 850;
      letter-spacing: -.04em;
    }

    .mascot-wrap {
      height: 150px;
      display: grid;
      place-items: center;
      position: relative;
    }

    .mascot-glow {
      position: absolute;
      width: 100px;
      height: 30px;
      bottom: 24px;
      border-radius: 50%;
      background: rgba(232,171,67,.20);
      filter: blur(16px);
    }

    .mini,
    .sprite,
    .px,
    .bar {
      display: none !important;
    }

  
    
    
    /* TITAN_PREVIEW_MASCOT_START */
    .titan-mascot {
      position: relative;
      display: inline-block;
      user-select: none;
      filter:
        drop-shadow(0 16px 28px rgba(0,0,0,.30))
        drop-shadow(0 0 18px rgba(232,171,67,.10));
      transform-style: preserve-3d;
    }

    .titan-mascot .seg {
      position: absolute;
      bottom: 0;
      box-shadow:
        inset 0 10px 14px rgba(255,255,255,.22),
        inset 0 -12px 16px rgba(0,0,0,.12),
        inset -4px 0 8px rgba(0,0,0,.06),
        0 8px 16px rgba(0,0,0,.12);
    }

    .titan-mascot .seg-y {
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,.33), transparent 42%),
        linear-gradient(180deg, #fff6a8 0%, #f9ea7d 38%, #e8dc67 100%);
    }

    .titan-mascot .seg-o {
      background:
        radial-gradient(circle at 30% 18%, rgba(255,255,255,.28), transparent 40%),
        linear-gradient(180deg, #ffd89d 0%, #ffc063 34%, #e8ab43 100%);
      z-index: 2;
    }

    .titan-mascot .seg-r {
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,.26), transparent 42%),
        linear-gradient(180deg, #f9b6ae 0%, #f39a91 36%, #dd867b 100%);
      z-index: 1;
    }

    .titan-mascot-lg {
      width: 128px;
      height: 106px;
    }

    .titan-mascot-lg .seg-y {
      left: 13px;
      bottom: 8px;
      width: 38px;
      height: 52px;
      border-radius: 15px;
    }

    .titan-mascot-lg .seg-o {
      left: 45px;
      bottom: 8px;
      width: 40px;
      height: 88px;
      border-radius: 16px;
    }

    .titan-mascot-lg .seg-r {
      left: 78px;
      bottom: 8px;
      width: 38px;
      height: 60px;
      border-radius: 15px;
    }

    .titan-mascot-sm {
      width: 42px;
      height: 42px;
      margin-right: 10px;
      vertical-align: middle;
      filter:
        drop-shadow(0 8px 14px rgba(0,0,0,.24))
        drop-shadow(0 0 12px rgba(232,171,67,.08));
    }

    .titan-mascot-sm .seg-y {
      left: 3px;
      bottom: 3px;
      width: 12px;
      height: 20px;
      border-radius: 5px;
    }

    .titan-mascot-sm .seg-o {
      left: 14px;
      bottom: 3px;
      width: 13px;
      height: 34px;
      border-radius: 6px;
      z-index: 2;
    }

    .titan-mascot-sm .seg-r {
      left: 25px;
      bottom: 3px;
      width: 12px;
      height: 24px;
      border-radius: 5px;
      z-index: 1;
    }

    .titan-face .eye-wrap {
      position: absolute;
      overflow: hidden;
      border-radius: 999px;
      transform-origin: center center;
      background: transparent;
      z-index: 5;
      transition: transform .14s ease;
    }

    /* Slightly smaller than before, still cute */
    .titan-mascot-lg .eye-wrap {
      width: 17px;
      height: 26px;
      top: 49px;
    }

    .titan-mascot-lg .eye-left {
      left: 48px;
    }

    .titan-mascot-lg .eye-right {
      left: 68px;
    }

    .titan-mascot-sm .eye-wrap {
      width: 6px;
      height: 10px;
      top: 18px;
    }

    .titan-mascot-sm .eye-left {
      left: 16px;
    }

    .titan-mascot-sm .eye-right {
      left: 24px;
    }

    .titan-face .eye-core {
      position: absolute;
      inset: 0;
      border-radius: 999px;
      background:
        radial-gradient(circle at 38% 28%, #243f82 0%, #13254f 34%, #091335 64%, #020611 100%);
      box-shadow:
        inset -2px -3px 5px rgba(0,0,0,.28),
        0 1px 2px rgba(0,0,0,.18);
      transform: translate(0px, 0px);
      transition: transform .09s linear;
    }

    .titan-face .eye-core::after {
      content: "";
      position: absolute;
      width: 30%;
      height: 30%;
      left: 24%;
      top: 14%;
      border-radius: 50%;
      background: rgba(255,255,255,.99);
      box-shadow: 0 0 4px rgba(255,255,255,.45);
    }

    .titan-face.blink .eye-wrap {
      transform: scaleY(0.05);
    }

    .floating {
      animation: titanFloat 3.2s ease-in-out infinite;
    }

    @keyframes titanFloat {
      0%   { transform: translateY(0px); }
      50%  { transform: translateY(-6px); }
      100% { transform: translateY(0px); }
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 22px;
      font-weight: 850;
      letter-spacing: -.04em;
    }

    .mascot-wrap {
      height: 150px;
      display: grid;
      place-items: center;
      position: relative;
    }

    .mascot-glow {
      position: absolute;
      width: 116px;
      height: 34px;
      bottom: 20px;
      border-radius: 50%;
      background:
        radial-gradient(circle, rgba(255,203,96,.26) 0%, rgba(232,171,67,.14) 45%, transparent 80%);
      filter: blur(16px);
    }

    .mini, .sprite, .px, .bar {
      display: none !important;
    }
    /* TITAN_PREVIEW_MASCOT_END */



  
    /* TITAN_LIVE_TRACE_VIEWER_START */
    .compact-row {
      margin: 0;
      align-items: center;
    }

    .toggle-label {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      user-select: none;
    }

    .jobs-layout {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 16px;
      min-height: 520px;
    }

    .job-list-wrap,
    .job-detail-wrap {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.035);
      border-radius: 18px;
      overflow: hidden;
    }

    .section-title {
      padding: 13px 15px;
      border-bottom: 1px solid var(--line);
      font-weight: 800;
      color: #f4f4f5;
      background: rgba(255,255,255,.035);
    }

    .job-list {
      max-height: 680px;
      overflow-y: auto;
      padding: 12px;
      display: grid;
      gap: 10px;
    }

    .job-card {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 16px;
      padding: 12px;
      cursor: pointer;
      transition: transform .14s ease, background .14s ease, border-color .14s ease;
    }

    .job-card:hover {
      background: rgba(255,255,255,.075);
      transform: translateY(-1px);
    }

    .job-card.active {
      border-color: rgba(232,171,67,.38);
      background: rgba(232,171,67,.09);
    }

    .job-card-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      align-items: center;
      margin-bottom: 8px;
      font-weight: 800;
      font-size: 13px;
    }

    .job-card-task {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.055);
      color: #d4d4d8;
      white-space: nowrap;
    }

    .status-pill.running,
    .status-pill.queued {
      color: #fbbf24;
      border-color: rgba(251,191,36,.28);
      background: rgba(251,191,36,.09);
    }

    .status-pill.done {
      color: #22c55e;
      border-color: rgba(34,197,94,.25);
      background: rgba(34,197,94,.08);
    }

    .status-pill.error {
      color: #fb7185;
      border-color: rgba(251,113,133,.28);
      background: rgba(251,113,133,.09);
    }

    .job-tabs {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      padding: 12px;
      border-bottom: 1px solid var(--line);
    }

    .job-tabs .btn.active {
      background: rgba(232,171,67,.18);
      border-color: rgba(232,171,67,.34);
    }

    .job-pane {
      display: none;
      padding: 14px;
    }

    .job-pane.active {
      display: block;
    }

    .job-pane pre {
      max-height: 590px;
      overflow-y: auto;
      background: rgba(0,0,0,.18);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
    }

    @media (max-width: 980px) {
      .jobs-layout {
        grid-template-columns: 1fr;
      }

      .job-list {
        max-height: 320px;
      }
    }
    /* TITAN_LIVE_TRACE_VIEWER_END */

  
    /* TITAN_FILE_BROWSER_START */
    .small-field {
      max-width: 180px;
      min-width: 150px;
      height: 40px;
    }

    .file-path {
      color: var(--muted);
      margin-bottom: 12px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
    }

    .files-layout {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 16px;
      min-height: 620px;
    }

    .file-list-wrap,
    .file-editor-wrap {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.035);
      border-radius: 18px;
      overflow: hidden;
    }

    .file-list {
      max-height: 680px;
      overflow-y: auto;
      padding: 12px;
      display: grid;
      gap: 8px;
    }

    .file-item {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 14px;
      padding: 10px 11px;
      cursor: pointer;
      transition: background .14s ease, transform .14s ease, border-color .14s ease;
    }

    .file-item:hover {
      background: rgba(255,255,255,.075);
      transform: translateY(-1px);
    }

    .file-item.active {
      border-color: rgba(232,171,67,.38);
      background: rgba(232,171,67,.09);
    }

    .file-name {
      font-weight: 800;
      font-size: 13px;
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .file-meta {
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }

    .file-editor-wrap {
      padding-bottom: 14px;
    }

    .file-editor-wrap .row {
      padding: 0 14px;
    }

    .file-editor {
      width: calc(100% - 28px);
      min-height: 390px;
      margin: 0 14px 14px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      outline: none;
      resize: vertical;
      background: rgba(0,0,0,.20);
      color: #f4f4f5;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      line-height: 1.45;
    }

    #fileStatus {
      margin: 0 14px;
      max-height: 150px;
      overflow-y: auto;
      color: var(--muted);
    }

    @media (max-width: 980px) {
      .files-layout {
        grid-template-columns: 1fr;
      }

      .file-list {
        max-height: 320px;
      }
    }
    /* TITAN_FILE_BROWSER_END */

  
    /* TITAN_PRODUCT_LAUNCHER_START */
    .product-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-top: 14px;
    }

    .product-card {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 18px;
      padding: 14px;
      display: grid;
      gap: 10px;
      min-height: 170px;
    }

    .product-title {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
      font-weight: 850;
    }

    .product-meta {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
      white-space: pre-wrap;
    }

    .product-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: auto;
    }

    @media (max-width: 980px) {
      .product-grid {
        grid-template-columns: 1fr;
      }
    }
    /* TITAN_PRODUCT_LAUNCHER_END */

  
    /* TITAN_SEARCH_DIFF_START */
    .search-layout {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 16px;
      min-height: 600px;
    }

    .search-results-wrap,
    .diff-wrap {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.035);
      border-radius: 18px;
      overflow: hidden;
    }

    .search-results {
      max-height: 680px;
      overflow-y: auto;
      padding: 12px;
      display: grid;
      gap: 10px;
    }

    .search-item {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 16px;
      padding: 12px;
      cursor: pointer;
      transition: background .14s ease, transform .14s ease;
    }

    .search-item:hover {
      background: rgba(255,255,255,.075);
      transform: translateY(-1px);
    }

    .search-title {
      font-weight: 850;
      font-size: 13px;
      margin-bottom: 6px;
    }

    .search-meta {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }

    .search-snippet {
      color: #d4d4d8;
      font-size: 12px;
      line-height: 1.4;
      white-space: pre-wrap;
    }

    #diffOut {
      max-height: 680px;
      overflow-y: auto;
      margin: 14px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(0,0,0,.18);
    }

    @media (max-width: 980px) {
      .search-layout {
        grid-template-columns: 1fr;
      }
    }
    /* TITAN_SEARCH_DIFF_END */

  
    /* TITAN_COMMAND_PALETTE_START */
    .palette-button {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.055);
      color: white;
      border-radius: 16px;
      padding: 12px 13px;
      cursor: pointer;
      text-align: left;
      font-size: 14px;
      transition: background .14s ease, transform .14s ease;
    }

    .palette-button:hover {
      background: rgba(255,255,255,.085);
      transform: translateY(-1px);
    }

    .palette-backdrop {
      position: fixed;
      inset: 0;
      z-index: 9999;
      display: none;
      align-items: flex-start;
      justify-content: center;
      padding-top: 12vh;
      background: rgba(0,0,0,.42);
      backdrop-filter: blur(10px);
    }

    .palette-backdrop.active {
      display: flex;
    }

    .palette {
      width: min(720px, calc(100vw - 28px));
      border: 1px solid rgba(255,255,255,.12);
      background:
        radial-gradient(circle at 20% -20%, rgba(232,171,67,.16), transparent 35%),
        rgba(18,19,22,.96);
      border-radius: 24px;
      box-shadow: 0 28px 80px rgba(0,0,0,.42);
      overflow: hidden;
      animation: paletteIn .14s ease both;
    }

    @keyframes paletteIn {
      from { opacity: 0; transform: translateY(8px) scale(.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    .palette-top {
      height: 64px;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
    }

    .palette-icon {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.07);
      color: #f8fafc;
      border-radius: 12px;
      padding: 8px 10px;
      font-size: 13px;
      font-weight: 800;
    }

    #paletteInput {
      flex: 1;
      border: 0;
      outline: 0;
      background: transparent;
      color: white;
      font-size: 18px;
    }

    .palette-results {
      max-height: 420px;
      overflow-y: auto;
      padding: 10px;
      display: grid;
      gap: 6px;
    }

    .palette-item {
      border: 1px solid transparent;
      background: transparent;
      color: #e5e7eb;
      border-radius: 16px;
      padding: 12px;
      display: grid;
      gap: 4px;
      cursor: pointer;
      transition: background .12s ease, border-color .12s ease;
    }

    .palette-item:hover,
    .palette-item.active {
      background: rgba(255,255,255,.075);
      border-color: rgba(232,171,67,.26);
    }

    .palette-item-title {
      font-weight: 850;
      font-size: 14px;
    }

    .palette-item-desc {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    .palette-help {
      padding: 10px 14px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
    }
    /* TITAN_COMMAND_PALETTE_END */

  
    /* TITAN_TOASTS_START */
    .toast-host {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 10000;
      display: grid;
      gap: 10px;
      width: min(390px, calc(100vw - 36px));
      pointer-events: none;
    }

    .toast {
      pointer-events: auto;
      border: 1px solid rgba(255,255,255,.12);
      background:
        radial-gradient(circle at 18% 0%, rgba(232,171,67,.18), transparent 36%),
        rgba(18,19,22,.96);
      box-shadow: 0 18px 50px rgba(0,0,0,.36);
      backdrop-filter: blur(12px);
      color: #f4f4f5;
      border-radius: 18px;
      padding: 13px 14px;
      display: grid;
      grid-template-columns: 28px 1fr auto;
      gap: 10px;
      align-items: start;
      animation: toastIn .18s ease both;
    }

    .toast.leaving {
      animation: toastOut .16s ease both;
    }

    @keyframes toastIn {
      from { opacity: 0; transform: translateY(8px) scale(.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @keyframes toastOut {
      from { opacity: 1; transform: translateY(0) scale(1); }
      to { opacity: 0; transform: translateY(8px) scale(.98); }
    }

    .toast-icon {
      width: 28px;
      height: 28px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      background: rgba(255,255,255,.075);
      font-size: 15px;
    }

    .toast.success .toast-icon {
      background: rgba(34,197,94,.14);
      color: #22c55e;
    }

    .toast.error .toast-icon {
      background: rgba(251,113,133,.16);
      color: #fb7185;
    }

    .toast.warn .toast-icon {
      background: rgba(251,191,36,.14);
      color: #fbbf24;
    }

    .toast.info .toast-icon {
      background: rgba(96,165,250,.14);
      color: #60a5fa;
    }

    .toast-title {
      font-weight: 850;
      font-size: 14px;
      margin-bottom: 3px;
    }

    .toast-body {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .toast-close {
      border: 0;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font-size: 18px;
      line-height: 1;
      padding: 0 2px;
    }

    .toast-close:hover {
      color: white;
    }
    /* TITAN_TOASTS_END */

  
    /* TITAN_CHAT_HISTORY_START */
    .history-layout {
      display: grid;
      grid-template-columns: 300px 1fr;
      gap: 16px;
      min-height: 560px;
    }

    .history-side,
    .history-main {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.035);
      border-radius: 18px;
      overflow: hidden;
    }

    .history-list {
      max-height: 620px;
      overflow-y: auto;
      padding: 12px;
      display: grid;
      gap: 8px;
    }

    .history-section-item {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.045);
      border-radius: 14px;
      padding: 10px;
      cursor: pointer;
      transition: background .14s ease, transform .14s ease;
    }

    .history-section-item:hover {
      background: rgba(255,255,255,.075);
      transform: translateY(-1px);
    }

    .history-section-item.active {
      border-color: rgba(232,171,67,.38);
      background: rgba(232,171,67,.09);
    }

    .history-section-name {
      font-weight: 850;
      font-size: 13px;
    }

    .history-section-meta {
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }

    #historyOut {
      max-height: 620px;
      overflow-y: auto;
      margin: 14px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: rgba(0,0,0,.18);
    }

    @media (max-width: 980px) {
      .history-layout {
        grid-template-columns: 1fr;
      }
    }
    /* TITAN_CHAT_HISTORY_END */

  
/* TITAN_VIDEO_DASHBOARD_V3 */
.video-item { border: 1px solid var(--line); background: rgba(255,255,255,.045); border-radius: 14px; padding: 10px; margin: 8px; cursor: pointer; }
#videoOut { max-height: 500px; overflow-y: auto; margin: 14px; padding: 14px; border-radius: 16px; border: 1px solid var(--line); background: rgba(0,0,0,.18); }

</style>
</head>
<body>
  <div class="app">
    <aside>
      
      <div class="brand">
        <div class="titan-mascot titan-mascot-sm titan-face" data-eye-scale="0.9" aria-hidden="true">
          <div class="seg seg-y"></div>
          <div class="seg seg-o"></div>
          <div class="seg seg-r"></div>

          <div class="eye-wrap eye-left"><div class="eye-core"></div></div>
          <div class="eye-wrap eye-right"><div class="eye-core"></div></div>
        </div>
        <span>Titan</span>
      </div>

      <nav>
        <button class="active" onclick="showView('chat', this)">💬 Chat</button>
        <button onclick="showView('video', this); loadVideos()">▣ Video</button>
        <button onclick="showView('history', this); loadHistory()">▤ History</button>
        <button onclick="showView('jobs', this); loadJobs()">▣ Jobs</button>
        <button onclick="showView('files', this); loadFiles()">🗂 Files</button>
        <button onclick="showView('search', this)">🔎 Search / Diff</button>
        <button onclick="showView('products', this); loadProducts()">◇ Products</button>
        <button onclick="showView('skills', this); loadSkills()">✧ Skills</button>
        <button onclick="showView('memory', this); loadMemory()">🧠 Memory</button>
        <button onclick="showView('rag', this); loadRag()">⌕ RAG</button>
        <button onclick="showView('models', this); loadModels()">☷ Models</button>
        <button onclick="showView('permissions', this); loadMode()">⚙ Permissions</button>
      </nav>

      <button class="palette-button" onclick="openCommandPalette()">⌘K Command Palette</button>

      <div class="side-footer">
        Local Titan<br>
        Dashboard: 5050<br>
        Models: Ollama local
      </div>
    </aside>

    <main>
      <div class="shell">
        <section class="hero">
          <div class="mascot-wrap">
            <div class="mascot-glow"></div>
            <div class="titan-mascot titan-mascot-lg titan-face floating" id="titanMascot" data-eye-scale="1.6">
              <div class="seg seg-y"></div>
              <div class="seg seg-o"></div>
              <div class="seg seg-r"></div>

              <div class="eye-wrap eye-left"><div class="eye-core"></div></div>
              <div class="eye-wrap eye-right"><div class="eye-core"></div></div>
            </div>
          </div>
        </section>

        
        <section id="view-history" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Chat History / Project Sections</strong>
              <button class="btn" onclick="loadHistory()">Refresh</button>
            </div>

            <div class="panel-body">
              <div class="row">
                <input class="field" id="sectionName" placeholder="section name, e.g. Dashboard Config">
                <button class="btn primary" onclick="setHistorySection()">Set Section</button>
                <button class="btn" onclick="loadSections()">Sections</button>
                <button class="btn" onclick="exportHistory()">Export Current</button>
                <button class="btn" onclick="exportAllSections()">Export All Sections</button>
              </div>

              <div class="row">
                <input class="field" id="historyQuery" placeholder="search chat history">
                <button class="btn" onclick="searchHistory()">Search</button>
              </div>

              <div class="history-layout">
                <div class="history-side">
                  <div class="section-title">Sections</div>
                  <div id="sectionsOut" class="history-list">Loading...</div>
                </div>

                <div class="history-main">
                  <div class="section-title" id="historyTitle">History</div>
                  <pre id="historyOut">Loading...</pre>
                </div>
              </div>
            </div>
          </div>
        </section>


        
        <section id="view-video" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Video Studio</strong>
              <button class="btn" onclick="loadVideoStatus()">Status</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <select class="field small-field" id="videoQuality"><option value="low">low</option><option value="medium" selected>medium</option><option value="high">high</option></select>
                <button class="btn" onclick="setVideoQuality()">Set Quality</button>
                <select class="field small-field" id="videoMotion"><option value="low">low</option><option value="medium">medium</option><option value="high" selected>high</option></select>
                <button class="btn" onclick="setVideoMotion()">Set Motion</button>
                <select class="field small-field" id="videoImageBackend"><option value="pollinations" selected>pollinations</option><option value="comfyui">comfyui</option><option value="local">local</option></select>
                <button class="btn" onclick="setVideoImageBackend()">Set Backend</button>
              </div>
              <textarea id="videoPrompt" class="file-editor" placeholder="Describe the video...">a cute Titan three-bar mascot building a neon trading dashboard, animated charts, typing code, glowing terminal</textarea>
              <div class="row">
                <button class="btn primary" onclick="createDashboardVideo()">Create Video</button>
                <button class="btn" onclick="loadVideos()">Refresh Videos</button>
              </div>
              <pre id="videoOut">Video output appears here.</pre>
              <div id="videoList" class="history-list">No videos loaded.</div>
            </div>
          </div>
        </section>


<section id="view-chat" class="view active">
          <form class="composer" onsubmit="sendChat(event)">
            <input id="chatInput" placeholder="Ask Titan..." autocomplete="off">
            <button class="btn primary" type="submit">↑</button>
          </form>

          <div class="panel">
            <div class="panel-head">
              <strong>Titan Chat</strong>
              <button class="btn" onclick="clearChat()">Clear</button>
            </div>
            <div class="messages" id="messages">
              <div class="msg"><small>Titan</small>Ready. Ask me to build, inspect, search, remember, index, or run jobs.</div>
            </div>
          </div>

          <div class="grid">
            <div class="card" onclick="quick('Show me the workspace tree.')"><div>🗂</div><h3>Workspace</h3><p>Inspect files and project structure.</p></div>
            <div class="card" onclick="quick('Search RAG for Titan dashboard port and summarize the result.')"><div>⌕</div><h3>RAG Search</h3><p>Use local knowledge.</p></div>
            <div class="card" onclick="quick('List my skills.')"><div>✧</div><h3>Skills</h3><p>Show reusable workflows.</p></div>
          </div>
        </section>

        
        <section id="view-jobs" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Jobs / Live Trace</strong>
              <div class="row compact-row">
                <label class="toggle-label">
                  <input type="checkbox" id="jobsAutoRefresh" checked>
                  Auto-refresh
                </label>
                <button class="btn" onclick="loadJobs()">Refresh</button>
              </div>
            </div>

            <div class="panel-body">
              <div class="jobs-layout">
                <div class="job-list-wrap">
                  <div class="section-title">Recent Jobs</div>
                  <div id="jobsList" class="job-list">Loading...</div>
                </div>

                <div class="job-detail-wrap">
                  <div class="section-title" id="selectedJobTitle">Select a job</div>

                  <div class="job-tabs">
                    <button class="btn active" onclick="showJobTab('summary', this)">Summary</button>
                    <button class="btn" onclick="showJobTab('result', this)">Result</button>
                    <button class="btn" onclick="showJobTab('trace', this)">Trace</button>
                    <button class="btn" onclick="showJobTab('log', this)">Log</button>
                  </div>

                  <div class="job-pane active" id="jobPane-summary">
                    <pre id="jobSummary">No job selected.</pre>
                  </div>

                  <div class="job-pane" id="jobPane-result">
                    <pre id="jobResult">No result yet.</pre>
                  </div>

                  <div class="job-pane" id="jobPane-trace">
                    <pre id="jobTrace">No trace yet.</pre>
                  </div>

                  <div class="job-pane" id="jobPane-log">
                    <pre id="jobLog">No log yet.</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>


        
        
        <section id="view-search" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Search / Diff</strong>
              <button class="btn" onclick="searchFiles()">Search</button>
            </div>

            <div class="panel-body">
              <div class="row">
                <select class="field small-field" id="searchRoot">
                  <option value="all">all</option>
                  <option value="workspace">workspace</option>
                  <option value="products">products</option>
                  <option value="skills">skills</option>
                  <option value="rag">rag/docs</option>
                  <option value="docs">docs</option>
                  <option value="downloads">downloads</option>
                </select>
                <input class="field" id="searchQuery" placeholder="search file names or content">
                <button class="btn primary" onclick="searchFiles()">Search</button>
              </div>

              <div class="row">
                <select class="field small-field" id="snapshotRoot">
                  <option value="workspace">workspace</option>
                  <option value="products">products</option>
                  <option value="skills">skills</option>
                  <option value="rag">rag/docs</option>
                  <option value="docs">docs</option>
                </select>
                <button class="btn" onclick="makeSnapshot()">Snapshot</button>
                <button class="btn" onclick="showChanged()">Changed</button>
              </div>

              <div class="search-layout">
                <div class="search-results-wrap">
                  <div class="section-title">Results</div>
                  <div id="searchResults" class="search-results">Search results will appear here.</div>
                </div>

                <div class="diff-wrap">
                  <div class="section-title" id="diffTitle">Diff</div>
                  <pre id="diffOut">Select a changed file or search result.</pre>
                </div>
              </div>
            </div>
          </div>
        </section>


        <section id="view-files" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>File Browser</strong>
              <div class="row compact-row">
                <select class="field small-field" id="fileRoot" onchange="changeFileRoot()">
                  <option value="workspace">workspace</option>
                  <option value="products">products</option>
                  <option value="skills">skills</option>
                  <option value="rag">rag/docs</option>
                  <option value="docs">docs</option>
                  <option value="downloads">downloads</option>
                </select>
                <button class="btn" onclick="loadFiles()">Refresh</button>
                <button class="btn" onclick="fileUp()">Up</button>
              </div>
            </div>

            <div class="panel-body">
              <div class="file-path" id="filePath">/</div>

              <div class="files-layout">
                <div class="file-list-wrap">
                  <div class="section-title">Files</div>
                  <div id="fileList" class="file-list">Loading...</div>
                </div>

                <div class="file-editor-wrap">
                  <div class="section-title" id="editorTitle">No file selected</div>

                  <div class="row">
                    <input class="field" id="newFilePath" placeholder="new file path, e.g. notes/todo.md">
                    <button class="btn" onclick="createFileFromInput()">New File</button>
                  </div>

                  <div class="row">
                    <input class="field" id="newFolderPath" placeholder="new folder path, e.g. notes">
                    <button class="btn" onclick="createFolderFromInput()">New Folder</button>
                  </div>

                  <textarea id="fileEditor" class="file-editor" placeholder="Open or create a text file..."></textarea>

                  <div class="row">
                    <button class="btn primary" onclick="saveOpenFile()">Save</button>
                    <button class="btn" onclick="reloadOpenFile()">Reload</button>
                  </div>

                  <pre id="fileStatus"></pre>
                </div>
              </div>
            </div>
          </div>
        </section>


        
        <section id="view-products" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Products</strong>
              <button class="btn" onclick="loadProducts()">Refresh</button>
            </div>

            <div class="panel-body">
              <div class="row">
                <input class="field" id="productName" placeholder="product name">
                <select class="field small-field" id="productKind">
                  <option value="python_cli">python_cli</option>
                  <option value="flask_app">flask_app</option>
                  <option value="static_website">static_website</option>
                </select>
                <button class="btn" onclick="createProduct()">Create</button>
              </div>

              <div id="productsGrid" class="product-grid">Loading...</div>
              <pre id="productStatus"></pre>
            </div>
          </div>
        </section>


        <section id="view-skills" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Skills</strong>
              <button class="btn" onclick="loadSkills()">Refresh</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <input class="field" id="skillName" placeholder="skill name">
                <input class="field" id="skillDesc" placeholder="description">
                <button class="btn" onclick="createSkill()">Create</button>
              </div>
              <pre id="skillsOut">Loading...</pre>
            </div>
          </div>
        </section>

        <section id="view-memory" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Memory</strong>
              <button class="btn" onclick="loadMemory()">Refresh</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <input class="field" id="memoryText" placeholder="memory to save">
                <button class="btn" onclick="saveMemory()">Remember</button>
              </div>
              <div class="row">
                <input class="field" id="memoryQuery" placeholder="search memories">
                <button class="btn" onclick="searchMemory()">Search</button>
              </div>
              <pre id="memoryOut">Loading...</pre>
            </div>
          </div>
        </section>

        <section id="view-rag" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>RAG</strong>
              <div>
                <button class="btn" onclick="loadRag()">Status</button>
                <button class="btn" onclick="indexRag()">Index</button>
              </div>
            </div>
            <div class="panel-body">
              <div class="row">
                <input class="field" id="ragQuery" placeholder="search RAG">
                <button class="btn" onclick="searchRag()">Search</button>
              </div>
              <pre id="ragOut">Loading...</pre>
            </div>
          </div>
        </section>

        <section id="view-models" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Models</strong>
              <button class="btn" onclick="loadModels()">Refresh</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <button class="btn" onclick="setProfile('tiny')">Tiny</button>
                <button class="btn" onclick="setProfile('fast')">Fast</button>
                <button class="btn" onclick="setProfile('coder')">Coder</button>
                <button class="btn" onclick="setProfile('smart')">Smart</button>
                <button class="btn" onclick="setProfile('heavy')">Heavy</button>
                <button class="btn" onclick="setProfile('max')">Max</button>
              </div>
              <pre id="modelsOut">Loading...</pre>
            </div>
          </div>
        </section>

        <section id="view-permissions" class="view">
          <div class="panel">
            <div class="panel-head">
              <strong>Permissions</strong>
              <button class="btn" onclick="loadMode()">Refresh</button>
            </div>
            <div class="panel-body">
              <div class="row">
                <button class="btn" onclick="setMode('safe')">Safe</button>
                <button class="btn" onclick="setMode('power')">Power</button>
                <button class="btn" onclick="setMode('agentic')">Agentic</button>
              </div>
              <div class="row">
                <input class="field" id="runCmd" placeholder="approved shell command">
                <button class="btn" onclick="runCommand()">Run</button>
              </div>
              <pre id="modeOut">Loading...</pre>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>

<script>
const titanMascot = document.getElementById("titanMascot");

function blinkTitan() {
  document.querySelectorAll(".titan-logo").forEach(el => el.classList.add("blink"));
  setTimeout(() => {
    document.querySelectorAll(".titan-logo").forEach(el => el.classList.remove("blink"));
  }, 130);
}

setInterval(blinkTitan, 30000);

window.addEventListener("mousemove", event => {
  if (!titanMascot) return;

  const rect = titanMascot.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;

  const dx = Math.max(-1, Math.min(1, (event.clientX - cx) / 500));
  const dy = Math.max(-1, Math.min(1, (event.clientY - cy) / 500));

  titanMascot.style.translate = `${dx * 5}px ${dy * 5}px`;
});

function showView(name, btn) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById("view-" + name).classList.add("active");
  document.querySelectorAll("nav button").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
}

function addMessage(role, text) {
  const box = document.getElementById("messages");
  const d = document.createElement("div");
  d.className = "msg " + (role === "user" ? "user" : "");
  d.innerHTML = "<small>" + (role === "user" ? "You" : "Titan") + "</small>";
  const body = document.createElement("div");
  body.textContent = typeof text === "string" ? text : JSON.stringify(text, null, 2);
  d.appendChild(body);
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}

function clearChat() {
  document.getElementById("messages").innerHTML = "";
  addMessage("assistant", "Clean slate.");
}

async function jsonFetch(url, options={}) {
  const res = await fetch(url, options);
  return await res.json();
}

async function sendChat(event) {
  event.preventDefault();
  const input = document.getElementById("chatInput");
  const task = input.value.trim();
  if (!task) return;
  input.value = "";
  await quick(task);
}

async function quick(task) {
  addMessage("user", task);
  addMessage("assistant", "Started background job...");
  const data = await jsonFetch("/api/task", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({task})
  });
  if (data.error) {
    addMessage("assistant", data.error);
    return;
  }
  addMessage("assistant", "Job: " + data.job_id);
  pollJob(data.job_id);
}

async function pollJob(id) {
  for (let i = 0; i < 240; i++) {
    const data = await jsonFetch("/api/job/" + encodeURIComponent(id));
    if (data.status === "done" || data.status === "error" || data.status === "cancelled") {
      addMessage("assistant", data.result || data.error || JSON.stringify(data, null, 2));
      return;
    }
    await new Promise(r => setTimeout(r, 1500));
  }
  addMessage("assistant", "Job still running: " + id);
}

async function loadJobs() {
  document.getElementById("jobsOut").textContent = JSON.stringify(await jsonFetch("/api/jobs"), null, 2);
}

async function loadSkills() {
  document.getElementById("skillsOut").textContent = (await jsonFetch("/api/skills")).result;
}

async function createSkill() {
  const name = document.getElementById("skillName").value.trim();
  const description = document.getElementById("skillDesc").value.trim();
  document.getElementById("skillsOut").textContent = JSON.stringify(await jsonFetch("/api/skills/create", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({name, description})
  }), null, 2);
}

async function loadMemory() {
  document.getElementById("memoryOut").textContent = (await jsonFetch("/api/memory")).result;
}

async function saveMemory() {
  const text = document.getElementById("memoryText").value.trim();
  document.getElementById("memoryOut").textContent = JSON.stringify(await jsonFetch("/api/memory/save", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({text})
  }), null, 2);
}

async function searchMemory() {
  const q = document.getElementById("memoryQuery").value.trim();
  document.getElementById("memoryOut").textContent = (await jsonFetch("/api/memory/search?q=" + encodeURIComponent(q))).result;
}

async function loadRag() {
  document.getElementById("ragOut").textContent = (await jsonFetch("/api/rag")).result;
}

async function indexRag() {
  document.getElementById("ragOut").textContent = "Indexing...";
  document.getElementById("ragOut").textContent = JSON.stringify(await jsonFetch("/api/rag/index", {method:"POST"}), null, 2);
}

async function searchRag() {
  const q = document.getElementById("ragQuery").value.trim();
  document.getElementById("ragOut").textContent = (await jsonFetch("/api/rag/search?q=" + encodeURIComponent(q))).result;
}

async function loadModels() {
  document.getElementById("modelsOut").textContent = JSON.stringify(await jsonFetch("/api/models"), null, 2);
}

async function setProfile(profile) {
  document.getElementById("modelsOut").textContent = JSON.stringify(await jsonFetch("/api/models/profile", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({profile})
  }), null, 2);
}

async function loadMode() {
  document.getElementById("modeOut").textContent = (await jsonFetch("/api/mode")).result;
}

async function setMode(mode) {
  document.getElementById("modeOut").textContent = JSON.stringify(await jsonFetch("/api/mode", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({mode})
  }), null, 2);
}

async function runCommand() {
  const command = document.getElementById("runCmd").value.trim();
  document.getElementById("modeOut").textContent = JSON.stringify(await jsonFetch("/api/run", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({command})
  }), null, 2);
}

window.addEventListener("DOMContentLoaded", () => {
  const faces = Array.from(document.querySelectorAll(".titan-face"));

  function blinkAll() {
    faces.forEach(face => face.classList.add("blink"));
    setTimeout(() => faces.forEach(face => face.classList.remove("blink")), 130);
  }

  setInterval(blinkAll, 30000);

  window.addEventListener("mousemove", (e) => {
    faces.forEach(face => {
      const rect = face.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;

      let dx = (e.clientX - cx) / rect.width;
      let dy = (e.clientY - cy) / rect.height;

      dx = Math.max(-1, Math.min(1, dx));
      dy = Math.max(-1, Math.min(1, dy));

      const scale = parseFloat(face.dataset.eyeScale || "1");
      const moveX = dx * 1.8 * scale;
      const moveY = dy * 1.2 * scale;

      face.querySelectorAll(".eye-core").forEach(eye => {
        eye.style.transform = `translate(${moveX}px, ${moveY}px)`;
      });
    });
  });
});



// TITAN_PREVIEW_MASCOT_JS_START
window.addEventListener("DOMContentLoaded", () => {
  const faces = Array.from(document.querySelectorAll(".titan-face"));

  function blinkAll(duration = 170) {
    faces.forEach(face => face.classList.add("blink"));
    setTimeout(() => {
      faces.forEach(face => face.classList.remove("blink"));
    }, duration);
  }

  function doubleBlink() {
    blinkAll(170);
    setTimeout(() => blinkAll(150), 240);
  }

  /* quick startup blink so you know it works */
  setTimeout(() => blinkAll(180), 900);

  /* more visible than every 30 sec */
  setInterval(() => {
    if (Math.random() < 0.35) {
      doubleBlink();
    } else {
      blinkAll(180);
    }
  }, 12000);

  window.addEventListener("mousemove", (e) => {
    faces.forEach(face => {
      const rect = face.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;

      let dx = (e.clientX - cx) / rect.width;
      let dy = (e.clientY - cy) / rect.height;

      dx = Math.max(-1, Math.min(1, dx));
      dy = Math.max(-1, Math.min(1, dy));

      const scale = parseFloat(face.dataset.eyeScale || "1");
      const mx = dx * 1.0 * scale;
      const my = dy * 0.75 * scale;

      face.querySelectorAll(".eye-core").forEach(eye => {
        eye.style.transform = `translate(${mx}px, ${my}px)`;
      });
    });
  });
});
// TITAN_PREVIEW_MASCOT_JS_END



// TITAN_LIVE_TRACE_VIEWER_JS_START
let selectedJobId = null;
let jobsRefreshTimer = null;

function statusClass(status) {
  status = String(status || "").toLowerCase();
  if (["running", "queued", "done", "error", "cancelled"].includes(status)) return status;
  return "";
}

function compactTask(text, max = 180) {
  text = String(text || "");
  return text.length > max ? text.slice(0, max) + "..." : text;
}

function showJobTab(name, btn) {
  document.querySelectorAll(".job-pane").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".job-tabs .btn").forEach(b => b.classList.remove("active"));
  const pane = document.getElementById("jobPane-" + name);
  if (pane) pane.classList.add("active");
  if (btn) btn.classList.add("active");
}

async function loadJobs() {
  const data = await jsonFetch("/api/jobs");
  const jobs = data.jobs || [];
  const list = document.getElementById("jobsList");

  if (!list) return;

  if (!jobs.length) {
    list.textContent = "No jobs yet.";
    return;
  }

  list.innerHTML = "";

  jobs.forEach(job => {
    const card = document.createElement("div");
    card.className = "job-card" + (job.id === selectedJobId ? " active" : "");
    card.onclick = () => selectJob(job.id);

    const title = document.createElement("div");
    title.className = "job-card-title";

    const id = document.createElement("span");
    id.textContent = job.id || "unknown-job";

    const status = document.createElement("span");
    status.className = "status-pill " + statusClass(job.status);
    status.textContent = job.status || "unknown";

    title.appendChild(id);
    title.appendChild(status);

    const task = document.createElement("div");
    task.className = "job-card-task";
    task.textContent = compactTask(job.task || "(no task)");

    card.appendChild(title);
    card.appendChild(task);
    list.appendChild(card);
  });

  if (!selectedJobId && jobs[0] && jobs[0].id) {
    selectJob(jobs[0].id);
  }
}

async function selectJob(id) {
  selectedJobId = id;
  document.querySelectorAll(".job-card").forEach(c => c.classList.remove("active"));

  const title = document.getElementById("selectedJobTitle");
  if (title) title.textContent = "Job: " + id;

  await loadJobDetail(id);
  await loadJobs();
}

async function loadJobDetail(id) {
  if (!id) return;

  const data = await jsonFetch("/api/job/" + encodeURIComponent(id));

  const summary = {
    id: data.id,
    status: data.status,
    source: data.source,
    created_at: data.created_at,
    started_at: data.started_at,
    finished_at: data.finished_at,
    task: data.task,
    error: data.error
  };

  const summaryEl = document.getElementById("jobSummary");
  const resultEl = document.getElementById("jobResult");
  const traceEl = document.getElementById("jobTrace");
  const logEl = document.getElementById("jobLog");

  if (summaryEl) summaryEl.textContent = JSON.stringify(summary, null, 2);
  if (resultEl) resultEl.textContent = data.result || "(no result yet)";
  if (traceEl) traceEl.textContent = data.trace || "(no trace yet)";
  if (logEl) logEl.textContent = data.log || "(no log yet)";
}

function ensureJobsAutoRefresh() {
  if (jobsRefreshTimer) clearInterval(jobsRefreshTimer);

  jobsRefreshTimer = setInterval(async () => {
    const auto = document.getElementById("jobsAutoRefresh");
    const jobsView = document.getElementById("view-jobs");

    if (!auto || !auto.checked) return;
    if (!jobsView || !jobsView.classList.contains("active")) return;

    await loadJobs();
    if (selectedJobId) await loadJobDetail(selectedJobId);
  }, 2500);
}

setTimeout(ensureJobsAutoRefresh, 500);

// Patch quick chat job output to include a visible trace hint.
const oldQuickTitan = typeof quick === "function" ? quick : null;
if (oldQuickTitan) {
  quick = async function(task) {
    addMessage("user", task);
    addMessage("assistant", "Started background job...");
    const data = await jsonFetch("/api/task", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({task})
    });

    if (data.error) {
      addMessage("assistant", data.error);
      return;
    }

    addMessage("assistant", "Job: " + data.job_id + "\nOpen Jobs tab to watch trace/log live.");
    selectedJobId = data.job_id;
    pollJob(data.job_id);
  }
}
// TITAN_LIVE_TRACE_VIEWER_JS_END


// TITAN_FILE_BROWSER_JS_START
let currentFileRoot = "workspace";
let currentFilePath = "";
let currentOpenFile = "";

async function changeFileRoot() {
  currentFileRoot = document.getElementById("fileRoot").value;
  currentFilePath = "";
  currentOpenFile = "";
  document.getElementById("fileEditor").value = "";
  document.getElementById("editorTitle").textContent = "No file selected";
  await loadFiles();
}

async function loadFiles(pathOverride = null) {
  if (pathOverride !== null) currentFilePath = pathOverride;

  const rootEl = document.getElementById("fileRoot");
  if (rootEl) currentFileRoot = rootEl.value;

  const url = `/api/files?root=${encodeURIComponent(currentFileRoot)}&path=${encodeURIComponent(currentFilePath)}`;
  const data = await jsonFetch(url);

  const filePath = document.getElementById("filePath");
  const fileList = document.getElementById("fileList");

  if (filePath) filePath.textContent = `${data.root || currentFileRoot}:/${data.path || ""}`;

  if (data.error) {
    fileList.textContent = data.error;
    return;
  }

  fileList.innerHTML = "";

  if (!data.items || !data.items.length) {
    fileList.textContent = "Empty folder.";
    return;
  }

  data.items.forEach(item => {
    const div = document.createElement("div");
    div.className = "file-item" + (item.path === currentOpenFile ? " active" : "");
    div.onclick = () => {
      if (item.type === "dir") {
        openFolder(item.path);
      } else {
        openFile(item.path);
      }
    };

    const name = document.createElement("div");
    name.className = "file-name";
    name.textContent = (item.type === "dir" ? "📁 " : "📄 ") + item.name;

    const meta = document.createElement("div");
    meta.className = "file-meta";
    meta.textContent = item.type + (item.size !== null && item.size !== undefined ? ` · ${item.size} bytes` : "") + ` · ${item.modified || ""}`;

    div.appendChild(name);
    div.appendChild(meta);
    fileList.appendChild(div);
  });
}

async function openFolder(path) {
  currentFilePath = path || "";
  await loadFiles(currentFilePath);
}

async function fileUp() {
  const parts = String(currentFilePath || "").split("/").filter(Boolean);
  parts.pop();
  currentFilePath = parts.join("/");
  await loadFiles(currentFilePath);
}

async function openFile(path) {
  currentOpenFile = path;
  const data = await jsonFetch(`/api/file?root=${encodeURIComponent(currentFileRoot)}&path=${encodeURIComponent(path)}`);

  const editor = document.getElementById("fileEditor");
  const title = document.getElementById("editorTitle");
  const status = document.getElementById("fileStatus");

  if (data.error) {
    status.textContent = data.error;
    return;
  }

  title.textContent = `${currentFileRoot}:/${data.path}`;
  editor.value = data.content || "";
  status.textContent = `Opened ${data.path} · ${data.size} bytes · ${data.modified}`;
  await loadFiles();
}

async function saveOpenFile() {
  const status = document.getElementById("fileStatus");

  if (!currentOpenFile) {
    status.textContent = "No file selected.";
    return;
  }

  const content = document.getElementById("fileEditor").value;

  const data = await jsonFetch("/api/file/save", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      root: currentFileRoot,
      path: currentOpenFile,
      content
    })
  });

  status.textContent = JSON.stringify(data, null, 2);
  await loadFiles();
}

async function reloadOpenFile() {
  if (currentOpenFile) await openFile(currentOpenFile);
}

async function createFileFromInput() {
  const input = document.getElementById("newFilePath");
  const status = document.getElementById("fileStatus");
  const rel = input.value.trim();

  if (!rel) {
    status.textContent = "Enter a file path.";
    return;
  }

  const base = currentFilePath ? currentFilePath + "/" : "";
  currentOpenFile = base + rel;

  const data = await jsonFetch("/api/file/save", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      root: currentFileRoot,
      path: currentOpenFile,
      content: ""
    })
  });

  status.textContent = JSON.stringify(data, null, 2);
  input.value = "";
  await loadFiles();
  await openFile(currentOpenFile);
}

async function createFolderFromInput() {
  const input = document.getElementById("newFolderPath");
  const status = document.getElementById("fileStatus");
  const rel = input.value.trim();

  if (!rel) {
    status.textContent = "Enter a folder path.";
    return;
  }

  const base = currentFilePath ? currentFilePath + "/" : "";
  const folderPath = base + rel;

  const data = await jsonFetch("/api/folder/create", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      root: currentFileRoot,
      path: folderPath
    })
  });

  status.textContent = JSON.stringify(data, null, 2);
  input.value = "";
  await loadFiles();
}
// TITAN_FILE_BROWSER_JS_END


// TITAN_PRODUCT_LAUNCHER_JS_START
async function loadProducts() {
  const data = await jsonFetch("/api/product/list");
  const grid = document.getElementById("productsGrid");
  const status = document.getElementById("productStatus");

  if (!grid) return;

  const products = data.products || [];

  if (!products.length) {
    grid.textContent = "No products yet.";
    if (status) status.textContent = "";
    return;
  }

  grid.innerHTML = "";

  products.forEach(p => {
    const card = document.createElement("div");
    card.className = "product-card";

    const title = document.createElement("div");
    title.className = "product-title";

    const name = document.createElement("span");
    name.textContent = p.name;

    const pill = document.createElement("span");
    pill.className = "status-pill " + (p.running ? "done" : "");
    pill.textContent = p.running ? "running" : "stopped";

    title.appendChild(name);
    title.appendChild(pill);

    const meta = document.createElement("div");
    meta.className = "product-meta";
    meta.textContent = `kind: ${p.kind}\nurl: ${p.url || "-"}\npid: ${p.pid || "-"}\npath: ${p.path}`;

    const actions = document.createElement("div");
    actions.className = "product-actions";

    const start = document.createElement("button");
    start.className = "btn";
    start.textContent = "Start";
    start.onclick = () => startProduct(p.name);

    const stop = document.createElement("button");
    stop.className = "btn";
    stop.textContent = "Stop";
    stop.onclick = () => stopProduct(p.name);

    const logs = document.createElement("button");
    logs.className = "btn";
    logs.textContent = "Logs";
    logs.onclick = () => productLogs(p.name);

    actions.appendChild(start);
    actions.appendChild(stop);
    actions.appendChild(logs);

    if (p.url) {
      const open = document.createElement("button");
      open.className = "btn primary";
      open.textContent = "Open";
      open.onclick = () => window.open(p.url, "_blank");
      actions.appendChild(open);
    }

    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(actions);
    grid.appendChild(card);
  });
}

async function createProduct() {
  const name = document.getElementById("productName").value.trim();
  const kind = document.getElementById("productKind").value;
  const status = document.getElementById("productStatus");

  if (!name) {
    status.textContent = "Enter a product name.";
    return;
  }

  const data = await jsonFetch("/api/product/create", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name, kind, description: "Created from Titan dashboard."})
  });

  status.textContent = JSON.stringify(data, null, 2);
  await loadProducts();
}

async function startProduct(name) {
  const status = document.getElementById("productStatus");
  const data = await jsonFetch("/api/product/start", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name})
  });
  status.textContent = JSON.stringify(data, null, 2);
  await loadProducts();
}

async function stopProduct(name) {
  const status = document.getElementById("productStatus");
  const data = await jsonFetch("/api/product/stop", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({name})
  });
  status.textContent = JSON.stringify(data, null, 2);
  await loadProducts();
}

async function productLogs(name) {
  const status = document.getElementById("productStatus");
  const data = await jsonFetch("/api/product/logs?name=" + encodeURIComponent(name));
  status.textContent = JSON.stringify(data, null, 2);
}
// TITAN_PRODUCT_LAUNCHER_JS_END


// TITAN_SEARCH_DIFF_JS_START
async function searchFiles() {
  const root = document.getElementById("searchRoot").value;
  const q = document.getElementById("searchQuery").value.trim();
  const out = document.getElementById("searchResults");

  if (!q) {
    out.textContent = "Enter a search query.";
    return;
  }

  const data = await jsonFetch(`/api/search?root=${encodeURIComponent(root)}&q=${encodeURIComponent(q)}`);

  if (data.error) {
    out.textContent = data.error;
    return;
  }

  const results = data.results || [];

  if (!results.length) {
    out.textContent = "No results.";
    return;
  }

  out.innerHTML = "";

  results.forEach(item => {
    const div = document.createElement("div");
    div.className = "search-item";
    div.onclick = () => loadDiff(item.root, item.path);

    const title = document.createElement("div");
    title.className = "search-title";
    title.textContent = `${item.root}:/${item.path}`;

    const meta = document.createElement("div");
    meta.className = "search-meta";
    meta.textContent = `${item.match} · ${item.size} bytes`;

    const snippet = document.createElement("div");
    snippet.className = "search-snippet";
    snippet.textContent = item.snippet || "Click to diff against snapshot.";

    div.appendChild(title);
    div.appendChild(meta);
    div.appendChild(snippet);
    out.appendChild(div);
  });
}

async function makeSnapshot() {
  const root = document.getElementById("snapshotRoot").value;
  const out = document.getElementById("diffOut");
  const data = await jsonFetch("/api/snapshot", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({root})
  });
  out.textContent = JSON.stringify(data, null, 2);
}

async function showChanged() {
  const root = document.getElementById("snapshotRoot").value;
  const out = document.getElementById("searchResults");
  const data = await jsonFetch(`/api/changed?root=${encodeURIComponent(root)}`);

  if (data.error) {
    out.textContent = data.error;
    return;
  }

  const changed = data.changed || [];

  if (!changed.length) {
    out.textContent = "No changed files.";
    return;
  }

  out.innerHTML = "";

  changed.forEach(item => {
    const div = document.createElement("div");
    div.className = "search-item";
    div.onclick = () => loadDiff(item.root, item.path);

    const title = document.createElement("div");
    title.className = "search-title";
    title.textContent = `${item.status}: ${item.root}:/${item.path}`;

    const meta = document.createElement("div");
    meta.className = "search-meta";
    meta.textContent = `snapshot: ${data.snapshot_created_at || "-"}`;

    div.appendChild(title);
    div.appendChild(meta);
    out.appendChild(div);
  });

  document.getElementById("diffOut").textContent = JSON.stringify(data, null, 2);
}

async function loadDiff(root, path) {
  const out = document.getElementById("diffOut");
  const title = document.getElementById("diffTitle");
  title.textContent = `Diff: ${root}:/${path}`;
  const data = await jsonFetch(`/api/diff?root=${encodeURIComponent(root)}&path=${encodeURIComponent(path)}`);
  out.textContent = data.diff || data.error || JSON.stringify(data, null, 2);
}
// TITAN_SEARCH_DIFF_JS_END


// TITAN_COMMAND_PALETTE_JS_START
let paletteIndex = 0;
let paletteFiltered = [];

const paletteCommands = [
  {
    title: "Open Chat",
    desc: "Go to Titan chat.",
    keywords: "chat home",
    run: () => clickNavByView("chat")
  },
  {
    title: "Open History",
    desc: "Open chat history and project sections.",
    keywords: "history sections logs chat project tasks sessions",
    run: () => { clickNavByView("history"); loadHistory(); }
  },
  {
    title: "Refresh History",
    desc: "Reload chat history and sections.",
    keywords: "refresh history sections logs",
    run: () => loadHistory()
  },
  {
    title: "Export History",
    desc: "Export the current chat history section to Markdown.",
    keywords: "export history markdown project logs sections",
    run: () => { clickNavByView("history"); exportHistory(); }
  },
  {
    title: "Export All History Sections",
    desc: "Export every chat history section to Markdown.",
    keywords: "export all history sections markdown logs",
    run: () => { clickNavByView("history"); exportAllSections(); }
  },
  {
    title: "Open Jobs",
    desc: "Go to jobs and live trace viewer.",
    keywords: "jobs trace logs result",
    run: () => { clickNavByView("jobs"); loadJobs(); }
  },
  {
    title: "Open Files",
    desc: "Browse and edit project files.",
    keywords: "files browser editor workspace",
    run: () => { clickNavByView("files"); loadFiles(); }
  },
  {
    title: "Open Products",
    desc: "Create, start, stop, and open products.",
    keywords: "products launcher apps",
    run: () => { clickNavByView("products"); loadProducts(); }
  },
  {
    title: "Open Search / Diff",
    desc: "Search files and inspect diffs.",
    keywords: "search diff changed snapshot",
    run: () => clickNavByView("search")
  },
  {
    title: "Open Skills",
    desc: "List and create Titan skills.",
    keywords: "skills workflows",
    run: () => { clickNavByView("skills"); loadSkills(); }
  },
  {
    title: "Open Memory",
    desc: "View and search saved memories.",
    keywords: "memory remember recall",
    run: () => { clickNavByView("memory"); loadMemory(); }
  },
  {
    title: "Open RAG",
    desc: "Index and search local docs.",
    keywords: "rag docs knowledge index",
    run: () => { clickNavByView("rag"); loadRag(); }
  },
  {
    title: "Open Models",
    desc: "View or switch model profiles.",
    keywords: "models ollama fast smart heavy max",
    run: () => { clickNavByView("models"); loadModels(); }
  },
  {
    title: "Open Permissions",
    desc: "View mode and run approved shell commands.",
    keywords: "permissions mode safe power agentic run",
    run: () => { clickNavByView("permissions"); loadMode(); }
  },
  {
    title: "Refresh Jobs",
    desc: "Reload jobs and current trace.",
    keywords: "refresh jobs trace",
    run: () => loadJobs()
  },
  {
    title: "Refresh Skills",
    desc: "Reload skills list.",
    keywords: "refresh skills",
    run: () => loadSkills()
  },
  {
    title: "Refresh Memory",
    desc: "Reload memory list.",
    keywords: "refresh memory",
    run: () => loadMemory()
  },
  {
    title: "Refresh RAG",
    desc: "Reload RAG status.",
    keywords: "refresh rag",
    run: () => loadRag()
  },
  {
    title: "Refresh Models",
    desc: "Reload model config.",
    keywords: "refresh models",
    run: () => loadModels()
  },
  {
    title: "Set Fast Model",
    desc: "Switch Titan to fast profile.",
    keywords: "model fast speed",
    run: () => setProfile("fast")
  },
  {
    title: "Set Coder Model",
    desc: "Switch Titan to coder profile.",
    keywords: "model coder code",
    run: () => setProfile("coder")
  },
  {
    title: "Set Smart Model",
    desc: "Switch Titan to smart profile.",
    keywords: "model smart",
    run: () => setProfile("smart")
  },
  {
    title: "Set Heavy Model",
    desc: "Switch Titan to heavy profile.",
    keywords: "model heavy planning",
    run: () => setProfile("heavy")
  },
  {
    title: "Set Agentic Mode",
    desc: "Switch permissions to agentic mode.",
    keywords: "agentic permission mode",
    run: () => setMode("agentic")
  },
  {
    title: "Set Power Mode",
    desc: "Switch permissions to power mode.",
    keywords: "power permission mode",
    run: () => setMode("power")
  },
  {
    title: "Set Safe Mode",
    desc: "Switch permissions to safe mode.",
    keywords: "safe permission mode",
    run: () => setMode("safe")
  }
];

function clickNavByView(view) {
  const button = Array.from(document.querySelectorAll("nav button")).find(btn => {
    return btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(`showView('${view}'`);
  });

  if (button) {
    button.click();
  } else {
    showView(view, null);
  }
}

function openCommandPalette() {
  const backdrop = document.getElementById("paletteBackdrop");
  const input = document.getElementById("paletteInput");

  if (!backdrop || !input) return;

  backdrop.classList.add("active");
  input.value = "";
  paletteIndex = 0;
  renderPalette("");
  setTimeout(() => input.focus(), 20);
}

function closeCommandPalette(event = null) {
  if (event && event.target && event.target.id !== "paletteBackdrop") return;
  const backdrop = document.getElementById("paletteBackdrop");
  if (backdrop) backdrop.classList.remove("active");
}

function scoreCommand(command, query) {
  if (!query) return 1;

  const haystack = `${command.title} ${command.desc} ${command.keywords}`.toLowerCase();
  const parts = query.toLowerCase().split(/\s+/).filter(Boolean);

  let score = 0;
  for (const part of parts) {
    if (command.title.toLowerCase().includes(part)) score += 5;
    if (haystack.includes(part)) score += 2;
  }
  return score;
}

function renderPalette(query) {
  const results = document.getElementById("paletteResults");
  if (!results) return;

  paletteFiltered = paletteCommands
    .map(cmd => ({cmd, score: scoreCommand(cmd, query)}))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map(item => item.cmd);

  results.innerHTML = "";

  if (!paletteFiltered.length) {
    results.textContent = "No matching commands.";
    return;
  }

  paletteFiltered.slice(0, 12).forEach((cmd, index) => {
    const item = document.createElement("div");
    item.className = "palette-item" + (index === paletteIndex ? " active" : "");
    item.onclick = () => runPaletteCommand(index);

    const title = document.createElement("div");
    title.className = "palette-item-title";
    title.textContent = cmd.title;

    const desc = document.createElement("div");
    desc.className = "palette-item-desc";
    desc.textContent = cmd.desc;

    item.appendChild(title);
    item.appendChild(desc);
    results.appendChild(item);
  });
}

function runPaletteCommand(index = paletteIndex) {
  const cmd = paletteFiltered[index];
  if (!cmd) return;

  closeCommandPalette();
  try {
    cmd.run();
  } catch (err) {
    console.error(err);
  }
}

window.addEventListener("keydown", event => {
  const isPaletteShortcut = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";

  if (isPaletteShortcut) {
    event.preventDefault();
    openCommandPalette();
    return;
  }

  const backdrop = document.getElementById("paletteBackdrop");
  const open = backdrop && backdrop.classList.contains("active");

  if (!open) return;

  if (event.key === "Escape") {
    event.preventDefault();
    closeCommandPalette();
    return;
  }

  if (event.key === "ArrowDown") {
    event.preventDefault();
    paletteIndex = Math.min(paletteIndex + 1, Math.min(paletteFiltered.length - 1, 11));
    renderPalette(document.getElementById("paletteInput").value);
    return;
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    paletteIndex = Math.max(paletteIndex - 1, 0);
    renderPalette(document.getElementById("paletteInput").value);
    return;
  }

  if (event.key === "Enter") {
    event.preventDefault();
    runPaletteCommand();
  }
});

window.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("paletteInput");
  if (!input) return;

  input.addEventListener("input", () => {
    paletteIndex = 0;
    renderPalette(input.value);
  });
});
// TITAN_COMMAND_PALETTE_JS_END


// TITAN_TOASTS_JS_START
function titanToast(title, body = "", type = "info", timeout = 4200) {
  const host = document.getElementById("toastHost");
  if (!host) return;

  const toast = document.createElement("div");
  toast.className = "toast " + type;

  const icon = document.createElement("div");
  icon.className = "toast-icon";
  icon.textContent =
    type === "success" ? "✓" :
    type === "error" ? "!" :
    type === "warn" ? "⚠" :
    "i";

  const content = document.createElement("div");

  const titleEl = document.createElement("div");
  titleEl.className = "toast-title";
  titleEl.textContent = title || "Titan";

  const bodyEl = document.createElement("div");
  bodyEl.className = "toast-body";
  bodyEl.textContent = String(body || "");

  const close = document.createElement("button");
  close.className = "toast-close";
  close.textContent = "×";
  close.onclick = () => removeToast(toast);

  content.appendChild(titleEl);
  if (body) content.appendChild(bodyEl);

  toast.appendChild(icon);
  toast.appendChild(content);
  toast.appendChild(close);

  host.appendChild(toast);

  if (timeout) {
    setTimeout(() => removeToast(toast), timeout);
  }
}

function removeToast(toast) {
  if (!toast || toast.classList.contains("leaving")) return;
  toast.classList.add("leaving");
  setTimeout(() => toast.remove(), 180);
}

function summarizeTitanResponse(url, data) {
  if (!data) return null;

  if (data.error) {
    return {
      type: "error",
      title: "Titan error",
      body: typeof data.error === "string" ? data.error.slice(0, 240) : JSON.stringify(data.error).slice(0, 240)
    };
  }

  if (url.includes("/api/task")) {
    return { type: "success", title: "Job started", body: data.job_id || "Background job queued." };
  }

  if (url.includes("/api/file/save")) {
    return { type: "success", title: "File saved", body: data.path || data.result || "Saved." };
  }

  if (url.includes("/api/folder/create")) {
    return { type: "success", title: "Folder created", body: data.path || data.result || "Created." };
  }

  if (url.includes("/api/product/create")) {
    return { type: "success", title: "Product created", body: data.result || "Created." };
  }

  if (url.includes("/api/product/start")) {
    return { type: "success", title: "Product started", body: data.url || data.name || "Started." };
  }

  if (url.includes("/api/product/stop")) {
    return { type: "warn", title: "Product stopped", body: data.name || data.result || "Stopped." };
  }

  if (url.includes("/api/skills/create")) {
    return { type: "success", title: "Skill created", body: data.result || "Created." };
  }

  if (url.includes("/api/memory/save")) {
    return { type: "success", title: "Memory saved", body: data.result || "Saved." };
  }

  if (url.includes("/api/rag/index")) {
    return { type: "success", title: "RAG indexed", body: data.result || "Index complete." };
  }

  if (url.includes("/api/models/profile")) {
    return { type: "success", title: "Model profile changed", body: data.profile || data.model || "Updated." };
  }

  if (url.includes("/api/mode")) {
    return { type: "success", title: "Permission mode updated", body: data.result || "Updated." };
  }

  if (url.includes("/api/run")) {
    return { type: "info", title: "Command finished", body: "Check output panel." };
  }

  if (url.includes("/api/snapshot")) {
    return { type: "success", title: "Snapshot saved", body: data.path || "Snapshot complete." };
  }

  return null;
}

/* Wrap jsonFetch so existing dashboard actions get toast feedback automatically. */
setTimeout(() => {
  if (typeof jsonFetch !== "function" || window.__titanToastWrapped) return;

  const originalJsonFetch = jsonFetch;
  window.__titanToastWrapped = true;

  jsonFetch = async function(url, options = {}) {
    try {
      const data = await originalJsonFetch(url, options);
      const method = String(options.method || "GET").toUpperCase();

      if (method !== "GET") {
        const summary = summarizeTitanResponse(String(url), data);
        if (summary) titanToast(summary.title, summary.body, summary.type);
      }

      if (data && data.error) {
        const summary = summarizeTitanResponse(String(url), data);
        if (summary) titanToast(summary.title, summary.body, summary.type, 6500);
      }

      return data;
    } catch (err) {
      titanToast("Network error", String(err).slice(0, 260), "error", 7000);
      throw err;
    }
  };
}, 80);

/* Toast on command palette actions */
setTimeout(() => {
  if (typeof runPaletteCommand !== "function" || window.__titanPaletteToastWrapped) return;

  const originalRunPaletteCommand = runPaletteCommand;
  window.__titanPaletteToastWrapped = true;

  runPaletteCommand = function(index = paletteIndex) {
    const cmd = paletteFiltered && paletteFiltered[index];
    originalRunPaletteCommand(index);
    if (cmd) titanToast("Command palette", cmd.title, "info", 2200);
  };
}, 120);

/* Startup hello */
window.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => titanToast("Titan dashboard ready", "Command Palette: Cmd+K / Ctrl+K", "success", 3200), 650);
});
// TITAN_TOASTS_JS_END


// TITAN_CHAT_HISTORY_JS_START
async function loadSections() {
  const data = await jsonFetch("/api/history/sections");
  const out = document.getElementById("sectionsOut");
  if (!out) return;

  const sections = data.sections || [];

  if (!sections.length) {
    out.textContent = "No sections yet.";
    return;
  }

  out.innerHTML = "";

  sections.forEach(sec => {
    const div = document.createElement("div");
    div.className = "history-section-item" + (sec.active ? " active" : "");
    div.onclick = () => loadHistory(sec.section);

    const name = document.createElement("div");
    name.className = "history-section-name";
    name.textContent = sec.section;

    const meta = document.createElement("div");
    meta.className = "history-section-meta";
    meta.textContent = `${sec.count} entries` + (sec.active ? " · active" : "");

    div.appendChild(name);
    div.appendChild(meta);
    out.appendChild(div);
  });
}

function renderHistoryItems(items) {
  if (!items || !items.length) return "No chat history found.";

  return items.map(item => {
    return `${item.time || ""} | ${item.section || "General"} | ${item.role || ""}\n${item.content || ""}\n`;
  }).join("\n");
}

async function loadHistory(section = "") {
  await loadSections();

  const url = "/api/history" + (section ? "?section=" + encodeURIComponent(section) : "");
  const data = await jsonFetch(url);

  const title = document.getElementById("historyTitle");
  const out = document.getElementById("historyOut");

  if (title) title.textContent = section ? "History: " + section : "History";
  if (out) out.textContent = renderHistoryItems(data.items || []);
}

async function searchHistory() {
  const q = document.getElementById("historyQuery").value.trim();
  const out = document.getElementById("historyOut");
  const title = document.getElementById("historyTitle");

  if (!q) {
    if (out) out.textContent = "Enter a search query.";
    return;
  }

  const data = await jsonFetch("/api/history/search?q=" + encodeURIComponent(q));

  if (title) title.textContent = "History Search: " + q;
  if (out) out.textContent = renderHistoryItems(data.items || []);
}

async function setHistorySection() {
  const name = document.getElementById("sectionName").value.trim();
  if (!name) {
    titanToast("Section missing", "Enter a section name.", "warn");
    return;
  }

  const data = await jsonFetch("/api/history/section", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({section: name})
  });

  titanToast("Section changed", data.result || name, "success");
  await loadSections();
  await loadHistory(name);
}
// TITAN_CHAT_HISTORY_JS_END


// TITAN_HISTORY_EXPORT_JS_START
async function exportHistory(section = "") {
  const active = document.querySelector(".history-section-item.active .history-section-name");
  const chosen = section || (active ? active.textContent : "");

  const data = await jsonFetch("/api/history/export", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({section: chosen})
  });

  titanToast("History exported", data.path || data.result || "Export complete.", "success", 6500);

  const out = document.getElementById("historyOut");
  if (out) out.textContent = JSON.stringify(data, null, 2);
}

async function exportAllSections() {
  const data = await jsonFetch("/api/history/export-all", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({})
  });

  titanToast("All sections exported", `${data.count || 0} exports created.`, "success", 6500);

  const out = document.getElementById("historyOut");
  if (out) out.textContent = JSON.stringify(data, null, 2);
}
// TITAN_HISTORY_EXPORT_JS_END


// TITAN_VIDEO_DASHBOARD_V3
async function loadVideoStatus() {
  const out = document.getElementById("videoOut");
  const data = await jsonFetch("/api/video/status");
  if (out) out.textContent = JSON.stringify(data, null, 2);
}
async function setVideoQuality() {
  const q = document.getElementById("videoQuality").value;
  const data = await jsonFetch("/api/video/quality", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({quality:q})});
  document.getElementById("videoOut").textContent = JSON.stringify(data, null, 2);
}
async function setVideoMotion() {
  const m = document.getElementById("videoMotion").value;
  const data = await jsonFetch("/api/video/motion", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({motion:m})});
  document.getElementById("videoOut").textContent = JSON.stringify(data, null, 2);
}
async function setVideoImageBackend() {
  const backend = document.getElementById("videoImageBackend").value;
  const data = await jsonFetch("/api/video/image-backend", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({backend})});
  document.getElementById("videoOut").textContent = JSON.stringify(data, null, 2);
}
async function createDashboardVideo() {
  const prompt = document.getElementById("videoPrompt").value.trim();
  const out = document.getElementById("videoOut");
  out.textContent = "Creating generated keyframe video...";
  const data = await jsonFetch("/api/video/create", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({prompt})});
  out.textContent = JSON.stringify(data, null, 2);
  await loadVideos();
}
async function loadVideos() {
  const list = document.getElementById("videoList");
  if (!list) return;
  const data = await jsonFetch("/api/video/list");
  const files = data.files || [];
  if (!files.length) { list.textContent = "No videos found."; return; }
  list.innerHTML = "";
  files.forEach(file => {
    const div = document.createElement("div");
    div.className = "video-item";
    div.textContent = file.name + " | " + file.size + " bytes";
    div.onclick = () => { document.getElementById("videoOut").textContent = JSON.stringify(file, null, 2); };
    list.appendChild(div);
  });
}

</script>

  <!-- TITAN_COMMAND_PALETTE_HTML_START -->
  <div class="palette-backdrop" id="paletteBackdrop" onclick="closeCommandPalette(event)">
    <div class="palette" onclick="event.stopPropagation()">
      <div class="palette-top">
        <span class="palette-icon">⌘K</span>
        <input id="paletteInput" placeholder="Search commands..." autocomplete="off">
      </div>
      <div class="palette-results" id="paletteResults"></div>
      <div class="palette-help">
        Enter to run · Esc to close · ↑↓ to move
      </div>
    </div>
  </div>
  <!-- TITAN_COMMAND_PALETTE_HTML_END -->


  <!-- TITAN_TOASTS_HTML_START -->
  <div id="toastHost" class="toast-host" aria-live="polite"></div>
  <!-- TITAN_TOASTS_HTML_END -->

</body>
</html>
"""


def safe(fn):
    try:
        return jsonify(fn())
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


def now():
    return datetime.now().isoformat(timespec="seconds")


def make_job_id():
    count = len(list(RUNNING.glob("*.json"))) + len(list(DONE.glob("*.json"))) + 1
    return "dash-" + datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{count:03d}"


def start_job(task):
    # TITAN_HISTORY_START_JOB_PATCH
    try:
        from agent_core.chat_history import log_event
        history_user_id = log_event("user", task, meta={"source": "dashboard"})
    except Exception:
        history_user_id = None

    job_id = make_job_id()
    job = {
        "id": job_id,
        "task": task,
        "status": "queued",
        "created_at": now(),
        "source": "dashboard",
        "max_steps": 8,
        "history_user_id": history_user_id
    }

    (RUNNING / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")

    worker = BASE / "background_worker.py"
    subprocess.Popen(
        [sys.executable, str(worker), job_id],
        cwd=str(BASE),
        stdout=(LOGS / f"{job_id}.stdout.log").open("w"),
        stderr=(LOGS / f"{job_id}.stderr.log").open("w"),
        start_new_session=True
    )

    return {"job_id": job_id, "status": "queued"}


def read_job(job_id):
    for folder in [RUNNING, DONE]:
        path = folder / f"{job_id}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))

            # TITAN_HISTORY_READ_JOB_PATCH
            if data.get("status") in ["done", "error"] and data.get("result") and not data.get("history_logged"):
                try:
                    from agent_core.chat_history import log_event
                    log_event("assistant", data.get("result", ""), meta={"source": "dashboard", "job_id": job_id, "reply_to": data.get("history_user_id")})
                    data["history_logged"] = True
                    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                except Exception:
                    pass

            trace = TRACES / f"{job_id}.trace.md"
            log = LOGS / f"{job_id}.log"
            data["trace"] = trace.read_text(errors="ignore")[-8000:] if trace.exists() else ""
            data["log"] = log.read_text(errors="ignore")[-4000:] if log.exists() else ""
            return data
    return {"error": "Job not found", "job_id": job_id}


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/task", methods=["POST"])
def api_task():
    return safe(lambda: start_job(request.json.get("task", "").strip()))


@app.route("/api/job/<job_id>")
def api_job(job_id):
    return safe(lambda: read_job(job_id))


@app.route("/api/jobs")
def api_jobs():
    def run():
        jobs = []
        for folder in [RUNNING, DONE]:
            for p in sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:40]:
                try:
                    jobs.append(json.loads(p.read_text(encoding="utf-8")))
                except Exception:
                    pass
        return {"jobs": jobs}
    return safe(run)


@app.route("/api/skills")
def api_skills():
    from agent_core.skills import list_skills
    return safe(lambda: {"result": list_skills()})


@app.route("/api/skills/create", methods=["POST"])
def api_skill_create():
    from agent_core.skills import create_skill_pack
    return safe(lambda: {"result": create_skill_pack(request.json.get("name", ""), request.json.get("description", ""), [])})


@app.route("/api/memory")
def api_memory():
    from agent_core.memory import memory_list
    return safe(lambda: {"result": memory_list("all", 50)})


@app.route("/api/memory/save", methods=["POST"])
def api_memory_save():
    from agent_core.memory import memory_save
    return safe(lambda: {"result": memory_save(request.json.get("text", ""), "project_fact", "project", ["dashboard"])})


@app.route("/api/memory/search")
def api_memory_search():
    from agent_core.memory import memory_search
    return safe(lambda: {"result": memory_search(request.args.get("q", ""), "all", 8)})


@app.route("/api/rag")
def api_rag():
    from agent_core.rag import rag_status
    return safe(lambda: {"result": rag_status()})


@app.route("/api/rag/index", methods=["POST"])
def api_rag_index():
    from agent_core.rag import rag_index
    return safe(lambda: {"result": rag_index()})


@app.route("/api/rag/search")
def api_rag_search():
    from agent_core.rag import rag_search
    return safe(lambda: {"result": rag_search(request.args.get("q", ""), 5)})


@app.route("/api/models")
def api_models():
    def run():
        cfg = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
        return {
            "active_profile": cfg.get("active_profile"),
            "model": cfg.get("model"),
            "fallback_model": cfg.get("fallback_model"),
            "role_models": cfg.get("role_models"),
            "profiles": cfg.get("model_profiles", {})
        }
    return safe(run)


@app.route("/api/models/profile", methods=["POST"])
def api_model_profile():
    def run():
        cfg_path = BASE / "config.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        profile = request.json.get("profile", "")
        profiles = cfg.get("model_profiles", {})
        if profile not in profiles:
            return {"error": "Unknown profile", "available": list(profiles.keys())}
        cfg.update(profiles[profile])
        cfg["active_profile"] = profile
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return {"result": "Profile enabled", "profile": profile, "model": cfg.get("model")}
    return safe(run)


@app.route("/api/mode", methods=["GET", "POST"])
def api_mode():
    from agent_core.approvals import permission_status, set_mode
    if request.method == "GET":
        return safe(lambda: {"result": permission_status()})
    return safe(lambda: {"result": set_mode(request.json.get("mode", ""))})


@app.route("/api/run", methods=["POST"])
def api_run():
    from agent_core.tools import run_command
    return safe(lambda: {"result": run_command(request.json.get("command", ""))})



@app.route("/assets/<path:name>")
def titan_assets(name):
    return send_from_directory(str(BASE / "assets"), name)




@app.route("/api/files")
def api_files():
    from agent_core.file_browser import list_dir
    return safe(lambda: list_dir(request.args.get("root", "workspace"), request.args.get("path", "")))


@app.route("/api/file")
def api_file():
    from agent_core.file_browser import read_file
    return safe(lambda: read_file(request.args.get("root", "workspace"), request.args.get("path", "")))


@app.route("/api/file/save", methods=["POST"])
def api_file_save():
    from agent_core.file_browser import write_file
    return safe(lambda: write_file(request.json.get("root", "workspace"), request.json.get("path", ""), request.json.get("content", "")))


@app.route("/api/folder/create", methods=["POST"])
def api_folder_create():
    from agent_core.file_browser import make_dir
    return safe(lambda: make_dir(request.json.get("root", "workspace"), request.json.get("path", "")))



@app.route("/api/product/list")
def api_product_list():
    from agent_core.products import list_products
    return safe(lambda: {"products": list_products()})


@app.route("/api/product/create", methods=["POST"])
def api_product_create():
    from agent_core.products import create_product
    return safe(lambda: {"result": create_product(request.json.get("name", ""), request.json.get("kind", "python_cli"), request.json.get("description", ""))})


@app.route("/api/product/start", methods=["POST"])
def api_product_start():
    from agent_core.products import start_product
    return safe(lambda: start_product(request.json.get("name", "")))


@app.route("/api/product/stop", methods=["POST"])
def api_product_stop():
    from agent_core.products import stop_product
    return safe(lambda: stop_product(request.json.get("name", "")))


@app.route("/api/product/logs")
def api_product_logs():
    from agent_core.products import product_logs
    return safe(lambda: product_logs(request.args.get("name", "")))



@app.route("/api/search")
def api_search():
    from agent_core.search_diff import search_files
    return safe(lambda: search_files(request.args.get("q", ""), request.args.get("root", "all")))


@app.route("/api/snapshot", methods=["POST"])
def api_snapshot():
    from agent_core.search_diff import make_snapshot
    return safe(lambda: make_snapshot(request.json.get("root", "workspace")))


@app.route("/api/changed")
def api_changed():
    from agent_core.search_diff import changed_files
    return safe(lambda: changed_files(request.args.get("root", "workspace")))


@app.route("/api/diff")
def api_diff():
    from agent_core.search_diff import diff_file
    return safe(lambda: {"diff": diff_file(request.args.get("root", "workspace"), request.args.get("path", ""))})



@app.route("/api/history")
def api_history():
    from agent_core.chat_history import history_list
    return safe(lambda: history_list(request.args.get("section") or None, int(request.args.get("limit", 100))))


@app.route("/api/history/search")
def api_history_search():
    from agent_core.chat_history import history_search
    return safe(lambda: history_search(request.args.get("q", ""), int(request.args.get("limit", 60))))


@app.route("/api/history/sections")
def api_history_sections():
    from agent_core.chat_history import list_sections
    return safe(lambda: {"sections": list_sections()})


@app.route("/api/history/section", methods=["POST"])
def api_history_section():
    from agent_core.chat_history import set_section
    return safe(lambda: {"result": set_section(request.json.get("section", "General"))})



@app.route("/api/history/export", methods=["POST"])
def api_history_export():
    from agent_core.chat_export import export_history
    return safe(lambda: export_history(request.json.get("section") or None))


@app.route("/api/history/export-all", methods=["POST"])
def api_history_export_all():
    from agent_core.chat_export import export_all_sections
    return safe(lambda: export_all_sections())



@app.route("/api/video/create", methods=["POST"])
def api_video_create():
    from agent_core.video_tools import create_video
    return safe(lambda: create_video(request.json.get("prompt", "")))


@app.route("/api/video/list")
def api_video_list():
    from agent_core.video_tools import list_videos
    return safe(lambda: list_videos())


@app.route("/api/video/status")
def api_video_status():
    from agent_core.video_tools import video_status
    return safe(lambda: video_status())


@app.route("/api/video/quality", methods=["POST"])
def api_video_quality():
    from agent_core.video_tools import set_video_quality
    return safe(lambda: set_video_quality(request.json.get("quality", "medium")))


@app.route("/api/video/motion", methods=["POST"])
def api_video_motion():
    from agent_core.video_tools import set_video_motion
    return safe(lambda: set_video_motion(request.json.get("motion", "high")))


@app.route("/api/video/image-backend", methods=["POST"])
def api_video_image_backend():
    from agent_core.video_tools import set_video_image_backend
    return safe(lambda: set_video_image_backend(request.json.get("backend", "pollinations")))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
