# Agent Monitor

[English](README.md)

Aplicación nativa y liviana para la barra de menú de macOS (SwiftUI + AppKit) que muestra en tiempo real el estado del agente y las cuotas restantes de **Google Antigravity**, **ChatGPT (Codex)** y **Claude Code**.

## Características

- **Indicador compacto en el Menu Bar**: Muestra únicamente los agentes que elijas, cada uno con su semáforo en vivo y su porcentaje mínimo restante (por ejemplo, `AG ● 80%  CX ● 100%  CC ● 74%`).
- **Semáforo en tiempo real**:
  - **Amarillo**: El agente está esperando una respuesta explícita tuya (pregunta, permiso o aprobación de plan).
  - **Rojo**: El agente está pensando, ejecutando herramientas o con tareas en segundo plano.
  - **Verde**: El agente está inactivo.
- **Cuotas y resets en vivo**: Ventanas de 5 horas y límites semanales/mensuales, barras de progreso por color, alerta por cuota baja (`< 20%`) y cuenta regresiva en tiempo real hasta el próximo reset.
- **Selector de agentes y gestión segura de hooks**: Elige qué agentes monitorear al iniciar o desde **Ajustes**. Al activar o desactivar un proveedor, se conectan o limpian únicamente los hooks del monitor sin pisar tu configuración previa (incluyendo `notify` en Codex o un `statusLine` previo en Claude Code).
- **Notificaciones nativas de macOS**: Avisos cuando un agente pasa a amarillo o cuando una cuota baja del `20%`. Al hacer clic en la notificación, abre o enfoca la app correspondiente.
- **7 idiomas integrados**: Detección automática del idioma de macOS + selector manual en **Ajustes** para **English**, **Español**, **Português**, **Français**, **Deutsch**, **简体中文** y **日本語**.

## Proveedores compatibles

| Proveedor | Etiqueta | Origen de cuotas | Origen de estado en vivo |
| :--- | :--- | :--- | :--- |
| **Antigravity** | `AG` | `agy` CLI `statusLine` (`gemini` y `3p` 5h/semanal) | `~/.gemini/config/hooks.json` |
| **ChatGPT (Codex)** | `CX` | `codex app-server` JSON-RPC (`account/rateLimits/read`) | `~/.codex/hooks.json` |
| **Claude Code** | `CC` | `statusLine` en `~/.claude/settings.json` (`rate_limits`) | Hooks en `~/.claude/settings.json` |

### Notas por proveedor

- **Codex**: Si Codex CLI solicita confirmar los hooks recién agregados en `~/.codex/hooks.json`, ejecuta `/hooks` una sola vez dentro de Codex para aprobarlos.
- **Claude Code**: Envía `rate_limits` (`five_hour` y `seven_day`) mediante su `statusLine` oficial durante sesiones activas. Si ya tenías un `statusLine` previo, se encadena automáticamente y se restaura al desactivar o desinstalar.

## Requisitos

- macOS 14.0 o superior
- Xcode Command Line Tools (`xcode-select --install`) para `swiftc` y `/usr/bin/python3`

## Instalación

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./install.sh
```

Esto compila `/Applications/AgentMonitor.app` (o `~/Applications/AgentMonitor.app` si no hay permisos en `/Applications`), instala los scripts en `~/.gemini/agent-monitor`, registra el `LaunchAgent` (`com.agentmonitor.app`) y abre el selector inicial en la barra de menú.

## Desinstalación

```bash
./uninstall.sh
```

Elimina la aplicación, el `LaunchAgent`, los scripts auxiliares y todos los hooks del monitor (restaurando cualquier `statusLine` previo de Claude Code).

## Privacidad

Agent Monitor no accede a credenciales privadas ni bases internas no documentadas: utiliza únicamente interfaces oficiales (`agy --settings`, `codex app-server` y los contratos oficiales de `hooks` / `statusLine`) guardando el estado localmente en `~/.gemini/agent-monitor/`.

## Licencia

MIT — ver [LICENSE](LICENSE).
