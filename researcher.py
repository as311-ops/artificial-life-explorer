import argparse
import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import anthropic


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class ResearchConfig:
    model: str = "claude-sonnet-4-6"
    experiment_timeout_seconds: int = 600
    max_experiments: int = 50
    max_total_cost_usd: float = 10.0
    default_grid_width: int = 80
    default_grid_height: int = 45
    default_num_epochs: int = 3000
    default_mutation_rate: float = 0.00024
    main_py_path: str = "main.py"
    journal_path: str = "research_journal.md"
    state_path: str = "research_state.json"
    backup_dir: str = ".researcher_backups"
    metrics_dir: str = ".researcher_metrics"


# ── State ─────────────────────────────────────────────────────────────────────

@dataclass
class ResearchState:
    experiment_count: int = 0
    total_cost_usd: float = 0.0
    current_main_py_hash: str = ""
    applied_patches: list[dict] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def sha256_file(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def backup_main_py(config: ResearchConfig, exp_id: int) -> str:
    backup_dir = Path(config.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / f"main_py_before_{exp_id:04d}.py"
    shutil.copy2(config.main_py_path, dest)
    return str(dest)


def apply_patches(path: str, patches: list[dict]) -> tuple[bool, str]:
    content = Path(path).read_text().replace("\r\n", "\n")
    for patch in patches:
        old = patch["old_string"].replace("\r\n", "\n")
        new = patch["new_string"].replace("\r\n", "\n")
        count = content.count(old)
        if count != 1:
            return False, f"old_string '{old[:60]}...' kommt {count}x vor (erwartet: 1)"
        content = content.replace(old, new, 1)
    Path(path).write_text(content)
    return True, ""


def revert_main_py(backup_path: str, main_py_path: str) -> None:
    shutil.copy2(backup_path, main_py_path)


def git_commit(message: str) -> None:
    subprocess.run(
        ["git", "add", "main.py", "research_journal.md", "research_state.json"],
        check=True,
    )
    subprocess.run(["git", "commit", "-m", message], check=True)


def run_simulator(config: ResearchConfig, params: dict, exp_id: int) -> dict:
    metrics_path = f"{config.metrics_dir}/exp_{exp_id:04d}.json"
    Path(config.metrics_dir).mkdir(parents=True, exist_ok=True)

    grid_width = params.get("grid_width", config.default_grid_width)
    grid_height = params.get("grid_height", config.default_grid_height)
    num_programs = grid_width * grid_height

    cmd = [
        "uv", "run", "main.py",
        "--no-gif",
        "--seed", str(params["seed"]),
        "--num-epochs", str(params["num_epochs"]),
        "--mutation-rate", str(params.get("mutation_rate", config.default_mutation_rate)),
        "--grid-width", str(grid_width),
        "--grid-height", str(grid_height),
        "--num-programs", str(num_programs),
        "--metrics-path", metrics_path,
        "--metrics-every", "10",
    ]
    if "replicator_threshold" in params:
        cmd += ["--replicator-threshold", str(params["replicator_threshold"])]

    timed_out = False
    returncode = -1
    try:
        proc = subprocess.run(
            cmd,
            timeout=config.experiment_timeout_seconds,
            capture_output=True,
            text=True,
        )
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True

    metrics = None
    metrics_file = Path(metrics_path)
    if metrics_file.exists():
        try:
            metrics = json.loads(metrics_file.read_text())
        except Exception:
            pass

    return {
        "returncode": returncode,
        "timed_out": timed_out,
        "metrics": metrics,
        "metrics_path": metrics_path,
    }


def load_journal(config: ResearchConfig) -> str:
    path = Path(config.journal_path)
    if not path.exists():
        return ""
    content = path.read_text()
    if len(content) > 50_000:
        return content[:5_000] + "\n\n[... gekürzt ...]\n\n" + content[-45_000:]
    return content


def append_to_journal(config: ResearchConfig, content: str) -> None:
    with open(config.journal_path, "a", encoding="utf-8") as f:
        f.write(content + "\n")


def init_journal(config: ResearchConfig, main_py_hash: str) -> None:
    experiments_baseline = ""
    experiments_path = Path("EXPERIMENTE.md")
    if experiments_path.exists():
        experiments_baseline = experiments_path.read_text()

    header = f"""# BFF-Universum Forschungsjournal

Gestartet: {datetime.now(timezone.utc).isoformat()}
main.py SHA256: {main_py_hash}

## Bekannte Erkenntnisse (aus EXPERIMENTE.md)

{experiments_baseline}

---
"""
    Path(config.journal_path).write_text(header)


def load_state(config: ResearchConfig) -> ResearchState:
    path = Path(config.state_path)
    if not path.exists():
        return ResearchState()
    try:
        data = json.loads(path.read_text())
        return ResearchState(
            experiment_count=data.get("experiment_count", 0),
            total_cost_usd=data.get("total_cost_usd", 0.0),
            current_main_py_hash=data.get("current_main_py_hash", ""),
            applied_patches=data.get("applied_patches", []),
        )
    except Exception:
        return ResearchState()


def save_state(state: ResearchState, config: ResearchConfig) -> None:
    data = {
        "experiment_count": state.experiment_count,
        "total_cost_usd": state.total_cost_usd,
        "current_main_py_hash": state.current_main_py_hash,
        "applied_patches": state.applied_patches,
    }
    Path(config.state_path).write_text(json.dumps(data, indent=2))


# ── LLM Tools ─────────────────────────────────────────────────────────────────

TOOL_EXPERIMENT_DECISION = {
    "name": "experiment_decision",
    "description": "Entscheide das nächste Experiment oder beende die Forschungsrunde.",
    "input_schema": {
        "type": "object",
        "required": ["action", "hypothesis", "simulator_params"],
        "properties": {
            "action": {"type": "string", "enum": ["run_experiment", "stop"]},
            "hypothesis": {"type": "string"},
            "force_reflection": {"type": "boolean", "default": False},
            "simulator_params": {
                "type": "object",
                "required": ["seed", "num_epochs"],
                "properties": {
                    "seed":                 {"type": "integer"},
                    "num_epochs":           {"type": "integer", "minimum": 100},
                    "mutation_rate":        {"type": "number", "minimum": 0.0, "maximum": 0.1},
                    "grid_width":           {"type": "integer", "minimum": 10},
                    "grid_height":          {"type": "integer", "minimum": 10},
                    "replicator_threshold": {"type": "number"},
                },
            },
            "code_patches": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["old_string", "new_string", "description"],
                    "properties": {
                        "old_string":  {"type": "string"},
                        "new_string":  {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
        },
    },
}

TOOL_EXPERIMENT_ANALYSIS = {
    "name": "experiment_analysis",
    "description": "Analysiere das abgeschlossene Experiment.",
    "input_schema": {
        "type": "object",
        "required": ["reflection", "surprise_score", "next_hypothesis"],
        "properties": {
            "reflection":         {"type": "string"},
            "surprise_score":     {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "next_hypothesis":    {"type": "string"},
            "parameter_insights": {"type": "array", "items": {"type": "string"}},
        },
    },
}

TOOL_PATCH_DECISION = {
    "name": "patch_decision",
    "description": "Entscheide ob ein Code-Patch dauerhaft behalten werden soll.",
    "input_schema": {
        "type": "object",
        "required": ["keep", "reason"],
        "properties": {
            "keep":   {"type": "boolean"},
            "reason": {"type": "string"},
        },
    },
}

SYSTEM_EXPERIMENT_DECISION = """Du bist ein autonomer Forschungsagent für BFF-Universum-Selbstreplikation.

Simulator-Konzepte:
- Opcode-%: Anteil semantischer Bytes (>, <, {, }, +, -, ., ,, [, ]) — steigt wenn Replikatoren entstehen
- Shannon-Entropie: Byte-Diversität (max 8.0 bits = uniform random; sinkt bei Monokultur)
- Replikator-Epoch: erste Epoch wo Opcode-% >= Schwellwert

Forschungsprinzipien:
1. Falsifizierbare Hypothesen formulieren
2. Wenn möglich nur einen Parameter variieren
3. Kleine Grids (80×45) für schnelle Exploration bevorzugen
4. Code-Patches nur wenn Parameter-Exploration das nicht abdecken kann
5. Bei Code-Patches: old_string exakt aus aktuellem main.py kopieren"""

SYSTEM_EXPERIMENT_ANALYSIS = """Du analysierst ein Experiment zu BFF-Universum-Selbstreplikation.
Fokus: Was widerspricht der Hypothese? Welche Kausalzusammenhänge sind sichtbar?
Welche Schwellwert-Effekte gibt es? Was ist die präziseste nächste Hypothese?"""


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return input_tokens * 3.0 / 1_000_000 + output_tokens * 15.0 / 1_000_000


def call_llm_experiment_decision(
    client: anthropic.Anthropic,
    config: ResearchConfig,
    journal: str,
    state: ResearchState,
    main_py: str,
) -> tuple[dict, float]:
    state_summary = {
        "experiment_count": state.experiment_count,
        "total_cost_usd": round(state.total_cost_usd, 4),
        "applied_patches": state.applied_patches,
    }
    user_content = f"""## Forschungsjournal (aktuell)

{journal}

## State
```json
{json.dumps(state_summary, indent=2)}
```

## main.py (aktuell)

```python
{main_py}
```"""
    response = client.messages.create(
        model=config.model,
        max_tokens=4096,
        system=SYSTEM_EXPERIMENT_DECISION,
        tools=[TOOL_EXPERIMENT_DECISION],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": user_content}],
    )
    cost = estimate_cost_usd(response.usage.input_tokens, response.usage.output_tokens)
    for block in response.content:
        if block.type == "tool_use" and block.name == "experiment_decision":
            return block.input, cost
    raise RuntimeError("LLM lieferte kein experiment_decision Tool-Result")


def call_llm_experiment_analysis(
    client: anthropic.Anthropic,
    config: ResearchConfig,
    journal: str,
    decision: dict,
    metrics: dict | None,
) -> tuple[dict, float]:
    user_content = f"""## Hypothese
{decision.get("hypothesis", "")}

## Parameter
```json
{json.dumps(decision.get("simulator_params", {}), indent=2)}
```

## Metriken
```json
{json.dumps(metrics, indent=2) if metrics else "keine Metriken verfügbar"}
```

## Bisheriges Journal (Auszug)
{journal[-10_000:]}"""
    response = client.messages.create(
        model=config.model,
        max_tokens=2048,
        system=SYSTEM_EXPERIMENT_ANALYSIS,
        tools=[TOOL_EXPERIMENT_ANALYSIS],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": user_content}],
    )
    cost = estimate_cost_usd(response.usage.input_tokens, response.usage.output_tokens)
    for block in response.content:
        if block.type == "tool_use" and block.name == "experiment_analysis":
            return block.input, cost
    raise RuntimeError("LLM lieferte kein experiment_analysis Tool-Result")


def call_llm_patch_decision(
    client: anthropic.Anthropic,
    config: ResearchConfig,
    metrics: dict | None,
    patches: list[dict],
) -> tuple[dict, float]:
    user_content = f"""## Angewandte Patches
{json.dumps(patches, indent=2)}

## Experiment-Metriken
```json
{json.dumps(metrics, indent=2) if metrics else "keine Metriken verfügbar"}
```

Sollen diese Code-Patches dauerhaft in main.py behalten werden?"""
    response = client.messages.create(
        model=config.model,
        max_tokens=512,
        system="Du entscheidest ob ein Code-Patch für den BFF-Simulator dauerhaft behalten werden soll.",
        tools=[TOOL_PATCH_DECISION],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": user_content}],
    )
    cost = estimate_cost_usd(response.usage.input_tokens, response.usage.output_tokens)
    for block in response.content:
        if block.type == "tool_use" and block.name == "patch_decision":
            return block.input, cost
    raise RuntimeError("LLM lieferte kein patch_decision Tool-Result")


# ── Heuristic Surprise ────────────────────────────────────────────────────────

def heuristic_surprise(metrics: dict | None, state: ResearchState) -> float:
    if metrics is None:
        return 0.8
    replicator_epoch = metrics.get("replicator_epoch")
    final_opcode = metrics.get("final_opcode_percent")
    final_entropy = metrics.get("final_shannon_entropy")

    score = 0.0
    if replicator_epoch is None:
        score = max(score, 0.6)
    elif replicator_epoch < 50:
        score = max(score, 0.7)
    elif replicator_epoch > 2000:
        score = max(score, 0.6)
    if final_entropy is not None and final_entropy < 3.0:
        score = max(score, 0.7)
    if final_opcode is not None and final_opcode > 80.0:
        score = max(score, 0.6)
    return score


# ── Journal Entry ─────────────────────────────────────────────────────────────

def format_journal_entry(
    exp_id: int,
    decision: dict,
    result: dict,
    analysis: dict | None,
    patch_applied: bool,
    patch_kept: bool,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    metrics = result.get("metrics") or {}
    params = decision.get("simulator_params", {})

    replicator_epoch = metrics.get("replicator_epoch", "nicht erreicht")
    final_opcode = metrics.get("final_opcode_percent", "N/A")
    final_entropy = metrics.get("final_shannon_entropy", "N/A")
    elapsed = metrics.get("total_elapsed_seconds", "N/A")
    timed_out = "Ja" if result.get("timed_out") else "Nein"

    patch_section = "KEINER"
    if decision.get("code_patches"):
        descs = [p.get("description", "?") for p in decision["code_patches"]]
        status = "BEHALTEN" if patch_kept else "REVERTIERT"
        patch_section = f"Patch: {'; '.join(descs)} — {status}"

    findings = "— kein Reflexionsschritt —"
    next_hyp = ""
    if analysis:
        findings = analysis.get("reflection", findings)
        next_hyp = f"\n**Nächste Hypothese:** {analysis.get('next_hypothesis', '')}"

    return f"""## Experiment {exp_id} | {now}

**Hypothese:** {decision.get("hypothesis", "")}

### Parameter
```json
{json.dumps(params, indent=2)}
```

### Code-Patch
{patch_section}

### Metriken
| Metrik | Wert |
|--------|------|
| Replikator-Epoch | {replicator_epoch} |
| Finaler Opcode-% | {final_opcode}% |
| Finale Shannon-Entropie | {final_entropy} bits |
| Laufzeit | {elapsed}s |
| Timeout | {timed_out} |

### Findings
{findings}{next_hyp}

---"""


# ── Main Loop ─────────────────────────────────────────────────────────────────

def research_loop(
    config: ResearchConfig,
    no_patches: bool = False,
    no_git: bool = False,
) -> None:
    client = anthropic.Anthropic()
    state = load_state(config)

    if state.experiment_count == 0:
        main_py_hash = sha256_file(config.main_py_path)
        init_journal(config, main_py_hash)
        state.current_main_py_hash = main_py_hash
        save_state(state, config)
        print("Journal initialisiert.")

    print(
        f"Starte Forschungsrunde | Experimente bisher: {state.experiment_count} "
        f"| Kosten: ${state.total_cost_usd:.4f}"
    )

    while (
        state.experiment_count < config.max_experiments
        and state.total_cost_usd < config.max_total_cost_usd
    ):
        journal = load_journal(config)
        main_py = Path(config.main_py_path).read_text()

        print(f"\n[Exp {state.experiment_count + 1}] Frage LLM nach nächstem Experiment...")
        try:
            decision, cost = call_llm_experiment_decision(
                client, config, journal, state, main_py
            )
        except Exception as e:
            print(f"LLM-Fehler (experiment_decision): {e}")
            break
        state.total_cost_usd += cost

        if decision.get("action") == "stop":
            append_to_journal(
                config,
                f"\n## Forschungsrunde beendet | {datetime.now(timezone.utc).isoformat()}\n\n"
                "Das LLM hat entschieden, die Forschungsrunde zu beenden.\n\n---\n",
            )
            save_state(state, config)
            print("LLM hat Forschungsrunde beendet.")
            break

        exp_id = state.experiment_count + 1
        patch_applied = False
        patch_kept = False
        backup_path = None

        # Patch anwenden
        patches = decision.get("code_patches") or []
        if patches and not no_patches:
            backup_path = backup_main_py(config, exp_id)
            success, err = apply_patches(config.main_py_path, patches)
            if not success:
                append_to_journal(
                    config,
                    f"\n> **Patch-Fehler (Exp {exp_id}):** {err} — Experiment läuft ohne Patch weiter.\n",
                )
                patches = []
            else:
                patch_applied = True
                print(f"  Patch angewandt: {[p.get('description') for p in patches]}")

        # Simulator starten
        sim_params = decision["simulator_params"]
        print(
            f"  Starte Simulator: seed={sim_params['seed']}, "
            f"epochs={sim_params['num_epochs']}"
        )
        if state.experiment_count == 0:
            print("  (Hinweis: Numba JIT-Warmup beim ersten Experiment — dauert länger)")

        result = run_simulator(config, sim_params, exp_id)

        # Patch revertieren wenn Simulator fehlschlug (kein Timeout)
        if patch_applied and result["returncode"] != 0 and not result["timed_out"]:
            print("  Simulator fehlgeschlagen — revertiere Patch")
            revert_main_py(backup_path, config.main_py_path)
            patch_applied = False

        # Surprise berechnen
        force_reflection = decision.get("force_reflection", False)
        surprise = heuristic_surprise(result["metrics"], state)
        print(
            f"  Surprise: {surprise:.2f} | Timeout: {result['timed_out']} "
            f"| Returncode: {result['returncode']}"
        )

        # Reflexion
        analysis = None
        if surprise >= 0.5 or force_reflection:
            print("  Starte Reflexions-Analyse...")
            try:
                analysis, analysis_cost = call_llm_experiment_analysis(
                    client, config, journal, decision, result["metrics"]
                )
                state.total_cost_usd += analysis_cost
            except Exception as e:
                print(f"  LLM-Fehler (experiment_analysis): {e}")

        # Patch-Entscheidung
        if patch_applied and result["returncode"] == 0:
            print("  Frage LLM: Patch behalten?")
            try:
                patch_decision_result, pd_cost = call_llm_patch_decision(
                    client, config, result["metrics"], patches
                )
                state.total_cost_usd += pd_cost
                if patch_decision_result.get("keep"):
                    patch_kept = True
                    print(f"  Patch behalten: {patch_decision_result.get('reason', '')}")
                else:
                    print(f"  Patch revertiert: {patch_decision_result.get('reason', '')}")
                    revert_main_py(backup_path, config.main_py_path)
                    patch_applied = False
            except Exception as e:
                print(f"  LLM-Fehler (patch_decision): {e}")
                revert_main_py(backup_path, config.main_py_path)
                patch_applied = False

        # Journal-Eintrag
        entry = format_journal_entry(
            exp_id, decision, result, analysis, patch_applied, patch_kept
        )
        append_to_journal(config, entry)

        # State aktualisieren
        state.experiment_count = exp_id
        state.current_main_py_hash = sha256_file(config.main_py_path)
        if patch_kept:
            state.applied_patches.append({
                "exp_id": exp_id,
                "description": "; ".join(p.get("description", "?") for p in patches),
                "kept": True,
            })
        save_state(state, config)

        # Git commit bei behaltenen Patches
        if patch_kept and not no_git:
            try:
                git_commit(f"exp {exp_id}: {decision.get('hypothesis', '')[:60]}")
            except Exception as e:
                print(f"  Git-Fehler: {e}")

        metrics = result.get("metrics") or {}
        print(
            f"  Abgeschlossen | Replikator-Epoch: {metrics.get('replicator_epoch', 'N/A')} "
            f"| Opcode: {metrics.get('final_opcode_percent', 'N/A')}% "
            f"| Kosten gesamt: ${state.total_cost_usd:.4f}"
        )

    print(
        f"\nForschungsrunde abgeschlossen. "
        f"{state.experiment_count} Experimente, ${state.total_cost_usd:.4f} Kosten."
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BFF-Universum Forschungsagent")
    parser.add_argument("--max-experiments", type=int, default=50)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--max-cost", type=float, default=10.0)
    parser.add_argument("--no-patches", action="store_true", default=False)
    parser.add_argument("--no-git", action="store_true", default=False)
    args = parser.parse_args()

    config = ResearchConfig(
        max_experiments=args.max_experiments,
        experiment_timeout_seconds=args.timeout_seconds,
        max_total_cost_usd=args.max_cost,
    )

    research_loop(config, no_patches=args.no_patches, no_git=args.no_git)
