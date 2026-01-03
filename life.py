#!/usr/bin/env python3
"""
Neuron657 AI Arena - NPC Inteligente vs Máquina - VERSIÓN MEJORADA
================================================
EL NPC AHORA APRENDE REALMENTE con sistemas mejorados:
1. Meta-aprendizaje con retroalimentación en tiempo real
2. Transferencia de conocimiento inteligente entre comportamientos
3. Generación y validación de hipótesis
4. Memoria episódica persistente
5. Observación, imitación y mejora continua
6. Sistema de auto-evaluación y corrección
"""
# ---------- SILENCIO TOTAL ----------
import logging
import warnings
logging.disable(logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("neuron657").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

import pygame
import sys
import os
import math
import random
import time
import numpy as np
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque
import json
import hashlib

# Configuración de paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importamos Neuron657
try:
    from neuron657 import (
        Neuron657Core,
        NPF657Pattern,
        Goal657,
        CognitiveMode657,
        Config,
        validate_integrity
    )
    NEURON657_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Advertencia: No se pudo importar Neuron657: {e}")
    print("El NPC funcionará en modo dummy (sin aprendizaje)")
    NEURON657_AVAILABLE = False

# ============================================
# CONFIGURACIÓN DEL JUEGO SUPER-MEJORADA
# ============================================

class GameConfig:
    # Pantalla
    WIDTH = 1200  # Más ancho para mostrar más información
    HEIGHT = 800  # Más alto
    FPS = 60
    
    # Colores
    BACKGROUND = (15, 15, 25)
    GRID_COLOR = (35, 35, 50)
    TEXT_COLOR = (230, 230, 250)
    NPC_COLOR = (80, 180, 255)    # Azul más brillante
    AI_COLOR = (255, 90, 90)      # Rojo más brillante
    HEALTH_BAR_GOOD = (60, 220, 100)
    HEALTH_BAR_WARNING = (255, 220, 70)
    HEALTH_BAR_DANGER = (255, 70, 70)
    UI_BG = (25, 25, 40, 220)
    UI_BORDER = (70, 70, 100)
    
    # NPC (que aprende)
    NPC_SPEED = 3.8  # Un poco más rápido
    NPC_ATTACK_RANGE = 80  # Mayor rango
    NPC_ATTACK_DAMAGE = 14  # Más daño
    NPC_ATTACK_COOLDOWN = 22  # Cooldown reducido
    NPC_DEFENSE_REDUCTION = 0.55  # Mejor defensa
    
    # Máquina (hardcodeada)
    AI_SPEED = 4.2  # Un poco más rápido para mayor desafío
    AI_ATTACK_RANGE = 85
    AI_ATTACK_DAMAGE = 16
    AI_ATTACK_COOLDOWN = 18
    AI_DEFENSE_REDUCTION = 0.45
    
    # Arena
    ARENA_PADDING = 60
    ARENA_COLOR = (20, 20, 35)
    
    # Aprendizaje MEJORADO - CRÍTICO: Tamaño de patrón debe coincidir con Neuron657
    PATTERN_SIZE = 64  # DEBE SER 64 para coincidir con NPF657Pattern.SIZE
    LEARNING_RATE = 0.18
    MEMORY_FILE = "npc_intelligent_v2.n657"
    
    # Rondas
    ROUNDS_PER_BEHAVIOR = 4  # Más rondas por comportamiento
    MAX_ROUND_TIME = 60  # Más tiempo por ronda
    
    # Nuevos parámetros de inteligencia MEJORADOS
    EPISODIC_MEMORY_SIZE = 1000  # Más memoria
    HYPOTHESIS_EXPLORATION_RATE = 0.35
    KNOWLEDGE_TRANSFER_RATE = 0.75
    META_LEARNING_INTERVAL = 80
    PATTERN_RECOGNITION_THRESHOLD = 0.65
    
    # Sistema de recompensas mejorado
    REWARD_SUCCESS = 0.8
    REWARD_FAILURE = -0.5
    REWARD_SURVIVAL = 0.1
    REWARD_DAMAGE = 0.02
    PENALTY_DAMAGE = -0.03
    
    # Nuevo: Sistema de especialización
    BEHAVIOR_MASTERY_THRESHOLD = 25  # Éxitos necesarios para dominar
    ADAPTATION_SPEED_INCREASE = 0.05  # Incremento de velocidad de adaptación
    
    # Debug y visualización
    DEBUG_MODE = True
    SHOW_LEARNING_PROGRESS = True

# ============================================
# VERIFICACIÓN CRÍTICA DE CONFIGURACIÓN
# ============================================

def verify_configuration():
    """Verifica que la configuración sea consistente."""
    issues = []
    
    # Verificar PATTERN_SIZE
    if NEURON657_AVAILABLE:
        try:
            from neuron657 import NPF657Pattern
            neuron_pattern_size = NPF657Pattern.SIZE
            if GameConfig.PATTERN_SIZE != neuron_pattern_size:
                issues.append(f"PATTERN_SIZE mismatch: Game={GameConfig.PATTERN_SIZE}, Neuron657={neuron_pattern_size}")
        except:
            issues.append("No se pudo verificar PATTERN_SIZE de Neuron657")
    
    # Verificar que el archivo de memoria sea accesible
    memory_file = GameConfig.MEMORY_FILE
    if os.path.exists(memory_file):
        try:
            with open(memory_file, 'rb') as f:
                f.read(1)
        except Exception as e:
            issues.append(f"No se puede leer archivo de memoria: {e}")
    
    # Verificar tamaños mínimos
    if GameConfig.EPISODIC_MEMORY_SIZE < 10:
        issues.append("EPISODIC_MEMORY_SIZE demasiado pequeño")
    
    if GameConfig.LEARNING_RATE <= 0 or GameConfig.LEARNING_RATE > 1:
        issues.append("LEARNING_RATE fuera de rango (0,1]")
    
    if issues:
        print("⚠️  ADVERTENCIAS DE CONFIGURACIÓN:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    return True

# ============================================
# COMPORTAMIENTOS DE LA MÁQUINA - AÑADIDOS NUEVOS
# ============================================

class AIBehavior(Enum):
    """Diferentes comportamientos pre-programados para la máquina."""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    EVASIVE = "evasive"
    PATTERN_A = "pattern_a"
    PATTERN_B = "pattern_b"
    RANDOM = "random"
    CIRCLE = "circle"
    CHARGE = "charge"
    SNIPER = "sniper"
    TURTLE = "turtle"
    # NUEVOS COMPORTAMIENTOS
    ADAPTIVE = "adaptive"        # Cambia entre comportamientos
    FEINT = "feint"              # Finta y contraataca
    VORTEX = "vortex"            # Movimiento en espiral
    SHADOW = "shadow"            # Imita al NPC
    BERSERK = "berserk"          # Velocidad y daño aumentados con baja salud
    TACTICIAN = "tactician"      # Analiza patrones del NPC

# ============================================
# SISTEMA DE METAS ADAPTATIVO MEJORADO
# ============================================

class AdvancedGoalSystem:
    """Sistema de metas dinámico con memoria de éxito."""
    
    def __init__(self):
        self.goals = {
            "survival": {
                "priority": 1.0, 
                "active": True, 
                "drive": 0.0,
                "success_rate": 0.5,
                "usage_count": 0
            },
            "damage_dealt": {
                "priority": 0.9, 
                "active": True, 
                "drive": 0.0,
                "success_rate": 0.5,
                "usage_count": 0
            },
            "pattern_learning": {
                "priority": 1.3, 
                "active": True, 
                "drive": 0.0,
                "success_rate": 0.5,
                "usage_count": 0
            },
            "adaptation_speed": {
                "priority": 1.2, 
                "active": True, 
                "drive": 0.0,
                "success_rate": 0.5,
                "usage_count": 0
            },
            "energy_efficiency": {
                "priority": 0.8, 
                "active": False, 
                "drive": 0.0,
                "success_rate": 0.5,
                "usage_count": 0
            },
            "prediction_accuracy": {
                "priority": 1.1,
                "active": True,
                "drive": 0.0,
                "success_rate": 0.5,
                "usage_count": 0
            }
        }
        
        # Mapa mejorado de comportamientos a metas
        self.behavior_goal_map = {
            AIBehavior.AGGRESSIVE: ["survival", "damage_dealt", "prediction_accuracy"],
            AIBehavior.DEFENSIVE: ["pattern_learning", "energy_efficiency", "survival"],
            AIBehavior.EVASIVE: ["adaptation_speed", "pattern_learning", "prediction_accuracy"],
            AIBehavior.PATTERN_A: ["pattern_learning", "damage_dealt", "prediction_accuracy"],
            AIBehavior.PATTERN_B: ["pattern_learning", "adaptation_speed", "damage_dealt"],
            AIBehavior.RANDOM: ["adaptation_speed", "survival", "pattern_learning"],
            AIBehavior.CIRCLE: ["pattern_learning", "prediction_accuracy", "damage_dealt"],
            AIBehavior.CHARGE: ["survival", "adaptation_speed", "damage_dealt"],
            AIBehavior.SNIPER: ["pattern_learning", "energy_efficiency", "prediction_accuracy"],
            AIBehavior.TURTLE: ["damage_dealt", "pattern_learning", "energy_efficiency"],
            AIBehavior.ADAPTIVE: ["adaptation_speed", "pattern_learning", "prediction_accuracy"],
            AIBehavior.FEINT: ["prediction_accuracy", "adaptation_speed", "damage_dealt"],
            AIBehavior.VORTEX: ["pattern_learning", "prediction_accuracy", "adaptation_speed"],
            AIBehavior.SHADOW: ["pattern_learning", "adaptation_speed", "prediction_accuracy"],
            AIBehavior.BERSERK: ["damage_dealt", "survival", "adaptation_speed"],
            AIBehavior.TACTICIAN: ["pattern_learning", "prediction_accuracy", "adaptation_speed"]
        }
        
        self.history = deque(maxlen=100)
        self.last_adjustment_time = time.time()
    
    def adjust_for_behavior(self, behavior: AIBehavior, outcome: dict):
        """Ajusta metas basado en comportamiento y resultado."""
        behavior_key = behavior.value
        
        # Decaimiento natural de drives
        for goal in self.goals.values():
            goal["drive"] *= 0.93
        
        # Activar metas relevantes
        relevant_goals = self.behavior_goal_map.get(behavior, ["survival", "adaptation_speed"])
        
        for goal_name in relevant_goals:
            if goal_name in self.goals:
                goal = self.goals[goal_name]
                goal["drive"] += 0.15
                goal["active"] = True
                goal["usage_count"] += 1
        
        # Ajuste basado en resultado
        success = outcome.get("success", False)
        damage_ratio = outcome.get("damage_ratio", 1.0)
        survival_bonus = 1.0 if outcome.get("survived", False) else 0.0
        
        if success:
            # Reforzar metas que llevaron al éxito
            for goal_name in relevant_goals:
                if goal_name in self.goals:
                    goal = self.goals[goal_name]
                    goal["success_rate"] = min(1.0, goal["success_rate"] + 0.05)
                    goal["drive"] += 0.1 * goal["success_rate"]
        else:
            # Ajustar prioridades basado en fracaso
            if damage_ratio < 0.5:  # Recibió mucho daño
                self.goals["survival"]["drive"] += 0.3
                self.goals["energy_efficiency"]["drive"] += 0.2
                self.goals["energy_efficiency"]["active"] = True
        
        # Añadir bonus por supervivencia
        if survival_bonus > 0:
            self.goals["survival"]["drive"] += 0.2 * survival_bonus
        
        # Registrar en historial
        self.history.append({
            "timestamp": time.time(),
            "behavior": behavior_key,
            "outcome": outcome,
            "active_goal": self.get_active_goal()
        })
        
        self.last_adjustment_time = time.time()
    
    def get_active_goal(self) -> str:
        """Devuelve la meta con mayor drive ajustado por éxito."""
        active_goals = {k: v for k, v in self.goals.items() if v["active"]}
        if not active_goals:
            return "survival"
        
        # Score = drive * success_rate
        scored_goals = {}
        for name, goal in active_goals.items():
            score = goal["drive"] * (0.7 + 0.3 * goal["success_rate"])
            scored_goals[name] = score
        
        return max(scored_goals.keys(), key=lambda k: scored_goals[k])
    
    def get_goal_drive(self, goal_name: str) -> float:
        """Obtiene el drive de una meta específica."""
        return self.goals.get(goal_name, {}).get("drive", 0.0)
    
    def get_goal_success_rate(self, goal_name: str) -> float:
        """Obtiene la tasa de éxito de una meta."""
        return self.goals.get(goal_name, {}).get("success_rate", 0.5)
    
    def reset(self):
        """Resetea drives pero mantiene tasas de éxito."""
        for goal in self.goals.values():
            goal["drive"] = 0.0
            goal["active"] = goal["priority"] > 1.0
    
    def get_stats(self) -> dict:
        """Devuelve estadísticas del sistema de metas."""
        return {
            "total_goals": len(self.goals),
            "active_goals": sum(1 for g in self.goals.values() if g["active"]),
            "history_size": len(self.history),
            "success_rates": {k: v["success_rate"] for k, v in self.goals.items()}
        }

# ============================================
# NPC SUPER-INTELIGENTE MEJORADO
# ============================================

class SuperIntelligentNPC:
    """NPC con aprendizaje REAL y sistemas de inteligencia avanzados."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = GameConfig.NPC_COLOR
        self.radius = 32  # Un poco más grande
        self.health = 100
        self.max_health = 100
        
        # Estado de combate
        self.attacking = False
        self.defending = False
        self.attack_cooldown = 0
        self.attack_direction = (0, 0)
        
        # Movimiento
        self.vx = 0
        self.vy = 0
        self.speed = GameConfig.NPC_SPEED
        
        # ===== SISTEMA DE CEREBRO MEJORADO =====
        self.brain = None
        self.brain_initialized = False
        self.learning_enabled = NEURON657_AVAILABLE
        
        # Estado de aprendizaje
        self.current_state = None
        self.last_state = None
        self.last_action_hash = None
        self.reward_history = deque(maxlen=1000)
        self.learning_rate = GameConfig.LEARNING_RATE
        
        # Memoria específica por comportamiento
        self.behavior_memory = {}
        self.current_ai_behavior = None
        
        # Estadísticas
        self.attacks_made = 0
        self.attacks_hit = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.successful_defenses = 0
        
        # Para seguimiento visual
        self.thought_bubble = ""
        self.thought_timer = 0
        self.insight_bubble = ""
        self.insight_timer = 0
        self.debug_bubble = ""
        self.debug_timer = 0
        
        # Decision making mejorado
        self.decision_confidence = 0.6
        self.exploration_rate = 0.35
        self.adaptation_speed = 0.15
        
        # Para visualización
        self.last_action = "Inicializando..."
        self.action_timer = 0
        
        # ===== SISTEMAS AVANZADOS =====
        
        # Sistema de metas mejorado
        self.goal_system = AdvancedGoalSystem()
        
        # Memoria episódica persistente
        self.episodic_memory = deque(maxlen=GameConfig.EPISODIC_MEMORY_SIZE)
        self.current_episode = []
        
        # Aprendizaje por imitación mejorado
        self.observation_window = deque(maxlen=100)
        self.last_observed_behavior = None
        self.learned_counter_patterns = defaultdict(list)
        
        # Sistema de hipótesis mejorado
        self.active_hypotheses = []
        self.tested_hypotheses = deque(maxlen=200)
        self.hypothesis_success_rate = 0.5
        
        # Metacognición mejorada
        self.learning_effectiveness = 0.6
        self.pattern_recognition_threshold = GameConfig.PATTERN_RECOGNITION_THRESHOLD
        self.meta_learning_counter = 0
        
        # Transferencia de conocimiento mejorada
        self.knowledge_base = {}
        self.similar_behaviors = {
            AIBehavior.AGGRESSIVE: [AIBehavior.CHARGE, AIBehavior.PATTERN_A, AIBehavior.BERSERK],
            AIBehavior.DEFENSIVE: [AIBehavior.TURTLE, AIBehavior.SNIPER, AIBehavior.TACTICIAN],
            AIBehavior.EVASIVE: [AIBehavior.CIRCLE, AIBehavior.PATTERN_B, AIBehavior.VORTEX],
            AIBehavior.CIRCLE: [AIBehavior.EVASIVE, AIBehavior.PATTERN_B, AIBehavior.VORTEX],
            AIBehavior.CHARGE: [AIBehavior.AGGRESSIVE, AIBehavior.PATTERN_A, AIBehavior.BERSERK],
            AIBehavior.SNIPER: [AIBehavior.DEFENSIVE, AIBehavior.TACTICIAN, AIBehavior.TURTLE],
            AIBehavior.TURTLE: [AIBehavior.DEFENSIVE, AIBehavior.SNIPER, AIBehavior.TACTICIAN],
            AIBehavior.ADAPTIVE: [AIBehavior.TACTICIAN, AIBehavior.EVASIVE, AIBehavior.SHADOW],
            AIBehavior.FEINT: [AIBehavior.EVASIVE, AIBehavior.PATTERN_B, AIBehavior.ADAPTIVE],
            AIBehavior.VORTEX: [AIBehavior.CIRCLE, AIBehavior.EVASIVE, AIBehavior.PATTERN_B],
            AIBehavior.SHADOW: [AIBehavior.ADAPTIVE, AIBehavior.TACTICIAN, AIBehavior.EVASIVE],
            AIBehavior.BERSERK: [AIBehavior.AGGRESSIVE, AIBehavior.CHARGE, AIBehavior.PATTERN_A],
            AIBehavior.TACTICIAN: [AIBehavior.ADAPTIVE, AIBehavior.SHADOW, AIBehavior.DEFENSIVE]
        }
        
        # Historial de acciones
        self.action_history = deque(maxlen=50)
        self.behavior_transition_history = []
        
        # Contadores de aprendizaje
        self.total_learning_cycles = 0
        self.successful_adaptations = 0
        self.failed_adaptations = 0
        
        # Sistema de especialización
        self.behavior_mastery = {behavior.value: 0 for behavior in AIBehavior}
        self.specialized_behaviors = []
        
        # Sistema de guardado automático
        self.last_save_time = time.time()
        self.save_interval = 30  # Guardar cada 30 segundos
        self.auto_save_enabled = True
        
        # Debug y monitoreo
        self.learning_debug_log = deque(maxlen=20)
        
        # Inicializar cerebro
        self.initialize_brain()
        
        # Verificar configuración
        if not verify_configuration():
            print("⚠️  Problemas de configuración detectados. Aprendizaje puede ser afectado.")
        
        print("🧠 NPC SUPER-INTELIGENTE INICIALIZADO")
        print(f"   • Cerebro: {'✅ INICIALIZADO' if self.brain_initialized else '❌ FALLÓ'}")
        print(f"   • Tasa aprendizaje: {self.learning_rate:.2f}")
        print(f"   • Confianza inicial: {self.decision_confidence:.2f}")
    
    def initialize_brain(self):
        """Inicializa el cerebro con persistencia mejorada."""
        if not self.learning_enabled:
            print("❌ Aprendizaje deshabilitado - Neuron657 no disponible")
            self.brain_initialized = False
            return False
        
        try:
            memory_file = GameConfig.MEMORY_FILE
            
            # Verificar si existe memoria previa
            memory_exists = os.path.exists(memory_file)
            compactstore_exists = os.path.exists(memory_file + ".compactstore")
            index_exists = os.path.exists(memory_file + ".index")
            
            if memory_exists and compactstore_exists and index_exists:
                print(f"🧠 Cargando cerebro existente desde: {memory_file}")
                print(f"   • Tamaño archivo: {os.path.getsize(memory_file):,} bytes")
                print(f"   • CompactStore: {'✅' if compactstore_exists else '❌'}")
                print(f"   • Índice: {'✅' if index_exists else '❌'}")
                
                try:
                    self.brain = Neuron657Core(
                        memory_file,
                        total_size=8 * 1024 * 1024  # 8MB para más capacidad
                    )
                    self.brain_initialized = True
                    print("✅ Cerebro cargado exitosamente")
                    
                    # Analizar experiencia previa
                    self._analyze_existing_memory()
                    
                    # Cargar conocimiento transferido
                    self._load_transferred_knowledge()
                    
                    # Actualizar parámetros basados en experiencia
                    self._update_parameters_from_memory()
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ Error cargando cerebro: {e}")
                    print("🧠 Creando nuevo cerebro...")
                    # Continuar con creación nueva
            
            # Crear nuevo cerebro
            print("🧠 Inicializando NUEVO cerebro NPC super-inteligente...")
            self.brain = Neuron657Core(
                memory_file,
                total_size=8 * 1024 * 1024
            )
            
            # Inicializar conocimiento avanzado
            self._initialize_advanced_knowledge()
            
            self.brain_initialized = True
            print("✅ Nuevo cerebro inicializado con conocimiento avanzado")
            
            # Configurar modo cognitivo
            self.brain.set_mode("autonomous")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR CRÍTICO inicializando cerebro: {e}")
            import traceback
            traceback.print_exc()
            self.brain = None
            self.brain_initialized = False
            return False
    
    def _initialize_advanced_knowledge(self):
        """Inicializa conocimiento avanzado de combate."""
        if not self.brain:
            return
        
        try:
            # Crear metas cognitivas avanzadas
            goals = [
                Goal657("observar_patrones", "machine_pattern", priority=1.5),
                Goal657("transferir_conocimiento", "similar_behavior", priority=1.4),
                Goal657("generar_hipotesis", "uncertain_situation", priority=1.3),
                Goal657("meta_aprendizaje", "learning_opportunity", priority=1.6),
                Goal657("eficiencia_energetica", "low_health", priority=1.2),
                Goal657("prediccion_precisa", "predictive_situation", priority=1.4),
                Goal657("adaptacion_rapida", "new_behavior", priority=1.5)
            ]
            
            for goal in goals:
                self.brain.add_goal(goal)
            
            # Patrones fundamentales de combate
            fundamental_patterns = [
                (b"predict_movement_01", ["prediction", "movement", "fundamental"], "anticipate"),
                (b"counter_attack_01", ["counter", "attack", "fundamental"], "counter_attack"),
                (b"defensive_position", ["defense", "position", "fundamental"], "defend"),
                (b"distance_control", ["distance", "control", "fundamental"], "control_range"),
                (b"pattern_interrupt", ["interrupt", "pattern", "fundamental"], "interrupt"),
                (b"timing_attack", ["timing", "attack", "fundamental"], "timed_attack")
            ]
            
            for data, tags, action in fundamental_patterns:
                try:
                    pattern = NPF657Pattern(
                        data=data.ljust(GameConfig.PATTERN_SIZE, b'\x00')[:GameConfig.PATTERN_SIZE],
                        tags=tags + [f"action_{action}", "npc_fundamental"]
                    )
                    self.brain.nip.STORE_PATTERN(pattern)
                except Exception as e:
                    print(f"⚠️  Error almacenando patrón fundamental: {e}")
            
            print(f"✅ Conocimiento fundamental inicializado: {len(fundamental_patterns)} patrones")
            
        except Exception as e:
            print(f"⚠️  Error inicializando conocimiento avanzado: {e}")
    
    def _analyze_existing_memory(self):
        """Analiza la memoria existente para ajustar parámetros."""
        if not self.brain:
            return
        
        try:
            # Intentar obtener estadísticas de la memoria
            total_patterns = 0
            try:
                # Buscar patrones NPC para estimar experiencia
                test_pattern = NPF657Pattern(
                    data=b"npc_pattern".ljust(GameConfig.PATTERN_SIZE, b'\x00'),
                    tags=["npc_pattern"]
                )
                search_result = self.brain.nip.SEARCH_SIMILAR(test_pattern, limit=100).result()
                if search_result.get('ok'):
                    total_patterns = len(search_result.get('results', []))
            except:
                pass
            
            # Ajustar parámetros basado en experiencia estimada
            if total_patterns > 50:
                experience_level = min(1.0, total_patterns / 500)
                self.decision_confidence = min(0.95, 0.5 + experience_level * 0.4)
                self.exploration_rate = max(0.15, 0.4 - experience_level * 0.3)
                self.learning_effectiveness = min(0.98, 0.4 + experience_level * 0.5)
                self.adaptation_speed = min(0.3, 0.1 + experience_level * 0.2)
                
                print(f"📊 Experiencia detectada: ~{total_patterns} patrones")
                print(f"   • Confianza ajustada a: {self.decision_confidence:.2f}")
                print(f"   • Exploración ajustada a: {self.exploration_rate:.2f}")
                print(f"   • Efectividad ajustada a: {self.learning_effectiveness:.2f}")
            
        except Exception as e:
            print(f"⚠️  Error analizando memoria existente: {e}")
    
    def _load_transferred_knowledge(self):
        """Carga conocimiento transferido de sesiones anteriores."""
        if not self.brain_initialized:
            return
        
        try:
            # Buscar patrones de transferencia
            transfer_pattern = NPF657Pattern(
                data=b"knowledge_transfer".ljust(GameConfig.PATTERN_SIZE, b'\x00'),
                tags=["transfer", "knowledge", "npc_learned"]
            )
            
            search_result = self.brain.nip.SEARCH_SIMILAR(transfer_pattern, limit=50).result()
            
            if search_result.get('ok') and search_result['results']:
                loaded_transfers = 0
                for result in search_result['results']:
                    try:
                        # Cargar información del patrón
                        cid = result.get('cid')
                        offset = result.get('offset')
                        if cid is None or offset is None:
                            continue
                        
                        pattern = self.brain.memory.load_pattern_compacted(cid, offset)
                        
                        # Extraer información de transferencia de tags
                        for tag in pattern.tags:
                            if tag.startswith("transfer_"):
                                parts = tag.replace("transfer_", "").split("_to_")
                                if len(parts) == 2:
                                    from_behav, to_behav = parts
                                    transfer_key = f"{from_behav}_to_{to_behav}"
                                    
                                    if transfer_key not in self.knowledge_base:
                                        self.knowledge_base[transfer_key] = {
                                            "count": 0,
                                            "success_rate": 0.5,
                                            "last_used": 0
                                        }
                                    
                                    self.knowledge_base[transfer_key]["count"] += 1
                                    loaded_transfers += 1
                    except:
                        continue
                
                if loaded_transfers > 0:
                    print(f"📚 Conocimiento transferido cargado: {loaded_transfers} transferencias")
            
        except Exception as e:
            print(f"⚠️  Error cargando conocimiento transferido: {e}")
    
    def _update_parameters_from_memory(self):
        """Actualiza parámetros basados en análisis de memoria."""
        try:
            # Analizar éxito histórico basado en patrones de aprendizaje
            success_pattern = NPF657Pattern(
                data=b"learning_success".ljust(GameConfig.PATTERN_SIZE, b'\x00'),
                tags=["learning", "success", "npc_learned"]
            )
            
            fail_pattern = NPF657Pattern(
                data=b"learning_fail".ljust(GameConfig.PATTERN_SIZE, b'\x00'),
                tags=["learning", "fail", "npc_learned"]
            )
            
            success_search = self.brain.nip.SEARCH_SIMILAR(success_pattern, limit=20).result()
            fail_search = self.brain.nip.SEARCH_SIMILAR(fail_pattern, limit=20).result()
            
            success_count = len(success_search.get('results', []))
            fail_count = len(fail_search.get('results', []))
            
            total_attempts = success_count + fail_count
            if total_attempts > 0:
                historical_success_rate = success_count / total_attempts
                # Ajustar confianza basada en éxito histórico
                self.decision_confidence = min(0.95, max(0.3, historical_success_rate))
                print(f"📈 Éxito histórico: {historical_success_rate:.2%}")
                print(f"   • Confianza ajustada a: {self.decision_confidence:.2f}")
            
        except Exception as e:
            print(f"⚠️  Error actualizando parámetros desde memoria: {e}")
    
    # ============================================
    # SISTEMA DE OBSERVACIÓN E IMITACIÓN MEJORADO
    # ============================================
    
    def observe_machine_patterns(self, machine):
        """Observa y aprende de los patrones de la máquina en tiempo real."""
        if machine.behavior != self.last_observed_behavior:
            self.last_observed_behavior = machine.behavior
            self.observation_window.clear()
            self.thought_bubble = f"Observando nuevo comportamiento: {machine.behavior.value}"
            self.thought_timer = 60
        
        # Capturar observación detallada
        observation = {
            'timestamp': time.time(),
            'behavior': machine.behavior.value,
            'state': machine.state,
            'action': machine.last_action,
            'position': (machine.x, machine.y),
            'velocity': (machine.vx, machine.vy),
            'attacking': machine.attacking,
            'defending': machine.defending,
            'health': machine.health,
            'npc_health': self.health,
            'distance': math.sqrt((machine.x - self.x)**2 + (machine.y - self.y)**2)
        }
        
        self.observation_window.append(observation)
        
        # Detectar patrones después de suficientes observaciones
        if len(self.observation_window) >= 15:
            detected_patterns = self._detect_repetitive_patterns()
            new_patterns_count = 0
            
            for pattern in detected_patterns:
                if self._learn_counter_pattern(pattern, machine.behavior):
                    new_patterns_count += 1
            
            if new_patterns_count > 0:
                self.insight_bubble = f"🎯 {new_patterns_count} nuevo(s) patrón(es) detectado(s)!"
                self.insight_timer = 90
                
                # Recompensa por detección de patrones
                self._add_reward(0.3, "pattern_detection")
    
    def _detect_repetitive_patterns(self):
        """Detecta patrones repetitivos con algoritmo mejorado."""
        if len(self.observation_window) < 8:
            return []
        
        patterns = []
        window_list = list(self.observation_window)
        
        # Usar ventana deslizante para detectar patrones de 3 a 7 pasos
        for pattern_length in range(3, 8):
            for start_idx in range(len(window_list) - pattern_length * 2 + 1):
                seq1 = window_list[start_idx:start_idx + pattern_length]
                seq2 = window_list[start_idx + pattern_length:start_idx + pattern_length * 2]
                
                # Calcular similitud mejorada
                similarity = self._calculate_enhanced_similarity(seq1, seq2)
                
                if similarity > self.pattern_recognition_threshold:
                    pattern = {
                        'actions': [obs['action'] for obs in seq1],
                        'states': [obs['state'] for obs in seq1],
                        'positions': [obs['position'] for obs in seq1],
                        'length': pattern_length,
                        'confidence': similarity,
                        'behavior': seq1[0]['behavior'],
                        'timestamp': time.time(),
                        'detection_count': 1
                    }
                    
                    # Verificar si es un patrón único
                    if not self._is_duplicate_pattern(pattern, patterns):
                        patterns.append(pattern)
        
        return patterns
    
    def _calculate_enhanced_similarity(self, seq1, seq2):
        """Calcula similitud mejorada considerando múltiples factores."""
        if len(seq1) != len(seq2):
            return 0.0
        
        total_score = 0
        max_score = 0
        
        for obs1, obs2 in zip(seq1, seq2):
            # Acción (peso 0.4)
            if obs1['action'] == obs2['action']:
                total_score += 0.4
            
            # Estado (peso 0.3)
            if obs1['state'] == obs2['state']:
                total_score += 0.3
            
            # Posición relativa similar (peso 0.3)
            pos1 = obs1['position']
            pos2 = obs2['position']
            distance = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
            if distance < 50:  # Posiciones similares
                total_score += 0.3
            
            max_score += 1.0
        
        return total_score / max_score if max_score > 0 else 0.0
    
    def _is_duplicate_pattern(self, new_pattern, existing_patterns, threshold=0.8):
        """Verifica si un patrón es similar a uno existente."""
        for pattern in existing_patterns:
            # Comparar acciones
            if pattern['actions'] == new_pattern['actions']:
                return True
            
            # Comparar similitud general
            similarity = 0
            min_len = min(len(pattern['actions']), len(new_pattern['actions']))
            matches = sum(1 for i in range(min_len) if pattern['actions'][i] == new_pattern['actions'][i])
            similarity = matches / max(len(pattern['actions']), len(new_pattern['actions']))
            
            if similarity > threshold:
                return True
        
        return False
    
    def _learn_counter_pattern(self, pattern, behavior):
        """Aprende y almacena un patrón de contraataque."""
        behavior_key = behavior.value
        
        # Verificar si el patrón ya fue aprendido
        existing_idx = -1
        for i, existing in enumerate(self.learned_counter_patterns[behavior_key]):
            if existing['actions'] == pattern['actions']:
                existing_idx = i
                break
        
        if existing_idx >= 0:
            # Actualizar patrón existente
            existing = self.learned_counter_patterns[behavior_key][existing_idx]
            existing['confidence'] = max(existing['confidence'], pattern['confidence'])
            existing['detection_count'] = existing.get('detection_count', 0) + 1
            existing['last_updated'] = time.time()
            
            # Mejorar tasa de éxito si se usa bien
            if existing.get('usage_count', 0) > 0:
                success_rate = existing.get('success_rate', 0.5)
                existing['success_rate'] = min(1.0, success_rate + 0.05)
            
            # Guardar en memoria permanente
            self._store_pattern_in_memory(existing, behavior, is_update=True)
            
            return False
        else:
            # Nuevo patrón
            pattern['learned_at'] = time.time()
            pattern['usage_count'] = 0
            pattern['success_rate'] = 0.5
            pattern['success_history'] = deque(maxlen=10)
            
            self.learned_counter_patterns[behavior_key].append(pattern)
            
            # Almacenar en memoria permanente
            storage_success = self._store_pattern_in_memory(pattern, behavior, is_update=False)
            
            if storage_success:
                # Mostrar insight
                self.insight_bubble = f"🎯 Nuevo patrón vs {behavior_key}!"
                self.insight_timer = 90
                
                # Registrar en debug
                self._log_learning_event(f"Nuevo patrón aprendido: {behavior_key} - {pattern['actions']}")
                
                print(f"🧠 Nuevo patrón aprendido para {behavior_key}: {pattern['actions']}")
                return True
        
        return False
    
    def _store_pattern_in_memory(self, pattern, behavior, is_update=False):
        """Almacena un patrón aprendido en Neuron657 de forma persistente."""
        if not self.brain_initialized:
            return False
        
        try:
            # Serializar patrón a JSON
            pattern_data = {
                'actions': pattern['actions'],
                'behavior': behavior.value,
                'confidence': pattern['confidence'],
                'learned_at': pattern.get('learned_at', time.time()),
                'usage_count': pattern.get('usage_count', 0),
                'success_rate': pattern.get('success_rate', 0.5)
            }
            
            json_str = json.dumps(pattern_data, separators=(',', ':'))
            json_bytes = json_str.encode('utf-8')
            
            # Asegurar tamaño correcto
            if len(json_bytes) > GameConfig.PATTERN_SIZE:
                json_bytes = json_bytes[:GameConfig.PATTERN_SIZE]
            else:
                json_bytes = json_bytes.ljust(GameConfig.PATTERN_SIZE, b'\x00')
            
            # Crear patrón Neuron657
            tags = [
                "npc_learned_pattern",
                f"behavior_{behavior.value}",
                f"actions_{len(pattern['actions'])}",
                f"confidence_{pattern['confidence']:.2f}",
                f"success_{pattern.get('success_rate', 0.5):.2f}",
                f"usage_{pattern.get('usage_count', 0)}"
            ]
            
            if is_update:
                tags.append("updated")
            else:
                tags.append("new")
            
            n657_pattern = NPF657Pattern(
                data=json_bytes,
                tags=tags
            )
            
            # Almacenar patrón
            store_result = self.brain.nip.STORE_PATTERN(n657_pattern)
            
            if store_result.get('ok'):
                # Si es nuevo, asociar con comportamiento
                if not is_update:
                    behavior_pattern = NPF657Pattern(
                        data=behavior.value.encode('utf-8').ljust(GameConfig.PATTERN_SIZE, b'\x00'),
                        tags=[f"behavior_{behavior.value}", "meta", "reference"]
                    )
                    behavior_result = self.brain.nip.STORE_PATTERN(behavior_pattern)
                    
                    if behavior_result.get('ok'):
                        self.brain.nip.ASSOCIATE(
                            behavior_result['hash'],
                            store_result['hash']
                        )
                
                return True
            else:
                print(f"⚠️  Error almacenando patrón en Neuron657")
                return False
            
        except Exception as e:
            print(f"❌ Error almacenando patrón: {e}")
            return False
    
    # ============================================
    # SISTEMA DE GENERACIÓN DE HIPÓTESIS MEJORADO
    # ============================================
    
    def generate_hypotheses(self, machine, current_situation):
        """Genera hipótesis inteligentes basadas en múltiples factores."""
        hypotheses = []
        behavior = machine.behavior
        
        # Factor 1: Análisis de daño
        damage_ratio = self.damage_dealt / max(1, self.damage_taken)
        
        if damage_ratio < 0.5:
            hypotheses.append({
                'id': len(self.tested_hypotheses) + 1,
                'type': 'damage_recovery',
                'action': 'defensive_repositioning',
                'confidence': 0.8 - (damage_ratio * 0.3),
                'reason': f'Ratio daño desfavorable ({damage_ratio:.2f})',
                'expected_outcome': 'reduce_damage_taken',
                'test_count': 0,
                'priority': 1.5
            })
        
        # Factor 2: Análisis de comportamiento específico
        behavior_hypotheses = self._generate_behavior_specific_hypotheses(behavior, machine)
        hypotheses.extend(behavior_hypotheses)
        
        # Factor 3: Análisis de salud
        if self.health < 40:
            hypotheses.append({
                'id': len(self.tested_hypotheses) + 1,
                'type': 'survival_critical',
                'action': 'evasive_survival',
                'confidence': 0.95,
                'reason': f'Salud crítica ({self.health:.0f}/100)',
                'expected_outcome': 'survive_and_recover',
                'test_count': 0,
                'priority': 2.0  # Alta prioridad
            })
        
        # Factor 4: Análisis de patrones aprendidos
        if behavior.value in self.learned_counter_patterns:
            patterns = self.learned_counter_patterns[behavior.value]
            if patterns:
                best_pattern = max(patterns, key=lambda p: p['confidence'] * p.get('success_rate', 0.5))
                if best_pattern['confidence'] > 0.6:
                    hypotheses.append({
                        'id': len(self.tested_hypotheses) + 1,
                        'type': 'pattern_application',
                        'action': 'apply_best_pattern',
                        'confidence': best_pattern['confidence'],
                        'reason': f'Patrón confiable disponible (conf: {best_pattern["confidence"]:.2f})',
                        'expected_outcome': 'successful_counter',
                        'pattern_id': hash(tuple(best_pattern['actions'])),
                        'test_count': 0,
                        'priority': 1.2
                    })
        
        # Factor 5: Transferencia de conocimiento
        transfer_hypotheses = self._generate_transfer_hypotheses(behavior)
        hypotheses.extend(transfer_hypotheses)
        
        # Ordenar por prioridad y confianza
        for hyp in hypotheses:
            hyp['score'] = hyp.get('priority', 1.0) * hyp['confidence']
        
        hypotheses.sort(key=lambda x: x['score'], reverse=True)
        
        return hypotheses[:10]  # Limitar a 10 hipótesis
    
    def _generate_behavior_specific_hypotheses(self, behavior, machine):
        """Genera hipótesis específicas para cada comportamiento."""
        hypotheses = []
        
        if behavior == AIBehavior.SNIPER:
            current_distance = math.sqrt((machine.x - self.x)**2 + (machine.y - self.y)**2)
            if current_distance > 200:
                hypotheses.append({
                    'type': 'sniper_closure',
                    'action': 'aggressive_closure',
                    'confidence': 0.85,
                    'reason': 'Sniper mantiene distancia excesiva',
                    'expected_outcome': 'force_close_combat',
                    'priority': 1.3
                })
        
        elif behavior == AIBehavior.TURTLE:
            if not machine.defending and self.attack_cooldown == 0:
                hypotheses.append({
                    'type': 'turtle_exploit',
                    'action': 'timed_attack',
                    'confidence': 0.75,
                    'reason': 'Turtle no está defendiendo',
                    'expected_outcome': 'successful_attack',
                    'priority': 1.4
                })
        
        elif behavior == AIBehavior.CIRCLE:
            # Predecir movimiento circular
            if hasattr(machine, 'target_angle'):
                predicted_angle = machine.target_angle + 0.25
                hypotheses.append({
                    'type': 'circle_intercept',
                    'action': 'predictive_intercept',
                    'confidence': 0.7,
                    'reason': 'Movimiento circular predecible',
                    'expected_outcome': 'successful_intercept',
                    'predicted_angle': predicted_angle,
                    'priority': 1.2
                })
        
        elif behavior == AIBehavior.ADAPTIVE:
            hypotheses.append({
                'type': 'adaptive_disruption',
                'action': 'unpredictable_movement',
                'confidence': 0.65,
                'reason': 'Comportamiento adaptativo requiere variabilidad',
                'expected_outcome': 'disrupt_adaptation',
                'priority': 1.1
            })
        
        # Añadir ID a cada hipótesis
        for i, hyp in enumerate(hypotheses):
            hyp['id'] = len(self.tested_hypotheses) + i + 1
            hyp['test_count'] = 0
        
        return hypotheses
    
    def _generate_transfer_hypotheses(self, behavior):
        """Genera hipótesis basadas en transferencia de conocimiento."""
        hypotheses = []
        
        if behavior in self.similar_behaviors:
            similar_behaviors = self.similar_behaviors[behavior]
            
            for similar_behavior in similar_behaviors:
                transfer_key = f"{similar_behavior.value}_to_{behavior.value}"
                
                if transfer_key in self.knowledge_base:
                    kb = self.knowledge_base[transfer_key]
                    success_rate = kb.get('success_rate', 0.5)
                    
                    if success_rate > 0.6:
                        hypotheses.append({
                            'type': 'knowledge_transfer',
                            'action': 'apply_transferred_knowledge',
                            'confidence': success_rate,
                            'reason': f'Conocimiento transferible de {similar_behavior.value}',
                            'expected_outcome': 'leverage_existing_knowledge',
                            'source_behavior': similar_behavior.value,
                            'transfer_success_rate': success_rate,
                            'priority': 1.4  # Prioridad media-alta
                        })
        
        return hypotheses
    
    def select_best_hypothesis(self, hypotheses):
        """Selecciona la mejor hipótesis considerando múltiples factores."""
        if not hypotheses:
            return None
        
        for hyp in hypotheses:
            # Calcular score combinado
            base_score = hyp['confidence']
            
            # Penalizar hipótesis probadas muchas veces
            test_penalty = min(0.5, hyp.get('test_count', 0) * 0.1)
            
            # Bonus por prioridad
            priority_bonus = (hyp.get('priority', 1.0) - 1.0) * 0.2
            
            # Bonus por novedad (si no ha sido probada)
            novelty_bonus = 0.3 if hyp.get('test_count', 0) == 0 else 0
            
            # Bonus por tipo (transferencia tiene bonus)
            type_bonus = 0.15 if hyp['type'] == 'knowledge_transfer' else 0
            
            hyp['selection_score'] = (base_score - test_penalty + 
                                     priority_bonus + novelty_bonus + type_bonus)
        
        # Seleccionar hipótesis con mayor score
        best_hypothesis = max(hypotheses, key=lambda x: x['selection_score'])
        
        # Solo seleccionar si el score es razonable
        if best_hypothesis['selection_score'] > 0.4:
            return best_hypothesis
        
        return None
    
    def test_hypothesis(self, hypothesis, machine):
        """Prueba una hipótesis y evalúa resultados."""
        action_map = {
            'defensive_repositioning': self._execute_defensive_repositioning,
            'aggressive_closure': self._execute_aggressive_closure,
            'timed_attack': self._execute_timed_attack,
            'predictive_intercept': self._execute_predictive_intercept,
            'unpredictable_movement': self._execute_unpredictable_movement,
            'evasive_survival': self._execute_evasive_survival,
            'apply_best_pattern': self._execute_best_pattern,
            'apply_transferred_knowledge': self._execute_transfer_knowledge
        }
        
        action_func = action_map.get(hypothesis['action'])
        if action_func:
            # Registrar inicio de prueba
            hypothesis['test_start_time'] = time.time()
            hypothesis['initial_health'] = self.health
            hypothesis['initial_machine_health'] = machine.health
            
            # Ejecutar acción
            result = action_func(hypothesis, machine)
            
            # Registrar fin de prueba
            hypothesis['test_duration'] = time.time() - hypothesis['test_start_time']
            hypothesis['health_change'] = self.health - hypothesis['initial_health']
            hypothesis['machine_health_change'] = machine.health - hypothesis['initial_machine_health']
            
            # Actualizar contador
            hypothesis['test_count'] = hypothesis.get('test_count', 0) + 1
            hypothesis['last_test_time'] = time.time()
            hypothesis['last_result'] = result
            
            # Almacenar en historial
            self.tested_hypotheses.append(hypothesis.copy())
            
            # Mostrar en pantalla
            self.thought_bubble = f"🧪 Probando: {hypothesis['reason'][:25]}..."
            self.thought_timer = 60
            
            # Registrar en debug
            self._log_learning_event(f"Hipótesis probada: {hypothesis['type']} - {hypothesis['action']}")
            
            return result
        
        return None
    
    def _execute_defensive_repositioning(self, hypothesis, machine):
        """Ejecuta reposicionamiento defensivo."""
        # Calcular dirección segura
        dx = machine.x - self.x
        dy = machine.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 120:
            # Demasiado cerca, retroceder
            retreat_angle = math.atan2(dy, dx) + math.pi + random.uniform(-0.3, 0.3)
            retreat_distance = 150
            
            target_x = self.x + math.cos(retreat_angle) * retreat_distance
            target_y = self.y + math.sin(retreat_angle) * retreat_distance
            
            self.move_towards(target_x, target_y)
            self.defend()
        else:
            # Mantener distancia segura
            ideal_distance = 180
            if distance > ideal_distance + 30:
                self.move_towards(machine.x, machine.y)
            elif distance < ideal_distance - 30:
                self.move_away_from(machine.x, machine.y)
            else:
                # Movimiento lateral
                lateral_angle = math.atan2(dy, dx) + math.pi/2
                self.vx = math.cos(lateral_angle) * self.speed * 0.6
                self.vy = math.sin(lateral_angle) * self.speed * 0.6
        
        self.last_action = "HIPÓTESIS: REPOSICIONAMIENTO DEFENSIVO"
        return {"type": "defensive", "action": "reposition", "confidence": hypothesis['confidence']}
    
    def _execute_aggressive_closure(self, hypothesis, machine):
        """Cierra distancia agresivamente contra sniper."""
        self.move_towards(machine.x, machine.y)
        
        # Ataque rápido si está en rango
        dx = machine.x - self.x
        dy = machine.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
            direction = (dx/max(1, distance), dy/max(1, distance))
            if self.attack_cooldown == 0:
                self.attack(direction)
        
        self.last_action = "HIPÓTESIS: CIERRE AGRESIVO"
        return {"type": "aggressive", "action": "close_distance", "confidence": hypothesis['confidence']}
    
    def _execute_timed_attack(self, hypothesis, machine):
        """Ataque con tiempo contra turtle."""
        # Esperar momento oportuno
        if not machine.defending and self.attack_cooldown == 0:
            dx = machine.x - self.x
            dy = machine.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                direction = (dx/max(1, distance), dy/max(1, distance))
                self.attack(direction)
                
                # Retroceder después del ataque
                self.move_away_from(machine.x, machine.y)
        
        self.last_action = "HIPÓTESIS: ATAQUE CON TIEMPO"
        return {"type": "timed", "action": "opportunistic_attack", "confidence": hypothesis['confidence']}
    
    def _execute_predictive_intercept(self, hypothesis, machine):
        """Intercepta movimiento predecible."""
        if hasattr(machine, 'target_angle'):
            predicted_angle = hypothesis.get('predicted_angle', machine.target_angle + 0.25)
            intercept_distance = 120
            
            intercept_x = machine.x + math.cos(predicted_angle) * intercept_distance
            intercept_y = machine.y + math.sin(predicted_angle) * intercept_distance
            
            self.move_towards(intercept_x, intercept_y)
        else:
            # Interceptación genérica
            intercept_time = 0.4
            predicted_x = machine.x + machine.vx * intercept_time
            predicted_y = machine.y + machine.vy * intercept_time
            
            self.move_towards(predicted_x, predicted_y)
        
        self.last_action = "HIPÓTESIS: INTERCEPTACIÓN PREDICTIVA"
        return {"type": "predictive", "action": "intercept", "confidence": hypothesis['confidence']}
    
    def _execute_unpredictable_movement(self, hypothesis, machine):
        """Movimiento impredecible para desorientar."""
        # Cambiar dirección aleatoriamente
        if random.random() < 0.3:
            angle = random.uniform(0, math.pi * 2)
            self.vx = math.cos(angle) * self.speed * random.uniform(0.5, 1.0)
            self.vy = math.sin(angle) * self.speed * random.uniform(0.5, 1.0)
        
        # Ataque oportunista
        dx = machine.x - self.x
        dy = machine.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius and random.random() < 0.4:
            direction = (dx/max(1, distance), dy/max(1, distance))
            if self.attack_cooldown == 0:
                self.attack(direction)
        
        self.last_action = "HIPÓTESIS: MOVIMIENTO IMPREDECIBLE"
        return {"type": "unpredictable", "action": "random_movement", "confidence": hypothesis['confidence']}
    
    def _execute_evasive_survival(self, hypothesis, machine):
        """Supervivencia evasiva en salud crítica."""
        self.defend()
        
        # Retroceder en zigzag
        retreat_angle = math.atan2(machine.y - self.y, machine.x - self.x) + math.pi
        
        # Alternar entre zig y zag
        if int(time.time() * 2) % 2 == 0:
            retreat_angle += math.pi / 3  # Zig
        else:
            retreat_angle -= math.pi / 3  # Zag
        
        self.vx = math.cos(retreat_angle) * self.speed * 0.8
        self.vy = math.sin(retreat_angle) * self.speed * 0.8
        
        self.last_action = "HIPÓTESIS: SUPERVIVENCIA EVASIVA"
        return {"type": "survival", "action": "evasive_retreat", "confidence": hypothesis['confidence']}
    
    def _execute_best_pattern(self, hypothesis, machine):
        """Aplica el mejor patrón aprendido."""
        behavior_key = machine.behavior.value
        
        if behavior_key in self.learned_counter_patterns and self.learned_counter_patterns[behavior_key]:
            patterns = self.learned_counter_patterns[behavior_key]
            best_pattern = max(patterns, key=lambda p: p['confidence'] * p.get('success_rate', 0.5))
            
            # Ejecutar primera acción del patrón
            if best_pattern['actions']:
                action_type = best_pattern['actions'][0].lower()
                
                if 'attack' in action_type:
                    dx = machine.x - self.x
                    dy = machine.y - self.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                        direction = (dx/max(1, distance), dy/max(1, distance))
                        if self.attack_cooldown == 0:
                            self.attack(direction)
                            self.last_action = f"PATRÓN: {best_pattern['actions'][0]}"
                            return {"type": "pattern", "action": "attack", "confidence": best_pattern['confidence']}
                
                elif 'defend' in action_type:
                    self.defend()
                    self.last_action = f"PATRÓN: {best_pattern['actions'][0]}"
                    return {"type": "pattern", "action": "defend", "confidence": best_pattern['confidence']}
        
        # Fallback
        return self._execute_aggressive_closure(hypothesis, machine)
    
    def _execute_transfer_knowledge(self, hypothesis, machine):
        """Aplica conocimiento transferido."""
        source_behavior = hypothesis.get('source_behavior')
        
        if source_behavior and source_behavior in self.learned_counter_patterns:
            patterns = self.learned_counter_patterns[source_behavior]
            if patterns:
                # Usar patrón con mejor tasa de éxito
                best_pattern = max(patterns, key=lambda p: p.get('success_rate', 0.5))
                
                # Adaptar el patrón al comportamiento actual
                adapted_action = self._adapt_transferred_pattern(best_pattern, source_behavior, machine.behavior.value)
                
                # Ejecutar acción adaptada
                if 'attack' in adapted_action:
                    dx = machine.x - self.x
                    dy = machine.y - self.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                        direction = (dx/max(1, distance), dy/max(1, distance))
                        if self.attack_cooldown == 0:
                            self.attack(direction)
                
                self.last_action = f"TRANSFERENCIA: {source_behavior}→{machine.behavior.value}"
                return {
                    "type": "transfer",
                    "source": source_behavior,
                    "action": adapted_action,
                    "confidence": hypothesis['confidence']
                }
        
        # Fallback
        return self._execute_aggressive_closure(hypothesis, machine)
    
    def _adapt_transferred_pattern(self, pattern, source_behavior, target_behavior):
        """Adapta un patrón transferido."""
        # En una implementación real, aquí habría lógica de adaptación compleja
        # Por ahora, simplificamos
        actions_map = {
            "aggressive": "attack",
            "defensive": "defend",
            "evasive": "dodge",
            "pattern_a": "pattern_attack",
            "pattern_b": "pattern_attack",
            "circle": "intercept",
            "charge": "counter_attack",
            "sniper": "close_distance",
            "turtle": "timed_attack"
        }
        
        return actions_map.get(target_behavior, "attack")
    
    # ============================================
    # SISTEMA DE MEMORIA EPISÓDICA MEJORADO
    # ============================================
    
    def store_episodic_memory(self, state, action, reward, next_state, outcome):
        """Almacena experiencia con metadatos enriquecidos."""
        episode = {
            'timestamp': time.time(),
            'behavior': self.current_ai_behavior.value if self.current_ai_behavior else None,
            'state_hash': state.hash() if state else None,
            'action': action,
            'reward': reward,
            'next_state_hash': next_state.hash() if next_state else None,
            'outcome': outcome,
            'health': self.health,
            'machine_health': outcome.get('machine_health', 0),
            'damage_dealt': outcome.get('damage_dealt', 0),
            'damage_taken': outcome.get('damage_taken', 0),
            'successful': reward > 0,
            'confidence': self.decision_confidence,
            'exploration_rate': self.exploration_rate
        }
        
        self.episodic_memory.append(episode)
        self.current_episode.append(episode)
        
        # Consolidar si el episodio está completo o la ronda terminó
        if len(self.current_episode) >= 15 or outcome.get('round_ended', False):
            self._consolidate_episode()
            
            # Guardar en Neuron657 si es significativo
            if abs(reward) > 0.3:
                self._store_episode_in_memory(episode)
            
            self.current_episode.clear()
    
    def _consolidate_episode(self):
        """Consolida y aprende de un episodio completo."""
        if not self.current_episode:
            return
        
        try:
            # Calcular estadísticas
            episode_rewards = [e['reward'] for e in self.current_episode]
            avg_reward = sum(episode_rewards) / len(episode_rewards)
            
            success_count = sum(1 for e in self.current_episode if e['successful'])
            success_rate = success_count / len(self.current_episode)
            
            # Aprender del episodio
            if success_rate > 0.7:
                # Éxito - consolidar aprendizaje
                self.learning_effectiveness = min(0.98, self.learning_effectiveness + 0.03)
                self.successful_adaptations += 1
                self.decision_confidence = min(0.95, self.decision_confidence + 0.04)
                
                # Disminuir exploración
                self.exploration_rate = max(0.1, self.exploration_rate - 0.02)
                
                self.thought_bubble = "🎯 Consolidando aprendizaje exitoso"
                self.thought_timer = 60
                
            elif success_rate < 0.3:
                # Fracaso - ajustar estrategia
                self.learning_effectiveness = max(0.2, self.learning_effectiveness - 0.02)
                self.failed_adaptations += 1
                
                # Aumentar exploración
                self.exploration_rate = min(0.7, self.exploration_rate + 0.03)
                
                self.thought_bubble = "🔄 Ajustando estrategia después de fracaso"
                self.thought_timer = 60
            
            # Actualizar meta-aprendizaje
            self._update_meta_learning(avg_reward, success_rate)
            
            # Registrar en debug
            self._log_learning_event(f"Episodio consolidado: éxito={success_rate:.2f}, recompensa={avg_reward:.2f}")
            
        except Exception as e:
            print(f"⚠️  Error consolidando episodio: {e}")
    
    def _store_episode_in_memory(self, episode):
        """Almacena episodio significativo en Neuron657."""
        if not self.brain_initialized:
            return
        
        try:
            # Serializar episodio
            episode_summary = {
                'behavior': episode['behavior'],
                'reward': episode['reward'],
                'successful': episode['successful'],
                'damage_ratio': episode['damage_dealt'] / max(1, episode['damage_taken']),
                'timestamp': episode['timestamp']
            }
            
            json_str = json.dumps(episode_summary, separators=(',', ':'))
            json_bytes = json_str.encode('utf-8')
            
            # Asegurar tamaño
            if len(json_bytes) > GameConfig.PATTERN_SIZE:
                json_bytes = json_bytes[:GameConfig.PATTERN_SIZE]
            else:
                json_bytes = json_bytes.ljust(GameConfig.PATTERN_SIZE, b'\x00')
            
            # Crear patrón
            tags = [
                "episodic_memory",
                f"behavior_{episode['behavior']}",
                f"reward_{episode['reward']:.2f}",
                f"success_{episode['successful']}",
                f"confidence_{episode.get('confidence', 0.5):.2f}"
            ]
            
            if episode['successful']:
                tags.append("positive_experience")
            else:
                tags.append("negative_experience")
            
            pattern = NPF657Pattern(
                data=json_bytes,
                tags=tags
            )
            
            # Almacenar
            self.brain.nip.STORE_PATTERN(pattern)
            
        except Exception as e:
            print(f"⚠️  Error almacenando episodio: {e}")
    
    def _update_meta_learning(self, avg_reward, success_rate):
        """Actualiza parámetros de meta-aprendizaje."""
        # Ajustar tasa de aprendizaje basada en éxito reciente
        if success_rate > 0.6 and avg_reward > 0:
            self.learning_rate = min(0.25, self.learning_rate + 0.005)
        elif success_rate < 0.4 and avg_reward < 0:
            self.learning_rate = max(0.05, self.learning_rate - 0.003)
        
        # Ajustar umbral de reconocimiento de patrones
        if success_rate > 0.7:
            self.pattern_recognition_threshold = min(0.9, self.pattern_recognition_threshold + 0.02)
        elif success_rate < 0.4:
            self.pattern_recognition_threshold = max(0.5, self.pattern_recognition_threshold - 0.03)
    
    def _experience_replay(self):
        """Replay de experiencias para mejorar el aprendizaje."""
        if len(self.episodic_memory) < 20:
            return
        
        # Muestrear experiencias de forma inteligente
        # Priorizar experiencias extremas (muy buenas o muy malas)
        extreme_experiences = []
        normal_experiences = []
        
        for exp in self.episodic_memory:
            if abs(exp['reward']) > 0.5:
                extreme_experiences.append(exp)
            else:
                normal_experiences.append(exp)
        
        # Muestrear
        sample_size = min(8, len(self.episodic_memory))
        samples = []
        
        if extreme_experiences:
            extreme_sample = random.sample(extreme_experiences, min(4, len(extreme_experiences)))
            samples.extend(extreme_sample)
        
        remaining = sample_size - len(samples)
        if remaining > 0 and normal_experiences:
            normal_sample = random.sample(normal_experiences, min(remaining, len(normal_experiences)))
            samples.extend(normal_sample)
        
        # Aprender de las muestras
        total_reward = sum(s['reward'] for s in samples)
        avg_reward = total_reward / len(samples) if samples else 0
        
        success_count = sum(1 for s in samples if s['successful'])
        success_rate = success_count / len(samples) if samples else 0
        
        # Ajustar parámetros
        if avg_reward > 0.2:
            # Experiencias positivas
            self.decision_confidence = min(0.95, self.decision_confidence + 0.02)
            self.insight_bubble = "🔄 Consolidando éxitos pasados"
            self.insight_timer = 60
            
            # Registrar especialización si es consistente
            if success_rate > 0.8 and len(samples) >= 5:
                behavior = samples[0].get('behavior')
                if behavior:
                    self.behavior_mastery[behavior] = self.behavior_mastery.get(behavior, 0) + 1
                    
                    if self.behavior_mastery[behavior] >= GameConfig.BEHAVIOR_MASTERY_THRESHOLD:
                        if behavior not in self.specialized_behaviors:
                            self.specialized_behaviors.append(behavior)
                            self.adaptation_speed += GameConfig.ADAPTATION_SPEED_INCREASE
                            self.insight_bubble = f"🎖️  Especializado en {behavior}"
                            self.insight_timer = 90
        
        elif avg_reward < -0.2:
            # Experiencias negativas
            self.exploration_rate = min(0.7, self.exploration_rate + 0.03)
            self.insight_bubble = "🔄 Aprendiendo de errores"
            self.insight_timer = 60
    
    # ============================================
    # META-APRENDIZAJE MEJORADO
    # ============================================
    
    def meta_learning_update(self):
        """Actualiza parámetros de aprendizaje basado en efectividad."""
        self.meta_learning_counter += 1
        
        if self.meta_learning_counter < GameConfig.META_LEARNING_INTERVAL:
            return
        
        self.meta_learning_counter = 0
        
        if len(self.reward_history) < 30:
            return
        
        # Calcular métricas recientes
        recent_rewards = list(self.reward_history)[-30:]
        success_rate = sum(1 for r in recent_rewards if r > 0) / len(recent_rewards)
        avg_reward = sum(recent_rewards) / len(recent_rewards)
        reward_variance = np.var(recent_rewards) if len(recent_rewards) > 1 else 0
        
        # Guardar valores antiguos para comparación
        old_confidence = self.decision_confidence
        old_exploration = self.exploration_rate
        old_effectiveness = self.learning_effectiveness
        
        # Ajustes dinámicos basados en múltiples factores
        adjustment_made = False
        
        if success_rate < 0.35:
            # Bajo éxito - aumentar exploración, reducir confianza
            self.exploration_rate = min(0.75, self.exploration_rate + 0.06)
            self.decision_confidence = max(0.35, self.decision_confidence - 0.05)
            self.learning_rate = min(0.3, self.learning_rate + 0.01)
            
            adjustment_made = True
            self.thought_bubble = "🤔 Aumentando exploración (bajo éxito)"
            self.thought_timer = 90
            
        elif success_rate > 0.75:
            # Alto éxito - reducir exploración, aumentar confianza
            self.exploration_rate = max(0.15, self.exploration_rate - 0.04)
            self.decision_confidence = min(0.95, self.decision_confidence + 0.06)
            
            adjustment_made = True
            self.thought_bubble = "🎯 Refinando estrategia (alto éxito)"
            self.thought_timer = 90
        
        # Ajustar por consistencia de recompensas
        if reward_variance < 0.05 and len(recent_rewards) > 10:
            # Recompensas consistentes - ajustar finamente
            self.learning_rate = max(0.08, self.learning_rate - 0.002)
        
        # Actualizar efectividad del aprendizaje
        self.learning_effectiveness = success_rate * 0.6 + (1 - reward_variance) * 0.2 + avg_reward * 0.2
        
        # Ajustar metas basado en efectividad
        if self.current_ai_behavior:
            outcome = {
                "success": success_rate > 0.5,
                "damage_ratio": self.damage_dealt / max(1, self.damage_taken),
                "survived": self.health > 0
            }
            self.goal_system.adjust_for_behavior(self.current_ai_behavior, outcome)
        
        # Registrar en debug si hubo ajustes significativos
        if adjustment_made:
            confidence_change = self.decision_confidence - old_confidence
            exploration_change = self.exploration_rate - old_exploration
            
            self._log_learning_event(
                f"Meta-aprendizaje: éxito={success_rate:.2f}, "
                f"confianza={self.decision_confidence:.2f}({confidence_change:+.2f}), "
                f"exploración={self.exploration_rate:.2f}({exploration_change:+.2f})"
            )
    
    # ============================================
    # TRANSFERENCIA DE CONOCIMIENTO MEJORADA
    # ============================================
    
    def transfer_knowledge(self, from_behavior, to_behavior):
        """Transfiere conocimiento entre comportamientos similares."""
        if from_behavior not in self.similar_behaviors:
            return 0
        
        if to_behavior not in self.similar_behaviors[from_behavior]:
            return 0
        
        from_key = from_behavior.value
        to_key = to_behavior.value
        transfer_key = f"{from_key}_to_{to_key}"
        
        transferred_patterns = 0
        transferred_success_rate = 0.0
        
        if from_key in self.learned_counter_patterns:
            for pattern in self.learned_counter_patterns[from_key]:
                # Solo transferir patrones confiables y exitosos
                if pattern['confidence'] > 0.65 and pattern.get('success_rate', 0.5) > 0.6:
                    # Crear patrón adaptado
                    adapted_pattern = pattern.copy()
                    
                    # Ajustar confianza por transferencia
                    adaptation_factor = GameConfig.KNOWLEDGE_TRANSFER_RATE
                    adapted_pattern['confidence'] *= adaptation_factor
                    
                    # Añadir metadata de transferencia
                    adapted_pattern['transferred_from'] = from_key
                    adapted_pattern['transferred_at'] = time.time()
                    adapted_pattern['adaptation_factor'] = adaptation_factor
                    
                    # Inicializar en nuevo comportamiento
                    if to_key not in self.learned_counter_patterns:
                        self.learned_counter_patterns[to_key] = []
                    
                    # Verificar si ya existe
                    existing = next(
                        (p for p in self.learned_counter_patterns[to_key] 
                         if p['actions'] == adapted_pattern['actions']), 
                        None
                    )
                    
                    if not existing:
                        self.learned_counter_patterns[to_key].append(adapted_pattern)
                        transferred_patterns += 1
                        transferred_success_rate += adapted_pattern.get('success_rate', 0.5)
        
        # Registrar transferencia
        if transferred_patterns > 0:
            avg_success_rate = transferred_success_rate / transferred_patterns
            
            if transfer_key not in self.knowledge_base:
                self.knowledge_base[transfer_key] = {
                    "patterns_transferred": 0,
                    "success_rate": 0.5,
                    "last_transfer": time.time(),
                    "total_transfers": 0
                }
            
            kb = self.knowledge_base[transfer_key]
            kb["patterns_transferred"] += transferred_patterns
            kb["total_transfers"] += 1
            
            # Actualizar tasa de éxito (media móvil)
            old_rate = kb["success_rate"]
            kb["success_rate"] = old_rate * 0.7 + avg_success_rate * 0.3
            
            # Almacenar transferencia en memoria permanente
            self._store_knowledge_transfer(transfer_key, transferred_patterns, avg_success_rate)
            
            # Mostrar insight
            self.insight_bubble = f"🔄 Transferidos {transferred_patterns} patrones {from_key}→{to_key}"
            self.insight_timer = 90
            
            # Registrar en debug
            self._log_learning_event(
                f"Transferencia completada: {from_key} → {to_key} "
                f"({transferred_patterns} patrones, éxito={avg_success_rate:.2f})"
            )
            
            print(f"🔄 Transferencia: {from_key} → {to_key} ({transferred_patterns} patrones)")
            
            return transferred_patterns
        
        return 0
    
    def _store_knowledge_transfer(self, transfer_key, count, success_rate):
        """Almacena una transferencia en Neuron657."""
        if not self.brain_initialized:
            return
        
        try:
            transfer_data = {
                'transfer_key': transfer_key,
                'patterns_count': count,
                'success_rate': success_rate,
                'timestamp': time.time()
            }
            
            json_str = json.dumps(transfer_data, separators=(',', ':'))
            json_bytes = json_str.encode('utf-8')
            
            if len(json_bytes) > GameConfig.PATTERN_SIZE:
                json_bytes = json_bytes[:GameConfig.PATTERN_SIZE]
            else:
                json_bytes = json_bytes.ljust(GameConfig.PATTERN_SIZE, b'\x00')
            
            pattern = NPF657Pattern(
                data=json_bytes,
                tags=[
                    "knowledge_transfer",
                    f"transfer_{transfer_key}",
                    f"patterns_{count}",
                    f"success_{success_rate:.2f}",
                    f"timestamp_{int(time.time())}",
                    "npc_learned"
                ]
            )
            
            self.brain.nip.STORE_PATTERN(pattern)
            
        except Exception as e:
            print(f"⚠️  Error almacenando transferencia: {e}")
    
    # ============================================
    # APRENDIZAJE MEJORADO Y PERSISTENTE
    # ============================================
    
    def learn_from_experience(self, machine, outcome):
        """Aprendizaje completo que integra todos los sistemas."""
        if not self.learning_enabled or not self.brain_initialized:
            return
        
        if not self.current_state:
            return
        
        try:
            # 1. Calcular recompensa avanzada
            reward = self._calculate_advanced_reward(machine, outcome)
            self.reward_history.append(reward)
            self.total_learning_cycles += 1
            
            # 2. Memoria episódica
            self.store_episodic_memory(
                self.current_state,
                self.last_action,
                reward,
                None,  # next_state no disponible todavía
                outcome
            )
            
            # 3. Actualizar comportamiento actual en memoria
            if self.current_ai_behavior:
                behavior_key = self.current_ai_behavior.value
                
                if behavior_key not in self.behavior_memory:
                    self.behavior_memory[behavior_key] = {
                        "successes": 0,
                        "attempts": 0,
                        "adaptation": 0.1,
                        "last_encounter": time.time(),
                        "damage_ratio_history": deque(maxlen=10)
                    }
                
                mem = self.behavior_memory[behavior_key]
                mem["attempts"] += 1
                mem["damage_ratio_history"].append(self.damage_dealt / max(1, self.damage_taken))
                
                if reward > 0.5:
                    mem["successes"] += 1
                    mem["adaptation"] = min(0.4, mem["adaptation"] + 0.03)
                    
                    # Transferir conocimiento si se domina este comportamiento
                    if self._is_behavior_mastered(self.current_ai_behavior):
                        similar_behaviors = self.similar_behaviors.get(self.current_ai_behavior, [])
                        for similar in similar_behaviors:
                            self.transfer_knowledge(self.current_ai_behavior, similar)
                else:
                    mem["adaptation"] = max(0.05, mem["adaptation"] - 0.01)
            
            # 4. Ajustar parámetros de aprendizaje
            self._adjust_learning_parameters(reward, machine.behavior)
            
            # 5. Replay de experiencias periódico
            if self.total_learning_cycles % 25 == 0:
                self._experience_replay()
            
            # 6. Consolidar aprendizaje en memoria permanente
            self._consolidate_learning(reward, machine, outcome)
            
            # 7. Guardado automático periódico
            current_time = time.time()
            if self.auto_save_enabled and current_time - self.last_save_time > self.save_interval:
                self.save_learned_knowledge()
                self.last_save_time = current_time
            
        except Exception as e:
            print(f"⚠️  Error en aprendizaje inteligente: {e}")
            self._log_learning_event(f"ERROR en aprendizaje: {str(e)[:50]}")
    
    def _calculate_advanced_reward(self, machine, outcome):
        """Calcula recompensa multifactorial para aprendizaje."""
        reward = 0.0
        behavior = machine.behavior
        
        # 1. Base por comportamiento
        behavior_bonus = {
            AIBehavior.CHARGE: 1.4,
            AIBehavior.SNIPER: 1.3,
            AIBehavior.TURTLE: 1.2,
            AIBehavior.CIRCLE: 1.3,
            AIBehavior.ADAPTIVE: 1.5,
            AIBehavior.TACTICIAN: 1.4,
            AIBehavior.BERSERK: 1.4,
            AIBehavior.VORTEX: 1.3,
            AIBehavior.SHADOW: 1.4
        }.get(behavior, 1.0)
        
        # 2. Recompensas por acciones específicas
        if outcome.get('successful_counter_pattern', False):
            reward += 0.4 * behavior_bonus
        
        if outcome.get('successful_hypothesis', False):
            reward += 0.5 * behavior_bonus
            self.hypothesis_success_rate = min(1.0, self.hypothesis_success_rate + 0.05)
        
        if outcome.get('successful_transfer', False):
            reward += 0.6 * behavior_bonus
        
        # 3. Recompensas por daño (base)
        reward += outcome.get('damage_dealt', 0) * GameConfig.REWARD_DAMAGE * behavior_bonus
        reward += outcome.get('damage_taken', 0) * GameConfig.PENALTY_DAMAGE * behavior_bonus
        
        # 4. Recompensas por supervivencia
        if self.health > 60 and outcome.get('damage_taken', 0) < 15:
            reward += GameConfig.REWARD_SURVIVAL
        
        # 5. Recompensas por aprendizaje efectivo
        if self.learning_effectiveness > 0.75:
            reward += 0.08
        
        # 6. Recompensas por meta cumplida
        active_goal = self.goal_system.get_active_goal()
        goal_drive = self.goal_system.get_goal_drive(active_goal)
        
        if active_goal == "survival" and self.health > 70:
            reward += 0.12 * goal_drive
        elif active_goal == "damage_dealt" and outcome.get('damage_dealt', 0) > 25:
            reward += 0.15 * goal_drive
        elif active_goal == "pattern_learning" and outcome.get('pattern_learned', False):
            reward += 0.18 * goal_drive
        elif active_goal == "prediction_accuracy" and outcome.get('successful_prediction', False):
            reward += 0.2 * goal_drive
        
        # 7. Penalizaciones
        if outcome.get('attack_missed', False):
            reward -= 0.07
        
        if outcome.get('failed_hypothesis', False):
            reward -= 0.12
            self.hypothesis_success_rate = max(0.1, self.hypothesis_success_rate - 0.03)
        
        if outcome.get('failed_transfer', False):
            reward -= 0.15
        
        # 8. Bonus por uso eficiente de recursos
        if self.attack_cooldown == 0 and outcome.get('damage_dealt', 0) > 0:
            reward += 0.05
        
        # 9. Bonus por adaptación rápida
        if self.current_ai_behavior and self.current_ai_behavior.value in self.behavior_memory:
            mem = self.behavior_memory[self.current_ai_behavior.value]
            if mem["attempts"] <= 3 and reward > 0.3:
                reward *= 1.2  # Bonus por aprendizaje rápido
        
        # Limitar y escalar recompensa
        scaled_reward = max(-1.0, min(1.0, reward)) * self.learning_rate
        
        # Registrar en debug
        if abs(scaled_reward) > 0.3:
            self._log_learning_event(f"Recompensa significativa: {scaled_reward:.3f} (comportamiento: {behavior.value})")
        
        return scaled_reward
    
    def _adjust_learning_parameters(self, reward, behavior):
        """Ajusta dinámicamente los parámetros de aprendizaje."""
        
        # Ajuste basado en recompensa
        if reward > 0.4:
            # Gran éxito
            self.exploration_rate = max(0.08, self.exploration_rate - 0.015)
            self.decision_confidence = min(0.97, self.decision_confidence + 0.04)
            self.learning_effectiveness = min(0.99, self.learning_effectiveness + 0.02)
            
            if reward > 0.7:
                self.adaptation_speed = min(0.35, self.adaptation_speed + 0.01)
        
        elif reward < -0.4:
            # Gran fracaso
            self.exploration_rate = min(0.8, self.exploration_rate + 0.025)
            self.decision_confidence = max(0.25, self.decision_confidence - 0.06)
            
            # Aumentar tasa de aprendizaje si hay fracasos consecutivos
            if len(self.reward_history) > 8:
                recent_rewards = list(self.reward_history)[-8:]
                if all(r < 0 for r in recent_rewards):
                    self.learning_rate = min(0.35, self.learning_rate + 0.015)
                    self.thought_bubble = "📈 Aumentando tasa de aprendizaje"
                    self.thought_timer = 60
        
        # Ajuste basado en comportamiento específico
        if behavior:
            behavior_key = behavior.value
            if behavior_key in self.behavior_memory:
                adaptation = self.behavior_memory[behavior_key]["adaptation"]
                
                # Ajustar exploración y confianza basado en adaptación
                self.exploration_rate *= (1.0 - adaptation * 0.25)
                self.decision_confidence = min(0.95, self.decision_confidence + adaptation * 0.12)
    
    def _consolidate_learning(self, reward, machine, outcome):
        """Consolida el aprendizaje en Neuron657."""
        if not self.brain_initialized:
            return
        
        try:
            # Preparar tags de aprendizaje
            learning_tags = [
                "learning",
                f"behavior_{machine.behavior.value}",
                f"reward_{reward:.3f}",
                f"confidence_{self.decision_confidence:.2f}",
                f"effectiveness_{self.learning_effectiveness:.2f}",
                "npc_learned"
            ]
            
            # Clasificar resultado
            if reward > 0.7:
                learning_tags.extend(["great_success", "breakthrough"])
                outcome_type = "breakthrough"
            elif reward > 0.4:
                learning_tags.extend(["good_success", "effective_learning"])
                outcome_type = "success"
            elif reward > 0:
                learning_tags.extend(["minor_success", "learning_progress"])
                outcome_type = "progress"
            elif reward > -0.4:
                learning_tags.extend(["minor_failure", "learning_opportunity"])
                outcome_type = "minor_failure"
            else:
                learning_tags.extend(["major_failure", "needs_improvement"])
                outcome_type = "failure"
            
            # Añadir información específica
            if outcome.get('successful_counter_pattern', False):
                learning_tags.append("pattern_success")
            
            if outcome.get('successful_hypothesis', False):
                learning_tags.append("hypothesis_success")
            
            if outcome.get('successful_transfer', False):
                learning_tags.append("transfer_success")
            
            # Crear datos de aprendizaje
            learning_data = {
                'timestamp': time.time(),
                'behavior': machine.behavior.value,
                'reward': reward,
                'outcome_type': outcome_type,
                'npc_health': self.health,
                'machine_health': machine.health,
                'damage_dealt': outcome.get('damage_dealt', 0),
                'damage_taken': outcome.get('damage_taken', 0),
                'decision_confidence': self.decision_confidence,
                'learning_effectiveness': self.learning_effectiveness
            }
            
            # Serializar a JSON
            json_str = json.dumps(learning_data, separators=(',', ':'))
            json_bytes = json_str.encode('utf-8')
            
            # Asegurar tamaño
            if len(json_bytes) > GameConfig.PATTERN_SIZE:
                json_bytes = json_bytes[:GameConfig.PATTERN_SIZE]
            else:
                json_bytes = json_bytes.ljust(GameConfig.PATTERN_SIZE, b'\x00')
            
            # Crear y almacenar patrón
            learning_pattern = NPF657Pattern(
                data=json_bytes,
                tags=learning_tags
            )
            
            store_result = self.brain.nip.STORE_PATTERN(learning_pattern)
            
            if store_result.get('ok'):
                # Asociar con estado actual si está disponible
                if self.current_state:
                    try:
                        self.brain.nip.ASSOCIATE(
                            self.current_state.hash(),
                            store_result['hash']
                        )
                    except:
                        pass
                
                # Registrar en debug
                if outcome_type in ["breakthrough", "failure"]:
                    self._log_learning_event(f"Aprendizaje consolidado: {outcome_type} (recompensa: {reward:.3f})")
            
        except Exception as e:
            print(f"⚠️  Error consolidando aprendizaje: {e}")
    
    def save_learned_knowledge(self):
        """Guarda todo el conocimiento aprendido en Neuron657."""
        if not self.brain_initialized:
            return
        
        try:
            saved_patterns = 0
            saved_transfers = 0
            
            # 1. Guardar patrones de contraataque
            for behavior_key, patterns in self.learned_counter_patterns.items():
                for pattern in patterns:
                    if pattern.get('confidence', 0) > 0.5 and pattern.get('usage_count', 0) > 0:
                        try:
                            behavior = AIBehavior(behavior_key)
                            if self._store_pattern_in_memory(pattern, behavior, is_update=True):
                                saved_patterns += 1
                        except:
                            continue
            
            # 2. Guardar transferencias de conocimiento
            for transfer_key, data in self.knowledge_base.items():
                if data.get('patterns_transferred', 0) > 0:
                    transfer_data = {
                        'transfer_key': transfer_key,
                        'patterns_count': data['patterns_transferred'],
                        'success_rate': data.get('success_rate', 0.5),
                        'total_transfers': data.get('total_transfers', 1),
                        'last_transfer': data.get('last_transfer', time.time())
                    }
                    
                    json_str = json.dumps(transfer_data, separators=(',', ':'))
                    json_bytes = json_str.encode('utf-8')
                    
                    if len(json_bytes) > GameConfig.PATTERN_SIZE:
                        json_bytes = json_bytes[:GameConfig.PATTERN_SIZE]
                    else:
                        json_bytes = json_bytes.ljust(GameConfig.PATTERN_SIZE, b'\x00')
                    
                    pattern = NPF657Pattern(
                        data=json_bytes,
                        tags=["knowledge_transfer_snapshot", f"transfer_{transfer_key}", "npc_saved"]
                    )
                    
                    self.brain.nip.STORE_PATTERN(pattern)
                    saved_transfers += 1
            
            # 3. Consolidar
            self.brain.nip.CONSOLIDATE().result()
            
            # Mostrar confirmación
            if saved_patterns > 0 or saved_transfers > 0:
                self.debug_bubble = f"💾 Guardado: {saved_patterns} patrones, {saved_transfers} transferencias"
                self.debug_timer = 120
                
                print(f"💾 Conocimiento guardado: {saved_patterns} patrones, {saved_transfers} transferencias")
            
        except Exception as e:
            print(f"❌ Error guardando conocimiento: {e}")
            self.debug_bubble = f"❌ Error guardando: {str(e)[:20]}"
            self.debug_timer = 120
    
    def _add_reward(self, amount, reason=""):
        """Añade recompensa directamente al historial."""
        self.reward_history.append(amount)
        if reason:
            self._log_learning_event(f"Recompensa directa: {amount:.3f} ({reason})")
    
    def _log_learning_event(self, message):
        """Registra evento de aprendizaje para debug."""
        self.learning_debug_log.append({
            'timestamp': time.time(),
            'message': message,
            'health': self.health,
            'confidence': self.decision_confidence
        })
        
        if GameConfig.DEBUG_MODE:
            print(f"📝 [NPC Learning] {message}")
    
    # ============================================
    # DECISIÓN INTELIGENTE INTEGRADA - MEJORADA
    # ============================================
    
    
    def encode_game_state(self, machine, arena_rect):
        import math
        dx, dy = machine.x - self.x, machine.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        dist_bin = min(int(dist // 40), 15)
        angle_bin = int(((math.atan2(dy, dx) + math.pi) / (2 * math.pi)) * 16) % 16
        p = bytearray(64)
        p[0], p[1] = dist_bin, angle_bin
        p[2] = max(0, min(int((self.health / self.max_health) * 4), 4))
        p[3] = max(0, min(int((machine.health / machine.max_health) * 4), 4))
        p[61] = 78 # Version v7.8
        return NPF657Pattern(data=bytes(p), tags=["episodic"])
    def choose_action(self, machine, arena_rect):
        """Decisión inteligente integrando todos los sistemas mejorados."""
        # Actualizar comportamiento actual
        self.current_ai_behavior = machine.behavior
        
        # Si no hay cerebro, usar IA simple
        if not self.learning_enabled or not self.brain_initialized:
            self.thought_bubble = "❌ MODO SIMPLE (sin aprendizaje)"
            self.thought_timer = 60
            return self._simple_counter_ai(machine, arena_rect)
        
        try:
            # 1. Observar patrones de la máquina
            self.observe_machine_patterns(machine)
            
            # 2. Codificar estado actual
            current_state = self.encode_game_state(machine, arena_rect)
            self.current_state = current_state
            
            # 3. Meta-aprendizaje periódico
            self.meta_learning_update()
            
            # 4. Generar hipótesis si es necesario
            should_generate_hypotheses = (
                not self.active_hypotheses or 
                random.random() < 0.25 or
                self.hypothesis_success_rate < 0.4
            )
            
            if should_generate_hypotheses:
                current_situation = {
                    'distance': math.sqrt((machine.x - self.x)**2 + (machine.y - self.y)**2),
                    'health_ratio': self.health / self.max_health,
                    'damage_ratio': self.damage_dealt / max(1, self.damage_taken),
                    'time_in_round': len(self.action_history)
                }
                self.active_hypotheses = self.generate_hypotheses(machine, current_situation)
            
            # 5. Decisión: probar hipótesis vs usar conocimiento
            use_hypothesis = False
            
            if (self.active_hypotheses and 
                random.random() < GameConfig.HYPOTHESIS_EXPLORATION_RATE and
                self.exploration_rate > 0.25):
                
                # Seleccionar mejor hipótesis
                best_hypothesis = self.select_best_hypothesis(self.active_hypotheses)
                
                if best_hypothesis and best_hypothesis['confidence'] > 0.55:
                    action_result = self.test_hypothesis(best_hypothesis, machine)
                    if action_result:
                        self.action_history.append({
                            'type': 'hypothesis',
                            'hypothesis_id': best_hypothesis['id'],
                            'action': action_result,
                            'timestamp': time.time(),
                            'confidence': best_hypothesis['confidence']
                        })
                        
                        # Evaluar resultado inmediato
                        outcome = {
                            'hypothesis_tested': True,
                            'hypothesis_type': best_hypothesis['type'],
                            'confidence': best_hypothesis['confidence']
                        }
                        
                        return action_result
            
            # 6. Usar conocimiento existente
            behavior_key = machine.behavior.value
            
            # Primero, verificar si somos especialistas en este comportamiento
            if behavior_key in self.specialized_behaviors:
                # Usar estrategia especializada
                action_result = self._execute_specialized_strategy(machine)
                if action_result:
                    self.thought_bubble = f"🎖️  Estrategia especializada"
                    self.thought_timer = 60
                    return action_result
            
            # Segundo, verificar patrones aprendidos
            if behavior_key in self.learned_counter_patterns and self.learned_counter_patterns[behavior_key]:
                # Filtrar patrones confiables y exitosos
                reliable_patterns = [
                    p for p in self.learned_counter_patterns[behavior_key]
                    if p['confidence'] > 0.6 and p.get('success_rate', 0.5) > 0.55
                ]
                
                if reliable_patterns:
                    # Seleccionar patrón con mejor score
                    best_pattern = max(
                        reliable_patterns,
                        key=lambda p: p['confidence'] * p.get('success_rate', 0.5) * 
                                     (1 - p.get('usage_count', 0) * 0.02)
                    )
                    
                    # Ejecutar patrón
                    action_result = self._execute_learned_pattern(best_pattern, machine)
                    if action_result:
                        self.thought_bubble = f"🎯 Usando patrón confiable"
                        self.thought_timer = 60
                        
                        # Actualizar uso
                        best_pattern['usage_count'] = best_pattern.get('usage_count', 0) + 1
                        
                        self.action_history.append({
                            'type': 'learned_pattern',
                            'behavior': behavior_key,
                            'pattern_confidence': best_pattern['confidence'],
                            'pattern_success_rate': best_pattern.get('success_rate', 0.5),
                            'timestamp': time.time()
                        })
                        
                        return action_result
            
            # 7. Decisión por defecto: explorar o explotar conocimiento general
            if random.random() < self.exploration_rate:
                # Exploración inteligente
                action_result = self._explore_counter_action(machine)
                self.thought_bubble = "🔍 Explorando nuevas estrategias"
                self.thought_timer = 60
            else:
                # Explotar conocimiento general de Neuron657
                action_result, confidence = self._exploit_knowledge(current_state, machine)
                self.thought_bubble = f"🧠 Decidiendo (conf: {confidence:.2f})"
                self.thought_timer = 60
            
            return action_result
            
        except Exception as e:
            print(f"⚠️  Error en decisión NPC inteligente: {e}")
            self._log_learning_event(f"ERROR en decisión: {str(e)[:40]}")
            import traceback
            traceback.print_exc()
            return self._simple_counter_ai(machine, arena_rect)
    
    def _execute_specialized_strategy(self, machine):
        """Ejecuta estrategia especializada para un comportamiento dominado."""
        behavior = machine.behavior
        behavior_key = behavior.value
        
        # Estrategias especializadas por comportamiento
        specialized_strategies = {
            AIBehavior.AGGRESSIVE: self._execute_aggressive_specialized,
            AIBehavior.DEFENSIVE: self._execute_defensive_specialized,
            AIBehavior.EVASIVE: self._execute_evasive_specialized,
            AIBehavior.CIRCLE: self._execute_circle_specialized,
            AIBehavior.SNIPER: self._execute_sniper_specialized,
            AIBehavior.TURTLE: self._execute_turtle_specialized,
            AIBehavior.ADAPTIVE: self._execute_adaptive_specialized
        }
        
        strategy_func = specialized_strategies.get(behavior)
        if strategy_func:
            return strategy_func(machine)
        
        # Fallback a patrón aprendido
        return self._execute_best_learned_pattern(machine)
    
    def _execute_aggressive_specialized(self, machine):
        """Estrategia especializada contra comportamiento agresivo."""
        # Contra agresivo: esquivar y contraatacar
        dx = machine.x - self.x
        dy = machine.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if machine.attacking and distance < 100:
            # Esquivar ataque
            dodge_angle = math.atan2(dy, dx) + math.pi/2
            self.vx = math.cos(dodge_angle) * self.speed * 1.3
            self.vy = math.sin(dodge_angle) * self.speed * 1.3
            
            # Contraataque rápido
            if self.attack_cooldown == 0 and distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                direction = (dx/max(1, distance), dy/max(1, distance))
                self.attack(direction)
            
            self.last_action = "ESPECIALIZADO: ESQUIVAR Y CONTRAATACAR"
            return {"type": "specialized", "strategy": "dodge_counter", "behavior": "aggressive"}
        else:
            # Mantener distancia óptima
            optimal_distance = 120
            if distance > optimal_distance + 30:
                self.move_towards(machine.x, machine.y)
            elif distance < optimal_distance - 30:
                self.move_away_from(machine.x, machine.y)
            
            self.last_action = "ESPECIALIZADO: CONTROL DE DISTANCIA"
            return {"type": "specialized", "strategy": "distance_control", "behavior": "aggressive"}
    
    def _execute_defensive_specialized(self, machine):
        """Estrategia especializada contra comportamiento defensivo."""
        # Contra defensivo: ataques rápidos y retirada
        if not machine.defending and self.attack_cooldown == 0:
            # Ataque rápido
            dx = machine.x - self.x
            dy = machine.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                direction = (dx/max(1, distance), dy/max(1, distance))
                self.attack(direction)
                
                # Retirada inmediata
                self.move_away_from(machine.x, machine.y)
                
                self.last_action = "ESPECIALIZADO: ATAQUE RÁPIDO"
                return {"type": "specialized", "strategy": "quick_strike", "behavior": "defensive"}
        
        # Presionar si está defendiendo
        if machine.defending:
            # Moverse alrededor para buscar apertura
            circle_angle = math.atan2(machine.y - self.y, machine.x - self.x) + 0.1
            circle_distance = 100
            
            target_x = machine.x + math.cos(circle_angle) * circle_distance
            target_y = machine.y + math.sin(circle_angle) * circle_distance
            
            self.move_towards(target_x, target_y)
            
            self.last_action = "ESPECIALIZADO: PRESIONAR DEFENSA"
            return {"type": "specialized", "strategy": "pressure_defense", "behavior": "defensive"}
        
        return None
    
    def _execute_evasive_specialized(self, machine):
        """Estrategia especializada contra comportamiento evasivo."""
        # Predecir movimientos evasivos
        if hasattr(machine, 'state'):
            if machine.state == "dodge":
                # Predecir dirección de esquive
                predicted_dodge_angle = math.atan2(machine.vy, machine.vx) if machine.vx != 0 or machine.vy != 0 else 0
                intercept_distance = 80
                
                intercept_x = machine.x + math.cos(predicted_dodge_angle) * intercept_distance
                intercept_y = machine.y + math.sin(predicted_dodge_angle) * intercept_distance
                
                self.move_towards(intercept_x, intercept_y)
                
                self.last_action = "ESPECIALIZADO: INTERCEPTAR ESQUIVE"
                return {"type": "specialized", "strategy": "intercept_dodge", "behavior": "evasive"}
        
        # Estrategia por defecto: mantener presión constante
        self.move_towards(machine.x, machine.y)
        
        # Ataque oportunista
        dx = machine.x - self.x
        dy = machine.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius and random.random() < 0.4:
            direction = (dx/max(1, distance), dy/max(1, distance))
            if self.attack_cooldown == 0:
                self.attack(direction)
        
        self.last_action = "ESPECIALIZADO: PRESIÓN CONSTANTE"
        return {"type": "specialized", "strategy": "constant_pressure", "behavior": "evasive"}
    
    def _execute_circle_specialized(self, machine):
        """Estrategia especializada contra movimiento circular."""
        if hasattr(machine, 'target_angle'):
            # Predecir posición futura en el círculo
            prediction_steps = 3
            predicted_angle = machine.target_angle + 0.05 * prediction_steps
            
            # Interceptar en punto adelantado
            intercept_distance = 110
            intercept_x = machine.x + math.cos(predicted_angle) * intercept_distance
            intercept_y = machine.y + math.sin(predicted_angle) * intercept_distance
            
            self.move_towards(intercept_x, intercept_y)
            
            # Ataque si está alineado
            dx = machine.x - self.x
            dy = machine.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            angle_to_machine = math.atan2(dy, dx)
            angle_diff = abs(predicted_angle - angle_to_machine)
            
            if angle_diff < 0.3 and distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                if self.attack_cooldown == 0:
                    direction = (dx/max(1, distance), dy/max(1, distance))
                    self.attack(direction)
            
            self.last_action = "ESPECIALIZADO: INTERCEPTAR CÍRCULO"
            return {"type": "specialized", "strategy": "circle_intercept", "behavior": "circle"}
        
        return None
    
    def _execute_sniper_specialized(self, machine):
        """Estrategia especializada contra sniper."""
        # Cerrar distancia rápidamente pero con zigzag
        dx = machine.x - self.x
        dy = machine.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 150:
            # Zigzag para evitar ataques a distancia
            base_angle = math.atan2(dy, dx)
            
            # Alternar entre zig y zag
            if int(time.time() * 3) % 2 == 0:
                approach_angle = base_angle + 0.3  # Zig
            else:
                approach_angle = base_angle - 0.3  # Zag
            
            approach_distance = min(distance * 0.7, 100)
            target_x = self.x + math.cos(approach_angle) * approach_distance
            target_y = self.y + math.sin(approach_angle) * approach_distance
            
            self.move_towards(target_x, target_y)
            
            self.last_action = "ESPECIALIZADO: ZIGZAG DE APROXIMACIÓN"
            return {"type": "specialized", "strategy": "zigzag_approach", "behavior": "sniper"}
        else:
            # En distancia corta, atacar agresivamente
            if self.attack_cooldown == 0:
                direction = (dx/max(1, distance), dy/max(1, distance))
                self.attack(direction)
            
            self.last_action = "ESPECIALIZADO: ATAQUE CERCANO"
            return {"type": "specialized", "strategy": "close_combat", "behavior": "sniper"}
    
    def _execute_turtle_specialized(self, machine):
        """Estrategia especializada contra turtle."""
        # Esperar apertura y atacar con timing
        if not machine.defending:
            # Turtle está vulnerable
            dx = machine.x - self.x
            dy = machine.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                if self.attack_cooldown == 0:
                    direction = (dx/max(1, distance), dy/max(1, distance))
                    self.attack(direction)
                    
                    # Combo: múltiples ataques rápidos
                    self.attack_cooldown = max(0, self.attack_cooldown - 5)
                    
                    self.last_action = "ESPECIALIZADO: COMBO RÁPIDO"
                    return {"type": "specialized", "strategy": "fast_combo", "behavior": "turtle"}
        else:
            # Presionar la defensa
            # Moverse alrededor para cansar
            pressure_angle = math.atan2(machine.y - self.y, machine.x - self.x) + 0.15
            pressure_distance = 90
            
            target_x = machine.x + math.cos(pressure_angle) * pressure_distance
            target_y = machine.y + math.sin(pressure_angle) * pressure_distance
            
            self.move_towards(target_x, target_y)
            
            self.last_action = "ESPECIALIZADO: PRESIONAR DEFENSA"
            return {"type": "specialized", "strategy": "pressure_defense", "behavior": "turtle"}
        
        return None
    
    def _execute_adaptive_specialized(self, machine):
        """Estrategia especializada contra comportamiento adaptativo."""
        # Variar estrategia frecuentemente para evitar ser predecible
        strategies = [
            self._execute_aggressive_specialized,
            self._execute_defensive_specialized,
            self._execute_evasive_specialized,
            lambda m: self._execute_circle_specialized(m) or self._execute_aggressive_specialized(m)
        ]
        
        # Cambiar estrategia basado en tiempo
        strategy_index = int(time.time() * 0.5) % len(strategies)
        strategy_func = strategies[strategy_index]
        
        result = strategy_func(machine)
        if result:
            result['adaptive_strategy'] = True
            result['strategy_index'] = strategy_index
        
        self.last_action = f"ESPECIALIZADO: ESTRATEGIA {strategy_index}"
        return result
    
    def _execute_best_learned_pattern(self, machine):
        """Ejecuta el mejor patrón aprendido para el comportamiento actual."""
        behavior_key = machine.behavior.value
        
        if behavior_key in self.learned_counter_patterns and self.learned_counter_patterns[behavior_key]:
            patterns = self.learned_counter_patterns[behavior_key]
            
            # Seleccionar patrón con mejor score
            scored_patterns = []
            for pattern in patterns:
                score = (
                    pattern['confidence'] * 
                    pattern.get('success_rate', 0.5) * 
                    (1.0 / (1 + pattern.get('usage_count', 0) * 0.01))
                )
                scored_patterns.append((score, pattern))
            
            if scored_patterns:
                best_score, best_pattern = max(scored_patterns, key=lambda x: x[0])
                
                if best_score > 0.3:
                    return self._execute_learned_pattern(best_pattern, machine)
        
        return None
    
    def _execute_learned_pattern(self, pattern, machine):
        """Ejecuta un patrón aprendido específico."""
        if not pattern['actions']:
            return None
        
        # Tomar la primera acción del patrón (simplificado)
        action_type = pattern['actions'][0].lower()
        
        if 'attack' in action_type or 'atk' in action_type:
            dx = machine.x - self.x
            dy = machine.y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                if self.attack_cooldown == 0:
                    direction = (dx/max(1, distance), dy/max(1, distance))
                    self.attack(direction)
                    self.last_action = f"PATRÓN: ATAQUE"
                    return {"type": "pattern", "action": "attack", "confidence": pattern['confidence']}
        
        elif 'defend' in action_type or 'def' in action_type:
            self.defend()
            
            # Retroceder mientras defiende
            if random.random() < 0.7:
                self.move_away_from(machine.x, machine.y)
            
            self.last_action = f"PATRÓN: DEFENSA"
            return {"type": "pattern", "action": "defend", "confidence": pattern['confidence']}
        
        elif 'circle' in action_type or 'circ' in action_type:
            # Movimiento circular
            angle = math.atan2(machine.y - self.y, machine.x - self.x) + 0.08
            circle_distance = 130
            
            target_x = machine.x + math.cos(angle) * circle_distance
            target_y = machine.y + math.sin(angle) * circle_distance
            
            self.move_towards(target_x, target_y)
            self.last_action = f"PATRÓN: CIRCULAR"
            return {"type": "pattern", "action": "circle", "confidence": pattern['confidence']}
        
        elif 'intercept' in action_type or 'int' in action_type:
            # Interceptación
            if hasattr(machine, 'target_angle'):
                predicted_angle = machine.target_angle + 0.2
            else:
                predicted_angle = math.atan2(machine.vy, machine.vx) if machine.vx != 0 or machine.vy != 0 else 0
            
            intercept_distance = 100
            intercept_x = machine.x + math.cos(predicted_angle) * intercept_distance
            intercept_y = machine.y + math.sin(predicted_angle) * intercept_distance
            
            self.move_towards(intercept_x, intercept_y)
            self.last_action = f"PATRÓN: INTERCEPTAR"
            return {"type": "pattern", "action": "intercept", "confidence": pattern['confidence']}
        
        # Acción por defecto: acercar
        self.move_towards(machine.x, machine.y)
        self.last_action = f"PATRÓN: ACERCAR"
        return {"type": "pattern", "action": "approach", "confidence": pattern['confidence']}
    
    def _explore_counter_action(self, machine):
        """Explora posibles contraataques de forma inteligente."""
        # Exploración dirigida basada en situación actual
        current_distance = math.sqrt((machine.x - self.x)**2 + (machine.y - self.y)**2)
        health_ratio = self.health / self.max_health
        
        if health_ratio < 0.4:
            # Salud baja: estrategias conservadoras
            actions = ["defensive_retreat", "evasive_movement", "distance_control"]
        elif current_distance < 100:
            # Cerca: estrategias de combate cercano
            actions = ["quick_attack", "dodge_counter", "pressure_move"]
        elif current_distance > 200:
            # Lejos: estrategias de aproximación
            actions = ["aggressive_approach", "flanking_move", "zigzag_approach"]
        else:
            # Distancia media: estrategias balanceadas
            actions = ["timed_attack", "predictive_move", "pattern_test"]
        
        action = random.choice(actions)
        return self._execute_counter_action(action, machine)
    
    def _exploit_knowledge(self, state_pattern, machine):
        """Usa el conocimiento aprendido en Neuron657."""
        try:
            if not self.brain_initialized:
                return self._explore_counter_action(machine), 0.3
            
            # Buscar patrones similares
            search_result = self.brain.nip.SEARCH_SIMILAR(state_pattern, limit=5).result()
            
            if search_result['ok'] and search_result['results']:
                best_action = None
                best_confidence = 0
                
                for result in search_result['results']:
                    confidence = float(result['confidence'])
                    
                    if confidence > best_confidence:
                        # Cargar patrón completo para obtener tags de acción
                        try:
                            cid = result.get('cid')
                            offset = result.get('offset')
                            
                            if cid is not None and offset is not None:
                                pattern = self.brain.memory.load_pattern_compacted(cid, offset)
                                
                                # Buscar tags de acción
                                action_tags = [tag for tag in pattern.tags if tag.startswith('action_')]
                                
                                if action_tags:
                                    action_name = action_tags[0].replace('action_', '')
                                    best_confidence = confidence
                                    best_action = action_name
                        except:
                            continue
                
                if best_action and best_confidence > 0.45:
                    self.decision_confidence = min(0.95, self.decision_confidence + 0.02)
                    return self._execute_counter_action(best_action, machine), best_confidence
            
            # Fallback a exploración con confianza baja
            return self._explore_counter_action(machine), 0.25
            
        except Exception as e:
            print(f"⚠️  Error en explotación de conocimiento: {e}")
            return self._explore_counter_action(machine), 0.2
    
    def _execute_counter_action(self, action_name, machine):
        """Versión mejorada de ejecución de contraataques."""
        dx = machine.x - self.x
        dy = machine.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        direction = (dx/max(1, distance), dy/max(1, distance)) if distance > 0 else (0, 0)
        
        # Acciones mejoradas con lógica más inteligente
        if action_name == "aggressive_approach":
            if distance > 150:
                # Aproximación rápida
                self.move_towards(machine.x, machine.y)
                self.speed = GameConfig.NPC_SPEED * 1.2  # Aumento temporal de velocidad
                self.last_action = "APROXIMACIÓN AGRESIVA"
                return {"type": "aggressive", "action": "fast_approach"}
        
        elif action_name == "defensive_retreat":
            self.defend()
            
            # Retroceder inteligentemente
            retreat_angle = math.atan2(dy, dx) + math.pi
            
            # Añadir variación para evitar ser predecible
            if random.random() < 0.5:
                retreat_angle += random.uniform(-0.4, 0.4)
            
            retreat_distance = 120
            target_x = self.x + math.cos(retreat_angle) * retreat_distance
            target_y = self.y + math.sin(retreat_angle) * retreat_distance
            
            self.move_towards(target_x, target_y)
            self.last_action = "RETIRADA DEFENSIVA"
            return {"type": "defensive", "action": "smart_retreat"}
        
        elif action_name == "quick_attack":
            if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                if self.attack_cooldown == 0:
                    self.attack(direction)
                    self.last_action = "ATAQUE RÁPIDO"
                    return {"type": "aggressive", "action": "quick_strike"}
            else:
                self.move_towards(machine.x, machine.y)
                self.last_action = "ACERCAR PARA ATAQUE"
                return {"type": "aggressive", "action": "approach_for_attack"}
        
        elif action_name == "dodge_counter":
            # Esquivar y contraatacar
            if machine.attacking and distance < 120:
                dodge_angle = math.atan2(dy, dx) + math.pi/2
                self.vx = math.cos(dodge_angle) * self.speed * 1.4
                self.vy = math.sin(dodge_angle) * self.speed * 1.4
                
                # Contraataque después de esquivar
                if self.attack_cooldown == 0 and distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                    self.attack(direction)
                
                self.last_action = "ESQUIVAR Y CONTRAATACAR"
                return {"type": "counter", "action": "dodge_and_counter"}
        
        elif action_name == "pressure_move":
            # Presionar moviéndose alrededor
            pressure_angle = math.atan2(dy, dx) + 0.15
            pressure_distance = 100
            
            target_x = machine.x + math.cos(pressure_angle) * pressure_distance
            target_y = machine.y + math.sin(pressure_angle) * pressure_distance
            
            self.move_towards(target_x, target_y)
            
            # Ataque oportunista
            if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius and random.random() < 0.3:
                if self.attack_cooldown == 0:
                    self.attack(direction)
            
            self.last_action = "MOVIMIENTO DE PRESIÓN"
            return {"type": "pressure", "action": "circling_pressure"}
        
        elif action_name == "zigzag_approach":
            # Aproximación en zigzag
            base_angle = math.atan2(dy, dx)
            
            # Alternar dirección
            if int(time.time() * 2) % 2 == 0:
                approach_angle = base_angle + 0.25  # Zig
            else:
                approach_angle = base_angle - 0.25  # Zag
            
            approach_distance = min(distance * 0.6, 80)
            target_x = self.x + math.cos(approach_angle) * approach_distance
            target_y = self.y + math.sin(approach_angle) * approach_distance
            
            self.move_towards(target_x, target_y)
            self.last_action = "APROXIMACIÓN ZIGZAG"
            return {"type": "evasive", "action": "zigzag_approach"}
        
        elif action_name == "timed_attack":
            # Ataque con tiempo
            if not machine.defending and self.attack_cooldown == 0:
                if distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
                    self.attack(direction)
                    self.last_action = "ATAQUE CON TIEMPO"
                    return {"type": "timing", "action": "timed_strike"}
                else:
                    self.move_towards(machine.x, machine.y)
                    self.last_action = "PREPARAR ATAQUE CON TIEMPO"
                    return {"type": "timing", "action": "positioning"}
        
        elif action_name == "predictive_move":
            # Movimiento predictivo
            if hasattr(machine, 'vx') and hasattr(machine, 'vy'):
                predict_time = 0.35
                predicted_x = machine.x + machine.vx * predict_time
                predicted_y = machine.y + machine.vy * predict_time
                
                self.move_towards(predicted_x, predicted_y)
                self.last_action = "MOVIMIENTO PREDICTIVO"
                return {"type": "predictive", "action": "predicted_movement"}
        
        # Acción por defecto mejorada
        return self._simple_counter_ai(machine, None)
    
    def _simple_counter_ai(self, machine, arena_rect):
        """IA simple para cuando no hay aprendizaje - mejorada."""
        dx = machine.x - self.x
        dy = machine.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        direction = (dx/max(1, distance), dy/max(1, distance)) if distance > 0 else (0, 0)
        
        # IA básica mejorada
        if machine.attacking and distance < 130:
            # Defensa activa
            self.defend()
            
            # Esquivar si es posible
            if random.random() < 0.6:
                dodge_angle = math.atan2(dy, dx) + math.pi/2
                self.vx = math.cos(dodge_angle) * self.speed * 1.2
                self.vy = math.sin(dodge_angle) * self.speed * 1.2
                self.last_action = "ESQUIVAR DEFENSIVO"
                self.thought_bubble = "🛡️ Esquivando!"
                self.thought_timer = 30
                return {"type": "basic", "action": "dodge_defense"}
            else:
                self.move_away_from(machine.x, machine.y)
                self.last_action = "RETIRADA DEFENSIVA"
                self.thought_bubble = "🛡️ Retirándose!"
                self.thought_timer = 30
                return {"type": "basic", "action": "defensive_retreat"}
        
        elif distance < GameConfig.NPC_ATTACK_RANGE + machine.radius:
            # Ataque
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "ATAQUE BÁSICO"
                self.thought_bubble = "⚔️ Atacando!"
                self.thought_timer = 30
                return {"type": "basic", "action": "attack"}
            else:
                # Moverse mientras espera cooldown
                lateral_angle = math.atan2(dy, dx) + math.pi/2
                self.vx = math.cos(lateral_angle) * self.speed * 0.7
                self.vy = math.sin(lateral_angle) * self.speed * 0.7
                self.last_action = "MOVIMIENTO LATERAL"
                return {"type": "basic", "action": "lateral_movement"}
        
        elif distance > 180:
            # Acercar
            self.move_towards(machine.x, machine.y)
            self.last_action = "ACERCAR"
            self.thought_bubble = "🎯 Acercando..."
            self.thought_timer = 30
            return {"type": "basic", "action": "approach"}
        
        else:
            # Mantener distancia óptima
            optimal_distance = 140
            if distance > optimal_distance + 20:
                self.move_towards(machine.x, machine.y)
            elif distance < optimal_distance - 20:
                self.move_away_from(machine.x, machine.y)
            else:
                # Movimiento de patrulla
                patrol_angle = math.atan2(dy, dx) + 0.05
                self.vx = math.cos(patrol_angle) * self.speed * 0.5
                self.vy = math.sin(patrol_angle) * self.speed * 0.5
            
            self.last_action = "CONTROL DE DISTANCIA"
            self.thought_bubble = "📏 Manteniendo distancia..."
            self.thought_timer = 30
            return {"type": "basic", "action": "distance_control"}
    
    def _is_behavior_mastered(self, behavior):
        """Determina si un comportamiento ha sido dominado."""
        behavior_key = behavior.value
        
        if behavior_key not in self.behavior_memory:
            return False
        
        mem = self.behavior_memory[behavior_key]
        successes = mem.get("successes", 0)
        attempts = mem.get("attempts", 0)
        adaptation = mem.get("adaptation", 0)
        
        # Criterios para dominio
        has_successes = successes >= GameConfig.BEHAVIOR_MASTERY_THRESHOLD
        has_high_adaptation = adaptation > 0.25
        has_good_ratio = attempts > 0 and (successes / attempts) > 0.6
        
        # Dominio si cumple múltiples criterios
        mastery_score = (
            (1 if has_successes else 0) * 0.4 +
            (1 if has_high_adaptation else 0) * 0.3 +
            (1 if has_good_ratio else 0) * 0.3
        )
        
        return mastery_score >= 0.7
    
    # ============================================
    # MÉTODOS DE JUEGO BÁSICOS
    # ============================================
    
    def update(self, arena_rect):
        """Actualiza posición y estado."""
        # Aplicar velocidad
        new_x = self.x + self.vx
        new_y = self.y + self.vy
        
        # Limitar a la arena
        margin = self.radius + 5
        if (arena_rect.left + margin <= new_x <= arena_rect.right - margin and
            arena_rect.top + margin <= new_y <= arena_rect.bottom - margin):
            self.x = new_x
            self.y = new_y
        
        # Actualizar cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # Actualizar timers
        if self.action_timer > 0:
            self.action_timer -= 1
        
        if self.thought_timer > 0:
            self.thought_timer -= 1
        
        if self.insight_timer > 0:
            self.insight_timer -= 1
        
        if self.debug_timer > 0:
            self.debug_timer -= 1
        
        # Resetear ataque
        if self.attacking and self.attack_cooldown < 5:
            self.attacking = False
        
        # Normalizar velocidad (deceleración)
        self.vx *= 0.92
        self.vy *= 0.92
        
        # Restaurar velocidad normal si estaba aumentada
        self.speed = GameConfig.NPC_SPEED
    
    def move_towards(self, target_x, target_y):
        """Mueve hacia una posición objetivo."""
        dx = target_x - self.x
        dy = target_y - self.y
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        
        self.vx = (dx / dist) * self.speed
        self.vy = (dy / dist) * self.speed
    
    def move_away_from(self, target_x, target_y):
        """Se aleja de una posición."""
        dx = self.x - target_x
        dy = self.y - target_y
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        
        self.vx = (dx / dist) * self.speed
        self.vy = (dy / dist) * self.speed
    
    def stop(self):
        """Detiene el movimiento."""
        self.vx = 0
        self.vy = 0
    
    def attack(self, direction):
        """Realiza un ataque."""
        if self.attack_cooldown <= 0 and self.health > 0:
            self.attacking = True
            self.attack_direction = direction
            self.attack_cooldown = GameConfig.NPC_ATTACK_COOLDOWN
            self.attacks_made += 1
            return True
        return False
    
    def defend(self):
        """Se pone en posición defensiva."""
        self.defending = True
        self.last_action = "Defender"
        self.action_timer = 15
    
    def stop_defend(self):
        """Sale de la defensa."""
        self.defending = False
    
    def take_damage(self, amount, attacker=None):
        """Recibe daño."""
        if self.defending:
            amount *= GameConfig.NPC_DEFENSE_REDUCTION
            self.successful_defenses += 1
        
        self.health = max(0, self.health - amount)
        self.damage_taken += amount
        
        if attacker:
            attacker.damage_dealt += amount
        
        return amount
    
    def is_in_attack_range(self, other):
        """Verifica si otro combatiente está en rango de ataque."""
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance <= GameConfig.NPC_ATTACK_RANGE + other.radius
    
    # ============================================
    # VISUALIZACIÓN SUPER-MEJORADA
    # ============================================
    
    def draw(self, screen, font):
        """Dibuja el NPC con indicadores de inteligencia avanzados."""
        # Cuerpo con gradiente
        for i in range(3):
            radius = self.radius - i * 2
            alpha = 200 - i * 40
            color = (
                max(0, min(255, self.color[0] - i * 20)),
                max(0, min(255, self.color[1] - i * 10)),
                max(0, min(255, self.color[2] + i * 10))
            )
            
            # Crear superficie con alpha
            circle_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            rgba_color = color + (alpha,)
            pygame.draw.circle(circle_surface, rgba_color, (radius, radius), radius)
            screen.blit(circle_surface, (int(self.x - radius), int(self.y - radius)))
        
        # Borde según estado
        border_color = (255, 255, 255)
        border_width = 2
        
        if self.defending:
            border_color = (100, 200, 255)
            border_width = 4
            # Escudo visual
            shield_surface = pygame.Surface((self.radius*2 + 10, self.radius*2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (100, 200, 255, 80), 
                             (self.radius + 5, self.radius + 5), 
                             self.radius + 5, 3)
            screen.blit(shield_surface, (int(self.x - self.radius - 5), int(self.y - self.radius - 5)))
        
        if self.attacking:
            border_color = (255, 220, 50)
            border_width = 5
            # Visual de ataque
            attack_length = 60
            attack_end_x = self.x + self.attack_direction[0] * attack_length
            attack_end_y = self.y + self.attack_direction[1] * attack_length
            
            # Línea de ataque con gradiente
            for i in range(3):
                line_width = 6 - i * 2
                line_alpha = 200 - i * 50
                line_color = (255, 220 - i*30, 50, line_alpha)
                pygame.draw.line(screen, line_color,
                                (int(self.x), int(self.y)),
                                (int(attack_end_x), int(attack_end_y)), line_width)
        
        # Borde exterior
        pygame.draw.circle(screen, border_color, (int(self.x), int(self.y)), 
                          self.radius, border_width)
        
        # Ojos inteligentes animados
        eye_radius = 6
        pupil_radius = 3
        
        # Ojo izquierdo
        left_eye_x = self.x - 10
        left_eye_y = self.y - 8
        
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(left_eye_x), int(left_eye_y)), eye_radius)
        
        # Pupila que sigue (dirección hacia la máquina)
        pupil_offset_x = 0
        pupil_offset_y = 0
        pygame.draw.circle(screen, (50, 100, 220), 
                          (int(left_eye_x + pupil_offset_x), int(left_eye_y + pupil_offset_y)), 
                          pupil_radius)
        
        # Ojo derecho
        right_eye_x = self.x + 10
        right_eye_y = self.y - 8
        
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(right_eye_x), int(right_eye_y)), eye_radius)
        
        pygame.draw.circle(screen, (50, 100, 220), 
                          (int(right_eye_x + pupil_offset_x), int(right_eye_y + pupil_offset_y)), 
                          pupil_radius)
        
        # Indicador de cerebro activo
        if self.brain_initialized and self.learning_enabled:
            brain_radius = 4
            brain_color = (100, 255, 150) if self.learning_effectiveness > 0.7 else (255, 200, 100)
            pygame.draw.circle(screen, brain_color, 
                             (int(self.x), int(self.y + 10)), brain_radius)
        
        # Nombre y estado
        name = "NPC (SUPER-INTELIGENTE)"
        name_surface = font.render(name, True, (255, 255, 255))
        screen.blit(name_surface, (int(self.x - name_surface.get_width()/2), 
                                  int(self.y - self.radius - 30)))
        
        # Especializaciones
        if self.specialized_behaviors:
            spec_text = f"Especializado en: {len(self.specialized_behaviors)} comportamientos"
            spec_surface = pygame.font.Font(None, 16).render(spec_text, True, (255, 220, 100))
            screen.blit(spec_surface, (int(self.x - spec_surface.get_width()/2),
                                      int(self.y - self.radius - 50)))
        
        # Última acción
        if self.action_timer > 0:
            action_surface = font.render(self.last_action, True, (200, 230, 255))
            screen.blit(action_surface, (int(self.x - action_surface.get_width()/2),
                                        int(self.y + self.radius + 8)))
        
        # Burbujas de pensamiento e insight
        if self.thought_timer > 0 and self.thought_bubble:
            self._draw_thought_bubble(screen, self.thought_bubble, 
                                     self.x, self.y - self.radius - 70)
        
        if self.insight_timer > 0 and self.insight_bubble:
            self._draw_insight_bubble(screen, self.insight_bubble,
                                     self.x, self.y - self.radius - 100)
        
        if self.debug_timer > 0 and self.debug_bubble:
            self._draw_debug_bubble(screen, self.debug_bubble,
                                   self.x, self.y - self.radius - 130)
        
        # Indicador de meta activa
        try:
            self._draw_active_goal(screen, self.x, self.y - self.radius - 160)
        except Exception as e:
            print(f"Error dibujando active goal: {e}")
        
        # Indicador de efectividad
        self._draw_effectiveness_indicator(screen, self.x, self.y + self.radius + 25)
        
        # Indicador de confianza
        self._draw_confidence_indicator(screen, self.x, self.y + self.radius + 45)
    
    def _draw_thought_bubble(self, screen, text, x, y):
        """Dibuja burbuja de pensamiento."""
        # Dividir texto si es muy largo
        max_chars = 35
        if len(text) > max_chars:
            parts = []
            for i in range(0, len(text), max_chars):
                parts.append(text[i:i+max_chars])
            text_lines = parts[:2]  # Máximo 2 líneas
        else:
            text_lines = [text]
        
        # Calcular tamaño de burbuja
        line_height = 20
        bubble_height = len(text_lines) * line_height + 15
        bubble_width = 300
        
        bubble_rect = pygame.Rect(0, 0, bubble_width, bubble_height)
        bubble_rect.center = (x, y)
        
        # Fondo
        pygame.draw.rect(screen, (40, 45, 70, 230), bubble_rect, border_radius=12)
        pygame.draw.rect(screen, (80, 120, 210), bubble_rect, 2, border_radius=12)
        
        # Texto
        thought_font = pygame.font.Font(None, 18)
        for i, line in enumerate(text_lines):
            thought_text = thought_font.render(line, True, (210, 225, 255))
            screen.blit(thought_text, 
                       (x - thought_text.get_width()//2, 
                        y - bubble_height//2 + 8 + i * line_height))
    
    def _draw_insight_bubble(self, screen, text, x, y):
        """Dibuja burbuja de insight."""
        bubble_rect = pygame.Rect(0, 0, 340, 28)
        bubble_rect.center = (x, y)
        
        pygame.draw.rect(screen, (60, 40, 85, 230), bubble_rect, border_radius=10)
        pygame.draw.rect(screen, (180, 100, 220), bubble_rect, 2, border_radius=10)
        
        insight_font = pygame.font.Font(None, 19)
        insight_text = insight_font.render(text, True, (240, 200, 255))
        screen.blit(insight_text,
                   (x - insight_text.get_width()//2,
                    y - insight_text.get_height()//2))
    
    def _draw_debug_bubble(self, screen, text, x, y):
        """Dibuja burbuja de debug."""
        bubble_rect = pygame.Rect(0, 0, 320, 26)
        bubble_rect.center = (x, y)
        
        pygame.draw.rect(screen, (40, 60, 40, 230), bubble_rect, border_radius=10)
        pygame.draw.rect(screen, (100, 220, 100), bubble_rect, 2, border_radius=10)
        
        debug_font = pygame.font.Font(None, 17)
        debug_text = debug_font.render(text, True, (200, 255, 200))
        screen.blit(debug_text,
                   (x - debug_text.get_width()//2,
                    y - debug_text.get_height()//2))
    
    def _draw_active_goal(self, screen, x, y):
        """Dibuja indicador de meta activa."""
        active_goal = self.goal_system.get_active_goal()
        goal_drive = self.goal_system.get_goal_drive(active_goal)
        success_rate = self.goal_system.get_goal_success_rate(active_goal)
        
        goal_text = f"🎯 {active_goal.replace('_', ' ').title()}"
        stats_text = f"Drive: {goal_drive:.2f} | Éxito: {success_rate:.0%}"
        
        goal_rect = pygame.Rect(0, 0, 240, 40)
        goal_rect.center = (x, y)
        
        # Color basado en la meta
        goal_colors = {
            "survival": (255, 100, 100, 190),
            "damage_dealt": (255, 150, 50, 190),
            "pattern_learning": (100, 180, 255, 190),
            "adaptation_speed": (150, 100, 255, 190),
            "prediction_accuracy": (100, 220, 150, 190),
            "energy_efficiency": (255, 220, 100, 190)
        }
        
        color = goal_colors.get(active_goal, (80, 80, 100, 190))
        
        pygame.draw.rect(screen, color, goal_rect, border_radius=10)
        pygame.draw.rect(screen, (color[0]+50, color[1]+50, color[2]+50), goal_rect, 2, border_radius=10)
        
        # Texto principal
        goal_font = pygame.font.Font(None, 18)
        goal_surface = goal_font.render(goal_text, True, (255, 255, 255))
        screen.blit(goal_surface,
                   (x - goal_surface.get_width()//2,
                    y - 12))
        
        # Texto de estadísticas
        stats_font = pygame.font.Font(None, 14)
        stats_surface = stats_font.render(stats_text, True, (230, 230, 230))
        screen.blit(stats_surface,
                   (x - stats_surface.get_width()//2,
                    y + 5))
    
    def _draw_effectiveness_indicator(self, screen, x, y):
        """Dibuja indicador de efectividad del aprendizaje."""
        indicator_width = 70
        indicator_height = 10
        
        # Fondo
        pygame.draw.rect(screen, (60, 60, 80),
                        (x - indicator_width//2, y, indicator_width, indicator_height))
        
        # Barra de efectividad
        effectiveness_width = int(indicator_width * self.learning_effectiveness)
        
        # Color según efectividad
        if self.learning_effectiveness > 0.8:
            effectiveness_color = (100, 255, 100)
        elif self.learning_effectiveness > 0.6:
            effectiveness_color = (200, 220, 100)
        elif self.learning_effectiveness > 0.4:
            effectiveness_color = (255, 180, 100)
        else:
            effectiveness_color = (255, 100, 100)
        
        pygame.draw.rect(screen, effectiveness_color,
                        (x - indicator_width//2, y, effectiveness_width, indicator_height))
        
        # Borde
        pygame.draw.rect(screen, (100, 100, 120),
                        (x - indicator_width//2, y, indicator_width, indicator_height), 1)
        
        # Texto
        eff_text = f"Efectividad: {self.learning_effectiveness:.0%}"
        eff_font = pygame.font.Font(None, 14)
        eff_surface = eff_font.render(eff_text, True, (200, 200, 200))
        screen.blit(eff_surface,
                   (x - eff_surface.get_width()//2,
                    y + indicator_height + 2))
    
    def _draw_confidence_indicator(self, screen, x, y):
        """Dibuja indicador de confianza."""
        indicator_width = 70
        indicator_height = 8
        
        # Fondo
        pygame.draw.rect(screen, (60, 60, 80),
                        (x - indicator_width//2, y, indicator_width, indicator_height))
        
        # Barra de confianza
        confidence_width = int(indicator_width * self.decision_confidence)
        
        # Color según confianza
        if self.decision_confidence > 0.8:
            confidence_color = (100, 200, 255)
        elif self.decision_confidence > 0.6:
            confidence_color = (150, 180, 255)
        else:
            confidence_color = (200, 150, 255)
        
        pygame.draw.rect(screen, confidence_color,
                        (x - indicator_width//2, y, confidence_width, indicator_height))
        
        # Borde
        pygame.draw.rect(screen, (100, 100, 120),
                        (x - indicator_width//2, y, indicator_width, indicator_height), 1)
        
        # Texto
        conf_text = f"Confianza: {self.decision_confidence:.0%}"
        conf_font = pygame.font.Font(None, 13)
        conf_surface = conf_font.render(conf_text, True, (200, 200, 230))
        screen.blit(conf_surface,
                   (x - conf_surface.get_width()//2,
                    y + indicator_height + 2))
    
    def draw_health_bar(self, screen, x, y, width, height):
        """Dibuja la barra de salud con mejoras visuales."""
        # Fondo
        pygame.draw.rect(screen, (50, 50, 60), (x, y, width, height))
        pygame.draw.rect(screen, (80, 80, 100), (x, y, width, height), 2)
        
        # Salud actual
        health_ratio = self.health / self.max_health
        health_width = int(width * health_ratio)
        
        # Color con gradiente
        if health_ratio > 0.7:
            color = (100, 200, 255)  # Azul saludable
        elif health_ratio > 0.4:
            color = (150, 200, 255)  # Azul medio
        elif health_ratio > 0.2:
            color = (200, 180, 255)  # Púrpura bajo
        else:
            color = (255, 150, 150)  # Rojo crítico
        
        pygame.draw.rect(screen, color, (x, y, health_width, height))
        
        # Efecto de brillo en el borde superior
        highlight_height = max(1, height // 4)
        highlight_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
        pygame.draw.rect(screen, highlight_color, (x, y, health_width, highlight_height))
        
        # Texto de salud
        health_text = f"{int(self.health)}/{self.max_health}"
        font = pygame.font.Font(None, 22)
        text_surface = font.render(health_text, True, (255, 255, 255))
        screen.blit(text_surface, (x + width//2 - text_surface.get_width()//2,
                                  y + height//2 - text_surface.get_height()//2))
    
    def draw_intelligence_hud(self, screen, x, y, font):
        """Dibuja HUD detallado de inteligencia."""
        panel_width = 380
        panel_height = 240
        panel_x = x
        panel_y = y
        
        # Panel de fondo
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (30, 35, 55, 230), 
                        panel_surface.get_rect(), border_radius=12)
        pygame.draw.rect(panel_surface, (60, 70, 100),
                        panel_surface.get_rect(), 2, border_radius=12)
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Título
        title = font.render("🧠 SISTEMA DE INTELIGENCIA AVANZADO", True, (220, 230, 255))
        screen.blit(title, (panel_x + panel_width//2 - title.get_width()//2, panel_y + 12))
        
        # Métricas principales
        metrics_y = panel_y + 45
        line_height = 20
        
        main_metrics = [
            f"Efectividad aprendizaje: {self.learning_effectiveness:.2f}",
            f"Confianza decisión: {self.decision_confidence:.2f}",
            f"Tasa exploración: {self.exploration_rate:.2f}",
            f"Velocidad adaptación: {self.adaptation_speed:.2f}",
            f"Tasa aprendizaje: {self.learning_rate:.3f}"
        ]
        
        for i, metric in enumerate(main_metrics):
            metric_text = font.render(metric, True, (200, 210, 240))
            screen.blit(metric_text, (panel_x + 15, metrics_y + i * line_height))
        
        # Métricas de conocimiento
        knowledge_y = metrics_y + len(main_metrics) * line_height + 10
        
        total_patterns = sum(len(v) for v in self.learned_counter_patterns.values())
        total_hypotheses = len(self.tested_hypotheses)
        total_transfers = len(self.knowledge_base)
        
        knowledge_metrics = [
            f"Patrones aprendidos: {total_patterns}",
            f"Hipótesis probadas: {total_hypotheses}",
            f"Transferencias: {total_transfers}",
            f"Éxito hipótesis: {self.hypothesis_success_rate:.0%}",
            f"Adaptaciones exitosas: {self.successful_adaptations}"
        ]
        
        for i, metric in enumerate(knowledge_metrics):
            metric_text = font.render(metric, True, (180, 220, 255))
            screen.blit(metric_text, (panel_x + 15, knowledge_y + i * line_height))
        
        # Especializaciones
        if self.specialized_behaviors:
            spec_text = f"Especializaciones: {len(self.specialized_behaviors)}"
            spec_surface = font.render(spec_text, True, (255, 220, 100))
            screen.blit(spec_surface, (panel_x + 15, panel_y + panel_height - 35))
        
        # Barra de progreso de aprendizaje
        progress_y = panel_y + panel_height - 20
        progress_width = panel_width - 30
        progress_height = 10
        
        # Progreso basado en múltiples factores
        experience_score = (
            self.learning_effectiveness * 0.3 +
            (self.successful_adaptations / max(1, self.successful_adaptations + self.failed_adaptations)) * 0.3 +
            min(1.0, total_patterns / 50) * 0.2 +
            min(1.0, self.total_learning_cycles / 200) * 0.2
        )
        
        pygame.draw.rect(screen, (60, 60, 80),
                       (panel_x + 15, progress_y, progress_width, progress_height))
        
        progress_color = (
            int(100 + 155 * experience_score),
            int(100 + 155 * self.learning_effectiveness),
            200
        )
        
        pygame.draw.rect(screen, progress_color,
                       (panel_x + 15, progress_y, progress_width * experience_score, progress_height))
        
        pygame.draw.rect(screen, (100, 100, 120),
                       (panel_x + 15, progress_y, progress_width, progress_height), 1)
        
        # Texto de experiencia
        exp_text = f"Experiencia total: {self.total_learning_cycles}"
        exp_surface = pygame.font.Font(None, 14).render(exp_text, True, (180, 220, 255))
        screen.blit(exp_surface, (panel_x + 15, progress_y - 18))
    
    def draw_debug_info(self, screen, x, y, font):
        """Dibuja información de debug."""
        if not GameConfig.DEBUG_MODE:
            return
        
        panel_width = 400
        panel_height = 180
        panel_x = x
        panel_y = y
        
        # Panel de fondo
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (40, 30, 40, 200), 
                        panel_surface.get_rect(), border_radius=10)
        pygame.draw.rect(panel_surface, (100, 70, 100),
                        panel_surface.get_rect(), 2, border_radius=10)
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Título
        title = font.render("🔧 DEBUG INFO", True, (255, 200, 200))
        screen.blit(title, (panel_x + 15, panel_y + 10))
        
        # Información
        info_y = panel_y + 40
        line_height = 18
        
        # Cerebro
        brain_status = "✅ INICIALIZADO" if self.brain_initialized else "❌ NO INICIALIZADO"
        brain_color = (100, 255, 100) if self.brain_initialized else (255, 100, 100)
        
        brain_text = font.render(f"Cerebro: {brain_status}", True, brain_color)
        screen.blit(brain_text, (panel_x + 15, info_y))
        
        # Aprendizaje
        learning_status = "✅ ACTIVO" if self.learning_enabled else "❌ INACTIVO"
        learning_color = (100, 255, 100) if self.learning_enabled else (255, 100, 100)
        
        learning_text = font.render(f"Aprendizaje: {learning_status}", True, learning_color)
        screen.blit(learning_text, (panel_x + 15, info_y + line_height))
        
        # Patrones en memoria
        if self.brain_initialized:
            try:
                # Intentar contar patrones NPC
                test_pattern = NPF657Pattern(
                    data=b"npc".ljust(GameConfig.PATTERN_SIZE, b'\x00'),
                    tags=["npc_pattern"]
                )
                search_result = self.brain.nip.SEARCH_SIMILAR(test_pattern, limit=50).result()
                npc_patterns_count = len(search_result.get('results', []))
                
                patterns_text = font.render(f"Patrones NPC en cerebro: {npc_patterns_count}", 
                                          True, (200, 200, 255))
                screen.blit(patterns_text, (panel_x + 15, info_y + line_height * 2))
            except:
                patterns_text = font.render("Patrones NPC: Error al contar", 
                                          True, (255, 150, 150))
                screen.blit(patterns_text, (panel_x + 15, info_y + line_height * 2))
        
        # Logs recientes
        if self.learning_debug_log:
            log_y = info_y + line_height * 4
            log_font = pygame.font.Font(None, 14)
            
            for i, log_entry in enumerate(list(self.learning_debug_log)[-3:]):
                log_text = log_font.render(f"{log_entry['message'][:45]}", True, (220, 220, 180))
                screen.blit(log_text, (panel_x + 15, log_y + i * 16))
        
        # Último guardado
        if self.auto_save_enabled:
            time_since_save = int(time.time() - self.last_save_time)
            save_text = font.render(f"Último guardado: {time_since_save}s", 
                                  True, (180, 220, 180))
            screen.blit(save_text, (panel_x + 15, panel_y + panel_height - 25))

# ============================================
# MÁQUINA CONTROLADA POR IA MEJORADA
# ============================================

class AIControlledFighter:
    """Máquina hardcodeada con comportamientos pre-programados mejorados."""
    
    def __init__(self, x, y, behavior=AIBehavior.AGGRESSIVE):
        self.x = x
        self.y = y
        self.color = GameConfig.AI_COLOR
        self.radius = 32
        self.health = 100
        self.max_health = 100
        
        # Estado de combate
        self.attacking = False
        self.defending = False
        self.attack_cooldown = 0
        self.attack_direction = (0, 0)
        
        # Movimiento
        self.vx = 0
        self.vy = 0
        self.speed = GameConfig.AI_SPEED
        
        # Comportamiento
        self.behavior = behavior
        self.behavior_timer = 0
        self.state = "idle"
        self.state_timer = 0
        
        # Para comportamientos específicos
        self.pattern_step = 0
        self.target_angle = 0
        self.charge_count = 0
        self.sniper_distance = 220
        self.adaptive_behaviors = []  # Para comportamiento ADAPTIVE
        self.current_adaptive_index = 0
        self.adaptive_timer = 0
        
        # Nuevos atributos para comportamientos avanzados
        self.feint_count = 0
        self.vortex_direction = 1
        self.shadow_memory = deque(maxlen=20)
        self.berserk_multiplier = 1.0
        self.tactician_analysis = {}
        
        # Estadísticas
        self.attacks_made = 0
        self.attacks_hit = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.successful_defenses = 0
        
        # Para visualización
        self.last_action = "Idle"
        self.action_timer = 0
        self.behavior_text = behavior.value.upper()
    
    def update(self, arena_rect, npc):
        """Actualiza la máquina según su comportamiento mejorado."""
        # Movimiento
        new_x = self.x + self.vx
        new_y = self.y + self.vy
        
        # Limitar a la arena
        margin = self.radius + 5
        if (arena_rect.left + margin <= new_x <= arena_rect.right - margin and
            arena_rect.top + margin <= new_y <= arena_rect.bottom - margin):
            self.x = new_x
            self.y = new_y
        
        # Cooldown de ataque
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # Temporizador de acción
        if self.action_timer > 0:
            self.action_timer -= 1
        
        # Temporizador de estado
        if self.state_timer > 0:
            self.state_timer -= 1
        
        # Actualizar comportamiento
        self.behavior_timer += 1
        
        # Comportamientos BERSERK y ADAPTIVE necesitan actualizaciones especiales
        if self.behavior == AIBehavior.BERSERK:
            self._update_berserk_state(npc)
        elif self.behavior == AIBehavior.ADAPTIVE:
            self._update_adaptive_state(npc)
        elif self.behavior == AIBehavior.TACTICIAN:
            self._update_tactician_state(npc)
        
        # Elegir acción según comportamiento
        self._execute_behavior(npc, arena_rect)
        
        # Resetear ataque
        if self.attacking and self.attack_cooldown < 5:
            self.attacking = False
        
        # Normalizar velocidad
        self.vx *= 0.92
        self.vy *= 0.92
    
    def _update_berserk_state(self, npc):
        """Actualiza estado BERSERK (más rápido y fuerte con poca salud)."""
        health_ratio = self.health / self.max_health
        
        if health_ratio < 0.4:
            self.berserk_multiplier = 1.0 + (0.4 - health_ratio) * 2.5
            self.speed = GameConfig.AI_SPEED * self.berserk_multiplier
        else:
            self.berserk_multiplier = 1.0
            self.speed = GameConfig.AI_SPEED
    
    def _update_adaptive_state(self, npc):
        """Actualiza comportamiento ADAPTIVE (cambia entre comportamientos)."""
        self.adaptive_timer += 1
        
        # Cambiar comportamiento cada 5-8 segundos
        if self.adaptive_timer > random.randint(300, 480):
            self.adaptive_timer = 0
            
            if not self.adaptive_behaviors:
                # Inicializar lista de comportamientos adaptativos
                self.adaptive_behaviors = [
                    AIBehavior.AGGRESSIVE,
                    AIBehavior.DEFENSIVE,
                    AIBehavior.EVASIVE,
                    AIBehavior.CIRCLE,
                    AIBehavior.FEINT,
                    AIBehavior.SNIPER
                ]
                random.shuffle(self.adaptive_behaviors)
            
            # Cambiar al siguiente comportamiento
            self.current_adaptive_index = (self.current_adaptive_index + 1) % len(self.adaptive_behaviors)
            new_behavior = self.adaptive_behaviors[self.current_adaptive_index]
            
            # Actualizar comportamiento
            self.behavior = new_behavior
            self.behavior_text = f"ADAPTIVE->{new_behavior.value.upper()}"
            
            # Resetear estado
            self.state = "idle"
            self.state_timer = 0
            self.pattern_step = 0
    
    def _update_tactician_state(self, npc):
        """Actualiza estado TACTICIAN (analiza patrones del NPC)."""
        # Registrar movimiento del NPC
        self.shadow_memory.append({
            'x': npc.x,
            'y': npc.y,
            'vx': npc.vx,
            'vy': npc.vy,
            'action': npc.last_action,
            'timestamp': time.time()
        })
        
        # Analizar cada 2 segundos
        if self.behavior_timer % 120 == 0:
            self._analyze_npc_patterns(npc)
    
    def _analyze_npc_patterns(self, npc):
        """Analiza patrones del NPC para el comportamiento TACTICIAN."""
        if len(self.shadow_memory) < 10:
            return
        
        memory_list = list(self.shadow_memory)
        
        # Análisis básico
        avg_speed = np.mean([math.sqrt(m['vx']**2 + m['vy']**2) for m in memory_list])
        direction_changes = sum(1 for i in range(1, len(memory_list)) 
                              if memory_list[i]['action'] != memory_list[i-1]['action'])
        
        # Detectar patrones de ataque
        attack_patterns = [m for m in memory_list if 'ATAQUE' in m['action'] or 'ATK' in m['action']]
        defense_patterns = [m for m in memory_list if 'DEFEN' in m['action'] or 'DEF' in m['action']]
        
        self.tactician_analysis = {
            'avg_speed': avg_speed,
            'direction_changes': direction_changes,
            'attack_frequency': len(attack_patterns) / len(memory_list),
            'defense_frequency': len(defense_patterns) / len(memory_list),
            'predictability': 1.0 - (direction_changes / len(memory_list))
        }
    
    def _execute_behavior(self, npc, arena_rect):
        """Ejecuta el comportamiento actual de la máquina."""
        dx = npc.x - self.x
        dy = npc.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Calcular dirección hacia el NPC
        direction = (dx/max(1, distance), dy/max(1, distance)) if distance > 0 else (0, 0)
        
        # Comportamientos básicos (mantenidos de la versión original)
        if self.behavior == AIBehavior.AGGRESSIVE:
            self._aggressive_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.DEFENSIVE:
            self._defensive_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.EVASIVE:
            self._evasive_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.PATTERN_A:
            self._pattern_a_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.PATTERN_B:
            self._pattern_b_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.RANDOM:
            self._random_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.CIRCLE:
            self._circle_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.CHARGE:
            self._charge_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.SNIPER:
            self._sniper_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.TURTLE:
            self._turtle_behavior(npc, distance, direction)
        # Nuevos comportamientos
        elif self.behavior == AIBehavior.ADAPTIVE:
            # Usar el comportamiento actual en la lista adaptativa
            if self.adaptive_behaviors:
                current_behavior = self.adaptive_behaviors[self.current_adaptive_index]
                # Llamar al método correspondiente dinámicamente
                behavior_methods = {
                    AIBehavior.AGGRESSIVE: self._aggressive_behavior,
                    AIBehavior.DEFENSIVE: self._defensive_behavior,
                    AIBehavior.EVASIVE: self._evasive_behavior,
                    AIBehavior.CIRCLE: self._circle_behavior,
                    AIBehavior.FEINT: self._feint_behavior,
                    AIBehavior.SNIPER: self._sniper_behavior
                }
                method = behavior_methods.get(current_behavior)
                if method:
                    method(npc, distance, direction)
        elif self.behavior == AIBehavior.FEINT:
            self._feint_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.VORTEX:
            self._vortex_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.SHADOW:
            self._shadow_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.BERSERK:
            self._berserk_behavior(npc, distance, direction)
        elif self.behavior == AIBehavior.TACTICIAN:
            self._tactician_behavior(npc, distance, direction)
    
    # Comportamientos básicos (mantenidos de la versión original)
    def _aggressive_behavior(self, npc, distance, direction):
        """Comportamiento agresivo: siempre ataca."""
        if distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "ATTACK"
                self.action_timer = 15
        else:
            # Acercarse
            self.move_towards(npc.x, npc.y)
            self.last_action = "APPROACH"
            self.action_timer = 15
        
        self.defending = False
    
    def _defensive_behavior(self, npc, distance, direction):
        """Comportamiento defensivo: prioriza defensa."""
        if distance < 120:
            if npc.attacking:
                # Defender si el NPC ataca
                self.defend()
                self.move_away_from(npc.x, npc.y)
                self.last_action = "DEFEND"
                self.action_timer = 15
            elif distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
                # Atacar si está en rango
                if self.attack_cooldown == 0:
                    self.attack(direction)
                    self.last_action = "ATTACK"
                    self.action_timer = 15
        else:
            # Mantener distancia media
            self.move_towards(npc.x, npc.y)
            self.last_action = "APPROACH"
            self.action_timer = 15
    
    def _evasive_behavior(self, npc, distance, direction):
        """Comportamiento evasivo: esquiva y contraataca."""
        if self.state == "idle":
            if distance < 100:
                self.state = "dodge"
                self.state_timer = 30
            elif distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
                self.state = "attack"
                self.state_timer = 20
            else:
                self.move_towards(npc.x, npc.y)
        
        elif self.state == "dodge":
            # Esquivar perpendicularmente
            angle = math.atan2(direction[1], direction[0]) + math.pi/2
            self.vx = math.cos(angle) * self.speed * 1.2
            self.vy = math.sin(angle) * self.speed * 1.2
            self.last_action = "DODGE"
            
            if self.state_timer < 15:
                self.state = "counter"
                self.state_timer = 10
        
        elif self.state == "counter":
            # Contraataque rápido
            self.attack(direction)
            self.last_action = "COUNTER"
            self.state = "idle"
        
        elif self.state == "attack":
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "ATTACK"
            self.state = "retreat"
            self.state_timer = 40
        
        elif self.state == "retreat":
            self.move_away_from(npc.x, npc.y)
            self.last_action = "RETREAT"
            if self.state_timer == 0:
                self.state = "idle"
    
    def _pattern_a_behavior(self, npc, distance, direction):
        """Patrón específico A: ataque en triángulo."""
        pattern_steps = [
            ("approach", 30),
            ("attack", 10),
            ("circle_right", 40),
            ("attack", 10),
            ("circle_left", 40),
            ("attack", 10),
        ]
        
        step_name, duration = pattern_steps[self.pattern_step]
        
        if self.state_timer == 0:
            self.pattern_step = (self.pattern_step + 1) % len(pattern_steps)
            step_name, duration = pattern_steps[self.pattern_step]
            self.state_timer = duration
        
        if step_name == "approach":
            self.move_towards(npc.x, npc.y)
            self.last_action = "APPROACH"
        elif step_name == "attack":
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "PATTERN ATK"
        elif step_name == "circle_right":
            angle = math.atan2(npc.y - self.y, npc.x - self.x) + 0.1
            self.vx = math.cos(angle) * self.speed
            self.vy = math.sin(angle) * self.speed
            self.last_action = "CIRCLE →"
        elif step_name == "circle_left":
            angle = math.atan2(npc.y - self.y, npc.x - self.x) - 0.1
            self.vx = math.cos(angle) * self.speed
            self.vy = math.sin(angle) * self.speed
            self.last_action = "CIRCLE ←"
    
    def _pattern_b_behavior(self, npc, distance, direction):
        """Patrón específico B: ataque en zigzag."""
        if self.behavior_timer % 60 < 30:
            # Fase 1: Ataque rápido
            if distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
                if self.attack_cooldown == 0:
                    self.attack(direction)
                    self.last_action = "ZIG-ATK"
            else:
                self.move_towards(npc.x, npc.y)
                self.last_action = "ZIG-APPROACH"
        else:
            # Fase 2: Movimiento lateral
            angle = math.atan2(direction[1], direction[0]) + math.pi/2
            if self.behavior_timer % 10 < 5:
                angle += math.pi  # Cambiar dirección cada 5 frames
            
            self.vx = math.cos(angle) * self.speed * 0.7
            self.vy = math.sin(angle) * self.speed * 0.7
            self.last_action = "ZIG-ZAG"
    
    def _random_behavior(self, npc, distance, direction):
        """Comportamiento aleatorio."""
        if self.state_timer == 0:
            actions = ["approach", "retreat", "attack", "defend", "circle", "dodge"]
            self.state = random.choice(actions)
            self.state_timer = random.randint(20, 60)
        
        if self.state == "approach":
            self.move_towards(npc.x, npc.y)
            self.last_action = "RAND APPROACH"
        elif self.state == "retreat":
            self.move_away_from(npc.x, npc.y)
            self.last_action = "RAND RETREAT"
        elif self.state == "attack":
            if distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
                if self.attack_cooldown == 0:
                    self.attack(direction)
                    self.last_action = "RAND ATTACK"
        elif self.state == "defend":
            self.defend()
            self.last_action = "RAND DEFEND"
        elif self.state == "circle":
            angle = math.atan2(npc.y - self.y, npc.x - self.x) + 0.05
            self.vx = math.cos(angle) * self.speed * 0.8
            self.vy = math.sin(angle) * self.speed * 0.8
            self.last_action = "RAND CIRCLE"
        elif self.state == "dodge":
            angle = random.uniform(0, math.pi * 2)
            self.vx = math.cos(angle) * self.speed
            self.vy = math.sin(angle) * self.speed
            self.last_action = "RAND DODGE"
    
    def _circle_behavior(self, npc, distance, direction):
        """Se mueve en círculos alrededor del NPC."""
        # Calcular ángulo para movimiento circular
        self.target_angle += 0.05
        if self.target_angle > math.pi * 2:
            self.target_angle -= math.pi * 2
        
        # Radio del círculo
        circle_radius = 150
        target_x = npc.x + math.cos(self.target_angle) * circle_radius
        target_y = npc.y + math.sin(self.target_angle) * circle_radius
        
        self.move_towards(target_x, target_y)
        self.last_action = "CIRCLE MOVE"
        
        # Atacar cuando está de frente al NPC
        angle_to_npc = math.atan2(npc.y - self.y, npc.x - self.x)
        angle_diff = abs(angle_to_npc - self.target_angle)
        if angle_diff < 0.2 and distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "CIRCLE ATK"
    
    def _charge_behavior(self, npc, distance, direction):
        """Carga en línea recta y luego retrocede."""
        if self.state == "charge":
            # Cargar hacia el NPC
            self.vx = direction[0] * self.speed * 1.5
            self.vy = direction[1] * self.speed * 1.5
            self.last_action = "CHARGE!"
            
            # Atacar durante la carga
            if distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
                if self.attack_cooldown == 0:
                    self.attack(direction)
            
            # Cambiar a retroceso después de un tiempo
            self.charge_count += 1
            if self.charge_count > 40:
                self.state = "recover"
                self.charge_count = 0
                self.state_timer = 30
        
        elif self.state == "recover":
            # Retroceder
            self.move_away_from(npc.x, npc.y)
            self.last_action = "RECOVER"
            
            if self.state_timer == 0:
                self.state = "charge"
        
        else:
            self.state = "charge"
    
    def _sniper_behavior(self, npc, distance, direction):
        """Mantiene distancia y ataca desde lejos."""
        desired_distance = self.sniper_distance
        
        if distance > desired_distance + 20:
            # Demasiado lejos, acercarse
            self.move_towards(npc.x, npc.y)
            self.last_action = "SNIPER APPROACH"
        elif distance < desired_distance - 20:
            # Demasiado cerca, alejarse
            self.move_away_from(npc.x, npc.y)
            self.last_action = "SNIPER RETREAT"
        else:
            # Distancia correcta, atacar
            self.stop()
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "SNIPER SHOT"
    
    def _turtle_behavior(self, npc, distance, direction):
        """Defensa extrema: rara vez ataca."""
        if distance < 100:
            # Defenderse agresivamente
            self.defend()
            self.move_away_from(npc.x, npc.y)
            self.last_action = "TURTLE DEF"
        elif self.behavior_timer % 120 == 0:  # Atacar solo cada 2 segundos
            # Ataque lento pero poderoso
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "TURTLE ATK"
        else:
            # Moverse lentamente
            angle = math.atan2(npc.y - self.y, npc.x - self.x) + 0.02
            self.vx = math.cos(angle) * self.speed * 0.5
            self.vy = math.sin(angle) * self.speed * 0.5
            self.last_action = "TURTLE MOVE"
    
    # Nuevos comportamientos
    def _feint_behavior(self, npc, distance, direction):
        """Comportamiento de finta: engaña y contraataca."""
        if self.state == "idle":
            if distance < 130:
                self.state = "feint_attack"
                self.state_timer = 15
                self.feint_count = 0
            else:
                self.move_towards(npc.x, npc.y)
        
        elif self.state == "feint_attack":
            # Falso ataque
            self.attacking = True
            self.attack_direction = direction
            self.last_action = "FEINT ATTACK"
            
            self.feint_count += 1
            if self.feint_count > 10:
                self.state = "real_attack"
                self.state_timer = 5
        
        elif self.state == "real_attack":
            # Ataque real después de la finta
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "REAL ATTACK"
            
            self.state = "retreat"
            self.state_timer = 25
        
        elif self.state == "retreat":
            self.move_away_from(npc.x, npc.y)
            self.last_action = "FEINT RETREAT"
            
            if self.state_timer == 0:
                self.state = "idle"
    
    def _vortex_behavior(self, npc, distance, direction):
        """Movimiento en espiral que se acerca gradualmente."""
        # Calcular ángulo de espiral
        spiral_speed = 0.08
        approach_speed = 0.3
        
        self.target_angle += spiral_speed * self.vortex_direction
        if self.target_angle > math.pi * 2:
            self.target_angle -= math.pi * 2
        
        # Radio que disminuye con el tiempo
        spiral_radius = max(80, 200 - (self.behavior_timer * 0.1))
        
        # Posición en espiral
        spiral_x = npc.x + math.cos(self.target_angle) * spiral_radius
        spiral_y = npc.y + math.sin(self.target_angle) * spiral_radius
        
        # Añadir componente de aproximación
        approach_x = npc.x + direction[0] * approach_speed * 50
        approach_y = npc.y + direction[1] * approach_speed * 50
        
        target_x = (spiral_x * 0.7 + approach_x * 0.3)
        target_y = (spiral_y * 0.7 + approach_y * 0.3)
        
        self.move_towards(target_x, target_y)
        self.last_action = "VORTEX SPIRAL"
        
        # Cambiar dirección de espiral ocasionalmente
        if self.behavior_timer % 200 == 0:
            self.vortex_direction *= -1
        
        # Atacar cuando está bien alineado
        angle_to_npc = math.atan2(npc.y - self.y, npc.x - self.x)
        angle_diff = abs(angle_to_npc - self.target_angle)
        
        if angle_diff < 0.15 and distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "VORTEX ATK"
    
    def _shadow_behavior(self, npc, distance, direction):
        """Imita los movimientos del NPC."""
        if len(self.shadow_memory) > 5:
            # Obtener movimiento reciente del NPC
            recent_memory = list(self.shadow_memory)[-1]
            
            # Calcular dirección para imitar
            mimic_direction = (
                recent_memory['vx'] / max(1, abs(recent_memory['vx'])),
                recent_memory['vy'] / max(1, abs(recent_memory['vy']))
            )
            
            # Moverse en dirección similar
            self.vx = mimic_direction[0] * self.speed * 0.8
            self.vy = mimic_direction[1] * self.speed * 0.8
            
            self.last_action = "SHADOW MIMIC"
            
            # Atacar si el NPC ataca
            if 'ATAQUE' in recent_memory['action'] or 'ATK' in recent_memory['action']:
                if self.attack_cooldown == 0 and distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
                    self.attack(direction)
                    self.last_action = "SHADOW ATK"
        else:
            # Comportamiento por defecto hasta tener suficiente memoria
            self.move_towards(npc.x, npc.y)
            self.last_action = "SHADOW APPROACH"
    
    def _berserk_behavior(self, npc, distance, direction):
        """Comportamiento frenético que mejora con poca salud."""
        # Siempre atacar agresivamente
        if distance < GameConfig.AI_ATTACK_RANGE + npc.radius * 1.2:
            if self.attack_cooldown == 0:
                self.attack(direction)
                self.last_action = "BERSERK ATK"
            
            # Movimiento errático cerca del NPC
            erratic_angle = random.uniform(0, math.pi * 2)
            self.vx = math.cos(erratic_angle) * self.speed * 0.6
            self.vy = math.sin(erratic_angle) * self.speed * 0.6
        else:
            # Cargar hacia el NPC
            charge_multiplier = 1.0 + (1.0 - (self.health / self.max_health)) * 0.8
            self.vx = direction[0] * self.speed * charge_multiplier
            self.vy = direction[1] * self.speed * charge_multiplier
            self.last_action = "BERSERK CHARGE"
        
        # Nunca defenderse
        self.defending = False
    
    def _tactician_behavior(self, npc, distance, direction):
        """Comportamiento táctico que analiza y explota patrones."""
        if not self.tactician_analysis:
            # Comportamiento por defecto hasta tener análisis
            self._aggressive_behavior(npc, distance, direction)
            return
        
        # Usar análisis para elegir estrategia
        predictability = self.tactician_analysis.get('predictability', 0.5)
        attack_freq = self.tactician_analysis.get('attack_frequency', 0.3)
        defense_freq = self.tactician_analysis.get('defense_frequency', 0.3)
        
        if predictability > 0.7:
            # NPC predecible - usar contra-estrategia
            if attack_freq > defense_freq:
                # NPC ataca mucho - defenderse y contraatacar
                if distance < 120:
                    self.defend()
                    if npc.attacking:
                        # Contraataque después de defender
                        self.move_away_from(npc.x, npc.y)
                        self.last_action = "TACTICIAN COUNTER"
                    else:
                        self.attack(direction)
                        self.last_action = "TACTICIAN ATK"
                else:
                    self.move_towards(npc.x, npc.y)
                    self.last_action = "TACTICIAN APPROACH"
            else:
                # NPC se defiende mucho - presionar
                self.move_towards(npc.x, npc.y)
                if distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
                    if self.attack_cooldown == 0:
                        self.attack(direction)
                        self.last_action = "TACTICIAN PRESSURE"
        else:
            # NPC impredecible - usar estrategia conservadora
            if distance < 100:
                self.defend()
                self.move_away_from(npc.x, npc.y)
                self.last_action = "TACTICIAN CAUTIOUS"
            elif distance < GameConfig.AI_ATTACK_RANGE + npc.radius:
                if self.attack_cooldown == 0:
                    self.attack(direction)
                    self.last_action = "TACTICIAN OPPORTUNITY"
            else:
                self.move_towards(npc.x, npc.y)
                self.last_action = "TACTICIAN ADVANCE"
    
    # Métodos de movimiento y combate (mantenidos de la versión original)
    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        self.vx = (dx / dist) * self.speed
        self.vy = (dy / dist) * self.speed
    
    def move_away_from(self, target_x, target_y):
        dx = self.x - target_x
        dy = self.y - target_y
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        self.vx = (dx / dist) * self.speed
        self.vy = (dy / dist) * self.speed
    
    def stop(self):
        self.vx = 0
        self.vy = 0
    
    def attack(self, direction):
        if self.attack_cooldown <= 0 and self.health > 0:
            self.attacking = True
            self.attack_direction = direction
            self.attack_cooldown = GameConfig.AI_ATTACK_COOLDOWN
            self.attacks_made += 1
            return True
        return False
    
    def defend(self):
        self.defending = True
        self.last_action = "Defend"
        self.action_timer = 15
    
    def stop_defend(self):
        self.defending = False
    
    def take_damage(self, amount, attacker=None):
        if self.defending:
            amount *= GameConfig.AI_DEFENSE_REDUCTION
            self.successful_defenses += 1
        
        self.health = max(0, self.health - amount)
        self.damage_taken += amount
        
        if attacker:
            attacker.damage_dealt += amount
        
        return amount
    
    def is_in_attack_range(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        return distance <= GameConfig.AI_ATTACK_RANGE + other.radius
    
    def draw(self, screen, font):
        """Dibuja la máquina con mejoras visuales."""
        # Cuerpo con gradiente
        for i in range(3):
            radius = self.radius - i * 2
            alpha = 200 - i * 40
            color = (
                self.color[0] - i * 20,
                self.color[1] + i * 10,
                self.color[2] - i * 10
            )
            
            circle_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, (color[0], color[1], color[2], alpha), (radius, radius), radius)
            screen.blit(circle_surface, (int(self.x - radius), int(self.y - radius)))
        
        # Borde según estado
        border_color = (255, 255, 255)
        border_width = 2
        
        if self.defending:
            border_color = (255, 150, 100)
            border_width = 4
            # Escudo visual
            shield_surface = pygame.Surface((self.radius*2 + 10, self.radius*2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (255, 150, 100, 80), 
                             (self.radius + 5, self.radius + 5), 
                             self.radius + 5, 3)
            screen.blit(shield_surface, (int(self.x - self.radius - 5), int(self.y - self.radius - 5)))
        
        if self.attacking:
            border_color = (255, 200, 50)
            border_width = 5
            # Visual de ataque
            attack_length = 60
            attack_end_x = self.x + self.attack_direction[0] * attack_length
            attack_end_y = self.y + self.attack_direction[1] * attack_length
            
            for i in range(3):
                line_width = 6 - i * 2
                line_alpha = 200 - i * 50
                line_color = (255, 200 - i*20, 50, line_alpha)
                pygame.draw.line(screen, line_color,
                                (int(self.x), int(self.y)),
                                (int(attack_end_x), int(attack_end_y)), line_width)
        
        pygame.draw.circle(screen, border_color, (int(self.x), int(self.y)), 
                          self.radius, border_width)
        
        # Ojos robóticos (cuadrados)
        eye_size = 8
        eye_color = (255, 255, 255)
        
        # Ojo izquierdo
        pygame.draw.rect(screen, eye_color, 
                        (int(self.x - 12), int(self.y - 10), eye_size, eye_size))
        # Ojo derecho
        pygame.draw.rect(screen, eye_color, 
                        (int(self.x + 4), int(self.y - 10), eye_size, eye_size))
        
        # Indicador de comportamiento BERSERK
        if self.behavior == AIBehavior.BERSERK and self.berserk_multiplier > 1.0:
            berserk_radius = 6
            berserk_color = (255, 50, 50)
            pygame.draw.circle(screen, berserk_color, 
                             (int(self.x), int(self.y + 12)), berserk_radius)
        
        # Nombre y comportamiento
        name = f"MÁQUINA: {self.behavior_text}"
        name_surface = font.render(name, True, (255, 255, 255))
        screen.blit(name_surface, (int(self.x - name_surface.get_width()/2), 
                                  int(self.y - self.radius - 30)))
        
        # Última acción
        if self.action_timer > 0:
            action_surface = font.render(self.last_action, True, (255, 200, 200))
            screen.blit(action_surface, (int(self.x - action_surface.get_width()/2),
                                        int(self.y + self.radius + 8)))
    
    def draw_health_bar(self, screen, x, y, width, height):
        """Dibuja la barra de salud."""
        # Fondo
        pygame.draw.rect(screen, (60, 60, 60), (x, y, width, height))
        pygame.draw.rect(screen, (100, 100, 100), (x, y, width, height), 2)
        
        # Salud actual
        health_ratio = self.health / self.max_health
        health_width = int(width * health_ratio)
        
        # Color según salud
        if health_ratio > 0.6:
            color = (255, 100, 100)  # Rojo para máquina
        elif health_ratio > 0.3:
            color = (255, 150, 100)
        else:
            color = (255, 80, 80)
        
        pygame.draw.rect(screen, color, (x, y, health_width, height))
        
        # Efecto de brillo
        highlight_height = max(1, height // 4)
        highlight_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
        pygame.draw.rect(screen, highlight_color, (x, y, health_width, highlight_height))
        
        # Texto de salud
        health_text = f"{int(self.health)}/{self.max_health}"
        font = pygame.font.Font(None, 22)
        text_surface = font.render(health_text, True, (255, 255, 255))
        screen.blit(text_surface, (x + width//2 - text_surface.get_width()//2,
                                  y + height//2 - text_surface.get_height()//2))

# ============================================
# ARENA SUPER-MEJORADA
# ============================================

class SuperIntelligentAIArena:
    """Arena de combate con NPC super-inteligente."""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GameConfig.WIDTH, GameConfig.HEIGHT))
        pygame.display.set_caption("Neuron657 AI Arena - NPC Super-Inteligente vs Máquina")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "playing"
        
        # Fuentes mejoradas
        try:
            self.font_large = pygame.font.Font(None, 40)
            self.font_medium = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 20)
            self.font_tiny = pygame.font.Font(None, 16)
        except:
            # Fallback a fuentes del sistema
            self.font_large = pygame.font.SysFont('dejavusans', 40, bold=True)
            self.font_medium = pygame.font.SysFont('dejavusans', 28)
            self.font_small = pygame.font.SysFont('dejavusans', 20)
            self.font_tiny = pygame.font.SysFont('dejavusans', 16)
        
        # Arena
        self.arena_rect = pygame.Rect(
            GameConfig.ARENA_PADDING,
            GameConfig.ARENA_PADDING,
            GameConfig.WIDTH - 2 * GameConfig.ARENA_PADDING,
            GameConfig.HEIGHT - 2 * GameConfig.ARENA_PADDING
        )
        
        # Combatientes
        self.npc = SuperIntelligentNPC(
            GameConfig.WIDTH * 0.3,
            GameConfig.HEIGHT * 0.5
        )
        
        # Comportamientos disponibles de la máquina (todos)
        self.all_behaviors = list(AIBehavior)
        self.current_behavior_index = 0
        self.current_behavior = self.all_behaviors[self.current_behavior_index]
        
        # La máquina
        self.machine = AIControlledFighter(
            GameConfig.WIDTH * 0.7,
            GameConfig.HEIGHT * 0.5,
            self.current_behavior
        )
        
        # Ronda actual
        self.round = 1
        self.round_time = 0
        self.max_round_time = GameConfig.MAX_ROUND_TIME * 60
        self.rounds_with_current_behavior = 0
        
        # Resultados
        self.npc_wins = 0
        self.machine_wins = 0
        self.draws = 0
        
        # Estadísticas por comportamiento
        self.behavior_stats = {behavior.value: {"wins": 0, "losses": 0, "draws": 0, "avg_damage": 0} 
                              for behavior in self.all_behaviors}
        
        # Efectos visuales
        self.hit_effects = []
        self.text_effects = []
        self.behavior_change_effects = []
        self.learning_effects = []
        
        # UI
        self.show_stats = True
        self.show_help = False
        self.show_intelligence = True
        self.show_debug = GameConfig.DEBUG_MODE
        self.auto_advance = True
        
        # Historial de aprendizaje
        self.learning_history = []
        
        # Sistema de guardado
        self.last_autosave_time = time.time()
        self.autosave_interval = 45  # Autoguardado cada 45 segundos
        
        print("\n" + "="*70)
        print("🤖 ARENA DE NPC SUPER-INTELIGENTE INICIALIZADA")
        print("="*70)
        print("Sistemas activos:")
        print("  • Meta-aprendizaje con retroalimentación en tiempo real")
        print("  • Generación y validación de hipótesis inteligentes")
        print("  • Transferencia de conocimiento entre comportamientos")
        print("  • Memoria episódica persistente")
        print("  • Sistema de especialización por comportamiento")
        print("  • Auto-evaluación y corrección")
        print(f"  • Comportamientos de máquina: {len(self.all_behaviors)}")
        print("="*70 + "\n")
        
        # Verificar aprendizaje
        self._verify_learning_system()
    
    def _verify_learning_system(self):
        """Verifica que el sistema de aprendizaje esté funcionando."""
        print("🔍 VERIFICANDO SISTEMA DE APRENDIZAJE...")
        
        # Verificar cerebro
        if not self.npc.brain_initialized:
            print("❌ CEREBRO NO INICIALIZADO - El NPC no aprenderá")
            print("   Solución: Verificar que neuron657.py esté en el mismo directorio")
        else:
            print("✅ Cerebro inicializado correctamente")
        
        # Verificar configuración
        config_ok = verify_configuration()
        if not config_ok:
            print("⚠️  Problemas de configuración detectados")
        
        # Verificar archivos de persistencia
        memory_file = GameConfig.MEMORY_FILE
        files_exist = [
            os.path.exists(memory_file),
            os.path.exists(memory_file + ".compactstore"),
            os.path.exists(memory_file + ".index")
        ]
        
        existing_files = sum(files_exist)
        print(f"📁 Archivos de persistencia: {existing_files}/3 existentes")
        
        if existing_files == 3:
            print("✅ Persistencia completa detectada")
        elif existing_files > 0:
            print("⚠️  Persistencia parcial - algunos archivos faltan")
        else:
            print("📝 Creando nueva persistencia...")
        
        print("\n🎮 CONTROLES PRINCIPALES:")
        print("  • H: Ayuda")
        print("  • S: Estadísticas")
        print("  • I: Información de inteligencia")
        print("  • D: Información de debug (si DEBUG_MODE=True)")
        print("  • C: Cambiar comportamiento manualmente")
        print("  • ESPACIO: Pausa")
        print("  • Ctrl+G: Guardar cerebro del NPC")
        print("  • Ctrl+L: Recargar cerebro del NPC")
        print("  • ESC: Salir")
        print("\n")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.reset_combat()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.reset_combat()
                elif event.key == pygame.K_SPACE:
                    self.game_state = "paused" if self.game_state == "playing" else "playing"
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_s:
                    self.show_stats = not self.show_stats
                elif event.key == pygame.K_i:
                    self.show_intelligence = not self.show_intelligence
                elif event.key == pygame.K_d and GameConfig.DEBUG_MODE:
                    self.show_debug = not self.show_debug
                elif event.key == pygame.K_a:
                    self.auto_advance = not self.auto_advance
                elif event.key == pygame.K_n and self.game_state == "game_over":
                    self.next_behavior()
                elif event.key == pygame.K_r and self.game_state == "game_over":
                    self.reset_round()
                elif event.key == pygame.K_c and self.game_state == "playing":
                    self.change_behavior_manual()
                
                # Guardar/recargar cerebro
                elif event.key == pygame.K_g and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.save_npc_brain()
                elif event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.load_npc_brain()
                
                # Debug: forzar aprendizaje
                elif event.key == pygame.K_F1 and GameConfig.DEBUG_MODE:
                    self._debug_force_learning()
                
                # Debug: mostrar estado del NPC
                elif event.key == pygame.K_F2 and GameConfig.DEBUG_MODE:
                    self.npc.debug_learning_status()
    
    def _debug_force_learning(self):
        """Forzar evento de aprendizaje para debug."""
        print("\n🔧 DEBUG: Forzando evento de aprendizaje...")
        
        # Crear resultado simulado
        simulated_outcome = {
            'damage_dealt': random.randint(5, 25),
            'damage_taken': random.randint(5, 20),
            'successful_counter_pattern': random.random() > 0.7,
            'successful_hypothesis': random.random() > 0.8,
            'pattern_learned': random.random() > 0.6,
            'attack_missed': random.random() > 0.5
        }
        
        # Forzar aprendizaje
        self.npc.learn_from_experience(self.machine, simulated_outcome)
        
        print("✅ Evento de aprendizaje forzado completado")
    
    
    def reset_combat(self):
        """Reinicia el combate sin cerrar el juego."""
        self.npc.health = self.npc.max_health
        self.machine.health = self.machine.max_health
        self.npc.x, self.npc.y = 100, GameConfig.HEIGHT // 2
        self.machine.x, self.machine.y = GameConfig.WIDTH - 150, GameConfig.HEIGHT // 2
        self.npc.alive = True
        self.machine.alive = True
        # Cambiamos el comportamiento de la máquina para que el NPC aprenda más
        self.machine.behavior = random.choice(list(BehaviorMode))

    def update(self):
        if self.game_state != "playing":
            return
        
        # Actualizar tiempo de ronda
        self.round_time += 1
        if self.round_time >= self.max_round_time:
            self.end_round("draw")
        
        # Actualizar máquina
        self.machine.update(self.arena_rect, self.npc)
        
        # El NPC decide su acción
        npc_action = self.npc.choose_action(self.machine, self.arena_rect)
        
        # Actualizar NPC
        self.npc.update(self.arena_rect)
        
        # Resolver ataques de la máquina
        if self.machine.attacking and self.npc.is_in_attack_range(self.machine):
            attack_dir = self.machine.attack_direction
            dx = self.npc.x - self.machine.x
            dy = self.npc.y - self.machine.y
            dist = max(1, math.sqrt(dx*dx + dy*dy))
            
            dot_product = (attack_dir[0] * dx/dist) + (attack_dir[1] * dy/dist)
            angle = math.degrees(math.acos(max(-1, min(1, dot_product))))
            
            if angle < 30:  # Dentro del cono de ataque
                damage = self.npc.take_damage(GameConfig.AI_ATTACK_DAMAGE, self.machine)
                self.create_hit_effect(self.npc.x, self.npc.y, damage, "machine")
                self.create_text_effect(f"-{damage:.0f}", self.npc.x, self.npc.y, (255, 100, 100))
                
                # NPC aprende del golpe
                outcome = {
                    'damage_taken': damage,
                    'machine_action': self.machine.last_action,
                    'npc_action': npc_action,
                    'successful_defense': self.npc.defending,
                    'hit_during_charge': self.machine.behavior == AIBehavior.CHARGE and self.machine.state == "charge",
                    'machine_health': self.machine.health
                }
                
                # Verificar tipo de acción para aprendizaje específico
                if isinstance(npc_action, dict):
                    if npc_action.get('type') == 'pattern':
                        outcome['failed_counter_pattern'] = True
                    elif npc_action.get('type') == 'hypothesis':
                        outcome['failed_hypothesis'] = True
                    elif npc_action.get('type') == 'transfer':
                        outcome['failed_transfer'] = True
                
                self.npc.learn_from_experience(self.machine, outcome)
        
        # Resolver ataques del NPC
        if self.npc.attacking and self.machine.is_in_attack_range(self.npc):
            attack_dir = self.npc.attack_direction
            dx = self.machine.x - self.npc.x
            dy = self.machine.y - self.npc.y
            dist = max(1, math.sqrt(dx*dx + dy*dy))
            
            dot_product = (attack_dir[0] * dx/dist) + (attack_dir[1] * dy/dist)
            angle = math.degrees(math.acos(max(-1, min(1, dot_product))))
            
            if angle < 30:  # Dentro del cono de ataque
                damage = self.machine.take_damage(GameConfig.NPC_ATTACK_DAMAGE, self.npc)
                self.create_hit_effect(self.machine.x, self.machine.y, damage, "npc")
                self.create_text_effect(f"-{damage:.0f}", self.machine.x, self.machine.y, (100, 150, 255))
                
                # NPC aprende del éxito
                outcome = {
                    'damage_dealt': damage,
                    'npc_action': npc_action,
                    'attack_missed': False,
                    'attacked_during_opening': self.machine.behavior == AIBehavior.TURTLE and not self.machine.defending,
                    'successful_intercept': self.machine.behavior == AIBehavior.CIRCLE and "INTERCEPT" in self.npc.last_action,
                    'machine_health': self.machine.health,
                    'round_ended': self.machine.health <= 0
                }
                
                # Verificar tipo de acción para aprendizaje específico
                if isinstance(npc_action, dict):
                    if npc_action.get('type') == 'hypothesis':
                        outcome['successful_hypothesis'] = True
                    elif npc_action.get('type') == 'pattern':
                        outcome['successful_counter_pattern'] = True
                    elif npc_action.get('type') == 'transfer':
                        outcome['successful_transfer'] = True
                    elif npc_action.get('type') == 'specialized':
                        outcome['successful_specialized'] = True
                
                self.npc.learn_from_experience(self.machine, outcome)
                self.npc.attacks_hit += 1
            else:
                outcome = {
                    'damage_dealt': 0,
                    'npc_action': npc_action,
                    'attack_missed': True
                }
                self.npc.learn_from_experience(self.machine, outcome)
        
        # Verificar si alguien murió
        if self.npc.health <= 0 and self.machine.health > 0:
            self.end_round("machine_wins")
        elif self.machine.health <= 0 and self.npc.health > 0:
            self.end_round("npc_wins")
        elif self.npc.health <= 0 and self.machine.health <= 0:
            self.end_round("draw")
        
        # Actualizar efectos
        self.update_effects()
        
        # Autoguardado periódico
        current_time = time.time()
        if current_time - self.last_autosave_time > self.autosave_interval:
            self.npc.save_learned_knowledge()
            self.last_autosave_time = current_time
        
        # Registrar progreso de aprendizaje periódico
        if self.round_time % 180 == 0:  # Cada 3 segundos
            self._record_learning_progress()
    
    def _record_learning_progress(self):
        """Registra el progreso del aprendizaje."""
        progress = {
            'round': self.round,
            'behavior': self.current_behavior.value,
            'time': self.round_time / 60,
            'npc_health': self.npc.health,
            'machine_health': self.machine.health,
            'npc_damage_dealt': self.npc.damage_dealt,
            'npc_damage_taken': self.npc.damage_taken,
            'learning_effectiveness': self.npc.learning_effectiveness,
            'decision_confidence': self.npc.decision_confidence,
            'patterns_learned': sum(len(v) for v in self.npc.learned_counter_patterns.values()),
            'hypotheses_tested': len(self.npc.tested_hypotheses),
            'specialized_behaviors': len(self.npc.specialized_behaviors)
        }
        
        self.learning_history.append(progress)
        
        # Mantener historial limitado
        if len(self.learning_history) > 200:
            self.learning_history.pop(0)
    
    def create_hit_effect(self, x, y, damage, source):
        intensity = min(1.0, damage / 30)
        color = (255, 100, 50) if source == "machine" else (100, 150, 255)
        
        # Crear múltiples círculos concéntricos
        for i in range(3):
            radius = 20 + intensity * 30 + i * 8
            alpha = 200 - i * 60
            
            self.hit_effects.append({
                'x': x,
                'y': y,
                'radius': radius,
                'alpha': alpha,
                'color': color,
                'growth': 1.0 + i * 0.3
            })
    
    def create_text_effect(self, text, x, y, color):
        self.text_effects.append({
            'text': text,
            'x': x,
            'y': y,
            'color': color,
            'timer': 70,
            'velocity_y': -1.8,
            'velocity_x': random.uniform(-0.5, 0.5)
        })
    
    def create_learning_effect(self, x, y, text):
        """Crea efecto visual para eventos de aprendizaje."""
        self.learning_effects.append({
            'text': text,
            'x': x,
            'y': y,
            'timer': 90,
            'velocity_y': -1.2,
            'size': 22,
            'color': (180, 220, 255)
        })
    
    def update_effects(self):
        # Actualizar efectos de golpe
        for effect in self.hit_effects[:]:
            effect['alpha'] -= 6
            effect['radius'] += effect.get('growth', 1.0)
            if effect['alpha'] <= 0:
                self.hit_effects.remove(effect)
        
        # Actualizar efectos de texto
        for text_effect in self.text_effects[:]:
            text_effect['y'] += text_effect['velocity_y']
            text_effect['x'] += text_effect.get('velocity_x', 0)
            text_effect['timer'] -= 1
            if text_effect['timer'] <= 0:
                self.text_effects.remove(text_effect)
        
        # Actualizar efectos de aprendizaje
        for learning_effect in self.learning_effects[:]:
            learning_effect['y'] += learning_effect['velocity_y']
            learning_effect['timer'] -= 1
            if learning_effect['timer'] <= 0:
                self.learning_effects.remove(learning_effect)
        
        # Actualizar efectos de cambio de comportamiento
        for effect in self.behavior_change_effects[:]:
            effect['timer'] -= 1
            if effect['timer'] <= 0:
                self.behavior_change_effects.remove(effect)
    
    def end_round(self, result):
        self.game_state = "game_over"
        
        # Actualizar estadísticas
        behavior_key = self.current_behavior.value
        stats = self.behavior_stats[behavior_key]
        
        if result == "npc_wins":
            self.npc_wins += 1
            stats["losses"] += 1
            
            # Gran recompensa para el NPC
            final_outcome = {
                'damage_dealt': self.npc.damage_dealt,
                'damage_taken': self.npc.damage_taken,
                'round_won': True,
                'machine_health': 0,
                'successful_adaptation': True
            }
            self.npc.learn_from_experience(self.machine, final_outcome)
            
            # Efecto visual
            self.create_learning_effect(self.npc.x, self.npc.y, "¡VICTORIA! + Aprendizaje")
            
        elif result == "machine_wins":
            self.machine_wins += 1
            stats["wins"] += 1
            
            # Penalización para el NPC
            final_outcome = {
                'damage_dealt': self.npc.damage_dealt,
                'damage_taken': self.npc.damage_taken,
                'round_lost': True,
                'machine_health': self.machine.health,
                'failed_adaptation': True
            }
            self.npc.learn_from_experience(self.machine, final_outcome)
            
            # Efecto visual
            self.create_learning_effect(self.machine.x, self.machine.y, "Derrota - Ajustando estrategia")
            
        else:
            self.draws += 1
            stats["draws"] += 1
        
        # Actualizar daño promedio
        total_damage = self.npc.damage_dealt + self.npc.damage_taken
        stats["avg_damage"] = (stats["avg_damage"] * (stats["wins"] + stats["losses"] + stats["draws"] - 1) + total_damage) / (stats["wins"] + stats["losses"] + stats["draws"])
        
        # Forzar guardado al final de la ronda
        self.npc.save_learned_knowledge()
        
        # Avanzar automáticamente si está habilitado
        if self.auto_advance:
            self.rounds_with_current_behavior += 1
            if self.rounds_with_current_behavior >= GameConfig.ROUNDS_PER_BEHAVIOR:
                self.next_behavior()
    
    def reset_round(self):
        # Resetear NPC
        self.npc.x = GameConfig.WIDTH * 0.3
        self.npc.y = GameConfig.HEIGHT * 0.5
        self.npc.health = self.npc.max_health
        self.npc.attacking = False
        self.npc.defending = False
        self.npc.vx = 0
        self.npc.vy = 0
        self.npc.damage_dealt = 0
        self.npc.damage_taken = 0
        self.npc.attack_cooldown = 0
        
        # Resetear máquina
        self.machine.x = GameConfig.WIDTH * 0.7
        self.machine.y = GameConfig.HEIGHT * 0.5
        self.machine.health = self.machine.max_health
        self.machine.attacking = False
        self.machine.defending = False
        self.machine.vx = 0
        self.machine.vy = 0
        self.machine.attack_cooldown = 0
        
        # Resetear estado del juego
        self.game_state = "playing"
        self.round_time = 0
        
        # Limpiar efectos
        self.hit_effects.clear()
        self.text_effects.clear()
        self.learning_effects.clear()
        
        # Resetear metas para nueva ronda
        self.npc.goal_system.reset()
    
    def next_behavior(self):
        """Cambia al siguiente comportamiento de la máquina."""
        old_behavior = self.current_behavior
        
        self.current_behavior_index = (self.current_behavior_index + 1) % len(self.all_behaviors)
        self.current_behavior = self.all_behaviors[self.current_behavior_index]
        self.machine.behavior = self.current_behavior
        self.machine.behavior_text = self.current_behavior.value.upper()
        
        # Reiniciar estado de la máquina
        self.machine.state = "idle"
        self.machine.state_timer = 0
        self.machine.pattern_step = 0
        self.machine.adaptive_behaviors = []  # Reset para comportamiento ADAPTIVE
        self.machine.current_adaptive_index = 0
        self.machine.adaptive_timer = 0
        
        self.rounds_with_current_behavior = 0
        self.round += 1
        
        # Efecto visual de cambio
        self.behavior_change_effects.append({
            'text': f"NUEVO COMPORTAMIENTO: {self.current_behavior.value.upper()}",
            'timer': 180,
            'y': 100
        })
        
        # Transferir conocimiento del comportamiento anterior si es similar
        if old_behavior in self.npc.similar_behaviors:
            if self.current_behavior in self.npc.similar_behaviors[old_behavior]:
                transferred = self.npc.transfer_knowledge(old_behavior, self.current_behavior)
                if transferred > 0:
                    self.create_learning_effect(
                        GameConfig.WIDTH // 2,
                        GameConfig.HEIGHT // 2,
                        f"🔄 Transferidos {transferred} patrones"
                    )
        
        self.reset_round()
    
    def change_behavior_manual(self):
        """Cambia el comportamiento manualmente durante el juego."""
        old_behavior = self.current_behavior
        self.next_behavior()
        
        # Mostrar transferencia si aplica
        if old_behavior in self.npc.similar_behaviors:
            if self.current_behavior in self.npc.similar_behaviors[old_behavior]:
                self.create_text_effect(
                    f"TRANSFERENCIA: {old_behavior.value}→{self.current_behavior.value}", 
                    GameConfig.WIDTH//2, GameConfig.HEIGHT//2,
                    (255, 200, 100)
                )
        else:
            self.create_text_effect(
                f"COMPORTAMIENTO: {self.current_behavior.value}", 
                GameConfig.WIDTH//2, GameConfig.HEIGHT//2,
                (255, 200, 100)
            )
    
    def save_npc_brain(self):
        if self.npc.brain_initialized:
            try:
                # Forzar guardado completo
                self.npc.save_learned_knowledge()
                
                # Consolidar
                if self.npc.brain:
                    self.npc.brain.nip.CONSOLIDATE().result()
                
                print("💾 Cerebro del NPC super-inteligente guardado.")
                self.create_learning_effect(
                    GameConfig.WIDTH//2, GameConfig.HEIGHT//2,
                    "💾 Cerebro Guardado"
                )
            except Exception as e:
                print(f"❌ Error guardando cerebro: {e}")
                self.create_text_effect(
                    f"Error guardando: {str(e)[:20]}",
                    GameConfig.WIDTH//2, GameConfig.HEIGHT//2,
                    (255, 100, 100)
                )
    
    def load_npc_brain(self):
        if NEURON657_AVAILABLE:
            try:
                # Guardar posición actual
                old_x, old_y = self.npc.x, self.npc.y
                
                # Crear nuevo NPC (cargará cerebro automáticamente)
                self.npc = SuperIntelligentNPC(old_x, old_y)
                
                print("📂 Cerebro del NPC super-inteligente recargado.")
                self.create_learning_effect(
                    GameConfig.WIDTH//2, GameConfig.HEIGHT//2,
                    "📂 Cerebro Recargado"
                )
            except Exception as e:
                print(f"❌ Error cargando cerebro: {e}")
                self.create_text_effect(
                    f"Error cargando: {str(e)[:20]}",
                    GameConfig.WIDTH//2, GameConfig.HEIGHT//2,
                    (255, 100, 100)
                )
    
    def draw(self):
        # Fondo
        self.screen.fill(GameConfig.BACKGROUND)
        self.draw_advanced_grid()
        
        # Dibujar arena
        pygame.draw.rect(self.screen, GameConfig.ARENA_COLOR, self.arena_rect)
        pygame.draw.rect(self.screen, GameConfig.UI_BORDER, self.arena_rect, 4)
        
        # Dibujar efectos
        self.draw_effects()
        
        # Dibujar combatientes
        self.npc.draw(self.screen, self.font_medium)
        self.machine.draw(self.screen, self.font_medium)
        
        # Dibujar UI
        self.draw_advanced_ui()
        
        # Dibujar HUD de inteligencia si está activado
        if self.show_intelligence:
            self.npc.draw_intelligence_hud(self.screen, 20, 140, self.font_tiny)
        
        # Dibujar debug info si está activado
        if self.show_debug and GameConfig.DEBUG_MODE:
            self.npc.draw_debug_info(self.screen, 20, 400, self.font_tiny)
        
        # Efectos de cambio de comportamiento
        for effect in self.behavior_change_effects:
            text_surface = self.font_medium.render(effect['text'], True, (255, 200, 100))
            alpha = min(255, effect['timer'] * 2)
            text_surface.set_alpha(alpha)
            self.screen.blit(text_surface,
                           (GameConfig.WIDTH//2 - text_surface.get_width()//2,
                            effect['y']))
        
        if self.game_state == "paused":
            self.draw_pause_screen()
        elif self.game_state == "game_over":
            self.draw_game_over_screen()
        
        if self.show_help:
            self.draw_help_screen()
        
        pygame.display.flip()
    
    def draw_advanced_grid(self):
        """Dibuja una cuadrícula más avanzada."""
        grid_size = 40
        
        # Líneas principales
        for x in range(0, GameConfig.WIDTH, grid_size):
            alpha = 100 if x % (grid_size * 5) == 0 else 40
            pygame.draw.line(self.screen, (*GameConfig.GRID_COLOR, alpha), 
                           (x, 0), (x, GameConfig.HEIGHT), 1)
        
        for y in range(0, GameConfig.HEIGHT, grid_size):
            alpha = 100 if y % (grid_size * 5) == 0 else 40
            pygame.draw.line(self.screen, (*GameConfig.GRID_COLOR, alpha), 
                           (0, y), (GameConfig.WIDTH, y), 1)
        
        # Puntos de intersección
        for x in range(grid_size, GameConfig.WIDTH, grid_size * 2):
            for y in range(grid_size, GameConfig.HEIGHT, grid_size * 2):
                pygame.draw.circle(self.screen, (*GameConfig.GRID_COLOR, 30), (x, y), 1)
    
    def draw_effects(self):
        """Dibuja todos los efectos visuales."""
        # Efectos de golpe
        for effect in self.hit_effects:
            alpha_surface = pygame.Surface((effect['radius']*2, effect['radius']*2), pygame.SRCALPHA)
            pygame.draw.circle(alpha_surface, (*effect['color'], effect['alpha']),
                             (effect['radius'], effect['radius']), effect['radius'])
            self.screen.blit(alpha_surface, 
                           (effect['x'] - effect['radius'], effect['y'] - effect['radius']))
        
        # Efectos de texto
        for text_effect in self.text_effects:
            text_font = pygame.font.Font(None, 22)
            text_surface = text_font.render(text_effect['text'], True, text_effect['color'])
            alpha = min(255, text_effect['timer'] * 4)
            text_surface.set_alpha(alpha)
            self.screen.blit(text_surface,
                           (text_effect['x'] - text_surface.get_width()//2,
                            text_effect['y'] - text_surface.get_height()//2))
        
        # Efectos de aprendizaje
        for learning_effect in self.learning_effects:
            text_font = pygame.font.Font(None, int(learning_effect['size']))
            text_surface = text_font.render(learning_effect['text'], True, learning_effect['color'])
            alpha = min(255, learning_effect['timer'] * 3)
            text_surface.set_alpha(alpha)
            self.screen.blit(text_surface,
                           (learning_effect['x'] - text_surface.get_width()//2,
                            learning_effect['y'] - text_surface.get_height()//2))
    
    def draw_advanced_ui(self):
        """Dibuja la interfaz de usuario avanzada."""
        # Panel superior
        panel_height = 90
        panel_rect = pygame.Rect(0, 0, GameConfig.WIDTH, panel_height)
        
        panel_surface = pygame.Surface((GameConfig.WIDTH, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (*GameConfig.UI_BG[:3], 190), panel_surface.get_rect())
        self.screen.blit(panel_surface, (0, 0))
        pygame.draw.rect(self.screen, GameConfig.UI_BORDER, panel_rect, 3)
        
        # Información de ronda y comportamiento
        round_text = self.font_medium.render(f"Ronda {self.round}", True, GameConfig.TEXT_COLOR)
        self.screen.blit(round_text, (25, 25))
        
        behavior_text = self.font_medium.render(
            f"Comportamiento: {self.current_behavior.value.upper()}", 
            True, GameConfig.TEXT_COLOR
        )
        self.screen.blit(behavior_text, (GameConfig.WIDTH//2 - behavior_text.get_width()//2, 25))
        
        # Tiempo
        time_left = max(0, (self.max_round_time - self.round_time) // 60)
        time_color = (255, 255, 255) if time_left > 10 else (255, 150, 150)
        time_text = self.font_medium.render(f"Tiempo: {time_left}s", True, time_color)
        self.screen.blit(time_text, (GameConfig.WIDTH - time_text.get_width() - 25, 25))
        
        # Marcador mejorado
        score_text = self.font_medium.render(
            f"NPC: {self.npc_wins} | Máquina: {self.machine_wins} | Empates: {self.draws}",
            True, GameConfig.TEXT_COLOR
        )
        self.screen.blit(score_text, (GameConfig.WIDTH//2 - score_text.get_width()//2, 60))
        
        # Rondas con comportamiento actual
        rounds_text = self.font_small.render(
            f"Rondas con este comportamiento: {self.rounds_with_current_behavior}/{GameConfig.ROUNDS_PER_BEHAVIOR}",
            True, (180, 200, 255)
        )
        self.screen.blit(rounds_text, (GameConfig.WIDTH//2 - rounds_text.get_width()//2, 85))
        
        # Estado del aprendizaje
        if self.npc.learning_enabled:
            if self.npc.brain_initialized:
                status_color = (100, 255, 150) if self.npc.learning_effectiveness > 0.6 else (255, 200, 100)
                status_text = f"🧠 APRENDIZAJE ACTIVO | Efectividad: {self.npc.learning_effectiveness:.0%} | Confianza: {self.npc.decision_confidence:.0%}"
                status_surface = self.font_small.render(status_text, True, status_color)
                self.screen.blit(status_surface, (GameConfig.WIDTH//2 - status_surface.get_width()//2, 110))
            else:
                status_text = "🧠 CEREBRO NO INICIALIZADO - Modo simple"
                status_surface = self.font_small.render(status_text, True, (255, 150, 100))
                self.screen.blit(status_surface, (GameConfig.WIDTH//2 - status_surface.get_width()//2, 110))
        
        # Barras de salud mejoradas
        health_bar_width = 320
        health_bar_height = 24
        health_bar_margin = 15
        
        # Salud NPC (izquierda)
        npc_health_x = 25
        npc_health_y = panel_height + health_bar_margin
        self.npc.draw_health_bar(self.screen, npc_health_x, npc_health_y,
                                health_bar_width, health_bar_height)
        
        npc_label = self.font_small.render("NPC (SUPER-INTELIGENTE)", True, GameConfig.NPC_COLOR)
        self.screen.blit(npc_label, (npc_health_x, npc_health_y - 22))
        
        # Estadísticas NPC
        npc_stats = self.font_tiny.render(
            f"Ataques: {self.npc.attacks_hit}/{self.npc.attacks_made} | "
            f"Daño: {self.npc.damage_dealt:.0f}/{self.npc.damage_taken:.0f} | "
            f"Defensas: {self.npc.successful_defenses}",
            True, (180, 200, 255)
        )
        self.screen.blit(npc_stats, (npc_health_x, npc_health_y + health_bar_height + 2))
        
        # Salud Máquina (derecha)
        machine_health_x = GameConfig.WIDTH - health_bar_width - 25
        machine_health_y = panel_height + health_bar_margin
        self.machine.draw_health_bar(self.screen, machine_health_x, machine_health_y,
                                    health_bar_width, health_bar_height)
        
        machine_label = self.font_small.render(f"MÁQUINA ({self.current_behavior.value})", 
                                              True, GameConfig.AI_COLOR)
        self.screen.blit(machine_label, (machine_health_x, machine_health_y - 22))
        
        # Estadísticas máquina
        machine_stats = self.font_tiny.render(
            f"Ataques: {self.machine.attacks_hit}/{self.machine.attacks_made} | "
            f"Daño: {self.machine.damage_dealt:.0f}/{self.machine.damage_taken:.0f} | "
            f"Defensas: {self.machine.successful_defenses}",
            True, (255, 200, 200)
        )
        self.screen.blit(machine_stats, (machine_health_x, machine_health_y + health_bar_height + 2))
        
        # Estadísticas avanzadas
        if self.show_stats:
            self.draw_advanced_stats_panel()
        
        # Instrucciones mejoradas
        controls_lines = [
            "H: Ayuda | S: Stats | I: Inteligencia | D: Debug | C: Cambiar comportamiento",
            "ESPACIO: Pausa | Ctrl+G: Guardar | Ctrl+L: Recargar | ESC: Salir"
        ]
        
        for i, line in enumerate(controls_lines):
            controls_text = self.font_tiny.render(line, True, (180, 200, 220))
            self.screen.blit(controls_text,
                            (GameConfig.WIDTH//2 - controls_text.get_width()//2,
                             GameConfig.HEIGHT - 40 + i * 18))
    
    def draw_advanced_stats_panel(self):
        """Dibuja panel de estadísticas avanzadas."""
        panel_width = 380
        panel_height = 280
        panel_x = GameConfig.WIDTH - panel_width - 25
        panel_y = 140
        
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (*GameConfig.UI_BG[:3], 210), 
                        panel_surface.get_rect(), border_radius=12)
        pygame.draw.rect(panel_surface, GameConfig.UI_BORDER,
                        panel_surface.get_rect(), 2, border_radius=12)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Título
        title = self.font_medium.render("ESTADÍSTICAS AVANZADAS", True, (230, 230, 255))
        self.screen.blit(title, (panel_x + panel_width//2 - title.get_width()//2, panel_y + 12))
        
        # Sección 1: Estadísticas del NPC
        section1_y = panel_y + 45
        section1_title = self.font_small.render("🧠 NPC INTELIGENTE", True, (180, 220, 255))
        self.screen.blit(section1_title, (panel_x + 15, section1_y))
        
        npc_stats = [
            f"• Efectividad aprendizaje: {self.npc.learning_effectiveness:.2f}",
            f"• Confianza decisión: {self.npc.decision_confidence:.2f}",
            f"• Tasa exploración: {self.npc.exploration_rate:.2f}",
            f"• Patrones aprendidos: {sum(len(v) for v in self.npc.learned_counter_patterns.values())}",
            f"• Hipótesis probadas: {len(self.npc.tested_hypotheses)}",
            f"• Transferencias: {len(self.npc.knowledge_base)}",
            f"• Adaptaciones exitosas: {self.npc.successful_adaptations}",
            f"• Comportamientos especializados: {len(self.npc.specialized_behaviors)}"
        ]
        
        for i, stat in enumerate(npc_stats):
            stat_text = self.font_tiny.render(stat, True, (200, 210, 240))
            self.screen.blit(stat_text, (panel_x + 25, section1_y + 20 + i * 16))
        
        # Sección 2: Comportamiento actual
        section2_y = section1_y + 20 + len(npc_stats) * 16 + 10
        behavior_stats = self.behavior_stats[self.current_behavior.value]
        
        section2_title = self.font_small.render(f"📊 {self.current_behavior.value.upper()}", True, (255, 200, 180))
        self.screen.blit(section2_title, (panel_x + 15, section2_y))
        
        behavior_stat_lines = [
            f"• Victorias NPC: {behavior_stats['losses']}",
            f"• Victorias Máquina: {behavior_stats['wins']}",
            f"• Empates: {behavior_stats['draws']}",
            f"• Daño promedio/ronda: {behavior_stats['avg_damage']:.1f}"
        ]
        
        for i, line in enumerate(behavior_stat_lines):
            line_text = self.font_tiny.render(line, True, (220, 210, 200))
            self.screen.blit(line_text, (panel_x + 25, section2_y + 20 + i * 16))
        
        # Barra de progreso de experiencia
        progress_y = panel_y + panel_height - 35
        progress_width = panel_width - 30
        progress_height = 12
        
        # Calcular experiencia total
        total_experience = (
            self.npc.total_learning_cycles +
            sum(len(v) for v in self.npc.learned_counter_patterns.values()) * 10 +
            len(self.npc.tested_hypotheses) * 5 +
            len(self.npc.knowledge_base) * 15
        )
        experience_ratio = min(1.0, total_experience / 2000)
        
        pygame.draw.rect(self.screen, (60, 60, 80),
                       (panel_x + 15, progress_y, progress_width, progress_height))
        
        progress_color = (
            int(100 + 155 * self.npc.learning_effectiveness),
            int(100 + 155 * experience_ratio),
            200
        )
        
        pygame.draw.rect(self.screen, progress_color,
                       (panel_x + 15, progress_y, progress_width * experience_ratio, progress_height))
        
        pygame.draw.rect(self.screen, (100, 100, 120),
                       (panel_x + 15, progress_y, progress_width, progress_height), 1)
        
        progress_text = f"EXPERIENCIA TOTAL: {total_experience}"
        progress_surface = self.font_tiny.render(progress_text, True, (180, 220, 255))
        self.screen.blit(progress_surface, (panel_x + 15, progress_y - 18))
    
    def draw_pause_screen(self):
        overlay = pygame.Surface((GameConfig.WIDTH, GameConfig.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("PAUSA", True, (255, 255, 255))
        self.screen.blit(pause_text,
                        (GameConfig.WIDTH//2 - pause_text.get_width()//2,
                         GameConfig.HEIGHT//2 - 80))
        
        # Mostrar estadísticas de aprendizaje en pausa
        learning_stats = [
            f"Efectividad aprendizaje: {self.npc.learning_effectiveness:.0%}",
            f"Patrones aprendidos: {sum(len(v) for v in self.npc.learned_counter_patterns.values())}",
            f"Hipótesis probadas: {len(self.npc.tested_hypotheses)}",
            f"Adaptaciones exitosas: {self.npc.successful_adaptations}",
            f"Comportamientos especializados: {len(self.npc.specialized_behaviors)}"
        ]
        
        for i, stat in enumerate(learning_stats):
            stat_surface = self.font_medium.render(stat, True, (200, 220, 255))
            self.screen.blit(stat_surface,
                            (GameConfig.WIDTH//2 - stat_surface.get_width()//2,
                             GameConfig.HEIGHT//2 - 30 + i * 30))
        
        continue_text = self.font_medium.render("Presiona ESPACIO para continuar", 
                                               True, (200, 200, 255))
        self.screen.blit(continue_text,
                        (GameConfig.WIDTH//2 - continue_text.get_width()//2,
                         GameConfig.HEIGHT//2 + 120))
    
    def draw_game_over_screen(self):
        overlay = pygame.Surface((GameConfig.WIDTH, GameConfig.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Determinar resultado
        if self.npc.health <= 0 and self.machine.health > 0:
            result_text = "MÁQUINA GANA"
            result_color = (255, 100, 100)
        elif self.machine.health <= 0 and self.npc.health > 0:
            result_text = "NPC GANA"
            result_color = (100, 200, 255)
        else:
            result_text = "EMPATE"
            result_color = (200, 200, 200)
        
        result_surface = self.font_large.render(result_text, True, result_color)
        self.screen.blit(result_surface,
                        (GameConfig.WIDTH//2 - result_surface.get_width()//2,
                         GameConfig.HEIGHT//2 - 60))
        
        # Estadísticas de la ronda
        round_stats = [
            f"Daño infligido por NPC: {self.npc.damage_dealt:.0f}",
            f"Daño recibido por NPC: {self.npc.damage_taken:.0f}",
            f"Precisión NPC: {self.npc.attacks_hit/max(1, self.npc.attacks_made)*100:.1f}%",
            f"Tiempo de ronda: {self.round_time//60}s"
        ]
        
        for i, stat in enumerate(round_stats):
            stat_surface = self.font_medium.render(stat, True, (220, 220, 240))
            self.screen.blit(stat_surface,
                            (GameConfig.WIDTH//2 - stat_surface.get_width()//2,
                             GameConfig.HEIGHT//2 + i * 30))
        
        # Instrucciones
        instructions = [
            "Presiona R para reiniciar ronda",
            "Presiona N para siguiente comportamiento",
            "Presiona ESPACIO para continuar"
        ]
        
        for i, instruction in enumerate(instructions):
            instr_surface = self.font_small.render(instruction, True, (180, 200, 220))
            self.screen.blit(instr_surface,
                            (GameConfig.WIDTH//2 - instr_surface.get_width()//2,
                             GameConfig.HEIGHT//2 + 150 + i * 25))
    
    def draw_help_screen(self):
        overlay = pygame.Surface((GameConfig.WIDTH, GameConfig.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        help_title = self.font_large.render("AYUDA - NPC SUPER-INTELIGENTE", True, (255, 255, 255))
        self.screen.blit(help_title,
                        (GameConfig.WIDTH//2 - help_title.get_width()//2, 50))
        
        # Controles
        controls_section = self.font_medium.render("🎮 CONTROLES", True, (255, 220, 180))
        self.screen.blit(controls_section,
                        (GameConfig.WIDTH//2 - controls_section.get_width()//2, 120))
        
        controls = [
            "H: Mostrar/ocultar esta ayuda",
            "S: Mostrar/ocultar estadísticas",
            "I: Mostrar/ocultar información de inteligencia",
            "D: Mostrar/ocultar información de debug",
            "C: Cambiar comportamiento de la máquina",
            "ESPACIO: Pausar/reanudar",
            "Ctrl+G: Guardar cerebro del NPC",
            "Ctrl+L: Recargar cerebro del NPC",
            "ESC: Salir del juego"
        ]
        
        for i, control in enumerate(controls):
            control_surface = self.font_small.render(control, True, (200, 220, 255))
            self.screen.blit(control_surface,
                            (GameConfig.WIDTH//2 - control_surface.get_width()//2,
                             160 + i * 28))
        
        # Sistemas de aprendizaje
        systems_section = self.font_medium.render("🧠 SISTEMAS DE APRENDIZAJE", True, (180, 220, 255))
        self.screen.blit(systems_section,
                        (GameConfig.WIDTH//2 - systems_section.get_width()//2, 420))
        
        systems = [
            "• Meta-aprendizaje: Ajusta parámetros basado en éxito",
            "• Generación de hipótesis: Prueba estrategias nuevas",
            "• Transferencia de conocimiento: Aplica aprendizaje entre comportamientos",
            "• Memoria episódica: Recuerda experiencias pasadas",
            "• Especialización: Mejora contra comportamientos específicos",
            "• Auto-evaluación: Corrige errores y refina estrategias"
        ]
        
        for i, system in enumerate(systems):
            system_surface = self.font_small.render(system, True, (200, 230, 200))
            self.screen.blit(system_surface,
                            (GameConfig.WIDTH//2 - system_surface.get_width()//2,
                             460 + i * 26))
        
        # Cerrar ayuda
        close_text = self.font_medium.render("Presiona H para cerrar ayuda", True, (255, 200, 100))
        self.screen.blit(close_text,
                        (GameConfig.WIDTH//2 - close_text.get_width()//2,
                         GameConfig.HEIGHT - 60))
    
    def run(self):
        """Bucle principal del juego."""
        print("\n🚀 INICIANDO ARENA DE NPC SUPER-INTELIGENTE")
        print("   El NPC comenzará a aprender y mejorar inmediatamente.")
        print("   Observa cómo desarrolla estrategias contra cada comportamiento.\n")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(GameConfig.FPS)
        
        # Guardar al cerrar
        self.save_npc_brain()
        self.reset_combat() # Reinicio infinito

def reset_combat(self):
        """Reinicia el combate para entrenamiento infinito."""
        self.npc.health = self.npc.max_health
        self.machine.health = self.machine.max_health
        self.npc.x, self.npc.y = 100, GameConfig.HEIGHT // 2
        self.machine.x, self.machine.y = GameConfig.WIDTH - 150, GameConfig.HEIGHT // 2
        self.npc.alive = True
        self.machine.alive = True
        
        # FIX: Acceso seguro a BehaviorMode
        try:
            # Intentamos usar el nombre global, si falla usamos el de la clase
            self.machine.behavior = random.choice(list(BehaviorMode))
        except NameError:
            # Si BehaviorMode está dentro de otra estructura, esto lo rescata
            from life import BehaviorMode
            self.machine.behavior = random.choice(list(BehaviorMode))
        
        print(f"🔄 Reinicio exitoso. Modo máquina: {self.machine.behavior}")
# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

def run(self):
        """Bucle principal del juego."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(GameConfig.FPS)
        
        self.save_npc_brain()
        pygame.quit()
        sys.exit() # <--- AQUÍ TERMINA EL MÉTODO RUN

# Fuera de la clase, al final de todo el archivo:
if __name__ == "__main__":
    try:
        arena = SuperIntelligentAIArena()
        arena.run()
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()