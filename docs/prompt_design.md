# EssayMate Prompt Design

EssayMate currently uses a mock AI engine.

The product logic is designed as if it could be connected to a real AI model later.

## AI Scoring Prompt Design

Goal:

Evaluate a junior high English essay with clear, student-friendly feedback.

Prompt structure:

```text
You are an English writing coach for junior high students.
Evaluate the essay using four dimensions:
1. Content
2. Grammar
3. Structure
4. Vocabulary

Give a total score out of 15.
Explain problems in simple language.
Do not only criticize. Give encouragement and next steps.
```

Expected output:

- total score
- four-dimension score
- key problems
- actionable suggestions

## Sentence-Level Correction Prompt

Goal:

Help students see exactly how each sentence can be improved.

Prompt structure:

```text
For each sentence, return:
- Original sentence
- Improved sentence
- Reason

Use simple explanations.
If the sentence is already correct, improve fluency or add a useful detail.
```

Expected output:

| Original | Improved | Reason |
| --- | --- | --- |
| I like read books. | I like reading books. | Use like doing sth. |

## Model Essay Prompt

Goal:

Generate a short, memorable model essay for junior high students.

Prompt structure:

```text
Write a model essay for a junior high student.
Use simple vocabulary.
Keep the structure clear.
Include useful connectors.
Length: around 120 words.
Make it easy to imitate and memorize.
```

Expected output:

- simple opening
- clear body
- natural ending
- reusable phrases

## Learning Feedback Prompt

Goal:

Turn correction into learning.

Prompt structure:

```text
Based on the essay feedback, summarize what the student learned today.
Divide it into:
- Grammar
- Structure
- Vocabulary

Then suggest the next learning action.
```

Expected output:

- what you learned today
- next practice action
- retry guidance

