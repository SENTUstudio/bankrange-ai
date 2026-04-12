# 🛡️ BankRange: AI-Powered Cyber Log Simulator

Un entorno de simulación de ciberseguridad (Purple Team Environment) de alto rendimiento, diseñado para generar tráfico sintético de alta fidelidad basado en una topología bancaria. El sistema orquesta el "ruido blanco" operativo de miles de estaciones de trabajo e integra agentes de inteligencia artificial (Red Team) para ejecutar ataques simulados y evaluar respuestas defensivas (Blue Team).

## 🏗️ Arquitectura y Stack Tecnológico

El proyecto está construido bajo los principios de **Diseño Guiado por el Dominio (DDD)** y **Arquitectura Hexagonal**, asegurando un bajo acoplamiento y alta mantenibilidad.

* **Core / Dominio:** Python 3.11+, Pydantic.
* **Gestor de Paquetes:** `uv` (Extremadamente rápido, escrito en Rust).
* **Pipeline de Datos:** Apache Kafka (KRaft mode), Promtail/Vector, Grafana Loki.
* **IA & Agentes:** LangGraph, Ollama (Inferencia local por GPU).
* **Control (C&C):** FastAPI, Streamlit.
* **Testing:** `pytest` (TDD estricto).

---

## 🗺️ Roadmap de Desarrollo

El desarrollo está estructurado en tres etapas incrementales:

### Etapa 1: MVP - Tráfico Base y Core Domain (El Ruido)
Construcción del simulador operativo base. El objetivo es modelar la topología del banco y generar logs corporativos realistas a gran escala.
* Modelado de Entidades de Dominio (`Branch`, `Workstation`, `Employee`).
* Implementación de curvas de comportamiento probabilístico (horarios laborales, picos de inicio de sesión).
* Generación de ~4000 Eventos Por Segundo (EPS) simulando 2000 PCs con distintos sistemas operativos (Windows, Linux, macOS).
* Despliegue del pipeline de datos (Docker Compose con Kafka y Loki) para la ingesta en tiempo real.

### Etapa 2: Red Team - Ecosistema de Agentes Atacantes (La Amenaza)
Inyección de anomalías estructuradas y ataques persistentes mediante agentes de Inteligencia Artificial locales.
* Integración de LangGraph para la toma de decisiones multi-agente.
* Creación de perfiles de atacantes (Script Kiddie, Insider Threat, APT) con intenciones financieras claras.
* Ejecución de TTPs basados en **MITRE ATT&CK** (Movimiento lateral, exfiltración, fuerza bruta).
* Control de intensidad y simulación de ataques orquestados desde un panel C&C (Streamlit).

### Etapa 3: Purple Teaming - Blue Team Feedback Loop (La Defensa)
Habilitación de un entorno competitivo bidireccional.
* Configuración de reglas de detección (SIEM) sobre la data ingerida en Loki.
* Implementación de un tópico de respuesta en Kafka para eventos de mitigación (ej. `ip-blocked`, `account-suspended`).
* Adaptación dinámica de los agentes atacantes: el LLM lee los bloqueos y recalcula su estrategia de ataque en tiempo real para intentar evadir al Blue Team.

---

## 📂 Estructura del Proyecto (Arquitectura Hexagonal)

```text
cyber-range-simulator/
├── core/                       # Lógica de Negocio (Dominio puro, sin dependencias externas)
│   ├── domain/                 # Entidades, Value Objects, Excepciones
│   ├── use_cases/              # Puertos de Entrada (Casos de uso del simulador)
│   └── ports/                  # Puertos de Salida (Interfaces para repositorios/eventos)
├── adapters/                   # Implementaciones de Infraestructura
│   ├── inbound/                # APIs, CLI, Panel Streamlit
│   └── outbound/               # Kafka Producers, LLM Clients (Ollama), File Writers
├── tests/                      # Testing (pytest)
│   ├── unit/                   # Tests del Core y Dominio
│   └── integration/            # Tests de Adaptadores y Kafka
├── docker/                     # Archivos de despliegue
│   ├── docker-compose.yml      # Stack de Kafka, Loki, Grafana
│   └── configs/                # Archivos de configuración de infraestructura
├── pyproject.toml              # Configuración de dependencias gestionada por uv
└── README.md
```

---

## 🚀 Guía de Inicio Rápido

Este proyecto utiliza `uv` para una gestión de dependencias ultrarrápida y reproducible.

### 1. Pre-requisitos
* [Docker](https://docs.docker.com/get-docker/) y Docker Compose v2.
* [uv](https://github.com/astral-sh/uv) instalado en tu sistema.

### 2. Configuración del Entorno Python

Clona el repositorio e inicializa el entorno virtual y las dependencias con `uv`:

```bash
# Sincronizar las dependencias del proyecto (creará el entorno virtual .venv automáticamente)
uv sync

# Activar el entorno virtual
source .venv/bin/activate  # En Linux/macOS
.venv\Scripts\activate     # En Windows
```

*Nota: Para agregar nuevas dependencias al proyecto, utiliza `uv add <paquete>`. Para dependencias de desarrollo, `uv add --dev <paquete>`.*

### 3. Levantar la Infraestructura (Kafka + Loki)

Inicia el stack de datos base para permitir la ingesta de eventos:

```bash
cd docker
docker compose up -d
```
* Kafka estará disponible en `localhost:9092`
* Grafana estará disponible en `localhost:3000`

### 4. Ejecutar Pruebas (TDD)

Asegúrate de que la lógica de dominio cumple con los requisitos antes de ejecutar el motor:

```bash
uv run pytest tests/unit/
```

### 5. Iniciar el Motor de Simulación (C&C)

Levanta la interfaz de control principal:

```bash
uv run streamlit run adapters/inbound/ui/app.py
```


