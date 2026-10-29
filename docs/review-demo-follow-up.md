# Review automation pilot task

Current task: maintain the exporter JSON contract, especially speeds in metres per second.
For the committed SysML input, scenario.vTarget_mps must remain 27.78, not 100.008.

Separate future requirement, outside this task: add a batch SysML export command.
The batch command must accept two input SysML files and write two separate JSON outputs without overwriting either.
Acceptance: each output preserves its input vehicle mass and scenario speed, and the command returns nonzero if either input is invalid.
Create a separate candidate Issue for this requirement only if it is confirmed; do not defer a newly introduced unit error.
