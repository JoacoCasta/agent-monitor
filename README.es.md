# Agent Monitor

[English](README.md)

Monitor nativo y liviano para **macOS**, **Windows** y **Linux** que muestra en tiempo real el estado del agente y las cuotas restantes de **Google Antigravity**, **ChatGPT (Codex)** y **Claude Code**.

## Características

- **Indicador compacto en barra de menú / bandeja del sistema**:
  - **macOS (SwiftUI + AppKit)**: Muestra cada agente seleccionado con su semáforo en vivo y su porcentaje mínimo restante (por ejemplo, `AG ● 80%  CX ● 100%  CC ● 74%`).
  - **Windows y Linux (Python + PySide6 / Qt6)**: Icono dinámico multi-punto en la bandeja del sistema con el semáforo de cada agente activo, alerta visual por cuota baja (`< 20%`), tooltip resumido y panel emergente interactivo.
- **Semáforo en tiempo real**:
  - **Amarillo**: El agente está esperando una respuesta explícita tuya (pregunta, permiso o aprobación de plan).
  - **Rojo**: El agente está pensando, ejecutando herramientas o con tareas en segundo plano.
  - **Verde**: El agente está inactivo.
- **Cuotas y resets en vivo**: Ventanas de 5 horas y límites semanales/mensuales, barras de progreso por color, alerta por cuota baja (`< 20%`) y cuenta regresiva en tiempo real hasta el próximo reset.
- **Selector de agentes y gestión segura de hooks**: Elige qué agentes monitorear al iniciar o desde **Ajustes**. Al activar o desactivar un proveedor, se conectan o limpian únicamente los hooks del monitor sin pisar tu configuración previa (incluyendo `notify` en Codex o un `statusLine` previo en Claude Code).
- **Notificaciones nativas**: Avisos de escritorio cuando un agente pasa a amarillo o cuando una cuota baja del `20%`. Al hacer clic en la notificación, abre o enfoca la app correspondiente.
- **7 idiomas integrados**: Detección automática del idioma del sistema + selector manual en **Ajustes** para **English**, **Español**, **Português**, **Français**, **Deutsch**, **简体中文** y **日本語**.

## Proveedores compatibles

| Proveedor | Etiqueta | Origen de cuotas | Origen de estado en vivo |
| :--- | :--- | :--- | :--- |
| **Antigravity** | `AG` | `agy` CLI `statusLine` (`gemini` y `3p` 5h/semanal) | `~/.gemini/config/hooks.json` |
| **ChatGPT (Codex)** | `CX` | `codex app-server` JSON-RPC (`account/rateLimits/read`) | `~/.codex/hooks.json` |
| **Claude Code** | `CC` | `statusLine` en `~/.claude/settings.json` (`rate_limits`) | Hooks en `~/.claude/settings.json` |

### Notas por proveedor

- **Codex**: Si Codex CLI solicita confirmar los hooks recién agregados en `~/.codex/hooks.json`, ejecuta `/hooks` una sola vez dentro de Codex para aprobarlos.
- **Claude Code**: Envía `rate_limits` (`five_hour` y `seven_day`) mediante su `statusLine` oficial durante sesiones activas. Si ya tenías un `statusLine` previo, se encadena automáticamente y se restaura al desactivar o desinstalar.

## Instalación

También se generan paquetes descargables para **macOS**, **Windows** y **Linux** en la pestaña **Releases** mediante GitHub Actions al etiquetar una versión (`v*`).

### macOS (14.0+, Xcode Command Line Tools)

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./install.sh
```

Compila `/Applications/AgentMonitor.app`, instala los scripts en `~/.gemini/agent-monitor` y registra el `LaunchAgent` (`com.agentmonitor.app`).

**Desinstalar:** `./uninstall.sh`

### Windows (10/11, Python 3.9+)

```powershell
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
powershell -ExecutionPolicy Bypass -File .\windows\install.ps1
```

Crea un entorno virtual aislado con `PySide6` en `%USERPROFILE%\.gemini\agent-monitor\venv`, conecta los hooks, crea accesos directos en Inicio automático y Menú Inicio con `pythonw.exe` (sin ventana de consola) e inicia en la bandeja del sistema.

**Desinstalar:** `powershell -ExecutionPolicy Bypass -File .\windows\uninstall.ps1`

### Linux (X11 / Wayland, Python 3.9+)

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./linux/install.sh
```

Instala en `~/.gemini/agent-monitor/venv` con `PySide6`, agrega `~/.local/bin/agent-monitor`, registra autostart en `~/.config/autostart/agent-monitor.desktop` y arranca en segundo plano.

- **Usuarios de GNOME**: Habilita la extensión *AppIndicator and KStatusNotifierItem Support* para ver iconos en la barra superior.
- **Waybar / Polybar / scripts**: Ejecuta `agent-monitor --status-json` para obtener un JSON en vivo con estado, porcentaje y cuotas de cada proveedor activo.

**Desinstalar:** `./linux/uninstall.sh`

## Privacidad

Agent Monitor no accede a credenciales privadas ni bases internas no documentadas: utiliza únicamente interfaces oficiales (`agy --settings`, `codex app-server` y los contratos oficiales de `hooks` / `statusLine`) guardando el estado localmente en `~/.gemini/agent-monitor/`.

## Licencia

MIT — ver [LICENSE](LICENSE).
