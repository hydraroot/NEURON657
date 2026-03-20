#!/usr/bin/env python3
"""
NEURON657 — NPC Intelligence Demo  (v3.0 FULL COGNITIVE)
FSM clásica vs NEURON657 — mismo mapa, cerebros distintos.


  ✓ Integración completa con neuron657_v13 (Free Energy Minimization)
  ✓ El motor cognitivo provee planes basados en energía libre
  ✓ Votación híbrida: impulsos + LTM + episódica + motor cognitivo
  ✓ Exploración epsilon-greedy dinámica
  ✓ Fatiga, supresión y cobertura optimizadas
  ✓ Decaimiento de memoria episódica para evitar estancamiento
  ✓ Control de frecuencia de llamadas al motor (cada 0.5s)
"""
import sys, math, time, random
from collections import deque, defaultdict
from pathlib import Path
from unittest.mock import MagicMock
from typing import Dict, Any, Optional, Tuple, List

sys.modules.setdefault('websockets', MagicMock())
sys.path.insert(0, str(Path(__file__).parent))
try:
    # Importar desde la nueva versión v13.2 
    from neuron657_v13 import (
        NeuronEngine, CognitiveMode, set_random_seed,
        FactoredWorldModel, EpisodicMemory, GoalManager, IntentionSystem,
        AttentionSystem, UncertaintyEstimator, CuriosityModule,
        MetaCognitionModule, StrategySelector, TheoryOfMind
    )
    set_random_seed(77)
    NEURON_OK = True
    _eng_counter = [0]

    def _patch_snapshot(engine, inst_id):
        """Deshabilita snapshots para uso en combate (evita hilos y carpetas)."""
        ss = engine.snapshot_system
        if ss is not None and hasattr(ss, 'snapshot_thread'):
            ss.create_incremental   = lambda *a, **kw: "disabled"
            ss.create_full_snapshot = lambda *a, **kw: "disabled"
            ss._background_snapshot = lambda: None
        engine.snapshot_system = None

    def _make_engine():
        _eng_counter[0] += 1
        # Crear módulos extendidos
        fwm = FactoredWorldModel()
        em = EpisodicMemory()
        gm = GoalManager()
        its = IntentionSystem()
        att = AttentionSystem()
        ue = UncertaintyEstimator(fwm)
        cm = CuriosityModule(ue)
        mc = MetaCognitionModule()
        ss = StrategySelector()
        tom = TheoryOfMind()

        eng = NeuronEngine(
            exploration_rate=0.18,
            world_model_ext=fwm,
            episodic_memory=em,
            goal_manager=gm,
            intention_system=its,
            attention_system=att,
            uncertainty_estimator=ue,
            curiosity_module=cm,
            metacognition_module=mc,
            strategy_selector=ss,
            theory_of_mind=tom
        )
        _patch_snapshot(eng, _eng_counter[0])
        return eng

except Exception as e:
    NEURON_OK = False
    def _make_engine(): return None
    print(f"[WARN] neuron657_v13 no disponible: {e}")

import tkinter as tk
from tkinter import font as tkfont

# ── PALETTE ──────────────────────────────────────────────────────
P = {
    "bg":"#06090f","bg1":"#0b1220","bg2":"#0f1828",
    "border":"#1a2d45","grid":"#0d1a28","wall":"#1e3a5a","floor":"#080e18",
    "fsm_npc":"#e05050","fsm_hi":"#ff9090",
    "n_npc":"#30d090","n_hi":"#70ffb8",
    "player":"#ffd740","player_hi":"#ffe880",
    "bullet_p":"#fff176","bullet_e":"#ff6b6b",
    "text":"#8ab0d0","text_hi":"#c8e0f0","dim":"#2a4060",
    "green":"#00e676","cyan":"#00e5ff","orange":"#ff9100",
    "red":"#ff5252","yellow":"#ffd740","purple":"#b388ff","blue":"#448aff",
    "white":"#ffffff",
    "fsm_bg":"#0a0f18",
    "n_bg":"#070f18",
    "ambush":"#ff00ff",   # magenta para AMBUSH
    "RAID":"#ffaa00",      # naranja oscuro para RAID
}
MODE_COLOR  = {"autonomous":P["green"],"reasoning":P["cyan"],"safe_recovery":P["orange"],
               "adaptive":P["purple"],"meta_learning":P["blue"],"assistant":P["yellow"],
               "integrated":P["green"],"simulation":P["dim"]}
MODE_LABEL  = {"autonomous":"AUTÓNOMO","reasoning":"ANALIZANDO","safe_recovery":"EVASIÓN",
               "adaptive":"ADAPTATIVO","meta_learning":"APRENDIENDO","assistant":"ASISTIDO",
               "integrated":"INTEGRADO","simulation":"SIMULANDO"}
TACTIC_COLOR= {"aggressive":P["red"],"balanced":P["cyan"],
               "defensive":P["blue"],"sniper":P["purple"],
               "berserker":P["orange"],"flanker":P["green"],
               "RAID":P["RAID"]}

# ── MAP ──────────────────────────────────────────────────────────
AW,AH,CELL = 380,360,20
GCOLS,GROWS = AW//CELL, AH//CELL

def make_map():
    m=[[0]*GCOLS for _ in range(GROWS)]
    for c in range(GCOLS): m[0][c]=m[GROWS-1][c]=1
    for r in range(GROWS): m[r][0]=m[r][GCOLS-1]=1
    for r,c in [(3,3),(3,4),(3,5),(4,3),(5,3),(3,13),(3,14),(3,15),(4,15),(5,15),
                (8,5),(8,6),(8,7),(8,8),(9,8),(10,8),(8,10),(8,11),(8,12),(8,13),
                (9,10),(10,10),(13,3),(14,3),(15,3),(15,4),(15,5),(13,14),(14,14),
                (15,14),(15,13),(15,12),(6,1),(7,1),(6,17),(7,17),(11,1),(12,1)]:
        if 0<r<GROWS-1 and 0<c<GCOLS-1: m[r][c]=1
    return m

ARENA_MAP=make_map()
_ESCAPE_MAP = {}

# ── Cono de visión (raycasting 2D) ───────────────────────────────
def ray_hit(ox, oy, angle, max_r):
    dx = math.cos(angle); dy = math.sin(angle)
    step = 4.0
    x, y = ox, oy
    traveled = 0.0
    while traveled < max_r:
        x += dx * step; y += dy * step; traveled += step
        if traveled > 12 and iwall(x, y):
            return x - dx * step, y - dy * step
    return ox + dx * max_r, oy + dy * max_r

def vision_polygon(ox, oy, facing, fov_deg, max_r, n_rays=40):
    half = math.radians(fov_deg / 2)
    pts = [(ox, oy)]
    for i in range(n_rays + 1):
        angle = facing - half + (2 * half * i / n_rays)
        hx, hy = ray_hit(ox, oy, angle, max_r)
        pts.append((hx, hy))
    return pts

def point_in_vision(ox, oy, facing, fov_deg, max_r, tx, ty):
    dist = math.hypot(tx - ox, ty - oy)
    if dist > max_r: return False
    angle_to = math.atan2(ty - oy, tx - ox)
    diff = (angle_to - facing + math.pi) % (2 * math.pi) - math.pi
    margin = math.radians(3)
    if abs(diff) > math.radians(fov_deg / 2) + margin: return False
    return has_los(ox, oy, tx, ty)

def get_escape_map():
    global _ESCAPE_MAP
    if not _ESCAPE_MAP:
        cx,cy=GROWS//2,GCOLS//2
        for r in range(1,GROWS-1):
            for c in range(1,GCOLS-1):
                if ARENA_MAP[r][c]: continue
                free_n=sum(1 for dr,dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]
                           if 0<=r+dr<GROWS and 0<=c+dc<GCOLS and not ARENA_MAP[r+dr][c+dc])
                _ESCAPE_MAP[(r,c)]=math.hypot(r-cx,c-cy)*0.6+free_n*1.5
    return _ESCAPE_MAP

