# Product Requirements Document (PRD)
**Proyecto:** Cyber Range & Bank Log Simulator (Purple Team Environment)
**Versión:** 1.0.0
**Estado:** Propuesta Inicial

## 1. Resumen Ejecutivo
Desarrollo de un entorno de simulación de ciberseguridad (Cyber Range) capaz de generar tráfico sintético de alta fidelidad basado en una topología bancaria. El sistema orquesta tanto el "ruido blanco" operativo de miles de estaciones de trabajo como la actividad maliciosa dirigida por agentes de inteligencia artificial (Red Team), todo convergiendo en un pipeline de datos de grado empresarial (Double-Hop Kappa Architecture) para entrenamiento avanzado de Data Engineers, evaluación de analistas (Blue Team) y pruebas de estrés de infraestructura.

## 2. Objetivos y Alcance
* **Fase 1 (Baseline):** Generar tráfico operativo realista para 2.000 estaciones de trabajo (Windows, macOS, Linux) distribuidas en distintas sucursales y áreas corporativas.
* **Fase 2 (Red Team):** Introducir un motor de inyección de ataques basado en LLMs, con capacidad para orquestar hasta 50 agentes autónomos con intenciones específicas (ej. exfiltración, escalada de privilegios) utilizando el framework MITRE ATT&CK.
* **Fase 3 (Purple Teaming):** Habilitar un bucle de retroalimentación donde las acciones defensivas (Blue Team) registradas en el pipeline afecten el estado y las decisiones en tiempo real de los agentes atacantes.

## 3. Arquitectura del Sistema
El sistema se construirá priorizando la mantenibilidad, escalabilidad y la separación de responsabilidades mediante **Arquitectura Hexagonal** y principios **SOLID** y **DDD (Domain-Driven Design)**.

### 3.1. Ecosistema de Datos e Infraestructura (Double-Hop Kappa Architecture en Docker Compose)
* **Capa de Ingesta (Swamp):** Apache Kafka (`bankrange-raw`) actuando como buffer inicial para la recepción de cadenas de texto crudas, caóticas y multi-formato sin procesar.
* **Capa ETL (Vector VRL):** Vector asume el rol de motor ETL pesado central. Implementa lógica condicional VRL, extracciones Regex y splittings posicionales para normalizar el lodo de datos proveniente de los distintos sistemas operativos.
* **Capa de Refinamiento (Lakehouse/SIEM):** 
  - Apache Kafka (`bankrange-clean`): Tópico secundario que almacena el JSON estandarizado para su posterior consumo por herramientas de IA y analítica.
  - Grafana Loki: Indexador optimizado para metadatos de logs a gran volumen, alimentado directamente por el ETL normalizado.
* **Visualización:** Grafana (Dashboards enfocados a Data Engineering y SOC, visualizando Totales de Volumen y Seguridad en Reposo).

### 3.2. Motor de Simulación (Core Domain)
* **Lenguaje:** Python.
* **Modelado del Dominio:** Entidades fuertemente tipadas (`Branch`, `Workstation`, `Employee`, `NetworkSegment`).
* **Generador Temporal:** Motor probabilístico basado en series temporales para simular jornadas laborales, picos de actividad y descansos.

### 3.3. Orquestación de Agentes (IA Local)
* **Framework:** LangGraph para la gestión de estados y toma de decisiones multi-agente.
* **Inferencia:** Integración con ecosistemas de IA locales para inferencia rápida acelerada por hardware (ej. GPUs con alta VRAM), asegurando privacidad y cero latencia de red externa en la generación de payloads maliciosos.

### 3.4. Interfaz de Control (Command & Control - C&C)
* **Backend:** FastAPI para exponer los controles del motor de simulación.
* **Frontend:** Streamlit para gestionar intensidades de tráfico, perfiles de atacantes y métricas de simulación en tiempo real.

## 4. Métricas de Carga y Rendimiento (Estimadas)
Basado en la configuración inicial objetivo:
* **Estaciones Normales:** 2,000 PCs a ~2 EPS = 4,000 EPS.
* **Agentes Atacantes:** 50 Agentes a ~10 EPS = 500 EPS.
* **Carga Total del Pipeline:** ~4,500 EPS sostenidos.
* **Volumen de Datos Generado:** ~7.5 GB por hora (~180 GB/día).
* **Requisitos de Hardware Objetivo:** Entorno local de alto rendimiento (mínimo 64GB RAM recomendados para mantener brokers, base de datos de series temporales y motor de inferencia operativa simultáneamente).

## 5. Criterios de Aceptación (Fase 1)
1. **Caos Deliberado:** El motor del simulador (Core Domain) debe emitir de forma intencionada cadenas de texto caóticas y multi-formato ( flattened XML para Windows, RFC 3164 para Linux, TSV posicional para macOS) sin ningún wrapper JSON.
2. **Double-Hop ETL:** La infraestructura debe soportar una arquitectura Kappa obligando a que los datos fluyan crudos hacia un tópico Kafka (`bankrange-raw`), sean parseados severamente por un motor Vector ETL, y finalicen en un formato maestro estandarizado en un segundo tópico y en Loki.
3. El volumen de EPS debe ser ajustable dinámicamente mediante la interfaz C&C sin necesidad de reiniciar los contenedores.
4. Grafana debe contar con Dashboards pre-configurados que prioricen métricas absolutas de volumetría ("Totales", Data-at-Rest) en lugar de exclusivas tasas instantáneas.

## 6. Riesgos y Consideraciones
* **Saturación de Disco:** 180 GB/día requiere políticas de rotación estrictas (Data Retention Policies) en Loki para entornos locales.
* **Cuellos de Botella en Inferencia:** La toma de decisiones sincrónica de 50 agentes LLM simultáneos puede saturar la GPU. Se requerirá un diseño asíncrono o procesamiento por lotes en LangGraph.