# Annotation Protocol

## 1. Double annotation policy

- At least 25% of samples must be annotated independently by two annotators.
- All high_flood and urgent_rescue candidates should be prioritized for double annotation.

## 2. Conflict resolution

- If two labels disagree, sample goes to adjudication queue.
- One lead reviewer finalizes label and records rationale.

## 3. Quality tracking

- Track agreement rate weekly.
- If agreement drops below 0.8, update guideline examples.

## 4. Privacy rules

- Remove or mask personally identifiable information from text.
- Do not store personal phone numbers or full addresses in public report files.

## 5. Minimum metadata fields

- source
- event
- province
- timestamp (if available)
- annotator_1
- annotator_2
- final_label
- review_note
