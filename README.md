# Keystroke Dynamics: Who's Typing?

## The idea

Each person has their own typing rhythm. Some people hold down keys for longer periods, while others are quicker at typing certain combinations of letters. The project asks whether these differences are enough to **recognize who is typing**, and **how much text is required** to do this with reliability.

The goal is to apply this in situations where a user is interacting with an AI (such as ChatGPT or Claude) via a browser. If someone else takes over the keyboard, the system should detect the change and trigger an alert.

The project consists of two primary programs:

- `main.py` is the **test tool**. It evaluates the detector’s performance using recorded keystroke data (CSV files).
- `app.py` is the **demo that is running**. You write in a window, and the program attempts to determine which person from the dataset is doing the writing.

---

## 1. Getting started

```bash cd Project pip install -r requirements.txt python main.py. ```

### Live Demo: "Who is Typing?"

```bash python app.py ```

1. When the program starts, the models are trained with all the Dataset_* folders. This takes a few seconds. The button becomes available once everything is ready.

2. Type whatever you want in the text box. English is recommended because most of the dataset contains English. You need at least one hundred keystrokes, which is about two or three sentences. Copying and pasting is disabled because pasted text does not have a typing rhythm.

3. Click Who's typing?. Press Ctrl+Enter. The program shows the likely person, together with a score for each person. A score near one means the typing rhythm matches that person's pattern. A higher score means it is less similar.

4. Click Clear to reset everything and start a test.

The program does not look at *what* you type, but *how* you type it.

The keystrokes are cleaned in the same way as the CSV files (`ksd/data.py`).

They are then split into windows of fifty keystrokes. Each window is compared with the k‑NN model of every person (`ksd/identify.py`).

The final score is the average across all windows.

Available options: `--window 100` `--distance gunetti`, `--k 5`.

**End-to-end test:** The last nine free-text sentences from each person are left out of training. Then replayed in groups of three as if they had been typed in the demo. **All twelve groups were correctly identified.**

> The system will always choose someone from the existing dataset because it simply selects the match.

> If the score is greater than the threshold, the result turns orange.

> This indicates that the typing rhythm is quite different from the person's pattern.

> It could be another person using the keyboard. It could be a different keyboard.

> Because everyone recorded their data on their computer, the results may be less reliable when using a different keyboard.

### Testing tool

Running the evaluation takes about one minute. You can also use these options:

| Command | What it does |
|---|---|
| `python main.py --dataset each` | Evaluates each type of dataset separately (recommended). |
| `python main.py --dataset free` | Uses only free-text sentences. |
| `python main.py --distance gunetti` | Uses another method to compare typing patterns (see Section 3). |
| `python main.py --k 5` | Compares against the 5 nearest neighbors instead of 3. |
| `python main.py --windows 30 60 120` | Tests different window sizes. |
| `python main.py --no-explore` | Skips the initial data statistics. |
| `python main.py --export-common` | Converts the data into the common CSV format used by the class. |

The results are saved in the `results/` folder:

- `distributions.png`: key hold times and typing delays for each person.
- `eer_vs_window_l1.png`: error rate depending on how much text is typed.
- `results_l1.csv`: the final results table.


## 2. The dataset

There are four participants: Constance, Fatima, Mariel, and Noé. Each one of them recorded three types of text and stored the records in their dataset folders named `Dataset_<name>`:

| Type | Content | Folders |
|---|---|---|
| `fixed` | The same sentence, "I am student at INSA", typed around 80 times. | `INSA80_*`, `one_sentence` |
| `ten` | 10 sentences copied from a given text. | `Ten_First_Sentences_*`, `11-sentence` |
| `free` | Around 50 sentences written freely by each person. | `50_Diff_Sentences_*`, `random_sentenses` |

Each row in a CSV represents either a **key press** (`keydown`) or a **key release** (`keyup`), together with its exact timestamp.

When the data is loaded, participants' names are replaced with pseudonyms in alphabetical order:

- **P01 = Constance**
- **P02 = Fatima**
- **P03 = Mariel**
- **P04 = Noé**

Names are compared without accents or capital letters, so `Noé` and `Noe` are treated as the same person.

The live demo, however, displays the actual names.

---

## 3. How the program works

### Step 1: Reconstructing keystrokes (`ksd/data.py`)

First, each key press is matched with its corresponding key release.

```text
keydown a at 2960 ms + keyup a at 3078 ms → "a" held for 118 ms
```


Some cleaning is also needed:

- A key that stays pressed and keeps repeating is only counted once.

- A key that is pressed but not released is not considered.

- The letter I (pressed while Shift is held) and the letter i (released) are seen as the same key.

### Step 2: Measuring typing rhythm

The program uses two measurements:

- **Hold time**: how long a key stays pressed.

- **Digraph latency**: time between pressing one key and the next. For example `a>m` shows the delay from pressing "a" to pressing "m”.

Some combinations are ignored:

- Those that involve a correction (Backspace) or an arrow key.

- Those that have a latency of ** more than **1.5 seconds** because this usually means a pause while thinking rather than part of a typing rhythm.

### Step 3: Splitting the data into windows (`ksd/features.py`)

The keystrokes  were split from each person into groups of **N keystrokes** (20, 50 100 etc.).

Each group then becomes a feature profile. That feature profile gives a quick summary of the typing rhythm.

For example:

> "a: 120 ms, e: 115 ms, a>m: 137 ms, t>space: 195 ms..."

