# Frontier-Engineering overlap review

Reviewed 2026-09-08. Sources: [paper v1 Appendix A](https://arxiv.org/html/2604.12290v1#A1), all 47 task descriptions; [official catalog](https://github.com/Einsia/Frontier-Engineering/blob/e3fa29c193356af2ce1ec8b3d23ab1a2e2410071/TASK_DETAILS.md), all 78 rows, with EngDesign expanded into seven subtasks (84 entries). The seven EngDesign prompts and the relevant nearby task contracts were read. The paper/catalog discrepancy is explicit: this review does not claim an unreconciled 95-task catalog was traversed.

The official FE main was e3fa29c193356af2ce1ec8b3d23ab1a2e2410071 at retrieval. SLE main was b9252e6bbaae2262cd3b624553efffaf6322d05a; its 82 task paths, keyword hits and related contracts were screened, not every line of all 82 task descriptions.

No task constructing minimum ternary radius-one covering codes was identified. FE HighReliableSimulation and LDPCErrorFloor estimate bit-error rates for fixed binary codes; weighted_parameter_coverage maximizes weighted molecular-feature coverage under a fixed selection budget. SLE NonlinearCodeRecords maximizes binary code size under minimum pairwise distance 10, a packing problem. These differ from finding a small code that covers every ternary word within Hamming distance one. This is not a claim that FE contains no coding-theory tasks.