def cc(r,c): return c*CELL+CELL//2, r*CELL+CELL//2
def w2c(x,y): return int(y//CELL),int(x//CELL)
def iwall(x,y):
    r,c=w2c(x,y)
    return not(0<=r<GROWS and 0<=c<GCOLS) or ARENA_MAP[r][c]==1

def bfs(sr,sc,gr,gc):
    if (sr,sc)==(gr,gc): return sr,sc
    vis={(sr,sc)}; q=deque([((sr,sc),[])])
    while q:
        (r,c),path=q.popleft()
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr,nc=r+dr,c+dc
            if (nr,nc) not in vis and 0<=nr<GROWS and 0<=nc<GCOLS and ARENA_MAP[nr][nc]==0:
                vis.add((nr,nc))
                np2=path+[(nr,nc)]
                if nr==gr and nc==gc: return np2[0] if np2 else (sr,sc)
                q.append(((nr,nc),np2))
    return sr,sc

def has_los(ax,ay,bx,by):
    dx,dy=bx-ax,by-ay
    dist=math.hypot(dx,dy)
    if dist<1: return True
    steps=max(int(dist/CELL)+2, 4)
    for i in range(1, steps):
        t=i/steps
        x=ax+t*dx; y=ay+t*dy
        if t<0.08 or t>0.92: continue
        if iwall(x,y): return False
    return True

# ── FX ───────────────────────────────────────────────────────────
class Particle:
    def __init__(self,x,y,color):
        self.x,self.y=x,y
        a=random.uniform(0,2*math.pi); spd=random.uniform(40,140)
        self.vx=math.cos(a)*spd; self.vy=math.sin(a)*spd
        self.life=random.uniform(0.25,0.55); self.max_life=self.life
        self.r=random.randint(2,5); self.color=color
    def update(self,dt):
        self.x+=self.vx*dt; self.y+=self.vy*dt
        self.vx*=0.82; self.vy*=0.82; self.life-=dt
    @property
    def alive(self): return self.life>0

class DmgNum:
    def __init__(self,x,y,txt,color):
        self.x,self.y=float(x),float(y); self.txt=txt; self.color=color
        self.life=0.9; self.vy=-50.0
    def update(self,dt): self.y+=self.vy*dt; self.vy*=0.88; self.life-=dt
    @property
    def alive(self): return self.life>0

# ── BULLET ───────────────────────────────────────────────────────
class Bullet:
    SPD=140; R=3
    def __init__(self,x,y,dx,dy,owner):
        self.x,self.y=x,y; ln=math.hypot(dx,dy) or 1
        self.vx=dx/ln*self.SPD; self.vy=dy/ln*self.SPD
        self.owner=owner; self.alive=True
    def update(self,dt):
        self.x+=self.vx*dt; self.y+=self.vy*dt
        if iwall(self.x,self.y): self.alive=False

# ── PLAYER ───────────────────────────────────────────────────────
class Player:
    SPD=70; R=8; MAX_HP=200
    def __init__(self,x,y):
        self.x,self.y=float(x),float(y); self.hp=self.MAX_HP
        self.score=0; self._scd=0.0; self._hf=0.0
        self.auto=False
        self._ai_state="hunt"
        self._ai_dodge_t=0.0
        self._px_hist=deque(maxlen=6); self._py_hist=deque(maxlen=6)
        self._cover_target=None
        self._flank_angle=0.0; self._flank_dir=1
        self._stuck_t=0.0; self._stuck_ref=(0.0,0.0)
        self._cover_timer=0.0; self._hunt_no_los_t=0.0

    def move(self,dx,dy,dt):
        nx=self.x+dx*self.SPD*dt; ny=self.y+dy*self.SPD*dt
        if not iwall(nx,self.y): self.x=max(self.R,min(AW-self.R,nx))
        if not iwall(self.x,ny): self.y=max(self.R,min(AH-self.R,ny))

    def shoot(self,tx,ty,bl,dt,match_cd=0.62):
        self._scd-=dt
        if self._scd<=0 and math.hypot(tx-self.x,ty-self.y)>1 and has_los(self.x,self.y,tx,ty):
            bl.append(Bullet(self.x,self.y,tx-self.x,ty-self.y,"player")); self._scd=match_cd

    def take_hit(self,d=10):
        self.hp=max(0,self.hp-d); self._hf=0.35
        self._dmg_taken_total=getattr(self,'_dmg_taken_total',0)+d
        if self.auto:
            self._ai_state="retreat"; self._cover_target=None

    def update(self,dt):
        self._hf=max(0,self._hf-dt)
        if self.auto and self.hp<self.MAX_HP:
            if hasattr(self,'_ai_state') and self._ai_state in ("cover","retreat"):
                self.hp=min(self.MAX_HP, self.hp+3.0*dt)

    @property
    def alive(self): return self.hp>0

    def ai_update(self,npc,bullets,dt):
        if not self.auto or not npc.alive: return 0,0
        self._ai_dodge_t=max(0,self._ai_dodge_t-dt)
        survival=self.hp/self.MAX_HP
        dist=math.hypot(npc.x-self.x,npc.y-self.y)
        los_ok=has_los(self.x,self.y,npc.x,npc.y)

        moved=math.hypot(self.x-self._stuck_ref[0],self.y-self._stuck_ref[1])
        if moved>10: self._stuck_t=0.0; self._stuck_ref=(self.x,self.y)
        else: self._stuck_t+=dt
        cover_arrived=(self._ai_state=="cover" and self._cover_target is not None and
                       math.hypot(self.x-self._cover_target[0],self.y-self._cover_target[1])<25)
        if self._stuck_t>1.2 and not cover_arrived:
            self._stuck_t=0.0; self._flank_dir*=-1
            self._cover_target=None; self._cover_timer=0.0; self._ai_state="hunt"
            best_dx,best_dy=AW/2-self.x,AH/2-self.y
            for k in range(8):
                a=self._flank_angle + k*math.pi/4
                tdx,tdy=math.cos(a),math.sin(a)
                tx2,ty2=self.x+tdx*35,self.y+tdy*35
                if not iwall(tx2,self.y) and not iwall(self.x,ty2):
                    best_dx,best_dy=tdx,tdy; break
            ln=math.hypot(best_dx,best_dy) or 1
            return best_dx/ln,best_dy/ln

        best_threat=0.0; best_perp=(0.0,0.0)
        for b in bullets:
            if b.owner!="player": continue
            db=math.hypot(b.x-self.x,b.y-self.y)
            if db>110: continue
            bspd=math.hypot(b.vx,b.vy) or 1
            dot=(b.vx*(self.x-b.x)+b.vy*(self.y-b.y))/(bspd*db+0.001)
            if dot<0.5 or db/bspd>0.65: continue
            threat=dot*(1-db/(bspd*0.65))
            if threat>best_threat:
                best_threat=threat
                px2,py2=-b.vy/bspd,b.vx/bspd
                for sign in (1,-1):
                    ex=self.x+px2*sign*40; ey=self.y+py2*sign*40
                    if not iwall(ex,self.y) or not iwall(self.x,ey):
                        best_perp=(px2*sign,py2*sign); break
        if best_threat>0.3 and self._ai_dodge_t<=0:
            self._ai_dodge_t=0.3; return best_perp[0],best_perp[1]

        prev_ai_state=self._ai_state
        if survival<0.25 and self._ai_state not in ("cover","retreat"):
            self._ai_state="retreat"; self._cover_target=None; self._cover_timer=0.0
            if hasattr(self,'_retreat_timer'): self._retreat_timer=0.0
        elif survival<0.45 and self._ai_state not in ("cover","retreat","hunt"):
            self._ai_state="cover"; self._cover_target=None; self._cover_timer=0.0
        elif survival>0.70 and self._ai_state=="cover":
            self._ai_state="hunt"; self._cover_target=None
        elif los_ok and 70<dist<130 and self._ai_state=="hunt":
            self._ai_state="flank"
        elif (dist<70 or dist>130 or not los_ok) and self._ai_state=="flank":
            self._ai_state="hunt"
        if self._ai_state!=prev_ai_state:
            self._stuck_t=0.0; self._stuck_ref=(self.x,self.y)

        if self._ai_state=="retreat":
            if not hasattr(self,'_retreat_timer'): self._retreat_timer=0.0
            self._retreat_timer+=dt
            if self._retreat_timer>3.0 or survival>0.70:
                self._ai_state="hunt"; self._retreat_timer=0.0; return 0,0
            px2,py2=self.x-npc.x,self.y-npc.y; ln=math.hypot(px2,py2) or 1
            dx=px2/ln+math.sin(self._flank_angle)*0.3
            dy=py2/ln+math.cos(self._flank_angle)*0.3
            ln=math.hypot(dx,dy) or 1; return dx/ln,dy/ln

        elif self._ai_state=="cover":
            self._cover_timer+=dt
            if self._cover_timer>4.5:
                self._ai_state="hunt"; self._cover_target=None; self._cover_timer=0.0; return 0,0
            if self._cover_target is None:
                best=None; best_sc=-9999
                for r2 in range(1,GROWS-1,2):
                    for c2 in range(1,GCOLS-1,2):
                        if ARENA_MAP[r2][c2]: continue
                        cx2,cy2=cc(r2,c2)
                        if has_los(cx2,cy2,npc.x,npc.y): continue
                        sc3=math.hypot(cx2-npc.x,cy2-npc.y)*0.5-math.hypot(cx2-self.x,cy2-self.y)*0.4
                        if sc3>best_sc: best_sc=sc3; best=(cx2,cy2)
                self._cover_target=best or (AW-self.x,AH-self.y)
            tx,ty=self._cover_target
            if math.hypot(tx-self.x,ty-self.y)<20: return 0,0
            nr,nc=bfs(*w2c(self.x,self.y),*w2c(tx,ty))
            cx,cy=cc(nr,nc); dx,dy=cx-self.x,cy-self.y
            ln=math.hypot(dx,dy) or 1; return dx/ln,dy/ln

        elif self._ai_state=="flank":
            self._flank_angle+=dt*2.0*self._flank_dir
            px2,py2=npc.x-self.x,npc.y-self.y; ln=math.hypot(px2,py2) or 1
            perp_x=-py2/ln*self._flank_dir; perp_y=px2/ln*self._flank_dir
            if iwall(self.x+perp_x*25,self.y+perp_y*25):
                self._flank_dir*=-1; perp_x=-py2/ln*self._flank_dir; perp_y=px2/ln*self._flank_dir
            rnd=random.gauss(0,0.07)
            dx=perp_x*0.65+(px2/ln)*0.25+rnd; dy=perp_y*0.65+(py2/ln)*0.25+rnd
            ln=math.hypot(dx,dy) or 1; return dx/ln,dy/ln

        else:  # hunt
            self._flank_angle+=dt*1.4*self._flank_dir
            if not los_ok: self._hunt_no_los_t+=dt
            else: self._hunt_no_los_t=0.0
            if self._hunt_no_los_t>1.5:
                self._hunt_no_los_t=0.0; self._flank_dir*=-1
            if dist>70 or not los_ok:
                nr,nc=bfs(*w2c(self.x,self.y),*w2c(npc.x,npc.y))
                cx,cy=cc(nr,nc); dx,dy=cx-self.x,cy-self.y
                ln=math.hypot(dx,dy) or 1
                if ln<CELL*0.6:
                    dx=math.cos(self._flank_angle); dy=math.sin(self._flank_angle)
                else:
                    dx=dx/ln+math.sin(self._flank_angle)*0.3
                    dy=dy/ln+math.cos(self._flank_angle)*0.3
                    ln=math.hypot(dx,dy) or 1; dx/=ln; dy/=ln
                return dx,dy
            else:
                px2,py2=self.x-npc.x,self.y-npc.y; ln=math.hypot(px2,py2) or 1
                dx=px2/ln*0.55+math.sin(self._flank_angle)*self._flank_dir*0.45
                dy=py2/ln*0.55+math.cos(self._flank_angle)*self._flank_dir*0.45
                ln=math.hypot(dx,dy) or 1; return dx/ln,dy/ln
        return 0,0


# ── FSM NPC (sin cambios — es el baseline) ───────────────────────
class FSM_NPC:
    """
    FSM Tradicional Interactive style — hardcoded maximum tactical AI.
    - Burst fire con recoil lead
    - Supresión táctica (silencio deliberado para forzar movimiento)
    - Peek corners (asomarse desde cobertura)
    - Stance shuffle (movimiento lateral pre-disparo)
    - Grenade-throw fake (correr hacia cover fingiendo lanzar)
    - BFS pathfinding, búsqueda de flanco
    - Regen adaptativa, detección de LOS en patrulla
    """
    R=9; MAX_HP=240; DETECT=195; ATK_R=108
    SP_PAT=52; SP_CHA=88; SP_RET=72; SP_STRAFE=65; SP_PEEK=58
    SHOOT_CD_BASE=0.55   # Tradicional dispara más rápido que la FSM clásica
    BURST_SIZE_MIN=2; BURST_SIZE_MAX=4
    PATROL_PTS=[cc(2,2),cc(2,16),cc(16,16),cc(16,2)]
    STATES=("PATROL","CHASE","STRAFE","ATTACK","RETREAT",
            "COVER","SUPPRESS","PEEK","FLANK","SEARCH")

    def __init__(self):
        self.x,self.y=[float(v) for v in cc(9,9)]
        self.hp=self.MAX_HP; self.state="PATROL"
        self._pidx=0; self._ret_t=0.0; self._scd=0.0; self._hf=0.0
        self._strafe_dir=1; self._strafe_t=0.0
        self._no_hit_t=0.0; self._no_hit_streak=0
        self._last_px=0.0; self._last_py=0.0
        self._pvx=0.0; self._pvy=0.0
        self.npc_shots=0; self.npc_hits=0; self.hits_received=0
        self.decision_log=deque(maxlen=8)
        self._facing=0.0; self._facing_spd=0.85
        self.FOV=125; self.FOV_PATROL=82
        self.fov_deg=self.FOV
        self.detect_u=self.DETECT/CELL
        # Burst fire
        self._burst_remaining=0
        self._burst_cd=0.0
        self._inter_burst_cd=0.0
        self._shots_this_burst=0
        # Supresión
        self._suppress_t=0.0
        self._suppress_cd=0.0
        # Peek corner
        self._peek_t=0.0
        self._peek_dir=1
        self._peek_origin=None
        self._peek_target=None
        self._in_peek=False
        # Flank
        self._flank_target=None
        self._flank_angle=0.0
        # Cover dinámico
        self._cover_cell=None
        self._cover_pos=None
        self._cover_quality=0.0
        self._cover_t=0.0
        self._cover_upd=0.0
        # Búsqueda
        self._search_target=None
        self._search_t=0.0
        # Danger map local
        self._danger_map={}
        self._danger_decay=0.0
        # Stance shuffle
        self._shuffle_t=0.0
        self._shuffle_dir=1
        # Grenade fake
        self._grenade_fake_t=0.0
        self._grenade_fake_active=False
        # Recoil lead
        self._target_lead_x=0.0
        self._target_lead_y=0.0
        # Anti-stuck
        self._stuck_t=0.0
        self._stuck_pos=(self.x,self.y)
        # Adaptativo
        self._shot_accuracy=deque(maxlen=8)
        self._scd_mult=1.0
        self.SHOOT_CD_FIXED=self.SHOOT_CD_BASE

    def update(self,player,bullets,dt):
        self._hf=max(0,self._hf-dt)
        self._scd=max(0,self._scd-dt)
        self._strafe_t=max(0,self._strafe_t-dt)
        self._suppress_t=max(0,self._suppress_t-dt)
        self._suppress_cd=max(0,self._suppress_cd-dt)
        self._burst_cd=max(0,self._burst_cd-dt)
        self._inter_burst_cd=max(0,self._inter_burst_cd-dt)
        self._peek_t=max(0,self._peek_t-dt)
        self._grenade_fake_t=max(0,self._grenade_fake_t-dt)
        self._shuffle_t=max(0,self._shuffle_t-dt)
        self._cover_upd+=dt
        self._no_hit_t+=dt
        self._danger_decay+=dt

        # HP regen
        if self._no_hit_t>2.5 and self.hp<self.MAX_HP:
            regen={"PATROL":1.6,"COVER":1.8,"RETREAT":1.0,"SUPPRESS":1.2}.get(self.state,0.7)
            self.hp=min(self.MAX_HP,self.hp+regen*dt)

        # Danger map decay
        if self._danger_decay>8.0:
            self._danger_decay=0.0
            self._danger_map={k:max(0,v-18) for k,v in self._danger_map.items() if v>5}

        # Anti-stuck
        moved=math.hypot(self.x-self._stuck_pos[0],self.y-self._stuck_pos[1])
        if moved>12: self._stuck_t=0.0; self._stuck_pos=(self.x,self.y)
        else: self._stuck_t+=dt
        if self._stuck_t>3.0 and self.state in ("COVER","RETREAT","FLANK","PEEK"):
            self._stuck_t=0.0; self._cover_cell=None; self._flank_target=None
            self.state="CHASE"; self._log("Anti-stuck → CHASE")

        dist=math.hypot(player.x-self.x,player.y-self.y)
        survival=self.hp/self.MAX_HP

        # Tracking de velocidad del jugador
        self._pvx=(player.x-self._last_px)/max(dt,0.001)*0.3+self._pvx*0.7
        self._pvy=(player.y-self._last_py)/max(dt,0.001)*0.3+self._pvy*0.7
        self._last_px=player.x; self._last_py=player.y

        # Orientación
        if self.state=="PATROL":
            self._facing+=self._facing_spd*dt
        elif self.state=="PEEK" and self._peek_target:
            ta=math.atan2(self._peek_target[1]-self.y,self._peek_target[0]-self.x)
            diff=(ta-self._facing+math.pi)%(2*math.pi)-math.pi
            self._facing+=diff*min(1.0,dt*10)
        else:
            target_ang=math.atan2(player.y-self.y,player.x-self.x)
            diff=(target_ang-self._facing+math.pi)%(2*math.pi)-math.pi
            self._facing+=diff*min(1.0,dt*7)

        # Detección
        if self.state in ("PATROL","SEARCH"):
            can_see=point_in_vision(self.x,self.y,self._facing,self.FOV_PATROL,self.DETECT,player.x,player.y)
        else:
            can_see=has_los(self.x,self.y,player.x,player.y)

        # ── MÁQUINA DE ESTADOS Tradicional ──────────────────────────────
        prev=self.state

        if self.state=="PATROL":
            if can_see:
                if random.random()<0.28 and dist>80:
                    ft=self._calc_flank_target(player)
                    if ft: self._flank_target=ft; self.state="FLANK"; self._log("Detectado → FLANK táctico")
                    else: self.state="CHASE"; self._log("Detectado → CHASE")
                else:
                    self.state="CHASE"; self._log("Detectado → CHASE")

        elif self.state=="SEARCH":
            self._search_t-=dt
            if can_see: self.state="CHASE"; self._log("Encontrado en búsqueda → CHASE")
            elif self._search_t<=0: self.state="PATROL"; self._log("Búsqueda agotada → PATROL")
            else:
                if self._search_target and math.hypot(self.x-self._search_target[0],self.y-self._search_target[1])<25:
                    a=random.uniform(0,math.pi*2); r2=random.uniform(40,100)
                    nx=max(CELL,min(AW-CELL,self.x+math.cos(a)*r2))
                    ny=max(CELL,min(AH-CELL,self.y+math.sin(a)*r2))
                    self._search_target=(nx,ny)

        elif self.state=="CHASE":
            if dist<self.ATK_R*0.85: self.state="STRAFE"; self._log("En rango → STRAFE")
            elif not can_see and dist>self.DETECT*1.2:
                self._search_target=(self._last_px,self._last_py)
                self._search_t=5.0; self.state="SEARCH"; self._log("Perdí rastro → SEARCH")
            elif survival<0.30:
                self._find_cover(player.x,player.y); self.state="COVER"; self._log(f"HP={self.hp:.0f} → COVER")
            elif dist<120 and not can_see and self._grenade_fake_t<=0 and random.random()<0.04:
                self._grenade_fake_active=True; self._grenade_fake_t=2.0
                self._log("GRENADE FAKE: correr hacia flanco")

        elif self.state=="FLANK":
            if self._flank_target and math.hypot(self.x-self._flank_target[0],self.y-self._flank_target[1])<28:
                self.state="CHASE"; self._log("Flanco alcanzado → CHASE")
            elif dist<self.ATK_R*0.8: self.state="STRAFE"; self._log("En rango en flanco → STRAFE")
            elif not can_see and dist>self.DETECT*1.3: self.state="PATROL"; self._log("Perdido en flanco → PATROL")

        elif self.state=="STRAFE":
            if dist<self.ATK_R*0.5: self.state="ATTACK"; self._log("Muy cerca → ATTACK")
            elif dist>self.ATK_R*1.35: self.state="CHASE"; self._log("Lejos → CHASE")
            elif survival<0.35:
                self._find_cover(player.x,player.y); self.state="COVER"; self._log(f"HP bajo en STRAFE → COVER")
            elif self._can_peek(player) and self._peek_t<=0:
                self._setup_peek(player); self.state="PEEK"; self._log("PEEK corner → exposición mínima")

        elif self.state=="ATTACK":
            if dist>self.ATK_R: self.state="STRAFE"
            elif survival<0.20:
                self._find_cover(player.x,player.y); self.state="COVER"; self._log("HP crítico → COVER")

        elif self.state=="PEEK":
            if self._peek_t<=0 or not can_see:
                self.state="STRAFE"; self._in_peek=False; self._log("Peek completado → STRAFE")
            elif survival<0.30:
                self.state="COVER"; self._in_peek=False; self._log("Peek abortado → COVER")

        elif self.state=="SUPPRESS":
            self._suppress_t-=0
            if self._suppress_t<=0:
                self.state="STRAFE"; self._log("Supresión terminada → STRAFE")
            elif not can_see or dist>self.DETECT:
                self.state="CHASE"; self._log("Jugador perdido en SUPPRESS → CHASE")

        elif self.state=="COVER":
            self._cover_t-=dt
            if self._cover_upd>1.8:
                self._cover_upd=0.0; self._find_cover(player.x,player.y)
            if (self.hp>self.MAX_HP*0.75 and self._cover_t<1.5) or self._cover_t<=0:
                self.state="CHASE"; self._log(f"Recuperado en COVER → CHASE hp={self.hp:.0f}")
            elif survival>0.50 and can_see and dist<self.ATK_R*1.3:
                self._suppress_t=random.uniform(1.0,2.2); self._suppress_cd=4.0
                self.state="SUPPRESS"; self._log(f"Desde COVER → SUPPRESS {self._suppress_t:.1f}s")

        elif self.state=="RETREAT":
            self._ret_t-=dt
            if self._ret_t<=0:
                if survival>0.55: self.state="CHASE"; self._log("Retreat OK → CHASE")
                else:
                    self._find_cover(player.x,player.y); self.state="COVER"; self._log("Retreat → COVER")

        if self.state!=prev:
            self._stuck_t=0.0; self._stuck_pos=(self.x,self.y)

        self._move(player,dt)
        self._dodge(bullets,dt)
        self.fov_deg=self.FOV; self.facing=self._facing
        self.SHOOT_CD_FIXED=self.SHOOT_CD_BASE*self._scd_mult

        # ── DISPARO Tradicional ────────────────────────────────────────
        self._handle_shooting(player,bullets,dist,can_see)

    def _handle_shooting(self,player,bullets,dist,can_see):
        if not can_see: return
        if self._suppress_t>0: return

        lead_t=min(dist/280.0, 0.35)
        aim_x=player.x+self._pvx*lead_t
        aim_y=player.y+self._pvy*lead_t
        aim_err=max(0, (dist-80)/350)*random.gauss(0,8)
        aim_x+=aim_err; aim_y+=aim_err*random.uniform(-1,1)

        can_shoot=(self.state in ("ATTACK","STRAFE","FLANK","PEEK","SUPPRESS") or
                   (self.state=="CHASE" and dist<self.ATK_R*1.5) or
                   (self.state=="RETREAT" and dist<self.ATK_R*1.1))
        if not can_shoot: return

        if self._burst_remaining>0 and self._burst_cd<=0:
            bullets.append(Bullet(self.x,self.y,aim_x-self.x,aim_y-self.y,"npc"))
            self._scd=self.SHOOT_CD_BASE*0.28; self._burst_cd=self.SHOOT_CD_BASE*0.28
            self._burst_remaining-=1; self.npc_shots+=1
            if self._burst_remaining==0:
                self._inter_burst_cd=random.uniform(0.55,1.10)
                self._shuffle_t=random.uniform(0.3,0.6)
        elif self._burst_remaining==0 and self._inter_burst_cd<=0 and self._scd<=0:
            if self.state=="SUPPRESS":
                self._burst_remaining=random.randint(1,2)
            elif self.state in ("ATTACK","PEEK"):
                self._burst_remaining=random.randint(self.BURST_SIZE_MAX,self.BURST_SIZE_MAX+1)
            else:
                self._burst_remaining=random.randint(self.BURST_SIZE_MIN,self.BURST_SIZE_MAX)
            self._shots_this_burst=self._burst_remaining
            if (self._suppress_cd<=0 and len(self._shot_accuracy)>=4 and
                    sum(self._shot_accuracy)/len(self._shot_accuracy)<0.15 and
                    random.random()<0.30):
                self._suppress_t=random.uniform(0.8,1.5); self._suppress_cd=5.0
                self.state="SUPPRESS"; self._burst_remaining=0
                self._log(f"Auto-supresión {self._suppress_t:.1f}s")

    def _move(self,player,dt):
        sr,sc=w2c(self.x,self.y)
        dist=math.hypot(player.x-self.x,player.y-self.y)

        if self.state=="PATROL":
            tx,ty=self.PATROL_PTS[self._pidx]
            if math.hypot(tx-self.x,ty-self.y)<14: self._pidx=(self._pidx+1)%4
            nr,nc=bfs(sr,sc,*w2c(tx,ty))
            dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=self.SP_PAT

        elif self.state=="SEARCH":
            if self._search_target:
                tx,ty=self._search_target
                if math.hypot(self.x-tx,self.y-ty)<22: dx,dy=0,0; spd=0
                else:
                    nr,nc=bfs(sr,sc,*w2c(tx,ty))
                    dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=self.SP_CHA*0.7
            else: dx,dy=0,0; spd=0

        elif self.state=="CHASE":
            if self._grenade_fake_active and self._grenade_fake_t>0:
                a=math.atan2(player.y-self.y,player.x-self.x)+math.pi*0.6*self._strafe_dir
                tx2=player.x+math.cos(a)*70; ty2=player.y+math.sin(a)*70
                tx2=max(CELL,min(AW-CELL,tx2)); ty2=max(CELL,min(AH-CELL,ty2))
                nr,nc=bfs(sr,sc,*w2c(tx2,ty2))
                dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=self.SP_CHA*1.15
            else:
                nr,nc=bfs(sr,sc,*w2c(player.x,player.y))
                dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=self.SP_CHA
            if self._grenade_fake_t<=0: self._grenade_fake_active=False

        elif self.state=="FLANK":
            if self._flank_target:
                tx,ty=self._flank_target
                nr,nc=bfs(sr,sc,*w2c(tx,ty))
                dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=self.SP_CHA*0.92
            else: dx,dy=player.x-self.x,player.y-self.y; spd=self.SP_CHA

        elif self.state in ("STRAFE","SUPPRESS"):
            if self._strafe_t<=0:
                px,py=player.x-self.x,player.y-self.y; ln=math.hypot(px,py) or 1
                for sign in (self._strafe_dir, -self._strafe_dir):
                    tx2=self.x+(-py/ln)*sign*30; ty2=self.y+(px/ln)*sign*30
                    if not iwall(tx2,ty2): self._strafe_dir=sign; break
                self._strafe_t=random.uniform(0.9,2.2)
            if self._shuffle_t>0:
                dx=random.gauss(0,0.4); dy=random.gauss(0,0.4)
                spd=self.SP_STRAFE*0.35
            else:
                px,py=player.x-self.x,player.y-self.y; ln=math.hypot(px,py) or 1
                dx=(-py/ln)*self._strafe_dir+(px/ln)*0.25
                dy=(px/ln)*self._strafe_dir+(py/ln)*0.25
                spd=self.SP_STRAFE

        elif self.state=="ATTACK":
            dx,dy=player.x-self.x,player.y-self.y; spd=self.SP_CHA*0.55

        elif self.state=="PEEK":
            if self._peek_origin and not self._in_peek:
                tx2,ty2=self._peek_origin
                if math.hypot(self.x-tx2,self.y-ty2)<14:
                    self._in_peek=True; dx,dy=0,0; spd=0
                else:
                    nr,nc=bfs(sr,sc,*w2c(tx2,ty2))
                    dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=self.SP_PEEK
            else:
                dx,dy=0,0; spd=0

        elif self.state=="COVER":
            if self._cover_pos:
                tx2,ty2=self._cover_pos
                if math.hypot(self.x-tx2,self.y-ty2)<CELL*0.7: dx,dy=0,0; spd=0
                else:
                    nr,nc=bfs(sr,sc,*w2c(tx2,ty2))
                    dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=self.SP_CHA*1.05
            else:
                far=max(self.PATROL_PTS,key=lambda pt:math.hypot(pt[0]-player.x,pt[1]-player.y))
                nr,nc=bfs(sr,sc,*w2c(*far)); dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=self.SP_RET

        elif self.state=="RETREAT":
            away_x,away_y=self.x-player.x,self.y-player.y; al=math.hypot(away_x,away_y) or 1
            far=max(self.PATROL_PTS,key=lambda p2:math.hypot(p2[0]-player.x,p2[1]-player.y))
            nr,nc=bfs(sr,sc,*w2c(*far)); bx2,by2=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; bl=math.hypot(bx2,by2) or 1
            perp_x,perp_y=-by2/bl,bx2/bl
            dx=0.55*(away_x/al)+0.35*(bx2/bl)+0.10*perp_x*math.sin(self._ret_t*5)*self._strafe_dir
            dy=0.55*(away_y/al)+0.35*(by2/bl)+0.10*perp_y*math.sin(self._ret_t*5)*self._strafe_dir
            spd=self.SP_RET*1.18 if dist<35 else self.SP_RET
        else: return

        try:
            ln=math.hypot(dx,dy) or 1
            nx=self.x+(dx/ln)*spd*dt; ny=self.y+(dy/ln)*spd*dt
            if not iwall(nx,self.y): self.x=max(9,min(AW-9,nx))
            if not iwall(self.x,ny): self.y=max(9,min(AH-9,ny))
        except Exception: pass

    def _find_cover(self,px,py):
        best=None; best_sc=-9999
        sr,sc=w2c(self.x,self.y)
        for r in range(max(0,sr-5),min(GROWS,sr+6)):
            for c in range(max(0,sc-5),min(GCOLS,sc+6)):
                if ARENA_MAP[r][c]: continue
                cx2,cy2=cc(r,c)
                if has_los(cx2,cy2,px,py): continue
                near_wall=any(ARENA_MAP[r+dr][c+dc] for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]
                              if 0<=r+dr<GROWS and 0<=c+dc<GCOLS)
                d_me=math.hypot(cx2-self.x,cy2-self.y)
                d_pl=math.hypot(cx2-px,cy2-py)
                danger=self._danger_map.get((r,c),0)
                sc2=float(near_wall)*30+d_pl*0.3-d_me*0.2-danger*0.4
                if sc2>best_sc: best_sc=sc2; best=(cx2,cy2)
        self._cover_pos=best
        self._cover_quality=min(1.0,max(0,best_sc/80.0))
        self._cover_t=random.uniform(2.5,4.5)
        self._cover_cell=None

    def _can_peek(self,player):
        sr,sc=w2c(self.x,self.y)
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr2,nc2=sr+dr,sc+dc
            if 0<=nr2<GROWS and 0<=nc2<GCOLS and ARENA_MAP[nr2][nc2]:
                pr,pc=sr-dr,sc-dc
                if 0<=pr<GROWS and 0<=pc<GCOLS and not ARENA_MAP[pr][pc]:
                    px2,py2=cc(pr,pc)
                    if has_los(px2,py2,player.x,player.y):
                        return True
        return False

    def _setup_peek(self,player):
        sr,sc=w2c(self.x,self.y)
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr2,nc2=sr+dr,sc+dc
            if 0<=nr2<GROWS and 0<=nc2<GCOLS and ARENA_MAP[nr2][nc2]:
                pr,pc=sr-dr,sc-dc
                if 0<=pr<GROWS and 0<=pc<GCOLS and not ARENA_MAP[pr][pc]:
                    px2,py2=cc(pr,pc)
                    if has_los(px2,py2,player.x,player.y):
                        self._peek_origin=(px2,py2)
                        self._peek_target=(player.x,player.y)
                        self._peek_t=random.uniform(0.6,1.1)
                        self._in_peek=False
                        return

    def _calc_flank_target(self,player):
        a=math.atan2(player.y-self.y,player.x-self.x)+math.pi*0.5*random.choice([-1,1])
        for r2 in [80,120,60]:
            tx=player.x+math.cos(a)*r2; ty=player.y+math.sin(a)*r2
            tx=max(CELL,min(AW-CELL,tx)); ty=max(CELL,min(AH-CELL,ty))
            tr,tc=w2c(tx,ty)
            if 0<=tr<GROWS and 0<=tc<GCOLS and not ARENA_MAP[tr][tc]:
                if not has_los(tx,ty,self.x,self.y):
                    return (tx,ty)
        return None

    def take_hit(self,d=15):
        self.hp=max(0,self.hp-d); self._hf=0.5
        self._no_hit_t=0.0; self.hits_received+=1
        r,c=w2c(self.x,self.y)
        self._danger_map[(r,c)]=self._danger_map.get((r,c),0)+d
        if self.state in ("ATTACK","STRAFE","SUPPRESS"):
            self._find_cover(self._last_px,self._last_py)
            self.state="COVER"
            self._log(f"Golpeado {d}dmg → COVER inmediato ({self.hp:.0f}HP)")
        elif self.state=="RETREAT":
            self._ret_t=min(self._ret_t+0.8,3.5)
            self._log(f"Golpeado en RETREAT ({self.hp:.0f}HP) → +0.8s")
        else:
            self.state="RETREAT"; self._ret_t=2.2
            self._log(f"Golpeado ({self.hp:.0f}HP) → RETREAT 2.2s")
        self._shot_accuracy.append(False)

    def register_npc_hit(self):
        self.npc_hits+=1
        self._shot_accuracy.append(True)
        if len(self._shot_accuracy)>=4:
            acc=sum(self._shot_accuracy)/len(self._shot_accuracy)
            self._scd_mult=max(0.75, min(1.25, 1.0-acc*0.25+0.05))

    def _dodge(self,bullets,dt):
        best_tti=9999; best_dir=(0,0)
        for b in bullets:
            if b.owner!="player": continue
            db=math.hypot(b.x-self.x,b.y-self.y)
            if db>100: continue
            bspd=math.hypot(b.vx,b.vy) or 1
            dot=(b.vx*(self.x-b.x)+b.vy*(self.y-b.y))/(bspd*(db+0.001))
            if dot<0.5: continue
            tti=db/bspd
            if tti<best_tti:
                best_tti=tti
                perp_x=-b.vy/bspd; perp_y=b.vx/bspd
                for sign in (1,-1):
                    if not iwall(self.x+perp_x*sign*40,self.y+perp_y*sign*40):
                        best_dir=(perp_x*sign, perp_y*sign); break
        if best_tti<0.55 and (best_dir[0]!=0 or best_dir[1]!=0):
            spd=min(95,140/max(best_tti,0.1))*dt
            nx=self.x+best_dir[0]*spd; ny=self.y+best_dir[1]*spd
            if not iwall(nx,self.y): self.x=max(9,min(AW-9,nx))
            if not iwall(self.x,ny): self.y=max(9,min(AH-9,ny))

    def _log(self,reason):
        self.decision_log.appendleft({"state":self.state,"reason":reason})

    @property
    def alive(self): return self.hp>0
    @property
    def color(self): return P["fsm_hi"] if self._hf>0.25 else P["fsm_npc"]
    @property
    def xu(self): return self.x/CELL
    @property
    def yu(self): return self.y/CELL
    @property
    def max_hp(self): return self.MAX_HP
    @property
    def flash(self): return self._hf


# =============================================================================
# NUEVOS COMPONENTES COGNITIVOS PARA NEURON657
# =============================================================================

