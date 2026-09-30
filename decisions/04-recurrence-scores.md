| option | chronicle | mnemo | tendril | all | growth | status | loses |
|---|---|---|---|---|---|---|---|
| rrule (sim) | 0.67 | 0.50 | 1.00 | 0.73 | 1 | **front** | chronicle-random-days, mnemo-cron-dom-or-dow, mnemo-stochastic-window |
| rrule+ext (sim) | 1.00 | 1.00 | 1.00 | 1.00 | 11 | **front** | - |
| cron+ext (sim) | 0.67 | 1.00 | 0.00 | 0.55 | 10 | **front** | tendril-elastic-3d, tendril-monthly-31st, tendril-second-tuesday, tendril-until, chronicle-every-90min |
| chronicle-enum (sim) | 1.00 | 0.00 | 0.25 | 0.36 | 9 | **front** | tendril-monthly-31st, tendril-second-tuesday, tendril-until, mnemo-cron-every-15, mnemo-cron-twice-daily, mnemo-cron-dom-or-dow, mnemo-stochastic-window |
| one-shot (sim) | 0.00 | 0.00 | 0.00 | 0.00 | 0 | control | tendril-elastic-3d, tendril-monthly-31st, tendril-second-tuesday, tendril-until, chronicle-every-90min, chronicle-weekdays, chronicle-random-days, mnemo-cron-every-15, mnemo-cron-twice-daily, mnemo-cron-dom-or-dow, mnemo-stochastic-window |

11 cases, 5 options, front: rrule, rrule+ext, cron+ext, chronicle-enum
