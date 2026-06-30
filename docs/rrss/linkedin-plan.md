# Plan LinkedIn — BankRange Cyber Range

## Estrategia general

Serie de 6 posts publicados con 3-4 días de separación.
Arco narrativo: problema → construcción → revelación → profundidad técnica → impacto → llamada a la comunidad.

Hashtags base (usar en todos los posts):
`#DataEngineering` `#Cybersecurity` `#Python` `#Kafka` `#OpenSource`

---

## Post 1 — El Gancho (Problema + Suspenso)

**Objetivo:** generar curiosidad. No revelar el proyecto todavía.

**Texto:**
> ¿Cómo entrenas a un analista de seguridad si no podés exponerlo a un ataque real?
>
> No podés usar producción. No podés inventar datos a mano. Y los datasets públicos no tienen la fidelidad que necesitás.
>
> Estuve meses pensando en este problema.
>
> La semana que viene muestro lo que construí.
>
> 👇 Seguime para no perderte el lanzamiento.

**Hashtags adicionales:** `#PurpleTeam` `#BlueTeam` `#SIEM` `#CyberRange`
**SEO keywords:** data engineering, cybersecurity training, synthetic data, SIEM

---

## Post 2 — La Revelación (Lanzamiento del proyecto)

**Objetivo:** presentar BankRange con impacto visual y técnico.

**Texto:**
> Construí un banco falso. Con 1.000 empleados, turnos de trabajo, sucursales en toda Argentina, y logs generados en tiempo real desde cada PC.
>
> Se llama **BankRange** — un Cyber Range de código abierto para entrenar Data Engineers y analistas de seguridad.
>
> El stack completo corriendo en local:
> → Apache Kafka (Double-Hop Kappa Architecture)
> → Vector ETL procesando XML, Syslog RFC 3164 y TSV en paralelo
> → Grafana + Loki + Prometheus para observabilidad
> → FastAPI + SvelteKit como panel C&C
> → Python con Arquitectura Hexagonal y DDD
>
> 4.000 eventos por segundo. 3 sistemas operativos. Caos deliberado.
>
> Y esto es solo la Fase 1.
>
> 🔗 [link al repo]

**Hashtags adicionales:** `#ApacheKafka` `#Grafana` `#FastAPI` `#DDD` `#HexagonalArchitecture`
**SEO keywords:** kafka data pipeline, vector etl, grafana loki, python hexagonal architecture

---

## Post 3 — La Profundidad Técnica (El ETL)

**Objetivo:** demostrar expertise técnico. Atraer a data engineers.

**Texto:**
> El problema más interesante que resolví en BankRange: normalizar 3 formatos de log completamente distintos en un esquema maestro único.
>
> Windows genera XML plano:
> `<Event><Computer>SUC001-PC-042</Computer>...`
>
> Linux genera Syslog RFC 3164:
> `<134>May 20 09:15:22 SUC001-LX-006 sshd[1234]: m.gonzalez - INFO - ...`
>
> macOS genera TSV posicional:
> `2026-05-20T09:15:22\tSUC001-MC-007\tc.torres\tmacos\t...`
>
> Tres formatos. Un pipeline. Vector VRL hace la transformación en tiempo real antes de que lleguen a Kafka clean y Loki.
>
> El truco: cada OS tiene su propio consumer group. Caos deliberado en la ingesta, orden en la salida.
>
> Así se entrena a un Data Engineer de verdad.

**Hashtags adicionales:** `#ETL` `#VectorDev` `#DataPipeline` `#LogManagement`
**SEO keywords:** vector vrl, kafka etl, log normalization, data pipeline architecture

---

## Post 4 — El Detalle Humano (Empleados con turnos)

**Objetivo:** mostrar el nivel de fidelidad del simulador. Generar admiración.

**Texto:**
> Un detalle que nadie espera en un simulador de logs: los empleados tienen turno de trabajo.
>
> De 8 a 18hs → los logs de `SUC001-PC-042` muestran `username: m.gonzalez`
> De 0 a 7hs → los mismos logs muestran `username: SYSTEM`
>
> ¿Por qué importa esto?
>
> Porque si un analista ve `m.gonzalez` autenticándose a las 3am, eso es una anomalía real.
> Si ve `SYSTEM` a las 3am, es un batch job normal.
>
> La diferencia entre un dataset de entrenamiento mediocre y uno que realmente enseña a detectar amenazas está en estos detalles.
>
> BankRange tiene 1.000 workstations, cada una con su empleado asignado, su turno, su departamento y su historial coherente.

