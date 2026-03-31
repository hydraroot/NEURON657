# NEURON657 — General-Purpose Cognitive Architecture

PARA VER EN ESPAÑOL IR A LINEA 280

[![Neuron657 vs FSM](https://img.youtube.com/vi/XzNyIML9Go8/hqdefault.jpg)](https://www.youtube.com/watch?v=XzNyIML9Go8)

<div align="center">

**Version 13.2 · Bio-Inspired Adaptive Decision-Making**

[![License: AGPLv3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Status: Active](https://img.shields.io/badge/status-active-green.svg)]()

*Created by [Walter Diego Spaltro](https://www.linkedin.com/in/walter-diego-spaltro-2942b2178/) · wds657@hotmail.com*

</div>

---

## What is NEURON657?

NEURON657 is a **general-purpose cognitive architecture** designed for adaptive decision-making in complex, uncertain environments. Unlike traditional AI approaches (FSMs, behavior trees, or pure reinforcement learning), NEURON657 produces behavior that **emerges from the continuous interaction** between internal state variables, predictive world modeling, and meta-cognitive monitoring — no hardcoded rules required.

> **Core Innovation:** Decisions arise from biological-inspired state dynamics, a Free Energy Principle implementation for surprise minimization, and multi-tier memory systems that learn and adapt across sessions.

---

## Where Can NEURON657 Be Used?

NEURON657 is **domain-agnostic**. The same architecture runs across:

| Domain | Description |
|---|---|
| 🎮 **Game AI / NPCs** | Characters that adapt to player behavior without manual scripting. Demonstrated with full tactical combat (fear, aggression, curiosity drives). |
| 🤖 **Robotics** | Decision-making for robots in uncertain, dynamic environments. World model handles sensor uncertainty; meta-learner adapts control strategies. |
| 🏭 **Process Automation** | Business workflows that learn optimal strategies from experience under variable load, urgency, and resource availability. |
| 🖥️ **Adaptive Interfaces** | UI systems that model user intent and expertise level to adjust interaction patterns in real time. |
| 🎯 **Simulation & Training** | Realistic agent behaviors for military, medical, or emergency scenarios requiring human-like decisions under stress. |
| 🤝 **Multi-Agent Systems** | Multiple NEURON657 instances coordinate via Theory of Mind — no central controller needed. |

---

## Architecture Overview

NEURON657 processes information through **nine interconnected subsystems**:

```
Input → [Attention] → [World Model + Self Model] → [Planner]
                                    ↓
              [Free Energy Manager] ← [Meta-Learner]
                                    ↓
         [Strategy Selector] → [Execution Mode] → Output
                    ↑
          [Memory: STM / Episodic / Identity]
```

### Core Subsystems

| Subsystem | Role |
|---|---|
| **Working Memory (STM)** | High-speed pattern cache with HDC (Hyperdimensional Computing) vectors |
| **Episodic Memory** | Time-indexed experience storage for temporal reasoning and learning |
| **Identity Memory** | Long-term goal tracking and belief persistence across sessions |
| **World Model** | Predictive model of environment dynamics with Bayesian uncertainty |
| **Self Model** | Introspective model of own capabilities; enables meta-cognitive monitoring |
| **Theory of Mind** | Reasoning about other agents' beliefs, goals, and intentions |
| **Free Energy Manager** | Implements the Free Energy Principle — minimizes surprise automatically |
| **Meta-Learner** | Learns which strategies work best in which contexts across episodes |
| **Cognitive Planner** | Multi-step forward planning with MCTS; adapts depth to urgency |

### Cognitive Modes

| Mode | When Used |
|---|---|
| `AUTONOMOUS` | Self-directed operation pursuing internal goals |
| `REASONING` | Deep deliberation for complex decisions |
| `META_LEARNING` | Active strategy profile optimization |
| `SAFE_RECOVERY` | Fallback to conservative heuristics under high failure risk |
| `ADAPTIVE` | Aggressive adaptation triggered by high aggression or winning state |

---

## Key Technical Advantages

### vs. Finite State Machines
- No hardcoded transitions — behavior emerges from continuous state space
- Smooth, graded transitions instead of discrete switches
- No exponential state explosion with multi-dimensional context

### vs. Behavior Trees
- No manual priority assignment — priorities emerge from internal drives
- Learns optimal action selection without redesigning the tree
- Handles novel situations not covered by the tree structure

### vs. Pure Reinforcement Learning
- Faster transfer learning thanks to structured cognitive architecture
- Interpretable decisions with explicit reasoning traces
- No catastrophic forgetting — Identity Memory preserves core objectives
- Behavioral constraints from architecture reduce unsafe exploration

---

## Included Files

| File | Description |
|---|---|
| `neuron657_v13.py` | Core cognitive architecture — all subsystems, classes, and the public API |
| `test4f.py` | Full NPC demo: FSM Tradicional vs NEURON657 cognitive agent in 2D combat simulation (requires `tkinter`) |

---

## Quick Start

### Requirements

```bash
pip install websockets
```

`tkinter` is required for the visual demo (`test4f.py`) and is included in most standard Python distributions.

### Run the Demo (FSM vs NEURON657)

```bash
python test4f.py
```

This launches a side-by-side 2D arena where a traditional hardcoded FSM NPC fights alongside a NEURON657 cognitive NPC against the same player. You can play manually or press `[A]` to activate full AI-vs-AI mode.

**Controls:**
| Key | Action |
|---|---|
| `Arrow keys` | Move player (Manual mode) |
| `A` | Toggle Manual / AI-vs-AI |
| `N` | Switch to NEURON657-driven player |
| `P` | Pause |
| `R` | Reset arena |
| `Q` | Quit & save memory |

### Use NEURON657 in Your Own Project

```python
from neuron657_v13 import (
    NeuronEngine,
    FactoredWorldModel, EpisodicMemory, GoalManager,
    IntentionSystem, AttentionSystem, UncertaintyEstimator,
    CuriosityModule, MetaCognitionModule, StrategySelector, TheoryOfMind
)

# Create extended modules (all optional)
fwm = FactoredWorldModel()
em  = EpisodicMemory()
gm  = GoalManager()
mc  = MetaCognitionModule()

# Initialize the engine
engine = NeuronEngine(
    exploration_rate=0.15,
    world_model_ext=fwm,
    episodic_memory=em,
    goal_manager=gm,
    metacognition_module=mc
)

# Add a long-term goal
engine.identity_memory.add_goal("minimize prediction error", priority=0.9)

# Process input and get a strategy decision
result = engine.process_input(
    input_data={"type": "perception", "data": "your_data_here"},
    context={
        "pattern_size": 500,
        "pattern_tags": ["sensor", "high_priority"],
        "memory_pressure": 0.3,
    }
)

print(result["strategy"])    # e.g. "hybrid"
print(result["confidence"])  # e.g. 0.78
print(result["explanation"]) # human-readable reasoning trace

# Graceful shutdown (saves MetaLearner state)
engine.shutdown()
```

### Checking System Health

```python
status = engine.get_system_status()
print(status["health"]["overall"])          # "healthy" / "warning" / "degraded"
print(status["energy_manager"])             # free energy, budget
print(status["learning"]["insights"])       # best/worst performing strategies
```

---

## Module Reference

### `Neuron657CoreV13` (aliased as `NeuronEngine`)

The main entry point. Accepts all subsystem modules via dependency injection.

| Parameter | Type | Description |
|---|---|---|
| `exploration_rate` | `float` | ε-greedy exploration probability (default `0.1`) |
| `world_model_ext` | `IWorldModel` | Optional factored world model |
| `episodic_memory` | `IEpisodicMemory` | Optional episodic memory store |
| `goal_manager` | `IGoalManager` | Optional goal tracking system |
| `intention_system` | `IIntentionSystem` | Optional intention system |
| `attention_system` | `IAttentionSystem` | Optional attention filter |
| `uncertainty_estimator` | `IUncertaintyEstimator` | Optional uncertainty estimation |
| `curiosity_module` | `ICuriosityModule` | Optional intrinsic reward module |
| `metacognition_module` | `IMetaCognitionModule` | Optional self-assessment module |
| `strategy_selector` | `IStrategySelector` | Optional high-level strategy selector |
| `theory_of_mind` | `ITheoryOfMind` | Optional multi-agent reasoning module |

### Key Classes

| Class | Description |
|---|---|
| `CognitiveState` | Immutable value object representing full system state at a moment |
| `MetricsManager` | Thread-safe metrics collection with history and trend analysis |
| `MetaLearner` | Strategy profile optimization with weighted learning history |
| `ExplainableDecision` | Produces human-readable reasoning summaries for every decision |
| `EnergyManager` | Cognitive energy budget with free energy computation |
| `IdentityMemory` | Long-term belief store with JSON persistence |
| `CognitivePlanner` | MCTS-based multi-step planner |
| `FactoredWorldModel` | Lightweight per-variable predictive model |
| `GoalManager` | Goal lifecycle with priority and deadline support |

---

## Memory Persistence

NEURON657 automatically persists learned state between runs:

- **`meta_learner_state_v13.json`** — strategy performance profiles and learning weights
- **`identity_memory.json`** — goals, beliefs, and free energy target
- **`npc_ltm.json`** — NPC episodic memory (demo-specific)

The MetaLearner state is loaded on startup and saved on `engine.shutdown()`. This means the system **improves across multiple runs** without any extra configuration.

---

## Licensing

NEURON657 is dual-licensed:

- **AGPLv3** — Free use (including commercial) with copyleft requirements. Modifications must be shared under the same license.
- **Commercial License** — For closed-source products where AGPLv3 requirements cannot be met (games, SaaS, proprietary systems).

**Patent Pending:** The adaptive cognitive architecture and bio-inspired decision-making mechanisms are subject to intellectual property protection.

---

## Author & Contact

**Walter Diego Spaltro**
- 📧 Email: [wds657@hotmail.com](mailto:wds657@hotmail.com)
- 💼 LinkedIn: [walter-diego-spaltro-2942b2178](https://www.linkedin.com/in/walter-diego-spaltro-2942b2178/)
- 💻 GitHub: [github.com/hydraroot/NEURON657](https://github.com/hydraroot/NEURON657)

For academic collaboration, commercial licensing inquiries, or technical questions — feel free to reach out.

---

## Research Directions

Current active research:
- Integration with large language models for natural language reasoning
- Neural world model learning from sensory data
- Hierarchical planning with temporal abstraction
- Collective intelligence via multi-agent episodic memory sharing
- Real-time adaptation to human feedback in interactive systems

---

*Copyright © 2026 Walter Diego Spaltro. All rights reserved.*


# NEURON657 — Arquitectura Cognitiva de Propósito General

<div align="center">

**Versión 13.2 · Toma de Decisiones Adaptativa Biológicamente Inspirada**

[![Licencia: AGPLv3](https://img.shields.io/badge/Licencia-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Estado: Activo](https://img.shields.io/badge/estado-activo-green.svg)]()

*Creado por [Walter Diego Spaltro](https://www.linkedin.com/in/walter-diego-spaltro-2942b2178/) · wds657@hotmail.com*

</div>

---

## ¿Qué es NEURON657?

NEURON657 es una **arquitectura cognitiva de propósito general** diseñada para la toma de decisiones adaptativa en entornos complejos e inciertos. A diferencia de los enfoques tradicionales de IA (máquinas de estados, árboles de comportamiento o aprendizaje por refuerzo puro), NEURON657 produce comportamiento que **emerge de la interacción continua** entre variables de estado interno, modelado predictivo del mundo y monitoreo meta-cognitivo — sin reglas hardcodeadas.

> **Innovación central:** Las decisiones surgen de dinámicas de estado biológicamente inspiradas, una implementación del Principio de Energía Libre para minimizar la sorpresa, y sistemas de memoria multi-nivel que aprenden y se adaptan entre sesiones.

---

## ¿Dónde se puede usar NEURON657?

NEURON657 es **agnóstico al dominio**. La misma arquitectura funciona en:

| Dominio | Descripción |
|---|---|
| 🎮 **IA en Videojuegos / NPCs** | Personajes que se adaptan al comportamiento del jugador sin scripting manual. Demostrado con combate táctico completo (miedo, agresión, curiosidad como impulsos). |
| 🤖 **Robótica** | Toma de decisiones para robots en entornos dinámicos e inciertos. El modelo del mundo maneja la incertidumbre de los sensores; el meta-aprendizaje adapta estrategias de control. |
| 🏭 **Automatización de Procesos** | Flujos de trabajo empresariales que aprenden estrategias óptimas a partir de la experiencia, bajo distintas cargas, urgencias y disponibilidad de recursos. |
| 🖥️ **Interfaces Adaptativas** | Sistemas de UI que modelan la intención y nivel de experiencia del usuario para ajustar patrones de interacción en tiempo real. |
| 🎯 **Simulación y Entrenamiento** | Comportamientos realistas de agentes para escenarios militares, médicos o de emergencia que requieren decisiones similares a las humanas bajo estrés. |
| 🤝 **Sistemas Multi-Agente** | Múltiples instancias de NEURON657 se coordinan mediante la Teoría de la Mente — sin controlador central. |

---

## Visión General de la Arquitectura

NEURON657 procesa información a través de **nueve subsistemas interconectados**:

```
Entrada → [Atención] → [Modelo del Mundo + Modelo Propio] → [Planificador]
                                       ↓
             [Gestor de Energía Libre] ← [Meta-Aprendizaje]
                                       ↓
        [Selector de Estrategia] → [Modo de Ejecución] → Salida
                    ↑
        [Memoria: STM / Episódica / Identidad]
```

### Subsistemas Principales

| Subsistema | Función |
|---|---|
| **Memoria de Trabajo (STM)** | Caché de patrones de alta velocidad con vectores HDC (Computación Hiperdimensional) |
| **Memoria Episódica** | Almacenamiento de experiencias indexadas por tiempo para razonamiento temporal y aprendizaje |
| **Memoria de Identidad** | Seguimiento de metas a largo plazo y persistencia de creencias entre sesiones |
| **Modelo del Mundo** | Modelo predictivo de la dinámica del entorno con incertidumbre bayesiana |
| **Modelo Propio** | Modelo introspectivo de las propias capacidades; permite monitoreo meta-cognitivo |
| **Teoría de la Mente** | Razonamiento sobre creencias, metas e intenciones de otros agentes |
| **Gestor de Energía Libre** | Implementa el Principio de Energía Libre — minimiza la sorpresa automáticamente |
| **Meta-Aprendizaje** | Aprende qué estrategias funcionan mejor en qué contextos a lo largo de los episodios |
| **Planificador Cognitivo** | Planificación multi-paso con MCTS; adapta la profundidad a la urgencia |

### Modos Cognitivos

| Modo | Cuándo se usa |
|---|---|
| `AUTONOMOUS` | Operación autodirigida persiguiendo metas internas |
| `REASONING` | Deliberación profunda para decisiones complejas |
| `META_LEARNING` | Optimización activa de perfiles de estrategia |
| `SAFE_RECOVERY` | Repliegue a heurísticas conservadoras ante alto riesgo de fallo |
| `ADAPTIVE` | Adaptación agresiva ante estado de alta agresión o victoria |

---

## Ventajas Técnicas

### vs. Máquinas de Estados Finitos (FSM)
- Sin transiciones hardcodeadas — el comportamiento emerge del espacio de estado continuo
- Transiciones suaves y graduadas en lugar de saltos discretos
- Sin explosión exponencial de estados ante contexto multidimensional

### vs. Árboles de Comportamiento
- Sin asignación manual de prioridades — emergen del estado interno
- Aprende la selección óptima de acciones sin rediseñar el árbol
- Maneja situaciones novedosas no cubiertas por la estructura del árbol

### vs. Aprendizaje por Refuerzo Puro
- Aprendizaje por transferencia más rápido gracias a la arquitectura cognitiva estructurada
- Decisiones interpretables con trazas de razonamiento explícitas
- Sin olvido catastrófico — la Memoria de Identidad preserva los objetivos centrales
- Las restricciones arquitecturales reducen la exploración insegura

---

## Archivos Incluidos

| Archivo | Descripción |
|---|---|
| `neuron657_v13.py` | Arquitectura cognitiva completa — todos los subsistemas, clases y API pública |
| `test4f.py` | Demo completa de NPC: FSM Tradicional vs agente cognitivo NEURON657 en simulación de combate 2D (requiere `tkinter`) |

---

## Inicio Rápido

### Requisitos

```bash
pip install websockets
```

`tkinter` es necesario para la demo visual (`test4f.py`) y viene incluido en la mayoría de las instalaciones estándar de Python.

### Ejecutar la Demo (FSM vs NEURON657)

```bash
python test4f.py
```

Esto lanza una arena 2D en paralelo donde un NPC FSM hardcodeado y un NPC cognitivo NEURON657 combaten contra el mismo jugador. Podés jugar manualmente o presionar `[A]` para activar el modo IA-vs-IA.

**Controles:**
| Tecla | Acción |
|---|---|
| `Flechas` | Mover jugador (modo Manual) |
| `A` | Alternar Manual / IA-vs-IA |
| `N` | Cambiar al jugador controlado por NEURON657 |
| `P` | Pausar |
| `R` | Reiniciar arena |
| `Q` | Salir y guardar memoria |

### Usar NEURON657 en tu Propio Proyecto

```python
from neuron657_v13 import (
    NeuronEngine,
    FactoredWorldModel, EpisodicMemory, GoalManager,
    IntentionSystem, AttentionSystem, UncertaintyEstimator,
    CuriosityModule, MetaCognitionModule, StrategySelector, TheoryOfMind
)

# Crear módulos extendidos (todos opcionales)
fwm = FactoredWorldModel()
em  = EpisodicMemory()
gm  = GoalManager()
mc  = MetaCognitionModule()

# Inicializar el motor
motor = NeuronEngine(
    exploration_rate=0.15,
    world_model_ext=fwm,
    episodic_memory=em,
    goal_manager=gm,
    metacognition_module=mc
)

# Agregar una meta a largo plazo
motor.identity_memory.add_goal("minimizar error de predicción", priority=0.9)

# Procesar entrada y obtener una decisión de estrategia
resultado = motor.process_input(
    input_data={"type": "percepcion", "data": "tus_datos_aqui"},
    context={
        "pattern_size": 500,
        "pattern_tags": ["sensor", "alta_prioridad"],
        "memory_pressure": 0.3,
    }
)

print(resultado["strategy"])    # ej: "hybrid"
print(resultado["confidence"])  # ej: 0.78
print(resultado["explanation"]) # traza de razonamiento legible

# Apagado ordenado (guarda estado del MetaLearner)
motor.shutdown()
```

### Verificar la Salud del Sistema

```python
estado = motor.get_system_status()
print(estado["health"]["overall"])          # "healthy" / "warning" / "degraded"
print(estado["energy_manager"])             # energía libre, presupuesto
print(estado["learning"]["insights"])       # mejores/peores estrategias aprendidas
```

---

## Referencia de Módulos

### `Neuron657CoreV13` (alias `NeuronEngine`)

El punto de entrada principal. Acepta todos los módulos del subsistema por inyección de dependencias.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `exploration_rate` | `float` | Probabilidad de exploración ε-greedy (por defecto `0.1`) |
| `world_model_ext` | `IWorldModel` | Modelo del mundo factorizado opcional |
| `episodic_memory` | `IEpisodicMemory` | Almacén de memoria episódica opcional |
| `goal_manager` | `IGoalManager` | Sistema de seguimiento de metas opcional |
| `intention_system` | `IIntentionSystem` | Sistema de intenciones opcional |
| `attention_system` | `IAttentionSystem` | Filtro de atención opcional |
| `uncertainty_estimator` | `IUncertaintyEstimator` | Módulo de estimación de incertidumbre opcional |
| `curiosity_module` | `ICuriosityModule` | Módulo de recompensa intrínseca opcional |
| `metacognition_module` | `IMetaCognitionModule` | Módulo de autoevaluación opcional |
| `strategy_selector` | `IStrategySelector` | Selector de estrategia de alto nivel opcional |
| `theory_of_mind` | `ITheoryOfMind` | Módulo de razonamiento multi-agente opcional |

### Clases Principales

| Clase | Descripción |
|---|---|
| `CognitiveState` | Objeto de valor inmutable que representa el estado completo del sistema en un momento |
| `MetricsManager` | Recolección de métricas thread-safe con historial y análisis de tendencias |
| `MetaLearner` | Optimización de perfiles de estrategia con historial de aprendizaje ponderado |
| `ExplainableDecision` | Produce resúmenes de razonamiento legibles para cada decisión |
| `EnergyManager` | Presupuesto de energía cognitiva con cómputo de energía libre |
| `IdentityMemory` | Almacén de creencias a largo plazo con persistencia JSON |
| `CognitivePlanner` | Planificador multi-paso basado en MCTS |
| `FactoredWorldModel` | Modelo predictivo liviano por variable |
| `GoalManager` | Ciclo de vida de metas con prioridad y plazo |

---

## Persistencia de Memoria

NEURON657 persiste automáticamente el estado aprendido entre ejecuciones:

- **`meta_learner_state_v13.json`** — perfiles de rendimiento de estrategias y pesos de aprendizaje
- **`identity_memory.json`** — metas, creencias y objetivo de energía libre
- **`npc_ltm.json`** — memoria episódica del NPC (específica de la demo)

El estado del MetaLearner se carga al inicio y se guarda al llamar `motor.shutdown()`. Esto significa que el sistema **mejora a través de múltiples ejecuciones** sin configuración adicional.

---

## Licenciamiento

NEURON657 tiene doble licencia:

- **AGPLv3** — Uso libre (incluyendo comercial) con requisitos de copyleft. Las modificaciones deben compartirse bajo la misma licencia.
- **Licencia Comercial** — Para productos de código cerrado donde no se pueden cumplir los requisitos de AGPLv3 (videojuegos, SaaS, sistemas propietarios).

**Patente en trámite:** La arquitectura cognitiva adaptativa y los mecanismos de toma de decisiones biológicamente inspirados están sujetos a protección de propiedad intelectual.

---

## Autor y Contacto

**Walter Diego Spaltro**
- 📧 Email: [wds657@hotmail.com](mailto:wds657@hotmail.com)
- 💼 LinkedIn: [walter-diego-spaltro-2942b2178](https://www.linkedin.com/in/walter-diego-spaltro-2942b2178/)
- 💻 GitHub: [github.com/hydraroot/NEURON657](https://github.com/hydraroot/NEURON657)

Para colaboración académica, consultas de licenciamiento comercial o preguntas técnicas — no dudes en contactarme.

---

## Líneas de Investigación Actuales

- Integración con modelos de lenguaje grande para razonamiento en lenguaje natural
- Aprendizaje de modelos del mundo neurales a partir de datos sensoriales
- Planificación jerárquica con abstracción temporal
- Inteligencia colectiva mediante memoria episódica compartida entre múltiples agentes
- Adaptación en tiempo real al feedback humano en sistemas interactivos

---

*Copyright © 2026 Walter Diego Spaltro. Todos los derechos reservados.*

