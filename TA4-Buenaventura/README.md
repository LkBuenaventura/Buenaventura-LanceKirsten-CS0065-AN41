# Technical Assessment 4: Personal Study-Room Assistant

**Student:** Lance Kirsten Y. Buenaventura  
**Course:** CS0065 - Intelligent Systems, AN41

This Python console application demonstrates knowledge representation (KR), rule-based reasoning (RBR), and case-based reasoning (CBR) through a study-room assistant. Given room conditions and study preferences, it prints recommendations from explicit rules and compares them with a solution retrieved from past cases.

## Files

| File | Purpose |
| --- | --- |
| `ta4_main.py` | Knowledge base, rules, similarity scoring, interactive review, and persistence. |
| `study_cases.json` | Saved case base containing starter examples and a retained scenario. |
| [TA4_Buenaventura.pdf](TA4_Buenaventura.pdf) | Accompanying technical assessment PDF. |

## Requirements and execution

Install Python 3. No third-party packages or internet connection are required. From the repository root:

```sh
cd TA4-Buenaventura
python ta4_main.py
```

On Windows, `py` can replace `python` if that is how Python is installed.

For a repeatable demonstration without prompts:

```sh
python ta4_main.py --demo
```

Demo mode uses the built-in starter cases, retains the example only in memory, and does not read or modify `study_cases.json`.

To use a separate saved case file:

```sh
python ta4_main.py --case-file practice_cases.json
```

If that file does not exist, the application starts with the three built-in cases and creates the file after a completed interactive run. The parent directory must already exist. Run `python ta4_main.py --help` for command-line options.

## Part 1: Knowledge representation

Seven facts are represented in nested dictionaries under four categories:

| Category | Facts |
| --- | --- |
| Weather | Temperature in Celsius, relative humidity, whether it is raining. |
| Occupancy | Whether the room is occupied. |
| Lighting | Whether the room is dark. |
| Preferences | Preferred temperature and preference for natural light. |

Interactive input accepts temperatures from -20 to 60 degrees Celsius, humidity from 0 to 100, and `y`/`n` answers for Boolean facts.

## Part 2: Rule-based reasoning

The program evaluates five IF-THEN rules against a copy of the facts and collects every matching action:

| Condition | Action |
| --- | --- |
| Occupied room warmer than the preferred temperature | Suggest air conditioning toward the preferred temperature. |
| Rain | Suggest closing the windows. |
| Dark, occupied room | Suggest turning on the study light. |
| Bright, occupied room | Suggest daylight or a lamp according to the lighting preference. |
| Unoccupied room | Suggest keeping lights and cooling off. |

The console shows which rules match and lists their actions. These are text recommendations; the program does not control physical devices.

## Part 3: Case-based reasoning

1. **Retrieve:** Compare the current facts with each usable stored case. The case with the highest average feature score wins; the latest case wins ties.
2. **Reuse:** Display the selected case's written solution.
3. **Revise:** Press Enter or choose `1` to keep the solution. Choose `2` to write a replacement action. Blank or numeric-only replacements are rejected.
4. **Retain:** Append the current facts and final solution to the case base and save them after a completed interactive run.

All seven features have equal weight. Temperature and preferred-temperature similarity use `max(0, 1 - absolute_difference / 40)`; humidity uses `max(0, 1 - absolute_difference / 100)`. Boolean features receive 1 for a match and 0 otherwise. The final similarity is the mean of the seven scores. Older cases with numeric-only solutions are skipped during retrieval.

By default, interactive runs read and update `study_cases.json` beside the script. Malformed saved data is rejected before use, and saves use a temporary file followed by replacement.

## Demonstration output

The built-in demo uses a temperature of 32 degrees Celsius, humidity of 85%, rain, an occupied dark room, and preferences of 26 degrees Celsius and natural light. It produces three RBR actions: use air conditioning, close the windows, and turn on the study light.

CBR selects **Hot, humid, rainy evening** with **98.6% similarity**, reuses its solution, and increases the in-memory case count from three to four. Run `python ta4_main.py --demo` to reproduce this result without changing saved cases.

## Comparison and limitations

RBR derives actions from explicit conditions, while CBR retrieves a past written solution and lets the user revise it. Similarity is a feature-match score, not a probability that a recommendation is correct. CBR does not automatically reconcile its selected solution with the rule output, and a written revision is checked for text content rather than correctness. The scales, rules, and sample cases are demonstration choices.
