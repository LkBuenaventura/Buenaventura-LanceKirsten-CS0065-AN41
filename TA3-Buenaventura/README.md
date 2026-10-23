# Technical Assessment 3: Disaster Response Using Case-Based Reasoning

**Course:** CS0065 - Intelligent Systems, AN41  
**Submission:** Erlano and Buenaventura (as identified in the accompanying PDFs)

This Python console application demonstrates case-based reasoning (CBR) by retrieving a past disaster scenario and adapting its response to a new earthquake, typhoon, or flood scenario. It displays the selected case, similarity score, proposed evacuation strategy, shelter capacity, and categorized resources. Users review the shelter capacity and can retain the resulting case for future runs.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Interactive application, retrieval, adaptation, review, and persistence. |
| `disaster_memory.json` | Current local case base, including retained classroom scenarios. |
| `disaster_memory.json.legacy.bak` | Preserved backup of the earlier case-base format. |
| `test_main.py` | Regression tests using isolated temporary databases. |
| [Code PDF](TA3_Erlano_Buenaventura%20%28CODE%20File%29.pdf) | Accompanying code submission. |
| [Documentation PDF](TA3_Erlano_Buenaventura%20%28DOCUMENTATION%20File%29.pdf) | Accompanying project documentation. |

## Requirements and execution

Install Python 3. The local reasoning workflow uses only the Python standard library. From the repository root:

```sh
cd TA3-Buenaventura
python -X utf8 main.py
```

On Windows, `py` can replace `python` if that is how Python is installed. UTF-8 mode supports the application's symbols and emoji.

Earthquake scenarios also attempt an optional USGS event lookup. To enable it, install `requests` and use an internet connection:

```sh
python -m pip install requests
```

If the package or connection is unavailable, the application falls back to local cases. The response plans attached to online earthquake records are classroom templates; they are not response reports supplied by USGS.

## Using the application

1. Enter `Earthquake`, `Typhoon`, or `Flood`.
2. Enter a location, a nearby hazard such as `River` or `Mountain`, and a numeric intensity. Typhoon and flood levels must be between 1 and 5 in this demonstration.
3. Review the retrieved case, its score, and the adapted plan.
4. Press Enter to accept the proposed shelter capacity, or enter a positive whole number to revise it.
5. Enter `y` to save the reviewed case, or `n` to skip saving; then choose whether to analyze another scenario.

Saved cases are written to `disaster_memory.json` beside the script. Loading older records can migrate their format and create a `.legacy.bak` backup if one does not already exist. Keep a copy of the JSON file if you want to preserve a particular case-base snapshot before an interactive run.

## How the reasoning works

### Retrieve

Only cases with the same disaster type are considered. Each eligible case receives:

- 5 points for the matching disaster type.
- 3 points if the entered location occurs in the stored location, ignoring case.
- 2 points if the entered nonempty, non-`None` hazard occurs in the stored hazard, ignoring case.
- `max(0, 5 - abs(past_intensity - new_intensity))` points for intensity similarity.

The highest score wins; the first case wins ties. The maximum score is 15, and the score is a heuristic match measure.

### Reuse and adapt

The selected solution is copied before adaptation. If the new intensity exceeds the stored intensity by **more than 1.0**, shelter capacity increases by 50%, rounded up. Hazard-specific protocols, resources, and disaster-specific tips are added.

For example, the starter flood case has intensity 3 and capacity 5,000. A flood at intensity 5 produces a recommended capacity of 7,500 before review. An existing retained case may change which case is selected during an actual run.

### Revise and retain

The user accepts or revises shelter capacity. If saving is requested, the application appends the new problem and reviewed solution to the case base, using a temporary file followed by replacement for the JSON write.

## Verification

From this folder, run:

```sh
python -X utf8 -m unittest -v
```

The 13 regression tests cover retrieval, capacity calculation and rounding, legacy migration, input validation, review, retention, and offline lookup behavior. They use temporary databases and do not call the live USGS service.

## Project scope

This is an educational demonstration. Its intensity guides, resource estimates, and response rules are hard-coded classroom assumptions; the program does not validate real disaster outcomes or provide an operational emergency-planning system.