**Hashtags adicionales:** `#ThreatDetection` `#SOC` `#SecurityAnalytics` `#MITRE`
**SEO keywords:** threat detection training, soc analyst training, anomaly detection, synthetic logs

---

## Post 5 — La Arquitectura (Para los que quieren profundidad)

**Objetivo:** posicionarse como referente técnico. Atraer a arquitectos y seniors.

**Texto:**
> La arquitectura de BankRange en una imagen:
>
> ```
> Simulador Python (DDD + Hexagonal)
>         ↓
>   Kafka bankrange-raw-{os}     ← caos deliberado, 3 formatos
>         ↓
>   Vector ETL (VRL)             ← normalización por OS
>         ↓
>   Kafka bankrange-clean-{os}   ← JSON estandarizado
>   Loki                         ← logs indexados
>   Prometheus                   ← métricas de latency (~70ms)
>         ↓
>   Grafana                      ← SOC dashboard
> ```
>
> Decisiones de diseño que tomé y por qué:
>
> ✅ **Double-Hop Kappa** en lugar de Lambda: un solo pipeline para batch y streaming, sin duplicar lógica.
> ✅ **Métricas en Prometheus, logs en Loki**: cada herramienta hace lo que sabe hacer. No le pidas a Loki que calcule percentiles.
> ✅ **Rate limiting en nginx, no en el API**: la capa de red es el lugar correcto para eso.
> ✅ **uv** para gestión de dependencias: 10x más rápido que pip, lockfile reproducible.
>
> Cada decisión tiene un motivo. Eso es lo que diferencia un proyecto de producción de un tutorial.

**Hashtags adicionales:** `#SystemDesign` `#SoftwareArchitecture` `#KappaArchitecture` `#Prometheus`
**SEO keywords:** kappa architecture, system design, kafka architecture, prometheus grafana

---

## Post 6 — El Futuro (Fase 2 + llamada a la comunidad)

**Objetivo:** generar anticipación por Fase 2. Invitar colaboración.

**Texto:**
> BankRange Fase 1 está completa. Pero lo que viene es lo que realmente me quita el sueño.
>
> **Fase 2: 50 agentes de IA atacando el banco.**
>
> Cada agente tiene un perfil: Script Kiddie, Insider Threat, APT.
> Cada agente ejecuta TTPs del framework MITRE ATT&CK.
> Cada agente aprende de las defensas del Blue Team y adapta su estrategia.
>
> Todo corriendo local. Sin APIs externas. Sin datos que salgan de tu máquina.
>
> LangGraph + modelos locales (Ollama) + el pipeline de datos que ya construimos.
>
> Si sos Data Engineer, analista de seguridad, o simplemente te gusta construir cosas que importan — este proyecto es para vos.
>
> 🔗 Repo: [link]
> ⭐ Si te parece valioso, una estrella ayuda mucho.
> 💬 ¿Qué TTP de MITRE ATT&CK querés ver primero?

**Hashtags adicionales:** `#LangGraph` `#AIAgents` `#MITREAttack` `#RedTeam` `#LLM`
**SEO keywords:** mitre attack framework, langchain agents, red team automation, ai cybersecurity

---

## Calendario sugerido

| Post | Día | Mejor horario |
|------|-----|---------------|
| 1 — El Gancho | Lunes | 9am |
| 2 — La Revelación | Jueves | 9am |
| 3 — ETL Técnico | Lunes +1 | 9am |
| 4 — Empleados con turnos | Jueves +1 | 9am |
| 5 — Arquitectura | Lunes +2 | 9am |
| 6 — Fase 2 | Jueves +2 | 9am |

## Notas de formato

- Máximo 3 emojis por post. Menos es más en LinkedIn técnico.
- Párrafos cortos (1-2 líneas). LinkedIn penaliza los bloques de texto.
- Siempre terminar con una pregunta o CTA para fomentar comentarios.
- El link al repo va en el primer comentario, no en el post (LinkedIn reduce alcance a posts con links externos).
- Imagen o video del dashboard de Grafana en posts 2 y 5 — el visual técnico genera 3x más engagement.
