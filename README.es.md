# Agent Monitor

[![Latest Release](https://img.shields.io/github/v/release/JoacoCasta/agent-monitor)](https://github.com/JoacoCasta/agent-monitor/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/JoacoCasta/agent-monitor/ci.yml?branch=main&label=CI)](https://github.com/JoacoCasta/agent-monitor/actions/workflows/ci.yml)
[![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue)](https://github.com/JoacoCasta/agent-monitor/releases/latest)
[![License: MIT](https://img.shields.io/github/license/JoacoCasta/agent-monitor)](LICENSE)

[English](README.md) · [Changelog](CHANGELOG.md) · [Contribuir](CONTRIBUTING.md)

Monitor nativo y liviano para **macOS**, **Windows** y **Linux** que muestra en tiempo real el estado del agente y las cuotas restantes de **Google Antigravity**, **ChatGPT (Codex)** y **Claude Code**.

## Capturas de pantalla

![Indicador en barra de menú de macOS con los logos oficiales de Antigravity, OpenAI y Claude](docs/screenshots/menubar.png)

| Panel principal | Ajustes |
| :---: | :---: |
| ![Panel principal de Agent Monitor](docs/screenshots/dashboard.png) | ![Panel de ajustes de Agent Monitor](docs/screenshots/settings.png) |

## Descarga directa (Sin Terminal)

Descarga el instalador listo para usar según tu sistema desde [GitHub Releases](https://github.com/JoacoCasta/agent-monitor/releases/latest):

- **macOS (`AgentMonitor-macOS.dmg`)**: Abre el `.dmg`, arrastra **Agent Monitor** a **Aplicaciones** y ábrelo.
  - *Primer arranque en macOS*: Como esta app open-source aún no está notarizada por Apple, si macOS muestra aviso de desarrollador no verificado, haz **Clic derecho (o Control + clic) sobre `AgentMonitor.app` → Abrir** una sola vez.
- **Windows (`AgentMonitor-Windows-Setup.exe`)**: Doble clic para instalar (no requiere permisos de administrador) e iniciar directo en la bandeja del sistema. También está disponible el portable `AgentMonitor-Windows-Portable.zip`.
- **Linux (`AgentMonitor-Linux-x64.deb` / `AgentMonitor-Linux-x64.tar.gz`)**: Instala el `.deb` desde el Centro de Software / `sudo apt install ./AgentMonitor-Linux-x64.deb`, o descomprime el `.tar.gz` y ejecuta `./agent-monitor`.

Todas las versiones son **autocontenidas**: al abrirse por primera vez instalan automáticamente sus scripts auxiliares, muestran el selector inicial de agentes, incluyen el interruptor **Iniciar al encender** en **Ajustes** y configuran los hooks sin necesidad de usar la terminal.

## Características

- **Logos oficiales e indicador compacto en barra de menú / bandeja del sistema**:
  - **macOS (SwiftUI + AppKit)**: Renderiza el logo vectorial monocromático oficial de cada agente activo junto a su semáforo en vivo y su porcentaje mínimo restante, adaptándose con nitidez a barras claras y oscuras.
  - **Windows y Linux (Python + PySide6 / Qt6)**: Icono dinámico multi-punto en la bandeja del sistema con el semáforo de cada agente activo, alerta visual por cuota baja (`< 20%`), tooltip resumido y panel emergente interactivo con los logos vectoriales oficiales.
- **Semáforo en tiempo real**:
  - **Amarillo**: El agente está esperando una respuesta explícita tuya (pregunta, permiso o aprobación de plan).
  - **Rojo**: El agente está pensando, ejecutando herramientas o con tareas en segundo plano.
  - **Verde**: El agente está inactivo.
- **Cuotas y resets en vivo**: Ventanas de 5 horas y límites semanales/mensuales, barras de progreso por color, alerta por cuota baja (`< 20%`) y cuenta regresiva en tiempo real hasta el próximo reset.
- **Selector de agentes y gestión segura de hooks**: Elige qué agentes monitorear al iniciar o desde **Ajustes**. Al activar o desactivar un proveedor, se conectan o limpian únicamente los hooks del monitor sin pisar tu configuración previa (incluyendo `notify` en Codex o un `statusLine` previo en Claude Code).
- **Notificaciones nativas**: Avisos de escritorio cuando un agente pasa a amarillo o cuando una cuota baja del `20%`. Al hacer clic en la notificación, abre o enfoca la app correspondiente.
- **7 idiomas integrados**: Detección automática del idioma del sistema + selector manual en **Ajustes** para **English**, **Español**, **Português**, **Français**, **Deutsch**, **简体中文** y **日本語**.
- **Salida `--status-json` para scripts**: Expone la etiqueta `tag` (`AG`, `CX`, `CC`), estado en vivo, porcentaje, sesiones activas y ventanas de cuota de cada proveedor activo para Waybar, Polybar o scripts propios.

## Proveedores compatibles

| Proveedor | Logo y etiqueta `--status-json` | Origen de cuotas | Origen de estado en vivo |
| :--- | :--- | :--- | :--- |
| **Google Antigravity** | Logo oficial de Antigravity (`AG`) | `agy` CLI `statusLine` (`gemini` y `3p` 5h/semanal) | `~/.gemini/config/hooks.json` |
| **ChatGPT (Codex)** | Logo oficial de OpenAI (`CX`) | `codex app-server` JSON-RPC (`account/rateLimits/read`) | `~/.codex/hooks.json` |
| **Claude Code** | Logo oficial de Claude (`CC`) | `statusLine` en `~/.claude/settings.json` (`rate_limits`) | Hooks en `~/.claude/settings.json` |

## Compilar / Instalar desde el código fuente (Opcional)

### macOS (14.0+, Xcode Command Line Tools)

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./install.sh
```

**Desinstalar:** `./uninstall.sh`

### Windows (10/11, Python 3.9+)

```powershell
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
powershell -ExecutionPolicy Bypass -File .\windows\install.ps1
```

**Desinstalar:** `powershell -ExecutionPolicy Bypass -File .\windows\uninstall.ps1`

### Linux (X11 / Wayland, Python 3.9+)

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./linux/install.sh
```

- **Waybar / Polybar / scripts**: Ejecuta `agent-monitor --status-json` para obtener un JSON en vivo con la etiqueta `tag` (`AG`, `CX`, `CC`), estado, porcentaje y ventanas de cuota de cada proveedor activo.

**Desinstalar:** `./linux/uninstall.sh`

## Preguntas frecuentes y solución de problemas

- **macOS indica que no se puede abrir `"AgentMonitor.app"` porque proviene de un desarrollador no identificado**:
  Abre **Finder → Aplicaciones**, haz **Clic derecho (o Control + clic) sobre `AgentMonitor.app` → Abrir** y confirma **Abrir**. Solo es necesario la primera vez.
- **Codex CLI pide revisar o aprobar hooks nuevos en `~/.codex/hooks.json`**:
  Ejecuta `/hooks` una sola vez dentro de Codex CLI para aprobar los hooks de Agent Monitor. Tu configuración previa de `notify` se conserva intacta.
- **Claude Code ya tenía un `statusLine` personalizado**:
  Agent Monitor encadena automáticamente tu comando `statusLine` previo para que ambos sigan funcionando y lo restaura al desactivar Claude Code o desinstalar. Las cuotas (`five_hour` y `seven_day`) se actualizan durante sesiones activas de Claude Code.
- **En Linux GNOME no aparece el icono en la bandeja del sistema**:
  Habilita la extensión de GNOME Shell **AppIndicator and KStatusNotifierItem Support** para mostrar iconos Qt/StatusNotifier en la barra superior.

## Privacidad

Agent Monitor no accede a credenciales privadas ni bases internas no documentadas: utiliza únicamente interfaces oficiales (`agy --settings`, `codex app-server` y los contratos oficiales de `hooks` / `statusLine`) guardando el estado localmente en `~/.gemini/agent-monitor/`.

## Licencia

MIT — ver [LICENSE](LICENSE).
