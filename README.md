---
title: DesignRL
emoji: 🏗️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# DesignRL

DesignRL is an experimental reinforcement learning environment for arranging steel frame elements on a 20 × 20 metre grid. An agent places columns and beams, can add simplified wall elements, and receives displacement and member utilization feedback from a three dimensional frame model. Three tasks cover a warehouse, an office, and a hospital scenario.

**Status:** Research prototype. Its simplified loads, member checks, wall model, and scoring are not validated for real building design or a claim of Eurocode compliance. See [Model limitations](#model-limitations).

## Quick start

Use Python 3.10 or newer. From the repository root:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m uvicorn server.app:app --host 127.0.0.1 --port 7860
```

Open `http://127.0.0.1:7860/` for the interactive demo or `/docs` for the API. The container entry point is `server.app:app` on port 7860:

```bash
docker build -t designrl .
docker run --rm -p 7860:7860 designrl
```

The API and demo require no LLM credentials. For the optional baseline agent, copy `.env.example` to `.env`, set `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` for a compatible chat completions endpoint, then run `python inference.py task1_warehouse` against the local server. `SERVER_URL` overrides the default `http://localhost:7860`. With no task argument the script attempts all three tasks and incurs model calls. The agent requires a reachable external or local model endpoint; it has not been validated against every compatible provider.

## Tasks

| ID | Floors | Site | Step limit | Inputs |
| --- | ---: | --- | ---: | --- |
| `task1_warehouse` | 1 | 20 × 10 m | 25 | Dead and live load |
| `task2_office` | 3 | 20 × 20 m | 55 | Dead, live, wind, light seismic load |
| `task3_hospital` | 3 | 20 × 20 m | 85 | Dead, live, wind, higher seismic load |

The tasks use separate heuristic graders, each returning a number from 0 to 1. The grade combines validity with task specific mass, drift, wall layout, utilization, or column removal metrics. A grade is a simulation reward, not a safety certification.

## API example

`POST /reset` creates a session. Send one action per `POST /step` with the returned `session_id`. `/step` accepts either an action object or a JSON string in `message`.

```bash
curl -X POST http://localhost:7860/reset \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"task1_warehouse"}'

curl -X POST http://localhost:7860/step \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"SESSION_ID_FROM_RESET","action":{"action_type":"place_column","grid_x":0,"grid_y":0,"floor":0,"section":"HEB200"}}'
```

Replace `SESSION_ID_FROM_RESET` with the returned ID. Then place another column and a beam:

```json
{"action_type":"place_column","grid_x":5,"grid_y":0,"floor":0,"section":"HEB200"}
{"action_type":"place_beam","from_node_x":0,"from_node_y":0,"to_node_x":5,"to_node_y":0,"floor":0,"section":"IPE300","orientation":"x"}
{"action_type":"done"}
```

These are separate actions, sent in separate requests. Other action types are `upgrade_section`, `downgrade_section`, `remove_element`, and `add_wall`. Section changes and removals take an `element_id` from `observation.placed_elements`. `add_wall` uses the beam endpoint fields, `floor`, and optional `thickness_m` (`0.2` or `0.3`). The endpoints must already have columns on that floor. `GET /action_schema` lists examples and available HEB and IPE sections.

The step response includes `observation`, `reward`, `done`, `score` (when finished), and `info`. The observation contains the grid, placed elements, member checks, maximum utilization, drift ratio, mass, and a text summary. `GET /state?session_id=...` returns episode metadata; `POST /grade` scores a session for its matching task. `GET /query_forces`, `POST /what_if_remove`, and `GET /render` expose additional inspection data. `/health`, `/metadata`, `/schema`, and `/mcp` provide integration endpoints. Sessions live in process memory, so a server restart loses them and multiple workers do not share them.

## Model limitations

- The frame solver uses linear elastic Euler–Bernoulli elements and fixed base nodes. It does not model connection behavior, geometric nonlinearity, diaphragms, foundations, or construction details.
- The load generator estimates tributary areas from column coordinates and applies simplified nodal gravity, wind, and seismic actions. It does not implement complete design combinations, load paths, or floor slab behavior.
- The wall is represented as a stiff horizontal beam at a floor level, not as a shell or a physical vertical wall panel. Its checks and mass are approximations.
- Member checks implement selected simplified Eurocode inspired formulas. They do not cover all relevant failure modes or national annex choices. Deflection is based on nodal displacement rather than peak span deflection.
- `is_structurally_valid` reflects solver convergence, checked utilization, and the modeled drift limit. It does not establish full site coverage, continuous multistory framing, or suitability for construction.
- Graders and reference masses are task heuristics. The carbon estimate is a fixed multiplier on the reported element mass.

## Repository guide

| Path | Purpose |
| --- | --- |
| `structural_design_env/env.py`, `models.py`, `validation.py` | Episode state, API data models, action checks |
| `structural_design_env/graph.py`, `grid.py` | Element graph and plan display |
| `structural_design_env/solver/` | Frame solver, sections, loads, member checks, seismic and redundancy helpers |
| `structural_design_env/tasks/` | Task configurations and graders |
| `server/app.py`, `server/interactive_demo.html` | API and browser demo |
| `inference.py` | Optional LLM baseline |
| `tests/` | Solver, member, grader, environment, and route checks |
| `openenv.yaml`, `Dockerfile`, `pyproject.toml`, `uv.lock` | Integration, container, and dependencies |

`scripts/run_server.sh` is an alternate launcher. `.env.example` contains placeholders only; do not commit a populated `.env`.

## License

Licensed under the MIT License. See [LICENSE](LICENSE).
