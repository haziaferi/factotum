| option | shared | tendril | all | growth | status | loses |
|---|---|---|---|---|---|---|
| whole-page (sim) | 0.20 | 1.00 | 0.50 | 0 | **front** | shared-different-blocks-both-live, shared-concurrent-inserts, shared-cell-and-body, shared-canvas-nodes |
| whole-page+ask (sim) | 0.20 | 0.67 | 0.38 | 2 | dominated | tendril-later-edit-beats-trash, shared-different-blocks-both-live, shared-concurrent-inserts, shared-cell-and-body, shared-canvas-nodes |
| per-row (sim) | 1.00 | 0.67 | 0.88 | 17 | dominated | tendril-later-edit-beats-trash |
| per-row+ask (sim) | 1.00 | 0.67 | 0.88 | 19 | dominated | tendril-later-edit-beats-trash |
| per-row+revive (sim) | 1.00 | 1.00 | 1.00 | 17 | **front** | - |
| per-row+revive-blocks (sim) | 0.80 | 1.00 | 0.88 | 15 | **front** | shared-cell-loser-recoverable |
| discard (sim) | 0.00 | 0.67 | 0.25 | 0 | control | tendril-loser-recoverable, shared-different-blocks-both-live, shared-concurrent-inserts, shared-cell-and-body, shared-canvas-nodes, shared-cell-loser-recoverable |

8 cases, 7 options, front: whole-page, per-row+revive, per-row+revive-blocks
