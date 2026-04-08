# Backend-Laufzeit

Die Backend-Laufzeit wird durch `OrchestratorService` zusammengesetzt. Er besitzt Repository, Speicher, Ressourcenmanager, Planner, Handler-Registry und Execution-Engine.

Wichtige Regel: Laufzeitveraenderungen betreffen fast immer gleichzeitig Domaene, Engine und API-Snapshot.