class WorldModel:
    """
    Modelo cognitivo del entorno (para uso interno del NPC, no del motor).
    """
    def __init__(self):
        self.player_pos = (0.0, 0.0)
        self.player_vel = (0.0, 0.0)
        self.player_heading = 0.0
        self.last_seen_time = 0.0
        self.player_confidence = 0.0
        self.npc_x = 0.0
        self.npc_y = 0.0
        self.shots_this_action = 0
        self.danger_heatmap = defaultdict(float)
        self.known_covers = []
        self._scored_covers = []
        self._player_ax = 0.0
        self._player_ay = 0.0
        self.predicted_path = []
        self.prediction_horizon = 2.0
        self.last_update = 0.0
        self.version = 0

    def update(self, perception: Dict[str, Any], dt: float) -> None:
        current_time = time.time()
        if perception.get('los', False):
            old_vel = self.player_vel
            self.player_pos = perception['player_pos']
            new_vel = perception.get('player_vel', (0.0, 0.0))
            if dt > 0:
                self._player_ax = (new_vel[0] - old_vel[0]) / dt
                self._player_ay = (new_vel[1] - old_vel[1]) / dt
            self.player_vel = new_vel
            self.last_seen_time = current_time
            self.player_confidence = 1.0
        else:
            self.player_confidence = max(0.0, self.player_confidence - dt * 0.4)
            if self.player_confidence > 0:
                px, py = self.player_pos
                vx, vy = self.player_vel
                ax = getattr(self, '_player_ax', 0.0)
                ay = getattr(self, '_player_ay', 0.0)
                self.player_pos = (px + vx * dt + 0.5 * ax * dt * dt,
                                   py + vy * dt + 0.5 * ay * dt * dt)

        npc_r, npc_c = w2c(getattr(self, 'npc_x', self.player_pos[0]),
                           getattr(self, 'npc_y', self.player_pos[1]))
        danger_val = perception.get('danger_here', 0)
        if danger_val > 0:
            self.danger_heatmap[(npc_r, npc_c)] += danger_val

        decay = 0.995 ** (dt * 60)
        for cell in list(self.danger_heatmap.keys()):
            self.danger_heatmap[cell] *= decay
            if self.danger_heatmap[cell] < 0.5:
                del self.danger_heatmap[cell]

        if 'covers' in perception:
            npc_x = getattr(self, 'npc_x', self.player_pos[0])
            npc_y = getattr(self, 'npc_y', self.player_pos[1])
            survival = perception.get('survival', 1.0)
            new_covers = []
            for cx, cy in perception['covers']:
                cr, cc2 = w2c(cx, cy)
                danger = self.danger_heatmap.get((cr, cc2), 0)
                dist_npc = math.hypot(cx - npc_x, cy - npc_y)
                dist_player = math.hypot(cx - self.player_pos[0], cy - self.player_pos[1])
                urgency = 1.5 if survival < 0.4 else 1.0
                score = (dist_player * 0.4 * urgency - dist_npc * 0.3 - danger * 0.3)
                new_covers.append((cx, cy, score))

            existing = {(cx, cy): sc for cx, cy, sc in self._scored_covers}
            for cx, cy, sc in new_covers:
                key = (cx, cy)
                if key in existing:
                    existing[key] = existing[key] * 0.7 + sc * 0.3
                else:
                    existing[key] = sc
            sorted_covers = sorted(existing.items(), key=lambda x: x[1], reverse=True)[:25]
            self._scored_covers = [(cx, cy, sc) for (cx, cy), sc in sorted_covers]
            self.known_covers = [(cx, cy) for (cx, cy), _ in sorted_covers]

        self._predict_path()
        self.last_update = current_time
        self.version += 1

    def _predict_path(self):
        px, py = self.player_pos
        vx, vy = self.player_vel
        ax = getattr(self, '_player_ax', 0.0) * 0.3
        ay = getattr(self, '_player_ay', 0.0) * 0.3
        self.predicted_path = []
        for t in [0.25, 0.5, 1.0, 1.5, 2.0]:
            pred_x = px + vx * t + 0.5 * ax * t * t
            pred_y = py + vy * t + 0.5 * ay * t * t
            pred_x = max(CELL, min(AW - CELL, pred_x))
            pred_y = max(CELL, min(AH - CELL, pred_y))
            self.predicted_path.append((pred_x, pred_y))

    def predict_position(self, t_ahead: float) -> Tuple[float, float]:
        px, py = self.player_pos
        vx, vy = self.player_vel
        ax = getattr(self, '_player_ax', 0.0) * 0.3
        ay = getattr(self, '_player_ay', 0.0) * 0.3
        pred_x = px + vx * t_ahead + 0.5 * ax * t_ahead * t_ahead
        pred_y = py + vy * t_ahead + 0.5 * ay * t_ahead * t_ahead
        return (max(CELL, min(AW-CELL, pred_x)),
                max(CELL, min(AH-CELL, pred_y)))

    def best_cover_against(self, target_pos: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        candidates = self._scored_covers if self._scored_covers else [
            (cx, cy, 0.0) for cx, cy in self.known_covers
        ]
        best = None
        best_score = -9999
        for cx, cy, base_score in candidates:
            if has_los(cx, cy, *target_pos):
                continue
            cr, cc2 = w2c(cx, cy)
            danger = self.danger_heatmap.get((cr, cc2), 0)
            final_score = base_score - danger * 0.5
            if final_score > best_score:
                best_score = final_score
                best = (cx, cy)
        return best

    def snapshot(self) -> Dict:
        return {
            'player_pos': self.player_pos,
            'player_vel': self.player_vel,
            'player_heading': self.player_heading,
            'last_seen_time': self.last_seen_time,
            'player_confidence': self.player_confidence,
            'danger_heatmap': dict(self.danger_heatmap),
            'known_covers': self.known_covers,
            'predicted_path': self.predicted_path,
            'version': self.version,
        }

    @classmethod
    def from_snapshot(cls, data: Dict) -> 'WorldModel':
        wm = cls()
        wm.player_pos = data['player_pos']
        wm.player_vel = data['player_vel']
        wm.player_heading = data['player_heading']
        wm.last_seen_time = data['last_seen_time']
        wm.player_confidence = data['player_confidence']
        wm.danger_heatmap = defaultdict(float, data['danger_heatmap'])
        wm.known_covers = data['known_covers']
        wm.predicted_path = data['predicted_path']
        wm.version = data['version']
        return wm


class AttentionGate:
    """
    Filtro atencional: modula la importancia de las distintas señales.
    """
    def __init__(self):
        self.focus = None
        self.suppressed_drives = set()
        self.attention_bias = 1.0
        self.last_shift = 0.0

    def update(self, drives: Dict[str, float], world_model: WorldModel, dt: float):
        current_time = time.time()
        fear = drives.get('fear', 0)
        aggression = drives.get('aggression', 0)
        survival = drives.get('survival', 1.0)

        if fear > 0.7:
            self.focus = 'survival'
            self.suppressed_drives = {'curiosity', 'prey'}
            self.attention_bias = 1.5
        elif aggression > 0.6 and world_model.player_confidence > 0.5:
            self.focus = 'attack'
            self.suppressed_drives = {'caution', 'curiosity'}
            self.attention_bias = 1.3
        elif world_model.last_seen_time < current_time - 2.0:
            self.focus = 'search'
            self.suppressed_drives = {'prey', 'aggression'}
            self.attention_bias = 1.2
        else:
            self.focus = None
            self.suppressed_drives = set()
            self.attention_bias = 1.0

        self.last_shift = current_time

    def apply_to_votes(self, votes: Dict[str, float], drives: Dict[str, float]) -> Dict[str, float]:
        biased = votes.copy()
        drive_tactic_map = {
            'curiosity': ['flanker', 'balanced'],
            'prey':      ['berserker', 'aggressive'],
            'aggression':['aggressive', 'berserker', 'RAID'],
            'caution':   ['sniper', 'defensive'],
        }
        for suppressed_drive in self.suppressed_drives:
            for tactic in drive_tactic_map.get(suppressed_drive, []):
                if tactic in biased:
                    biased[tactic] *= 0.25

        if self.focus == 'survival':
            for tactic in ['aggressive', 'berserker', 'RAID']:
                if tactic in biased:
                    biased[tactic] *= 0.35
            for tactic in ['defensive', 'sniper', 'flanker']:
                biased[tactic] = biased.get(tactic, 0.0) + 0.15
        elif self.focus == 'attack':
            for tactic in ['aggressive', 'berserker', 'RAID', 'flanker']:
                if tactic in biased:
                    biased[tactic] *= 1.35
            for tactic in ['defensive']:
                if tactic in biased:
                    biased[tactic] *= 0.5
        elif self.focus == 'search':
            biased['flanker'] = biased.get('flanker', 0.0) + 0.20
            biased['balanced'] = biased.get('balanced', 0.0) + 0.10

        if self.attention_bias != 1.0:
            for tactic in biased:
                biased[tactic] *= self.attention_bias

        return {t: min(1.5, max(0.0, v)) for t, v in biased.items()}

    def should_process_stimulus(self, stimulus_type: str) -> bool:
        if self.focus == 'survival' and stimulus_type != 'threat':
            return False
        if self.focus == 'attack' and stimulus_type not in ('threat', 'enemy'):
            return False
        return True

    def snapshot(self) -> Dict:
        return {
            'focus': self.focus,
            'suppressed_drives': list(self.suppressed_drives),
            'attention_bias': self.attention_bias,
            'last_shift': self.last_shift,
        }

    @classmethod
    def from_snapshot(cls, data: Dict) -> 'AttentionGate':
        ag = cls()
        ag.focus = data['focus']
        ag.suppressed_drives = set(data['suppressed_drives'])
        ag.attention_bias = data['attention_bias']
        ag.last_shift = data['last_shift']
        return ag


class CognitivePlanner:
    """
    Genera y ejecuta planes de medio plazo (secuencias de acciones).
    """
    def __init__(self, horizon=4.0):
        self.active_plan = None
        self.current_step = 0
        self.plan_start_time = 0.0
        self.plan_score = 0.0
        self.horizon = horizon
        self.last_evaluation = 0.0
        self._plan_trigger = ''

    def generate_plan(self, world_model: WorldModel, drives: Dict, tactics_pool: Dict) -> bool:
        fear       = drives.get('fear', 0)
        aggression = drives.get('aggression', 0)
        curiosity  = drives.get('curiosity', 0)
        survival   = drives.get('survival', drives.get('survival', 1.0))

        if fear > 0.60:
            cover = world_model.best_cover_against(world_model.player_pos)
            if cover:
                counter_tactic = 'sniper' if survival > 0.35 else 'defensive'
                self.active_plan = [
                    {'type': 'move', 'target': cover, 'conditions': {'arrived': True}},
                    {'type': 'wait', 'duration': 1.2, 'conditions': {'time_elapsed': 1.2}},
                    {'type': 'tactic', 'name': counter_tactic, 'conditions': {'time_elapsed': 3.5}},
                ]
                self.plan_start_time = time.time()
                self.current_step = 0
                self.plan_score = self._evaluate_plan(self.active_plan, world_model, drives)
                self._plan_trigger = 'survival'
                return True
            self.active_plan = [
                {'type': 'tactic', 'name': 'flanker', 'conditions': {'time_elapsed': 2.5}},
            ]
            self.plan_start_time = time.time()
            self.current_step = 0
            self.plan_score = 0.3
            self._plan_trigger = 'survival_retreat'
            return True

        if aggression > 0.70 and world_model.player_confidence > 0.5:
            flank_pos = self._calc_flank_position(world_model)
            if flank_pos:
                self.active_plan = [
                    {'type': 'move', 'target': flank_pos, 'conditions': {'arrived': True}},
                    {'type': 'tactic', 'name': 'aggressive', 'conditions': {'time_elapsed': 2.5}},
                ]
                self.plan_start_time = time.time()
                self.current_step = 0
                self.plan_score = self._evaluate_plan(self.active_plan, world_model, drives)
                self._plan_trigger = 'attack'
                return True

        if curiosity > 0.50 and world_model.player_confidence < 0.3:
            pred_x, pred_y = world_model.predict_position(1.5)
            angle = random.uniform(0, 2 * math.pi)
            tx = pred_x + math.cos(angle) * 60
            ty = pred_y + math.sin(angle) * 60
            tx = max(CELL, min(AW - CELL, tx))
            ty = max(CELL, min(AH - CELL, ty))
            self.active_plan = [
                {'type': 'move', 'target': (tx, ty), 'conditions': {'arrived': True}},
                {'type': 'tactic', 'name': 'flanker', 'conditions': {'time_elapsed': 2.0}},
            ]
            self.plan_start_time = time.time()
            self.current_step = 0
            self.plan_score = self._evaluate_plan(self.active_plan, world_model, drives)
            self._plan_trigger = 'explore'
            return True

        self.active_plan = None
        return False

    def _evaluate_plan(self, plan, world_model, drives) -> float:
        score = 0.0
        discount = 1.0
        npc_x = getattr(world_model, 'npc_x', world_model.player_pos[0])
        npc_y = getattr(world_model, 'npc_y', world_model.player_pos[1])
        for step in plan:
            if step['type'] == 'move':
                dist_to_enemy = math.hypot(step['target'][0] - world_model.player_pos[0],
                                            step['target'][1] - world_model.player_pos[1])
                dist_to_npc  = math.hypot(step['target'][0] - npc_x,
                                           step['target'][1] - npc_y)
                if drives.get('aggression', 0) > 0.5:
                    score += discount * (200 - dist_to_enemy) / 200 * 10
                elif drives.get('fear', 0) > 0.5:
                    score += discount * dist_to_enemy / 200 * 8
                    score -= discount * dist_to_npc / 200 * 3
                else:
                    score += discount * 4
            elif step['type'] == 'shoot':
                score += discount * 15
            elif step['type'] == 'wait':
                score -= discount * 3
            elif step['type'] == 'tactic':
                score += discount * 6
            discount *= 0.85
        return score

    def update(self, dt: float, world_model: WorldModel, drives: Dict) -> Optional[str]:
        if self.active_plan is None:
            return None

        trigger = getattr(self, '_plan_trigger', '')
        fear = drives.get('fear', 0)
        aggression = drives.get('aggression', 0)
        elapsed = time.time() - self.plan_start_time

        interrupt = False
        if trigger == 'attack' and fear > 0.70:
            interrupt = True
        elif trigger == 'survival' and fear < 0.25 and elapsed > 1.5:
            interrupt = True
        elif elapsed > self.horizon:
            interrupt = True

        if interrupt:
            self.active_plan = None
            self._plan_trigger = ''
            return None

        current_action = self.active_plan[self.current_step]
        if self._check_conditions(current_action, world_model):
            self.current_step += 1
            if self.current_step >= len(self.active_plan):
                self.active_plan = None
                self._plan_trigger = ''
                return None
            current_action = self.active_plan[self.current_step]

        if current_action['type'] == 'tactic':
            return current_action['name']

        return None

    def _check_conditions(self, action, world_model):
        cond = action.get('conditions', {})
        if 'arrived' in cond and 'target' in action:
            tx, ty = action['target']
            npc_x = getattr(world_model, 'npc_x', world_model.player_pos[0])
            npc_y = getattr(world_model, 'npc_y', world_model.player_pos[1])
            dist = math.hypot(tx - npc_x, ty - npc_y)
            return dist < 20.0
        if 'duration' in action:
            return time.time() - self.plan_start_time > action['duration']
        if 'time_elapsed' in cond:
            return time.time() - self.plan_start_time > cond['time_elapsed']
        if 'shots_fired' in cond:
            return getattr(world_model, 'shots_this_action', 0) >= cond['shots_fired']
        return True

    def _calc_flank_position(self, world_model):
        px, py = world_model.player_pos
        npc_x = getattr(world_model, 'npc_x', px)
        npc_y = getattr(world_model, 'npc_y', py)
        base_angle = math.atan2(py - npc_y, px - npc_x)
        for sign in (1, -1):
            flank_angle = base_angle + sign * math.pi * 0.55
            tx = px + math.cos(flank_angle) * 80
            ty = py + math.sin(flank_angle) * 80
            tx = max(CELL, min(AW - CELL, tx))
            ty = max(CELL, min(AH - CELL, ty))
            if not iwall(tx, ty):
                return (tx, ty)
        return None

    def snapshot(self) -> Dict:
        if self.active_plan is None:
            return {'active_plan': None}
        return {
            'active_plan': self.active_plan,
            'current_step': self.current_step,
            'plan_start_time': self.plan_start_time,
            'plan_score': self.plan_score,
        }

    @classmethod
    def from_snapshot(cls, data: Dict) -> 'CognitivePlanner':
        planner = cls()
        if data.get('active_plan'):
            planner.active_plan = data['active_plan']
            planner.current_step = data['current_step']
            planner.plan_start_time = data['plan_start_time']
            planner.plan_score = data['plan_score']
        return planner


# =============================================================================
# NEURON657 NPC — versión con todos los componentes cognitivos integrados
# =============================================================================

class N657_NPC:
    """
    Motor cognitivo completo. Integra el nuevo motor neuron657_v13.
    """
    R=9; MAX_HP=240; DETECT=190
    PATROL_PTS=[cc(2,2),cc(2,16),cc(16,16),cc(16,2)]

    TACTICS={
        "aggressive":{"speed":98,  "scd":0.40,"atk_r":115,"ret_t":0.4,
                      "strafe":True, "flank":False,"kite":False,"chase_scd":0.52,
                      "fov":145, "detect_bonus":10},
        "balanced":  {"speed":76,  "scd":0.60,"atk_r":102,"ret_t":0.7,
                      "strafe":True, "flank":True, "kite":False,"chase_scd":0.68,
                      "fov":130, "detect_bonus":0},
        "defensive": {"speed":60,  "scd":0.75,"atk_r":88, "ret_t":1.0,
                      "strafe":False,"flank":False,"kite":True, "chase_scd":0.80,
                      "fov":110, "detect_bonus":15},
        "sniper":    {"speed":68,  "scd":0.46,"atk_r":172,"ret_t":0.6,
                      "strafe":False,"flank":False,"kite":True, "chase_scd":0.52,
                      "fov":100, "detect_bonus":30},
        "berserker": {"speed":112, "scd":0.30,"atk_r":82, "ret_t":0.25,
                      "strafe":False,"flank":False,"kite":False,"chase_scd":0.36,
                      "fov":155, "detect_bonus":5},
        "flanker":   {"speed":90,  "scd":0.53,"atk_r":106,"ret_t":0.45,
                      "strafe":False,"flank":True, "kite":False,"chase_scd":0.58,
                      "fov":130, "detect_bonus":0},
        "RAID": {"speed":95,  "scd":0.42,"atk_r":120,"ret_t":0.35,
                      "strafe":True, "flank":True, "kite":False,"chase_scd":0.55,
                      "fov":135, "detect_bonus":5},
    }

    _round_memory    = []
    _episodic_memory = []
    _best_tactic     = None
    _detect_adj      = 0
    _tactic_wins     = {}
    _round_count     = 0
    _shared_danger   = {}
    _shared_player_profile = {}
    _ltm_file        = 'npc_ltm.json'
    _fatigue_class   = 0.0

    def __init__(self):
        self.x,self.y=[float(v) for v in cc(9,9)]
        self.hp=self.MAX_HP; self.state="PATROL"
        self._pidx=0; self._ret_t=0.0; self._scd=0.0; self._hf=0.0
        self._strafe_dir=1; self._strafe_t=0.0
        self._flank_angle=0.0; self._kite_dir=1
        self.tactic=N657_NPC._best_tactic or "flanker"
        self.npc_shots=0; self.npc_hits=0; self.hits_received=0
        self._t_shots=0; self._t_hits=0; self._t_received=0
        self._eval_t=0.0
        self._no_hit_t=0.0; self._regen_rate=2.0; self._tactic_regen={}
        self._px_hist=deque(maxlen=8); self._py_hist=deque(maxlen=8)
        self._pt_hist=deque(maxlen=8)
        self._player_vx=0.0; self._player_vy=0.0
        self._player_ax=0.0; self._player_ay=0.0
        self._danger_map={}; self._danger_decay=0.0
        self._dir_danger={}
        self._retreat_target=None; self._retreat_arrived=False
        self.n_mode="autonomous"; self.n_strat="hybrid"; self.n_conf=0.88
        self.last_dec="Sistema iniciado."
        self.decision_log=deque(maxlen=8)
        self.engine=_make_engine() if NEURON_OK else None
        self._eff_detect=self.DETECT+N657_NPC._detect_adj
        self._facing=0.0; self._facing_spd=0.7
        self.FOV=130; self.FOV_PATROL=75
        self._ambush_pos=None
        self._ambush_wait=0.0
        self._ambush_max_wait=3.5
        self._ambush_fires=0
        self._search_spiral=[]
        self._search_idx=0
        self._last_known=None
        self._RAID_phase="hunt"
        self._RAID_t=0.0
        self._shot_window=deque(maxlen=10)
        self._adaptive_scd_mult=1.0
        self._tactic_flash=0.0
        self._prev_tactic=self.tactic
        self._post_hit_t=0.0
        self._last_dodge_dir=(0.0,0.0)
        self._anti_aim_dir=1
        self._anti_aim_cd=0.0
        self._anti_aim_t=0.0
        self._jitter_angle=random.uniform(0,6.28)
        self._jitter_cd=0.0
        self._dodge_log_t=0.0
        self._n_stuck_t=0.0
        self._drives={'fear':0.0,'aggression':0.0,'curiosity':0.0,'caution':0.0,'prey':0.0}
        self._death_risk=0.0
        self._n_stuck_pos=(self.x,self.y)
        self._last_px=self.x
        self._last_py=self.y
        self._fatigue=0.0
        self._fatigue_t=0.0
        self._suppress_t=0.0
        self._cover_quality = 0.0
        self._cover_pos=None
        self._profile_t=0.0
        # Nuevo: contador para llamar al motor cada cierto tiempo
        self._engine_eval_cd = 0.0

        # Componentes cognitivos locales (para el NPC)
        self.world_model = WorldModel()
        self.attention = AttentionGate()
        self.planner = CognitivePlanner()

        self._load_ltm_once()

    def _get_nearby_covers(self):
        covers = []
        r, c = w2c(self.x, self.y)
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                nr, nc = r + dr, c + dc
                if 0 <= nr < GROWS and 0 <= nc < GCOLS and not ARENA_MAP[nr][nc]:
                    if not has_los(cc(nr, nc)[0], cc(nr, nc)[1], self._last_px, self._last_py):
                        covers.append(cc(nr, nc))
        return covers

    @property
    def alive(self): return self.hp>0
    @property
    def color(self): return P["n_hi"] if self._hf>0.3 else P["n_npc"]
    @property
    def xu(self): return self.x/CELL
    @property
    def yu(self): return self.y/CELL
    @property
    def max_hp(self): return self.MAX_HP
    @property
    def flash(self): return self._hf
    @property
    def fov_deg(self):
        return self._p().get("fov", 130)
    @property
    def detect_u(self):
        return (self.DETECT + self._p().get("detect_bonus",0) + N657_NPC._detect_adj) / CELL
    @property
    def facing(self): return self._facing

    def _p(self): return self.TACTICS[self.tactic]

    def update(self,player,bullets,dt):
        if not self.alive: return
        self._hf=max(0,self._hf-dt); self._scd=max(0,self._scd-dt)
        self._strafe_t=max(0,self._strafe_t-dt)
        self._eval_t+=dt
        self._tactic_flash=max(0,self._tactic_flash-dt)

        dist=math.hypot(player.x-self.x,player.y-self.y)
        survival=self.hp/self.MAX_HP
        p=self._p(); prev=self.state

        self._update_player_tracking(player,dt)
        player_spd=math.hypot(self._player_vx,self._player_vy)
        in_combat2=self.state in ('ATTACK','STRAFE','FLANK','KITE','CHASE','AMBUSH')
        self._update_fatigue(dt, in_combat2)
        shot_eff2=self._t_hits/max(self._t_shots,1)
        toward_me2=((player.x-self.x)*(-self._player_vx)+(player.y-self.y)*(-self._player_vy))
        if dist>1: toward_me2/=(dist*max(player_spd,1))
        self._update_player_profile(dt,dist,player_spd,toward_me2,shot_eff2)
        self._update_suppression(dt,dist,has_los(self.x,self.y,player.x,player.y),player_spd)
        if not hasattr(self,'_cover_upd_t'): self._cover_upd_t=0.0
        self._cover_upd_t+=dt
        upd_interval=1.5 if self.state=='COVER' else 3.0
        if self._cover_upd_t>upd_interval:
            self._cover_upd_t=0.0
            self._find_dynamic_cover(player.x,player.y)

        toward_me=0
        if dist>1:
            toward_me=(((player.x-self.x)*(-self._player_vx)+(player.y-self.y)*(-self._player_vy))
                       /(dist*max(player_spd,1)))

        tac_fov=p.get("fov",130); self.FOV=tac_fov

        # Actualizar modelo del mundo local
        perception_data = {
            'player_pos': (player.x, player.y),
            'player_vel': (self._player_vx, self._player_vy),
            'los': has_los(self.x, self.y, player.x, player.y),
            'danger_here': self._danger_map.get(w2c(self.x, self.y), 0),
            'covers': self._get_nearby_covers(),
            'survival': self.hp / self.MAX_HP,
        }
        self.world_model.update(perception_data, dt)
        self.world_model.npc_x = self.x
        self.world_model.npc_y = self.y
        self.world_model.shots_this_action = self._t_shots

        # Anti-stuck
        n_moved=math.hypot(self.x-self._n_stuck_pos[0],self.y-self._n_stuck_pos[1])
        if n_moved>10: self._n_stuck_t=0.0; self._n_stuck_pos=(self.x,self.y)
        else: self._n_stuck_t+=dt
        if self._n_stuck_t>3.5 and self.state in ("COVER","RETREAT","FLANK","AMBUSH"):
            self._n_stuck_t=0.0; self._strafe_dir*=-1
            if hasattr(self,'_cover_cell'): self._cover_cell=None
            self._retreat_target=None; self._ambush_pos=None
            self.state="CHASE"; self._log(f"Anti-stuck: saliendo de {prev} → CHASE")

        self._danger_decay+=dt
        if self._danger_decay>=10.0:
            self._danger_decay=0.0
            self._danger_map={k:max(0,v-20) for k,v in self._danger_map.items() if v>5}
            self._dir_danger={k:max(0,v-15) for k,v in self._dir_danger.items() if v>5}

        self._no_hit_t+=dt
        if self._no_hit_t>2.0 and self.hp<self.MAX_HP:
            state_bonus={"PATROL":1.4,"COVER":1.6,"RETREAT":0.8,"KITE":0.9,
                         "CHASE":0.5,"STRAFE":0.4,"FLANK":0.4,"ATTACK":0.3,
                         "AMBUSH":1.2,"SEARCH":1.0,"RAID":0.6}
            self.hp=min(self.MAX_HP,self.hp+self._regen_rate*state_bonus.get(self.state,1.0)*dt)

        if len(self._shot_window)>=5:
            hit_rate=sum(1 for h in self._shot_window if h)/len(self._shot_window)
            if hit_rate>0.5:   self._adaptive_scd_mult=max(0.70,self._adaptive_scd_mult-0.02)
            elif hit_rate<0.2: self._adaptive_scd_mult=min(1.30,self._adaptive_scd_mult+0.03)

        tac_detect=self.DETECT+p.get("detect_bonus",0)+N657_NPC._detect_adj
        if self.state in ("PATROL","SEARCH"):
            los_direct=has_los(self.x,self.y,player.x,player.y)
            dist_now=math.hypot(player.x-self.x,player.y-self.y)
            los_detect=(point_in_vision(self.x,self.y,self._facing,
                                        self.FOV_PATROL,tac_detect,player.x,player.y)
                        or (los_direct and dist_now<tac_detect*0.55))
        else:
            los_detect=has_los(self.x,self.y,player.x,player.y)

        # Orientación
        if self.state in ("PATROL","SEARCH"):
            self._facing+=self._facing_spd*dt
        elif self.state=="AMBUSH":
            pred_x=player.x+self._player_vx*1.0; pred_y=player.y+self._player_vy*1.0
            target_ang=math.atan2(pred_y-self.y,pred_x-self.x)
            diff=(target_ang-self._facing+math.pi)%(2*math.pi)-math.pi
            self._facing+=diff*min(1.0,dt*4)
        else:
            target_ang=math.atan2(player.y-self.y,player.x-self.x)
            diff=(target_ang-self._facing+math.pi)%(2*math.pi)-math.pi
            self._facing+=diff*min(1.0,dt*8)

        # ── TRANSICIONES DE ESTADO ──
        can_see=los_detect
        if self.state=="PATROL":
            if can_see:
                if survival>0.6 and not has_los(self.x,self.y,player.x,player.y):
                    ap=self._find_ambush_point(player)
                    if ap:
                        self._ambush_pos=ap; self._ambush_wait=0.0; self._ambush_fires=0
                        self.state="AMBUSH"; self._log(f"Emboscada en ({ap[0]:.0f},{ap[1]:.0f})")
                    else: self.state="CHASE"
                else: self.state="CHASE"
        elif self.state=="AMBUSH":
            self._ambush_wait+=dt
            in_pos=(self._ambush_pos is not None and
                    math.hypot(self.x-self._ambush_pos[0],self.y-self._ambush_pos[1])<25)
            if (self._ambush_wait>self._ambush_max_wait or
                    has_los(self.x,self.y,player.x,player.y) and dist<p["atk_r"] or
                    self._ambush_fires>=3):
                self.state="CHASE"
                self._log(f"Emboscada ejecutada → CHASE ({self._ambush_fires} disparos)")
            elif survival<0.3:
                self.state="RETREAT"; self._ret_t=p["ret_t"]
                self._log("Emboscada abortada — HP crítico")
        elif self.state=="SEARCH":
            if can_see:
                self.state="CHASE"; self._last_known=None
                self._log("Jugador encontrado en SEARCH → CHASE")
            elif not self._search_spiral or self._search_idx>=len(self._search_spiral):
                self._last_known=None; self.state="PATROL"
                self._log("Búsqueda completada — volviendo a PATROL")
        elif self.state=="CHASE":
            if p["flank"] and dist<p["atk_r"]*0.9:      self.state="FLANK"
            elif p["strafe"] and dist<p["atk_r"]*0.70:  self.state="STRAFE"
            elif dist<p["atk_r"]*0.45:                  self.state="ATTACK"
            elif dist>tac_detect*1.4 and not los_detect:
                self._last_known=(player.x,player.y)
                self._search_spiral=self._build_search_spiral(player.x,player.y)
                self._search_idx=0; self.state="SEARCH"
                self._log(f"Perdí rastro → búsqueda espiral")
        elif self.state=="STRAFE":
            if dist>p["atk_r"]*1.3:   self.state="CHASE"
            elif dist<p["atk_r"]*0.5: self.state="RETREAT"; self._ret_t=p["ret_t"]
        elif self.state=="FLANK":
            if dist<p["atk_r"]*0.6:   self.state="RETREAT"; self._ret_t=p["ret_t"]
            elif dist>p["atk_r"]*1.8: self.state="CHASE"
        elif self.state=="ATTACK":
            if dist<35:                               self.state="RETREAT"; self._ret_t=p["ret_t"]
            elif p["kite"] and dist<p["atk_r"]*0.6: self.state="KITE"
            elif dist>p["atk_r"]*1.2:               self.state="CHASE"
        elif self.state=="KITE":
            if dist<30:                 self.state="RETREAT"; self._ret_t=p["ret_t"]
            elif dist>p["atk_r"]*0.95: self.state="ATTACK"
        elif self.state=="COVER":
            los_now=has_los(self.x,self.y,getattr(self,'_last_px',player.x),
                            getattr(self,'_last_py',player.y))
            if (not los_now or dist>80) and survival>0.45: self.state="CHASE"
            elif survival>0.70: self.state="CHASE"
        elif self.state=="RETREAT":
            self._ret_t-=dt
            if self._ret_t<=0: self._post_retreat(dist)
            elif survival>0.85 and dist>tac_detect*0.8:
                self._log(f"Retreat cancelado — HP={self.hp:.0f}"); self._post_retreat(dist)

        if self.tactic=="RAID": self._update_RAID(player,dt,dist)

        self._last_px=player.x; self._last_py=player.y
        self._move(player,dt,p)
        self._dodge(bullets,dt)

        # Disparo
        in_combat=self.state in ("ATTACK","STRAFE","FLANK","KITE","CHASE","RETREAT","AMBUSH")
        RAID_burst=(self.tactic=="RAID" and self._RAID_phase=="burst"
                         and self.state not in ("PATROL","SEARCH","COVER"))
        if (in_combat or RAID_burst) and self._scd<=0:
            if self.state in ("ATTACK","STRAFE","FLANK"):    scd=p["scd"]
            elif self.state=="AMBUSH":                        scd=p["scd"]*0.85
            elif self.state=="KITE":                          scd=p["scd"]*0.90
            elif self.state=="CHASE":
                if dist<p["atk_r"]:          scd=p["scd"]
                elif dist<p["atk_r"]*2.0:    scd=p.get("chase_scd",p["scd"]*1.2)
                else:                         scd=p["scd"]*1.5
            elif self.state=="RETREAT":  scd=p["scd"]*1.6 if dist<p["atk_r"]*1.3 else p["scd"]*2.5
            elif RAID_burst:        scd=p["scd"]*0.80
            else:                        scd=p["scd"]*1.5
            scd*=self._adaptive_scd_mult
            fat_pen=self._fatigue_penalty()
            scd=scd/max(0.3,fat_pen['accuracy'])
            if self._is_suppressing: scd=9999
            if has_los(self.x,self.y,player.x,player.y):
                aim_x, aim_y = self.world_model.predict_position(0.25)
                if self.state=="AMBUSH":
                    aim_x=player.x+self._player_vx*0.30; aim_y=player.y+self._player_vy*0.30
                self._do_shoot(aim_x,aim_y,bullets,scd,dt)

        # Evaluación cognitiva (cada ~1s o si recibió 2+ hits)
        if self._eval_t>=1.0:
            self._eval_t=0.0; self._evaluate(dist,toward_me,player_spd)
        elif self._t_received>=2 and self._eval_t>0.5:
            self._eval_t=0.0; self._evaluate(dist,toward_me,player_spd)

    def _do_shoot(self,aim_x,aim_y,bullets,scd,dt):
        bullets.append(Bullet(self.x,self.y,aim_x-self.x,aim_y-self.y,"npc"))
        self._scd=scd; self.npc_shots+=1; self._t_shots+=1
        self._shot_window.append(False)

    def _update_RAID(self,player,dt,dist):
        p=self._p(); self._RAID_t+=dt
        if self._RAID_phase=="hunt":
            if dist<p["atk_r"]*1.1 and has_los(self.x,self.y,player.x,player.y):
                self._RAID_phase="burst"; self._RAID_t=0.0
                self._log("RAID: burst iniciado")
        elif self._RAID_phase=="burst":
            if self._RAID_t>1.2 or self._t_shots>=3:
                self._RAID_phase="retreat_micro"; self._RAID_t=0.0
                self._retreat_target=self._safe_retreat_point()
                self._log("RAID: micro-retreat")
        elif self._RAID_phase=="retreat_micro":
            if self._RAID_t>1.8:
                self._RAID_phase="hunt"; self._RAID_t=0.0
                self._log("RAID: volviendo a cazar")

    def _update_player_tracking(self,player,dt):
        self._px_hist.append(player.x); self._py_hist.append(player.y)
        if len(self._px_hist)>=3:
            self._player_vx=(self._px_hist[-1]-self._px_hist[-3])/(2*dt+0.001)
            self._player_vy=(self._py_hist[-1]-self._py_hist[-3])/(2*dt+0.001)
        if len(self._px_hist)>=5:
            vx0=(self._px_hist[-3]-self._px_hist[-5])/(2*dt+0.001)
            vy0=(self._py_hist[-3]-self._py_hist[-5])/(2*dt+0.001)
            self._player_ax=(self._player_vx-vx0)/(2*dt+0.001)
            self._player_ay=(self._player_vy-vy0)/(2*dt+0.001)

    def _find_ambush_point(self,player):
        LEAD_T=1.5
        pred_x=max(CELL,min(AW-CELL,player.x+self._player_vx*LEAD_T))
        pred_y=max(CELL,min(AH-CELL,player.y+self._player_vy*LEAD_T))
        best=None; best_sc=-9999
        for r in range(1,GROWS-1):
            for c in range(1,GCOLS-1):
                if ARENA_MAP[r][c]: continue
                cx2,cy2=cc(r,c)
                if has_los(cx2,cy2,player.x,player.y): continue
                if not has_los(cx2,cy2,pred_x,pred_y): continue
                d_me=math.hypot(cx2-self.x,cy2-self.y)
                if d_me>180: continue
                danger=self._danger_map.get((r,c),0)+N657_NPC._shared_danger.get((r,c),0)*0.3
                score=-d_me*0.5+40-danger*1.5
                if score>best_sc: best_sc=score; best=(cx2,cy2)
        return best

    def _build_search_spiral(self,cx,cy,radius=3):
        cr,cc2=w2c(cx,cy); pts=[]; visited=set()
        for ring in range(1,radius+1):
            for dr in range(-ring,ring+1):
                for dc in range(-ring,ring+1):
                    if max(abs(dr),abs(dc))!=ring: continue
                    nr,nc=cr+dr,cc2+dc
                    if (nr,nc) in visited: continue
                    if 0<=nr<GROWS and 0<=nc<GCOLS and not ARENA_MAP[nr][nc]:
                        pts.append(cc(nr,nc)); visited.add((nr,nc))
        return pts

    def _register_danger_directional(self,damage,from_x,from_y):
        r,c=w2c(self.x,self.y)
        angle=math.atan2(self.y-from_y,self.x-from_x)%(2*math.pi)
        dir_bucket=int(angle/(math.pi/4))%8
        self._dir_danger[(r,c,dir_bucket)]=self._dir_danger.get((r,c,dir_bucket),0)+damage
        self._danger_map[(r,c)]=self._danger_map.get((r,c),0)+damage
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
            nr2,nc2=r+dr,c+dc
            if 0<=nr2<GROWS and 0<=nc2<GCOLS:
                self._danger_map[(nr2,nc2)]=self._danger_map.get((nr2,nc2),0)+damage*0.5
        N657_NPC._shared_danger[(r,c)]=N657_NPC._shared_danger.get((r,c),0)+damage*0.4

    def _directional_danger(self,r,c,from_angle):
        dir_bucket=int(from_angle/(math.pi/4))%8
        return self._dir_danger.get((r,c,dir_bucket),0)

    def _predict_player(self, dist, dt):
        px_h = list(self._px_hist)
        py_h = list(self._py_hist)
        n = len(px_h)
        if n < 3:
            return px_h[-1] if px_h else self.x, py_h[-1] if py_h else self.y
        vx = (px_h[-1] - px_h[-2]) / (dt + 0.001)
        vy = (py_h[-1] - py_h[-2]) / (dt + 0.001)
        if n >= 5:
            t_vals = list(range(n))
            tm = sum(t_vals) / n
            cov_tx = sum((t_vals[i]-tm)*(px_h[i]-sum(px_h)/n) for i in range(n))
            var_t  = sum((t-tm)**2 for t in t_vals) or 1
            vx = cov_tx / var_t / (dt + 0.001)
            cov_ty = sum((t_vals[i]-tm)*(py_h[i]-sum(py_h)/n) for i in range(n))
            vy = cov_ty / var_t / (dt + 0.001)
        BULLET_SPD = 220
        lead_t = min(dist / BULLET_SPD, 0.25)
        aim_x = px_h[-1] + vx * lead_t
        aim_y = py_h[-1] + vy * lead_t
        return aim_x, aim_y

    def _encode_situation(self, dist, survival, los_ok, winning, losing,
                          toward_me, player_spd, shot_eff, danger_here):
        def b(v, lo=0.0, hi=1.0):
            return int(max(0, min(255, (v - lo) / (hi - lo + 1e-9) * 255)))
        p = self._p()
        return bytes([
            b(dist,          0, 250),
            b(survival),
            b(float(los_ok)),
            b(float(winning)),
            b(float(losing)),
            b(toward_me,    -1, 1),
            b(player_spd,    0, 200),
            b(shot_eff),
            b(danger_here,   0, 100),
            b(self._player_ax, -500, 500),
            b(self._player_ay, -500, 500),
            b(float(self.state in ("RETREAT","COVER","SEARCH"))),
        ])

    def _ctx_vector(self, dist, survival, los_ok, winning, losing):
        return (
            min(1.0, dist / 200.0),
            survival,
            float(los_ok),
            float(winning),
            float(losing),
        )

    def _episodic_similarity(self, v1, v2):
        d = math.sqrt(sum((a-b)**2 for a,b in zip(v1,v2)))
        return max(0.0, 1.0 - d / 2.0)

    def _compute_drives(self, dist, survival, los_ok, winning, losing,
                        toward_me, player_spd, death_risk):
        p = self._p()
        fear = (
            (1.0 - survival) * 0.45 +
            min(1.0, self._t_received / 5.0) * 0.30 +
            death_risk * 0.25
        )
        if toward_me > 0.5 and player_spd > 60:
            fear = min(1.0, fear * 1.3)

        aggression = (
            (survival * 0.40) +
            (float(winning) * 0.35) +
            (float(los_ok and dist < p["atk_r"]) * 0.25)
        )
        if self._t_received >= 3:
            aggression *= 0.6

        curiosity = (
            (float(not los_ok) * 0.50) +
            (float(not winning and not losing) * 0.30) +
            (min(1.0, dist / 200.0) * 0.20)
        )

        shot_eff = self._t_hits / max(self._t_shots, 1)
        caution = (
            (float(dist > 130) * 0.40) +
            (float(shot_eff < 0.25 and self._t_shots >= 4) * 0.35) +
            ((1.0 - survival) * 0.25)
        )

        prey_drive = (
            float(toward_me < -0.4 and player_spd > 40) * 0.50 +
            float(winning and survival > 0.60) * 0.30 +
            float(dist < 160) * 0.20
        )

        return {
            "fear":      min(1.0, max(0.0, fear)),
            "aggression":min(1.0, max(0.0, aggression)),
            "curiosity": min(1.0, max(0.0, curiosity)),
            "caution":   min(1.0, max(0.0, caution)),
            "prey":      min(1.0, max(0.0, prey_drive)),
        }

    def _drives_to_tactic(self, drives, dist, survival, los_ok, death_risk):
        p = self._p()
        if drives["fear"] > 0.72 or death_risk > 0.75:
            if dist > 130 and los_ok:   return "sniper",   "MIEDO→sniper distancia"
            if survival < 0.22:         return "defensive", "MIEDO→defensive HP crítico"
            return "flanker", "MIEDO→flanker buscar cover"
        if drives["prey"] > 0.68 and drives["fear"] < 0.35:
            return "berserker", "PRESA→berserker presión"
        if drives["aggression"] > 0.65 and drives["fear"] < 0.40:
            if dist < 90:  return "aggressive", "AGRESIÓN→aggressive close"
            if dist < 140: return "RAID",  "AGRESIÓN→RAID hit-run"
            return "aggressive", "AGRESIÓN→aggressive"
        if drives["caution"] > 0.60 and drives["aggression"] < 0.45:
            if dist > 120: return "sniper",    "CAUTELA→sniper"
            return "defensive", "CAUTELA→defensive"
        if drives["curiosity"] > 0.58 and not los_ok:
            return "flanker", "CURIOSIDAD→flanker sin LOS"
        return "balanced", "EQUILIBRIO→balanced"

    def _recall_ltm(self, pattern_bytes, survival):
        if not NEURON_OK or not self.engine: return None, 0.0
        try:
            pool = self.engine.pattern_pool.pool
            if not pool: return None, 0.0
            best_sim  = 0.0
            best_tac  = None
            current_ep = __import__('neuron657_v13', fromlist=['EnhancedPattern']).EnhancedPattern \
                         if NEURON_OK else None
            if current_ep is None: return None, 0.0
            cur_pat = current_ep(data=pattern_bytes,
                                 tags=[self.tactic, self.state,
                                       f"hp{int(survival*10)}"])
            for ph, entry in list(pool.items())[-80:]:
                stored = entry.get("pattern")
                if stored is None: continue
                try:
                    sim = cur_pat.similarity(stored)
                    if sim > best_sim and sim > 0.72:
                        best_sim = sim
                        tags = getattr(stored, 'tags', [])
                        tac_tags = [t for t in tags if t in self.TACTICS]
                        if tac_tags:
                            best_tac = tac_tags[0]
                except Exception:
                    continue
            if best_tac:
                return best_tac, best_sim
        except Exception:
            pass
        return None, 0.0

    def _store_ltm(self, pattern_bytes, tactic, score, survival):
        if not NEURON_OK or not self.engine: return
        if abs(score - 0.5) < 0.10: return
        try:
            ep_cls = __import__('neuron657_v13', fromlist=['EnhancedPattern']).EnhancedPattern
            pat = ep_cls(
                data=pattern_bytes,
                tags=[tactic, self.state,
                      f"hp{int(survival*10)}",
                      "win" if score > 0.6 else "loss"],
                modality="combat"
            )
            ph = pat.hash()
            self.engine.pattern_pool._add_to_pool(ph, pat, __import__('time').time())
        except Exception:
            pass

    def _update_fatigue(self, dt, in_combat):
        if in_combat:
            self._fatigue_t += dt
            self._fatigue = min(1.0, self._fatigue + dt * 0.008)
        else:
            self._fatigue = max(0.0, self._fatigue - dt * 0.004)
        N657_NPC._fatigue_class = max(0.0, N657_NPC._fatigue_class - dt * 0.001)

    def _fatigue_penalty(self):
        fat = min(1.0, self._fatigue + N657_NPC._fatigue_class * 0.3)
        return {
            "accuracy":  1.0 - fat * 0.35,
            "speed":     1.0 - fat * 0.20,
            "eval_rate": 1.0 + fat * 0.50,
            "fear_amp":  1.0 + fat * 0.40,
        }

    def _update_player_profile(self, dt, dist, player_spd, toward_me, shot_eff):
        self._profile_t += dt
        if self._profile_t < 2.0: return
        self._profile_t = 0.0
        p = N657_NPC._shared_player_profile
        α = 0.15
        p["aggression"]  = p.get("aggression", 0.5) * (1-α) + float(toward_me > 0.4) * α
        p["mobility"]    = p.get("mobility",   0.5) * (1-α) + min(1.0, player_spd/120) * α
        p["precision"]   = p.get("precision",  0.5) * (1-α) + shot_eff * α
        p["close_pref"]  = p.get("close_pref", 0.5) * (1-α) + float(dist < 100) * α
        p["samples"]     = p.get("samples", 0) + 1

    def _profile_counter_tactic(self):
        p = N657_NPC._shared_player_profile
        if p.get("samples", 0) < 5: return None
        aggr  = p.get("aggression", 0.5)
        prec  = p.get("precision",  0.5)
        close = p.get("close_pref", 0.5)
        mob   = p.get("mobility",   0.5)
        if aggr > 0.65 and close > 0.60:
            return "sniper"
        if prec > 0.60 and mob < 0.40:
            return "flanker"
        if mob > 0.70 and aggr < 0.40:
            return "RAID"
        if prec < 0.25 and aggr < 0.40:
            return "aggressive"
        return None

    def _find_dynamic_cover(self, player_x, player_y):
        best_pos = None; best_score = -9999.0
        npc_r, npc_c = w2c(self.x, self.y)
        for r in range(max(0, npc_r-4), min(GROWS, npc_r+5)):
            for c in range(max(0, npc_c-4), min(GCOLS, npc_c+5)):
                if ARENA_MAP[r][c]: continue
                cx2, cy2 = cc(r, c)
                dist_me = math.hypot(cx2 - self.x, cy2 - self.y)
                if dist_me > CELL * 5: continue
                breaks_los = not has_los(cx2, cy2, player_x, player_y)
                near_wall = any(
                    ARENA_MAP[r+dr][c+dc]
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                    if 0<=r+dr<GROWS and 0<=c+dc<GCOLS
                )
                danger = (self._danger_map.get((r,c), 0) +
                          N657_NPC._shared_danger.get((r,c), 0) * 0.4)
                dist_player = math.hypot(cx2 - player_x, cy2 - player_y)
                score = (
                    float(breaks_los) * 60.0 +
                    float(near_wall)  * 25.0 -
                    danger            *  0.5 -
                    dist_me           *  0.08 +
                    max(0, 180 - dist_player) * 0.10
                )
                if score > best_score:
                    best_score = score
                    best_pos = (cx2, cy2)
        self._cover_pos = best_pos
        self._cover_quality = min(1.0, max(0.0, best_score / 100.0))

    def _update_suppression(self, dt, dist, los_ok, player_spd):
        self._suppress_t = max(0.0, self._suppress_t - dt)
        p_profile = N657_NPC._shared_player_profile
        mob = p_profile.get("mobility", 0.5)
        prec = p_profile.get("precision", 0.5)
        if (self._suppress_t <= 0 and
                mob < 0.35 and prec > 0.50 and
                self._t_shots >= 3 and self._t_hits == 0 and
                los_ok and dist < 180):
            self._suppress_t = random.uniform(0.8, 1.8)
            self._log(f"SUPRESIÓN: silencio {self._suppress_t:.1f}s")

    @property
    def _is_suppressing(self):
        return self._suppress_t > 0

    @classmethod
    def _load_ltm_once(cls):
        if getattr(cls, '_ltm_loaded', False): return
        cls._ltm_loaded = True
        try:
            import json
            with open(cls._ltm_file, 'r') as f:
                data = json.load(f)
            loaded = data.get("episodic", [])
            valid = [m for m in loaded
                     if isinstance(m, dict) and "ctx" in m and "tactic" in m]
            if valid:
                cls._episodic_memory = valid[-400:]
                cls._best_tactic = data.get("best_tactic")
                cls._round_count = data.get("round_count", 0)
                cls._shared_player_profile = data.get("player_profile", {})
                print(f"[INFO] LTM cargada: {len(cls._episodic_memory)} episodios, "
                      f"mejor táctica={cls._best_tactic}")
        except (FileNotFoundError, Exception):
            pass

    @classmethod
    def save_ltm(cls):
        try:
            import json
            data = {
                "episodic":       cls._episodic_memory[-400:],
                "best_tactic":    cls._best_tactic,
                "round_count":    cls._round_count,
                "player_profile": cls._shared_player_profile,
                "version":        "3.0",
            }
            with open(cls._ltm_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WARN] Error guardando LTM: {e}")

    def _move_to_cover(self, player_x, player_y, p, dt):
        if not self._cover_pos: return
        tx, ty = self._cover_pos
        dist_cover = math.hypot(tx - self.x, ty - self.y)
        if dist_cover < CELL * 0.8:
            self._cover_pos = None
            return
        sr, sc = w2c(self.x, self.y)
        tr, tc = w2c(tx, ty)
        try:
            nr, nc = bfs(sr, sc, tr, tc)
            nx_t, ny_t = cc(nr, nc)
            dx = nx_t - self.x; dy = ny_t - self.y
            ln = math.hypot(dx, dy) or 1
            spd = p["speed"] * 0.90
            nx = self.x + (dx/ln)*spd*dt
            ny = self.y + (dy/ln)*spd*dt
            if not iwall(nx, self.y): self.x = max(9, min(AW-9, nx))
            if not iwall(self.x, ny): self.y = max(9, min(AH-9, ny))
        except Exception: pass

    def _evaluate(self, dist, toward_me=0, player_spd=0):
        survival  = self.hp / self.MAX_HP
        los_ok    = has_los(self.x, self.y,
                            getattr(self,'_last_px', self.x),
                            getattr(self,'_last_py', self.y))
        shot_eff  = self._t_hits / max(self._t_shots, 1)
        cur_r, cur_c = w2c(self.x, self.y)
        danger_here  = (self._danger_map.get((cur_r, cur_c), 0) +
                        N657_NPC._shared_danger.get((cur_r, cur_c), 0) * 0.3)

        dmg_dealt  = self._t_hits * 10
        dmg_taken  = self._t_received * 15
        net_score  = dmg_dealt - dmg_taken
        winning    = (net_score > 10 and self._t_hits >= 2)
        losing     = (net_score < -15 or (self._t_received >= 3 and self._t_hits == 0))

        composite_score = min(1.0, max(0.0, (
            0.35 * max(0, net_score / 30) +
            0.30 * survival +
            0.20 * shot_eff +
            0.15 * max(0, 1.0 - danger_here / 60.0)
        )))

        regen_this = max(0, self._no_hit_t - 2.0) * self._regen_rate
        prev_regen = self._tactic_regen.get(self.tactic, 2.0)
        self._tactic_regen[self.tactic] = prev_regen * 0.7 + regen_this * 0.3
        if self._tactic_regen:
            best_regen = max(self._tactic_regen.values())
            self._regen_rate = min(3.5, max(1.5, best_regen * 0.4 + 2.0 * 0.6))

        hp_factor    = (1.0 - survival) ** 1.4
        hit_factor   = min(1.0, self._t_received / 4.0)
        dist_factor  = max(0.0, 1.0 - dist / 160.0)
        los_factor   = float(not los_ok) * 0.15
        no_cover     = float(self._cover_pos is None and self.state not in ("COVER","RETREAT")) * 0.10
        death_risk = min(1.0, (
            hp_factor   * 0.50 +
            hit_factor  * 0.30 +
            dist_factor * 0.12 +
            los_factor  +
            no_cover
        ))
        self._death_risk = death_risk

        pattern_bytes = self._encode_situation(
            dist, survival, los_ok, winning, losing,
            toward_me, player_spd, shot_eff, danger_here
        )

        drives = self._compute_drives(
            dist, survival, los_ok, winning, losing,
            toward_me, player_spd, death_risk
        )
        self._drives = drives

        drives_with_survival = dict(drives)
        drives_with_survival['survival'] = survival
        self.attention.update(drives_with_survival, self.world_model, self._eval_t or 0.033)

        # ══ NUEVO: llamada al motor cognitivo con planificación por energía libre ══
        motor_tactic = None   # <--- INICIALIZAR AQUÍ
        self._engine_eval_cd += self._eval_t or 0.033
        if self.engine and self._engine_eval_cd >= 0.5:   # cada 0.5 segundos
            self._engine_eval_cd = 0.0
            try:
                # Construir contexto rico para el motor
                ctx_motor = {
                    "pattern_size": int(dist),
                    "pattern_tags": [
                        self.state,
                        self.tactic,
                        "win" if winning else "lose" if losing else "neutral",
                        f"fear_{int(drives['fear']*10)}",
                        f"aggr_{int(drives['aggression']*10)}",
                        f"hp_{int(survival*10)}",
                        "los" if los_ok else "nolos",
                    ],
                    "memory_pressure": 1.0 - survival,
                    "error_rate": min(1.0, self._t_received / 5.0),
                    "free_energy": getattr(self.engine.energy_manager, 'current_free_energy', 0.0),
                }
                
                # ✅ FIX MEJORA: Actualizar beliefs en world_model antes de process_input
                if self.engine and hasattr(self.engine, 'world_model'):
                    try:
                        # Belief sobre visibilidad del jugador
                        self.engine.world_model.update_belief(
                            "player_visible",
                            los_ok,
                            confidence=0.95 if los_ok else 0.7
                        )
                        
                        # Belief sobre distancia al jugador
                        self.engine.world_model.update_belief(
                            "player_distance",
                            dist,
                            confidence=0.9 if los_ok else 0.5
                        )
                        
                        # Belief sobre salud propia
                        self.engine.world_model.update_belief(
                            "own_health",
                            survival,
                            confidence=1.0
                        )
                        
                        # Belief sobre threat level
                        threat = (1.0 - survival) * (dist / 50.0) if dist > 0 else 0
                        self.engine.world_model.update_belief(
                            "threat_level",
                            threat,
                            confidence=0.85
                        )
                        
                        # Belief sobre ammunition
                        if hasattr(self, 'ammo'):
                            ammo_availability = self.ammo / 30.0
                            self.engine.world_model.update_belief(
                                "ammo_available",
                                ammo_availability,
                                confidence=1.0
                            )
                    
                    except Exception as be:
                        self._log(f"[WARN] Error actualizando beliefs: {be}")
                
                # Llamar a process_input para obtener una estrategia cognitiva completa
                result = self.engine.process_input(
                    input_data={"type": "npc_perception", "data": ctx_motor},
                    context=ctx_motor
                )
                if result.get("ok", False):
                    strat = result.get("strategy", "hybrid")
                    confidence = result.get('confidence', 0.0)
                    
                    # ✅ FIX MEJORA: Logging detallado
                    self._log(
                        f"MOTOR: strat={strat} conf={confidence:.1%} "
                        f"mode={result.get('mode', '?')[:4]}"
                    )
                    
                    # Mapeo estrategia → táctica
                    strat_map = {
                        "byte":     "defensive",
                        "hdv":      "flanker",
                        "semantic": "balanced",
                        "hybrid":   "RAID",
                    }
                    motor_tactic = strat_map.get(strat, "balanced")
            except Exception as e:
                # ✅ FIX MEJORA: Logging de error (no silent failure)
                self._log(f"[DEBUG] Motor cognitive falló: {str(e)[:50]}")
                # Si falla, simplemente no hay voto del motor (graceful degradation)
                pass

        if not hasattr(self, '_plan_cooldown'): self._plan_cooldown = 0.0
        self._plan_cooldown = max(0.0, self._plan_cooldown - (self._eval_t or 0.033))

        needs_new_plan = (
            self.planner.active_plan is None and
            self._plan_cooldown <= 0.0 and
            (
                drives["fear"] > 0.60 or
                (drives["aggression"] > 0.70 and self.world_model.player_confidence > 0.5) or
                (drives["curiosity"] > 0.55 and not los_ok)
            )
        )
        if needs_new_plan:
            generated = self.planner.generate_plan(self.world_model, drives, self.TACTICS)
            if generated:
                self._plan_cooldown = 2.0
                self._log(f"PLAN generado: {len(self.planner.active_plan)} pasos "
                          f"[F{drives['fear']:.1f} A{drives['aggression']:.1f}]")

        next_tactic_from_plan = self.planner.update(self._eval_t or 0.033, self.world_model, drives)
        if next_tactic_from_plan is not None:
            candidate = next_tactic_from_plan
            why_plan = f"PLAN({candidate})"
            old_t = self.tactic
            if candidate != self.tactic:
                self.tactic = candidate
                self._prev_tactic = old_t; self._tactic_flash = 0.6
                self._t_shots = 0; self._t_hits = 0; self._t_received = 0
                self._log(f"BIO {old_t.upper()}→{candidate.upper()} | {why_plan}")
            else:
                self._t_shots = 0; self._t_hits = 0; self._t_received = 0
                self._log(f"BIO Mantiene {self.tactic.upper()} (plan)")
            return

        drive_candidate, drive_why = self._drives_to_tactic(
            drives, dist, survival, los_ok, death_risk
        )

        ltm_candidate, ltm_conf = self._recall_ltm(pattern_bytes, survival)

        ctx_vec = self._ctx_vector(dist, survival, los_ok, winning, losing)
        episodic_candidate = None; episodic_score = -1.0
        if N657_NPC._episodic_memory:
            tac_scores = {}
            for mem in N657_NPC._episodic_memory[-200:]:
                sim = self._episodic_similarity(ctx_vec, mem["ctx"])
                if sim < 0.60: continue
                t = mem["tactic"]; sc = mem["score"] * sim
                tac_scores.setdefault(t, []).append(sc)
            if tac_scores:
                avg = {t: sum(v)/len(v) for t, v in tac_scores.items()}
                best_t = max(avg, key=avg.get)
                if avg[best_t] > 0.40:
                    episodic_candidate = best_t
                    episodic_score = avg[best_t]

        meta_candidate = None
        if self.engine and NEURON_OK:
            try:
                self.engine.meta_learner.record_performance(
                    strategy=self.tactic,
                    context={
                        "mode":      self.n_mode,
                        "dist":      int(dist // 50),
                        "hp":        int(survival * 10),
                        "has_los":   int(los_ok),
                        "fear":      round(drives["fear"], 1),
                        "aggression":round(drives["aggression"], 1),
                    },
                    performance={
                        "success":  composite_score > 0.50,
                        "duration": 4.0,
                        "score":    composite_score,
                        "decision_class": (
                            "CONFIDENT" if composite_score > 0.70 else
                            "WEAK_MATCH" if composite_score > 0.45 else "FAILURE"
                        )
                    }
                )
                self.engine.metrics.update(
                    avg_confidence=composite_score,
                    error_rate_1min=min(1.0, self._t_received / 5.0),
                    stm_utilization=1.0 - survival,
                    cache_hit_rate=shot_eff
                )

                if death_risk > 0.75 or survival < 0.20:
                    self.engine.state_manager.transition(
                        reason="death_risk_critical", mode=CognitiveMode.SAFE_RECOVERY)
                elif drives["aggression"] > 0.65 and survival > 0.55:
                    self.engine.state_manager.transition(
                        reason="high_aggression", mode=CognitiveMode.ADAPTIVE)
                elif drives["fear"] > 0.55 or losing:
                    self.engine.state_manager.transition(
                        reason="fear_adapt", mode=CognitiveMode.REASONING)
                elif self.npc_shots >= 8:
                    self.engine.state_manager.transition(
                        reason="enough_data", mode=CognitiveMode.META_LEARNING)

                dec = self.engine.state_manager.decide_cognitive_strategy({
                    "pattern_size": int(dist),
                    "pattern_tags": [
                        self.state, self.tactic,
                        "win" if winning else "lose" if losing else "neutral",
                        f"fear_{int(drives['fear']*10)}",
                        f"aggr_{int(drives['aggression']*10)}",
                    ],
                })
                self.n_mode  = dec["mode"]
                self.n_strat = dec["strategy"]
                self.n_conf  = dec["confidence"]

                strat_map = {
                    "byte":     "defensive",
                    "hdv":      "flanker",
                    "semantic": "balanced",
                    "hybrid":   "RAID",
                }
                meta_candidate = strat_map.get(self.n_strat)

            except Exception as e:
                self.n_mode = "autonomous"; self.n_strat = "hybrid"; self.n_conf = 0.75

        else:
            if death_risk > 0.75:          self.n_mode = "safe_recovery"
            elif drives["aggression"]>0.65: self.n_mode = "adaptive"
            elif drives["fear"] > 0.55:     self.n_mode = "reasoning"
            else:                           self.n_mode = "autonomous"

        # ══ VOTACIÓN PONDERADA (incluye el voto del motor si existe) ══
        votes = {}

        def add_vote(tactic, weight, confidence=1.0):
            if tactic and tactic in self.TACTICS:
                votes[tactic] = votes.get(tactic, 0.0) + weight * confidence

        # Pesos ajustados para dar más relevancia al motor cognitivo
        add_vote(drive_candidate,    0.38, 1.0)          # 38% impulsos
        add_vote(ltm_candidate,      0.20, ltm_conf)     # 20% LTM
        add_vote(episodic_candidate, 0.14, min(1.0, episodic_score + 0.3))  # 14% episódica
        if motor_tactic:   # voto del motor (28%)
            add_vote(motor_tactic, 0.28, self.n_conf)
        add_vote(meta_candidate,     0.12, self.n_conf)  # 12% meta (coincide con motor a veces)
        profile_candidate = self._profile_counter_tactic()
        add_vote(profile_candidate,  0.08, 1.0)          # 8% perfil

        votes = self.attention.apply_to_votes(votes, drives)

        if votes:
            best_voted = max(votes, key=votes.get)
            best_score = votes[best_voted]
        else:
            best_voted = drive_candidate or "balanced"
            best_score = 0.40

        hp_critical_explore = survival < 0.22
        danger_blocks_explore = death_risk > 0.55
        if not hp_critical_explore and not danger_blocks_explore:
            epsilon = 0.04 + drives.get("curiosity", 0) * 0.12
            if random.random() < epsilon:
                alt_tactics = [t for t in self.TACTICS if t != best_voted]
                explored = random.choice(alt_tactics)
                self._log(f"EXPLORA ε={epsilon:.2f} {best_voted.upper()}→{explored.upper()}")
                best_voted = explored
                best_score = votes.get(best_voted, 0.20)

        # Overrides de emergencia
        override = None; override_why = ""
        hp_critical   = survival < 0.22
        no_los        = not los_ok
        shooting_blind= (self._t_shots >= 4 and self._t_hits == 0)
        player_charging=(toward_me > 0.6 and player_spd > 40)

        if hp_critical and best_voted not in ("defensive","sniper","flanker"):
            override = "sniper" if dist > 130 else "defensive"
            override_why = f"REFLEJO-HP ({self.hp:.0f})"
        elif death_risk > 0.80 and survival < 0.30:
            override = "defensive"
            override_why = f"REFLEJO-MUERTE risk={death_risk:.2f}"
        elif shooting_blind or (no_los and best_voted in ("aggressive","berserker")):
            override = "flanker"
            override_why = "REFLEJO-CIEGO"
        elif player_charging and survival > 0.45 and best_voted == "defensive":
            override = "flanker"
            override_why = "REFLEJO-CONTRAATAQUE"

        candidate   = override if override else best_voted
        why_sources = []
        if override:                  why_sources.append(override_why)
        if not override:              why_sources.append(f"drive={drive_why}")
        if ltm_candidate:             why_sources.append(f"LTM={ltm_candidate}({ltm_conf:.2f})")
        if episodic_candidate:        why_sources.append(f"epi={episodic_candidate}({episodic_score:.2f})")
        if meta_candidate:            why_sources.append(f"meta={meta_candidate}")
        if profile_candidate:         why_sources.append(f"perfil={profile_candidate}")
        if motor_tactic:               why_sources.append(f"motor={motor_tactic}")
        why = " | ".join(why_sources)

        old_t = self.tactic
        needs_change = (
            candidate != self.tactic and (
                self._t_shots >= 3 or hp_critical or
                losing or shooting_blind or override is not None
            )
        )
        if needs_change:
            self.tactic = candidate
            self._prev_tactic = old_t; self._tactic_flash = 0.6
            self._t_shots = 0; self._t_hits = 0; self._t_received = 0
            self._log(f"BIO {old_t.upper()}→{candidate.upper()} | {why} [{self.n_mode[:8]}]")
        else:
            self._t_shots = 0; self._t_hits = 0; self._t_received = 0
            impulse_str = (f"F{drives['fear']:.1f} "
                           f"A{drives['aggression']:.1f} "
                           f"P{drives['prey']:.1f}")
            self._log(f"BIO Mantiene {self.tactic.upper()} [{impulse_str}] "
                      f"risk={death_risk:.2f} [{self.n_mode[:8]}]")

        # Consolidar memoria
        N657_NPC._episodic_memory.append({
            "ctx":    ctx_vec,
            "tactic": self.tactic,
            "score":  composite_score,
            "round":  N657_NPC._round_count,
        })
        if len(N657_NPC._episodic_memory) > 500:
            N657_NPC._episodic_memory = N657_NPC._episodic_memory[-400:]

        self._store_ltm(pattern_bytes, self.tactic, composite_score, survival)

    def _post_retreat(self,dist):
        survival=self.hp/self.MAX_HP
        los_ok=has_los(self.x,self.y,
                       getattr(self,'_last_px',self.x),
                       getattr(self,'_last_py',self.y))
        mem_suggestion=None
        if N657_NPC._round_memory and len(N657_NPC._round_memory)>=2:
            hp_bucket=0 if survival<0.40 else (1 if survival<0.70 else 2)
            tac_scores={}
            for t,hg,hr,sv,_ in N657_NPC._round_memory:
                sv_bucket=0 if sv<0.40 else (1 if sv<0.70 else 2)
                if sv_bucket!=hp_bucket: continue
                sc=(hg*2-hr)/max(hg+hr,1)
                tac_scores.setdefault(t,[]).append(sc)
            if tac_scores:
                avg={t:sum(v)/len(v) for t,v in tac_scores.items()}
                best=max(avg,key=avg.get)
                if avg[best]>0.1 and best not in ("flanker","berserker"):
                    mem_suggestion=best

        if survival<0.20:
            new_t="sniper" if dist>130 else "defensive"
            why=f"HP={self.hp} (<20%) → {new_t} sobrevivir"
        elif survival<0.45 and not los_ok:
            new_t="flanker"; why=f"HP={self.hp} sin LOS → flanker"
        elif survival<0.45 and dist>120:
            new_t="sniper"; why=f"HP={self.hp} dist={dist:.0f}px → sniper"
        elif survival<0.45:
            new_t="balanced"; why=f"HP={self.hp} cerca → balanced"
        elif survival>=0.70:
            new_t="RAID" if dist<130 else "flanker"
            why=f"HP={self.hp} ({survival:.0%}) → {new_t} CONTRAATAQUE"
        else:
            new_t=self.tactic; why=f"HP={self.hp} ({survival:.0%}) — mantiene {self.tactic}"

        if mem_suggestion and mem_suggestion!=new_t and survival>0.30:
            why=f"MEM→{mem_suggestion.upper()} | "+why; new_t=mem_suggestion

        if new_t!=self.tactic:
            self._prev_tactic=self.tactic; self._tactic_flash=0.5
            self.tactic=new_t
            self._t_shots=0; self._t_hits=0; self._t_received=0
        self._t_received=0
        self._log(f"Post-retreat: {why} [{self.n_mode[:8]}]")
        if dist<50:
            self._ret_t=1.8; self._log(f"Post-retreat extendido — jugador a {dist:.0f}px")
        elif dist<self.DETECT:
            if self.hits_received>3 and self.hp<self.MAX_HP*0.6:
                self.state="COVER"
            else:
                self.state="CHASE"
        else:
            self.state="PATROL"

    def _safe_retreat_point(self):
        px=getattr(self,'_last_px',self.x); py=getattr(self,'_last_py',self.y)
        survival=self.hp/self.MAX_HP
        esc=get_escape_map()
        best=None; best_score=-9999
        panic=survival<0.20
        threat_angle=math.atan2(self.y-py,self.x-px) % (2*math.pi)
        for (r,c),esc_s in esc.items():
            tx,ty=cc(r,c)
            danger=self._danger_map.get((r,c),0)+N657_NPC._shared_danger.get((r,c),0)*0.3
            dir_d=self._directional_danger(r,c,threat_angle)
            if danger>80 and not panic: continue
            dist_player=math.hypot(tx-px,ty-py)
            dist_self=math.hypot(tx-self.x,ty-self.y)
            cover=not has_los(tx,ty,px,py)
            if panic:
                score=(50 if cover else 0)-dist_self*0.8+esc_s*0.2
            else:
                score=(dist_player*0.45+esc_s*0.30+(45 if cover else 0)
                       -danger*1.8-dist_self*0.08-dir_d*0.5)
            if score>best_score:
                best_score=score; best=(tx,ty)
        return best or self.PATROL_PTS[0]

    def _log(self,reason):
        self.last_dec=reason
        self.decision_log.appendleft({"mode":self.n_mode,"tactic":self.tactic,"reason":reason})

    def _move(self,player,dt,p):
        sr,sc=w2c(self.x,self.y)
        dist=math.hypot(player.x-self.x,player.y-self.y)

        if self.state=="PATROL":
            tx,ty=self.PATROL_PTS[self._pidx]
            if math.hypot(tx-self.x,ty-self.y)<12: self._pidx=(self._pidx+1)%4
            nr,nc2=bfs(sr,sc,*w2c(tx,ty))
            dx,dy=cc(nr,nc2)[0]-self.x,cc(nr,nc2)[1]-self.y; spd=p["speed"]*0.55

        elif self.state=="SEARCH":
            if (not self._search_spiral or
                    self._search_idx>=len(self._search_spiral)):
                dx,dy=0,0; spd=0
            else:
                tx,ty=self._search_spiral[self._search_idx]
                if math.hypot(self.x-tx,self.y-ty)<18:
                    self._search_idx+=1
                    if self._search_idx>=len(self._search_spiral):
                        dx,dy=0,0; spd=0
                    else:
                        tx,ty=self._search_spiral[self._search_idx]
                        nr,nc2=bfs(sr,sc,*w2c(tx,ty))
                        dx,dy=cc(nr,nc2)[0]-self.x,cc(nr,nc2)[1]-self.y; spd=p["speed"]*0.75
                else:
                    nr,nc2=bfs(sr,sc,*w2c(tx,ty))
                    dx,dy=cc(nr,nc2)[0]-self.x,cc(nr,nc2)[1]-self.y; spd=p["speed"]*0.75

        elif self.state=="AMBUSH":
            if self._ambush_pos is None:
                ap=self._find_ambush_point(player)
                if ap: self._ambush_pos=ap
                else: self.state="CHASE"; dx,dy=player.x-self.x,player.y-self.y; spd=p["speed"]
                return
            ax,ay=self._ambush_pos
            if math.hypot(self.x-ax,self.y-ay)<18:
                dx,dy=0,0; spd=0
            else:
                nr,nc2=bfs(sr,sc,*w2c(ax,ay))
                dx,dy=cc(nr,nc2)[0]-self.x,cc(nr,nc2)[1]-self.y; spd=p["speed"]*0.9

        elif self.state=="CHASE":
            nr,nc=bfs(sr,sc,*w2c(player.x,player.y))
            dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=p["speed"]

        elif self.state=="STRAFE":
            if self._strafe_t<=0:
                px2,py2=player.x-self.x,player.y-self.y; ln_t=math.hypot(px2,py2) or 1
                test1_x=self.x+(-py2/ln_t)*20; test1_y=self.y+(px2/ln_t)*20
                test2_x=self.x+(py2/ln_t)*20;  test2_y=self.y+(-px2/ln_t)*20
                los1=has_los(test1_x,test1_y,player.x,player.y)
                los2=has_los(test2_x,test2_y,player.x,player.y)
                if not los1 and los2: self._strafe_dir=1
                elif not los2 and los1: self._strafe_dir=-1
                else: self._strafe_dir*=-1
                self._strafe_t=random.uniform(1.2,2.5)
            px,py=player.x-self.x,player.y-self.y; ln=math.hypot(px,py) or 1
            dx=(-py/ln)*self._strafe_dir+(px/ln)*0.2
            dy=(px/ln)*self._strafe_dir+(py/ln)*0.2
            spd=p["speed"]*0.80

        elif self.state=="FLANK":
            self._flank_angle+=dt*1.5*self._strafe_dir
            if not hasattr(self,'_flank_stuck_t'): self._flank_stuck_t=0.0; self._flank_stuck_ref=(self.x,self.y)
            flank_moved=math.hypot(self.x-self._flank_stuck_ref[0],self.y-self._flank_stuck_ref[1])
            if flank_moved>15: self._flank_stuck_t=0.0; self._flank_stuck_ref=(self.x,self.y)
            else: self._flank_stuck_t+=dt
            if self._flank_stuck_t>2.0:
                self._flank_stuck_t=0.0; self._strafe_dir*=-1
                self.state="CHASE"; dx,dy=player.x-self.x,player.y-self.y; spd=p["speed"]
            else:
                best_angle=None
                for da in [0,-0.3,0.3,-0.6,0.6,-1.0,1.0,-1.6,1.6,math.pi]:
                    a=self._flank_angle+da
                    tx2=player.x+math.cos(a)*p["atk_r"]*0.7
                    ty2=player.y+math.sin(a)*p["atk_r"]*0.7
                    tx2=max(CELL,min(AW-CELL,tx2)); ty2=max(CELL,min(AH-CELL,ty2))
                    tr2,tc2=w2c(tx2,ty2)
                    if 0<=tr2<GROWS and 0<=tc2<GCOLS and not ARENA_MAP[tr2][tc2]:
                        best_angle=a; break
                if best_angle is None: best_angle=self._flank_angle
                tx2=player.x+math.cos(best_angle)*p["atk_r"]*0.7
                ty2=player.y+math.sin(best_angle)*p["atk_r"]*0.7
                tx2=max(CELL,min(AW-CELL,tx2)); ty2=max(CELL,min(AH-CELL,ty2))
                nr,nc=bfs(sr,sc,*w2c(tx2,ty2))
                cx_f,cy_f=cc(nr,nc)
                dx,dy=cx_f-self.x,cy_f-self.y
                if math.hypot(dx,dy)<CELL*0.7:
                    self._flank_angle+=0.5*self._strafe_dir
                    dx=math.cos(self._flank_angle)*self._strafe_dir
                    dy=math.sin(self._flank_angle)*self._strafe_dir
                spd=p["speed"]*0.88

        elif self.state=="ATTACK":
            dx,dy=player.x-self.x,player.y-self.y; spd=p["speed"]*0.6

        elif self.state=="KITE":
            px,py=player.x-self.x,player.y-self.y; ln=math.hypot(px,py) or 1
            dx=(-px/ln)+math.sin(self._flank_angle)*0.4
            dy=(-py/ln)+math.cos(self._flank_angle)*0.4
            self._flank_angle+=dt*2.0; spd=p["speed"]*0.9

        elif self.state=="RETREAT":
            if self._retreat_target:
                tx,ty=self._retreat_target
                if math.hypot(self.x-tx,self.y-ty)<20:
                    self._retreat_target=None
                    self._retreat_arrived=True
                    dx,dy=0,0; spd=0
                else:
                    nr,nc=bfs(sr,sc,*w2c(tx,ty))
                    bfs_x,bfs_y=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y
                    bfs_l=math.hypot(bfs_x,bfs_y) or 1
                    away_x,away_y=self.x-player.x,self.y-player.y
                    away_l=math.hypot(away_x,away_y) or 1
                    dx=0.5*(away_x/away_l)+0.5*(bfs_x/bfs_l)
                    dy=0.5*(away_y/away_l)+0.5*(bfs_y/bfs_l)
                    spd=p["speed"]*1.05
            else:
                away_x,away_y=self.x-player.x,self.y-player.y; away_l=math.hypot(away_x,away_y) or 1
                far=max(self.PATROL_PTS,key=lambda pt2:math.hypot(pt2[0]-player.x,pt2[1]-player.y))
                nr,nc=bfs(sr,sc,*w2c(*far))
                bfs_x,bfs_y=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; bfs_l=math.hypot(bfs_x,bfs_y) or 1
                dx=0.6*(away_x/away_l)+0.4*(bfs_x/bfs_l)
                dy=0.6*(away_y/away_l)+0.4*(bfs_y/bfs_l)
                spd=p["speed"]*1.05

        elif self.state=="COVER":
            if not hasattr(self,'_cover_cell'): self._cover_cell=None
            if not hasattr(self,'_cover_timeout'): self._cover_timeout=0.0
            self._cover_timeout=max(0,self._cover_timeout-dt)
            if self._cover_pos and self._cover_quality>0.3:
                tx2,ty2=self._cover_pos
                if math.hypot(self.x-tx2,self.y-ty2)<CELL*0.8:
                    dx,dy=0,0
                else:
                    nr,nc2=bfs(sr,sc,*w2c(tx2,ty2))
                    dx,dy=cc(nr,nc2)[0]-self.x,cc(nr,nc2)[1]-self.y
            else:
                if self._cover_cell is None:
                    best_cover=None; best_sc=-9999
                    for cr2 in range(1,GROWS-1):
                        for cc3 in range(1,GCOLS-1):
                            if ARENA_MAP[cr2][cc3]==1: continue
                            cx2,cy2=cc(cr2,cc3)
                            if has_los(cx2,cy2,player.x,player.y): continue
                            d_me=math.hypot(cx2-self.x,cy2-self.y)
                            d_pl=math.hypot(cx2-player.x,cy2-player.y)
                            danger=self._danger_map.get((cr2,cc3),0)+N657_NPC._shared_danger.get((cr2,cc3),0)*0.3
                            to_dest_x=cx2-self.x; to_dest_y=cy2-self.y
                            to_plr_x=player.x-self.x; to_plr_y=player.y-self.y
                            ld=math.hypot(to_dest_x,to_dest_y) or 1; lp=math.hypot(to_plr_x,to_plr_y) or 1
                            dot=(to_dest_x/ld)*(to_plr_x/lp)+(to_dest_y/ld)*(to_plr_y/lp)
                            route_penalty=max(0,dot)*30
                            sc4=(d_pl*0.35-d_me*0.25-danger*0.5-route_penalty)
                            if sc4>best_sc: best_sc=sc4; best_cover=(cr2,cc3)
                    self._cover_cell=best_cover; self._cover_timeout=3.5
                if self._cover_cell:
                    nr,nc2=bfs(sr,sc,*self._cover_cell)
                    cx_t,cy_t=cc(nr,nc2); dx,dy=cx_t-self.x,cy_t-self.y
                    if math.hypot(dx,dy)<CELL*0.7: dx,dy=0,0
                else:
                    far=max(self.PATROL_PTS,key=lambda pt3:math.hypot(pt3[0]-player.x,pt3[1]-player.y))
                    nr,nc2=bfs(sr,sc,*w2c(*far)); dx,dy=cc(nr,nc2)[0]-self.x,cc(nr,nc2)[1]-self.y
            if self._cover_timeout<=0 and self._cover_quality<=0.3:
                self._cover_cell=None; self.state="CHASE"; dx,dy=player.x-self.x,player.y-self.y
            spd=p["speed"]*1.1

        elif self.state=="RAID":
            if self._RAID_phase=="hunt":
                nr,nc=bfs(sr,sc,*w2c(player.x,player.y))
                dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=p["speed"]*0.9
            elif self._RAID_phase=="burst":
                px2,py2=player.x-self.x,player.y-self.y; ln=math.hypot(px2,py2) or 1
                dx=(-py2/ln)*self._strafe_dir+(px2/ln)*0.15
                dy=(px2/ln)*self._strafe_dir+(py2/ln)*0.15; spd=p["speed"]*0.75
            elif self._RAID_phase=="retreat_micro":
                if self._retreat_target:
                    tx,ty=self._retreat_target
                    nr,nc=bfs(sr,sc,*w2c(tx,ty))
                    dx,dy=cc(nr,nc)[0]-self.x,cc(nr,nc)[1]-self.y; spd=p["speed"]*1.1
                else:
                    away_x,away_y=self.x-player.x,self.y-player.y
                    ln=math.hypot(away_x,away_y) or 1; dx,dy=away_x/ln,away_y/ln
                    spd=p["speed"]*1.1
        else:
            return

        if self.state not in ("AMBUSH","SEARCH") or True:
            try:
                ln=math.hypot(dx,dy) or 1
                if self.state=="RETREAT" and dist<30: spd=p["speed"]*1.6
                fat_spd=self._fatigue_penalty()["speed"]
                spd*=fat_spd
                nx=self.x+(dx/ln)*spd*dt; ny=self.y+(dy/ln)*spd*dt
                if not iwall(nx,self.y): self.x=max(9,min(AW-9,nx))
                if not iwall(self.x,ny): self.y=max(9,min(AH-9,ny))
            except Exception: pass

    def take_hit(self,d=15,from_x=None,from_y=None):
        self.hp=max(0,self.hp-d); self._hf=0.5
        self._no_hit_t=0.0
        self.hits_received+=1; self._t_received+=1
        self._post_hit_t = 0.8
        fx=from_x if from_x is not None else getattr(self,'_last_px',self.x)
        fy=from_y if from_y is not None else getattr(self,'_last_py',self.y)
        self._register_danger_directional(d,fx,fy)
        if hasattr(self,'_cover_cell'): self._cover_cell=None
        ret_t=self._p()["ret_t"]
        survival=self.hp/self.MAX_HP
        self._retreat_target=self._safe_retreat_point()
        self._retreat_arrived=False
        if self._t_received>=5 and survival<0.50:
            actual_ret=min(ret_t*1.5,2.5)
            self.state="RETREAT"; self._ret_t=actual_ret
            self._log(f"Golpeado ({self.hp:.0f}HP) presión alta → retreat [{self.tactic}]")
        elif self.state=="RETREAT":
            self._ret_t=min(self._ret_t+0.4,3.0)
            self._log(f"Golpeado en retreat ({self.hp:.0f}HP) → +0.4s")
        elif self.state=="AMBUSH":
            if self._ambush_fires>0:
                self.state="RETREAT"; self._ret_t=ret_t
                self._ambush_pos=None
                self._log(f"Emboscada rota por disparo → retreat")
            else:
                self._log(f"Golpeado en emboscada ({self.hp:.0f}HP) — manteniendo posición")
        else:
            self.state="RETREAT"; self._ret_t=ret_t
            self._log(f"Golpeado ({self.hp:.0f}HP) → retreat seguro [{self.tactic}]")

    def register_npc_hit(self):
        self.npc_hits+=1; self._t_hits+=1
        if self.state=="AMBUSH": self._ambush_fires+=1
        if self._shot_window:
            lst=list(self._shot_window)
            for i in range(len(lst)-1,-1,-1):
                if not lst[i]: lst[i]=True; break
            self._shot_window=deque(lst,maxlen=10)

    def _dodge(self, bullets, dt):
        px = getattr(self, '_last_px', self.x)
        py = getattr(self, '_last_py', self.y)
        has_los_now = has_los(self.x, self.y, px, py)
        dist_to_player = math.hypot(px - self.x, py - self.y)
        DETECT_R = 140

        final_dx = 0.0
        final_dy = 0.0
        final_spd = 0.0
        active_layer = ""

        best_threat = 0.0
        best_tti    = 999.0
        best_impact = (self.x, self.y)
        best_bdir   = (0.0, 0.0)

        for b in bullets:
            if b.owner != "player": continue
            dist_b = math.hypot(b.x - self.x, b.y - self.y)
            if dist_b > DETECT_R: continue
            bspd = math.hypot(b.vx, b.vy) or 1
            dot = (b.vx*(self.x - b.x) + b.vy*(self.y - b.y)) / (bspd * dist_b + 0.001)
            if dot < 0.35: continue
            tti = dist_b / bspd
            if tti > 0.65: continue
            impact_x = b.x + b.vx * tti
            impact_y = b.y + b.vy * tti
            miss_dist = math.hypot(impact_x - self.x, impact_y - self.y)
            threat = dot * (1.0 - tti/0.65) * max(0, 1.0 - miss_dist/(self.R*3))
            if threat > best_threat:
                best_threat = threat
                best_tti    = tti
                best_impact = (impact_x, impact_y)
                best_bdir   = (b.vx/bspd, b.vy/bspd)

        if best_threat > 0.15:
            bvx, bvy = best_bdir
            candidates = [
                (-bvy,  bvx),
                ( bvy, -bvx),
                (-bvy*0.71 - bvx*0.71,  bvx*0.71 - bvy*0.71),
                ( bvy*0.71 - bvx*0.71, -bvx*0.71 - bvy*0.71),
                (-bvy*0.71 + bvx*0.71,  bvx*0.71 + bvy*0.71),
                ( bvy*0.71 + bvx*0.71, -bvx*0.71 + bvy*0.71),
                (-bvx, -bvy),
                (-bvx*0.5 - bvy*0.5, -bvy*0.5 + bvx*0.5),
            ]

            prev_dir = getattr(self, '_last_dodge_dir', (0.0, 0.0))

            def score_candidate(cdx, cdy):
                ln = math.hypot(cdx, cdy) or 1
                cdx, cdy = cdx/ln, cdy/ln
                step = max(35, self._p()["speed"] * 0.40)
                nx2, ny2 = self.x + cdx*step, self.y + cdy*step
                s = 0.0
                d_now  = math.hypot(self.x - best_impact[0], self.y - best_impact[1])
                d_next = math.hypot(nx2    - best_impact[0], ny2    - best_impact[1])
                s += (d_next - d_now) * 3.0
                if not has_los(nx2, ny2, px, py):
                    s += 50.0
                blocked_x = iwall(nx2, self.y)
                blocked_y = iwall(self.x, ny2)
                if blocked_x and blocked_y:
                    s -= 80.0
                elif blocked_x or blocked_y:
                    s -= 20.0
                r2, c2 = w2c(nx2, ny2)
                danger = (self._danger_map.get((r2,c2), 0) +
                          N657_NPC._shared_danger.get((r2,c2), 0) * 0.4)
                s -= danger * 0.4
                same = cdx*prev_dir[0] + cdy*prev_dir[1]
                if same > 0.8:
                    s -= 25.0
                return s, cdx, cdy

            best_s = -9999; best_cdx = 0.0; best_cdy = 0.0
            for cdx, cdy in candidates:
                sc, ndx, ndy = score_candidate(cdx, cdy)
                if sc > best_s:
                    best_s = sc; best_cdx = ndx; best_cdy = ndy

            self._last_dodge_dir = (best_cdx, best_cdy)
            urgency   = 1.0 + (1.0 - best_tti/0.65) * 1.4
            final_dx  = best_cdx
            final_dy  = best_cdy
            final_spd = self._p()["speed"] * urgency
            active_layer = f"ESQUIVE tti={best_tti:.2f}s thr={best_threat:.2f}"

        elif has_los_now and dist_to_player < self.DETECT * 0.9:
            if not hasattr(self, '_anti_aim_dir'):  self._anti_aim_dir = 1
            if not hasattr(self, '_anti_aim_cd'):   self._anti_aim_cd  = 0.0
            if not hasattr(self, '_anti_aim_t'):    self._anti_aim_t   = 0.0
            self._anti_aim_cd -= dt
            self._anti_aim_t  += dt
            if self._anti_aim_cd <= 0:
                self._anti_aim_dir *= -1
                self._anti_aim_cd   = random.uniform(0.50, 1.0)
            to_px = px - self.x; to_py = py - self.y
            ln    = math.hypot(to_px, to_py) or 1
            lat_x = (-to_py / ln) * self._anti_aim_dir
            lat_y = ( to_px / ln) * self._anti_aim_dir
            if iwall(self.x + lat_x*18, self.y) and iwall(self.x, self.y + lat_y*18):
                self._anti_aim_dir *= -1
                lat_x, lat_y = -lat_x, -lat_y
            proximity_factor = max(0.3, 1.0 - dist_to_player / (self.DETECT * 0.9))
            final_dx  = lat_x
            final_dy  = lat_y
            final_spd = self._p()["speed"] * 0.40 * (1.0 + proximity_factor)
            active_layer = "ANTI-AIM"

        if self._post_hit_t > 0:
            self._post_hit_t = max(0.0, self._post_hit_t - dt)
            fade = self._post_hit_t / 1.2
            best_rdir = None; best_dscore = 9999
            for adx, ady in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                tx2 = self.x + adx * CELL * 1.5
                ty2 = self.y + ady * CELL * 1.5
                if iwall(tx2, ty2): continue
                r2, c2 = w2c(tx2, ty2)
                los_bonus = 0 if has_los(tx2, ty2, px, py) else 40
                d = (self._danger_map.get((r2,c2), 0) +
                     N657_NPC._shared_danger.get((r2,c2), 0) * 0.3 - los_bonus)
                if d < best_dscore:
                    best_dscore = d; best_rdir = (adx, ady)
            if best_rdir:
                rln  = math.hypot(*best_rdir) or 1
                rdx  = best_rdir[0]/rln * fade
                rdy  = best_rdir[1]/rln * fade
                final_dx = final_dx * 0.7 + rdx * 0.3
                final_dy = final_dy * 0.7 + rdy * 0.3
                if final_spd == 0:
                    final_spd = self._p()["speed"] * 0.55 * fade

        if has_los_now and active_layer != "ESQUIVE" and "tti" not in active_layer:
            if not hasattr(self, '_jitter_angle'): self._jitter_angle = random.uniform(0, 6.28)
            if not hasattr(self, '_jitter_cd'):    self._jitter_cd    = 0.0
            self._jitter_cd -= dt
            if self._jitter_cd <= 0:
                self._jitter_angle = random.uniform(0, 2 * math.pi)
                self._jitter_cd    = random.uniform(0.15, 0.35)
            jx = math.cos(self._jitter_angle) * 0.25
            jy = math.sin(self._jitter_angle) * 0.25
            final_dx += jx; final_dy += jy

        if final_spd > 0 or (final_dx != 0 or final_dy != 0):
            ln = math.hypot(final_dx, final_dy) or 1
            spd = final_spd if final_spd > 0 else self._p()["speed"] * 0.35
            nx = self.x + (final_dx/ln) * spd * dt
            ny = self.y + (final_dy/ln) * spd * dt
            if not iwall(nx, self.y): self.x = max(9, min(AW-9, nx))
            if not iwall(self.x, ny): self.y = max(9, min(AH-9, ny))

            if not hasattr(self, '_dodge_log_t'): self._dodge_log_t = 0.0
            self._dodge_log_t += dt
            if self._dodge_log_t > 1.2 and active_layer:
                self._dodge_log_t = 0.0
                self._log(f"EVASIÓN [{active_layer}] spd={spd:.0f} [{self.n_mode[:6]}]")

    @classmethod
    def on_round_end(cls, tactic, npc_hits, hits_received, survival, ctx_vec=None):
        cls._round_count+=1
        if ctx_vec is None:
            ctx_vec=(0.5,survival,0.5,0.0,0.0)
        cls._round_memory.append((tactic,npc_hits,hits_received,survival,ctx_vec))
        if len(cls._round_memory)>30:
            cls._round_memory=cls._round_memory[-30:]

        if len(cls._round_memory)>=2:
            tac_scores={}
            for t,hg,hr,sv,_ in cls._round_memory[-10:]:
                sc=(hg*3-hr*2+sv*10)/max(hg+hr+1,1)
                tac_scores.setdefault(t,[]).append(sc)
            avg={t:sum(v)/len(v) for t,v in tac_scores.items()}
            cls._best_tactic=max(avg,key=avg.get)

        if len(cls._round_memory)>=3:
            avg_recv=sum(r[2] for r in cls._round_memory[-3:])/3
            if avg_recv>6: cls._detect_adj=min(30,cls._detect_adj+5)
            else:          cls._detect_adj=max(-20,cls._detect_adj-3)

        cls._shared_danger={k:max(0,v-30) for k,v in cls._shared_danger.items() if v>10}

        total_hits=hits_received+(8-min(npc_hits,8))
        if total_hits > 8:
            cls._fatigue_class=min(1.0, cls._fatigue_class+0.12)
        elif survival > 0.80:
            cls._fatigue_class=max(0.0, cls._fatigue_class-0.08)

        # Decaimiento de memoria episódica (3% por ronda)
        for mem in cls._episodic_memory:
            mem["score"] = mem["score"] * 0.97

        if cls._round_count % 5 == 0:
            cls.save_ltm()


# ── PLAYER N657 ───────────────────────────────────────────────────
class PlayerN657(Player):
    EVAL_CD=0.8
    def __init__(self,x,y):
        super().__init__(x,y)
        self._p_eval_t=0.0; self._p_mode="autonomous"; self._p_tactic="balanced"
        self._p_shots=0; self._p_hits=0; self._p_rcvd=0
        self._p_engine=_make_engine() if NEURON_OK else None
        self._p_tactics={
            "aggressive":dict(chase_dist=120,strafe_dist=70,retreat_hp=0.25,spd_mult=1.10),
            "balanced":  dict(chase_dist=100,strafe_dist=85,retreat_hp=0.30,spd_mult=1.00),
            "sniper":    dict(chase_dist=145,strafe_dist=110,retreat_hp=0.35,spd_mult=0.95),
            "evasive":   dict(chase_dist=80, strafe_dist=60, retreat_hp=0.45,spd_mult=1.05),
        }
        self.color_tag=P["cyan"]

    @property
    def color(self): return P["player_hi"] if self._hf>0 else P["cyan"]

    def take_hit(self,d=10):
        super().take_hit(d); self._p_rcvd+=1

    def _p_eval(self,npc,dt):
        self._p_eval_t+=dt
        if self._p_eval_t<self.EVAL_CD: return
        self._p_eval_t=0.0
        survival=self.hp/self.MAX_HP; dist=math.hypot(npc.x-self.x,npc.y-self.y)
        los_ok=has_los(self.x,self.y,npc.x,npc.y)
        winning=self._p_hits>self._p_rcvd and self._p_hits>=2
        losing=self._p_rcvd>self._p_hits*2
        if self._p_engine:
            self._p_engine.metrics.update(avg_confidence=survival,
                error_rate_1min=self._p_rcvd/max(self._p_eval_t+0.01,1),
                memory_pressure=1-survival)
            if survival<0.28:
                self._p_engine.state_manager.transition(reason="p_hp_crit",mode=CognitiveMode.SAFE_RECOVERY)
            elif winning and survival>0.5:
                self._p_engine.state_manager.transition(reason="p_winning",mode=CognitiveMode.ADAPTIVE)
            elif losing:
                self._p_engine.state_manager.transition(reason="p_losing",mode=CognitiveMode.REASONING)
            elif self._p_shots>=6:
                self._p_engine.state_manager.transition(reason="p_data",mode=CognitiveMode.META_LEARNING)
            dec=self._p_engine.state_manager.decide_cognitive_strategy({
                "pattern_size":int(dist),
                "pattern_tags":[self._ai_state,
                                "win" if winning else "lose" if losing else "neutral",
                                "close" if dist<90 else "mid" if dist<160 else "far"],
            })
            self._p_mode=dec["mode"]; strat=dec["strategy"]
            tmap={"byte":"evasive","zlib":"balanced","lzma":"sniper",
                  "bz2":"aggressive","hybrid":"balanced","cluster":"aggressive",
                  "stored":"balanced","adaptive":"aggressive"}
            self._p_tactic=tmap.get(strat,"balanced")
        else:
            if survival<0.28:          self._p_tactic="evasive"; self._p_mode="safe_recovery"
            elif winning and dist<100: self._p_tactic="aggressive"; self._p_mode="adaptive"
            elif losing:               self._p_tactic="sniper"; self._p_mode="reasoning"
            else:                      self._p_tactic="balanced"; self._p_mode="autonomous"
        self._p_shots=0; self._p_hits=0; self._p_rcvd=0

    def shoot(self,tx,ty,bl,dt,match_cd=0.62):
        prev_len=len(bl)
        super().shoot(tx,ty,bl,dt,match_cd)
        if len(bl)>prev_len: self._p_shots+=1

    def ai_update(self,npc,bullets,dt):
        if not self.auto or not npc.alive: return 0,0
        self._p_eval(npc,dt)
        tp=self._p_tactics.get(self._p_tactic,self._p_tactics["balanced"])
        self._ai_dodge_t=max(0,self._ai_dodge_t-dt)
        dist=math.hypot(npc.x-self.x,npc.y-self.y)
        los_ok=has_los(self.x,self.y,npc.x,npc.y)
        survival=self.hp/self.MAX_HP

        moved=math.hypot(self.x-self._stuck_ref[0],self.y-self._stuck_ref[1])
        if moved>10: self._stuck_t=0.0; self._stuck_ref=(self.x,self.y)
        else: self._stuck_t+=dt
        cover_arrived=(self._ai_state=="cover" and self._cover_target is not None and
                       math.hypot(self.x-self._cover_target[0],self.y-self._cover_target[1])<25)
        if self._stuck_t>1.2 and not cover_arrived:
            self._stuck_t=0.0; self._flank_dir*=-1
            self._cover_target=None; self._cover_timer=0.0; self._ai_state="hunt"
            for k in range(8):
                a=self._flank_angle+k*math.pi/4
                if not iwall(self.x+math.cos(a)*35,self.y+math.sin(a)*35):
                    return math.cos(a),math.sin(a)
            dx,dy=AW/2-self.x,AH/2-self.y; ln=math.hypot(dx,dy) or 1
            return dx/ln,dy/ln

        best_threat=0.0; best_perp=(0.0,0.0)
        for b in bullets:
            if b.owner!="player": continue
            db=math.hypot(b.x-self.x,b.y-self.y)
            if db>110: continue
            bspd=math.hypot(b.vx,b.vy) or 1
            dot=(b.vx*(self.x-b.x)+b.vy*(self.y-b.y))/(bspd*db+0.001)
            if dot<0.5 or db/bspd>0.65: continue
            threat=dot*(1-db/(bspd*0.65))
            if threat>best_threat:
                best_threat=threat
                px2,py2=-b.vy/bspd,b.vx/bspd
                for sign in (1,-1):
                    if not iwall(self.x+px2*sign*40,self.y+py2*sign*40):
                        best_perp=(px2*sign,py2*sign); break
        if best_threat>0.3 and self._ai_dodge_t<=0:
            self._ai_dodge_t=0.3; return best_perp[0],best_perp[1]

        prev_st=self._ai_state
        retreat_hp=tp["retreat_hp"]; chase_d=tp["chase_dist"]; strafe_d=tp["strafe_dist"]
        if survival<0.25 and self._ai_state not in ("cover","retreat"):
            self._ai_state="retreat"
            if hasattr(self,'_retreat_timer'): self._retreat_timer=0.0
        elif survival<retreat_hp and self._ai_state not in ("cover","retreat","hunt"):
            self._ai_state="cover"; self._cover_target=None; self._cover_timer=0.0
        elif survival>0.70 and self._ai_state=="cover":
            self._ai_state="hunt"; self._cover_target=None
        elif los_ok and strafe_d<dist<chase_d and self._ai_state=="hunt":
            self._ai_state="strafe"
        elif (dist<strafe_d-15 or dist>chase_d+15 or not los_ok) and self._ai_state=="strafe":
            self._ai_state="hunt"
        if self._ai_state!=prev_st:
            self._stuck_t=0.0; self._stuck_ref=(self.x,self.y)

        if self._ai_state=="retreat":
            if not hasattr(self,'_retreat_timer'): self._retreat_timer=0.0
            self._retreat_timer+=dt
            if self._retreat_timer>3.0 or survival>0.70:
                self._ai_state="hunt"; self._retreat_timer=0.0; return 0,0
            px2,py2=self.x-npc.x,self.y-npc.y; ln=math.hypot(px2,py2) or 1
            dx=px2/ln+math.sin(self._flank_angle)*0.3; dy=py2/ln+math.cos(self._flank_angle)*0.3
            ln=math.hypot(dx,dy) or 1; return dx/ln,dy/ln
        elif self._ai_state=="cover":
            self._cover_timer+=dt
            if self._cover_timer>4.5:
                self._ai_state="hunt"; self._cover_target=None; self._cover_timer=0.0; return 0,0
            if self._cover_target is None:
                best=None; best_sc=-9999
                for r2 in range(1,GROWS-1,2):
                    for c2 in range(1,GCOLS-1,2):
                        if ARENA_MAP[r2][c2]: continue
                        cx2,cy2=cc(r2,c2)
                        if has_los(cx2,cy2,npc.x,npc.y): continue
                        sc3=math.hypot(cx2-npc.x,cy2-npc.y)*0.5-math.hypot(cx2-self.x,cy2-self.y)*0.4
                        if sc3>best_sc: best_sc=sc3; best=(cx2,cy2)
                self._cover_target=best or (AW-self.x,AH-self.y)
            tx,ty=self._cover_target
            if math.hypot(tx-self.x,ty-self.y)<20: return 0,0
            nr,nc=bfs(*w2c(self.x,self.y),*w2c(tx,ty))
            cx,cy=cc(nr,nc); dx,dy=cx-self.x,cy-self.y
            ln=math.hypot(dx,dy) or 1; return dx/ln,dy/ln
        elif self._ai_state=="strafe":
            self._flank_angle+=dt*2.5*self._flank_dir*tp["spd_mult"]
            px2,py2=npc.x-self.x,npc.y-self.y; ln=math.hypot(px2,py2) or 1
            perp_x=-py2/ln*self._flank_dir; perp_y=px2/ln*self._flank_dir
            if iwall(self.x+perp_x*25,self.y+perp_y*25):
                self._flank_dir*=-1; perp_x=-py2/ln*self._flank_dir; perp_y=px2/ln*self._flank_dir
            rnd=random.gauss(0,0.07)
            dx=perp_x*0.65+(px2/ln)*0.25+rnd; dy=perp_y*0.65+(py2/ln)*0.25+rnd
            ln=math.hypot(dx,dy) or 1; return dx/ln,dy/ln
        else:
            self._flank_angle+=dt*1.4*self._flank_dir
            if not los_ok: self._hunt_no_los_t+=dt
            else: self._hunt_no_los_t=0.0
            if self._hunt_no_los_t>1.5:
                self._hunt_no_los_t=0.0; self._flank_dir*=-1
            if dist>strafe_d or not los_ok:
                nr,nc=bfs(*w2c(self.x,self.y),*w2c(npc.x,npc.y))
                cx,cy=cc(nr,nc); dx,dy=cx-self.x,cy-self.y
                ln=math.hypot(dx,dy) or 1
                if ln<CELL*0.6:
                    dx=math.cos(self._flank_angle); dy=math.sin(self._flank_angle)
                else:
                    dx=dx/ln+math.sin(self._flank_angle)*0.3
                    dy=dy/ln+math.cos(self._flank_angle)*0.3
                    ln=math.hypot(dx,dy) or 1; dx/=ln; dy/=ln
                return dx,dy
            else:
                px2,py2=self.x-npc.x,self.y-npc.y; ln=math.hypot(px2,py2) or 1
                dx=px2/ln*0.55+math.sin(self._flank_angle)*self._flank_dir*0.45
                dy=py2/ln*0.55+math.cos(self._flank_angle)*self._flank_dir*0.45
                ln=math.hypot(dx,dy) or 1; return dx/ln,dy/ln
        return 0,0


# ── ARENA ─────────────────────────────────────────────────────────
class Arena:
    def __init__(self,npc):
        self.npc=npc; self.player=Player(*cc(9,1))
        self.bullets=[]; self.particles=[]; self.dmgnums=[]
        self.t=0.0; self.round=1; self._resp=False; self._resp_t=0.0
        self.wins=0; self.losses=0; self.total_dmg_taken=0; self.total_dmg_dealt=0

    def update(self,keys,dt):
        if self._resp:
            self._resp_t-=dt
            if self._resp_t<=0:
                was_auto=self.player.auto; was_score=self.player.score
                is_n657p=isinstance(self.player,PlayerN657)
                self._resp=False
                self.player=(PlayerN657(*cc(9,1)) if is_n657p else Player(*cc(9,1)))
                self.player.auto=was_auto; self.player.score=was_score
                self.npc.hp=self.npc.MAX_HP; self.round+=1
                if hasattr(self.npc,'_t_received'):
                    self.npc._t_received=0; self.npc._t_shots=0; self.npc._t_hits=0
                    self.npc._no_hit_t=0.0; self.npc.hits_received=0
                if hasattr(self.npc,'_ambush_pos'):
                    self.npc._ambush_pos=None; self.npc._ambush_wait=0.0
                    self.npc._ambush_fires=0; self.npc._RAID_phase="hunt"
                    self.npc._RAID_t=0.0; self.npc._retreat_target=None
            return
        self.t+=dt
        if self.player.auto:
            dx,dy=self.player.ai_update(self.npc,self.bullets,dt)
        else:
            dx=(keys.get("Right",0)-keys.get("Left",0))
            dy=(keys.get("Down",0)-keys.get("Up",0))
        self.player.move(dx,dy,dt); self.player.update(dt)
        if self.npc.alive:
            self.player.shoot(self.npc.x,self.npc.y,self.bullets,dt,match_cd=0.62)
        if self.npc.alive: self.npc.update(self.player,self.bullets,dt)
        for b in self.bullets: b.update(dt)
        for b in self.bullets:
            if not b.alive: continue
            if b.owner=="npc" and self.player.alive:
                if math.hypot(b.x-self.player.x,b.y-self.player.y)<self.player.R+b.R:
                    self.player.take_hit(10); b.alive=False
                    self.npc.register_npc_hit()
                    self._hit(b.x,b.y,P["red"],"-10")
            elif b.owner=="player" and self.npc.alive:
                if math.hypot(b.x-self.npc.x,b.y-self.npc.y)<self.npc.R+b.R:
                    if hasattr(self.npc,'take_hit'):
                        try:
                            self.npc.take_hit(15,from_x=self.player.x,from_y=self.player.y)
                        except TypeError:
                            self.npc.take_hit(15)
                    b.alive=False; self.player.score+=10
                    self._hit(b.x,b.y,P["white"],"-15")
        self.bullets=[b for b in self.bullets if b.alive]
        for p in self.particles: p.update(dt)
        for d in self.dmgnums:   d.update(dt)
        self.particles=[p for p in self.particles if p.alive]
        self.dmgnums=[d for d in self.dmgnums if d.alive]

        if not self.npc.alive:
            self.player.score+=100; self.wins+=1
            self.total_dmg_dealt+=self.npc.hits_received*15
            self.total_dmg_taken+=getattr(self.player,'_dmg_taken_total',0)
            if isinstance(self.npc,N657_NPC):
                ctx=self.npc._ctx_vector(
                    math.hypot(self.npc.x-self.player.x,self.npc.y-self.player.y),
                    self.npc.hp/self.npc.MAX_HP, False, False, True)
                N657_NPC.on_round_end(
                    self.npc.tactic, self.npc.npc_hits,
                    self.npc.hits_received, self.npc.hp/self.npc.MAX_HP, ctx)
            self._resp=True; self._resp_t=3.0

        if not self.player.alive:
            self.losses+=1
            self.total_dmg_taken+=getattr(self.player,'_dmg_taken_total',0)
            if isinstance(self.npc,N657_NPC):
                ctx=self.npc._ctx_vector(
                    math.hypot(self.npc.x-self.player.x,self.npc.y-self.player.y),
                    self.npc.hp/self.npc.MAX_HP, True, True, False)
                N657_NPC.on_round_end(
                    self.npc.tactic, self.npc.npc_hits,
                    self.npc.hits_received, self.npc.hp/self.npc.MAX_HP, ctx)
            self._resp=True; self._resp_t=3.0

    def _hit(self,x,y,color,txt):
        for _ in range(12): self.particles.append(Particle(x,y,color))
        self.dmgnums.append(DmgNum(x,y-8,txt,color))


# ── DASHBOARD 2D ─────────────────────────────────────────────────
class Dashboard:
    W,H=1560,860
    def __init__(self,root):
        self.root=root; self.fsm=Arena(FSM_NPC()); self.neu=Arena(N657_NPC())
        self.neu.player=PlayerN657(*cc(9,1))
        self.keys={}; self._paused=False; self._mode="manual"
        self._setup(); self._fonts(); self._build()
        self.root.after(50,self._loop)
        self.root.after(100,self.root.focus_set)

    def _setup(self):
        self.root.title("NEURON657  ·  NPC Intelligence Demo  ·  FSM vs NEURON657")
        self.root.configure(bg=P["bg"]); self.root.geometry(f"1560x860")
        self.root.resizable(False,False)
        for k in ("Left","Right","Up","Down"):
            self.root.bind(f"<KeyPress-{k}>",   lambda e,kk=k: self.keys.update({kk:1}))
            self.root.bind(f"<KeyRelease-{k}>", lambda e,kk=k: self.keys.update({kk:0}))
        self.root.bind("<KeyPress-q>",lambda e:(N657_NPC.save_ltm(), self.root.destroy()))
        self.root.protocol("WM_DELETE_WINDOW", lambda:(N657_NPC.save_ltm(), self.root.destroy()))
        self.root.bind("<KeyPress-p>",lambda e:self._toggle())
        self.root.bind("<KeyPress-r>",lambda e:self._reset())
        self.root.bind("<KeyPress-a>",lambda e:self._toggle_auto())
        self.root.bind("<KeyPress-n>",lambda e:self._toggle_n657_player())

    def _fonts(self):
        self.ft=tkfont.Font(family="Courier",size=13,weight="bold")
        self.fh=tkfont.Font(family="Courier",size=10,weight="bold")
        self.fl=tkfont.Font(family="Courier",size=9)
        self.fs=tkfont.Font(family="Courier",size=8)
        self.fb=tkfont.Font(family="Courier",size=16,weight="bold")
        self.fm=tkfont.Font(family="Courier",size=11,weight="bold")
        self.fx=tkfont.Font(family="Courier",size=7)

    def _build(self):
        hdr=tk.Frame(self.root,bg=P["bg1"],height=48); hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,text="NEURON657",font=self.ft,fg=P["cyan"],bg=P["bg1"]).place(x=16,y=12)
        tk.Label(hdr,text="·  NPC INTELLIGENCE DEMO  ·  FSM Tradicional  vs  Cognitive Agent",
                 font=self.fl,fg=P["text"],bg=P["bg1"]).place(x=145,y=16)
        self._ll=tk.Label(hdr,text="● EN VIVO",font=self.fl,fg=P["green"],bg=P["bg1"])
        self._ll.place(x=1380,y=16)
        tk.Frame(self.root,bg=P["border"],height=1).pack(fill="x")

        ch=tk.Frame(self.root,bg=P["bg"],height=28); ch.pack(fill="x"); ch.pack_propagate(False)
        tk.Label(ch,text="◀  FSM Tradicional  —  IA táctica hardcoded, cobertura, supresión",
                 font=self.fl,fg=P["fsm_npc"],bg=P["bg"]).place(x=12,y=6)
        tk.Label(ch,text="NEURON657  —  Impulsos biológicos, memoria episódica, aprende  ▶",
                 font=self.fl,fg=P["n_npc"],bg=P["bg"]).place(x=820,y=6)
        tk.Frame(self.root,bg=P["border"],height=1).pack(fill="x")

        body=tk.Frame(self.root,bg=P["bg"]); body.pack(fill="both",expand=True,padx=6,pady=4)

        # ── COLUMNA 1: Arena FSM ──
        fc=tk.Frame(body,bg=P["bg"]); fc.pack(side="left",fill="y")
        self._cf=tk.Canvas(fc,width=AW,height=AH,bg=P["fsm_bg"],
                           highlightthickness=2,highlightbackground=P["fsm_npc"]); self._cf.pack()
        self._cf.bind("<Button-1>",lambda e:self.root.focus_set())
        self._panel(fc,"fsm")

        # ── COLUMNA 2: Scoreboard central ──
        sb=tk.Frame(body,bg=P["bg"],width=148); sb.pack(side="left",fill="y",padx=4)
        sb.pack_propagate(False)
        tk.Label(sb,text="SCORE",font=self.fm,fg=P["cyan"],bg=P["bg"]).pack(pady=(6,1))
        tk.Frame(sb,bg=P["border"],height=1).pack(fill="x",padx=4)
        tk.Label(sb,text="FSM",font=self.fh,fg=P["fsm_npc"],bg=P["bg"]).pack(pady=(4,0))
        self._sb_fsm_wins=tk.Label(sb,text="W: 0",font=self.fm,fg=P["green"],bg=P["bg"]); self._sb_fsm_wins.pack()
        self._sb_fsm_loss=tk.Label(sb,text="L: 0",font=self.fs,fg=P["red"],bg=P["bg"]); self._sb_fsm_loss.pack()
        self._sb_fsm_eff=tk.Label(sb,text="EFF: —",font=self.fs,fg=P["text"],bg=P["bg"]); self._sb_fsm_eff.pack()
        tk.Frame(sb,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)
        self._sb_vs=tk.Label(sb,text="VS",font=self.fb,fg=P["white"],bg=P["bg"]); self._sb_vs.pack()
        self._sb_winner=tk.Label(sb,text="",font=self.fh,fg=P["yellow"],bg=P["bg"],wraplength=136,justify="center"); self._sb_winner.pack(pady=1)
        tk.Frame(sb,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)
        tk.Label(sb,text="NEURON",font=self.fh,fg=P["n_npc"],bg=P["bg"]).pack()
        self._sb_neu_wins=tk.Label(sb,text="W: 0",font=self.fm,fg=P["green"],bg=P["bg"]); self._sb_neu_wins.pack()
        self._sb_neu_loss=tk.Label(sb,text="L: 0",font=self.fs,fg=P["red"],bg=P["bg"]); self._sb_neu_loss.pack()
        self._sb_neu_eff=tk.Label(sb,text="EFF: —",font=self.fs,fg=P["text"],bg=P["bg"]); self._sb_neu_eff.pack()
        tk.Frame(sb,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)
        tk.Label(sb,text="DMG TOTAL",font=self.fs,fg=P["text"],bg=P["bg"]).pack()
        self._sb_fsm_dmg=tk.Label(sb,text="FSM: 0",font=self.fs,fg=P["fsm_npc"],bg=P["bg"]); self._sb_fsm_dmg.pack()
        self._sb_neu_dmg=tk.Label(sb,text="NEU: 0",font=self.fs,fg=P["n_npc"],bg=P["bg"]); self._sb_neu_dmg.pack()
        tk.Frame(sb,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)
        tk.Label(sb,text="JUGADOR NEU",font=self.fs,fg=P["text"],bg=P["bg"]).pack()
        self._sb_plr_kind=tk.Label(sb,text="N657",font=self.fh,fg=P["purple"],bg=P["bg"]); self._sb_plr_kind.pack()
        self._sb_plr_tac=tk.Label(sb,text="balanced",font=self.fs,fg=P["cyan"],bg=P["bg"]); self._sb_plr_tac.pack()
        self._sb_plr_mode=tk.Label(sb,text="AUTÓNOMO",font=self.fs,fg=P["green"],bg=P["bg"]); self._sb_plr_mode.pack()
        tk.Frame(sb,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)
        tk.Label(sb,text="MEMORIA N657",font=self.fs,fg=P["text"],bg=P["bg"]).pack()
        self._sb_mem=tk.Label(sb,text="Rondas: 0",font=self.fs,fg=P["cyan"],bg=P["bg"]); self._sb_mem.pack()
        self._sb_btac=tk.Label(sb,text="Mejor: —",font=self.fs,fg=P["green"],bg=P["bg"]); self._sb_btac.pack()
        self._sb_epi=tk.Label(sb,text="Episodios: 0",font=self.fs,fg=P["purple"],bg=P["bg"]); self._sb_epi.pack()
        tk.Frame(sb,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)
        tk.Label(sb,text="PERFIL JUGADOR",font=self.fs,fg=P["text"],bg=P["bg"]).pack()
        self._sb_profile=tk.Label(sb,text="aprendiendo...",font=self.fs,fg=P["dim"],bg=P["bg"],wraplength=136,justify="left"); self._sb_profile.pack()
        self._sb_supr=tk.Label(sb,text="Disparo: libre",font=self.fs,fg=P["green"],bg=P["bg"]); self._sb_supr.pack()

        # ── COLUMNA 3: Arena NEU ──
        nc=tk.Frame(body,bg=P["bg"]); nc.pack(side="left",fill="y")
        self._cn=tk.Canvas(nc,width=AW,height=AH,bg=P["n_bg"],
                           highlightthickness=2,highlightbackground=P["n_npc"]); self._cn.pack()
        self._cn.bind("<Button-1>",lambda e:self.root.focus_set())
        self._panel(nc,"neu")

        # ── COLUMNA 4: Panel NEU — impulsos, stats NPC y jugador ──
        rp=tk.Frame(body,bg=P["bg"],width=195); rp.pack(side="left",fill="y",padx=(4,2))
        rp.pack_propagate(False)

        tk.Label(rp,text="NPC NEURON657",font=self.fh,fg=P["n_npc"],bg=P["bg"]).pack(pady=(6,1))
        tk.Frame(rp,bg=P["n_npc"],height=1).pack(fill="x",padx=4)
        tk.Label(rp,text="IMPULSOS BIOLÓGICOS",font=self.fx,fg=P["text"],bg=P["bg"]).pack(pady=(3,0))
        self._cv_drives=tk.Canvas(rp,width=188,height=90,bg=P["bg2"],highlightthickness=0); self._cv_drives.pack(padx=3,pady=1)
        tk.Label(rp,text="RIESGO / FATIGA",font=self.fx,fg=P["text"],bg=P["bg"]).pack(pady=(2,0))
        self._cv_risk=tk.Canvas(rp,width=188,height=28,bg=P["bg2"],highlightthickness=0); self._cv_risk.pack(padx=3,pady=1)

        tk.Frame(rp,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)
        tk.Label(rp,text="ESTADO COGNITIVO",font=self.fx,fg=P["text"],bg=P["bg"]).pack()
        self._sb_drives=tk.Label(rp,text="F:— A:— P:—",font=self.fs,fg=P["yellow"],bg=P["bg"]); self._sb_drives.pack()
        self._sb_risk=tk.Label(rp,text="Riesgo: 0%",font=self.fs,fg=P["green"],bg=P["bg"]); self._sb_risk.pack()
        self._sb_fatigue=tk.Label(rp,text="💤Fatiga: 0%",font=self.fs,fg=P["green"],bg=P["bg"]); self._sb_fatigue.pack()

        tk.Frame(rp,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)

        tk.Label(rp,text="JUGADOR NEU (vs NPC)",font=self.fh,fg=P["cyan"],bg=P["bg"]).pack(pady=(2,1))
        tk.Frame(rp,bg=P["cyan"],height=1).pack(fill="x",padx=4)
        tk.Label(rp,text="TÁCTICA / MODO",font=self.fx,fg=P["text"],bg=P["bg"]).pack(pady=(3,0))
        self._cv_plr=tk.Canvas(rp,width=188,height=52,bg=P["bg2"],highlightthickness=0); self._cv_plr.pack(padx=3,pady=1)
        tk.Label(rp,text="STATS COMBATE",font=self.fx,fg=P["text"],bg=P["bg"]).pack(pady=(2,0))
        self._sb_plr_stats=tk.Label(rp,text="Disparos: 0  Impactos: 0",font=self.fs,fg=P["text"],bg=P["bg"],wraplength=185,justify="left"); self._sb_plr_stats.pack()
        self._sb_plr_hp=tk.Label(rp,text="HP: 100/100",font=self.fs,fg=P["green"],bg=P["bg"]); self._sb_plr_hp.pack()
        self._sb_plr_ai=tk.Label(rp,text="Estado IA: —",font=self.fs,fg=P["cyan"],bg=P["bg"],wraplength=185); self._sb_plr_ai.pack()

        tk.Frame(rp,bg=P["border"],height=1).pack(fill="x",padx=4,pady=3)
        tk.Label(rp,text="FSM Tradicional — ESTADO",font=self.fx,fg=P["fsm_npc"],bg=P["bg"]).pack()
        self._sb_fsm_state=tk.Label(rp,text="PATROL",font=self.fh,fg=P["fsm_npc"],bg=P["bg"]); self._sb_fsm_state.pack()
        self._sb_fsm_sub=tk.Label(rp,text="—",font=self.fx,fg=P["text"],bg=P["bg"],wraplength=185,justify="left"); self._sb_fsm_sub.pack()
        self._sb_fsm_cover=tk.Label(rp,text="Cover: —",font=self.fx,fg=P["dim"],bg=P["bg"]); self._sb_fsm_cover.pack()

        ctrl=tk.Frame(self.root,bg=P["bg1"],height=32); ctrl.pack(fill="x",side="bottom")
        ctrl.pack_propagate(False)
        cfg=dict(font=self.fl,bg=P["bg2"],relief="flat",padx=8,pady=4,cursor="hand2")
        tk.Button(ctrl,text="[Q] Salir",fg=P["red"],command=lambda:(N657_NPC.save_ltm(),self.root.destroy()),**cfg).pack(side="left",padx=4,pady=3)
        tk.Button(ctrl,text="[P] Pausa",fg=P["yellow"],command=self._toggle,**cfg).pack(side="left",padx=2)
        tk.Button(ctrl,text="[R] Reset",fg=P["cyan"],command=self._reset,**cfg).pack(side="left",padx=2)
        self._auto_btn=tk.Button(ctrl,text="[A] 🕹 MANUAL",fg=P["yellow"],command=self._toggle_auto,**cfg)
        self._auto_btn.pack(side="left",padx=2)
        tk.Button(ctrl,text="[N] Jugador N657",fg=P["purple"],command=self._toggle_n657_player,**cfg).pack(side="left",padx=2)
        tk.Label(ctrl,text="Flechas: mover jugador (modo MANUAL)  ·  [A] alterna MANUAL / IA vs IA",
                 font=self.fx,fg=P["dim"],bg=P["bg1"]).pack(side="right",padx=12)

    def _panel(self,parent,side):
        w={}
        f=tk.Frame(parent,bg=P["bg"],height=AH); f.pack(fill="x",pady=(4,0))
        color=P["fsm_npc"] if side=="fsm" else P["n_npc"]
        lbl="FSM CLÁSICA" if side=="fsm" else "NEURON657"
        tk.Label(f,text=lbl,font=self.fh,fg=color,bg=P["bg"]).grid(row=0,column=0,sticky="w",padx=6)

        f2=tk.Frame(f,bg=P["bg"]); f2.grid(row=1,column=0,sticky="ew",padx=6,pady=1)
        tk.Label(f2,text="NPC HP",font=self.fx,fg=P["text"],bg=P["bg"]).pack(side="left")
        hcv=tk.Canvas(f2,width=190,height=14,bg=P["bg2"],highlightthickness=0); hcv.pack(side="left",padx=4)
        hbar=hcv.create_rectangle(0,0,190,14,fill=color,outline="")
        hplbl=tk.Label(f2,text="120/120",font=self.fx,fg=color,bg=P["bg"]); hplbl.pack(side="left")
        w["hp_cv"]=hcv; w["hp_bar"]=hbar; w["hp_lbl"]=hplbl

        f3=tk.Frame(f,bg=P["bg"]); f3.grid(row=2,column=0,sticky="ew",padx=6,pady=1)
        tk.Label(f3,text="PLR HP",font=self.fx,fg=P["text"],bg=P["bg"]).pack(side="left")
        phcv=tk.Canvas(f3,width=190,height=14,bg=P["bg2"],highlightthickness=0); phcv.pack(side="left",padx=4)
        phbar=phcv.create_rectangle(0,0,190,14,fill=P["player"],outline="")
        phlbl=tk.Label(f3,text="100/100",font=self.fx,fg=P["player"],bg=P["bg"]); phlbl.pack(side="left")
        w["php_cv"]=phcv; w["php_bar"]=phbar; w["php_lbl"]=phlbl
        auto_lbl=tk.Label(f3,text="🕹MAN",font=self.fx,fg=P["dim"],bg=P["bg"]); auto_lbl.pack(side="left",padx=4)
        w["auto_lbl"]=auto_lbl

        if side=="neu":
            f4=tk.Frame(f,bg=P["bg"]); f4.grid(row=3,column=0,sticky="ew",padx=6,pady=1)
            mode_lbl=tk.Label(f4,text="◉ AUTÓNOMO",font=self.fl,fg=P["green"],bg=P["bg"]); mode_lbl.pack(side="left")
            tac_lbl=tk.Label(f4,text="FLANKER",font=self.fl,fg=P["green"],bg=P["bg"]); tac_lbl.pack(side="left",padx=8)
            eff_lbl=tk.Label(f4,text="EFF:—",font=self.fx,fg=P["text"],bg=P["bg"]); eff_lbl.pack(side="left")
            flash_lbl=tk.Label(f4,text="",font=self.fl,fg=P["yellow"],bg=P["bg"]); flash_lbl.pack(side="left",padx=6)
            w["mode"]=mode_lbl; w["tactic"]=tac_lbl; w["eff"]=eff_lbl; w["tactic_flash"]=flash_lbl
        else:
            f4=tk.Frame(f,bg=P["bg"]); f4.grid(row=3,column=0,sticky="ew",padx=6,pady=1)
            st_lbl=tk.Label(f4,text="PATROL",font=self.fl,fg=P["fsm_npc"],bg=P["bg"]); st_lbl.pack(side="left")
            cd_lbl=tk.Label(f4,text="CD:0.85s",font=self.fx,fg=P["text"],bg=P["bg"]); cd_lbl.pack(side="left",padx=8)
            w["state"]=st_lbl; w["cd"]=cd_lbl

        dec_lbl=tk.Label(f,text="—",font=self.fx,fg=P["text"],bg=P["bg"],wraplength=AW-12,justify="left",anchor="w")
        dec_lbl.grid(row=4,column=0,sticky="ew",padx=6)
        w["dec"]=dec_lbl

        logs=[]
        for i in range(5):
            ll=tk.Label(f,text="",font=self.fx,fg=P["text"],bg=P["bg"],anchor="w",justify="left")
            ll.grid(row=5+i,column=0,sticky="ew",padx=6)
            logs.append(ll)
        w["log"]=logs

        if side=="fsm": self._w_fsm=w
        else: self._w_neu=w

    def _loop(self):
        if not self._paused:
            dt=0.033
            if self._mode == "manual":
                self.fsm.player.auto = False
                self.neu.player.auto = False
                self.fsm.update(self.keys, dt)
                self.neu.update(self.keys, dt)
            else:
                self.fsm.player.auto = True
                self.neu.player.auto = True
                self.fsm.update({}, dt)
                self.neu.update({}, dt)
        self._render(self._cf,self.fsm,"fsm")
        self._render(self._cn,self.neu,"neu")
        self._panels()
        self.root.after(33,self._loop)

    def _render(self,cv,arena,side):
        cv.delete("all")
        for r in range(GROWS):
            for c in range(GCOLS):
                x0,y0=c*CELL,r*CELL
                if ARENA_MAP[r][c]:
                    cv.create_rectangle(x0,y0,x0+CELL,y0+CELL,fill=P["wall"],outline=P["grid"],width=1)
                else:
                    cv.create_rectangle(x0,y0,x0+CELL,y0+CELL,fill=P["floor"],outline=P["grid"],width=1)

        p=arena.player; npc=arena.npc

        if arena._resp:
            cv.create_rectangle(0,0,AW,AH,fill="#000000",stipple="gray50")
            cv.create_text(AW//2,AH//2,text=f"{'VICTORIA' if arena.wins>arena.losses else 'DERROTA'}\nRonda {arena.round+1} →",
                           font=self.fh,fill=P["yellow"],justify="center")
            return

        if npc.alive:
            fov_d=getattr(npc,'fov_deg',120)
            facing=getattr(npc,'_facing',0)
            detect_px=(getattr(npc,'DETECT',185)+
                       (npc._p().get("detect_bonus",0) if hasattr(npc,'_p') else 0)+
                       N657_NPC._detect_adj if side=="neu" else 185)
            pts=vision_polygon(npc.x,npc.y,facing,fov_d,detect_px,n_rays=24)
            if len(pts)>4:
                flat=[v for pt in pts for v in pt]
                fov_color="#003322" if side=="neu" else "#1a0808"
                fov_border=P["n_npc"] if side=="neu" else P["fsm_npc"]
                cv.create_polygon(flat,fill=fov_color,outline=fov_border,width=1,stipple="gray25")

        if side=="neu" and hasattr(npc,'_danger_map'):
            for r2 in range(1,GROWS-1):
                for c2 in range(1,GCOLS-1):
                    if ARENA_MAP[r2][c2]: continue
                    cx2,cy2=cc(r2,c2)
                    if has_los(cx2,cy2,p.x,p.y): continue
                    danger_val=npc._danger_map.get((r2,c2),0)+N657_NPC._shared_danger.get((r2,c2),0)*0.3
                    if danger_val<15:
                        x0,y0=c2*CELL,r2*CELL
                        cv.create_rectangle(x0,y0,x0+CELL,y0+CELL,
                                            fill=P["green"],outline="",stipple="gray12")
            for (r2,c2),d2 in npc._danger_map.items():
                if d2<20: continue
                x0,y0=c2*CELL,r2*CELL
                stipple="gray50" if d2>60 else "gray25"
                cv.create_rectangle(x0,y0,x0+CELL,y0+CELL,
                                    fill=P["red"],outline="",stipple=stipple)
            if hasattr(npc,'_cover_pos') and npc._cover_pos and npc.state in ("COVER","RETREAT"):
                cpx,cpy=npc._cover_pos
                cv.create_rectangle(cpx-8,cpy-8,cpx+8,cpy+8,
                                    outline=P["purple"],width=2,dash=(3,3))
                cv.create_text(cpx,cpy,text="⛊",font=self.fx,fill=P["purple"])

        for pp in arena.particles:
            cv.create_oval(pp.x-pp.r,pp.y-pp.r,pp.x+pp.r,pp.y+pp.r,fill=pp.color,outline="")

        for b in arena.bullets:
            col=P["bullet_p"] if b.owner=="player" else P["bullet_e"]
            cv.create_oval(b.x-3,b.y-3,b.x+3,b.y+3,fill=col,outline="")

        r_p=p.R
        col_p=P["player_hi"] if p._hf>0 else (P["cyan"] if isinstance(p,PlayerN657) else P["player"])
        cv.create_oval(p.x-r_p,p.y-r_p,p.x+r_p,p.y+r_p,fill=col_p,outline=P["white"],width=2)
        facing_p=getattr(p,'angle',0) if hasattr(p,'angle') else math.atan2(0,1)
        if hasattr(p,'_ai_state'): cv.create_text(p.x,p.y,text=p._ai_state[:2].upper(),font=self.fx,fill=P["bg"])

        if npc.alive:
            nc_r=npc.R; nc_col=npc.color
            state_colors={
                "PATROL":P["blue"],"CHASE":P["yellow"],"ATTACK":P["red"],
                "RETREAT":P["orange"],"STRAFE":P["cyan"],"FLANK":P["green"],
                "COVER":P["purple"],"KITE":P["text"],"SEARCH":P["text_hi"],
                "AMBUSH":P["ambush"],"RAID":P["RAID"]
            }
            ring=state_colors.get(npc.state,P["dim"])
            if npc._hf>0.25:
                fr=nc_r+int(npc._hf*28)
                cv.create_oval(npc.x-fr,npc.y-fr,npc.x+fr,npc.y+fr,fill=P["white"],outline="")
            if npc.state=="AMBUSH":
                pulse=nc_r+8+int(math.sin(time.time()*8)*4)
                cv.create_oval(npc.x-pulse,npc.y-pulse,npc.x+pulse,npc.y+pulse,
                               outline=P["ambush"],width=2)
            cv.create_oval(npc.x-nc_r-5,npc.y-nc_r-5,npc.x+nc_r+5,npc.y+nc_r+5,
                           outline=ring,width=3 if npc.state=="ATTACK" else 2)
            bf=P["white"] if npc._hf>0.32 else nc_col
            cv.create_oval(npc.x-nc_r,npc.y-nc_r,npc.x+nc_r,npc.y+nc_r,fill=bf,outline="")
            cv.create_text(npc.x,npc.y,text=npc.state[:3],font=self.fx,fill=P["bg"])
            if side=="neu":
                fat=getattr(npc,'_fatigue',0.0)
                fat_cls=N657_NPC._fatigue_class
                fat_total=min(1.0, fat+fat_cls*0.3)
                if fat_total>0.15:
                    far2=nc_r+2+int(fat_total*14)
                    stipple_f="gray75" if fat_total>0.5 else "gray50"
                    aura_col=P["red"] if fat_total>0.7 else P["orange"] if fat_total>0.4 else "#886600"
                    cv.create_oval(npc.x-far2,npc.y-far2,npc.x+far2,npc.y+far2,
                                   outline=aura_col,width=2,dash=(2,3))
                    if fat_total>0.5:
                        cv.create_text(npc.x+nc_r+8,npc.y-nc_r,
                                       text=f"FAT{fat_total:.0%}",font=self.fx,fill=aura_col)
            if side=="neu" and getattr(npc,'_suppress_t',0)>0:
                cv.create_text(npc.x,npc.y-nc_r-30,text="🔇SUPR",font=self.fx,fill=P["yellow"])
            if side=="neu" and hasattr(npc,'_tactic_flash') and npc._tactic_flash>0:
                tc2=TACTIC_COLOR.get(npc.tactic,P["n_npc"])
                cv.create_text(npc.x,npc.y-nc_r-22,
                               text=f"▲{npc.tactic.upper()}",font=self.fl,fill=tc2)
            elif side=="neu":
                tc2=TACTIC_COLOR.get(npc.tactic,P["cyan"])
                cv.create_text(npc.x,npc.y-nc_r-15,text=npc.tactic.upper(),font=self.fl,fill=tc2)
            bw=nc_r*2+10; ratio=npc.hp/npc.MAX_HP
            cv.create_rectangle(npc.x-nc_r-5,npc.y+nc_r+3,npc.x+nc_r+5,npc.y+nc_r+12,fill=P["bg2"],outline=P["dim"])
            hc2=P["green"] if ratio>0.5 else P["yellow"] if ratio>0.25 else P["red"]
            cv.create_rectangle(npc.x-nc_r-5,npc.y+nc_r+3,npc.x-nc_r-5+int((bw+10)*ratio),npc.y+nc_r+12,fill=hc2,outline="")
            cv.create_text(npc.x,npc.y+nc_r+19,text=f"{int(npc.hp)}HP",font=self.fx,fill=hc2)
            if side=="neu" and hasattr(npc,'_ambush_pos') and npc._ambush_pos and npc.state=="AMBUSH":
                ax,ay=npc._ambush_pos
                cv.create_rectangle(ax-6,ay-6,ax+6,ay+6,outline=P["ambush"],width=2)
                cv.create_text(ax,ay-12,text="AMBUSH",font=self.fx,fill=P["ambush"])
                cv.create_line(npc.x,npc.y,ax,ay,fill=P["ambush"],width=1,dash=(4,4))

        for dn in arena.dmgnums:
            try:
                cv.create_text(dn.x+1,dn.y+1,text=dn.txt,font=self.fh,fill=P["bg"])
                cv.create_text(dn.x,dn.y,text=dn.txt,font=self.fh,fill=dn.color)
            except: pass

        cv.create_text(8,8,text=f"Ronda {arena.round}",font=self.fx,fill=P["text"],anchor="nw")
        cv.create_text(8,20,text=f"Score: {p.score}",font=self.fx,fill=P["yellow"],anchor="nw")
        legend=[("PAT",P["blue"]),("CHA",P["yellow"]),("ATK",P["red"]),
                ("RET",P["orange"]),("AMB",P["ambush"]),("GUE",P["RAID"])]
        for i,(st,co) in enumerate(legend):
            cv.create_rectangle(AW-58,4+i*12,AW-48,13+i*12,fill=co,outline="")
            cv.create_text(AW-44,9+i*12,text=st,font=self.fx,fill=co,anchor="w")
        if side=="neu" and hasattr(p,'_ai_state') and p.auto and npc.alive:
            p_facing=math.atan2(npc.y-p.y, npc.x-p.x)
            pts_p=vision_polygon(p.x,p.y,p_facing,110,175,n_rays=16)
            if len(pts_p)>4:
                flat_p=[v for pt in pts_p for v in pt]
                cv.create_polygon(flat_p,fill="#001133",outline=P["cyan"],width=1,stipple="gray12")

    def _panels(self):
        fw=self._w_fsm; fn=self.fsm.npc; fp=self.fsm.player
        self._hpbar(fw["hp_cv"],fn.hp,fn.MAX_HP,P["fsm_npc"])
        regen_str=f"+{1.0:.1f}/s" if fn._no_hit_t>3.0 and fn.hp<fn.MAX_HP else ""
        fw["hp_lbl"].config(text=f"{int(fn.hp)}/{fn.MAX_HP} {regen_str}")
        self._hpbar(fw["php_cv"],fp.hp,fp.MAX_HP,P["player"])
        fw["php_lbl"].config(text=f"{int(fp.hp)}/{fp.MAX_HP}")
        ai_st=fp._ai_state if fp.auto else None
        fw["auto_lbl"].config(text=f"🤖{ai_st[:3].upper()}" if fp.auto and ai_st else "🕹MAN",
                              fg=P["cyan"] if fp.auto else P["dim"])
        fw["state"].config(text=fn.state)
        fw["cd"].config(text=f"CD:{fn.SHOOT_CD_FIXED:.2f}s (fijo)")
        fw["dec"].config(text=fn.decision_log[0]["reason"][:60] if fn.decision_log else "—")
        for i,l in enumerate(fw["log"]):
            e=list(fn.decision_log)
            l.config(text=f"  {e[i]['state']:8s} — {e[i]['reason'][:40]}" if i<len(e) else "",
                     fg=P["fsm_npc"] if i==0 else P["text"])

        nw=self._w_neu; nn=self.neu.npc; np2=self.neu.player
        self._hpbar(nw["hp_cv"],nn.hp,nn.MAX_HP,P["n_npc"])
        regen_str2=f"+{nn._regen_rate:.1f}/s" if nn._no_hit_t>2.0 and nn.hp<nn.MAX_HP else ""
        nw["hp_lbl"].config(text=f"{int(nn.hp)}/{nn.MAX_HP} {regen_str2}")
        self._hpbar(nw["php_cv"],np2.hp,np2.MAX_HP,P["player"])
        nw["php_lbl"].config(text=f"{int(np2.hp)}/{np2.MAX_HP}")
        ai_st2=np2._ai_state if np2.auto else None
        nw["auto_lbl"].config(text=f"🤖{ai_st2[:3].upper()}" if np2.auto and ai_st2 else "🕹MAN",
                              fg=P["cyan"] if np2.auto else P["dim"])

        fa=self.fsm; na=self.neu
        tot_fsm=fa.wins+fa.losses or 1; tot_neu=na.wins+na.losses or 1
        self._sb_fsm_wins.config(text=f"W: {fa.wins}")
        self._sb_fsm_loss.config(text=f"L: {fa.losses}")
        self._sb_fsm_eff.config(text=f"EFF: {fa.wins/tot_fsm*100:.0f}%")
        self._sb_neu_wins.config(text=f"W: {na.wins}")
        self._sb_neu_loss.config(text=f"L: {na.losses}")
        self._sb_neu_eff.config(text=f"EFF: {na.wins/tot_neu*100:.0f}%")
        self._sb_fsm_dmg.config(text=f"FSM: {fa.total_dmg_dealt}")
        self._sb_neu_dmg.config(text=f"NEU: {na.total_dmg_dealt}")
        if na.wins>fa.wins:
            self._sb_winner.config(text=f"NEU +{na.wins-fa.wins}",fg=P["n_npc"])
            self._sb_vs.config(fg=P["n_npc"])
        elif fa.wins>na.wins:
            self._sb_winner.config(text=f"FSM +{fa.wins-na.wins}",fg=P["fsm_npc"])
            self._sb_vs.config(fg=P["fsm_npc"])
        else:
            self._sb_winner.config(text="EMPATE",fg=P["yellow"])
            self._sb_vs.config(fg=P["white"])

        p2=self.neu.player
        if isinstance(p2,PlayerN657):
            self._sb_plr_kind.config(text="N657",fg=P["purple"])
            self._sb_plr_tac.config(text=p2._p_tactic.upper(),
                fg={"aggressive":P["red"],"balanced":P["cyan"],
                    "sniper":P["purple"],"evasive":P["orange"]}.get(p2._p_tactic,P["text"]))
            self._sb_plr_mode.config(text=MODE_LABEL.get(p2._p_mode,p2._p_mode.upper()),
                fg=MODE_COLOR.get(p2._p_mode,P["text"]))
        else:
            self._sb_plr_kind.config(text="STD",fg=P["dim"])
            self._sb_plr_tac.config(text="—",fg=P["dim"])
            self._sb_plr_mode.config(text="RULES",fg=P["dim"])

        self._sb_mem.config(text=f"Rondas: {N657_NPC._round_count}")
        mode_col = P["cyan"] if self._mode=="ia_vs_ia" else P["white"]
        self._sb_vs.config(fg=mode_col)
        fa2=self.fsm; na2=self.neu
        if fa2.wins==na2.wins:
            mode_txt = "🤖 IA vs IA" if self._mode=="ia_vs_ia" else "🕹 MANUAL"
            self._sb_winner.config(text=mode_txt, fg=mode_col)
        self._sb_btac.config(text=f"Mejor: {N657_NPC._best_tactic or '—'}",
                             fg=TACTIC_COLOR.get(N657_NPC._best_tactic or "",P["green"]))
        self._sb_epi.config(text=f"Episodios: {len(N657_NPC._episodic_memory)}")
        d=getattr(nn,"_drives",{})
        dr=getattr(nn,"_death_risk",0.0)
        fat=min(1.0,getattr(nn,'_fatigue',0)+N657_NPC._fatigue_class*0.3)
        self._sb_drives.config(
            text=f"😱{d.get('fear',0):.1f} ⚔{d.get('aggression',0):.1f} 🐾{d.get('prey',0):.1f} 🔍{d.get('curiosity',0):.1f}",
            fg=P["red"] if d.get("fear",0)>0.6 else P["yellow"] if d.get("aggression",0)>0.6 else P["cyan"])
        risk_pct=int(dr*100)
        self._sb_risk.config(
            text=f"Riesgo muerte: {risk_pct}%",
            fg=P["red"] if risk_pct>60 else P["yellow"] if risk_pct>35 else P["green"])
        fat_pct=int(fat*100)
        self._sb_fatigue.config(
            text=f"💤Fatiga: {fat_pct}%" + (" [global]" if N657_NPC._fatigue_class>0.1 else ""),
            fg=P["red"] if fat>0.7 else P["orange"] if fat>0.4 else P["green"])
        prof=N657_NPC._shared_player_profile
        if prof.get("samples",0)>=3:
            self._sb_profile.config(
                text=(f"Jugador: agr={prof.get('aggression',0.5):.1f} "
                      f"prec={prof.get('precision',0.5):.1f} "
                      f"mob={prof.get('mobility',0.5):.1f}"),
                fg=P["cyan"])
        else:
            self._sb_profile.config(text="Perfil: aprendiendo...", fg=P["dim"])
        supr=getattr(nn,'_suppress_t',0)
        self._sb_supr.config(
            text=f"🔇Supresión: {supr:.1f}s" if supr>0 else "Disparo: libre",
            fg=P["yellow"] if supr>0 else P["green"])

        mc=MODE_COLOR.get(nn.n_mode,P["text"])
        nw["mode"].config(text=f"◉ {MODE_LABEL.get(nn.n_mode,nn.n_mode.upper())}",fg=mc)
        tc=TACTIC_COLOR.get(nn.tactic,P["cyan"])
        nw["tactic"].config(text=nn.tactic.upper(),fg=tc)
        dmg_d=nn.npc_hits*10; dmg_r=nn.hits_received*15; tot=dmg_d+dmg_r
        eff=dmg_d/tot if tot>0 else None
        nw["eff"].config(text=f"{eff:.0%}" if eff is not None else "—",
                         fg=P["green"] if eff and eff>0.5 else P["red"] if eff and eff<0.3 else P["yellow"])
        if hasattr(nn,'_tactic_flash') and nn._tactic_flash>0.2:
            nw["tactic_flash"].config(
                text=f"◀ {nn._prev_tactic.upper() if hasattr(nn,'_prev_tactic') else '?'} → {nn.tactic.upper()} ▶",
                fg=P["yellow"])
        else:
            nw["tactic_flash"].config(text="")

        nw["dec"].config(text=nn.last_dec[:65])
        for i,l in enumerate(nw["log"]):
            e=list(nn.decision_log)
            if i<len(e):
                l.config(text=f"  [{e[i].get('mode','?')[:8]:8s}] {e[i]['reason'][:44]}",
                         fg=P["n_npc"] if i==0 else P["text"])
            else: l.config(text="")

        cv_d=self._cv_drives; cv_d.delete("all")
        bar_items=[
            ("😱 fear",     d.get("fear",0),      P["red"]),
            ("⚔  aggr",    d.get("aggression",0), P["orange"]),
            ("🐾 prey",     d.get("prey",0),       P["yellow"]),
            ("🔍 curio",    d.get("curiosity",0),  P["cyan"]),
            ("🛡 caut",     d.get("caution",0),    P["blue"]),
        ]
        BAR_W=118
        for ii,(label,val,col) in enumerate(bar_items):
            y0=4+ii*17
            cv_d.create_text(4,y0+5,text=label,font=self.fx,fill=col,anchor="w")
            filled=int(val*BAR_W)
            cv_d.create_rectangle(58,y0,58+BAR_W,y0+12,outline=P["dim"],fill=P["bg"])
            if filled>0:
                cv_d.create_rectangle(58,y0,58+filled,y0+12,fill=col,outline="")
            cv_d.create_text(180,y0+6,text=f"{val:.2f}",font=self.fx,fill=col,anchor="e")

        cv_r=self._cv_risk; cv_r.delete("all")
        risk_col=P["red"] if dr>0.6 else P["yellow"] if dr>0.35 else P["green"]
        fat_col=P["red"] if fat>0.7 else P["orange"] if fat>0.4 else P["green"]
        cv_r.create_text(4,7,text="⚠ riesgo",font=self.fx,fill=risk_col,anchor="w")
        cv_r.create_rectangle(58,1,58+BAR_W,13,outline=P["dim"],fill=P["bg"])
        cv_r.create_rectangle(58,1,58+int(dr*BAR_W),13,fill=risk_col,outline="")
        cv_r.create_text(180,7,text=f"{int(dr*100)}%",font=self.fx,fill=risk_col,anchor="e")
        cv_r.create_text(4,21,text="💤 fatiga",font=self.fx,fill=fat_col,anchor="w")
        cv_r.create_rectangle(58,15,58+BAR_W,27,outline=P["dim"],fill=P["bg"])
        cv_r.create_rectangle(58,15,58+int(fat*BAR_W),27,fill=fat_col,outline="")
        cv_r.create_text(180,21,text=f"{int(fat*100)}%",font=self.fx,fill=fat_col,anchor="e")

        p2=self.neu.player; cv_p=self._cv_plr; cv_p.delete("all")
        if isinstance(p2,PlayerN657):
            tac_col={"aggressive":P["red"],"balanced":P["cyan"],
                     "sniper":P["purple"],"evasive":P["orange"]}.get(p2._p_tactic,P["text"])
            mode_col=MODE_COLOR.get(p2._p_mode,P["text"])
            cv_p.create_text(94,8,text=p2._p_tactic.upper(),font=self.fh,fill=tac_col,anchor="center")
            cv_p.create_text(94,22,text=MODE_LABEL.get(p2._p_mode,p2._p_mode.upper()),
                             font=self.fx,fill=mode_col,anchor="center")
            hp_ratio=p2.hp/p2.MAX_HP; hp_col=P["green"] if hp_ratio>0.5 else P["yellow"] if hp_ratio>0.25 else P["red"]
            cv_p.create_rectangle(8,32,180,44,outline=P["dim"],fill=P["bg"])
            cv_p.create_rectangle(8,32,8+int(172*hp_ratio),44,fill=hp_col,outline="")
            cv_p.create_text(94,38,text=f"HP {int(p2.hp)}/{p2.MAX_HP}",font=self.fx,fill=P["bg"],anchor="center")
            ai_s=getattr(p2,'_ai_state','—')
            cv_p.create_text(94,50,text=f"IA: {ai_s.upper()}" if p2.auto else "🕹 MANUAL",
                             font=self.fx,fill=P["cyan"] if p2.auto else P["dim"],anchor="center")
            self._sb_plr_kind.config(text="N657",fg=P["purple"])
            self._sb_plr_tac.config(text=p2._p_tactic.upper(),fg=tac_col)
            self._sb_plr_mode.config(text=MODE_LABEL.get(p2._p_mode,p2._p_mode.upper()),fg=mode_col)
            shots=getattr(p2,'_p_shots',0); hits=getattr(p2,'_p_hits',0)
            self._sb_plr_stats.config(text=f"Shots:{p2._p_shots+shots}  Hits:{p2._p_hits+hits}  Rcvd:{p2._p_rcvd}")
            self._sb_plr_hp.config(text=f"HP: {int(p2.hp)}/{p2.MAX_HP}",fg=hp_col)
            self._sb_plr_ai.config(text=f"Estado IA: {ai_s.upper() if p2.auto else 'MANUAL'}",
                                   fg=P["cyan"] if p2.auto else P["yellow"])
        else:
            cv_p.create_text(94,26,text="STD PLAYER",font=self.fh,fill=P["dim"],anchor="center")
            hp_ratio=p2.hp/p2.MAX_HP; hp_col=P["green"] if hp_ratio>0.5 else P["yellow"] if hp_ratio>0.25 else P["red"]
            cv_p.create_rectangle(8,32,180,44,outline=P["dim"],fill=P["bg"])
            cv_p.create_rectangle(8,32,8+int(172*hp_ratio),44,fill=hp_col,outline="")
            cv_p.create_text(94,38,text=f"HP {int(p2.hp)}/{p2.MAX_HP}",font=self.fx,fill=P["bg"],anchor="center")
            self._sb_plr_kind.config(text="STD",fg=P["dim"])
            self._sb_plr_tac.config(text="—",fg=P["dim"])
            self._sb_plr_mode.config(text="RULES",fg=P["dim"])
            self._sb_plr_stats.config(text="—")
            self._sb_plr_hp.config(text=f"HP: {int(p2.hp)}/{p2.MAX_HP}",fg=hp_col)
            self._sb_plr_ai.config(text="Manual / reglas")

        fn=self.fsm.npc
        self._sb_fsm_state.config(text=fn.state,
            fg={"PATROL":P["blue"],"CHASE":P["yellow"],"ATTACK":P["red"],
                "RETREAT":P["orange"],"STRAFE":P["cyan"],"SUPPRESS":P["purple"],
                "PEEK":P["green"],"COVER":P["purple"],"FLANK":P["green"]}.get(fn.state,P["text"]))
        fsm_detail=fn.decision_log[0]["reason"][:55] if fn.decision_log else "—"
        self._sb_fsm_sub.config(text=fsm_detail)
        cover_q=getattr(fn,'_cover_quality',0)
        supr=getattr(fn,'_suppress_t',0)
        burst=getattr(fn,'_burst_remaining',0)
        self._sb_fsm_cover.config(
            text=(f"Cover:{cover_q:.0%}  " if cover_q>0 else "")+
                 (f"🔇{supr:.1f}s  " if supr>0 else "")+
                 (f"Burst:{burst}" if burst>0 else ""),
            fg=P["purple"] if supr>0 else P["fsm_npc"])

    def _hpbar(self,cv,hp,maxhp,color):
        cv.delete("all"); ratio=hp/maxhp if maxhp>0 else 0; w=int(190*ratio)
        c=P["green"] if ratio>0.5 else P["yellow"] if ratio>0.25 else P["red"]
        if w>0: cv.create_rectangle(0,0,w,14,fill=c,outline="")

    def _toggle(self):
        self._paused=not self._paused
        self._ll.config(text="⏸ PAUSADO" if self._paused else "● EN VIVO",
                        fg=P["yellow"] if self._paused else P["green"])

    def _toggle_auto(self):
        self.root.focus_set()
        if self._mode == "manual":
            self._mode = "ia_vs_ia"
            self._auto_btn.config(text="[A] 🤖 IA vs IA", fg=P["cyan"])
            self._ll.config(text="● IA vs IA AUTO", fg=P["cyan"])
        else:
            self._mode = "manual"
            self.fsm.player.auto = False
            self.neu.player.auto = False
            self._auto_btn.config(text="[A] 🕹 MANUAL", fg=P["yellow"])
            self._ll.config(text="● EN VIVO", fg=P["green"])

    def _toggle_n657_player(self):
        self.root.focus_set()
        was_auto=self.neu.player.auto; was_score=self.neu.player.score
        if isinstance(self.neu.player,PlayerN657):
            self.neu.player=Player(*cc(9,1))
        else:
            self.neu.player=PlayerN657(*cc(9,1))
        self.neu.player.auto = True if self._mode=="ia_vs_ia" else was_auto
        self.neu.player.score=was_score

    def _reset(self):
        self.root.focus_set()
        self.fsm=Arena(FSM_NPC()); self.neu=Arena(N657_NPC())
        self.neu.player=PlayerN657(*cc(9,1))
        if self._mode == "ia_vs_ia":
            self.fsm.player.auto=True; self.neu.player.auto=True
        else:
            self.fsm.player.auto=False; self.neu.player.auto=False
        self.keys={}


def main():
    root=tk.Tk()
    dashboard = None
    
    try:
        dashboard = Dashboard(root)
        
        if not NEURON_OK:
            import tkinter.messagebox as mb
            mb.showwarning("NEURON657","neuron657_v13.py no encontrado — funcionando en modo degradado.")
        
        root.mainloop()
    
    except Exception as e:
        print(f"[ERROR] Error en main: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        #  Cleanup de engines
        print("[INFO] Limpiando recursos de NEURON657...")
        
        if dashboard is not None:
            # FSM Arena
            if hasattr(dashboard, 'fsm'):
                if hasattr(dashboard.fsm, 'npc'):
                    if hasattr(dashboard.fsm.npc, 'engine'):
                        try:
                            print("[INFO] Cerrando FSM engine...")
                            dashboard.fsm.npc.engine.shutdown()
                        except Exception as e:
                            print(f"[WARN] Error cerrando FSM engine: {e}")
            
            # Neuron657 Arena
            if hasattr(dashboard, 'neu'):
                if hasattr(dashboard.neu, 'npc'):
                    if hasattr(dashboard.neu.npc, 'engine'):
                        try:
                            print("[INFO] Cerrando NEURON657 engine...")
                            dashboard.neu.npc.engine.shutdown()
                        except Exception as e:
                            print(f"[WARN] Error cerrando NEURON657 engine: {e}")
        
        # Destruir GUI
        try:
            root.destroy()
        except:
            pass
        
        print("[INFO] Cleanup completo - Adiós!")

if __name__=="__main__": main()