This gives the program a way to describe and compare someone's typing behavior.

### Step 4: Comparing two profiles (`ksd/distance.py`)

Two different samples rarely contain the same words. Because of that, the program only compares **the keys and key combinations that appear in both samples**.

There are two comparison methods:

- **`l1` (default):** Measures the average difference between durations. The comparison is relative: a 10 ms difference matters more for a key held for 60 ms than for a key held for 400 ms.

  - **`gunetti`:** Ranks the key combinations from fastest to slowest in each sample, then checks whether their order is similar. This method is useful when someone types faster or slower, on occasion.

### Step 5: Training and detection (`ksd/detector.py`)

- **Training:** Each person's model is a group of their own typing patterns. It is trained with that person's data, just like a real situation where we would not have examples of future impostors.

- **Detection:** When a new sample comes in, the program looks for the 3 profiles in the model using the k-nearest neighbors algorithm (k-NN) and calculates a score.

A score close to 1 → the sample looks like that person.

A higher score → the sample is probably from someone else.

### Step 6: Evaluating the results (`ksd/evaluate.py`)

For each participant:

1. The first half of their samples in order is used for training.

2. The second half is used to test whether the system recognizes the person.

3. All samples from the participants are used for impostor tests.

---

## 4. Understanding the results

The detector uses a **threshold** to decide when to raise an alert. If the score is above this value, the system flags the sample.

There are two possible types of errors:

| Error | Meaning | Why it matters |
|---|---|---|
| **FAR** (False Acceptance Rate) | An impostor is accepted without being detected. | Serious security issue. |
| **FRR** (False Rejection Rate) | The system raises an alert even though the actual user is typing. | Annoying for users, who may eventually start ignoring the alerts. |

Increasing the threshold lowers the FRR but increases the FAR, and the opposite happens when lowering it.

Here are the main columns in the final results table:

| Column | Meaning | Ideal value |
|---|---|---|
| `window` | Number of keystrokes in each sample. | — |
| `n_windows` | Total number of available samples. | High |
| `EER` | Error rate at the point where FAR = FRR. This is the main metric used to summarize performance. | 0 |
| `threshold` | Threshold corresponding to the EER. | — |
| `FRR@FAR=5%` | False rejection rate when allowing only 5% of impostors to be accepted. | 0 |
| `ident_acc` | Percentage of samples correctly assigned to the right person ("Who's typing?"). | 1 |

### Results (`python main.py --dataset each`)

With the 4 participants, the results were:

| Window size | `free` (free text) | `fixed` (same sentence) | `all` (combined) |
|---|---|---|---|
| 20 keystrokes | EER 22% | 2.5% | 19% |
| 50 keystrokes | **9%** | 0.2% | 7% |
| 100 keystrokes | **0.4%** | 2% | 8% |
| 200 keystrokes | 14%  | 13%  | 5% |

With the first 3 participants, we obtained an EER of 4% for `free` with 50 keystrokes, and 0.4% with 100.

### What do these results tell us?

- **More text generally means fewer errors.**: Around 50 to 100 keystrokes (one or two sentences) were enough to make a decision.

- **The participants have noticeably different typing rhythms.** The initial statistics printed by the program show some examples:

  | | Fatima (P01) | Mariel (P02) | Noé (P03) |
  |---|---|---|---|
  | Median hold time | 96 ms | 83 ms | **120 ms** |
  | `e>n` latency | 246 ms | **54 ms** | 145 ms |
  | `n>s` latency | **395 ms** | 93 ms | 156 ms |

  The detector uses those differences to distinguish between participants.

- **The results for 200 keystrokes in `free` and `fixed` are not very reliable**. The fixed sentence only gives about 1,800 keystrokes per person, giving 7 or 8 samples of 200 keystrokes, and only  3 of these are available for training. With so few samples, the percentage is highly sensitive to error. Results based on around 30 samples should be treated with caution. The same is true for `ten` which has 17 samples of 50 keystrokes.

- **The combined `all` dataset performs worse than `free`.** Since training uses half of the data in chronological order, the model mostly sees the fixed sentence during training and is tested mainly on free text. The type of text changes from training to testing, which makes identification harder.

- **The current results are probably too optimistic.** With 4 participants, the detector only needs to distinguish between 4 different typing patterns. In the general population, people may have very similar rhythms, which would lead to more misclassifications.
---


## 5. Project structure

```text
Projet/
├── main.py            Testing tool: loads, explores, evaluates and plots results
├── app.py             Live demo (Tkinter "Who's typing?" window)
├── requirements.txt
├── results/           Generated graphs and tables
└── ksd/
    ├── data.py        CSV reading, key press/release matching, digraphs and common format export
    ├── features.py    Window splitting and feature extraction
    ├── distance.py    Comparison between two profiles (l1, gunetti)
    ├── detector.py    k-nearest neighbors detector
    ├── evaluate.py    FAR, FRR, EER and identification metrics
    └── identify.py    One model per person and scoring of live typing samples
```

---

## 6. What's next?

There are still a few things that could improve the project:

- **Data collection tool:** Create a browser extension that captures keystrokes and saves them in the CSV format that the class uses.

- **Live demo:** The basic version is already working in `app.py`. Right now, the start button should be pressed for the detection to start. The next step is to analyse the typing in real time and set the threshold accordingly, instead of the current 50-keystroke windows.

