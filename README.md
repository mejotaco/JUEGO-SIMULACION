# STAR FORCE 8-BIT

Juego arcade de disparos espaciales en 2D hecho con **Pygame CE**.

## Requisitos

- Python 3.10+
- `pygame-ce` (Community Edition)

```bash
pip install pygame-ce
```

## Cómo jugar

```bash
python main.py
```

### Modos

| Opción          | Descripción                         |
|-----------------|-------------------------------------|
| 1 JUGADOR       | Un solo jugador                     |
| 2 JUGADORES     | Split screen, cada uno en su mitad  |

### Controles

| Acción        | P1 (WASD)   | P2 (Flechas)  | Mando Xbox   |
|---------------|-------------|---------------|--------------|
| Movimiento    | W A S D     | ↑ ← ↓ →       | Stick/DPad   |
| Disparar      | BLOQ MAYÚS  | SHIFT         | A            |
| Pausa         | ESC         | ESC           | Start        |

*Los esquemas de control se pueden cambiar en **AJUSTES** del menú principal.*

## Oleadas

| Oleada | Kills   | Descripción                              |
|--------|---------|------------------------------------------|
| 1      | 0-14    | Enemigos básicos                         |
| 2      | 15-29   | Aparecen helicópteros                    |
| 3      | 30-49   | Enemigos más duros                       |
| 4      | 50-79   | Mayor densidad y velocidad               |
| 5      | 80-119  | **BOSS** – música especial + modo rabia  |
| 6+     | 120+    | Oleadas infinitas (cada 40 kills sube 1) |

Al pasar la oleada 5 aparece **GANASTE** y el juego continúa infinitamente.

### Powerups

Los enemigos pueden soltar powerups al morir:

| Powerup     | Efecto                          | Duración |
|-------------|---------------------------------|----------|
| RÁPIDO      | Disparo más rápido              | 6s       |
| SPREAD      | Triple disparo                   | 6s       |
| CALOR+      | +10 disparos antes de recargar  | 12s      |
| ESCUDO      | Absorbe un golpe                 | 1 hit    |

## Puntuaciones

Se guardan localmente las 5 mejores puntuaciones en `assets/leaderboard.json`.

## Assets

Los sprites y música van en `assets/`. Si faltan archivos, el juego usa fallbacks dibujados con píxeles.
